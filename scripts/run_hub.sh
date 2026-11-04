#!/usr/bin/env bash
# run_hub.sh - Launches the Project Sirens FastAPI/Uvicorn Hub server
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"
echo "🚀 Starting Project Sirens Hub on http://localhost:8000 ..."
exec python3 -m uvicorn hub.main:app --host 0.0.0.0 --port 8000
