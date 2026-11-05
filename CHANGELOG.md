# CHANGELOG

## [0.3.0] - Persistent CRM Logging, Lead Tracking, & UI Redesign
- Added persistent conversation storage using an SQLite database (via SQLAlchemy) to log customer interactions.
- Integrated Lead Tracking: interactions can now be flagged as qualified leads via `/mark_lead` and attached with follow-up persistence notes via `/update_follow_up`.
- Created a new `/api/log_interaction` webhook endpoint in the Hub to receive VLM Streamer events asynchronously.
- Added visual analytics via Chart.js to the Dashboard tracking conversation frequency over time.
- Completely redesigned the Hub Dashboard into a dense, unified single-page layout utilizing CSS grids and detailed tooltip helpers.
- Implemented robust Post/Redirect/Get (PRG) patterns for all configuration form endpoints and added visible `error_message` rendering states for users.
- Updated requirements.txt with explicitly pinned backend dependencies (`fastapi==0.139.0`, `playwright==1.61.0`, `sqlalchemy`, `httpx`, `pandas`).

## [0.2.0] - LLM Integration & System Config
- Integrated OpenAI API client for live VLM streams, overriding mock logic when `OPENAI_API_KEY` is present.
- Refactored `start_vision_loop` to attempt `cv2.VideoCapture(0)` hardware mapping when `USE_MOCK_VISION` is false.
- Added System Configuration routing to the Hub API for runtime toggle of hardware mocks and live API keys.
- Enhanced `tests/test_conversation.py` to prevent environment variables from bleeding into assertions.

## [0.1.1] - Hub UI Array Enhancements
- Expanded Hub HTML template with comprehensive form components for Inventory Items, Tactics Enforced, and Constraints.
- Added descriptive tooltips to all configuration elements.

## [0.1.0] - Initial Setup
- Initialized documentation files
- Set up directory structure and configurations
- Added git submodules (vendor/piper, vendor/yolov11-edge)
- Created docker-compose infrastructure
- Implemented core components: hub, main orchestrator, vision, llm_client, and audio_output

## [0.2.1] - Integration Testing & Follow-Ups
- Built complete E2E `pytest` integration test pipeline to protect Hub UI routes (`tests/test_api.py`).
- Documented follow-up requirements inside `TODO.md` for extended simulation testing parameters.
