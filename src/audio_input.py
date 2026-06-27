import os
import asyncio
import json
import redis.asyncio as redis

r = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379, db=0)

async def process_audio_input():
    print("Starting STT Mock Audio Input service...")

    # In a real environment, this loop would continuously stream from a microphone,
    # run inference on a local STT model like Whisper, and parse voice input.
    # We will mock the trigger using a secondary Redis queue for testing purposes,
    # or loop an input prompt.

    # For now, it will simply listen to a debug testing channel and route it to the LLM
    pubsub = r.pubsub()
    await pubsub.subscribe('DEBUG_MOCK_VOICE_INPUT')

    async for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'].decode('utf-8'))
            track_id = data.get('id', 1)
            text = data.get('text', "")

            print(f"[Audio Input / STT] Transcribed text for ID {track_id}: '{text}'")

            payload = {
                "id": track_id,
                "text": text
            }

            await r.publish('CUSTOMER_REPLY', json.dumps(payload))

if __name__ == "__main__":
    asyncio.run(process_audio_input())