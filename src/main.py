import asyncio
import sys
from src.vision import process_video_stream
from src.llm_client import handle_detection
from src.audio_output import process_audio_chunks

async def main():
    print("Starting Project Sirens Orchestrator...")

    # Check if a video source is provided, otherwise use default webcam (0)
    video_source = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else sys.argv[1] if len(sys.argv) > 1 else 0

    # Run all tasks concurrently
    await asyncio.gather(
        process_video_stream(video_source=video_source),
        handle_detection(),
        process_audio_chunks()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOrchestrator shutting down.")