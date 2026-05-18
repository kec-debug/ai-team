#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/_common.sh"

echo "===== smoke_check ====="
print_banner
echo

echo "----- status -----"
"$SCRIPT_DIR/status.sh" || true
echo

echo "----- start dry-run -----"
"$SCRIPT_DIR/start_dry_run.sh" || true
echo

echo "----- tick -----"
"$SCRIPT_DIR/tick.sh" || true
echo

echo "----- analyze -----"
"$SCRIPT_DIR/analyze.sh" || true
echo

echo "----- latest -----"
curl -sS "$BASE_URL/reports/dry-run/latest" | pretty_print || true
echo

echo "----- stop dry-run -----"
"$SCRIPT_DIR/stop_dry_run.sh" || true
