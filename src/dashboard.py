import html
from src.logger import get_logger

logger = get_logger(__name__)
import json
import sqlite3
import uvicorn
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Project Sirens Vendor Dashboard")
DB_FILE = "data/analytics.db"
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

        # Overall funnel stats
        cursor.execute("SELECT status, COUNT(*) FROM funnel GROUP BY status")
        funnel_data = dict(cursor.fetchall())

        # Strategy A/B testing stats
        cursor.execute(
            "SELECT strategy, COUNT(*) FROM funnel WHERE status='CONVERTED' GROUP BY strategy"
        )
        strategy_data = dict(cursor.fetchall())

        # Node performance stats
        cursor.execute(
            "SELECT node_id, COUNT(*) FROM funnel WHERE status='CONVERTED' GROUP BY node_id"
        )
        node_data = dict(cursor.fetchall())

        conn.close()
    except Exception as e:
        funnel_data = {"Error": 1}
        strategy_data = {"Error": 1}
        node_data = {"Error": 1}

    # Ensure keys exist for the funnel
    f_approached = funnel_data.get("APPROACHED", 0)
    f_engaged = funnel_data.get("ENGAGED", 0)
    f_objection = funnel_data.get("OBJECTION_RAISED", 0)
    f_converted = funnel_data.get("CONVERTED", 0)

    # Fetch Inventory
    import redis

    r = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=6379, db=0)

    live_inventory_bytes = r.get("live_inventory")
    if live_inventory_bytes:
        inventory_data = json.loads(live_inventory_bytes.decode("utf-8"))
        source_label = "<span class='badge live'>Live POS Cache</span>"
    else:
        with open(INVENTORY_FILE, "r") as f:
            inventory_data = json.load(f)
            source_label = "<span class='badge static'>Static Config</span>"

    # Build Inventory HTML Table
    inv_rows = ""
    for item in inventory_data.get("items", []):
        stock = item.get("stock_level", "N/A")
        price = item.get("price_usd", 0.0)
        name = item.get("product_name", "Unknown")
        usps = "<br>".join(item.get("unique_selling_points", []))
        inv_rows += f"<tr><td>{name}</td><td>${price:.2f}</td><td>{stock}</td><td>{usps}</td></tr>"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sirens Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root {{
                --bg-color: #f4f7f6;
                --card-bg: #ffffff;
                --text-main: #333;
                --accent: #4a90e2;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: var(--bg-color);
                color: var(--text-main);
                margin: 0;
                padding: 20px 40px;
            }}
            h1 {{ text-align: center; color: var(--accent); margin-bottom: 40px; }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }}
            .card {{
                background: var(--card-bg);
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }}
            .card h2 {{ margin-top: 0; font-size: 1.2rem; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            .chart-container {{ position: relative; height: 300px; width: 100%; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f8f9fa; font-weight: 600; }}
            .badge {{ padding: 5px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; color: white; }}
            .badge.live {{ background-color: #2ecc71; }}
            .badge.static {{ background-color: #e74c3c; }}
        </style>
    </head>
    <body>
        <h1>Project Sirens Central Hub</h1>

        <div class="grid">
            <div class="card">
                <h2>Conversion Funnel Metrics</h2>
                <div class="chart-container">
                    <canvas id="funnelChart"></canvas>
                </div>
            </div>

            <div class="card">
                <h2>A/B Strategy Win-Rates (Conversions)</h2>
                <div class="chart-container">
                    <canvas id="strategyChart"></canvas>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Current Inventory (Store: {inventory_data['store_name']}) - {source_label}</h2>
            <table>
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Price</th>
                        <th>Stock Level</th>
                        <th>Selling Points</th>
                    </tr>
                </thead>
                <tbody>
                    {inv_rows}
                </tbody>
            </table>
        </div>

        <script>
            // Funnel Chart
            const ctxFunnel = document.getElementById('funnelChart').getContext('2d');
            new Chart(ctxFunnel, {{
                type: 'bar',
                data: {{
                    labels: ['Approached', 'Engaged', 'Objection', 'Converted'],
                    datasets: [{{
                        label: 'Customers',
                        data: [{f_approached}, {f_engaged}, {f_objection}, {f_converted}],
                        backgroundColor: [
                            'rgba(54, 162, 235, 0.6)',
                            'rgba(255, 206, 86, 0.6)',
                            'rgba(255, 99, 132, 0.6)',
                            'rgba(46, 204, 113, 0.6)'
                        ],
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{ y: {{ beginAtZero: true }} }}
                }}
            }});

            // Strategy Chart
            const ctxStrategy = document.getElementById('strategyChart').getContext('2d');
            const stratData = {json.dumps(strategy_data)};
            new Chart(ctxStrategy, {{
                type: 'doughnut',
                data: {{
                    labels: Object.keys(stratData),
                    datasets: [{{
                        data: Object.values(stratData),
                        backgroundColor: ['#9b59b6', '#34495e', '#e67e22', '#1abc9c']
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false }}
            }});
        </script>
    </body>
    </html>
    """
    return html_content


@app.get("/api/inventory")
async def get_inventory():
    with open(INVENTORY_FILE, "r") as f:
        return json.load(f)


@app.post("/api/inventory")
async def update_inventory(inventory: InventoryUpdate):
    try:
        with open(INVENTORY_FILE, "w") as f:
            json.dump(inventory.dict(), f, indent=2)
        return {"status": "success", "message": "Inventory updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def serve_dashboard():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    logger.info("Starting Vendor Dashboard on port 8000...")
    await server.serve()


if __name__ == "__main__":
    import asyncio

    asyncio.run(serve_dashboard())
