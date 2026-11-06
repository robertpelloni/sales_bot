import sys
import os
import json

# Ensure project root is in sys.path so we can import src modules globally
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from contextlib import asynccontextmanager
import signal
import io
import csv
from typing import List, Optional
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import secrets
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, Integer, select
from .database import get_db, init_db, Interaction
from .ab_engine import bandit_engine


class ConnectionManager:
    """Manages active WebSocket connections for broadcasting real-time dashboard events."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


ws_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Project Sirens Dashboard", lifespan=lifespan)
security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, os.getenv("ADMIN_USER", "admin"))
    correct_password = secrets.compare_digest(credentials.password, os.getenv("ADMIN_PASS", "password"))
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

os.makedirs("hub/templates", exist_ok=True)

templates = Jinja2Templates(directory="hub/templates")

def get_config_path(filename):
    if os.path.exists(f"config/{filename}"):
        return f"config/{filename}"
    elif os.path.exists(f"../config/{filename}"):
        return f"../config/{filename}"
    return f"../config/{filename}"

class InteractionCreate(BaseModel):
    attributes: str
    response: str
    sales_framework: str = "Unknown"
    tts_latency_ms: int = 0

@app.post("/api/log_interaction")
async def log_interaction(interaction: InteractionCreate, db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    try:
        db_interaction = Interaction(
            attributes=interaction.attributes,
            response=interaction.response,
            sales_framework=interaction.sales_framework,
            tts_latency_ms=interaction.tts_latency_ms
        )
        db.add(db_interaction)
        await db.commit()
        await db.refresh(db_interaction)

        # Broadcast event to connected WebSocket dashboards
        await ws_manager.broadcast({
            "event": "NEW_INTERACTION",
            "data": {
                "id": db_interaction.id,
                "timestamp": db_interaction.timestamp.strftime('%Y-%m-%d %H:%M'),
                "attributes": db_interaction.attributes,
                "response": db_interaction.response,
                "sales_framework": db_interaction.sales_framework,
                "tts_latency_ms": db_interaction.tts_latency_ms,
                "is_lead": db_interaction.is_lead,
                "follow_up_notes": db_interaction.follow_up_notes,
                "feedback_score": db_interaction.feedback_score
            }
        })

        return {"status": "success", "id": db_interaction.id}
    except Exception as e:
        await db.rollback()
        print(f"Database error during log_interaction: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to log interaction.")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, simulated_response: str = "", error_message: str = "", db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    store_name = ""
    items = []
    promotions = []
    sales_framework = ""
    tactics_enforced = []
    constraints = []

    try:
        inv_path = get_config_path("inventory.json")
        if inv_path:
            with open(inv_path, "r") as f:
                inv = json.load(f)
                store_name = inv.get("store_name", "")
                items = inv.get("items", [])
                promotions = inv.get("promotions", [])

        pm_path = get_config_path("prompt_modifiers.json")
        if pm_path:
            with open(pm_path, "r") as f:
                pm = json.load(f)
                sales_framework = pm.get("sales_framework", "")
                tactics_enforced = pm.get("tactics_enforced", [])
                constraints = pm.get("constraints", [])
    except Exception as e:
        print(f"Error loading config: {e}")
        error_message = f"Failed to load configurations: {e}"

    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    use_mock_vision = os.getenv("USE_MOCK_VISION", "True")

    query = select(Interaction).order_by(Interaction.timestamp.desc()).limit(10)
    result = await db.execute(query)
    interactions = result.scalars().all()

    # Generate Chart Data
    import datetime
    today = datetime.datetime.now(datetime.UTC).date()
    dates = [(today - datetime.timedelta(days=i)) for i in range(7)]
    dates.reverse() # past to present

    chart_labels = [d.strftime("%Y-%m-%d") for d in dates]
    chart_data = []

    for d in dates:
        count_query = select(func.count()).select_from(Interaction).where(func.date(Interaction.timestamp) == str(d))
        count_result = await db.execute(count_query)
        count = count_result.scalar()
        chart_data.append(count)

    # Generate Framework Effectiveness Data
    framework_query = select(
        Interaction.sales_framework,
        func.count(Interaction.id).label("total"),
        func.sum(func.cast(Interaction.is_lead, Integer)).label("leads")
    ).group_by(Interaction.sales_framework)

    framework_result = await db.execute(framework_query)
    framework_metrics = framework_result.all()

    framework_labels = [row.sales_framework for row in framework_metrics]
    framework_totals = [row.total for row in framework_metrics]
    framework_leads = [row.leads or 0 for row in framework_metrics] # sum returns None if empty

    # Fetch real-time A/B Bandit statistics
    bandit_stats = await bandit_engine.get_framework_performance(db)

    return templates.TemplateResponse(request=request, name="index.html", context={
        "chart_labels": json.dumps(chart_labels),
        "chart_data": json.dumps(chart_data),
        "framework_labels": json.dumps(framework_labels),
        "framework_totals": json.dumps(framework_totals),
        "framework_leads": json.dumps(framework_leads),
        "store_name": store_name,
        "items": items,
        "promotions": promotions,
        "sales_framework": sales_framework,
        "tactics_enforced": tactics_enforced,
        "constraints": constraints,
        "openai_api_key": openai_api_key,
        "use_mock_vision": use_mock_vision,
        "simulated_response": simulated_response,
        "interactions": interactions,
        "bandit_stats": bandit_stats,
        "bandit_config": {
            "epsilon": bandit_engine.epsilon,
            "decay_rate": bandit_engine.decay_rate,
            "min_epsilon": bandit_engine.min_epsilon,
            "default_method": bandit_engine.default_method,
            "contextual_weighting": bandit_engine.contextual_weighting
        },
        "error_message": error_message
    })

from fastapi.responses import RedirectResponse

@app.post("/update_system_config")
async def update_system_config(request: Request, openai_api_key: str = Form(""), use_mock_vision: str = Form("True"), db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    os.environ["OPENAI_API_KEY"] = openai_api_key
    os.environ["USE_MOCK_VISION"] = use_mock_vision

    # Save system configs to a shared file so the Kiosk container can read them
    try:
        sys_config_path = get_config_path("system_config.json")
        sys_config = {
            "OPENAI_API_KEY": openai_api_key,
            "USE_MOCK_VISION": use_mock_vision
        }
        with open(sys_config_path, "w") as f:
            json.dump(sys_config, f, indent=2)
    except Exception as e:
        print(f"Error saving system config: {e}")
        return await read_root(request, error_message=f"Error saving system config: {e}", db=db)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/update_settings")
async def update_settings(request: Request, store_name: str = Form(...), sales_framework: str = Form(...), db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    try:
        inv_path = get_config_path("inventory.json")
        inv = {"store_name": store_name, "items": []}
        if os.path.exists(inv_path):
            with open(inv_path, "r") as f:
                inv = json.load(f)
        inv["store_name"] = store_name
        with open(inv_path, "w") as f:
            json.dump(inv, f, indent=2)

        pm_path = get_config_path("prompt_modifiers.json")
        pm = {"sales_framework": sales_framework, "tactics_enforced": [], "constraints": []}
        if os.path.exists(pm_path):
            with open(pm_path, "r") as f:
                pm = json.load(f)
        pm["sales_framework"] = sales_framework
        with open(pm_path, "w") as f:
            json.dump(pm, f, indent=2)

    except Exception as e:
        print(f"Error saving settings: {e}")
        return await read_root(request, error_message=f"Error saving settings: {e}", db=db)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/delete_item")
async def delete_item(request: Request, product_name: str = Form(...), db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    try:
        inv_path = get_config_path("inventory.json")
        if os.path.exists(inv_path):
            with open(inv_path, "r") as f:
                inv = json.load(f)

            inv["items"] = [item for item in inv.get("items", []) if item.get("product_name") != product_name]

            with open(inv_path, "w") as f:
                json.dump(inv, f, indent=2)
    except Exception as e:
        print(f"Error deleting item: {e}")
        return await read_root(request, error_message=f"Error deleting item: {e}", db=db)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/add_item")
async def add_item(request: Request, product_name: str = Form(...), price_usd: float = Form(...), usps: str = Form(...), db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    try:
        inv_path = get_config_path("inventory.json")
        inv = {"store_name": "", "items": []}
        if os.path.exists(inv_path):
            with open(inv_path, "r") as f:
                inv = json.load(f)

        new_item = {
            "product_name": product_name,
            "price_usd": price_usd,
            "unique_selling_points": [usp.strip() for usp in usps.split(",") if usp.strip()]
        }
        inv["items"].append(new_item)

        with open(inv_path, "w") as f:
            json.dump(inv, f, indent=2)
    except Exception as e:
        print(f"Error adding item: {e}")
        return await read_root(request, error_message=f"Error adding item: {e}", db=db)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/add_promotion")
async def add_promotion(
    request: Request,
    rule_name: str = Form(...),
    discount_percent: float = Form(...),
    trigger_type: str = Form(...),
    threshold: str = Form(""),
    description: str = Form(""),
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """Adds a dynamic promotional discount rule to inventory configuration."""
    try:
        inv_path = get_config_path("inventory.json")
        inv = {"store_name": "", "items": [], "promotions": []}
        if os.path.exists(inv_path):
            with open(inv_path, "r") as f:
                inv = json.load(f)

        if "promotions" not in inv or not isinstance(inv["promotions"], list):
            inv["promotions"] = []

        new_promo = {
            "rule_name": rule_name.strip(),
            "discount_percent": float(discount_percent),
            "trigger_type": trigger_type.strip(),
            "threshold": threshold.strip(),
            "description": description.strip()
        }
        inv["promotions"].append(new_promo)

        with open(inv_path, "w") as f:
            json.dump(inv, f, indent=2)
    except Exception as e:
        print(f"Error adding promotion: {e}")
        return await read_root(request, error_message=f"Error adding promotion: {e}", db=db)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/delete_promotion/{promo_index}")
async def delete_promotion(
    request: Request,
    promo_index: int,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """Deletes an active promotional rule by its index."""
    try:
        inv_path = get_config_path("inventory.json")
        if os.path.exists(inv_path):
            with open(inv_path, "r") as f:
                inv = json.load(f)

            if "promotions" in inv and 0 <= promo_index < len(inv["promotions"]):
                inv["promotions"].pop(promo_index)

            with open(inv_path, "w") as f:
                json.dump(inv, f, indent=2)
    except Exception as e:
        print(f"Error deleting promotion: {e}")
        return await read_root(request, error_message=f"Error deleting promotion: {e}", db=db)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/delete_tactic")
async def delete_tactic(request: Request, tactic: str = Form(...), db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    try:
        pm_path = get_config_path("prompt_modifiers.json")
        if os.path.exists(pm_path):
            with open(pm_path, "r") as f:
                pm = json.load(f)

            if "tactics_enforced" in pm:
                pm["tactics_enforced"] = [t for t in pm["tactics_enforced"] if t != tactic]

            with open(pm_path, "w") as f:
                json.dump(pm, f, indent=2)
    except Exception as e:
        print(f"Error deleting tactic: {e}")
        return await read_root(request, error_message=f"Error deleting tactic: {e}", db=db)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/add_tactic")
async def add_tactic(request: Request, tactic: str = Form(...), db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    try:
        pm_path = get_config_path("prompt_modifiers.json")
        pm = {"sales_framework": "", "tactics_enforced": [], "constraints": []}
        if os.path.exists(pm_path):
            with open(pm_path, "r") as f:
                pm = json.load(f)

        if tactic.strip() not in pm.get("tactics_enforced", []):
            pm.setdefault("tactics_enforced", []).append(tactic.strip())

        with open(pm_path, "w") as f:
            json.dump(pm, f, indent=2)
    except Exception as e:
        print(f"Error adding tactic: {e}")
        return await read_root(request, error_message=f"Error adding tactic: {e}", db=db)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/delete_constraint")
async def delete_constraint(request: Request, constraint: str = Form(...), db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    try:
        pm_path = get_config_path("prompt_modifiers.json")
        if os.path.exists(pm_path):
            with open(pm_path, "r") as f:
                pm = json.load(f)

            if "constraints" in pm:
                pm["constraints"] = [c for c in pm["constraints"] if c != constraint]

            with open(pm_path, "w") as f:
                json.dump(pm, f, indent=2)
    except Exception as e:
        print(f"Error deleting constraint: {e}")
        return await read_root(request, error_message=f"Error deleting constraint: {e}", db=db)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/add_constraint")
async def add_constraint(request: Request, constraint: str = Form(...), db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    try:
        pm_path = get_config_path("prompt_modifiers.json")
        pm = {"sales_framework": "", "tactics_enforced": [], "constraints": []}
        if os.path.exists(pm_path):
            with open(pm_path, "r") as f:
                pm = json.load(f)

        if constraint.strip() not in pm.get("constraints", []):
            pm.setdefault("constraints", []).append(constraint.strip())

        with open(pm_path, "w") as f:
            json.dump(pm, f, indent=2)
    except Exception as e:
        print(f"Error adding constraint: {e}")
        return await read_root(request, error_message=f"Error adding constraint: {e}", db=db)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/mark_lead/{interaction_id}")
async def mark_lead(request: Request, interaction_id: int, is_lead: bool = Form(...), db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    try:
        result = await db.execute(select(Interaction).filter(Interaction.id == interaction_id))
        interaction = result.scalars().first()
        if interaction:
            interaction.is_lead = is_lead
            await db.commit()
    except Exception as e:
        print(f"Error marking lead: {e}")
        return await read_root(request, error_message=f"Error marking lead: {e}", db=db)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/update_follow_up/{interaction_id}")
async def update_follow_up(request: Request, interaction_id: int, follow_up_notes: str = Form(...), db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    try:
        result = await db.execute(select(Interaction).filter(Interaction.id == interaction_id))
        interaction = result.scalars().first()
        if interaction:
            interaction.follow_up_notes = follow_up_notes
            await db.commit()
    except Exception as e:
        print(f"Error updating follow up notes: {e}")
        return await read_root(request, error_message=f"Error updating follow up notes: {e}", db=db)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/submit_feedback/{interaction_id}")
async def submit_feedback(request: Request, interaction_id: int, feedback_score: int = Form(...), db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    try:
        result = await db.execute(select(Interaction).filter(Interaction.id == interaction_id))
        interaction = result.scalars().first()
        if interaction:
            interaction.feedback_score = feedback_score
            await db.commit()
    except Exception as e:
        print(f"Error updating feedback score: {e}")
        return await read_root(request, error_message=f"Error updating feedback score: {e}", db=db)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """Real-time event stream for connected dashboard sessions."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; accept client pings/messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@app.post("/simulate_detection")
async def simulate_detection(
    request: Request,
    attributes: str = Form(...),
    system_prompt_override: str = Form(""),
    temperature: float = Form(0.8),
    proximity: str = Form("1.0m (close)"),
    distance_m: float = Form(1.0),
    dwell_time_s: float = Form(1.8),
    framework_selection: str = Form("auto"),
    db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)
):
    from src.llm_client import process_vlm_stream

    # Dynamically resolve framework if requested or defaulted to auto bandit allocation
    effective_framework = None
    if framework_selection == "auto":
        try:
            chosen_fw, _ = await bandit_engine.allocate_next_framework(
                db,
                dwell_time=dwell_time_s,
                distance_m=distance_m
            )
            effective_framework = chosen_fw
        except Exception as e:
            print(f"Error during bandit framework allocation: {e}")
    elif framework_selection.strip():
        effective_framework = framework_selection.strip()

    attrs_list = [attr.strip() for attr in attributes.split(",")]
    mock_packet = {
        "id": 999,
        "proximity": proximity.strip(),
        "distance_m": distance_m,
        "dwell_time_s": dwell_time_s,
        "attributes": attrs_list,
        "sales_framework": effective_framework,
        "frame_data": "",
        "system_prompt_override": system_prompt_override.strip(),
        "temperature": temperature
    }

    try:
        # We call it without redis for the simulation endpoint
        response = await process_vlm_stream(json.dumps(mock_packet), None)
        return await read_root(request, simulated_response=response, db=db)
    except Exception as e:
        print(f"Error during simulation: {e}")
        return await read_root(request, error_message=f"Error during simulation: {e}", db=db)


@app.get("/api/status")
async def get_server_status(username: str = Depends(get_current_username)):
    """Returns the operational status of the Hub, database, and system configs."""
    use_mock_vision = os.getenv("USE_MOCK_VISION", "True")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    camera_index = os.getenv("CAMERA_INDEX", "0")

    sys_config_path = get_config_path("system_config.json")
    if os.path.exists(sys_config_path):
        try:
            with open(sys_config_path, "r") as f:
                cfg = json.load(f)
                use_mock_vision = cfg.get("USE_MOCK_VISION", use_mock_vision)
                openai_key = cfg.get("OPENAI_API_KEY", openai_key)
                camera_index = cfg.get("CAMERA_INDEX", camera_index)
        except Exception:
            pass

    inv_path = get_config_path("inventory.json")
    item_count = 0
    promotions_count = 0
    if os.path.exists(inv_path):
        try:
            with open(inv_path, "r") as f:
                inv = json.load(f)
                item_count = len(inv.get("items", []))
                promotions_count = len(inv.get("promotions", []))
        except Exception:
            pass

    version = "0.8.0"
    for v_path in ["VERSION.md", "../VERSION.md"]:
        if os.path.exists(v_path):
            try:
                with open(v_path, "r") as vf:
                    version = vf.read().strip()
                break
            except Exception:
                pass

    return {
        "status": "healthy",
        "service": "Project Sirens Hub",
        "version": version,
        "mock_vision": str(use_mock_vision).lower() == "true",
        "camera_index": str(camera_index),
        "has_openai_key": bool(openai_key),
        "inventory_item_count": item_count,
        "active_promotions_count": promotions_count
    }


@app.get("/api/ab/allocations")
async def get_ab_allocations(db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    """Returns the multi-armed bandit framework performance, empirical win rates, confidence intervals, and Bayesian priors."""
    stats = await bandit_engine.get_framework_performance(db)
    return {
        "status": "success",
        "allocations": stats,
        "config": {
            "epsilon": bandit_engine.epsilon,
            "decay_rate": bandit_engine.decay_rate,
            "min_epsilon": bandit_engine.min_epsilon,
            "default_method": bandit_engine.default_method,
            "contextual_weighting": bandit_engine.contextual_weighting
        }
    }


@app.post("/api/ab/select_framework")
async def select_ab_framework(
    method: Optional[str] = None,
    dwell_time_s: Optional[float] = None,
    distance_m: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """Dynamically samples the optimal sales framework for an incoming customer interaction, supporting vision context."""
    chosen_framework, stats = await bandit_engine.allocate_next_framework(
        db,
        method=method,
        dwell_time=dwell_time_s,
        distance_m=distance_m
    )
    chosen_stats = stats.get(chosen_framework, {})
    return {
        "status": "success",
        "selected_framework": chosen_framework,
        "method": method or bandit_engine.default_method,
        "conversion_rate": chosen_stats.get("conversion_rate", 0.0),
        "context_affinity": chosen_stats.get("context_affinity", 1.0)
    }


class BanditConfigPayload(BaseModel):
    epsilon: Optional[float] = None
    decay_rate: Optional[float] = None
    min_epsilon: Optional[float] = None
    default_method: Optional[str] = None
    contextual_weighting: Optional[bool] = None


@app.post("/api/ab/config")
async def configure_ab_bandit(
    payload: BanditConfigPayload,
    username: str = Depends(get_current_username)
):
    """Dynamically reconfigures multi-armed bandit algorithmic parameters."""
    if payload.epsilon is not None:
        bandit_engine.epsilon = max(0.0, min(1.0, float(payload.epsilon)))
    if payload.decay_rate is not None:
        bandit_engine.decay_rate = max(0.5, min(1.0, float(payload.decay_rate)))
    if payload.min_epsilon is not None:
        bandit_engine.min_epsilon = max(0.0, min(1.0, float(payload.min_epsilon)))
    if payload.default_method is not None:
        if payload.default_method in ["thompson", "epsilon_greedy", "ucb1"]:
            bandit_engine.default_method = payload.default_method
    if payload.contextual_weighting is not None:
        bandit_engine.contextual_weighting = bool(payload.contextual_weighting)

    return {
        "status": "success",
        "config": {
            "epsilon": bandit_engine.epsilon,
            "decay_rate": bandit_engine.decay_rate,
            "min_epsilon": bandit_engine.min_epsilon,
            "default_method": bandit_engine.default_method,
            "contextual_weighting": bandit_engine.contextual_weighting
        }
    }


@app.post("/api/ab/reset")
async def reset_ab_bandit(
    epsilon: Optional[float] = None,
    username: str = Depends(get_current_username)
):
    """Resets the bandit exploration state and parameters to initial defaults."""
    bandit_engine.reset_parameters(epsilon=epsilon)
    return {
        "status": "success",
        "message": "Multi-Armed Bandit parameters and prior overrides reset successfully",
        "config": {
            "epsilon": bandit_engine.epsilon,
            "decay_rate": bandit_engine.decay_rate,
            "min_epsilon": bandit_engine.min_epsilon,
            "default_method": bandit_engine.default_method
        }
    }


@app.post("/update_ab_config")
async def update_ab_config_form(
    request: Request,
    epsilon: float = Form(0.20),
    decay_rate: float = Form(0.99),
    min_epsilon: float = Form(0.05),
    default_method: str = Form("thompson"),
    contextual_weighting: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """UI form endpoint to update bandit algorithm hyperparameters."""
    bandit_engine.epsilon = max(0.0, min(1.0, float(epsilon)))
    bandit_engine.decay_rate = max(0.5, min(1.0, float(decay_rate)))
    bandit_engine.min_epsilon = max(0.0, min(1.0, float(min_epsilon)))
    bandit_engine.contextual_weighting = (contextual_weighting == "on" or contextual_weighting == "true")
    if default_method in ["thompson", "epsilon_greedy", "ucb1"]:
        bandit_engine.default_method = default_method
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/reset_ab_bandit")
async def reset_ab_bandit_form(
    request: Request,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """UI form endpoint to reset bandit parameters."""
    bandit_engine.reset_parameters()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/api/leads/export")
async def export_leads_csv(all: bool = False, db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    """Exports CRM interactions as a downloadable CSV. Defaults to qualified leads only."""
    query = select(Interaction)
    if not all:
        query = query.filter(Interaction.is_lead == True)
    query = query.order_by(Interaction.id.desc())

    result = await db.execute(query)
    interactions = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "id",
        "timestamp",
        "attributes",
        "response",
        "sales_framework",
        "is_lead",
        "follow_up_notes",
        "tts_latency_ms",
        "feedback_score"
    ])

    for item in interactions:
        writer.writerow([
            item.id,
            item.timestamp.isoformat() if item.timestamp else "",
            item.attributes or "",
            item.response or "",
            item.sales_framework or "",
            item.is_lead,
            item.follow_up_notes or "",
            item.tts_latency_ms or 0,
            item.feedback_score or 0
        ])

    csv_data = output.getvalue()
    filename = "crm_all_interactions.csv" if all else "crm_leads.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/analytics/summary")
async def get_analytics_summary(db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    """Aggregates CRM conversion metrics, lead velocity, and average latency stats."""
    total_result = await db.execute(select(func.count(Interaction.id)))
    total_interactions = total_result.scalar() or 0

    lead_result = await db.execute(select(func.count(Interaction.id)).filter(Interaction.is_lead == True))
    total_leads = lead_result.scalar() or 0

    latency_result = await db.execute(select(func.avg(Interaction.tts_latency_ms)))
    avg_latency = latency_result.scalar() or 0.0

    feedback_result = await db.execute(select(func.avg(Interaction.feedback_score)).filter(Interaction.feedback_score > 0))
    avg_feedback = feedback_result.scalar() or 0.0

    conversion_rate = round((total_leads / total_interactions * 100), 2) if total_interactions > 0 else 0.0

    return {
        "status": "success",
        "total_interactions": total_interactions,
        "total_leads": total_leads,
        "conversion_rate_percent": conversion_rate,
        "avg_tts_latency_ms": round(float(avg_latency), 1),
        "avg_feedback_score": round(float(avg_feedback), 2)
    }


@app.post("/api/server/shutdown")
async def shutdown_server(username: str = Depends(get_current_username)):
    """Gracefully terminates the Hub server process."""
    def _delayed_exit():
        import time
        time.sleep(0.5)
        os.kill(os.getpid(), signal.SIGTERM)

    import threading
    threading.Thread(target=_delayed_exit, daemon=True).start()
    return JSONResponse(status_code=200, content={"status": "shutting_down", "message": "Hub server is shutting down gracefully."})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
