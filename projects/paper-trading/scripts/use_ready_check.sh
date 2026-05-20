#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(git -C "$PROJECT_DIR" rev-parse --show-toplevel 2>/dev/null || cd "$PROJECT_DIR/../.." && pwd)"
cd "$PROJECT_DIR"

# shellcheck disable=SC1091
. "$SCRIPT_DIR/_common.sh"

OK=0
FAIL=0
note_ok() { echo "[OK ] $1"; OK=$((OK+1)); }
note_fail() { echo "[FAIL] $1"; FAIL=$((FAIL+1)); }

echo "===== use_ready_check ====="
echo

if curl -sS -f -m 3 "$BASE_URL/healthz" >/dev/null 2>&1; then
    note_ok "server reachable at $BASE_URL/healthz"
else
    note_fail "server NOT reachable at $BASE_URL/healthz - start with ./scripts/start_server.sh"
fi

if curl -sS -f -m 3 "$BASE_URL/paper/status" >/dev/null 2>&1; then
    note_ok "/paper/status loaded"
else
    note_fail "/paper/status not reachable"
fi
if curl -sS -f -m 3 "$BASE_URL/ops/status" >/dev/null 2>&1; then
    note_ok "/ops/status loaded"
else
    note_fail "/ops/status not reachable"
fi
if curl -sS -f -m 3 "$BASE_URL/ops/preflight" >/dev/null 2>&1; then
    note_ok "/ops/preflight loaded"
else
    note_fail "/ops/preflight not reachable"
fi

echo
echo "----- smoke flow -----"
if "$SCRIPT_DIR/smoke_check.sh" >/tmp/smoke.log 2>&1; then
    note_ok "smoke_check.sh succeeded"
else
    note_fail "smoke_check.sh failed (see /tmp/smoke.log)"
fi

echo
echo "----- safety grep -----"
if "$SCRIPT_DIR/safety_grep.sh" >/tmp/safety.log 2>&1; then
    note_ok "safety_grep.sh clean"
else
    note_fail "safety_grep.sh reported issues (see /tmp/safety.log)"
fi

echo
echo "----- compileall + pytest -----"
if .venv/bin/python -m compileall app tests >/tmp/compileall.log 2>&1; then
    note_ok "compileall passed"
else
    note_fail "compileall failed (see /tmp/compileall.log)"
fi
if .venv/bin/python -m pytest -p no:cacheprovider --tb=no -q >/tmp/pytest.log 2>&1; then
    PASSED=$(grep -oE '[0-9]+ passed' /tmp/pytest.log | head -1 || echo "")
    note_ok "pytest passed ($PASSED)"
else
    note_fail "pytest failed (see /tmp/pytest.log)"
fi

echo
echo "----- git status (read-only summary) -----"
cd "$REPO_ROOT"
DIRTY=$(git status --short 2>/dev/null | wc -l)
if [ "$DIRTY" -eq 0 ]; then
    note_ok "git status clean"
else
    note_fail "git status has $DIRTY dirty entries (use 'git status --short' manually; do NOT use git add -A)"
fi
echo
echo "## git log (last 5)"
git log --oneline -5 2>/dev/null || echo "git log unavailable"

echo
echo "===== use_ready_check: OK=$OK FAIL=$FAIL ====="
if [ "$FAIL" -eq 0 ]; then
    echo "READY for paper trading session"
    exit 0
else
    echo "NOT READY - see [FAIL] items above"
    exit 1
fi
