import asyncio
import os

async def play_audio_chunk(text_chunk: str):
    if not text_chunk:
        return

    print(f"Audio Output: Piping '{text_chunk}' to Piper TTS via stdin...")
    command = ["cat"]

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate(input=text_chunk.encode('utf-8'))

        if process.returncode == 0:
            print(f"Audio Output (Mocked Success): {stdout.decode('utf-8').strip()}")
        else:
            print(f"Audio Output Error: {stderr.decode('utf-8')}")

    except Exception as e:
        print(f"Audio Output Execution failed: {e}")
