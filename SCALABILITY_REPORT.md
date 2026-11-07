# Project Sirens: Scalability & Performance Report

## Executive Summary
This report analyzes the performance bottlenecks and scalability limits of the Project Sirens architecture based on the integration of YOLOv11 (Vision), Redis (Pub/Sub), GPT-4o-mini (LLM), and Piper (TTS). The system was designed for an edge-cloud split to achieve sub-second latency, but scaling to multiple edge nodes introduces specific constraints.

## 1. Bottleneck Analysis

### 1.1 Redis Pub/Sub Throughput
*   **Current State:** Redis acts as the central message broker across all microservices (Vision -> LLM, LLM -> Audio).
*   **Observation:** While Redis handles high throughput well, the single-threaded nature of the `redis-py` async client handling JSON serialization/deserialization for large image payloads (base64) can block the event loop under heavy concurrent load from multiple kiosks.
*   **Impact:** Increased Time-To-First-Token (TTFT) as message queuing latency compounds.

### 1.2 Text-to-Speech (Piper) Latency
*   **Current State:** Piper runs locally via subprocess calls (`aplay`).
*   **Observation:** Piper's inference speed on an ARM-based Raspberry Pi 5 is fast enough for real-time *once* the text is received. However, overlapping subprocess calls (if the LLM generates short, rapid sentences) can lead to audio stuttering or dropped frames if the audio buffer isn't managed cleanly.
*   **Impact:** Degraded user experience due to robotic or overlapping speech output.

### 1.3 LLM Client Concurrency
*   **Current State:** The `llm_client.py` uses `asyncio` to handle multiple streams.
*   **Observation:** The OpenAI API rate limits and concurrent connection limits are the primary external bottleneck. A sudden spike in detections across 50 kiosks will exhaust standard tier API limits instantly.
*   **Impact:** 429 Too Many Requests errors, leading to silent failures at the kiosk level.

### 1.4 Edge Processing (YOLOv11)
*   **Current State:** Processing every 3rd frame to save CPU/GPU cycles.
*   **Observation:** Thermal throttling on the Pi 5 during continuous inference drops framerates, leading to missed proximity triggers or delayed attribute extraction.
*   **Impact:** Inconsistent customer engagement.

## 2. Recommended Optimizations (Proposed Architecture V2)

1.  **Payload Offloading:** Stop sending base64 images through Redis pub/sub. Instead, write images to an ephemeral RAM disk (`/tmpfs`) or a fast object store, and only pass the URI through Redis.
2.  **Audio Buffer Management:** Implement a proper audio queuing system (e.g., using `pyaudio` or `sounddevice`) in Python rather than relying on raw `subprocess.Popen` with `aplay`, allowing for seamless stitching of TTS chunks.
3.  **LLM Request Batching/Caching:** Implement semantic caching for common combinations of visual attributes to serve pre-generated pitches instantly without hitting the OpenAI API.
4.  **Hardware Acceleration:** Transition from raw YOLO execution to a quantized TensorRT engine specific to the Pi AI Camera hardware to reduce thermal load.
