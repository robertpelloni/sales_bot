# ROADMAP

- Phase 1: Initial implementation of Sirens Project (Completed 0.1.1)
  - Edge and Hub architecture setup
  - Mock YOLOv11 and Piper TTS integration via stdin
  - Configuration wiring and Hub dashboard implementation

- Phase 2: Production APIs & Real Vision (Completed 0.2.0)
  - Replace mock `generate_sales_response` with a true Frontier VLM integration (e.g. OpenAI/Gemini SDKs).
  - Transition `start_vision_loop` from a 10-iteration simulated loop to capturing actual video device frames (e.g., `/dev/video0`).
  - Connect configuration dashboard to save API keys to `.env` or secure config for LLM usage.

- Phase 3: Hardware Deployment
  - Refine PipeWire/ALSA configurations.
  - Profile performance on Pi 5 / Coral Edge TPU.
