import sys
import os
import json

# Ensure project root is in sys.path so we can import src modules globally
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
import secrets
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, Integer, select
from .database import get_db, init_db, Interaction

app = FastAPI(title="Project Sirens Dashboard")
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

@app.on_event("startup")
async def on_startup():
    await init_db()

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
        return {"status": "success", "id": db_interaction.id}
    except Exception as e:
        await db.rollback()
        print(f"Database error during log_interaction: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to log interaction.")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, simulated_response: str = "", error_message: str = "", db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)):
    store_name = ""
    items = []
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
    today = datetime.datetime.utcnow().date()
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

    return templates.TemplateResponse(request=request, name="index.html", context={
        "chart_labels": json.dumps(chart_labels),
        "chart_data": json.dumps(chart_data),
        "framework_labels": json.dumps(framework_labels),
        "framework_totals": json.dumps(framework_totals),
        "framework_leads": json.dumps(framework_leads),
        "store_name": store_name,
        "items": items,
        "sales_framework": sales_framework,
        "tactics_enforced": tactics_enforced,
        "constraints": constraints,
        "openai_api_key": openai_api_key,
        "use_mock_vision": use_mock_vision,
        "simulated_response": simulated_response,
        "interactions": interactions,
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


@app.post("/simulate_detection")
async def simulate_detection(
    request: Request,
    attributes: str = Form(...),
    system_prompt_override: str = Form(""),
    temperature: float = Form(0.8),
    db: AsyncSession = Depends(get_db), username: str = Depends(get_current_username)
):
    from src.llm_client import process_vlm_stream

    attrs_list = [attr.strip() for attr in attributes.split(",")]
    mock_packet = {
        "id": 999,
        "proximity": "1.0m",
        "attributes": attrs_list,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
