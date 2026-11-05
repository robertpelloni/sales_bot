# Project Sirens - Master Architecture & Vision

## 1. Ultimate Goal & Core Vision
Project Sirens is a next-generation autonomous retail engagement and conversion system designed for physical brick-and-mortar storefronts. By coupling ultra-low-latency edge computer vision with streaming frontier Vision-Language Models (VLMs) and on-device neural Text-to-Speech (TTS), Project Sirens detects passersby in real-time, infers stylistic and contextual cues (clothing colors, footwear style, carried items, posture), and proactively delivers charismatic, high-converting cold-open sales pitches.

Total target loop latency from physical visual detection to directional audio articulation is **under 1.2 to 1.5 seconds**, preventing any conversational hesitation.

## 2. Foundational Architecture (Edge-Cloud Split)
- **Local Edge Sensing (Raspberry Pi 5 + Sony IMX500 / Coral TPU)**:
  - Continuously executes YOLOv11n lightweight object tracking.
  - Computes spatial proximity and dwell time (>1.5s lock within ~6ft).
  - Emits metadata attribute packets without storing raw video frames or personally identifiable facial biometrics to disk, ensuring rigorous GDPR/CCPA privacy compliance.
- **Inter-Process Communication (In-Memory Redis Pub/Sub)**:
  - Decouples sensing, reasoning, and speech pipelines across independent asynchronous event loops.
- **Cloud Reasoning (Frontier VLM SSE Streaming)**:
  - Takes macro attribute packets and generates context-aware, pattern-interrupt sales hooks informed by retail psychology principles (anchoring, assumptive closes, Ben Franklin close, scarcity).
- **Edge Speech Synthesis (Piper ONNX Engine via ALSA/PipeWire)**:
  - Streams incoming VLM sentence tokens directly into local neural TTS subprocesses, playing audio while downstream tokens are still generating to hide round-trip network latency.
- **Central Control & Intelligence Hub (FastAPI + Async SQLAlchemy + SQLite WAL)**:
  - Provides a single-page management dashboard for store inventory, conversion psychology rules, real-time detection simulation, and persistent CRM interaction tracking.
- **Desktop System Tray Controller (`src/tray_app.py`)**:
  - Provides background server status monitoring, quick dashboard browser launching, and graceful shutdown/quit controls with headless fallback support.
