# DEPLOY

## Docker Compose Orchestration

Project Sirens relies on a multi-container architecture. Use the following baseline to deploy the stack:

- `hub`: FastAPI/Uvicorn web dashboard handling configuration, simulations, and the SQLite CRM database. Exposed on **Port 8000**.
- `kiosk`: Core Python asynchronous pipeline (`src/main.py`) handling vision tracking, API streams, and TTS loops.
- `redis`: In-memory Redis pub/sub broker handling IPC messaging between the VLM chunker and the TTS processes.

**Data Persistence:**
To ensure CRM data (`sirens.db`) and runtime configurations (`system_config.json`, `inventory.json`) survive container restarts, you **must mount local volumes** to `/app/config` and the hub directory.

## Hardware & System Configuration

- **LLM API**: Pass `OPENAI_API_KEY` into the `hub` UI or as an environment variable in the `docker-compose.yml`.
- **Vision Tracking**: To utilize local webcams or Pi camera modules, toggle `USE_MOCK_VISION` to false via the UI. You **must** ensure device passthrough (`--device=/dev/video0`) is active if running the Kiosk inside docker, or execute the Kiosk natively on Raspberry Pi OS.
- **Audio Output**: The Pi 5 implementation requires ALSA/PipeWire routing. Ensure the user running the `kiosk` container has audio group permissions to utilize `subprocess.PIPE` cleanly.

## CI/CD Pipeline & GitHub Secrets

The repository utilizes GitHub Actions (`.github/workflows/ci.yml`) to automatically execute the Pytest integration suite on all merges to `main`. To fully utilize the automated `deploy-staging` job, repository administrators must provision the following secrets in the GitHub Repo Settings:

- `STAGING_SSH_KEY`: The private key used by the runner to SSH into the remote hardware or cloud Hub VM.
- `STAGING_HOST`: The IP address or DNS record of the target machine.
- *(Optional)* `OPENAI_API_KEY`: Only required in the GitHub runner environment if future unit tests drop the `MockRedis` isolation in favor of hitting live Frontier VLM endpoints.
