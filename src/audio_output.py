import asyncio
import redis.asyncio as redis
import subprocess
import os

r = redis.Redis(host='localhost', port=6379, db=0)

async def process_audio_chunks():
    pubsub = r.pubsub()
    await pubsub.subscribe('AUDIO_CHUNK_READY')
    print("Listening for audio chunks...")

    PIPER_EXEC = "vendor/piper/piper"
    MODEL = "en_US-lessac-medium.onnx"

    # Simple check if binary exists
    piper_available = os.path.isfile(PIPER_EXEC)

    async for message in pubsub.listen():
        if message['type'] == 'message':
            chunk = message['data'].decode('utf-8')
            print(f"[Audio Output] Speaking: {chunk}")

            if piper_available:
                # Pipe string directly into piper and into aplay for instant playback securely
                try:
                    # Use a shell with shlex quoting to prevent injection
                    import shlex
                    safe_chunk = shlex.quote(chunk)
                    command = f'echo {safe_chunk} | {PIPER_EXEC} --model {MODEL} --output_file - | aplay -q'

                    process = await asyncio.create_subprocess_shell(
                        command,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await process.communicate()
                except Exception as e:
                    print(f"[Audio Output] Error running piper: {e}")
            else:
                # Fallback to simple print if piper is not built yet
                pass

if __name__ == "__main__":
    asyncio.run(process_audio_chunks())