# ROADMAP

- Phase 1: Initial implementation of Sirens Project (Completed 0.1.1)
  - Edge and Hub architecture setup
  - Mock YOLOv11 and Piper TTS integration via stdin
  - Configuration wiring and Hub dashboard implementation

- Phase 2: Production APIs & Real Vision (Completed 0.2.0)
  - Replace mock `generate_sales_response` with a true Frontier VLM integration (e.g. OpenAI/Gemini SDKs).
  - Transition `start_vision_loop` from a 10-iteration simulated loop to capturing actual video device frames (e.g., `/dev/video0`).
  - Connect configuration dashboard to save API keys to `.env` or secure config for LLM usage.

- Phase 3: CRM & Engagement Tracking (Completed 0.3.0)
  - Implement SQLite interaction persistence and visual analytics.
  - Expose API endpoints for marking leads and recording follow-ups.
  - Complete integration testing for the VLM/Redis data flow simulation via Playwright and Pytest.

- Phase 4: Hardware Deployment (Completed 0.4.0)
  - Refine PipeWire/ALSA configurations for zero-latency audio streaming.
  - Profile tracking performance on Pi 5 / Coral Edge TPU hardware modules.

- Phase 5: Feedback & Advanced Analytics (Completed 0.5.0)
  - Incorporate text-to-speech latency performance logging into the database.
  - Develop user interaction feedback mechanisms.

- Phase 6: Security & API Authorization
  - Implement FastAPI `HTTPBasic` authentication to protect configuration endpoints.
  - Secure `/api/log_interaction` webhook to prevent unauthorized DB writes.
