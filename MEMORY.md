# MEMORY

- Using Python 3.11+
- Edge-Cloud Split Architecture
- Redis pub/sub broker for inter-process communication
- Privacy Directive: Never save images or video frames to disk. Delete bounding box memory buffers every 60 seconds.
- Security Directive: Never interpolate LLM-generated text directly into shell commands. Always use `stdin`.
- `OPENAI_API_KEY` and `USE_MOCK_VISION` are toggled at runtime via the `hub` API (`/update_system_config`), persisting across app states without requiring `.env` hardcoding.
- Pytest environments require active pruning of dynamic `os.environ` keys so LLM logic doesn't override mocks unexpectedly.
- Submodules (`vendor/piper`, `vendor/yolov11-edge`) must be updated recursively whenever major architectural branch changes are merged to prevent orphaned paths.
