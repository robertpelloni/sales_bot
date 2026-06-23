# DEPLOY
## Requirements
- Hardware: Raspberry Pi 5 (8GB)
- OS: Raspberry Pi OS (Bookworm 64-bit)
- Dependencies: `redis-server`, `python3.11+`

## Setup
1. Clone the repository with submodules: `git clone --recursive <repo_url>`
2. Install Python requirements: `pip install -r requirements.txt`
3. Start Redis: `redis-server --daemonize yes`
4. Run the orchestrator: `python src/main.py`
