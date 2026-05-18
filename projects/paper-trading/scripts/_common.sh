#!/usr/bin/env bash
# Shared helpers for mvp-020 paper-trading scripts.
# Forces safe defaults regardless of .env values; never prints raw credentials.

set -euo pipefail

# Safe defaults exported before the server reads .env. python-dotenv does not
# override existing env vars, so these win over .env.
export TRADING_MODE=paper
export LIVE_TRADING_ENABLED=false
export ALLOW_MARKET_ORDERS=false
export KIS_ORDER_DRY_RUN=true

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
PORT="${PORT:-8000}"

HAS_JQ=0
if command -v jq >/dev/null 2>&1; then
    HAS_JQ=1
fi

pretty_print() {
    if [ "$HAS_JQ" -eq 1 ]; then
        jq .
    else
        cat
    fi
}

print_banner() {
    echo "[mvp-020] BASE_URL=$BASE_URL  TRADING_MODE=$TRADING_MODE  LIVE=$LIVE_TRADING_ENABLED  MARKET=$ALLOW_MARKET_ORDERS  KIS_DRY_RUN=$KIS_ORDER_DRY_RUN"
}
