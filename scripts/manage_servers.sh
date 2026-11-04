#!/usr/bin/env bash
# manage_servers.sh - Central control utility to start, stop, or inspect Sirens servers
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

PID_DIR="/tmp/sirens_pids"
mkdir -p "${PID_DIR}"

HUB_PID_FILE="${PID_DIR}/hub.pid"
KIOSK_PID_FILE="${PID_DIR}/kiosk.pid"

is_running() {
    local pid_file="$1"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

start_hub() {
    if is_running "$HUB_PID_FILE"; then
        echo "✅ Hub is already running (PID: $(cat "$HUB_PID_FILE"))."
    else
        echo "🚀 Starting Hub in background..."
        cd "$ROOT_DIR"
        nohup python3 -m uvicorn hub.main:app --host 0.0.0.0 --port 8000 > /tmp/sirens_hub.log 2>&1 &
        echo $! > "$HUB_PID_FILE"
        echo "✅ Hub started (PID: $(cat "$HUB_PID_FILE"))."
    fi
}

stop_hub() {
    if is_running "$HUB_PID_FILE"; then
        local pid=$(cat "$HUB_PID_FILE")
        echo "🛑 Stopping Hub (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        rm -f "$HUB_PID_FILE"
        echo "✅ Hub stopped."
    else
        echo "ℹ️  Hub is not running."
        rm -f "$HUB_PID_FILE"
    fi
}

start_kiosk() {
    if is_running "$KIOSK_PID_FILE"; then
        echo "✅ Kiosk is already running (PID: $(cat "$KIOSK_PID_FILE"))."
    else
        echo "👁️ Starting Kiosk in background..."
        cd "$ROOT_DIR"
        nohup python3 src/main.py > /tmp/sirens_kiosk.log 2>&1 &
        echo $! > "$KIOSK_PID_FILE"
        echo "✅ Kiosk started (PID: $(cat "$KIOSK_PID_FILE"))."
    fi
}

stop_kiosk() {
    if is_running "$KIOSK_PID_FILE"; then
        local pid=$(cat "$KIOSK_PID_FILE")
        echo "🛑 Stopping Kiosk (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        rm -f "$KIOSK_PID_FILE"
        echo "✅ Kiosk stopped."
    else
        echo "ℹ️  Kiosk is not running."
        rm -f "$KIOSK_PID_FILE"
    fi
}

status_all() {
    echo "=== Project Sirens Server Status ==="
    if is_running "$HUB_PID_FILE"; then
        echo "  Hub:   RUNNING (PID: $(cat "$HUB_PID_FILE")) [http://localhost:8000]"
    else
        echo "  Hub:   STOPPED"
    fi

    if is_running "$KIOSK_PID_FILE"; then
        echo "  Kiosk: RUNNING (PID: $(cat "$KIOSK_PID_FILE"))"
    else
        echo "  Kiosk: STOPPED"
    fi
}

case "$1" in
    start)
        start_hub
        start_kiosk
        ;;
    stop)
        stop_kiosk
        stop_hub
        ;;
    restart)
        stop_kiosk
        stop_hub
        sleep 1
        start_hub
        start_kiosk
        ;;
    status)
        status_all
        ;;
    start-hub)
        start_hub
        ;;
    stop-hub)
        stop_hub
        ;;
    start-kiosk)
        start_kiosk
        ;;
    stop-kiosk)
        stop_kiosk
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|start-hub|stop-hub|start-kiosk|stop-kiosk}"
        exit 1
        ;;
esac
