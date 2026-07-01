# IDEAS

- Use A/B testing framework to track which cold-opens result in long dwell times.
- Implement hardware-accelerated inferencing using Google Coral Edge TPU or Hailo-8 to speed up YOLOv11n bounding box tracking natively.
- Provide a unified WebSocket output stream from `hub/main.py` so external web clients can view the live bounding box detections or TTS outputs.
- Cache common VLM text strings to save on OpenAI API usage costs during high traffic retail periods.
