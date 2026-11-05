#!/usr/bin/env bash
# run_tray.sh - Launches the desktop taskbar system tray controller
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"
echo "⚡ Starting Project Sirens System Tray Controller..."
exec python3 src/tray_app.py
