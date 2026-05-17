#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/_common.sh"

PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

print_banner
echo "[start_server] starting uvicorn on 127.0.0.1:$PORT"
exec .venv/bin/uvicorn app.api.server:app --host 127.0.0.1 --port "$PORT"
