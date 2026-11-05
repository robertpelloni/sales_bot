#!/usr/bin/env bash
# run_kiosk.sh - Launches the Project Sirens edge vision & speech orchestrator
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"
echo "👁️  Starting Project Sirens Kiosk pipeline..."
exec python3 src/main.py
