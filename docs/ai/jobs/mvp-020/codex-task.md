# Codex Task — mvp-020: 초보자용 실행 스크립트 추가

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-020/plan.md` and `docs/ai/jobs/mvp-020/request.ko.md` first.

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-020`
- 대상 디렉터리: `projects/paper-trading/scripts/` (신규) + `projects/paper-trading/tests/` + `projects/paper-trading/README.md`.
- 본 작업은 **shell scripts 8개 + 메타 테스트 + README 단락**만 추가. `app/` 코드 변경 0건. KIS HTTP / Strategy / OMS / RiskEngine / Broker 변경 0건.

## 사전 점검 (Codex 첫 단계)

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m pytest -p no:cacheprovider --co -q 2>&1 | tail -3
# expect: 172 tests collected (or higher)

test -f app/api/server.py && echo "OK server.py"
grep -q "paper/dry-run/start" app/api/routes.py && echo "OK dry-run routes"
grep -q "reports/dry-run/analyze" app/api/routes.py && echo "OK reports routes"
test -f .venv/bin/uvicorn && echo "OK uvicorn"
test -d scripts && echo "WARN scripts/ exists" || echo "OK scripts/ absent"
command -v curl >/dev/null && echo "OK curl"
```

위 6개 OK → 진행.

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 금지(스크립트에 git 명령 0건).
- `.env`, secrets, credentials, KIS app key/secret/account number/token 변경/생성/읽기/노출 금지.
- 어떤 스크립트도 `.env`를 `cat`/`grep`/`echo`로 출력하지 않음.
- 어떤 스크립트도 `$KIS_APP_KEY` / `$KIS_APP_SECRET` / `$KIS_ACCOUNT_NO` 같은 raw 변수를 `echo`하지 않음.
- 외부 HTTP 라이브러리(`requests`, `httpx`, `aiohttp`, `urllib3` 등) import 금지(스크립트는 `curl`만 사용).
- 실제 KIS HTTP 호출 코드 신설 금지(스크립트는 paper-trading 서버 API만 호출, 그 API는 mvp-018/019에서 이미 안전).
- `pip install` 실행 금지.
- live trading 활성화 금지. 스크립트가 `LIVE_TRADING_ENABLED=true`나 `ALLOW_MARKET_ORDERS=true`나 `TRADING_MODE != paper`나 `KIS_ORDER_DRY_RUN=false`를 set하지 않음.
- `start_server.sh`이 `0.0.0.0`에 바인딩 금지. **`127.0.0.1`만 허용**.
- `OrderType.MARKET` 추가 금지(스크립트는 코드 변경 안 함이라 자동 충족).
- RiskEngine/OMS 우회 코드 경로 신설 금지.
- Strategy 패키지가 `app.broker.kis*` import 금지(스크립트는 app 변경 안 함이라 자동 충족).
- 임의 shell 명령 입력 UI/API 신설 금지.
- 본 작업 범위 외 파일 변경 금지. `app/`, `app/config.py`, `.env.example`, 프로젝트 `.gitignore`, 루트 `.gitignore`, 기존 테스트 파일(test_helper_scripts.py 외), mvp-001..mvp-019 산출물 미변경.

## 수정 허용 위치

### 신규

- `projects/paper-trading/scripts/_common.sh`
- `projects/paper-trading/scripts/start_server.sh`
- `projects/paper-trading/scripts/status.sh`
- `projects/paper-trading/scripts/start_dry_run.sh`
- `projects/paper-trading/scripts/tick.sh`
- `projects/paper-trading/scripts/stop_dry_run.sh`
- `projects/paper-trading/scripts/analyze.sh`
- `projects/paper-trading/scripts/smoke_check.sh`
- `projects/paper-trading/tests/test_helper_scripts.py`
- `docs/ai/jobs/mvp-020/patch.md`

### 수정 가능

- `projects/paper-trading/README.md` (mvp-020 단락 추가; 기존 단락 변경 없음)

### 절대 미수정

- `projects/paper-trading/app/` 전체
- `projects/paper-trading/.env.example`
- `projects/paper-trading/.gitignore`
- 루트 `.gitignore`
- `projects/paper-trading/tests/test_*.py` 중 본 작업이 추가하지 않는 것
- mvp-001..mvp-019 산출물
- `imports/`, `web/`, `prompts/`, 기존 `docs/`(`docs/ai/jobs/mvp-020/` 외)

## 구현 작업

`plan.md` §4 코드를 그대로 따른다. 다음은 빠뜨리기 쉬운 항목:

### 1) `scripts/_common.sh` (신규)

`plan.md` §4.2 코드 그대로. 핵심:

- `set -euo pipefail`
- 4개 `export` 라인(`TRADING_MODE=paper`, `LIVE_TRADING_ENABLED=false`, `ALLOW_MARKET_ORDERS=false`, `KIS_ORDER_DRY_RUN=true`)
- `BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"`, `PORT="${PORT:-8000}"`
- `HAS_JQ` + `pretty_print()` 함수
- `print_banner()` 함수
- shebang `#!/usr/bin/env bash`

### 2–8) 사용자 스크립트 7개

`plan.md` §4.3–§4.9 코드 그대로. 각 스크립트는:

- `#!/usr/bin/env bash`
- `set -euo pipefail`
- `SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"`로 자기 위치 찾기
- `. "$SCRIPT_DIR/_common.sh"`로 helper 로드
- `print_banner` 호출(선택)
- 해당 API curl 호출 + `pretty_print`

**핵심 불변식:**

- `start_server.sh`이 `--host 127.0.0.1`만 사용. `0.0.0.0` 절대 금지.
- `tick.sh`이 dry-run status에서 `running` 값을 추출해 not-running 시 `start` 먼저 호출.
- `analyze.sh`이 `run_dir`을 latest 응답에서 추출해 로컬 `analysis_report.md` 경로 출력.
- `smoke_check.sh`이 각 단계 호출에 `|| true` 붙여 개별 실패(409 등) 흡수.

### 9) 실행 권한 설정

Write 후 다음 명령으로 모두 `chmod +x`:

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
chmod +x scripts/_common.sh scripts/start_server.sh scripts/status.sh \
         scripts/start_dry_run.sh scripts/tick.sh scripts/stop_dry_run.sh \
         scripts/analyze.sh scripts/smoke_check.sh
```

### 10) `tests/test_helper_scripts.py` (신규)

`plan.md` §4.11 코드 그대로. 7개 테스트:

- `test_all_scripts_exist`
- `test_all_scripts_are_executable`
- `test_all_scripts_have_shebang`
- `test_all_scripts_pass_bash_syntax_check` — `bash -n` 사용
- `test_common_forces_safe_env_defaults` — 4개 `export ...=...` 패턴
- `test_no_script_prints_or_reads_secret_values` — 금지 패턴 부재
- `test_no_script_uses_git_or_pip` — 금지 명령 부재
- `test_start_server_uses_localhost` — `127.0.0.1` 있고 `0.0.0.0` 없음

### 11) `README.md` 변경

`plan.md` §4.12의 "## 초보자용 실행 방법 (mvp-020)" 단락을 mvp-019 단락 뒤(또는 적절한 위치)에 추가. 기존 단락 변경 없음.

### 12) 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
bash -n scripts/*.sh
```

저장소 루트:

```bash
git diff --stat
git status --short
```

기대: 기존 172 + 신규 7 = 179 PASS. compileall exit 0. `bash -n` 종료코드 0. mvp-020 외 변경 없음.

### 13) `docs/ai/jobs/mvp-020/patch.md`

`plan.md` §4.14 템플릿 그대로. 실제 KIS 값 미인용. Implementation Summary 6단락 모두 채움.

## 완료 정의 (Done)

- 8개 스크립트(`_common.sh` + 7) 신규 생성, 모두 실행 권한 보유.
- 모든 스크립트 `bash -n` 통과.
- `_common.sh`이 4개 안전 env 강제 export.
- `start_server.sh`이 `127.0.0.1`만 바인딩.
- `tick.sh`이 not-running 자동 start.
- `analyze.sh`이 `analysis_report.md` 로컬 경로 출력.
- `smoke_check.sh`이 6단계 순차 실행.
- 메타 테스트 7개 PASS.
- 기존 172 회귀 없음.
- README에 mvp-020 단락 추가, 기존 단락 미변경.
- `app/`, `app/config.py`, `app/api/*`, `.env.example`, `.gitignore` 변경 0건.
- mvp-001..mvp-019 산출물 변경 0건.
- 어떤 스크립트도 `git commit/push/merge` / `pip install` / `cat .env` / raw `KIS_*` echo 안 함.
- `git diff --stat`에 mvp-020 외 변경 없음.
- `.env` staged/committed 없음.
- `patch.md` 5섹션 + Implementation Summary 6단락 완성.
- commit/push/merge/deploy 자동화 없음.
