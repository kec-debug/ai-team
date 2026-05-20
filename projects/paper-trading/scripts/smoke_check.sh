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
echo

echo "----- ops status -----"
curl -sS "$BASE_URL/ops/status" | pretty_print || true
echo

echo "----- ops preflight -----"
curl -sS "$BASE_URL/ops/preflight" | pretty_print || true
echo

echo "----- paper simulation example -----"
curl -sS -X POST "$BASE_URL/paper/order/simulate" \
    -H "content-type: application/json" \
    -d '{
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 1,
        "order_type": "limit",
        "limit_price": "100",
        "stop_price": null,
        "mock_bid": "99",
        "mock_ask": "100",
        "mock_last": "100",
        "mock_volume": 100,
        "currency": "USD"
    }' | pretty_print || true
echo
echo "[OK] smoke_check sections completed"
echo "===== smoke_check done ====="
