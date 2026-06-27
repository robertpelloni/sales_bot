# DEPLOY
## Requirements
- Hardware: Raspberry Pi 5 (8GB) or generic Linux/x86_64 edge node.
- OS: Debian-based Linux (Raspberry Pi OS Bookworm 64-bit recommended)
- Dependencies: `docker`, `docker-compose`

## Containerized Setup (Recommended)
1. Clone the repository with submodules: `git clone --recursive <repo_url>`
2. Export your LLM API Key: `export OPENAI_API_KEY="your-key-here"`
3. Spin up the cluster: `docker-compose up --build -d`

*Note: The docker-compose passes through `/dev/video0` automatically. Ensure your webcam is plugged in before starting.*

## Manual Bare-Metal Setup
1. Clone the repository with submodules: `git clone --recursive <repo_url>`
2. Install system dependencies: `sudo apt-get install redis-server build-essential cmake libgl1-mesa-glx alsa-utils`
3. Install Python requirements: `pip install -r requirements.txt`
4. Start Redis: `redis-server --daemonize yes`
5. Run the orchestrator: `python -m src.main`
