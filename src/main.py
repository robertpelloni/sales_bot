import asyncio
import os
import json
import redis.asyncio as redis
from llm_client import process_vlm_stream
from audio_output import play_audio_chunk
from vision import start_vision_loop

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

async def orchestrator_loop():
    r = redis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    await pubsub.subscribe("CUSTOMER_DETECTED", "AUDIO_CHUNK_READY")

    print("Orchestrator listening on Redis...")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                channel = message["channel"].decode("utf-8")
                data = message["data"].decode("utf-8")

                if channel == "CUSTOMER_DETECTED":
                    # Fire LLM generation in background
                    print(f"Customer detected! Triggering VLM... Data: {data}")
                    asyncio.create_task(process_vlm_stream(data, r))

                elif channel == "AUDIO_CHUNK_READY":
                    # Fire audio processing in background
                    print(f"Audio chunk ready! Chunk: {data}")
                    asyncio.create_task(play_audio_chunk(data))

    except Exception as e:
        print(f"Orchestrator error: {e}")
    finally:
        await pubsub.unsubscribe()
        await r.aclose()

async def main():
    print("Starting Project Sirens...")

    # Start the local vision tracking loop as a background task
    asyncio.create_task(start_vision_loop(REDIS_URL))

    # Run the main orchestrator pub/sub loop
    await orchestrator_loop()

if __name__ == "__main__":
    asyncio.run(main())
