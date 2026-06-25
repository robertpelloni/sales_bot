# CHANGELOG
## [0.3.0] - Vendor Dashboard Integration
- Added `src/dashboard.py` (FastAPI) allowing vendors to view real-time funnel analytics.
- Integrated dashboard webserver into the main event loop.

## [0.2.0] - Analytics & Conversational Upgrades
- Created `src/analytics.py` for SQLite tracking of the conversion funnel.
- Implemented real-time dynamic system prompts based on total conversion feedback loop.

## [0.1.1] - Minor Updates
- Integrated Piper TTS subprocess calls into `src/audio_output.py`.

## [0.1.0] - Initial Build
- Created core asynchronous orchestrator.
- Integrated YOLOv11 for local computer vision tracking.
- Set up streaming LLM client with OpenAI API.
- Implemented TTS chunking pipeline.
