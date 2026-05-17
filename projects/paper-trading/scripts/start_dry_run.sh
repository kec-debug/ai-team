#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/_common.sh"

print_banner
echo
echo "## POST /paper/dry-run/start"
curl -sS -X POST -H 'content-type: application/json' "$BASE_URL/paper/dry-run/start" -d '{}' | pretty_print
