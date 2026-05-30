#!/bin/bash
# DEPRECATED: Watchdog is now part of Morpheus Daemon.
# Redirecting to unified daemon entry point.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "run_watchdog_daemon.sh is deprecated - Watchdog now runs inside Morpheus."
echo "Delegating to run_morpheus.sh..."
bash "$SCRIPT_DIR/run_morpheus.sh"
