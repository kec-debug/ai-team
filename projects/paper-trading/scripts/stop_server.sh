#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/_common.sh"

PORT="${PORT:-8000}"

PIDS=$(pgrep -f "uvicorn app.api.server" || true)
if [ -z "$PIDS" ]; then
    echo "[stop_server] no uvicorn paper-trading server running"
    exit 0
fi

echo "[stop_server] sending SIGTERM to PIDs: $PIDS"
echo "$PIDS" | xargs -r kill -TERM 2>/dev/null || true

for i in 1 2 3 4 5; do
    REMAIN=$(pgrep -f "uvicorn app.api.server" || true)
    if [ -z "$REMAIN" ]; then
        echo "[stop_server] stopped"
        exit 0
    fi
    sleep 1
done

REMAIN=$(pgrep -f "uvicorn app.api.server" || true)
if [ -n "$REMAIN" ]; then
    echo "[stop_server] SIGKILL fallback for PIDs: $REMAIN"
    echo "$REMAIN" | xargs -r kill -KILL 2>/dev/null || true
fi
echo "[stop_server] stopped"
