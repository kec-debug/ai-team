## 1. 요청 요약

서버를 어느 디렉터리에서 실행하든 `projects/paper-trading/.env`가 자동 로드되도록 **`load_settings()`의 dotenv 검색 경로를 명시화**한다. 그 결과 대시보드 `/paper/status` 응답의 `kis_config_loaded`가 `.env`에 KIS 값이 있을 때 `true`로 표시되며, raw credentials는 여전히 어디에도 노출되지 않는다.

### 현재 상태 점검 (직접 확인)

- `app/config.py:load_settings()`이 `load_dotenv()`를 인자 없이 호출 → **CWD부터 위쪽으로 `.env` 탐색**. uvicorn을 다른 디렉터리에서 실행하면 `.env`를 못 찾는다.
- 루트 `.gitignore`에 `.env` / `.env.*` / `!.env.example` 룰 이미 존재 ✓.
- 프로젝트 `.gitignore`에 `.env` 룰 이미 존재 ✓.
- `.env.example`에 `KIS_ENV` / `KIS_ACCOUNT_NO` / `KIS_APP_KEY` / `KIS_APP_SECRET` placeholder 이미 존재 ✓.
- `Settings`의 KIS 비밀 3필드는 `field(repr=False)` ✓ (mvp-006-1).

### 결론

**핵심 변경은 `app/config.py` 한 함수**: `load_dotenv()` → `load_dotenv(dotenv_path=<project_dir>/.env, override=False)`. 그 외는 회귀 방지 테스트 + README 한 단락.

### 안전 원칙 (mvp-005~mvp-021 누적 유지)

- live trading 활성화 금지. `load_settings()`의 `LIVE_TRADING_ENABLED=true` reject 유지.
- `ALLOW_MARKET_ORDERS=true` reject 유지.
- `OrderType.MARKET` 부재 유지.
- 외부 HTTP 라이브러리 import 금지.
- KIS endpoint URL/TR ID/payload 추가 금지.
- 실제 KIS app key/secret/account/token 어떤 파일에도 미포함. `.env.example`은 placeholder만.
- `Settings.kis_account_no`/`kis_app_key`/`kis_app_secret`의 `field(repr=False)` 유지.
- `KisBroker.__repr__` masking 유지.
- `/paper/status` 응답에 raw credentials 미포함(account_no_masked + `*_loaded` bool flags만).
- `load_dotenv`의 **`override=False`** 옵션을 명시적으로 사용 — shell이 export한 값(mvp-020 `_common.sh`의 safe defaults)이 `.env`보다 우선.
- `git commit`/`push`/`merge`/`deploy` 자동화 금지. `.env` Git 추가 금지.
- `pip install` 실행 금지.

### 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

기존 189 + 신규 약 4–6개 모두 PASS.

## 2. 작업 범위

### 포함 (In scope)

`projects/paper-trading/` 아래:

- **`app/config.py` (수정)** — 핵심 변경:
  - 신규 helper `_project_dir() -> Path` — `Path(__file__).resolve().parent.parent`(즉 `app/config.py → app/ → project_dir`).
  - `load_settings()`이 `_project_dir() / ".env"`를 명시적 경로로 전달. 파일 없으면 호출 자체를 건너뛰거나 `load_dotenv()` 기본 동작에 위임 — 어느 쪽이든 graceful.
  - `load_dotenv(dotenv_path=env_path, override=False)`로 shell 환경변수가 `.env`를 덮어쓰지 못하게 함. 이는 mvp-020 `scripts/_common.sh`의 safe defaults가 `.env`의 잠재적 위험값보다 우선하도록 보장.
  - 기존 paper/live/market_orders/kill_switch/KIS 가드 로직 변경 없음.
- **`tests/test_kis_config.py` (수정)** — 신규 테스트 추가:
  - `test_load_settings_reads_env_from_project_dir` — `_project_dir()`을 monkeypatch로 tmp_path로 교체, tmp_path에 `.env` 작성 후 `load_settings()` 호출 → KIS 4필드 채워짐 확인.
  - `test_load_settings_dotenv_does_not_override_existing_env` — shell이 이미 setenv한 값이 `.env`의 값보다 우선함 확인(`override=False` 검증).
  - `test_load_settings_works_without_env_file` — `_project_dir()`을 빈 tmp_path로 monkeypatch → settings 정상 생성, KIS 필드 None.
- **`tests/test_api_paper_status.py` (수정)** — 신규 테스트 추가:
  - `test_paper_status_kis_config_loaded_when_env_present` — 임시 `.env` + `_project_dir()` monkeypatch → `/paper/status`이 `kis_config_loaded: true`, `account_no_masked.startswith("***")`, raw 8-digit account 미노출.
- **`projects/paper-trading/README.md` (수정)** — 짧은 단락 추가: `.env` 자동 로딩 안내 + 권장 실행 명령 + 안전 가드(shell env가 .env보다 우선) 설명.
- **`docs/ai/jobs/mvp-022/patch.md` (신규)** — Codex 변경 요약.

### 제외 (Out of scope; 절대 만지지 않음)

- 실제 KIS HTTP 호출 / endpoint URL / TR ID / payload 추가.
- live trading 활성화. `ALLOW_MARKET_ORDERS=true` 허용.
- 시장가 주문 경로. `OrderType.MARKET` 추가.
- 외부 HTTP 라이브러리 import.
- `app/broker/*`, `app/runtime/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/domain/*`, `app/portfolio/*`, `app/session/*`, `app/reports/*`, `app/api/server.py`, `app/api/routes.py`, `app/main.py`, `app/static/*` 변경.
- `.env` 자체 생성/수정. `.env.example` 변경(이미 KIS_* placeholder 보유).
- 프로젝트/루트 `.gitignore` 변경(이미 안전 룰 보유 — 검증만).
- `Settings` 새 필드 추가(KIS 4필드는 이미 mvp-006-1에서 추가).
- mvp-001..mvp-021 산출물 변경.
- `scripts/` 변경(mvp-020 산출물).
- `imports/`, `web/`, `prompts/`, 기존 `docs/`(mvp-022 외) 변경.
- 자동 `git commit`/`push`/`merge`/`deploy`.
- 임의 shell 명령 입력 UI/API 신설.
- `pip install` 실행.

### 안전 가드

- `load_dotenv` 호출에 **`override=False`** 명시 — `os.environ`이 이미 가진 값이 `.env`의 값을 덮어쓰지 않음. mvp-020 `_common.sh`의 4개 안전 export가 `.env`의 값보다 우선.
- `.env`의 실제 KIS 값은 process 메모리에만. log/print/repr 어디에도 미노출(`Settings.field(repr=False)` + `__repr__` 마스킹 + `secret_exposed: false` 응답).
- `_project_dir()`은 `Path(__file__).resolve()` 기반 — 사용자 입력이나 env로 우회되지 않음(상대경로 traversal 위험 0).
- 테스트는 `_project_dir()`을 monkeypatch로 가짜 디렉터리로 바꿔서 검증 — production 동작과 격리.

### 사용자에게 안내할 운영 사항 (README + patch.md)

- 권장 실행: `cd projects/paper-trading && ./scripts/start_server.sh`(mvp-020) — `_common.sh`이 4개 safe env를 force export하므로 `.env`의 값보다 우선.
- 직접 uvicorn 호출 시도 가능: `.venv/bin/python -m uvicorn app.api.server:create_app --factory --host 127.0.0.1 --port 8000`. 단 **`--host 0.0.0.0`을 권장하지 않음** — 외부 노출 위험. mvp-020 스크립트가 `127.0.0.1`만 사용하는 이유.
- `.env`에 키 이름이 `KIS_*`인지 확인 — 일부 사용자는 `KIS_PAPER_*` (옛 mvp-006 명명)이 남아 있을 수 있음. 이 경우 `kis_config_loaded`이 여전히 false. 사용자가 SSH에서 직접 키 이름을 매핑해야 함(채팅 외부, 노출 위험 회피).

## 3. 수정해야 할 파일

### 신규

| 파일 | 목적 |
| --- | --- |
| `docs/ai/jobs/mvp-022/patch.md` | Codex 변경 요약 |

### 수정

| 파일 | 변경 내용 |
| --- | --- |
| `app/config.py` | `_project_dir()` helper + `load_dotenv` 명시 경로 + `override=False` |
| `tests/test_kis_config.py` | 3개 신규 테스트 추가(env path / no-override / no-env-file) |
| `tests/test_api_paper_status.py` | 1개 신규 테스트(kis_config_loaded with .env) |
| `projects/paper-trading/README.md` | `.env` 자동 로딩 + 권장 실행 단락 |

### 절대 미수정

- `projects/paper-trading/app/api/server.py`, `app/api/routes.py`, `app/main.py`, `app/static/*`
- `projects/paper-trading/app/broker/*`, `app/runtime/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/domain/*`, `app/portfolio/*`, `app/session/*`, `app/reports/*`
- `projects/paper-trading/.env.example`(KIS placeholder 이미 보유)
- 프로젝트 `.gitignore`, 루트 `.gitignore`(안전 룰 이미 보유; 검증만 수행)
- mvp-001..mvp-021 산출물
- `scripts/`(mvp-020 산출물)
- 기존 다른 테스트 파일(`test_dashboard.py`, `test_helper_scripts.py`, `test_dry_run_*.py`, `test_kis_*.py` 중 본 작업이 다루지 않는 것)
- `imports/`, `web/`, `prompts/`, 기존 `docs/`

## 4. Codex 구현 지시문

### 4.1 사전 점검

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m pytest -p no:cacheprovider --co -q 2>&1 | tail -3
# expect: 189+ tests collected

grep -q "load_dotenv" app/config.py && echo "OK load_dotenv import"
grep -q "kis_env" app/config.py && echo "OK Settings.kis_env"
grep -q "kis_app_key.*repr=False" app/config.py && echo "OK kis_app_key repr=False"
grep -q "^KIS_ENV=" .env.example && echo "OK .env.example KIS_ENV"
grep -q "^!.env.example" /root/ai-dev-center/projects/ai-team/.gitignore && echo "OK root .gitignore allows .env.example"
test -d .venv && echo "OK venv"
```

위 6개 OK → 진행.

### 4.2 `app/config.py` 변경

기존 import 보존. `load_dotenv`는 이미 import되어 있음. `Path` import 추가(없으면).

```python
from pathlib import Path  # add if missing
```

`Settings` 클래스 정의 위쪽에(또는 helper 영역에) 추가:

```python
def _project_dir() -> Path:
    """Return projects/paper-trading directory based on this module's location.

    app/config.py -> app/ -> project root. Independent of process CWD so .env
    auto-loading works no matter where the server is started from.
    """
    return Path(__file__).resolve().parent.parent
```

`load_settings()` 의 첫 두 줄을 다음으로 교체:

```python
def load_settings() -> Settings:
    env_file = _project_dir() / ".env"
    if env_file.is_file():
        load_dotenv(dotenv_path=env_file, override=False)
    else:
        load_dotenv(override=False)  # fall back to default search; no error if missing
    mode = TradingMode(os.getenv("TRADING_MODE", TradingMode.PAPER.value).lower())
    ...  # 기존 로직 그대로
```

**핵심 불변식:**

- `override=False` 명시 — shell env가 이미 set한 값을 `.env`가 덮어쓰지 않음. mvp-020 `_common.sh`의 safe defaults가 우선.
- `_project_dir()`이 `Path(__file__).resolve()` 기반이라 사용자 입력 traversal 위험 0.
- 기존 paper/live/market/kill_switch/KIS 가드 로직은 그대로 유지.

다른 코드는 변경하지 마.

### 4.3 `tests/test_kis_config.py` (수정) — 3개 신규 테스트

기존 테스트 모두 보존. 다음 추가:

```python
import pytest

# (기존 import 유지)


@pytest.fixture(autouse=False)
def _clear_kis_env(monkeypatch):
    for k in ("TRADING_MODE","LIVE_TRADING_ENABLED","ALLOW_MARKET_ORDERS",
              "KIS_ENV","KIS_ACCOUNT_NO","KIS_APP_KEY","KIS_APP_SECRET"):
        monkeypatch.delenv(k, raising=False)


def test_load_settings_reads_env_from_project_dir(monkeypatch, tmp_path):
    """`.env` is loaded from the project directory regardless of CWD."""
    # Clear any inherited env vars first.
    for k in ("TRADING_MODE","LIVE_TRADING_ENABLED","KIS_ENV","KIS_ACCOUNT_NO","KIS_APP_KEY","KIS_APP_SECRET"):
        monkeypatch.delenv(k, raising=False)
    # Redirect _project_dir() to tmp_path.
    monkeypatch.setattr("app.config._project_dir", lambda: tmp_path)
    (tmp_path / ".env").write_text(
        "TRADING_MODE=paper\n"
        "LIVE_TRADING_ENABLED=false\n"
        "ALLOW_MARKET_ORDERS=false\n"
        "KIS_ENV=paper\n"
        "KIS_ACCOUNT_NO=12345678\n"
        "KIS_APP_KEY=fake-key\n"
        "KIS_APP_SECRET=fake-secret\n",
        encoding="utf-8",
    )
    # Move CWD somewhere unrelated to prove discovery is path-based, not CWD-based.
    monkeypatch.chdir(tmp_path.parent)
    settings = load_settings()
    assert settings.kis_env == "paper"
    assert settings.kis_account_no == "12345678"
    assert settings.kis_app_key == "fake-key"
    assert settings.kis_app_secret == "fake-secret"


def test_load_settings_works_without_env_file(monkeypatch, tmp_path):
    """Missing `.env` does not crash; KIS fields default to None."""
    for k in ("TRADING_MODE","LIVE_TRADING_ENABLED","KIS_ENV","KIS_ACCOUNT_NO","KIS_APP_KEY","KIS_APP_SECRET"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr("app.config._project_dir", lambda: tmp_path)
    # tmp_path is empty, no .env.
    monkeypatch.setenv("TRADING_MODE", "paper")
    settings = load_settings()
    assert settings.kis_env is None
    assert settings.kis_account_no is None
    assert settings.kis_app_key is None
    assert settings.kis_app_secret is None


def test_load_settings_does_not_override_existing_shell_env(monkeypatch, tmp_path):
    """Shell-exported env vars take precedence over `.env` (override=False)."""
    for k in ("TRADING_MODE","LIVE_TRADING_ENABLED","KIS_ENV"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr("app.config._project_dir", lambda: tmp_path)
    (tmp_path / ".env").write_text(
        "TRADING_MODE=paper\n"
        "KIS_ENV=live\n",  # dangerous value in .env
        encoding="utf-8",
    )
    # Shell explicitly sets the safe value first.
    monkeypatch.setenv("TRADING_MODE", "paper")
    monkeypatch.setenv("KIS_ENV", "paper")
    settings = load_settings()
    # The shell value wins, NOT the .env "live" value.
    assert settings.kis_env == "paper"
```

### 4.4 `tests/test_api_paper_status.py` (수정) — 1개 신규 테스트

기존 테스트 모두 보존. 다음 추가:

```python
def test_paper_status_kis_config_loaded_when_env_present(monkeypatch, tmp_path):
    for k in ("TRADING_MODE","LIVE_TRADING_ENABLED","ALLOW_MARKET_ORDERS",
              "KIS_ENV","KIS_ACCOUNT_NO","KIS_APP_KEY","KIS_APP_SECRET"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr("app.config._project_dir", lambda: tmp_path)
    (tmp_path / ".env").write_text(
        "TRADING_MODE=paper\n"
        "KIS_ENV=paper\n"
        "KIS_ACCOUNT_NO=12345678\n"
        "KIS_APP_KEY=fake-key\n"
        "KIS_APP_SECRET=fake-secret\n",
        encoding="utf-8",
    )
    with TestClient(create_app()) as client:
        r = client.get("/paper/status")
    assert r.status_code == 200
    body = r.json()
    assert body["kis_config_loaded"] is True
    assert body["account_no_masked"].startswith("***")
    assert body["secret_exposed"] is False
    # raw values must never appear in the response body
    text = r.text
    for needle in ("fake-key", "fake-secret", "12345678"):
        assert needle not in text
```

### 4.5 README 변경 (`projects/paper-trading/README.md`)

mvp-021 단락 뒤(또는 적절한 위치)에 단락 추가. 기존 단락 변경 없음.

```markdown
## `.env` 자동 로딩 (mvp-022)

`load_settings()`이 `projects/paper-trading/.env`를 **현재 작업 디렉터리와 무관하게** 자동으로 읽습니다. 따라서 다음 어디서 실행하든 KIS 설정이 로드됩니다.

```bash
# 권장 (mvp-020 스크립트, 안전 env 강제 export):
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
./scripts/start_server.sh

# 직접 uvicorn (안전 env는 사용자가 직접 export하거나 .env에 둠):
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m uvicorn app.api.server:create_app --factory --host 127.0.0.1 --port 8000
```

### 안전 가드

- `load_dotenv(..., override=False)` 사용 — shell이 이미 export한 값(예: mvp-020 `scripts/_common.sh`의 `TRADING_MODE=paper` / `LIVE_TRADING_ENABLED=false` / `ALLOW_MARKET_ORDERS=false` / `KIS_ORDER_DRY_RUN=true`)이 `.env`보다 **우선합니다**.
- `.env`에 실수로 `LIVE_TRADING_ENABLED=true` 같은 위험값이 들어 있어도, shell이 `false`를 먼저 export하면 차단됩니다.
- `--host 0.0.0.0` 권장하지 않음 — 외부 노출 위험. `127.0.0.1`만 사용.
- `Settings`의 KIS 비밀 3필드는 `field(repr=False)`로 마스킹 — `repr(settings)`/`logging.info(settings)`에 raw 값 미노출.
- `/paper/status` 응답은 `account_no_masked`(`***xxxx`) + `kis_config_loaded`(bool) + `secret_exposed: false`만 노출. raw KIS app key/secret/account/token은 절대 응답에 포함되지 않습니다.

### `.env` 키 이름 매핑 (사용자 액션)

mvp-006-1 이전에 만들어진 `.env`는 `KIS_PAPER_*` (예: `KIS_PAPER_APP_KEY`)일 수 있습니다. 현재 코드는 `KIS_*` (예: `KIS_APP_KEY`)를 읽습니다. SSH 셸에서 직접(채팅 외부) 키 이름을 매핑하세요. 매핑하지 않으면 `kis_config_loaded`가 계속 `false`로 표시됩니다.
```

### 4.6 검증 명령

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

### 4.7 `docs/ai/jobs/mvp-022/patch.md`

요청의 "완료 후 patch.md에 정리" 8개 항목과 1:1 대응:

```markdown
## 1. Files Changed
- app/config.py: _project_dir() helper + 명시 dotenv 경로 + override=False
- tests/test_kis_config.py: 3개 신규 테스트
- tests/test_api_paper_status.py: 1개 신규 테스트
- README.md: .env 자동 로딩 단락
- docs/ai/jobs/mvp-022/patch.md: 본 요약

## 2. Implementation Summary

### 2.1 변경 파일
(목록 + 한 줄 설명)

### 2.2 .env 자동 로딩 방식
- _project_dir()이 app/config.py의 __file__ 기준 절대경로 사용 — CWD와 무관.
- load_dotenv(dotenv_path=<project>/.env, override=False) 명시.
- 파일 없으면 graceful fallback (load_dotenv() default search — 무해).

### 2.3 KIS 설정 표시 방식
- `.env`에 KIS_ENV/KIS_ACCOUNT_NO/KIS_APP_KEY/KIS_APP_SECRET이 있으면 Settings에 로드.
- /paper/status가 kis_config_loaded=true 반환.
- account_no_masked로 ***xxxx만 노출.

### 2.4 secret/account 미노출 여부
- Settings 비밀 3필드 field(repr=False) — repr(settings)에 미포함 (mvp-006-1).
- KisBroker.__repr__/sub-client __repr__ 마스킹 (mvp-007).
- /paper/status 응답 텍스트에 raw fake-key/fake-secret/12345678 등 미포함 (테스트로 검증).
- log/print에 settings를 dump해도 비밀 미노출.

### 2.5 live trading 비활성 유지
- load_settings()의 LIVE_TRADING_ENABLED=true ValueError 그대로.
- override=False로 shell의 safe export가 .env의 위험값을 덮어씀 보장.

### 2.6 market order 금지 유지
- ALLOW_MARKET_ORDERS=true ValueError 유지.
- OrderType.MARKET 부재.

### 2.7 테스트 결과
- compileall PASS
- pytest 189(기존) + 4(신규) = 193 PASS

### 2.8 서버 실행 방법
- 권장: ./scripts/start_server.sh (mvp-020, 127.0.0.1만)
- 직접: .venv/bin/python -m uvicorn app.api.server:create_app --factory --host 127.0.0.1 --port 8000
- 0.0.0.0 binding 비권장 (외부 노출 위험)

## 3. Safety Confirmation
- live trading 비활성 + 5+1단 차단 모두 유지
- 시장가 차단 유지
- override=False로 shell safe export 우선
- raw credentials 코드/응답/log/.env.example/patch.md 어디에도 없음
- /paper/status 응답 본문 텍스트 검사로 raw 미노출 확인
- KIS endpoint URL/TR ID 0건 추가
- 외부 HTTP 라이브러리 import 0건
- app/broker/*, app/api/server.py, app/api/routes.py, app/runtime/*, app/oms/*, app/risk/*, app/strategy/*, app/domain/*, app/portfolio/*, app/session/*, app/reports/* 미변경
- .env, secrets, .env.example, 프로젝트 .gitignore, 루트 .gitignore 미변경
- mvp-001..mvp-021 산출물 미변경
- commit/push/merge/deploy 자동화 0건

## 4. Test Results
(compileall + pytest 출력)

## 5. Remaining TODOs
- 사용자가 .env의 KIS_PAPER_* (옛 명명) 키를 KIS_* (새 명명)로 매핑(채팅 외부).
- KIS 공식 문서값(docs/kis/MISSING_OFFICIAL_VALUES.md)을 사람이 채운 뒤 별도 mvp에서 실제 HTTP 연결.
```

## 5. 테스트 기준

1. `.venv/bin/python -m compileall app tests` 종료코드 0.
2. `.venv/bin/python -m pytest -p no:cacheprovider` 종료코드 0. 기존 189 + 신규 4 PASS.
3. `_project_dir()`이 `Path(__file__).resolve().parent.parent` 사용 — 즉 `app/config.py`의 파일 위치 기반(CWD 무관).
4. `load_dotenv` 호출이 `override=False` 인자를 사용.
5. `tests/test_kis_config.py`의 신규 3개 + `tests/test_api_paper_status.py`의 신규 1개 PASS.
6. `/paper/status` 응답에 raw `fake-key`/`fake-secret`/`12345678` 등 미포함(테스트로 검증).
7. `Settings.kis_account_no`/`kis_app_key`/`kis_app_secret`의 `field(repr=False)` 유지(`grep` 확인).
8. `app/broker/kis.py` 변경 0건. `app/api/server.py`/`routes.py` 변경 0건. `app/runtime/*`/`app/oms/*`/`app/risk/*`/`app/strategy/*`/`app/domain/*`/`app/reports/*`/`app/portfolio/*`/`app/session/*` 변경 0건.
9. `.env`, `.env.example`, 프로젝트/루트 `.gitignore` 변경 0건.
10. `git diff --stat`에 mvp-022 외 변경 없음.
11. `.env` staged/committed 없음.

## 6. 리뷰 체크리스트

- [ ] `app/config.py`에 `_project_dir()` helper 추가.
- [ ] `load_settings()`이 `load_dotenv(dotenv_path=<project>/.env, override=False)` 호출.
- [ ] `.env` 없을 때 graceful fallback(에러 없음, KIS 필드 None).
- [ ] `override=False`로 shell env가 `.env`보다 우선함이 테스트로 검증됨.
- [ ] tmp_path + monkeypatch로 `_project_dir()`을 가짜 디렉터리로 바꿔 production 격리 테스트.
- [ ] `/paper/status`이 `.env` 자동 로딩 후 `kis_config_loaded: true`, `account_no_masked: ***xxxx`, `secret_exposed: false` 반환.
- [ ] 응답 본문에 raw KIS app key/secret/account 0건(텍스트 검사).
- [ ] `Settings` 비밀 필드 `field(repr=False)` 유지.
- [ ] 기존 189 회귀 0건.
- [ ] mvp-022 신규 4개 PASS.
- [ ] `app/broker/*`, `app/api/server.py`, `app/api/routes.py`, `app/runtime/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/domain/*`, `app/reports/*`, `app/portfolio/*`, `app/session/*`, `app/main.py`, `app/static/*` 변경 0건.
- [ ] `.env`, `.env.example`, 프로젝트 `.gitignore`, 루트 `.gitignore` 변경 0건.
- [ ] mvp-001..mvp-021 산출물 미변경.
- [ ] `OrderType.MARKET` 부재 유지.
- [ ] live trading + market orders + KIS endpoint 추가 가드 모두 유지.
- [ ] README에 mvp-022 단락 추가, 기존 단락 변경 없음.
- [ ] README가 `127.0.0.1` 권장 + `0.0.0.0` 비권장 명시.
- [ ] README가 사용자 액션(.env 키 이름 매핑, mvp-006-1) 명시.
- [ ] `git diff --stat`에 mvp-022 외 변경 없음.
- [ ] `.env` staged/committed 없음.
- [ ] commit/push/merge/deploy 자동화 없음.
- [ ] `patch.md` 5섹션 + Implementation Summary 8단락 완성.
