import os
import asyncio
import sys
from src.vision import process_video_stream
from src.llm_client import handle_events
from src.audio_output import process_audio_chunks
from src.audio_input import process_audio_input
from src.analytics import process_analytics
from src.dashboard import serve_dashboard
from src.pos_client import mock_pos_system

import argparse

async def main():
    parser = argparse.ArgumentParser(description="Project Sirens Orchestrator")
    parser.add_argument("--mode", type=str, default="all", choices=["all", "hub", "edge"], help="Operating mode of the node")
    parser.add_argument("--video_source", type=str, default="0", help="Video source (index or path)")
    args = parser.parse_args()

    print(f"Starting Project Sirens Orchestrator in {args.mode.upper()} mode...")

    video_source = int(args.video_source) if args.video_source.isdigit() else args.video_source

    tasks = []

    if args.mode in ["all", "edge"]:
        tasks.extend([
            process_video_stream(video_source=video_source),
            handle_events(),
            process_audio_chunks(),
            process_audio_input()
        ])

    if args.mode in ["all", "hub"]:
        tasks.extend([
            process_analytics(),
            serve_dashboard(),
            mock_pos_system()
        ])

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOrchestrator shutting down.")