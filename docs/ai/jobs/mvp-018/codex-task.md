# Codex Task — mvp-018: 장시간 KIS paper / dry-run 검증 runner

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-018/plan.md` and `docs/ai/jobs/mvp-018/request.ko.md` first.

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-018`
- 대상 디렉터리: `projects/paper-trading/`
- 본 작업은 stateful `DryRunController` + 리포트 파일 writer + 4개 API 엔드포인트 + 테스트를 만든다. **실제 KIS HTTP 호출 0건**, **`app/broker/kis.py` 미변경**, **`app/runtime/paper_runner.py` 미변경**.

## 사전 점검 (Codex 첫 단계)

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m pytest -p no:cacheprovider --co -q 2>&1 | tail -3
# expect: "131 tests collected" (or higher)

grep -q "class PaperRunner" app/runtime/paper_runner.py && echo "OK PaperRunner"
grep -q "kis_order_dry_run" app/config.py && echo "OK config.kis_order_dry_run"
grep -q "kill_switch_engaged" app/config.py && echo "OK config.kill_switch"
grep -q "class KisHttpClient" app/broker/kis.py && echo "OK KisHttpClient"
test -d ../../docs/kis && echo "OK docs/kis present" || echo "WARN docs/kis missing"
test -d .venv && echo "OK venv"
```

위 6개 OK → 진행. 누락이 있으면 `patch.md` Remaining TODOs에 명시하고 작업 중단.

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials, KIS 실제 endpoint URL/TR ID/payload/app key/app secret/account number/token 변경/생성/읽기/노출 금지.
- 외부 HTTP 라이브러리(`requests`, `httpx`, `aiohttp`, `urllib3` 등) 어떤 파일에도 import 금지.
- 실주문 코드, 실제 HTTP 호출 코드 신설 금지.
- `app/broker/kis.py` **한 줄도 변경 금지** (KIS endpoint/TR ID/payload 추가 금지, HTTP 라이브러리 import 금지).
- `app/runtime/paper_runner.py` **변경 금지** (DryRunController가 호출만 함).
- live trading 활성화 금지.
- `OrderType`에 MARKET 멤버 추가 금지.
- RiskEngine/OMS 우회 코드 경로 신설 금지.
- Strategy 패키지가 `app.broker.kis*` import 금지(grep 검증).
- OMS의 `_risk`/`_broker` private 유지. KIS 활성 broker 연결 금지.
- `/paper/status`나 어떤 응답/리포트에 raw key/secret/account/token 노출 금지.
- 리포트 dict에 알려진 secret 키 이름(`app_key`, `app_secret`, `account_no`, `access_token`, `authorization` 등) 포함 시 `dump_safe`가 `UnsafeReportPayloadError`로 차단.
- 임의 shell 명령 입력 UI/API 신설 금지.
- 본 작업 범위 외 파일 변경 금지. mvp-001..mvp-017 산출물, `imports/`, `web/`, `prompts/`, `scripts/`, `examples/`, 기존 `docs/`(`docs/kis/` + mvp-018 외) 미변경.
- `docs/kis/MISSING_OFFICIAL_VALUES.md` 변경 금지(mvp-014-017-bundle 산출물).
- `pip install` 실행 금지.
- asyncio 백그라운드 자동 tick loop 신설 금지(본 mvp는 명시적 tick만).

## 수정 허용 위치

### 신규

- `projects/paper-trading/app/runtime/dry_run.py`
- `projects/paper-trading/app/runtime/dry_run_report.py`
- `projects/paper-trading/tests/test_dry_run_controller.py`
- `projects/paper-trading/tests/test_dry_run_reports.py`
- `projects/paper-trading/tests/test_dry_run_routes.py`
- `docs/ai/jobs/mvp-018/patch.md`

### 수정 가능

- `projects/paper-trading/app/config.py` (3개 신규 필드 + env 로딩)
- `projects/paper-trading/app/api/server.py` (lifespan에 `DryRunController` 추가, `app.state.dry_run_controller` 보관)
- `projects/paper-trading/app/api/routes.py` (4개 신규 엔드포인트 + `/paper/status`에 `dry_run_running` 한 줄)
- `projects/paper-trading/.env.example` (3개 신규 placeholder)
- `projects/paper-trading/.gitignore` (프로젝트, `reports/` 추가)
- `projects/paper-trading/README.md` (mvp-018 단락)
- `projects/paper-trading/tests/test_api_paper_status.py` (`dry_run_running` assertion)

### 절대 미수정

- `projects/paper-trading/app/broker/kis.py` — 한 줄도 바꾸지 마.
- `projects/paper-trading/app/runtime/paper_runner.py` — 한 줄도 바꾸지 마.
- `projects/paper-trading/app/broker/{base,paper,alpaca_paper}.py`
- `projects/paper-trading/app/oms/manager.py`, `app/risk/engine.py`, `app/strategy/*`, `app/domain/*`, `app/main.py`
- 루트 `.gitignore`
- 기존 테스트 파일 중 본 작업이 다루지 않는 것: `test_alpaca_paper_stub.py`, `test_broker_interface.py`, `test_config.py`, `test_flow.py`, `test_kill_switch.py`, `test_kis_*.py`, `test_missing_official_values_doc.py`, `test_models.py`, `test_oms.py`, `test_paper_broker.py`, `test_paper_runner.py`, `test_risk_engine.py`, `test_strategy_premarket_gap.py`.
- mvp-001..mvp-017 산출물.
- `docs/kis/MISSING_OFFICIAL_VALUES.md`.
- `imports/local-mvp/`.

## 구현 작업

`plan.md` §4 코드를 그대로 따른다. 다음은 빠뜨리기 쉬운 항목.

### 1) `app/config.py` (수정)

`Settings`에 3 필드 추가:

```python
dry_run_reports_dir: str = "reports/dry_run"
dry_run_max_errors_before_auto_stop: int = 10
dry_run_max_ticks: int | None = None
```

`load_settings()`에 추가:

```python
dry_run_reports_dir=_str_env("DRY_RUN_REPORTS_DIR") or "reports/dry_run",
dry_run_max_errors_before_auto_stop=_int_env("DRY_RUN_MAX_ERRORS_BEFORE_AUTO_STOP", 10),
dry_run_max_ticks=(_int_env("DRY_RUN_MAX_TICKS", 0) or None) if os.getenv("DRY_RUN_MAX_TICKS") else None,
```

기존 paper/live/market_orders/kill_switch/KIS/dry_run 가드/필드 변경 없음.

### 2) `app/runtime/dry_run_report.py` (신규)

`plan.md` §4.3 코드 그대로. 핵심:

- `dump_safe(payload)` — 재귀적으로 dict 키 이름이 `_FORBIDDEN_KEY_FRAGMENTS`(`app_key`, `appkey`, `appKey`, `app_secret`, `appsecret`, `appSecret`, `account_no`, `accountNo`, `cano`, `access_token`, `accessToken`, `authorization`, `secret`) 중 하나라도 (case-insensitive substring으로) 매칭 시 `UnsafeReportPayloadError` raise.
- `make_run_dir(base_dir, started_at) -> Path` — `run_YYYY-MM-DDThh-mm-ss/` 생성(`parents=True, exist_ok=True`).
- `append_event(run_dir, event)` — JSONL 한 줄 append, `default=str` 사용해 datetime 등 serialize.
- `write_summary(run_dir, summary)` — overwrite, indent=2.
- `append_order(run_dir, order)` — CSV header 없으면 자동 추가, `extrasaction="ignore"` + 고정 컬럼 `_ORDER_COLUMNS`.

### 3) `app/runtime/dry_run.py` (신규)

`plan.md` §4.4 코드 그대로. 핵심 불변식:

- 어떤 분기에서도 `app.broker.kis`의 메서드를 직접 호출하지 않음. 호출은 오직 `self._runner.run_once(snapshots)`(PaperRunner).
- `start()`이 already-running이면 `RuntimeError`.
- `stop(reason="manual")`이 not-running이면 `RuntimeError`.
- `tick()`이 not-running이면 `RuntimeError`.
- `tick()` 최상단에서 `self._settings.kill_switch_engaged`면 즉시 `blocked_kill_switch` 반환, strategy 호출 안 함, `kill_switch_blocked_ticks += 1`.
- 에러 임계치(`errors_total >= settings.dry_run_max_errors_before_auto_stop`) 도달 시 `_auto_stop("error_threshold")`.
- max_ticks 도달 시 `_auto_stop("max_ticks_reached")`.
- `_reports_dir()` 가 절대 경로면 `RuntimeError("dry_run_reports_dir must be a project-relative path")`.
- `summary()` 항상 `"secret_exposed": False` 포함. raw credentials 미포함.

PaperRunner.run_once는 일반 Exception을 catch하지 않으므로 `tick()`의 `try/except Exception`이 방어층. 자체 raise는 없지만 broker.submit 등에서 RuntimeError가 올 수 있음(OMS reject 등). 그 경우 PaperRunner.run_once는 이미 `oms_error`로 감싸 반환하므로 본 try/except는 거의 작동 안 함(테스트가 force-raise로 검증).

### 4) `app/api/server.py` (수정)

lifespan 내부 PaperRunner 만든 직후에:

```python
from app.runtime.dry_run import DryRunController
from pathlib import Path
project_dir = Path(__file__).resolve().parents[2]
dry_run_controller = DryRunController(settings, app.state.runner, project_dir)
app.state.dry_run_controller = dry_run_controller
```

기존 와이어링은 그대로. import는 lifespan 안에 둬도 무방하며 module top-level로 옮겨도 됨.

### 5) `app/api/routes.py` (수정)

`plan.md` §4.6 그대로:

- 4개 신규 엔드포인트(`POST /paper/dry-run/start`, `stop`, `tick`; `GET /paper/dry-run/status`).
- `DryRunTickRequest` Pydantic 모델 (snapshots: list[StrategyInput] = []).
- `/paper/status` 응답에 `"dry_run_running": bool(...)` 한 줄 추가. 기존 모든 필드 보존.
- 모든 에러 RuntimeError → HTTPException(409, detail=str(exc)).
- 응답에 raw credentials 미포함.

### 6) `.env.example` (수정)

`KIS_ORDER_DRY_RUN=true` 다음에:

```
DRY_RUN_REPORTS_DIR=reports/dry_run
DRY_RUN_MAX_ERRORS_BEFORE_AUTO_STOP=10
DRY_RUN_MAX_TICKS=
```

다른 라인 변경 없음.

### 7) `.gitignore` (프로젝트) 수정

기존 룰 보존하면서 한 줄 추가:

```
reports/
```

루트 `.gitignore`는 손대지 않는다.

### 8) `README.md` (수정)

`plan.md` §4.9의 "## 장시간 KIS dry-run 검증 (mvp-018)" 단락 추가. 적절한 위치(KIS 섹션 뒤). 기존 단락 변경 없음.

### 9) 테스트

`plan.md` §4.10 그대로.

**테스트 설계 가이드:**

- `tmp_path` fixture를 사용해 임시 reports 디렉터리 만들기.
- `DryRunController` 직접 인스턴스화 테스트(`test_dry_run_controller.py`)에서는 `Settings(dry_run_reports_dir=str(tmp_path/"reports"))`를 만들고, `PaperRunner` mock 또는 실제(`PaperRunner(settings, NoopStrategy(settings), OMS(settings, RiskEngine(settings), PaperBroker()))`)를 주입.
- 라우트 테스트(`test_dry_run_routes.py`)는 `TestClient(create_app())` 사용. 이 경우 `DryRunController`가 프로젝트 디렉터리의 `reports/dry_run/`에 파일을 만들 수 있음 → 테스트 후 cleanup 필요. 두 가지 안전 옵션:
  - (권장) 환경변수 `DRY_RUN_REPORTS_DIR`을 `tmp_path/"reports"`로 monkeypatch 후 `create_app()` 호출 → `reports/`는 절대경로지만 plan에서 절대경로 reject. **상대경로 제약 회피**: tmp 디렉터리에서 작업하는 대신, 그냥 `projects/paper-trading/reports/test_runs/`처럼 프로젝트-상대 디렉터리를 사용하고 테스트가 끝난 뒤 `shutil.rmtree` 정리.
  - 또는 controller 측 `_reports_dir()` 검증 완화. **권장하지 않음** — plan의 path traversal 방어를 유지.
- 깔끔한 패턴: monkeypatch.setenv("DRY_RUN_REPORTS_DIR", "reports/test_runs") + autouse fixture가 `projects/paper-trading/reports/test_runs/`를 finally cleanup.
- `dump_safe`는 case-insensitive substring 매칭이므로 `{"order_id":"x"}`는 통과해야 함 (forbidden fragment에 "id"는 없음). 테스트가 false-positive 없음을 확인.

### 10) 검증

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

기대: 기존 131 + 신규 ~27 = ~158 PASS. compileall exit 0. mvp-018 외 변경 없음.

### 11) `docs/ai/jobs/mvp-018/patch.md`

`plan.md` §4.12 템플릿 그대로. 실제 KIS 값 미인용. mvp-018의 8가지 책임(state machine, counters, 리포트, safety, API, kill/auto-stop, tests, 다음 mvp) 모두 정리.

## 완료 정의 (Done)

- `app/runtime/dry_run.py` + `app/runtime/dry_run_report.py` 신규 생성.
- `DryRunController` 상태 머신: idle→running→stopped/auto_stopped. double-start/stop-when-not-running/tick-when-not-running 모두 `RuntimeError`.
- `tick()`: kill_switch면 `blocked_kill_switch`, max_ticks 도달 시 `auto_stopped("max_ticks_reached")`, errors_total 임계 도달 시 `auto_stopped("error_threshold")`.
- `dump_safe`가 알려진 secret 키 이름 substring(case-insensitive) 매칭 시 `UnsafeReportPayloadError`.
- 리포트 writer 3개(events.jsonl/summary.json/orders.csv)가 정상 동작 + `dump_safe` 통과 dict만 받음.
- `summary()`가 `secret_exposed: False` 포함, raw credentials 미포함.
- 4개 `/paper/dry-run/*` 엔드포인트 정상 + 409 에러 분기.
- `/paper/status`에 `dry_run_running` 한 줄 추가, 기존 필드 모두 보존.
- `Settings`에 3 신규 필드 + env 로딩. 기본값 안전.
- `.env.example`에 3 신규 placeholder.
- `.gitignore`(프로젝트)에 `reports/` 추가.
- README에 mvp-018 단락.
- 기존 131 회귀 없음 + 신규 ~27 PASS.
- `app/runtime/paper_runner.py` 변경 0줄.
- `app/broker/kis.py` 변경 0줄.
- 외부 HTTP 라이브러리 import 0건.
- KIS endpoint URL/TR ID 0건.
- `OrderType.MARKET` 부재 유지.
- Strategy 패키지가 `app.broker.kis*` import 0건 유지.
- `git diff --stat`에 mvp-018 외 변경 없음.
- `.env` staged/committed 없음.
- `patch.md` 5섹션 + Implementation Summary 8단락 완성.
- commit/push/merge/deploy 자동화 없음.
