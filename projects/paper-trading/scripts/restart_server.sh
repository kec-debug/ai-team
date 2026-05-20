#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
"$SCRIPT_DIR/stop_server.sh"
sleep 1
exec "$SCRIPT_DIR/start_server.sh" "$@"
