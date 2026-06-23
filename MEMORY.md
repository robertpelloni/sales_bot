# MEMORY
- Project Architecture: Hybrid Edge-Cloud Split Architecture.
- Local Edge: Vision (YOLOv11), Wake/Trigger State Machine, Audio capture/output (Piper TTS).
- Cloud: Low-latency Frontier Vision-Language Model (VLM) for conversational generation.
- IPC: In-memory Redis pub/sub broker to handle asynchronous microservices.
