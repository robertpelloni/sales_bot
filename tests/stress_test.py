import asyncio
import json
import time
import os
import redis.asyncio as redis
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stress_test")

async def simulate_kiosk(kiosk_id, r, num_events=3):
    pubsub = r.pubsub()
    await pubsub.subscribe(f"AUDIO_CHUNK_READY:{kiosk_id}")

    latencies = []

    for i in range(num_events):
        payload = {
            "metadata": {
                "id": i,
                "attributes": [f"stress test attribute {i}"],
                "strategy": "A_AGGRESSIVE",
                "is_repeat_customer": False,
            },
            "image_b64": "fake_image_b64",
        }

        start_time = time.time()
        await r.publish(f"CUSTOMER_DETECTED:{kiosk_id}", json.dumps(payload))

        try:
            async with asyncio.timeout(2.0):
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        ttft = (time.time() - start_time) * 1000
                        latencies.append(ttft)
                        break
        except asyncio.TimeoutError:
            logger.warning(f"Timeout for {kiosk_id}")

        await asyncio.sleep(0.1)

    await pubsub.unsubscribe()
    return latencies

async def main():
    r = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=6379, db=0)
    num_kiosks = 5

    logger.info(f"Starting stress test with {num_kiosks} kiosks.")

    # We also need a mock LLM listener for this to actually return chunks
    # Let's mock a simple listener
    async def mock_llm_listener():
        pubsub = r.pubsub()
        await pubsub.psubscribe("CUSTOMER_DETECTED:*")
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                channel = message["channel"].decode('utf-8')
                kiosk_id = channel.split(":")[1]
                await asyncio.sleep(0.05) # simulate processing time
                await r.publish(f"AUDIO_CHUNK_READY:{kiosk_id}", "Mock audio chunk")

    listener_task = asyncio.create_task(mock_llm_listener())

    # Let listener start
    await asyncio.sleep(0.5)

    tasks = []
    for i in range(num_kiosks):
        tasks.append(simulate_kiosk(f"kiosk_stress_{i}", r))

    results = await asyncio.gather(*tasks)
    listener_task.cancel()

    all_latencies = [l for r in results for l in r]
    if all_latencies:
        avg_latency = sum(all_latencies) / len(all_latencies)
        max_latency = max(all_latencies)
        min_latency = min(all_latencies)
        logger.info(f"Stress Test Results:")
        logger.info(f"Total events processed: {len(all_latencies)}")
        logger.info(f"Average TTFT: {avg_latency:.2f} ms")
        logger.info(f"Max TTFT: {max_latency:.2f} ms")
        logger.info(f"Min TTFT: {min_latency:.2f} ms")

    await r.aclose()

if __name__ == "__main__":
    asyncio.run(main())
