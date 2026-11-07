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

## Completed in 0.9.0
- [x] Implement Multi-Armed Bandit engine (`hub/ab_engine.py`) using Thompson Sampling and $\epsilon$-greedy strategies.
- [x] Wire live interaction database conversion events and feedback ratings into Bayesian $(\alpha, \beta)$ distributions.
- [x] Expose REST endpoints (`GET /api/ab/allocations`, `POST /api/ab/select_framework`) for dynamic kiosk querying.
- [x] Add high-value dashboard optimization card with live win rate badges and parameter metrics.
- [x] Visual Playwright verification and unit/integration tests (`tests/test_ab_engine.py`, `tests/test_api.py`).

## Completed in 1.0.0
- [x] Implement Multi-Armed Bandit engine (`hub/ab_engine.py`) with Thompson Sampling and $\epsilon$-greedy strategies.
- [x] Implement Coral Edge TPU compiled TFLite model runner for YOLOv11n in `src/vision.py` with Ultralytics and `tflite_runtime` delegate fallbacks.
- [x] Integrate REST endpoints (`/api/ab/allocations`, `/api/ab/select_framework`) and dashboard card.

## Completed in 1.1.0
- [x] Add dynamic promotional discount rule builder to the Inventory panel for automated volume and condition-triggered pricing.
- [x] Integrate active promotional campaigns into LLM sales prompt synthesis (`src/llm_client.py`).
- [x] Add interactive promotion management UI in dashboard with badges, trigger tags, and tooltip guidance.
- [x] Add Playwright visual verification and test suite expansion (`tests/test_promotions.py`, `tests/test_api.py`).

## Completed in 1.2.0
- [x] Implement streaming CSV export endpoint (`GET /api/leads/export`) with query filtering (`all=true` or qualified leads only).
- [x] Expose aggregated analytics summary endpoint (`GET /api/analytics/summary`) calculating conversion percentages, avg latency, and avg feedback score.
- [x] Wire CSV export buttons (`Export Leads (CSV)`, `All Logs`) into dashboard Live CRM Feed & Analytics header.
- [x] Add test suite (`tests/test_leads_export.py`) and visual Playwright UI verification.

## Completed in 1.3.0
- [x] Implement multi-algorithm bandit optimization with Upper Confidence Bound (UCB1) and Epsilon-Greedy with geometric decay in `hub/ab_engine.py`.
- [x] Compute and display 95% Wilson confidence intervals across all candidate sales framework arms.
- [x] Expose REST endpoints `POST /api/ab/config` and `POST /api/ab/reset` for runtime hyperparameter tuning.
- [x] Connect bandit algorithm selection controls and state reset triggers to dashboard UI.
- [x] Enable autonomous dynamic framework routing in simulated detections (`hub/main.py`).

## Completed in 1.4.0
- [x] Implement Contextual Multi-Armed Bandit arm selection in `hub/ab_engine.py` (`calculate_context_affinity`, `select_contextual`).
- [x] Wire vision sensory attributes (proximity distance and dwell time) into framework affinity heuristics.
- [x] Update REST API `/api/ab/select_framework` to accept contextual parameters and return affinity metrics.
- [x] Wire contextual bandit allocation into simulated detections (`/simulate_detection`).
- [x] Add Contextual Weighting toggle switch and active indicators in `hub/templates/index.html`.
- [x] Expand test suite with 3 comprehensive tests in `tests/test_ab_engine.py`.

## Completed in 1.5.0
- [x] Implement asynchronous outbound CRM Webhook Relay engine (`hub/webhooks.py`) with HMAC-SHA256 signature verification.
- [x] Wire non-blocking webhook dispatches into customer interaction creation and lead qualification lifecycle hooks.
- [x] Add REST configuration endpoints (`GET /api/webhooks/config`, `POST /api/webhooks/config`, `POST /api/webhooks/test`) and form handler (`POST /update_webhooks`).
- [x] Build External CRM Webhook Relay dashboard card in `hub/templates/index.html` with real-time test dispatch button.
- [x] Write comprehensive test suite in `tests/test_webhooks.py` with 100% pass rate.
- [x] Visual Playwright screenshot and UI verification.

## Completed in 1.5.1
- [x] Implement sensory condition dynamic promotional matching (`match_promotions`) in `src/llm_client.py`.
- [x] Synthesize empirical Multi-Armed Bandit win rates and 95% Wilson confidence bounds directly into VLM system prompts (`construct_system_prompt`).
- [x] Enrich multimodal chat content and fallback pitches with matched promotional discounts and scarcity directives.
- [x] Connect bandit telemetry into simulation pipeline (`POST /simulate_detection` in `hub/main.py`).
- [x] Expand automated test coverage with tests in `tests/test_promotions.py` and `tests/test_conversation.py`.

## Short-Term (1.6.0)
- [ ] Multi-kiosk fleet synchronization via central Redis clustering or gRPC mesh.
- [ ] Customer interaction replay and synthetic voice evaluation loop.
