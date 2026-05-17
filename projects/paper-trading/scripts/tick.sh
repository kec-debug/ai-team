#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/_common.sh"

print_banner

STATUS_JSON="$(curl -sS "$BASE_URL/paper/dry-run/status")"

is_running() {
    if [ "$HAS_JQ" -eq 1 ]; then
        echo "$STATUS_JSON" | jq -r '.running // false'
    else
        echo "$STATUS_JSON" | grep -oE '"running"[[:space:]]*:[[:space:]]*(true|false)' \
            | head -1 | awk -F: '{print $2}' | tr -d ' '
    fi
}

RUNNING="$(is_running)"
if [ "$RUNNING" != "true" ]; then
    echo "[tick] dry-run not running; starting first..."
    curl -sS -X POST -H 'content-type: application/json' "$BASE_URL/paper/dry-run/start" -d '{}' \
        | pretty_print
    echo
fi

echo "## POST /paper/dry-run/tick"
curl -sS -X POST -H 'content-type: application/json' "$BASE_URL/paper/dry-run/tick" -d '{"snapshots":[]}' \
    | pretty_print
