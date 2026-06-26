import asyncio
import json
import sqlite3
import redis.asyncio as redis
from datetime import datetime

r = redis.Redis(host='localhost', port=6379, db=0)

DB_FILE = "analytics.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funnel (
            session_id INTEGER PRIMARY KEY,
            timestamp TEXT,
            status TEXT,
            last_message TEXT,
            strategy TEXT
        )
    ''')
    # Add strategy column if it doesn't exist (for migration)
    try:
        cursor.execute("ALTER TABLE funnel ADD COLUMN strategy TEXT DEFAULT 'DEFAULT'")
    except sqlite3.OperationalError:
        pass # Column already exists

    conn.commit()
    conn.close()

def update_funnel(session_id, status, last_message="", strategy=""):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()

    # If strategy is empty, we don't want to overwrite an existing strategy with empty string
    if strategy:
        cursor.execute('''
            INSERT INTO funnel (session_id, timestamp, status, last_message, strategy)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                timestamp=excluded.timestamp,
                status=excluded.status,
                last_message=excluded.last_message,
                strategy=excluded.strategy
        ''', (session_id, timestamp, status, last_message, strategy))
    else:
        cursor.execute('''
            INSERT INTO funnel (session_id, timestamp, status, last_message)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                timestamp=excluded.timestamp,
                status=excluded.status,
                last_message=excluded.last_message
        ''', (session_id, timestamp, status, last_message))

    conn.commit()
    conn.close()

async def process_analytics():
    init_db()
    print("Analytics Microservice listening for funnel events...")

    pubsub = r.pubsub()
    await pubsub.subscribe('CUSTOMER_DETECTED', 'CUSTOMER_REPLY', 'CUSTOMER_CONVERTED', 'CUSTOMER_OBJECTION')

    async for message in pubsub.listen():
        if message['type'] == 'message':
            channel = message['channel'].decode('utf-8')
            data = json.loads(message['data'].decode('utf-8'))

            session_id = data.get('id', 0)

            if channel == 'CUSTOMER_DETECTED':
                # The detected payload has 'id' nested under 'metadata'
                session_id = data.get('metadata', {}).get('id', 0)
                strategy = data.get('metadata', {}).get('strategy', 'DEFAULT')
                await asyncio.to_thread(update_funnel, session_id, "APPROACHED", "", strategy)
                print(f"[Analytics] Session {session_id} entered funnel: APPROACHED using {strategy}")

            elif channel == 'CUSTOMER_REPLY':
                text = data.get('text', "")
                await asyncio.to_thread(update_funnel, session_id, "ENGAGED", text)
                print(f"[Analytics] Session {session_id} advanced funnel: ENGAGED")

            elif channel == 'CUSTOMER_OBJECTION':
                text = data.get('text', "")
                await asyncio.to_thread(update_funnel, session_id, "OBJECTION_RAISED", text)
                print(f"[Analytics] Session {session_id} funnel state: OBJECTION_RAISED")

            elif channel == 'CUSTOMER_CONVERTED':
                await asyncio.to_thread(update_funnel, session_id, "CONVERTED")
                print(f"[Analytics] Session {session_id} advanced funnel: CONVERTED")
                await r.incr("metric:total_conversions")

if __name__ == "__main__":
    asyncio.run(process_analytics())
