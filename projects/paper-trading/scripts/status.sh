#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/_common.sh"

print_banner
echo
echo "## GET /paper/status"
curl -sS -f "$BASE_URL/paper/status" | pretty_print
echo
echo "## GET /paper/dry-run/status"
curl -sS -f "$BASE_URL/paper/dry-run/status" | pretty_print
echo
echo "## GET /ops/status"
curl -sS -f "$BASE_URL/ops/status" | pretty_print || echo "[status] /ops/status not reachable"
echo
echo "## GET /ops/preflight"
curl -sS -f "$BASE_URL/ops/preflight" | pretty_print || echo "[status] /ops/preflight not reachable"
