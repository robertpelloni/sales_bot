# CHANGELOG

## [0.8.0] - Coral Edge TPU Hardware Acceleration & Dynamic Promotion Rules Engine
- **Coral Edge TPU Hardware Acceleration (`src/vision.py`)**: Added `load_vision_model` helper preferentially loading Edge TPU compiled TFLite models (`yolo11n_edgetpu.tflite` via `edgetpu` lib) to prevent thermal throttling on edge devices (Raspberry Pi 5 / Coral Accelerator), falling back to PyTorch `yolo11n.pt` and graceful `MockYOLO`.
- **Dynamic Promotions & Automated Discount Engine**: Extended `config/inventory.json` schema with automated promotion rules (`rule_name`, `discount_percent`, `trigger_type`, `threshold`, `description`).
- **Hub Promotion Endpoints & UI Controls**: Implemented `POST /add_promotion` and `POST /delete_promotion/{promo_index}` endpoints using the PRG pattern, rendering interactive rule management and dynamic badges directly inside the unified dashboard.
- **Top-level Import Hygiene & Dependency Hardening**: Ensured all imports in vision modules reside cleanly at top of files; installed `opencv-python-headless` for headless container/CI environments.
- **Vision & Promotion Test Suite**: Added `tests/test_vision.py` and `test_add_and_delete_promotion` in `tests/test_api.py` achieving 100% test pass rate across all 18 test cases.

## [0.7.0] - Real-Time WebSocket Streaming & Live CRM Event Push
- **WebSocket Streaming (`/ws/events`)**: Added FastAPI WebSocket route with `ConnectionManager` to push customer interactions directly to connected dashboard clients without polling.
- **Dynamic Dashboard Feed Updates**: Enhanced `hub/templates/index.html` with real-time WebSocket client listener, connection status pill (`WS Stream: Live`), auto-reconnect backoff logic, and instant UI prepending of new interaction cards into the CRM stream.
- **WebSocket Protocol Integration**: Added pinned `websockets` dependency to `requirements.txt` to support Uvicorn WebSocket serving.
- **End-to-End WebSocket Testing**: Added `test_websocket_event_streaming` in `tests/test_api.py` and Playwright visual verification script confirming real-time feed update behavior.

## [0.6.0] - Unified Dashboard Redesign, Desktop Tray Controller & Lifecycle Automation
- **Unified Single-Page Dashboard**: Completely redesigned `hub/templates/index.html` with a modern, responsive, high-value-first layout. Placed real-time system status indicators and server lifecycle controls at the top header, followed by the Simulation Engine and Live CRM Analytics feed with Chart.js charts, and consolidated Product Inventory and Psychology Settings below.
- **Desktop System Tray Controller (`src/tray_app.py`)**: Built a cross-platform system tray manager using `pystray` and `PIL` with dynamic lightning bolt taskbar icon rendering, browser launch shortcuts, server status monitoring, and graceful process shutdown controls. Includes automatic headless/display detection fallback for CI and server deployments.
- **Backend Lifecycle & Modernization**: Refactored `hub/main.py` to use modern FastAPI `@asynccontextmanager lifespan` handlers and replaced deprecated `datetime.utcnow()` with timezone-aware `datetime.now(datetime.UTC)`.
- **Server Health & Shutdown Endpoints**: Added `GET /api/status` for real-time Hub health/configuration checks and `POST /api/server/shutdown` for graceful server process termination.
- **Server Management Scripts**: Added `scripts/manage_servers.sh` (start/stop/restart/status), `scripts/run_hub.sh`, `scripts/run_kiosk.sh`, and `scripts/run_tray.sh`.
- **E2E Test Expansion**: Added `tests/test_tray.py` and updated `tests/test_api.py` to guarantee full coverage of server management, tray status, and dashboard API responses.

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
