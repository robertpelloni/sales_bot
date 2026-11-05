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

- Phase 6: Unified Dashboard, System Tray & Lifecycle Automation (Completed 0.6.0)
  - Redesign dashboard into a high-value single-page grid layout with comprehensive tooltips and status bar.
  - Add desktop system tray controller (`src/tray_app.py`) with process management and graceful shutdown.
  - Expose `/api/status` and `/api/server/shutdown` endpoints.
  - Provide unified server management scripts in `scripts/`.

- Phase 7: Real-Time WebSocket Streaming & Dynamic Feed (Completed 0.7.0)
  - Real-time duplex WebSocket stream (`/ws/events`) with `ConnectionManager`.
  - Push new customer interaction events directly to the dashboard DOM without polling.
  - Visual Playwright E2E verification of live feed card insertion.

- Phase 8: Vision Feature Extraction & Multimodal Frontier VLM Integration (Completed 0.8.0)
  - Calibrated bounding box proximity estimation and 1.5s dwell time locking.
  - Extracted dominant apparel color heuristics and packaged metadata with base64 JPEG crops.
  - Integrated multimodal OpenAI/Gemini chat completions with sentence-level stream chunking for Piper TTS.

- Phase 9: Multi-Armed Bandit Dynamic A/B Sales Testing Engine (Completed 0.9.0)
  - Autonomous strategy allocation using Thompson Sampling (Beta priors) and $\epsilon$-greedy exploration.
  - Integration with CRM conversion events (leads flagged, feedback ratings).
  - High-value dashboard card with live arm win rates and parameter introspection.
  - REST endpoints (`/api/ab/allocations`, `/api/ab/select_framework`) for dynamic kiosk querying.

- Phase 10: Edge Hardware Acceleration & Coral Edge TPU Support (Completed 1.0.0)
  - Support Coral Edge TPU TFLite runtime models (`yolo11n_edgetpu.tflite`) via Ultralytics backend and `tflite_runtime.interpreter.Interpreter` delegate initialization.
  - Hardened MockYOLO fallback for zero-dependency CI execution.

- Phase 11: Dynamic Store Promotions & Retail Prompt Synthesis (Completed 1.1.0)
  - Dynamic store promotions backend engine with discount rules, threshold conditions, and PRG UI forms.
  - Autonomous LLM prompt synthesis of active promotional campaigns into cold-open and dwell-time pitches.
  - Interactive promotions management panel in the consolidated dashboard.

- Phase 12: Multi-Kiosk Fleet Synchronization & Distributed Mesh (Planned 1.2.0)
  - Distributed SQLite sync via Litestream or Raft-backed Redis cluster across multi-kiosk storefront networks.
  - Cross-kiosk customer trajectory handover with privacy-preserving appearance embeddings.
