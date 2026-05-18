## 1. 요청 요약

초보자가 curl 명령을 직접 외우지 않아도 paper-trading 서버 시작 / 상태 확인 / dry-run 실행 / 분석 리포트 생성을 한 줄 명령으로 할 수 있게 **7개 shell script** + **공통 helper** + **README 단락**을 추가한다. 모든 스크립트는 안전한 환경변수 기본값(`TRADING_MODE=paper`, `LIVE_TRADING_ENABLED=false`, `ALLOW_MARKET_ORDERS=false`, `KIS_ORDER_DRY_RUN=true`)을 **shell 단에서 강제**한다.

### 안전 원칙 (mvp-005~mvp-019 누적 유지)

- live trading 활성화 금지. shell이 4개 안전 env를 export하여 `.env` 값이 무엇이든 paper 강제.
- `OrderType.MARKET` 부재 유지.
- 외부 HTTP 라이브러리 import 0건 (스크립트는 `curl`만 사용).
- 코드 변경 0건 — `app/`, `tests/` 비-스크립트 영역 미변경. mvp-005~mvp-019 산출물 미변경.
- `.env` 파일을 **읽거나/print/cat/echo 금지**. raw `KIS_APP_KEY`/`KIS_APP_SECRET`/`KIS_ACCOUNT_NO`/token을 어떤 스크립트도 출력하지 않음.
- `git commit`/`push`/`merge`/`deploy` 자동화 금지 — 스크립트에 git 명령 0건.
- `pip install` 실행 금지.
- 임의 shell 명령 입력 받는 API 신설 금지.

### 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
bash -n scripts/*.sh   # syntax check
```

기존 172 + 신규 약 5–7개(스크립트 메타 테스트) 모두 PASS.

## 2. 작업 범위

### 포함 (In scope)

`projects/paper-trading/` 아래:

- **`scripts/_common.sh` (신규)** — 공통 helper. 4개 안전 env 강제 export. `BASE_URL`/`PORT` 기본값. `pretty_print()` (jq 있으면 jq, 없으면 cat).
- **`scripts/start_server.sh` (신규)** — uvicorn으로 paper-trading API 실행. `PORT=${PORT:-8000}`. `--host 127.0.0.1`(외부 공개 금지).
- **`scripts/status.sh` (신규)** — `GET /paper/status` + `GET /paper/dry-run/status` 둘 다 호출, pretty-print.
- **`scripts/start_dry_run.sh` (신규)** — `POST /paper/dry-run/start`.
- **`scripts/tick.sh` (신규)** — dry-run 상태 확인 → not running이면 자동 start → `POST /paper/dry-run/tick` (snapshots=[]). 결과 pretty-print.
- **`scripts/stop_dry_run.sh` (신규)** — `POST /paper/dry-run/stop`.
- **`scripts/analyze.sh` (신규)** — `POST /reports/dry-run/analyze` → `GET /reports/dry-run/latest` → run_dir 추출하여 로컬 `analysis_report.md` 경로 출력.
- **`scripts/smoke_check.sh` (신규)** — 위 6개를 순차 호출(status → start → tick → analyze → stop). 각 단계 실패는 `|| true`로 흡수(409 처리 위해).
- **`tests/test_helper_scripts.py` (신규)** — 스크립트 메타 테스트(존재/실행 권한/syntax/안전 env 강제 검증/secret 출력 패턴 부재 검증).
- **`README.md` (수정)** — `## 초보자용 실행 방법 (mvp-020)` 섹션 추가. 스크립트 목록 표 + 사용 예시 + 안전 가드 설명.
- **`docs/ai/jobs/mvp-020/patch.md` (신규)** — Codex 변경 요약.

### 제외 (Out of scope; 절대 만지지 않음)

- 실제 주문 / HTTP / Strategy / OMS / RiskEngine / Broker 코드 변경.
- KIS endpoint URL/TR ID/payload 추가.
- 외부 HTTP 라이브러리 import.
- `app/` 디렉터리 변경 (스크립트는 app을 호출만 함).
- `app/config.py`, `Settings` 변경.
- `.env`, `.env.example` 변경.
- `.gitignore` 변경 (스크립트는 commit 대상이므로 ignored되면 안 됨 — 현재 `.gitignore`가 scripts/를 무시하지 않으므로 그대로 사용).
- mvp-001..mvp-019 산출물 변경.
- `web/`, `prompts/`, 기타 `scripts/`(저장소 루트), 기존 `docs/`(`docs/ai/jobs/mvp-020/` 외) 변경.
- 인증/결제/DB migration/production infra 변경.
- 자동 `git commit`/`push`/`merge`/`deploy`.
- `pip install` 실행.
- 임의 shell 명령 입력 UI/API 신설.
- 스크립트가 `.env` 파일을 cat/grep/echo (raw 값 출력 금지).
- 스크립트가 `$KIS_APP_KEY` 같은 raw 비밀변수를 echo.

### 안전 가드

- `_common.sh`가 4개 안전 env를 **export**(force overwrite). `.env`/`Settings.load_settings()`이 `LIVE_TRADING_ENABLED=true`나 `ALLOW_MARKET_ORDERS=true`를 받아도 shell 단에서 차단(python-dotenv는 기본적으로 기존 env를 override하지 않음).
- `start_server.sh`이 `--host 127.0.0.1`로 묶음 → 외부 노출 차단.
- 모든 curl 호출은 `127.0.0.1` 기본(BASE_URL env로 override 가능하지만 README는 로컬만 안내).
- 응답 출력은 서버가 이미 sanitize한 결과(dump_safe + secret_exposed=false + account_no_masked)를 그대로 보여주므로 raw credentials 노출 위험 0.
- `bash -n` syntax check 테스트로 스크립트 오류 방지.
- 메타 테스트가 `KIS_APP_KEY`/`KIS_APP_SECRET`/`KIS_ACCOUNT_NO`/`cat .env` 같은 forbidden 패턴이 스크립트에 등장하지 않음을 검증.

## 3. 수정해야 할 파일

### 신규

| 파일 | 목적 |
| --- | --- |
| `scripts/_common.sh` | 공통 helper(env 강제, BASE_URL, pretty_print) |
| `scripts/start_server.sh` | uvicorn 실행 |
| `scripts/status.sh` | /paper/status + /paper/dry-run/status |
| `scripts/start_dry_run.sh` | /paper/dry-run/start |
| `scripts/tick.sh` | 자동 start + tick |
| `scripts/stop_dry_run.sh` | /paper/dry-run/stop |
| `scripts/analyze.sh` | analyze + latest + report path |
| `scripts/smoke_check.sh` | status→start→tick→analyze→stop |
| `tests/test_helper_scripts.py` | 스크립트 메타 검증 |
| `docs/ai/jobs/mvp-020/patch.md` | Codex 변경 요약 |

### 수정

| 파일 | 변경 내용 |
| --- | --- |
| `projects/paper-trading/README.md` | `## 초보자용 실행 방법 (mvp-020)` 섹션 추가 |

### 절대 미수정

- `projects/paper-trading/app/` 전부.
- `projects/paper-trading/.env.example`, `.gitignore`.
- `projects/paper-trading/tests/test_*.py` 기존 테스트.
- 루트 `.gitignore`, 루트 `scripts/`.
- mvp-001..mvp-019 산출물.
- `docs/kis/MISSING_OFFICIAL_VALUES.md`.
- `imports/`, `web/`, `prompts/`, 기존 `docs/`(`docs/ai/jobs/mvp-020/` 외).

## 4. Codex 구현 지시문

### 4.1 사전 점검

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m pytest -p no:cacheprovider --co -q 2>&1 | tail -3
# expect: 172 tests collected (or higher)

test -f app/api/server.py && echo "OK server.py"
test -f app/api/routes.py && grep -q "paper/dry-run/start" app/api/routes.py && echo "OK dry-run routes"
test -f app/api/routes.py && grep -q "reports/dry-run/analyze" app/api/routes.py && echo "OK reports routes"
test -f .venv/bin/uvicorn && echo "OK uvicorn"
test -d scripts && echo "WARN scripts/ already exists" || echo "OK scripts/ absent (will be created)"
command -v curl >/dev/null 2>&1 && echo "OK curl"
```

위 6개 OK → 진행.

### 4.2 `scripts/_common.sh` (신규)

```bash
#!/usr/bin/env bash
# Shared helpers for mvp-020 paper-trading scripts.
# Forces safe defaults regardless of .env values; never prints raw credentials.

set -euo pipefail

# Safe defaults — exported BEFORE the server reads .env. python-dotenv does not
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
```

### 4.3 `scripts/start_server.sh` (신규)

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/_common.sh"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"
print_banner
echo "[start_server] starting uvicorn on 127.0.0.1:$PORT"
exec .venv/bin/uvicorn app.api.server:app --host 127.0.0.1 --port "$PORT"
```

### 4.4 `scripts/status.sh` (신규)

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/_common.sh"
print_banner
echo
echo "## GET /paper/status"
curl -sS -f "$BASE_URL/paper/status" | pretty_print
echo
echo "## GET /paper/dry-run/status"
curl -sS -f "$BASE_URL/paper/dry-run/status" | pretty_print
```

### 4.5 `scripts/start_dry_run.sh` (신규)

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/_common.sh"
print_banner
echo
echo "## POST /paper/dry-run/start"
curl -sS -X POST -H 'content-type: application/json' "$BASE_URL/paper/dry-run/start" -d '{}' | pretty_print
```

### 4.6 `scripts/tick.sh` (신규)

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/_common.sh"
print_banner

STATUS_JSON="$(curl -sS "$BASE_URL/paper/dry-run/status")"

is_running() {
    if [ "$HAS_JQ" -eq 1 ]; then
        echo "$STATUS_JSON" | jq -r '.running // false'
    else
        # crude fallback for "running": true|false
        echo "$STATUS_JSON" | grep -oE '"running"[[:space:]]*:[[:space:]]*(true|false)' \
            | head -1 | awk -F: '{print $2}' | tr -d ' '
    fi
}

RUNNING="$(is_running)"
if [ "$RUNNING" != "true" ]; then
    echo "[tick] dry-run not running — starting first..."
    curl -sS -X POST -H 'content-type: application/json' "$BASE_URL/paper/dry-run/start" -d '{}' \
        | pretty_print
    echo
fi

echo "## POST /paper/dry-run/tick"
curl -sS -X POST -H 'content-type: application/json' "$BASE_URL/paper/dry-run/tick" -d '{"snapshots":[]}' \
    | pretty_print
```

### 4.7 `scripts/stop_dry_run.sh` (신규)

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/_common.sh"
print_banner
echo
echo "## POST /paper/dry-run/stop"
curl -sS -X POST -H 'content-type: application/json' "$BASE_URL/paper/dry-run/stop" -d '{}' | pretty_print
```

### 4.8 `scripts/analyze.sh` (신규)

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
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

# Print local path of analysis_report.md.
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
```

### 4.9 `scripts/smoke_check.sh` (신규)

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/_common.sh"

echo "===== smoke_check =====" 
print_banner
echo

echo "----- status -----"
"$SCRIPT_DIR/status.sh" || true
echo

echo "----- start_dry_run -----"
"$SCRIPT_DIR/start_dry_run.sh" || true
echo

echo "----- tick -----"
"$SCRIPT_DIR/tick.sh" || true
echo

echo "----- analyze -----"
"$SCRIPT_DIR/analyze.sh" || true
echo

echo "----- stop_dry_run -----"
"$SCRIPT_DIR/stop_dry_run.sh" || true
echo

echo "===== smoke_check done ====="
```

### 4.10 모든 스크립트 실행 권한 부여

Write 후 다음 명령으로 모두 `chmod +x`:

```bash
chmod +x scripts/_common.sh scripts/start_server.sh scripts/status.sh \
         scripts/start_dry_run.sh scripts/tick.sh scripts/stop_dry_run.sh \
         scripts/analyze.sh scripts/smoke_check.sh
```

### 4.11 `tests/test_helper_scripts.py` (신규)

```python
"""mvp-020: helper script meta-tests.

These tests do NOT execute the scripts (which would require a running server).
They verify:
- all expected scripts exist and are executable
- shebang + bash syntax
- safe env defaults are present in _common.sh
- no forbidden patterns that would leak credentials
"""

import os
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

EXPECTED_SCRIPTS = (
    "_common.sh",
    "start_server.sh",
    "status.sh",
    "start_dry_run.sh",
    "tick.sh",
    "stop_dry_run.sh",
    "analyze.sh",
    "smoke_check.sh",
)


def test_all_scripts_exist():
    for name in EXPECTED_SCRIPTS:
        assert (SCRIPTS_DIR / name).is_file(), f"missing: {name}"


def test_all_scripts_are_executable():
    for name in EXPECTED_SCRIPTS:
        path = SCRIPTS_DIR / name
        assert os.access(path, os.X_OK), f"not executable: {name}"


def test_all_scripts_have_shebang():
    for name in EXPECTED_SCRIPTS:
        first = (SCRIPTS_DIR / name).read_text(encoding="utf-8").splitlines()[0]
        assert first.startswith("#!"), f"missing shebang: {name} ({first!r})"
        assert "bash" in first or "/sh" in first, f"non-bash shebang: {name} ({first!r})"


def test_all_scripts_pass_bash_syntax_check():
    for name in EXPECTED_SCRIPTS:
        result = subprocess.run(
            ["bash", "-n", str(SCRIPTS_DIR / name)],
            capture_output=True,
        )
        assert result.returncode == 0, (
            f"bash syntax error in {name}: {result.stderr.decode(errors='replace')}"
        )


def test_common_forces_safe_env_defaults():
    text = (SCRIPTS_DIR / "_common.sh").read_text(encoding="utf-8")
    assert "export TRADING_MODE=paper" in text
    assert "export LIVE_TRADING_ENABLED=false" in text
    assert "export ALLOW_MARKET_ORDERS=false" in text
    assert "export KIS_ORDER_DRY_RUN=true" in text


def test_no_script_prints_or_reads_secret_values():
    forbidden = (
        "cat .env",
        "cat $HOME/.env",
        "echo $KIS_APP_KEY",
        "echo $KIS_APP_SECRET",
        "echo $KIS_ACCOUNT_NO",
        "${KIS_APP_KEY}",
        "${KIS_APP_SECRET}",
        "${KIS_ACCOUNT_NO}",
    )
    for name in EXPECTED_SCRIPTS:
        text = (SCRIPTS_DIR / name).read_text(encoding="utf-8")
        for pattern in forbidden:
            assert pattern not in text, f"{name} contains forbidden pattern: {pattern!r}"


def test_no_script_uses_git_or_pip():
    """Scripts must not auto-commit, push, merge, deploy, or install."""
    forbidden = ("git commit", "git push", "git merge", "git deploy", "pip install")
    for name in EXPECTED_SCRIPTS:
        text = (SCRIPTS_DIR / name).read_text(encoding="utf-8")
        for pattern in forbidden:
            assert pattern not in text, f"{name} contains forbidden command: {pattern!r}"


def test_start_server_uses_localhost():
    text = (SCRIPTS_DIR / "start_server.sh").read_text(encoding="utf-8")
    assert "127.0.0.1" in text, "start_server.sh must bind to 127.0.0.1 only"
    assert "0.0.0.0" not in text, "start_server.sh must NOT bind to 0.0.0.0"
```

### 4.12 README 변경 (`projects/paper-trading/README.md`)

기존 단락 변경 금지. 적절한 위치(mvp-018 단락 뒤 또는 mvp-019 단락 뒤)에 다음 단락 추가:

```markdown
## 초보자용 실행 방법 (mvp-020)

`scripts/`에 짧은 명령어로 paper-trading 서버와 dry-run을 다룰 수 있는 헬퍼 스크립트가 있습니다. 모든 스크립트는 `_common.sh`에서 `TRADING_MODE=paper`, `LIVE_TRADING_ENABLED=false`, `ALLOW_MARKET_ORDERS=false`, `KIS_ORDER_DRY_RUN=true`를 shell 단에서 강제 export합니다. `.env`에 다른 값이 있어도 paper / dry-run으로 강제됩니다.

| 스크립트 | 동작 |
| --- | --- |
| `scripts/start_server.sh` | uvicorn으로 `127.0.0.1:8000` (또는 `PORT` env로 변경) 실행 |
| `scripts/status.sh` | `/paper/status` + `/paper/dry-run/status` |
| `scripts/start_dry_run.sh` | `POST /paper/dry-run/start` |
| `scripts/tick.sh` | dry-run이 not running이면 자동 start 후 `POST /paper/dry-run/tick` |
| `scripts/stop_dry_run.sh` | `POST /paper/dry-run/stop` |
| `scripts/analyze.sh` | `POST /reports/dry-run/analyze` + `GET /reports/dry-run/latest` + 로컬 `analysis_report.md` 경로 출력 |
| `scripts/smoke_check.sh` | status → start → tick → analyze → stop 일괄 실행 |

### 예시

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading

# 1. 서버 실행 (별도 터미널에서)
./scripts/start_server.sh

# 2. 다른 터미널에서:
./scripts/status.sh
./scripts/tick.sh
./scripts/analyze.sh

# 또는 한 번에:
./scripts/smoke_check.sh
```

`BASE_URL` env로 다른 서버 주소를 지정할 수 있습니다(기본 `http://127.0.0.1:8000`). `jq`가 설치되어 있으면 JSON 응답이 보기 좋게 출력됩니다.

### 안전 가드

- 4개 안전 env가 `_common.sh`에서 force export — `.env`보다 우선합니다(python-dotenv는 기본적으로 기존 env를 덮어쓰지 않음).
- `start_server.sh`은 `127.0.0.1`에만 바인딩 — 외부 노출 차단.
- 어떤 스크립트도 `.env`를 cat/echo하거나 raw `KIS_APP_KEY`/`KIS_APP_SECRET`/`KIS_ACCOUNT_NO`를 출력하지 않습니다.
- 어떤 스크립트도 `git commit`/`push`/`merge`/`pip install`을 실행하지 않습니다.
- 서버 응답은 이미 sanitize되어 있으므로(`dump_safe` + `secret_exposed: false` + `account_no_masked`) curl 출력에 raw credentials가 포함되지 않습니다.
```

### 4.13 검증 명령

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
bash -n scripts/*.sh   # additional syntax check (also covered by tests)
```

저장소 루트:

```bash
git diff --stat
git status --short
```

기대: 기존 172 + 신규 약 7개 ≈ 179 PASS. compileall exit 0. mvp-020 외 변경 없음.

### 4.14 `docs/ai/jobs/mvp-020/patch.md`

```markdown
## 1. Files Changed
- projects/paper-trading/scripts/_common.sh (신규)
- projects/paper-trading/scripts/start_server.sh (신규)
- projects/paper-trading/scripts/status.sh (신규)
- projects/paper-trading/scripts/start_dry_run.sh (신규)
- projects/paper-trading/scripts/tick.sh (신규)
- projects/paper-trading/scripts/stop_dry_run.sh (신규)
- projects/paper-trading/scripts/analyze.sh (신규)
- projects/paper-trading/scripts/smoke_check.sh (신규)
- projects/paper-trading/tests/test_helper_scripts.py (신규)
- projects/paper-trading/README.md (mvp-020 단락)
- docs/ai/jobs/mvp-020/patch.md (신규)

## 2. Implementation Summary

### 2.1 공통 helper
- _common.sh가 4개 안전 env(TRADING_MODE=paper, LIVE_TRADING_ENABLED=false, ALLOW_MARKET_ORDERS=false, KIS_ORDER_DRY_RUN=true) 강제 export.
- BASE_URL/PORT 기본값, pretty_print(jq fallback).

### 2.2 7개 사용자 스크립트
- start_server.sh — uvicorn 127.0.0.1:PORT.
- status.sh — paper/status + paper/dry-run/status.
- start_dry_run.sh, stop_dry_run.sh, tick.sh, analyze.sh — 각 API 1:1 호출.
- tick.sh이 not-running 시 자동 start.
- smoke_check.sh이 6개를 순차 실행(개별 실패는 `|| true`).

### 2.3 Safety
- start_server.sh은 0.0.0.0 미바인딩(127.0.0.1만).
- 어떤 스크립트도 .env cat / raw 변수 echo 안 함.
- 어떤 스크립트도 git/pip 실행 안 함.
- 메타 테스트 7개가 위 invariant 검증.

### 2.4 테스트
- 신규 test_helper_scripts.py: 존재/실행권한/shebang/bash syntax/safe env 강제/no-secret pattern/no-git-or-pip/127.0.0.1-only.
- 기존 172 회귀 0.

### 2.5 README
- 초보자용 실행 방법 (mvp-020) 단락. 스크립트 표 + 예시 + 안전 가드.

### 2.6 다음 mvp 후보
- snapshot 파일을 받아 tick.sh이 자동으로 dry-run에 입력하는 옵션
- GUI 통합(현재 ai-team web GUI는 별도 영역)
- 백그라운드 cron 등록 helper

## 3. Safety Confirmation
- live trading 활성화 신규 경로 0건.
- KIS endpoint URL/TR ID 0건.
- 외부 HTTP 라이브러리 import 0건(스크립트는 curl만 사용).
- raw credentials 출력 0건.
- .env 미접촉.
- /paper/dry-run/* + /reports/dry-run/* 외 API 호출 0건.
- app/, tests/(test_helper_scripts 외), config.py, .env.example, .gitignore 미변경.
- mvp-001..mvp-019 산출물 미변경.
- commit/push/merge/deploy/pip install 자동화 0건.

## 4. Test Results
- compileall: PASS
- pytest 172(기존) + 7(신규) = 179 PASS
- bash -n scripts/*.sh: PASS

## 5. Remaining TODOs
- 사용자가 KIS 공식 문서값을 채우는 별도 mvp 후 HTTP 연결.
- 워크트리 staging은 별도 commit으로 정리.
```

## 5. 테스트 기준

1. `.venv/bin/python -m compileall app tests` 종료코드 0.
2. `.venv/bin/python -m pytest -p no:cacheprovider` 종료코드 0. 기존 172 + 신규 약 7개 PASS.
3. `bash -n scripts/*.sh` 종료코드 0 모든 스크립트.
4. 모든 8개 스크립트(`_common.sh` 포함)가 `os.X_OK` 권한 보유.
5. `_common.sh`가 4개 안전 env를 `export`함.
6. 모든 스크립트에 `KIS_APP_KEY` / `KIS_APP_SECRET` / `KIS_ACCOUNT_NO` / `cat .env` / `${KIS_APP_KEY}` 같은 raw 비밀 패턴이 0건.
7. 모든 스크립트에 `git commit` / `git push` / `git merge` / `pip install`이 0건.
8. `start_server.sh`이 `127.0.0.1`에만 바인딩(`0.0.0.0` 부재).
9. `git diff --stat`에 mvp-020 외 변경 없음.
10. `.env` staged/committed 없음.

## 6. 리뷰 체크리스트

- [ ] 8개 스크립트(`_common.sh` + 7개 사용자 스크립트) 모두 존재 + 실행 권한.
- [ ] 모든 스크립트가 `#!/usr/bin/env bash` 또는 동등한 shebang.
- [ ] 모든 스크립트가 `bash -n` 통과.
- [ ] `_common.sh`이 4개 안전 env를 force export.
- [ ] `start_server.sh`이 `127.0.0.1`에만 바인딩, `0.0.0.0` 부재.
- [ ] `tick.sh`이 not-running 자동 start 로직 보유.
- [ ] `analyze.sh`이 run_dir 추출 + 로컬 `analysis_report.md` 경로 출력.
- [ ] `smoke_check.sh`이 6개를 `|| true`로 순차 실행.
- [ ] 어떤 스크립트도 `.env` cat / `KIS_*` raw echo 안 함.
- [ ] 어떤 스크립트도 `git commit/push/merge` / `pip install` 실행 안 함.
- [ ] 메타 테스트 7개(존재/권한/shebang/syntax/safe env/no-secret/no-git-pip/localhost) PASS.
- [ ] 기존 172 회귀 없음.
- [ ] README 단락 추가, 기존 단락 변경 없음.
- [ ] `app/`, `app/config.py`, `app/api/*` 미변경.
- [ ] `.env.example`, 프로젝트 `.gitignore`, 루트 `.gitignore` 미변경.
- [ ] mvp-001..mvp-019 산출물 미변경.
- [ ] `git diff --stat`에 mvp-020 외 변경 없음.
- [ ] `.env` staged/committed 없음.
- [ ] commit/push/merge/deploy 자동화 없음.
- [ ] `patch.md` 5섹션 + Implementation Summary 6단락 완성.
