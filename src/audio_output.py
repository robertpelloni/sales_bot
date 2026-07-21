import asyncio
import os
import time

async def play_audio_chunk(text_chunk: str):
    if not text_chunk:
        return

    print(f"Audio Output: Piping '{text_chunk}' to Piper TTS via stdin...")

    # Check if we are running in hardware mode or mock mode based on env vars
    # A true deployment relies on Piper TTS binaries built for ARM64/Pi5 and ALSA.
    use_mock = os.getenv("USE_MOCK_VISION", "True").lower() == "true"

    if use_mock:
        command = ["cat"]
    else:
        # Standard Piper invocation utilizing aplay for raw hardware audio out
        # Using a fast ONNX model like en_US-lessac-high
        command = ["sh", "-c", "vendor/piper/piper --model en_US-lessac-high.onnx --output_raw | aplay -r 22050 -f S16_LE -t raw -"]

    start_time = time.time()
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate(input=text_chunk.encode('utf-8'))

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        if process.returncode == 0:
            if use_mock:
                print(f"Audio Output (Mocked Success): {stdout.decode('utf-8').strip()} [{latency_ms}ms]")
            else:
                print(f"Audio Output (Hardware Success) [{latency_ms}ms].")

            # Log TTS latency to Redis to pass back to the hub CRM
            import redis.asyncio as redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            r = redis.from_url(redis_url)
            await r.publish("TTS_LATENCY_METRIC", str(latency_ms))
            await r.aclose()

        else:
            print(f"Audio Output Error: {stderr.decode('utf-8')}")

    except Exception as e:
        print(f"Audio Output Execution failed: {e}")
