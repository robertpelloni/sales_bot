import os
import json
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI(title="Project Sirens Dashboard")

os.makedirs("hub/templates", exist_ok=True)

templates = Jinja2Templates(directory="hub/templates")

def get_config_path(filename):
    if os.path.exists(f"config/{filename}"):
        return f"config/{filename}"
    elif os.path.exists(f"../config/{filename}"):
        return f"../config/{filename}"
    return None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, simulated_response: str = ""):
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

    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    use_mock_vision = os.getenv("USE_MOCK_VISION", "True")

    return templates.TemplateResponse(request=request, name="index.html", context={
        "store_name": store_name,
        "items": items,
        "sales_framework": sales_framework,
        "tactics_enforced": tactics_enforced,
        "constraints": constraints,
        "openai_api_key": openai_api_key,
        "use_mock_vision": use_mock_vision,
        "simulated_response": simulated_response
    })

@app.post("/update_system_config")
async def update_system_config(request: Request, openai_api_key: str = Form(""), use_mock_vision: str = Form("True")):
    os.environ["OPENAI_API_KEY"] = openai_api_key
    os.environ["USE_MOCK_VISION"] = use_mock_vision
    return await read_root(request)

@app.post("/update_settings")
async def update_settings(request: Request, store_name: str = Form(...), sales_framework: str = Form(...)):
    try:
        inv_path = get_config_path("inventory.json") or "../config/inventory.json"
        inv = {"store_name": store_name, "items": []}
        if os.path.exists(inv_path):
            with open(inv_path, "r") as f:
                inv = json.load(f)
        inv["store_name"] = store_name
        with open(inv_path, "w") as f:
            json.dump(inv, f, indent=2)

        pm_path = get_config_path("prompt_modifiers.json") or "../config/prompt_modifiers.json"
        pm = {"sales_framework": sales_framework, "tactics_enforced": [], "constraints": []}
        if os.path.exists(pm_path):
            with open(pm_path, "r") as f:
                pm = json.load(f)
        pm["sales_framework"] = sales_framework
        with open(pm_path, "w") as f:
            json.dump(pm, f, indent=2)

    except Exception as e:
        print(f"Error saving settings: {e}")

    return await read_root(request)

@app.post("/add_item")
async def add_item(request: Request, product_name: str = Form(...), price_usd: float = Form(...), usps: str = Form(...)):
    try:
        inv_path = get_config_path("inventory.json") or "../config/inventory.json"
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

    return await read_root(request)

@app.post("/add_tactic")
async def add_tactic(request: Request, tactic: str = Form(...)):
    try:
        pm_path = get_config_path("prompt_modifiers.json") or "../config/prompt_modifiers.json"
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

    return await read_root(request)

@app.post("/add_constraint")
async def add_constraint(request: Request, constraint: str = Form(...)):
    try:
        pm_path = get_config_path("prompt_modifiers.json") or "../config/prompt_modifiers.json"
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

    return await read_root(request)

@app.post("/simulate_detection")
async def simulate_detection(request: Request, attributes: str = Form(...)):
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from src.llm_client import process_vlm_stream

    attrs_list = [attr.strip() for attr in attributes.split(",")]
    mock_packet = {
        "id": 999,
        "proximity": "1.0m",
        "attributes": attrs_list,
        "frame_data": ""
    }

    # We call it without redis for the simulation endpoint
    response = await process_vlm_stream(json.dumps(mock_packet), None)

    return await read_root(request, simulated_response=response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
