import os
import asyncio
import json
import sqlite3
import unittest
import redis.asyncio as redis
from src.analytics import process_analytics, DB_FILE


class TestAnalytics(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.redis = redis.Redis(
            host=os.environ.get("REDIS_HOST", "localhost"), port=6379, db=0
        )
        # Clear DB table
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS funnel (
                session_id INTEGER,
                node_id TEXT,
                timestamp TEXT,
                status TEXT,
                last_message TEXT,
                strategy TEXT,
                PRIMARY KEY (session_id, node_id)
            )
        """)
        cursor.execute("DELETE FROM funnel")
        conn.commit()
        conn.close()

    async def asyncTearDown(self):
        await self.redis.delete("metric:total_conversions")
        await self.redis.aclose()

    async def test_funnel_tracking(self):
        # Start analytics background task
        analytics_task = asyncio.create_task(process_analytics())
        await asyncio.sleep(0.1)  # allow subscription

        # 1. Detection
        payload = {
            "metadata": {"id": 100, "attributes": ["mock test attributes"]},
            "image_b64": "mock_img",
        }
        await self.redis.publish("CUSTOMER_DETECTED:kiosk_default", json.dumps(payload))
        await asyncio.sleep(0.1)

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM funnel WHERE session_id=100")
        self.assertEqual(cursor.fetchone()[0], "APPROACHED")
        conn.close()

        # 2. Convert
        await self.redis.publish(
            "CUSTOMER_CONVERTED:kiosk_default", json.dumps({"id": 100})
        )
        await asyncio.sleep(0.1)

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM funnel WHERE session_id=100")
        self.assertEqual(cursor.fetchone()[0], "CONVERTED")
        conn.close()

        # Check Redis metric
        conversions = await self.redis.get("metric:total_conversions")
        self.assertEqual(int(conversions), 1)

        analytics_task.cancel()
        try:
            await analytics_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    unittest.main()
