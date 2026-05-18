# Codex Task — mvp-019: dry-run 결과 리포트 분석 + 전략 개선 루프 입력 문서

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-019/plan.md` and `docs/ai/jobs/mvp-019/request.ko.md` first.

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-019`
- 대상 디렉터리: `projects/paper-trading/`
- 본 작업은 **read-only analyzer** + CLI + 2개 신규 API 엔드포인트 + 테스트. mvp-018이 만든 dry-run 산출물(`reports/dry_run/run_<ts>/{events.jsonl, summary.json, orders.csv}`)을 읽어 분석 리포트 3종(analysis_summary.json, analysis_report.md, claude_review_input.md)을 같은 디렉터리에 생성한다. **실제 주문/HTTP/Strategy 변경 없음.**

## 사전 점검 (Codex 첫 단계)

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m pytest -p no:cacheprovider --co -q 2>&1 | tail -3
# expect: 155+ tests collected

grep -q "class DryRunController" app/runtime/dry_run.py && echo "OK DryRunController"
grep -q "make_run_dir" app/runtime/dry_run_report.py && echo "OK dry_run_report"
test -d .venv && echo "OK venv"
test -d app/reports && echo "WARN app/reports already exists" || echo "OK app/reports absent (will be created)"
```

위 4개 OK + app/reports absent → 진행. 누락 시 `patch.md` Remaining TODOs에 기록 후 중단.

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials, KIS 실제 endpoint URL/TR ID/payload/app key/app secret/account number/token 변경/생성/읽기/노출 금지.
- 외부 HTTP 라이브러리(`requests`, `httpx`, `aiohttp`, `urllib3` 등) `app/reports/`에 import 금지.
- `app/reports/`에서 `app.broker.kis`, `app.config` import 금지(API routes.py만 settings 사용 가능 — analyzer 자체는 파일 path만 받는 read-only 모듈).
- 실주문 코드, 실제 HTTP 호출 코드 신설 금지.
- `app/broker/kis.py`, `app/runtime/dry_run.py`, `app/runtime/dry_run_report.py`, `app/runtime/paper_runner.py`, `app/oms/`, `app/risk/`, `app/strategy/`, `app/domain/`, `app/portfolio/`, `app/session/`, `app/main.py`, `app/config.py`, `app/api/server.py`, `.env.example`, 프로젝트/루트 `.gitignore` **변경 금지**.
- live trading 활성화 금지.
- `OrderType`에 MARKET 멤버 추가 금지.
- RiskEngine/OMS 우회 코드 경로 신설 금지.
- Strategy 패키지가 `app.broker.kis*` import 금지 유지.
- LLM/agent가 본 analyzer 출력을 기반으로 직접 주문/Strategy 코드를 자동 수정하는 path 신설 금지. **사람용 advisory 문서만 생성**.
- `/reports/dry-run/analyze`가 path traversal(`..`, 절대경로, reports 외부) 받으면 400/404로 거절.
- analyzer 출력에 알려진 secret 키 이름(`app_key`, `app_secret`, `account_no`, `access_token`, `authorization`, `secret`) 포함 시 `dump_safe`가 `UnsafeReportPayloadError` raise. `secret_exposed` 정확 매칭만 whitelist.
- 임의 shell 명령 입력 UI/API 신설 금지.
- 본 작업 범위 외 파일 변경 금지. mvp-001..mvp-018 산출물 미변경.
- `pip install` 실행 금지.

## 수정 허용 위치

### 신규

- `projects/paper-trading/app/reports/__init__.py`
- `projects/paper-trading/app/reports/dry_run_analyzer.py`
- `projects/paper-trading/app/reports/render.py`
- `projects/paper-trading/app/reports/__main__.py`
- `projects/paper-trading/tests/test_dry_run_analyzer.py`
- `projects/paper-trading/tests/test_reports_api.py`
- `docs/ai/jobs/mvp-019/patch.md`

### 수정 가능

- `projects/paper-trading/app/api/routes.py` (2개 신규 엔드포인트만 추가; 기존 핸들러 변경 금지)
- `projects/paper-trading/README.md` (mvp-019 단락 추가; 기존 단락 변경 없음)

### 절대 미수정

- `projects/paper-trading/app/broker/*`
- `projects/paper-trading/app/runtime/*` (dry_run.py, dry_run_report.py, paper_runner.py 한 줄도 변경 금지)
- `projects/paper-trading/app/oms/`, `app/risk/`, `app/strategy/`, `app/domain/`, `app/portfolio/`, `app/session/`
- `projects/paper-trading/app/main.py`, `app/config.py`, `app/api/server.py`
- `projects/paper-trading/.env.example`
- 프로젝트 `.gitignore`, 루트 `.gitignore`
- 기존 테스트 중 본 작업이 다루지 않는 것
- mvp-001..mvp-018 산출물
- `docs/kis/MISSING_OFFICIAL_VALUES.md`, `imports/`

## 구현 작업

`plan.md` §4 코드를 그대로 따른다. 핵심 요점:

### 1) `app/reports/__init__.py`

빈 패키지 마커 + docstring 한 줄.

### 2) `app/reports/dry_run_analyzer.py`

`plan.md` §4.3 코드 그대로. 핵심:

- import: 표준 라이브러리만(`csv`, `json`, `collections`, `dataclasses`, `datetime`, `pathlib`, `typing`). `app.config`/`app.broker.kis`/외부 HTTP 라이브러리 import 금지.
- `dump_safe` substring 매칭 + `secret_exposed` whitelist(mvp-018 패턴과 일관).
- `load_summary`/`load_events`/`load_orders` — 파일 없거나 손상 시 robust 처리.
- `analyze_run(run_dir)` — events 기반 symbol/blocker 집계.
- `compute_suggestions`/`compute_warnings` 휴리스틱.
- `find_latest_run_dir` — `run_*` 디렉터리 정렬.
- `write_analysis_files(result)` — 3개 파일 모두 dump_safe 통과 후 write.

### 3) `app/reports/render.py`

`plan.md` §4.4 코드 그대로. `render_analysis_report`와 `render_claude_review_input` 두 함수.

`claude_review_input.md` 본문에 다음 명시:

- "LLM/Agent가 본 문서를 읽어도 직접 주문을 만들거나 KIS를 직접 호출하지 않습니다."
- "모든 전략 변경은 사람이 plan/codex-task를 작성한 뒤 별도 mvp로 진행됩니다."
- Safety reminders 단락(live 비활성, KIS_ORDER_DRY_RUN=true, 시장가 금지, OMS/RiskEngine 우회 금지, KIS endpoint 추측 금지).

### 4) `app/reports/__main__.py`

`plan.md` §4.5 코드 그대로. CLI:

```bash
.venv/bin/python -m app.reports --latest
.venv/bin/python -m app.reports --run-dir reports/dry_run/run_<ts>
.venv/bin/python -m app.reports --reports-dir <path>
```

exit code 0=성공 / 1=run_dir 못 찾음 / 2=분석 실패.

### 5) `app/api/routes.py` (수정)

2개 신규 엔드포인트만 추가. **기존 핸들러는 한 줄도 바꾸지 마.** `plan.md` §4.6 코드 그대로:

- `POST /reports/dry-run/analyze` (body: `AnalyzeRequest{run_dir: str | None}`, None이면 latest)
- `GET /reports/dry-run/latest`
- path 검증 헬퍼 `_reports_base`, `_resolve_run_dir`이 path traversal 거절.

import 추가:

```python
from app.reports.dry_run_analyzer import analyze_run, find_latest_run_dir, write_analysis_files
```

`json` import는 routes.py 상단에 이미 있으면 그대로, 없으면 추가.

### 6) README 추가

`plan.md` §4.7 단락 그대로. KIS 섹션 또는 mvp-018 단락 뒤에 추가. 기존 단락 변경 없음.

### 7) 테스트

`plan.md` §4.8 코드 그대로.

**핵심 주의사항:**

- `tests/test_dry_run_analyzer.py`는 `tmp_path` fixture 사용 — 프로젝트 디렉터리 미접촉.
- `tests/test_reports_api.py`는 monkeypatch로 `DRY_RUN_REPORTS_DIR=reports/test_runs_mvp019` 설정 후 `create_app()` → 프로젝트 내부 디렉터리지만 자동 cleanup. 테스트 종료 시 `shutil.rmtree(base, ignore_errors=True)`.
- 모든 fake 값은 `"12345678"`, `"fake-key"`, `"fake-secret"`만. 실제 KIS 값 절대 미사용.
- `secret_exposed` whitelist 동작 검증 테스트 포함.
- path traversal 거절 테스트 포함.

### 8) 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

저장소 루트:

```bash
git diff --stat
git status --short
```

기대: 기존 155 + 신규 약 17 = ~172 PASS. compileall exit 0. mvp-019 외 변경 없음.

### 9) `docs/ai/jobs/mvp-019/patch.md`

`plan.md` §4.10 템플릿 그대로. 실제 KIS 값 미인용. Implementation Summary 8단락 모두 채움.

## 완료 정의 (Done)

- `app/reports/` 4파일 신규 생성.
- `analyze_run`이 빈 run_dir / 정상 run_dir / invalid JSON 라인 모두 안전 처리.
- `dump_safe`가 secret 키 substring 매칭 거절 + `secret_exposed` whitelist.
- `write_analysis_files`이 3개 파일(`analysis_summary.json`, `analysis_report.md`, `claude_review_input.md`) 생성 + 모두 dump_safe 통과.
- `analysis_summary.json`에 `secret_exposed: False` 명시.
- CLI `python -m app.reports --help` 정상.
- `POST /reports/dry-run/analyze` + `GET /reports/dry-run/latest` 정상. path traversal 400/404.
- `app/reports/`에 `app.broker.kis` / `app.config` / HTTP 라이브러리 import 0건.
- `OrderType.MARKET` 부재 유지.
- Strategy 패키지가 `app.broker.kis*` import 0건 유지.
- mvp-018에서 변경된 `app/runtime/dry_run.py`/`dry_run_report.py`/`paper_runner.py` 한 줄도 변경 없음.
- 기존 155 회귀 없음.
- mvp-019 신규 약 17 PASS.
- `git diff --stat`에 mvp-019 외 변경 없음.
- `.env` staged/committed 없음.
- `patch.md` 5섹션 + Implementation Summary 8단락 완성.
- commit/push/merge/deploy 자동화 없음.
