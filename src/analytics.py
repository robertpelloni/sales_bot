import asyncio
import json
import sqlite3
import os
import redis.asyncio as redis
from datetime import datetime

r = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379, db=0)

DB_FILE = "data/analytics.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funnel (
            session_id INTEGER,
            node_id TEXT,
            timestamp TEXT,
            status TEXT,
            last_message TEXT,
            strategy TEXT,
            PRIMARY KEY (session_id, node_id)
        )
    ''')
    # Add strategy and node_id columns if they don't exist (for migration)
    try:
        cursor.execute("ALTER TABLE funnel ADD COLUMN strategy TEXT DEFAULT 'DEFAULT'")
    except sqlite3.OperationalError:
        pass # Column already exists
    try:
        cursor.execute("ALTER TABLE funnel ADD COLUMN node_id TEXT DEFAULT 'kiosk_default'")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def update_funnel(session_id, node_id, status, last_message="", strategy=""):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()

    if strategy:
        cursor.execute('''
            INSERT INTO funnel (session_id, node_id, timestamp, status, last_message, strategy)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id, node_id) DO UPDATE SET
                timestamp=excluded.timestamp,
                status=excluded.status,
                last_message=excluded.last_message,
                strategy=excluded.strategy
        ''', (session_id, node_id, timestamp, status, last_message, strategy))
    else:
        cursor.execute('''
            INSERT INTO funnel (session_id, node_id, timestamp, status, last_message)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(session_id, node_id) DO UPDATE SET
                timestamp=excluded.timestamp,
                status=excluded.status,
                last_message=excluded.last_message
        ''', (session_id, node_id, timestamp, status, last_message))

    conn.commit()
    conn.close()

async def process_analytics():
    init_db()
    print("Analytics Microservice listening for funnel events across all nodes...")

    pubsub = r.pubsub()
    # Subscribe to all node events using psubscribe
    await pubsub.psubscribe('CUSTOMER_DETECTED:*', 'CUSTOMER_REPLY:*', 'CUSTOMER_CONVERTED:*', 'CUSTOMER_OBJECTION:*')

    async for message in pubsub.listen():
        if message['type'] == 'pmessage':
            channel = message['channel'].decode('utf-8')
            data = json.loads(message['data'].decode('utf-8'))

            # Extract node_id and base channel
            parts = channel.split(':')
            base_channel = parts[0]
            node_id = parts[1] if len(parts) > 1 else 'kiosk_default'

            session_id = data.get('id', 0)

            if base_channel == 'CUSTOMER_DETECTED':
                # The detected payload has 'id' nested under 'metadata'
                session_id = data.get('metadata', {}).get('id', 0)
                strategy = data.get('metadata', {}).get('strategy', 'DEFAULT')
                await asyncio.to_thread(update_funnel, session_id, node_id, "APPROACHED", "", strategy)
                print(f"[Analytics] Session {session_id} on {node_id} entered funnel: APPROACHED using {strategy}")

            elif base_channel == 'CUSTOMER_REPLY':
                text = data.get('text', "")
                await asyncio.to_thread(update_funnel, session_id, node_id, "ENGAGED", text)
                print(f"[Analytics] Session {session_id} on {node_id} advanced funnel: ENGAGED")

            elif base_channel == 'CUSTOMER_OBJECTION':
                text = data.get('text', "")
                await asyncio.to_thread(update_funnel, session_id, node_id, "OBJECTION_RAISED", text)
                print(f"[Analytics] Session {session_id} on {node_id} funnel state: OBJECTION_RAISED")

            elif base_channel == 'CUSTOMER_CONVERTED':
                await asyncio.to_thread(update_funnel, session_id, node_id, "CONVERTED")
                print(f"[Analytics] Session {session_id} on {node_id} advanced funnel: CONVERTED")
                await r.incr("metric:total_conversions")

if __name__ == "__main__":
    asyncio.run(process_analytics())
