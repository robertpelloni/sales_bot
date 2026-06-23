import asyncio
import redis.asyncio as redis
import subprocess
import os

r = redis.Redis(host='localhost', port=6379, db=0)

async def process_audio_chunks():
    pubsub = r.pubsub()
    await pubsub.subscribe('AUDIO_CHUNK_READY')
    print("Listening for audio chunks...")

    # Pre-compile the piper command if using piper
    # E.g. echo "Hello" | piper --model en_US-lessac-medium.onnx --output_file - | aplay
    # Using a placeholder since we don't have piper installed globally on the system here or proper voice models.
    # In a real environment, you'd use a subprocess that interacts with the piper executable.

    async for message in pubsub.listen():
        if message['type'] == 'message':
            chunk = message['data'].decode('utf-8')
            print(f"[Audio Output] Speaking: {chunk}")

            # Using basic echo for demonstration or espeak. In real world, use vendor/piper.
            # Example piper invocation:
            # subprocess.run(["vendor/piper/piper", "--model", "en_US-lessac-medium.onnx", "--output_file", "output.wav"], input=chunk.encode())
            # subprocess.run(["aplay", "output.wav"])

if __name__ == "__main__":
    asyncio.run(process_audio_chunks())