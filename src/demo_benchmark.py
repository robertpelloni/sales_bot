from src.logger import get_logger

logger = get_logger(__name__)
import asyncio
import json
import base64
import time
import os
import redis.asyncio as redis

r = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=6379, db=0)

NODE_ID = os.environ.get("NODE_ID", "kiosk_benchmark")


async def run_benchmark():
    logger.info("=========================================")
    logger.info("  PROJECT SIRENS - PIPELINE BENCHMARK")
    logger.info("=========================================")

    pubsub = r.pubsub()
    await pubsub.subscribe(f"AUDIO_CHUNK_READY:{NODE_ID}")

    # Generate mock base64 image
    mock_img = base64.b64encode(b"mock_image_data_for_benchmark").decode("utf-8")

    payload = {
        "metadata": {
            "id": 9999,
            "attributes": ["wearing a blue athletic jacket, holding a coffee cup"],
            "strategy": "A_AGGRESSIVE",
            "is_repeat_customer": False,
        },
        "image_b64": mock_img,
    }

    logger.info("-> Emitting CUSTOMER_DETECTED event to Redis...")
    start_time = time.time()

    await r.publish(f"CUSTOMER_DETECTED:{NODE_ID}", json.dumps(payload))

    # Wait for the first chunk to return
    first_chunk_received = False

    async for message in pubsub.listen():
        if message["type"] == "message":
            chunk = message["data"].decode("utf-8")

            if not first_chunk_received:
                ttft = (time.time() - start_time) * 1000
                logger.info(f"-> [METRIC] Time-To-First-Audio-Chunk: {ttft:.2f} ms")
                first_chunk_received = True

            logger.info(f"   [LLM Output Stream]: {chunk}")

            # If the response finishes naturally (the LLM client completes its stream), we exit.
            # For this simple demo script, we'll wait for a few chunks and then timeout.
            pass


async def main():
    logger.info(
        "Note: The 'llm_client' microservice MUST be running for this benchmark to work."
    )
    logger.info("Run in another terminal: python3 -m src.main --mode edge")

    try:
        await asyncio.wait_for(run_benchmark(), timeout=10.0)
    except asyncio.TimeoutError:
        logger.info("Benchmark finished. Stream timeout reached.")
    finally:
        await r.aclose()


if __name__ == "__main__":
    asyncio.run(main())
