import asyncio
import httpx
import time
import statistics
import json

URL = "http://localhost:8000/api/log_interaction"
NUM_REQUESTS = 1000

async def make_request(client, payload):
    import base64
    auth_str = "admin:password"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    start_time = time.time()
    try:
        response = await client.post(URL, json=payload, timeout=10.0, headers={"Authorization": f"Basic {b64_auth}"})
        end_time = time.time()
        return end_time - start_time, response.status_code
    except Exception as e:
        return time.time() - start_time, str(e)

async def main():
    payload = {"attributes": "benchmark_test", "response": "benchmark_response"}

    # We use a connection pool limit higher than default to allow concurrency
    limits = httpx.Limits(max_connections=NUM_REQUESTS, max_keepalive_connections=NUM_REQUESTS)

    async with httpx.AsyncClient(limits=limits) as client:
        print(f"Starting {NUM_REQUESTS} concurrent requests to {URL}...")

        # Use a semaphore to prevent crashing the Uvicorn queue on small sandboxes
        sem = asyncio.Semaphore(100)

        async def bound_request(client, payload):
            async with sem:
                return await make_request(client, payload)

        # Fire requests with bounded concurrency
        tasks = [bound_request(client, payload) for _ in range(NUM_REQUESTS)]
        results = await asyncio.gather(*tasks)

        latencies = []
        errors = 0
        successes = 0

        for latency, status in results:
            if status == 200:
                successes += 1
                latencies.append(latency)
            else:
                errors += 1

        if not latencies:
            print("All requests failed!")
            return

        latencies_ms = [l * 1000 for l in latencies]
        latencies_ms.sort()

        p50 = statistics.quantiles(latencies_ms, n=100)[49]
        p90 = statistics.quantiles(latencies_ms, n=100)[89]
        p95 = statistics.quantiles(latencies_ms, n=100)[94]
        p99 = statistics.quantiles(latencies_ms, n=100)[98]

        report = f"""# Performance Benchmark: v0.1.0

## Target SLA
- 95th Percentile Latency: < 200ms

## Results
- Total Requests: {NUM_REQUESTS}
- Successful (200 OK): {successes}
- Failed/Errors: {errors}

## Latency Percentiles (ms)
- p50: {p50:.2f} ms
- p90: {p90:.2f} ms
- p95: {p95:.2f} ms
- p99: {p99:.2f} ms
- Max: {max(latencies_ms):.2f} ms
- Min: {min(latencies_ms):.2f} ms
- Mean: {statistics.mean(latencies_ms):.2f} ms

## SLA Status
"""
        if p95 < 200:
            report += "✅ PASS: 95th percentile is under 200ms."
        else:
            report += "❌ FAIL: 95th percentile exceeds 200ms."

        print(report)

        with open("metrics/perf_v0.1.0.txt", "w") as f:
            f.write(report)

if __name__ == "__main__":
    asyncio.run(main())
