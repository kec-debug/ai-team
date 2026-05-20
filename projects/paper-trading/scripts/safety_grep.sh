#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

FAIL=0

report() {
    local label="$1"
    local result="$2"
    if [ -z "$result" ]; then
        echo "[OK ] $label"
    else
        echo "[FAIL] $label"
        echo "$result"
        FAIL=$((FAIL+1))
    fi
}

echo "===== safety_grep ====="
echo

report "external HTTP libs in app/" \
    "$(grep -rnE '^(from|import) (requests|httpx|aiohttp|urllib3|openpyxl|pandas)' app 2>/dev/null || true)"

report "Strategy 가 KIS 직접 import" \
    "$(grep -rnE '^\s*(from|import)\s+app\.broker\.(kis|paper)' app/strategy 2>/dev/null || true)"

report "Agent / LLM 의 broker 직접 호출 (app/agent)" \
    "$(find app -maxdepth 2 -type d -name agent 2>/dev/null | xargs -r grep -rnE '^\s*(from|import)\s+app\.broker' 2>/dev/null || true)"

report "live trading 활성화 코드" \
    "$(grep -rnE 'live_trading_enabled\s*=\s*True' app 2>/dev/null || true)"

report "market order guard 우회 (allow_market_orders=True)" \
    "$(grep -rnE 'allow_market_orders\s*=\s*True' app 2>/dev/null || true)"

report "OrderType.STOP 도입" \
    "$(grep -rn 'OrderType\.STOP\b' app 2>/dev/null | grep -v 'STOP_LIMIT' || true)"

report "FX 변환 함수 도입" \
    "$(grep -rnE 'def\s+(convert_fx|fx_convert|to_base_currency)' app 2>/dev/null || true)"

report "JWT-style secret 노출 (Bearer eyJ / access_token=eyJ)" \
    "$(grep -rnE 'Bearer eyJ|access_token=eyJ' app docs 2>/dev/null | grep -v 'test_missing_market_data_values_doc\|docs/ai/jobs\|docs/OPS_AUDIT.md' || true)"

report ".env 가 git tracked 인지" \
    "$(git ls-files | grep -E '^\.env$' || true)"

echo
if [ "$FAIL" -eq 0 ]; then
    echo "===== safety_grep: ALL OK ====="
    exit 0
else
    echo "===== safety_grep: $FAIL FAIL(s) ====="
    exit 1
fi
