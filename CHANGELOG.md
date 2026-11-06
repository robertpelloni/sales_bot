# CHANGELOG

## [1.3.0] - Multi-Armed Bandit Algorithmic Refinement & Dynamic Routing
- **Multi-Algorithm Optimization Engine (`hub/ab_engine.py`)**: Expanded Multi-Armed Bandit capabilities beyond Thompson Sampling to include Upper Confidence Bound (UCB1) and Epsilon-Greedy with geometric exploration decay.
- **Exploration Decay & Floor (`decay_epsilon`)**: Automatically decays exploration epsilon ($\epsilon \cdot \text{decay\_rate}$) down to a configurable minimum boundary ($\text{min\_\epsilon}$).
- **95% Confidence Interval Tracking**: Wilson score / normal approximation confidence bounds (`ci_lower`, `ci_upper`) computed and displayed alongside empirical win rates.
- **Bandit Configuration & Reset Endpoints (`hub/main.py`)**: Added `POST /api/ab/config` and `POST /api/ab/reset` for runtime algorithmic hyperparameter tuning.
- **Dynamic Simulation Framework Routing**: Integrated bandit allocation directly into `/simulate_detection` with an "auto" framework selection toggle.
- **Dashboard Bandit Controls (`hub/templates/index.html`)**: Interactive form controls for tuning algorithm strategy, exploration rate, decay parameters, and instant learning state reset.

## [1.2.0] - CRM Leads CSV Export & Real-Time Analytics Reporting
- **Streaming CRM CSV Export (`hub/main.py`)**: Implemented `GET /api/leads/export` supporting RFC 4180 streaming CSV downloads with headers, sanitization, and optional query filtering (`all=true` for full logs or default qualified leads).
- **Aggregated Analytics Summary API (`hub/main.py`)**: Added `GET /api/analytics/summary` computing real-time metrics including total interactions, qualified leads count, conversion percentage, average TTS audio latency, and average pitch feedback score.
- **CRM Dashboard Export Actions (`hub/templates/index.html`)**: Added dedicated "Export Leads (CSV)" and "All Logs" download action buttons directly into the Live CRM Feed & Analytics card header with tooltips and responsive styling.
- **Analytics & Export Test Suite (`tests/test_leads_export.py`)**: Added comprehensive tests verifying CSV formatting, lead/all filtering, and analytics summary metrics.

## [1.1.0] - Dynamic Store Promotions Engine & Retail Prompt Synthesis
- **Dynamic Store Promotions Backend (`config/inventory.json`, `hub/main.py`)**: Added support for dynamic promotional incentive rules (`rule_name`, `discount_percent`, `trigger_type`, `threshold`, `description`). Implemented `POST /add_promotion` and `POST /delete_promotion/{promo_index}` endpoints using Post/Redirect/Get patterns and UI error handling.
- **Multimodal Prompt Promotion Synthesis (`src/llm_client.py`)**: Wired promotional rules into `construct_system_prompt()`, enabling autonomous sales agents to inject active discounts into cold-open pitches and dwell-time offers.
- **Dynamic Promotions Dashboard UI (`hub/templates/index.html`)**: Added dedicated "Active Store Promotions & Dynamic Discounts" management section with promotional badge overlays, trigger conditions, removal actions, and an interactive addition form with tooltip markers.
- **E2E & Unit Testing Expansion (`tests/test_promotions.py`, `tests/test_api.py`)**: Added tests validating promotional prompt formatting, REST endpoint operations, and updated system status schema reporting `active_promotions_count`.

## [1.0.0] - Multi-Armed Bandit Dynamic A/B Sales Engine & Edge Vision Acceleration
- **Bayesian Multi-Armed Bandit Core (`hub/ab_engine.py`)**: Implemented `MultiArmedBanditEngine` supporting Thompson Sampling (`random.betavariate(alpha, beta)`) and $\epsilon$-greedy framework allocation over live interaction lead conversions and pitch feedback ratings.
- **Dynamic Framework Allocation Endpoints (`hub/main.py`)**: Added `GET /api/ab/allocations` returning real-time trial counts, lead win rates, feedback averages, and Beta prior distributions, plus `POST /api/ab/select_framework` for autonomous interaction-time strategy assignment.
- **Dashboard Optimization UI (`hub/templates/index.html`)**: Added dedicated "Automated A/B Sales Framework Optimization" card displaying live conversion rate pills, Bayesian Beta parameter metrics ($\alpha$, $\beta$), and contextual explanatory tooltips.
- **Hardware Vision Edge TPU / TFLite Acceleration (`src/vision.py`)**: Enhanced `load_vision_model()` to detect and load Coral Edge TPU models (`yolo11n_edgetpu.tflite` or custom paths) via Ultralytics TFLite backend and direct `tflite_runtime.interpreter.Interpreter` delegate initialization (`libedgetpu.so.1`) before falling back to PyTorch and MockYOLO.

## [0.9.0] - Multi-Armed Bandit Dynamic A/B Sales Testing Engine
- **Bayesian Multi-Armed Bandit Core (`hub/ab_engine.py`)**: Implemented `MultiArmedBanditEngine` supporting Thompson Sampling (`random.betavariate(alpha, beta)`) and $\epsilon$-greedy framework allocation over live interaction lead conversions and pitch feedback ratings.
- **Dynamic Framework Allocation Endpoints (`hub/main.py`)**: Added `GET /api/ab/allocations` returning real-time trial counts, lead win rates, feedback averages, and Beta prior distributions, plus `POST /api/ab/select_framework` for autonomous interaction-time strategy assignment.
- **Dashboard Optimization UI (`hub/templates/index.html`)**: Added dedicated "Automated A/B Sales Framework Optimization" card displaying live conversion rate pills, Bayesian Beta parameter metrics ($\alpha$, $\beta$), and contextual explanatory tooltips.
- **A/B Engine Test Suite (`tests/test_ab_engine.py`, `tests/test_api.py`)**: Validated Bayesian convergence, exploitation vs. exploration mechanics, and HTTP REST endpoint integrity across unit and integration tests.

## [0.8.0] - Vision Feature Extraction & Multimodal Frontier VLM Integration
- **Distance Calibration & Proximity Estimation (`src/vision.py`)**: Implemented `calculate_proximity` inverse distance modeling mapped against frame height ratios (close ≤1.2m, mid-range 1.2–2.5m, far >2.5m).
- **Temporal Dwell Lock (>1.5s) (`src/vision.py`)**: Added `is_target_dwelling` tracking target persistence before triggering conversational locks.
- **Visual Attribute & Color Heuristics (`src/vision.py`)**: Built `extract_visual_attributes` parsing torso HSV values to identify broad outerwear colors and apparel categories without violating privacy guidelines.
- **Multimodal Frontier VLM Pipeline (`src/llm_client.py`)**: Implemented `format_multimodal_user_content` and updated `generate_sales_response` to package structured metadata alongside compressed base64 JPEG crops to OpenAI/Gemini chat completions.
- **Low-Latency Stream Chunking (`src/llm_client.py`)**: Added `chunk_text_stream` splitting token streams on punctuation marks (. ! ?) for low-latency Piper TTS audio piping.
- **Comprehensive Test Suite**: Added granular unit tests in `tests/test_vision.py` and `tests/test_conversation.py` with 100% test pass rate across 23 tests.

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
