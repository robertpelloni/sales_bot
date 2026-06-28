import os
import asyncio
import json
import unittest
import redis.asyncio as redis
from src.pos_client import mock_pos_system


class TestPOSClient(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.redis = redis.Redis(
            host=os.environ.get("REDIS_HOST", "localhost"), port=6379, db=0
        )

    async def asyncTearDown(self):
        await self.redis.delete("live_inventory")
        await self.redis.aclose()

    async def test_dynamic_pricing(self):
        # Start POS background task
        pos_task = asyncio.create_task(mock_pos_system())

        # Wait a moment for it to write to redis
        await asyncio.sleep(0.5)

        # Check Redis metric
        inventory_bytes = await self.redis.get("live_inventory")
        self.assertIsNotNone(inventory_bytes)

        inventory = json.loads(inventory_bytes.decode("utf-8"))
        self.assertIn("items", inventory)
        self.assertTrue(len(inventory["items"]) > 0)

        # Check structure
        first_item = inventory["items"][0]
        self.assertIn("stock_level", first_item)
        self.assertIn("price_usd", first_item)

        pos_task.cancel()
        try:
            await pos_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    unittest.main()
