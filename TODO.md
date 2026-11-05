# TODO

## Immediate
- [x] Implement actual LLM API client (OpenAI) in `src/llm_client.py` using `chat.completions.create(stream=True)`.
- [x] Add API Key configuration to `hub/templates/index.html` and `hub/main.py` so users can dynamically set their LLM keys.
- [x] Refactor `src/vision.py` to allow reading from a real camera device (`cv2.VideoCapture`) instead of a simulated loop. Add a "Mock Mode" flag for testing.
- [x] Expose Camera configuration (Device index/ID) in the Hub dashboard.

## Short-Term
- [x] Add a visual log/feed to the Dashboard showing recently detected customers and the responses generated.
- [x] Allow deleting items, tactics, and constraints from the UI.
- [x] Add optional simulation parameter configuration (e.g. LLM temperature or explicit system prompt overrides) inside the Hub UI's "Simulate Detection" form for deeper A/B testing.

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

## Short-Term (1.0.0)
- [ ] Implement Coral Edge TPU compiled TFLite model runner for YOLOv11n in `src/vision.py`.
- [ ] Add dynamic discount rule builder to the Inventory panel for automated volume pricing.

## Long-Term (1.1.0+)
- [ ] Multi-kiosk fleet synchronization via central Redis clustering or gRPC mesh.
- [ ] Multi-armed bandit reward convergence on customer dwell time alongside explicit lead conversion.
