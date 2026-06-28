import asyncio
import os
import redis.asyncio as redis
import sys

async def check_redis():
    print("Checking Redis connection...")
    try:
        r = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=6379, db=0)
        await asyncio.wait_for(r.ping(), timeout=2.0)
        print("✅ Redis is reachable.")
        await r.aclose()
        return True
    except Exception as e:
        print(f"❌ Redis check failed: {e}")
        return False

async def main():
    print("=== Automated Health Verification ===")

    redis_ok = await check_redis()

    if not redis_ok:
        print("\nHealth check FAILED. Please ensure all services are running.")
        sys.exit(1)

    print("\n✅ All systems GO. Ready for deployment.")
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
