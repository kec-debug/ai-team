#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/_common.sh"

print_banner
echo
echo "## POST /paper/dry-run/stop"
curl -sS -X POST -H 'content-type: application/json' "$BASE_URL/paper/dry-run/stop" -d '{}' | pretty_print
