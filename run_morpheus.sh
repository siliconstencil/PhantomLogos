#!/bin/bash
# Morpheus VRAM Management Daemon (Bash Launcher)
# Stop: scripts/stop_morpheus.sh (if exists) or kill PID

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR"
export PYTHONWARNINGS="ignore::FutureWarning:google.generativeai"

LOG_DIR="$SCRIPT_DIR/logs/system/morpheus"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/morpheus.log"
PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
SCRIPT="$SCRIPT_DIR/src/clotho/bootstrap.py"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "[ERROR] python not found at $PYTHON_BIN"
    exit 1
fi
if [ ! -f "$SCRIPT" ]; then
    echo "[ERROR] bootstrap.py not found at $SCRIPT"
    exit 1
fi

echo "Starting Morpheus Daemon in background..."
nohup "$PYTHON_BIN" -u "$SCRIPT" --daemon >> "$LOG_FILE" 2>&1 &
PID=$!

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ====== New session starting PID:$PID ======" >> "$LOG_FILE"
sleep 2

if ! kill -0 $PID 2>/dev/null; then
    echo "[ERROR] Morpheus PID:$PID terminated early."
    tail -n 10 "$LOG_FILE"
    exit 1
else
    echo "[OK] Morpheus is running in background (PID:$PID)."
fi
