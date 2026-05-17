#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/_common.sh"

PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
print_banner
echo
echo "## POST /reports/dry-run/analyze"
ANALYZE_JSON="$(curl -sS -X POST -H 'content-type: application/json' "$BASE_URL/reports/dry-run/analyze" -d '{}')"
echo "$ANALYZE_JSON" | pretty_print

echo
echo "## GET /reports/dry-run/latest"
LATEST_JSON="$(curl -sS "$BASE_URL/reports/dry-run/latest")"
echo "$LATEST_JSON" | pretty_print

if [ "$HAS_JQ" -eq 1 ]; then
    RUN_DIR_NAME="$(echo "$LATEST_JSON" | jq -r '.run_dir // empty')"
else
    RUN_DIR_NAME="$(echo "$LATEST_JSON" | grep -oE '"run_dir"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')"
fi

if [ -n "$RUN_DIR_NAME" ]; then
    REPORT_PATH="$PROJECT_DIR/reports/dry_run/$RUN_DIR_NAME/analysis_report.md"
    echo
    echo "[analyze] analysis_report: $REPORT_PATH"
fi
