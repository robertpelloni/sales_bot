from src.logger import get_logger
logger = get_logger(__name__)
import asyncio
import redis.asyncio as redis
import subprocess
import os

r = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379, db=0)

NODE_ID = os.environ.get('NODE_ID', 'kiosk_default')

async def process_audio_chunks():
    try:
        pubsub = r.pubsub()
        await pubsub.subscribe(f'AUDIO_CHUNK_READY:{NODE_ID}')
        logger.info(f"Listening for audio chunks on node {NODE_ID}...")

        PIPER_EXEC = "vendor/piper/piper"
        MODEL = "en_US-lessac-medium.onnx"

        # Simple check if binary exists
        piper_available = os.path.isfile(PIPER_EXEC)

        async for message in pubsub.listen():
            if message['type'] == 'message':
                chunk = message['data'].decode('utf-8')
                logger.info(f"[Audio Output] Speaking: {chunk}")

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
                        logger.info(f"[Audio Output] Error running piper: {e}")
                else:
                    # Fallback to simple print if piper is not built yet
                    pass
    except asyncio.CancelledError:
        logger.info(f"[Audio Output] Cancelled for node {NODE_ID}.")
    finally:
        await r.aclose()

if __name__ == "__main__":
    asyncio.run(process_audio_chunks())
