"""
Project Sirens - Edge Kiosk Orchestrator
Coordinates camera frame capture, local vision tracking, Frontier VLM stream processing,
and low-latency Piper TTS audio output via an in-memory Redis pub/sub broker.
"""

import asyncio
import os
import json
import redis.asyncio as redis
from llm_client import process_vlm_stream
from audio_output import play_audio_chunk
from vision import start_vision_loop

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


async def orchestrator_loop():
    """
    Subscribes to Redis pub/sub channels and orchestrates event-driven tasks:
    - CUSTOMER_DETECTED: Triggers asynchronous VLM pitch generation with visual context.
    - AUDIO_CHUNK_READY: Dispatches sentence audio chunks to local Piper TTS engine.
    """
    r = redis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    await pubsub.subscribe("CUSTOMER_DETECTED", "AUDIO_CHUNK_READY")

    print(f"Orchestrator listening on Redis ({REDIS_URL})...")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                channel = message["channel"].decode("utf-8")
                data = message["data"].decode("utf-8")

                if channel == "CUSTOMER_DETECTED":
                    # Non-blocking trigger of VLM processing with enriched customer context
                    print(f"Customer detected in frame! Triggering VLM pipeline...")
                    asyncio.create_task(process_vlm_stream(data, r))

                elif channel == "AUDIO_CHUNK_READY":
                    # Non-blocking delivery of audio chunk to Piper TTS
                    print(f"Audio chunk ready: '{data[:30]}...' -> dispatching to Piper TTS.")
                    asyncio.create_task(play_audio_chunk(data))

    except Exception as e:
        print(f"Orchestrator encountered error: {e}")
    finally:
        await pubsub.unsubscribe()
        await r.aclose()


async def main():
    print("Starting Project Sirens Edge Kiosk...")

    # Start the local vision tracking loop as an asynchronous background worker
    vision_task = asyncio.create_task(start_vision_loop(REDIS_URL))

    # Run the main orchestrator pub/sub message pump
    try:
        await orchestrator_loop()
    finally:
        vision_task.cancel()
        try:
            await vision_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
