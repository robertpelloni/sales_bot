import asyncio
import json
import random
import redis.asyncio as redis

r = redis.Redis(host='localhost', port=6379, db=0)

INVENTORY_FILE = "config/inventory.json"

async def mock_pos_system():
    print("Starting Mock POS Dynamic Pricing System...")

    while True:
        try:
            # Read base inventory
            with open(INVENTORY_FILE, 'r') as f:
                base_inventory = json.load(f)

            dynamic_inventory = {"store_name": base_inventory["store_name"], "items": []}

            for item in base_inventory["items"]:
                # Simulate live stock levels
                stock_level = random.randint(1, 100)
                original_price = item["price_usd"]

                # Apply dynamic pricing logic
                if stock_level > 80:
                    # Fire sale discount
                    dynamic_price = round(original_price * 0.85, 2)
                    item["unique_selling_points"].append("MANAGER'S SPECIAL: 15% OFF today only to clear inventory!")
                elif stock_level < 5:
                    # Scarcity premium
                    dynamic_price = round(original_price * 1.10, 2)
                    item["unique_selling_points"].append(f"EXTREME SCARCITY: Only {stock_level} units left in the state. High demand item.")
                else:
                    dynamic_price = original_price

                dynamic_item = {
                    "product_name": item["product_name"],
                    "price_usd": dynamic_price,
                    "stock_level": stock_level,
                    "unique_selling_points": item["unique_selling_points"]
                }
                dynamic_inventory["items"].append(dynamic_item)

            # Publish to Redis cache
            await r.set("live_inventory", json.dumps(dynamic_inventory))

        except Exception as e:
            print(f"[POS Client] Error updating dynamic pricing: {e}")

        # Update prices every 60 seconds
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(mock_pos_system())
