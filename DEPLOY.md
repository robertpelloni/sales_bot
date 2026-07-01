# DEPLOY

Docker Compose deployment:
- `hub`: FastAPI/Uvicorn dashboard + SQLite for analytics (Port 8000)
- `kiosk`: core Python asynchronous pipeline
- `redis`: in-memory Redis service

System Configuration:
- To leverage live API models, pass `OPENAI_API_KEY` into the `hub` UI or docker environment.
- To utilize local webcams/Pi camera modules, toggle `USE_MOCK_VISION` to false. Ensure device passthrough (`--device=/dev/video0`) is active if running inside docker, or run natively on Raspberry Pi OS.
