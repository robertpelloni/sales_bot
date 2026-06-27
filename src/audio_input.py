from src.logger import get_logger
logger = get_logger(__name__)
import asyncio
import json
import os
import redis.asyncio as redis

r = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379, db=0)

NODE_ID = os.environ.get('NODE_ID', 'kiosk_default')

async def process_audio_input():
    logger.info(f"Starting STT Mock Audio Input service on node {NODE_ID}...")

    # In a real environment, this loop would continuously stream from a microphone,
    # run inference on a local STT model like Whisper, and parse voice input.
    # We will mock the trigger using a secondary Redis queue for testing purposes,
    # or loop an input prompt.

    # For now, it will simply listen to a debug testing channel and route it to the LLM
    try:
        pubsub = r.pubsub()
        await pubsub.subscribe(f'DEBUG_MOCK_VOICE_INPUT:{NODE_ID}')

        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'].decode('utf-8'))
                track_id = data.get('id', 1)
                text = data.get('text', "")

                logger.info(f"[Audio Input / STT] Transcribed text for ID {track_id}: '{text}'")

                payload = {
                    "id": track_id,
                    "text": text,
                    "node_id": NODE_ID
                }

                await r.publish(f'CUSTOMER_REPLY:{NODE_ID}', json.dumps(payload))
    except asyncio.CancelledError:
        logger.info(f"[Audio Input] Cancelled for node {NODE_ID}.")
    finally:
        await r.aclose()

if __name__ == "__main__":
    asyncio.run(process_audio_input())
