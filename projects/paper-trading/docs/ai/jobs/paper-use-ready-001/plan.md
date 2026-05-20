# paper-use-ready-001 — Paper trading 실제 사용 준비 (tooling / RUNBOOK / 점검 자동화)

본 job 은 **앱 코드 무변동 / 운영 편의성과 점검 자동화에 집중**한다. `app/broker/*` / `app/oms/*` / `app/risk/*` / `app/portfolio/*` / `app/runtime/*` / `app/strategy/*` / `app/session/*` / `app/domain/*` / `app/ops/*` / `app/api/*` / `app/config.py` / `app/main.py` 어떤 파일도 수정하지 않는다. 결과물은 (1) bash scripts, (2) RUNBOOK / OPS_AUDIT 문서, (3) README 업데이트, (4) HTTP-level smoke test (TestClient) 한 개 — 사용자가 매일 켜서 paper trading 검증에 쓸 수 있는 운영 상태를 만드는 것이 목표.

## 1. 요청 요약

paper trading 기반 (paper-001 / paper-002 / runtime-002 / paper-ux-001 / api-orders-paper-001..003-query / strategy-002 / runtime-soak-001 / live-validation-001) 이 모두 land 된 시점에서 기능은 충분히 갖춰졌으나 **사용자 매일 운영 루틴이 복잡**하다. 본 job 의 deliverable:

- 서버 start / stop / restart / status 명령 → 한 줄 실행 가능.
- smoke check → server reachable + paper/ops status + dry-run lifecycle + paper simulation + safety grep + test + git status 를 한 번에 점검.
- RUNBOOK (한국어) → 초보자용 실행 순서 + PuTTY 안내 + 문제 해결.
- OPS_AUDIT (한국어) → 현재 안전 상태 + 안전 grep 결과 + 운영 체크리스트.
- README → 새 스크립트 명령 인용 + RUNBOOK / OPS_AUDIT 링크.

**핵심 제약**:

- 본 job 은 **앱 코드를 수정하지 않는다**. 모든 점검은 read-only HTTP 호출 + 새 스크립트 / 문서 / TestClient 테스트로 수행.
- 새 endpoint 추가 없음. 기존 `/paper/*` / `/ops/*` / `/reports/*` 만 사용.
- secret / `.env` 값 출력 금지. 스크립트 어디에서도 raw credential 표시 0.
- `git add -A` 권장 금지. README/RUNBOOK 의 staging 가이드는 file-by-file 명시.
- 자동 git commit / push / merge / deploy 0.
- live trading 활성화 / market order 허용 / KIS_ORDER_DRY_RUN=false 토글 0.
- 기존 547 passed 베이스라인 무변동 (새 TestClient 스모크 테스트가 추가되어 ~548-550 으로 증가 가능).

## 2. 작업 범위

### 2.1 포함

**Scripts (bash, `projects/paper-trading/scripts/`)**:

- `start_server.sh` — 기존 유지. 추가 변경 없음 (이미 안전 default 적용 중).
- `stop_server.sh` (NEW) — `pgrep -f "uvicorn app.api.server"` 로 PID 찾아 SIGTERM. 미실행이면 안전 종료. 5 초 후 강제 kill.
- `restart_server.sh` (NEW) — `stop_server.sh` → sleep 1 → `start_server.sh` (foreground 또는 backgrounded 옵션). 단순한 wrapper.
- `status.sh` — 기존 유지 + `/ops/status` + `/ops/preflight` 추가 표시.
- `smoke_check.sh` — 기존 유지 + 다음 추가:
  - `/ops/status` + `/ops/preflight` fetch.
  - `/paper/order/simulate` 예시 호출 (한 번).
  - 종료 시 [OK]/[FAIL] 요약 라인.
- `use_ready_check.sh` (NEW) — 마스터 점검 스크립트. 다음을 순서대로 실행 후 통합 결과 출력:
  1. server reachable check (`curl -sS -f $BASE_URL/healthz`)
  2. existing `smoke_check.sh` 실행
  3. safety grep (외부 HTTP / KIS 직접 호출 / live trading 활성화 / OrderType.STOP / FX 변환 / `.env` git tracked 여부) — 모두 0 lines 기대
  4. `git status --short` + `git log --oneline -10` (최상위 ai-team repo 기준)
  5. 최종 OK/FAIL 요약
- `safety_grep.sh` (NEW) — 안전 grep 만 모은 helper (use_ready_check 에서 호출).

**Docs**:

- `projects/paper-trading/docs/RUNBOOK.md` (NEW) — 한국어 운영 가이드. 초보자용 실행 순서 + PuTTY 안내 + 명령 cheat sheet + 문제 해결.
- `projects/paper-trading/docs/OPS_AUDIT.md` (NEW) — 한국어 최종 운영 감사 보고서. 현재 안전 상태 / 안전 grep 결과 / 운영 체크리스트.
- `projects/paper-trading/README.md` (MODIFY) — 새 scripts 인용 + RUNBOOK / OPS_AUDIT 링크. 기존 섹션 무변동 (append only).

**Tests**:

- `tests/test_use_ready_smoke.py` (NEW) — TestClient 로 smoke check 전체 흐름을 Python 단위에서 검증. bash 와 본질적으로 같은 endpoint 호출 시퀀스이지만 pytest 인프라 안에서 실행되어 재현성 보장. ~10 테스트.

**job docs**:

- `docs/ai/jobs/paper-use-ready-001/patch.md` (NEW, Codex 작성).
- `docs/ai/jobs/paper-use-ready-001/status.md` (NEW, Codex 작성).

### 2.2 제외 (절대 안 하는 것)

- `app/` 전체 무변동. 어떤 .py 파일도 추가/수정하지 않는다.
- 새 endpoint 추가 0. routes.py 무변동.
- dashboard.html 무변동 (이미 paper-ux-001 / live-validation-001 에서 완성됨).
- live trading 활성화 / market order 허용 / dry-run disable 토글 0.
- KIS endpoint / TR ID / payload / header 추측 0. catalog 미확인 값 사용 0.
- 외부 HTTP 라이브러리 import 0. bash 스크립트도 `curl` / `bash` builtin 만.
- `.env` 읽기/수정. 스크립트가 `.env` 의 raw 값을 echo 하지 않는다.
- `.env.example` 수정.
- 실 secret / 계좌번호 / token / Bearer 코드/문서/테스트/patch 기록.
- `git add -A` 사용 권장. README/RUNBOOK 은 명시적 file-by-file 추가만 권고.
- 자동 git commit / push / merge / deploy.
- 새 Settings 필드 추가.
- Strategy / Agent / LLM broker 직접 호출 경로 추가.
- OMS / RiskEngine 우회.

## 3. 수정해야 할 파일

| 경로 | 변경 종류 | 요약 |
| --- | --- | --- |
| `scripts/stop_server.sh` | NEW | uvicorn 프로세스 SIGTERM. idempotent. ~30 줄. |
| `scripts/restart_server.sh` | NEW | stop + start wrapper. ~15 줄. |
| `scripts/status.sh` | MODIFY (좁은 추가) | `/ops/status` + `/ops/preflight` 추가 표시. 기존 출력 무변동. |
| `scripts/smoke_check.sh` | MODIFY (좁은 추가) | ops endpoints + paper simulation + 최종 OK/FAIL 요약. 기존 단계 무변동. |
| `scripts/use_ready_check.sh` | NEW | 마스터 점검 wrapper. ~80 줄. |
| `scripts/safety_grep.sh` | NEW | 안전 grep helper. ~50 줄. |
| `docs/RUNBOOK.md` | NEW | 한국어 운영 가이드 (~200 줄). |
| `docs/OPS_AUDIT.md` | NEW | 한국어 최종 ops 감사 (~150 줄). |
| `README.md` | MODIFY | append "운영 스크립트 명령 정리" + "RUNBOOK / OPS_AUDIT 링크" 섹션. ~40 줄 추가. 기존 섹션 무변동. |
| `tests/test_use_ready_smoke.py` | NEW | TestClient HTTP 스모크 회귀 (~10 테스트). |
| `docs/ai/jobs/paper-use-ready-001/patch.md` | NEW | Codex 작성. |
| `docs/ai/jobs/paper-use-ready-001/status.md` | NEW | Codex 작성. |

**손대지 않는 파일**:

- `app/` 전체.
- `tests/` 의 기존 모든 파일.
- `.env`, `.env.example`.
- `docs/kis/MISSING_OFFICIAL_VALUES.md`.
- `docs/ai/jobs/` 의 다른 job 디렉터리.
- 기존 `scripts/start_server.sh` / `start_dry_run.sh` / `stop_dry_run.sh` / `tick.sh` / `analyze.sh` / `_common.sh` 내용 무변동 (단 `status.sh` / `smoke_check.sh` 는 좁은 추가만).

## 4. Codex 구현 지시문

자세한 단계는 `codex-task.md` 에 기록. 요지:

### 4.1 `scripts/stop_server.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/_common.sh"

PORT="${PORT:-8000}"

PIDS=$(pgrep -f "uvicorn app.api.server" || true)
if [ -z "$PIDS" ]; then
    echo "[stop_server] no uvicorn paper-trading server running"
    exit 0
fi

echo "[stop_server] sending SIGTERM to PIDs: $PIDS"
echo "$PIDS" | xargs -r kill -TERM 2>/dev/null || true

# Wait up to 5 seconds for graceful shutdown
for i in 1 2 3 4 5; do
    REMAIN=$(pgrep -f "uvicorn app.api.server" || true)
    if [ -z "$REMAIN" ]; then
        echo "[stop_server] stopped"
        exit 0
    fi
    sleep 1
done

REMAIN=$(pgrep -f "uvicorn app.api.server" || true)
if [ -n "$REMAIN" ]; then
    echo "[stop_server] SIGKILL fallback for PIDs: $REMAIN"
    echo "$REMAIN" | xargs -r kill -KILL 2>/dev/null || true
fi
echo "[stop_server] stopped"
```

- Idempotent: no process → exit 0 silently.
- 5 초 graceful 후 SIGKILL fallback.
- `pgrep -f "uvicorn app.api.server"` 로 본 프로젝트의 uvicorn 만 식별 (다른 uvicorn 프로세스 영향 없음).

### 4.2 `scripts/restart_server.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
"$SCRIPT_DIR/stop_server.sh"
sleep 1
exec "$SCRIPT_DIR/start_server.sh" "$@"
```

`start_server.sh` 가 foreground 이므로 `exec` 로 교체. 사용자가 background 로 원하면 `nohup ./scripts/start_server.sh &` 식으로 README 에 안내.

### 4.3 `scripts/status.sh` 추가

기존 status.sh 끝에 추가:

```bash
echo
echo "## GET /ops/status"
curl -sS -f "$BASE_URL/ops/status" | pretty_print || echo "[status] /ops/status not reachable"
echo
echo "## GET /ops/preflight"
curl -sS -f "$BASE_URL/ops/preflight" | pretty_print || echo "[status] /ops/preflight not reachable"
```

기존 `/paper/status` / `/paper/dry-run/status` 출력 무변동.

### 4.4 `scripts/smoke_check.sh` 추가

기존 smoke_check.sh 끝에 추가 (stop_dry_run 이후, 종료 직전):

```bash
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
echo "===== smoke_check done ====="
```

### 4.5 `scripts/safety_grep.sh`

```bash
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
    "$(grep -rnE 'Bearer eyJ|access_token=eyJ' app docs 2>/dev/null | grep -v 'test_missing_market_data_values_doc\|docs/ai/jobs' || true)"

report ".env 가 git tracked 인지" \
    "$(cd .. && git ls-files | grep -E '^projects/paper-trading/\.env$' || true)"

echo
if [ "$FAIL" -eq 0 ]; then
    echo "===== safety_grep: ALL OK ====="
    exit 0
else
    echo "===== safety_grep: $FAIL FAIL(s) ====="
    exit 1
fi
```

### 4.6 `scripts/use_ready_check.sh`

```bash
#!/usr/bin/env bash
set -uo pipefail   # not -e: continue past individual failures, collect at end

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(cd "$PROJECT_DIR/../.." && pwd)"
cd "$PROJECT_DIR"

. "$SCRIPT_DIR/_common.sh"

OK=0
FAIL=0
note_ok()   { echo "[OK ] $1"; OK=$((OK+1)); }
note_fail() { echo "[FAIL] $1"; FAIL=$((FAIL+1)); }

echo "===== use_ready_check ====="
echo

# 1. server reachable
if curl -sS -f -m 3 "$BASE_URL/healthz" >/dev/null 2>&1; then
    note_ok "server reachable at $BASE_URL/healthz"
else
    note_fail "server NOT reachable at $BASE_URL/healthz — start with ./scripts/start_server.sh"
fi

# 2. paper / ops status
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

# 3. smoke flow (existing smoke_check.sh)
echo
echo "----- smoke flow -----"
if "$SCRIPT_DIR/smoke_check.sh" >/tmp/smoke.log 2>&1; then
    note_ok "smoke_check.sh succeeded"
else
    note_fail "smoke_check.sh failed (see /tmp/smoke.log)"
fi

# 4. safety grep
echo
echo "----- safety grep -----"
if "$SCRIPT_DIR/safety_grep.sh" >/tmp/safety.log 2>&1; then
    note_ok "safety_grep.sh clean"
else
    note_fail "safety_grep.sh reported issues (see /tmp/safety.log)"
fi

# 5. compileall + pytest
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

# 6. git status
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

# Summary
echo
echo "===== use_ready_check: OK=$OK FAIL=$FAIL ====="
if [ "$FAIL" -eq 0 ]; then
    echo "✅ READY for paper trading session"
    exit 0
else
    echo "❌ NOT READY — see [FAIL] items above"
    exit 1
fi
```

### 4.7 `docs/RUNBOOK.md`

한국어 운영 가이드. 다음 섹션 (순서 그대로):

1. **시작 전 준비**: 프로젝트 위치, venv 활성화 안내, PuTTY 터널 설정 (Source 8000, Destination 127.0.0.1:8000).
2. **서버 명령 cheat sheet**:
   ```bash
   ./scripts/start_server.sh       # 서버 시작 (foreground)
   nohup ./scripts/start_server.sh > /tmp/paper.log 2>&1 &   # 백그라운드 시작
   ./scripts/stop_server.sh        # 서버 정지
   ./scripts/restart_server.sh     # 재시작
   ./scripts/status.sh             # 상태 확인 (paper + ops)
   ./scripts/use_ready_check.sh    # 마스터 점검 (server + smoke + safety + test + git)
   ```
3. **Dashboard 접속**: 브라우저 `http://127.0.0.1:8000/dashboard` (PuTTY 터널 사용 시).
4. **Dashboard 에서 확인할 것**: 안전 배너 / Live Validation 준비 상태 / Preflight Checklist / KIS 상태 / Paper 계좌 / Dry-run 상태.
5. **Dry-run 운영**: 시작 / Tick 1 회 / 중지 / 분석 / 최신 리포트 보기 — dashboard 버튼 또는 `./scripts/start_dry_run.sh` etc.
6. **Paper simulation 예시**: dashboard 의 "예시 모의 주문 실행" 또는 직접 `curl -X POST /paper/order/simulate ...`.
7. **KIS 상태 확인**: kis_config_loaded / kis_authenticated / account_no_masked / kis_last_error — 모두 read-only.
8. **테스트 + 안전 grep**: `./scripts/use_ready_check.sh` 한 줄.
9. **Git 운영 원칙**:
   - `git status --short` 로 확인.
   - **`git add -A` 사용 금지**. 변경한 파일을 명시적으로 `git add <path>` 로 추가.
   - 본 시리즈의 dirty 잔재가 있다면 logical commit 으로 분리.
   - `git commit / push / merge` 는 본 시스템이 자동화하지 않는다.
10. **문제 해결** (요청 §"문제 해결" 의 10 개 상황별):
    - `curl: Failed to connect to 127.0.0.1:8000` → 서버 미실행. `./scripts/start_server.sh`.
    - `/dashboard 가 Not Found` → server.py routes 미로드. `./scripts/restart_server.sh` 후 재시도.
    - `JSON 만 보임` → `Accept: text/html` 헤더 누락. 브라우저로 접속.
    - `kis_config_loaded=false` → `.env` 에 KIS_ENV / KIS_ACCOUNT_NO / KIS_APP_KEY / KIS_APP_SECRET 미설정. 본 가이드는 값을 명시하지 않음 — 사용자가 직접 설정.
    - `secret_exposed=true` → CRITICAL. 서버 정지 후 코드/로그/응답에서 raw secret 검색. 즉시 보안 검토.
    - `dry-run not running` → `./scripts/start_dry_run.sh` 실행.
    - `422 body missing` → POST body JSON 형식 오류. `_order_payload()` 예시 참고.
    - `409 conflict` → 이미 실행 중. `./scripts/stop_dry_run.sh` 후 재시도.
    - `pytest 가 안 돌아감` → `.venv/bin/python -m pytest -p no:cacheprovider` 직접 실행. 모듈 누락 시 `pip install -r requirements.txt` (.venv 활성화 후).
    - `venv 가 없음` → `python -m venv .venv && .venv/bin/pip install -r requirements.txt`.
    - `git status dirty` → 위 §9 절차.

### 4.8 `docs/OPS_AUDIT.md`

한국어 최종 ops 감사 보고서. 다음 섹션:

1. **현재 안전 상태 요약** — paper trading / live disabled / market disabled / dry-run default / kill switch off (운영 기준 시점).
2. **6 단 live trading 차단 가드** (`Settings` default + `load_settings()` env check + `RiskEngine.evaluate` reject + `OMS.place` 차단 + `POST /paper/run` 503 + `KisBroker.__init__` KIS_ENV reject).
3. **3중 market order 가드** (`OrderType.MARKET` 3-layer guard + `ALLOW_MARKET_ORDERS=true` reject + `RiskEngine` market reject).
4. **KIS 안전 경계** (catalog 확인 값만 사용 / `KIS_ORDER_DRY_RUN=true` 기본 / `validate_kis_order_request` preflight / sanitize / 모든 응답 redaction).
5. **Strategy / Agent / LLM 격리** (Strategy 의 `app.broker.*` import 0 / Agent 의 broker 직접 호출 0 / LLM 의 executable order 생성 0).
6. **현재 안전 grep 결과** — `./scripts/safety_grep.sh` 출력 사본 (실 실행 시 운영자가 갱신).
7. **운영 체크리스트 (매일 paper session 시작 전)**:
   - `./scripts/use_ready_check.sh` 실행 → 모두 [OK].
   - dashboard 의 banner 가 `info` level 인지.
   - Preflight Checklist 14 항 중 운영자 수동 확인 항목 (`recent_test_passed_manual`) 외 모두 ✅ 인지.
   - `live_validation_ready` 값 (현재는 운영자 수동 확인).
8. **실거래 전환 전 필요 조건** — Phase 5+ 별 job 으로 분리 (live-validation-002 등 future). 본 audit 는 그 진입을 승인하지 않음.

### 4.9 `tests/test_use_ready_smoke.py`

TestClient 기반 HTTP 스모크 회귀. 다음 테스트 (10 개):

```python
from fastapi.testclient import TestClient
from app.api.server import create_app


def test_smoke_healthz():
    with TestClient(create_app()) as client:
        assert client.get("/healthz").json() == {"ok": True}


def test_smoke_paper_status_keys_present():
    with TestClient(create_app()) as client:
        body = client.get("/paper/status").json()
    for key in ("mode", "live_enabled", "market_orders_allowed", "kis_order_dry_run",
                "secret_exposed", "kill_switch_engaged"):
        assert key in body


def test_smoke_ops_status_keys_present():
    with TestClient(create_app()) as client:
        body = client.get("/ops/status").json()
    for key in ("live_trading_enabled", "trading_mode", "live_validation_ready",
                "banner_level", "banner_text_ko", "secret_exposed"):
        assert key in body


def test_smoke_ops_preflight_includes_checklist():
    with TestClient(create_app()) as client:
        body = client.get("/ops/preflight").json()
    assert "items" in body and len(body["items"]) == 14


def test_smoke_dry_run_lifecycle():
    with TestClient(create_app()) as client:
        # start
        assert client.post("/paper/dry-run/start").status_code == 200
        # tick
        assert client.post("/paper/dry-run/tick", json={"snapshots": []}).status_code == 200
        # status
        s = client.get("/paper/dry-run/status").json()
        assert s["state"] == "running"
        # stop
        assert client.post("/paper/dry-run/stop").status_code == 200


def test_smoke_paper_order_simulate_demo():
    payload = {
        "symbol": "AAPL", "side": "buy", "quantity": 1, "order_type": "limit",
        "limit_price": "100", "stop_price": None,
        "mock_bid": "99", "mock_ask": "100", "mock_last": "100",
        "mock_volume": 100, "currency": "USD",
    }
    with TestClient(create_app()) as client:
        body = client.post("/paper/order/simulate", json=payload).json()
    assert body["accepted"] is True
    assert body["safety_flags"]["mode"] == "paper"
    assert body["safety_flags"]["live_trading_enabled"] is False


def test_smoke_reports_latest_after_analyze():
    with TestClient(create_app()) as client:
        client.post("/paper/dry-run/start")
        client.post("/paper/dry-run/tick", json={"snapshots": []})
        client.post("/paper/dry-run/stop")
        analyze = client.post("/reports/dry-run/analyze", json={"run_dir": None})
    assert analyze.status_code in (200, 404)  # 404 if no run dir yet


def test_smoke_no_secrets_in_combined_responses():
    forbidden = ("KIS_APP_KEY", "KIS_APP_SECRET", "KIS_ACCOUNT_NO",
                 "app_secret", "access_token", "Bearer ")
    with TestClient(create_app()) as client:
        endpoints = ["/paper/status", "/ops/status", "/ops/preflight",
                     "/paper/account", "/paper/positions", "/paper/fills",
                     "/paper/engine/status"]
        for path in endpoints:
            text = client.get(path).text
            for needle in forbidden:
                assert needle not in text, f"{path} leaked {needle!r}"


def test_smoke_ops_routes_are_get_only():
    with TestClient(create_app()) as client:
        for verb in ("post", "put", "delete"):
            fn = getattr(client, verb)
            assert fn("/ops/status").status_code == 405
            assert fn("/ops/preflight").status_code == 405


def test_smoke_dashboard_loads_html():
    with TestClient(create_app()) as client:
        response = client.get("/dashboard")
    assert response.status_code == 200
    assert "<html" in response.text or "<!DOCTYPE" in response.text
    assert "원본 JSON 보기" in response.text  # paper-ux-001 marker
```

### 4.10 `README.md` 추가

기존 README 끝에 append (기존 섹션 무변동):

```markdown
## 운영 스크립트 명령 정리 (paper-use-ready-001)

매일 paper trading session 운영 명령:

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading

./scripts/start_server.sh         # 서버 시작 (foreground)
./scripts/stop_server.sh          # 서버 정지
./scripts/restart_server.sh       # 재시작
./scripts/status.sh               # paper + ops 상태
./scripts/use_ready_check.sh      # 마스터 점검 (server + smoke + safety + test + git)
./scripts/safety_grep.sh          # 안전 grep 만
./scripts/smoke_check.sh          # dry-run 흐름 + paper simulation
./scripts/start_dry_run.sh        # dry-run 단독 시작
./scripts/stop_dry_run.sh         # dry-run 단독 중지
./scripts/tick.sh                 # tick 1 회
./scripts/analyze.sh              # 리포트 분석
```

운영 가이드: [docs/RUNBOOK.md](docs/RUNBOOK.md).
최종 ops 안전 감사: [docs/OPS_AUDIT.md](docs/OPS_AUDIT.md).

### Git 운영 원칙

- `git status --short` 로 dirty 파일 확인.
- **`git add -A` 사용 금지**. 변경한 파일을 명시적으로 `git add <path>` 로 추가.
- `git commit / push / merge` 는 본 시스템이 자동화하지 않는다.
```

## 5. 테스트 기준

- `compileall app tests` PASS 유지.
- `pytest -p no:cacheprovider` PASS 유지. 547 baseline + ~10 new = ~557 expected.
- `tests/test_use_ready_smoke.py` 10 신규 함수 모두 PASS.
- 기존 어떤 test 도 단언이 깨지지 않는다 (앱 코드 무변동).
- `scripts/use_ready_check.sh` 가 서버 실행 중일 때 exit 0, 미실행 시 첫 [FAIL] 로 종료 (의도된 동작).
- `scripts/safety_grep.sh` 가 단독 실행 시 모든 항목 [OK].

## 6. 리뷰 체크리스트

안전 회귀:

- [ ] `app/` 디렉터리 무변동 (어떤 .py 파일도 추가/수정/삭제 0).
- [ ] 새 endpoint 추가 0.
- [ ] dashboard.html 무변동.
- [ ] live trading 활성화 코드 / live arm / dry-run disable toggle / market allow toggle / `OrderType.STOP` / FX 변환 도입 0.
- [ ] KIS endpoint / TR ID / payload / header 추측 0.
- [ ] 외부 HTTP 라이브러리 추가 0 (스크립트는 `curl` / bash builtin 만).
- [ ] `.env` / `.env.example` 무변동. 새 env 변수 추가 0.
- [ ] `docs/kis/MISSING_OFFICIAL_VALUES.md` 무변동.
- [ ] Strategy / Agent / LLM broker 직접 호출 0 (기존 격리 유지).
- [ ] OMS / RiskEngine 우회 0.
- [ ] secret / 계좌번호 / token / Bearer 코드/스크립트/문서/테스트/patch 노출 0.
- [ ] `git add -A` 권장 0 — RUNBOOK / README 가 명시적 file-by-file staging 만 안내.
- [ ] 자동 git commit / push / merge / deploy 0.

스코프 / 동작:

- [ ] `stop_server.sh` 가 idempotent (미실행 시 exit 0).
- [ ] `restart_server.sh` 가 stop → start sequence.
- [ ] `status.sh` 가 `/paper/status` + `/paper/dry-run/status` + `/ops/status` + `/ops/preflight` 4 개 노출.
- [ ] `smoke_check.sh` 가 기존 lifecycle + ops endpoints + paper simulation + [OK]/[FAIL] summary.
- [ ] `use_ready_check.sh` 가 server reachable + smoke + safety + test + git 5 영역 통합 점검 + 최종 OK/FAIL 카운트.
- [ ] `safety_grep.sh` 가 9 개 grep 항목 모두 [OK]/[FAIL] 라인 출력.
- [ ] RUNBOOK 의 PuTTY 안내 + 명령 cheat sheet + 10 개 문제 해결 항목 모두 포함.
- [ ] OPS_AUDIT 의 6 단 live trading 차단 가드 + 3중 market guard + KIS 안전 경계 + Strategy/Agent/LLM 격리 + 운영 체크리스트 모두 포함.
- [ ] README append 가 새 명령 정리 + RUNBOOK / OPS_AUDIT 링크 + git 운영 원칙 포함.

테스트 / 문서:

- [ ] `compileall app tests` PASS.
- [ ] `pytest -p no:cacheprovider` 전체 PASS. baseline 547 + ~10 new.
- [ ] `tests/test_use_ready_smoke.py` 가 10 개 endpoint 흐름을 회귀.
- [ ] `patch.md` 가 수정 파일 / smoke 흐름 / safety grep 결과 / git status 결과 / Claude 검증 요청 프롬프트 / Follow-up Codex prompt 작성 규칙 모두 포함.

자동화 금지:

- [ ] commit / push / merge / PR / deploy 수행 0.
- [ ] `.env` / secret / credential / API key / token 수정 / 노출 0.
