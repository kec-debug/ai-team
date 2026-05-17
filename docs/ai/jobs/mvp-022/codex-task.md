# Codex Task — mvp-022: `.env` 자동 로딩 (CWD 무관) + KIS 설정 표시 확인

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-022/plan.md` and `docs/ai/jobs/mvp-022/request.ko.md` first.

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-022`
- 대상: `projects/paper-trading/app/config.py` 한 함수 수정 + 테스트 4개 + README 단락 + patch.md.
- 핵심 변경: `load_settings()`이 `_project_dir()/.env`를 명시적 경로로 `load_dotenv(..., override=False)` 호출.

## 사전 점검 (Codex 첫 단계)

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m pytest -p no:cacheprovider --co -q 2>&1 | tail -3
# expect: 189+ tests collected

grep -q "load_dotenv" app/config.py && echo "OK load_dotenv import"
grep -q "kis_env" app/config.py && echo "OK Settings.kis_env"
grep -q "kis_app_key.*repr=False" app/config.py && echo "OK kis_app_key repr=False"
grep -q "^KIS_ENV=" .env.example && echo "OK .env.example KIS_ENV"
grep -q "^!\.env\.example" /root/ai-dev-center/projects/ai-team/.gitignore && echo "OK root .gitignore allows .env.example"
test -d .venv && echo "OK venv"
```

위 6개 OK → 진행.

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials, KIS app key/secret/account/token 변경/생성/읽기/노출 금지.
- 외부 HTTP 라이브러리 import 금지.
- KIS endpoint URL/TR ID/payload/header 추가 금지.
- 실주문 코드 신설 금지. 실제 KIS HTTP 호출 코드 신설 금지.
- live trading 활성화 코드 경로 신설 금지. `ALLOW_MARKET_ORDERS=true` 허용 금지.
- `OrderType`에 MARKET 멤버 추가 금지.
- RiskEngine/OMS 우회 코드 경로 신설 금지.
- Strategy 패키지가 `app.broker.kis*` import 금지(기존 상태 유지).
- 화면/응답/log/repr 어디에도 `KIS_APP_KEY` / `KIS_APP_SECRET` / `KIS_ACCOUNT_NO` raw 값 노출 금지.
- `Settings`의 KIS 비밀 3필드의 `field(repr=False)` 제거 금지.
- `load_dotenv` 호출에 **`override=True`** 사용 금지(이 옵션 누락 또는 `override=False` 명시여야 함).
- `_project_dir()`이 사용자 입력/env로 우회 가능한 경로 신설 금지(`__file__` 기반만).
- 임의 shell 명령 입력 UI/API 신설 금지.
- 본 작업 범위 외 파일 변경 금지. mvp-001..mvp-021 산출물 미변경.
- `pip install` 실행 금지.
- `app/api/server.py`, `app/api/routes.py`, `app/main.py`, `app/static/*` 변경 금지.
- `app/broker/*`, `app/runtime/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/domain/*`, `app/portfolio/*`, `app/session/*`, `app/reports/*` 변경 금지.
- `.env`, `.env.example`, 프로젝트 `.gitignore`, 루트 `.gitignore` 변경 금지(이미 안전 룰 보유; 검증만).

## 수정 허용 위치

### 신규

- `docs/ai/jobs/mvp-022/patch.md`

### 수정 가능

- `projects/paper-trading/app/config.py` (`_project_dir()` helper + `load_dotenv` 명시 경로 + `override=False`만)
- `projects/paper-trading/tests/test_kis_config.py` (3개 신규 테스트만 추가, 기존 테스트 변경 없음)
- `projects/paper-trading/tests/test_api_paper_status.py` (1개 신규 테스트만 추가, 기존 테스트 변경 없음)
- `projects/paper-trading/README.md` (mvp-022 단락 추가, 기존 단락 변경 없음)

### 절대 미수정

- `projects/paper-trading/app/api/server.py`, `app/api/routes.py`, `app/main.py`, `app/static/*`
- `projects/paper-trading/app/broker/*`, `app/runtime/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/domain/*`, `app/portfolio/*`, `app/session/*`, `app/reports/*`
- `projects/paper-trading/.env`, `.env.example`
- `projects/paper-trading/.gitignore`, 루트 `.gitignore`
- mvp-001..mvp-021 산출물
- 다른 테스트 파일 (`test_dashboard.py`, `test_helper_scripts.py`, `test_dry_run_*.py`, `test_kis_auth_client.py`, `test_kis_account_client.py`, `test_kis_market_data_client.py`, `test_kis_order_*.py`, `test_broker_interface.py`, `test_kill_switch.py`, `test_config.py`, `test_models.py`, `test_oms.py`, `test_paper_broker.py`, `test_paper_runner.py`, `test_flow.py`, `test_risk_engine.py`, `test_strategy_premarket_gap.py`, `test_alpaca_paper_stub.py`, `test_reports_api.py`, `test_kis_http_boundaries.py`, `test_session_router.py`, `test_status_modules.py`, `test_missing_official_values_doc.py`)
- `imports/`, `web/`, `prompts/`, `scripts/`(mvp-020 산출물), 기존 `docs/`(`docs/ai/jobs/mvp-022/` 외)

## 구현 작업

`plan.md` §4 코드를 그대로 따른다. 다음은 빠뜨리기 쉬운 항목:

### 1) `app/config.py` 변경

기존 import 보존 + `from pathlib import Path` 보장(없으면 추가).

`Settings` 정의 위쪽 또는 helper 영역에 추가:

```python
def _project_dir() -> Path:
    """Return projects/paper-trading directory based on this module's location.

    app/config.py -> app/ -> project root. Independent of process CWD so .env
    auto-loading works no matter where the server is started from.
    """
    return Path(__file__).resolve().parent.parent
```

`load_settings()` 첫 부분을 다음으로 교체:

```python
def load_settings() -> Settings:
    env_file = _project_dir() / ".env"
    if env_file.is_file():
        load_dotenv(dotenv_path=env_file, override=False)
    else:
        load_dotenv(override=False)  # graceful fallback; no error if missing
    mode = TradingMode(os.getenv("TRADING_MODE", TradingMode.PAPER.value).lower())
    # ... 기존 로직 그대로 유지 ...
```

**핵심 불변식:**

- `override=False` 명시 — shell env가 우선.
- `_project_dir()`은 `Path(__file__).resolve()` 기반만 사용.
- 기존 paper/live/market_orders/kill_switch/KIS 검증 로직 한 줄도 변경하지 마.
- `Settings` 클래스 필드 추가/제거/변경 0건.

### 2) `tests/test_kis_config.py` 변경

기존 테스트 모두 보존. 파일 끝(또는 자연스러운 위치)에 `plan.md` §4.3의 3개 테스트 그대로 추가:

- `test_load_settings_reads_env_from_project_dir`
- `test_load_settings_works_without_env_file`
- `test_load_settings_does_not_override_existing_shell_env`

각 테스트는 `monkeypatch.setattr("app.config._project_dir", lambda: tmp_path)`로 `_project_dir`을 가짜로 교체해 production 격리.

**경고:** 테스트는 fake 값(`"12345678"`, `"fake-key"`, `"fake-secret"`)만 사용. 실제 KIS 값 절대 금지.

### 3) `tests/test_api_paper_status.py` 변경

기존 테스트 모두 보존. 파일 끝에 `plan.md` §4.4의 `test_paper_status_kis_config_loaded_when_env_present` 추가.

핵심 단언:

```python
assert body["kis_config_loaded"] is True
assert body["account_no_masked"].startswith("***")
assert body["secret_exposed"] is False

text = r.text
for needle in ("fake-key", "fake-secret", "12345678"):
    assert needle not in text
```

응답 본문 텍스트가 raw 값(fake-key/fake-secret/8-digit account) 미포함을 검증.

### 4) README 변경

`plan.md` §4.5의 "## `.env` 자동 로딩 (mvp-022)" 단락을 mvp-021 단락 뒤에 추가. 기존 단락 변경 없음.

README는 다음을 명확히 언급:

- `_project_dir()`이 CWD 무관하게 `.env` 자동 로딩.
- `override=False`로 shell이 export한 안전 env가 `.env`보다 우선.
- 권장 실행: `./scripts/start_server.sh` (mvp-020, `127.0.0.1`만).
- 직접 uvicorn: `--host 127.0.0.1` 권장, `--host 0.0.0.0` 비권장.
- 사용자가 `.env`의 `KIS_PAPER_*` (옛 명명)을 `KIS_*` (새 명명)로 매핑해야 함(SSH에서 직접, 채팅 외부).

### 5) 검증

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

기대: 기존 189 + 신규 4 = 193 PASS. compileall exit 0. mvp-022 외 변경 없음.

### 6) `docs/ai/jobs/mvp-022/patch.md`

`plan.md` §4.7 템플릿 그대로 채운다. 실제 KIS 값 미인용. Implementation Summary 8단락 (요청의 "완료 후" 항목과 1:1).

## 완료 정의 (Done)

- `app/config.py`에 `_project_dir()` helper 추가 + `load_dotenv(dotenv_path=..., override=False)` 명시.
- 기존 paper/live/market_orders/kill_switch/KIS 가드 로직 변경 0건.
- `Settings` 필드/구조 변경 0건.
- `tests/test_kis_config.py`에 3개 신규 테스트 추가, 기존 테스트 변경 없음.
- `tests/test_api_paper_status.py`에 1개 신규 테스트 추가, 기존 테스트 변경 없음.
- 모든 신규 테스트가 `tmp_path` + `monkeypatch.setattr`로 production 격리.
- 응답 본문 텍스트 검사로 raw `fake-key`/`fake-secret`/`12345678` 미노출 확인.
- README에 mvp-022 단락 추가, 기존 단락 미변경, `0.0.0.0` 비권장 명시.
- `app/api/server.py`, `app/api/routes.py`, `app/main.py`, `app/static/*` 변경 0건.
- `app/broker/*`, `app/runtime/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/domain/*`, `app/portfolio/*`, `app/session/*`, `app/reports/*` 변경 0건.
- `.env`, `.env.example`, 프로젝트 `.gitignore`, 루트 `.gitignore` 변경 0건.
- mvp-001..mvp-021 산출물 변경 0건.
- 기존 189 회귀 0건.
- mvp-022 신규 4 PASS.
- `OrderType.MARKET` 부재 유지.
- 외부 HTTP 라이브러리 import 0건.
- KIS endpoint URL/TR ID 코드 0건.
- `git diff --stat`에 mvp-022 외 변경 없음.
- `.env` staged/committed 없음.
- `patch.md` 5섹션 + Implementation Summary 8단락 완성.
- commit/push/merge/deploy 자동화 없음.
