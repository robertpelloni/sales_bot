# TODO

## Immediate (Completed in 0.6.0)
- [x] Redesign Hub Dashboard into a consolidated, intuitive single-page layout with high-value prioritization.
- [x] Implement Desktop System Tray controller (`src/tray_app.py`) with process control and headless fallback.
- [x] Add server health and graceful shutdown endpoints (`GET /api/status`, `POST /api/server/shutdown`).
- [x] Add modular server management scripts (`scripts/run_hub.sh`, `scripts/run_kiosk.sh`, `scripts/run_tray.sh`, `scripts/manage_servers.sh`).
- [x] Modernize FastAPI startup events to `@asynccontextmanager lifespan`.
- [x] Fix Python 3.12 `datetime.datetime.utcnow()` deprecations across backend modules.
- [x] Implement comprehensive unit tests in `tests/test_tray.py` and visual Playwright verification.

## Immediate (Completed in 0.7.0)
- [x] Add real-time WebSocket connection to `hub/main.py` (`/ws/events`) for live event broadcasting to UI without polling.
- [x] Dynamic dashboard live feed insertion and connection status badge in `hub/templates/index.html`.
- [x] Added `test_websocket_event_streaming` in `tests/test_api.py` and visual Playwright verification.

## Completed in 0.8.0
- [x] Implement bounding box distance calibration and proximity calculation in `src/vision.py`.
- [x] Implement 1.5s dwell time locking before triggering VLM customer engagement.
- [x] Extract dominant clothing color heuristics and apparel traits from cropped bounding box frames.
- [x] Package structured metadata JSON with base64 encoded JPEG crops for multimodal context.
- [x] Implement multimodal OpenAI/Gemini chat completions in `src/llm_client.py` with mock fallbacks.
- [x] Implement sentence-level stream chunking (. ! ?) in `src/llm_client.py` for low-latency Piper TTS piping.
- [x] Comprehensive test coverage in `tests/test_vision.py` and `tests/test_conversation.py`.

## Short-Term (0.9.0)
- [ ] Implement Coral Edge TPU compiled TFLite model runner for YOLOv11n in `src/vision.py`.
- [ ] Add dynamic discount rule builder to the Inventory panel for automated volume pricing.

## Long-Term (1.0.0+)
- [ ] Multi-kiosk fleet synchronization via central Redis clustering or gRPC mesh.
- [ ] Automated A/B test convergence engine using multi-armed bandits on customer dwell time.
