import json
import sqlite3
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Project Sirens Vendor Dashboard")
DB_FILE = "analytics.db"
INVENTORY_FILE = "config/inventory.json"

class InventoryItem(BaseModel):
    product_name: str
    price_usd: float
    unique_selling_points: List[str]

class InventoryUpdate(BaseModel):
    store_name: str
    items: List[InventoryItem]

@app.get("/", response_class=HTMLResponse)
async def read_dashboard():
    # Fetch Analytics
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) FROM funnel GROUP BY status")
        funnel_data = cursor.fetchall()

        cursor.execute("SELECT strategy, COUNT(*) FROM funnel WHERE status='CONVERTED' GROUP BY strategy")
        strategy_data = cursor.fetchall()

        conn.close()
    except Exception as e:
        funnel_data = [("Error connecting to DB", str(e))]
        strategy_data = []

    funnel_html = "".join([f"<li>{status}: {count}</li>" for status, count in funnel_data])
    strategy_html = "".join([f"<li>{strategy}: {count} conversions</li>" for strategy, count in strategy_data])

    # Fetch Inventory
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0)

    live_inventory_bytes = r.get("live_inventory")
    if live_inventory_bytes:
        inventory_data = json.loads(live_inventory_bytes.decode('utf-8'))
        source_label = "Live POS Cache"
    else:
        with open(INVENTORY_FILE, 'r') as f:
            inventory_data = json.load(f)
            source_label = "Static Config"

    html_content = f"""
    <html>
        <head>
            <title>Sirens Dashboard</title>
            <style>
                body {{ font-family: sans-serif; margin: 40px; }}
                .card {{ border: 1px solid #ccc; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>Project Sirens - Vendor Dashboard</h1>

            <div class="card">
                <h2>Conversion Funnel Metrics</h2>
                <ul>
                    {funnel_html}
                </ul>
                <h3>A/B Testing Strategies (Conversions)</h3>
                <ul>
                    {strategy_html}
                </ul>
            </div>

            <div class="card">
                <h2>Current Inventory (Store: {inventory_data['store_name']}) - Source: {source_label}</h2>
                <pre>{json.dumps(inventory_data['items'], indent=2)}</pre>
                <p><i>Use the /api/inventory POST endpoint to update the static config.</i></p>
            </div>
        </body>
    </html>
    """
    return html_content

@app.get("/api/inventory")
async def get_inventory():
    with open(INVENTORY_FILE, 'r') as f:
        return json.load(f)

@app.post("/api/inventory")
async def update_inventory(inventory: InventoryUpdate):
    try:
        with open(INVENTORY_FILE, 'w') as f:
            json.dump(inventory.dict(), f, indent=2)
        return {"status": "success", "message": "Inventory updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def serve_dashboard():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    print("Starting Vendor Dashboard on port 8000...")
    await server.serve()

if __name__ == "__main__":
    import asyncio
    asyncio.run(serve_dashboard())
