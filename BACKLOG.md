# Project Sirens: Prioritized Performance Backlog

This backlog outlines the necessary engineering tasks to scale the Project Sirens architecture from a single prototype to a multi-kiosk production deployment.

## High Priority (Critical for Stability)

- [ ] **Redis Payload Optimization:** Refactor `vision.py` and `llm_client.py` to utilize RAM disk (`/tmpfs`) for image passing instead of embedding base64 strings directly in Redis pub/sub payloads.
- [ ] **Audio Queue Manager:** Replace the `subprocess` + `aplay` execution in `audio_output.py` with a dedicated thread-safe audio queue using `pyaudio` to ensure smooth TTS playback of rapid chunks.
- [ ] **API Rate Limit Handling:** Implement exponential backoff and retry logic in `llm_client.py` to gracefully handle OpenAI HTTP 429 errors.

## Medium Priority (Performance & UX)

- [ ] **Semantic Caching Layer:** Integrate `Redisearch` or a local vector DB to cache LLM responses for common visual profiles (e.g., "red jacket", "casual wear") to bypass the LLM API and achieve near-zero latency for frequent profiles.
- [ ] **TensorRT Quantization:** Convert the YOLOv11 PyTorch model to a TensorRT engine optimized for the Raspberry Pi AI Camera to reduce CPU load and prevent thermal throttling.
- [ ] **Connection Pooling:** Implement connection pooling for the SQLite database in `analytics.py` to prevent locking issues under high concurrent write loads from multiple kiosks.

## Low Priority (Long-Term Scaling)

- [ ] **Kubernetes Migration:** Transition from `docker-compose` to a lightweight Kubernetes distribution (K3s) for the Hub service to allow automatic horizontal scaling of the analytics and LLM routing tiers.
- [ ] **Telemetry Dashboard:** Add Prometheus/Grafana integration to the Hub to visualize Redis queue depth, API latency, and Pi thermal metrics in real-time.
