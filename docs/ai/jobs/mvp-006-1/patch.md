## 1. Files Changed

신규:
- `projects/paper-trading/app/broker/kis.py`
- `projects/paper-trading/tests/test_kis_config.py`
- `projects/paper-trading/tests/test_broker_interface.py`
- `docs/ai/jobs/mvp-006-1/patch.md` (이 파일)

수정:
- `projects/paper-trading/app/config.py`
- `projects/paper-trading/app/api/server.py`
- `projects/paper-trading/app/api/routes.py`
- `projects/paper-trading/.env.example`
- `projects/paper-trading/README.md`
- `projects/paper-trading/tests/test_api_paper_status.py`

루트 `.gitignore`는 이미 `.env` / `.env.*` / `!.env.example` 룰을 보유하고 있어 수정하지 않음.

## 2. Implementation Summary

### 2.1 변경 파일

- `app/broker/kis.py`: 신규. `KisBroker` 스켈레톤 클래스. `mode = TradingMode.PAPER`. `__init__`이 `KIS_ENV != "paper"`, `KIS_ACCOUNT_NO`/`KIS_APP_KEY`/`KIS_APP_SECRET` 누락 시 `RuntimeError`로 fail-closed. `__repr__`가 `<set>`로 마스킹. 모든 KIS-스타일 메서드(`authenticate`/`refresh_token`/`get_account`/`get_positions`/`get_quote`/`get_open_orders`/`place_order`/`cancel_order`/`replace_order`)는 `NotImplementedError` + TODO 메시지. `healthcheck()`는 정적 disconnected dict 반환. BrokerAdapter Protocol 호환(`submit`/`cancel`/`open_orders`/`positions`)은 위 KIS-스타일 메서드로 위임. 외부 HTTP 라이브러리 import 없음.
- `app/config.py`: `Settings`에 `kis_env`, `kis_account_no(field repr=False)`, `kis_app_key(field repr=False)`, `kis_app_secret(field repr=False)`, `allow_market_orders` 다섯 필드 추가. `_str_env`/`_bool_env` 헬퍼 신규. `load_settings()`가 `ALLOW_MARKET_ORDERS=true` 검출 시 `ValueError`. KIS 필드는 누락 가능(`None` 허용) — adapter `__init__`에서만 강제 검증.
- `app/api/server.py`: lifespan 안에서 `KisBroker(settings)`를 `try/except RuntimeError`로 시도, 성공 시 `app.state.configured_brokers`에 `"KisBroker"` 등록. KIS 인스턴스 자체는 보관하지 않음(credentials 보관 회피). 활성 broker는 `PaperBroker` 그대로.
- `app/api/routes.py`: `/paper/status` 응답에 `broker_type`, `broker_environment`, `live_trading_enabled`, `market_orders_allowed`, `kis_config_loaded`, `kis_secret_exposed: false`, `configured_brokers` 필드 추가. 기존 `mode`/`live_enabled`/`strategies`/`safety` 키 보존. raw key/secret/account 미노출.
- `.env.example`: `ALLOW_MARKET_ORDERS=false`, `KIS_ENV=paper`, `KIS_ACCOUNT_NO=your_kis_paper_account_no`, `KIS_APP_KEY=your_kis_app_key`, `KIS_APP_SECRET=your_kis_app_secret` 추가. placeholder만, 실제 값 없음. "이 저장소는 vendor endpoint를 추측하지 않는다" 주석.
- `README.md`: `## KIS Open API (모의투자) 연결 준비` 섹션 + 환경변수 표 + 안전 가드 단락 + Phase 2 후보 항목 추가.
- `tests/test_kis_config.py`: 신규 5 테스트(기본값 paper/live=false, env 로딩, repr 마스킹, ALLOW_MARKET_ORDERS=true reject, .env.example placeholder 검증).
- `tests/test_broker_interface.py`: 신규 11 테스트(KisBroker 메서드 보유, mode=paper, KIS_ENV 누락/live/credentials 누락 fail-closed, 모든 비구현 메서드 NotImplementedError, healthcheck 형식, repr 마스킹, Strategy 격리 grep, HTTP 라이브러리 격리 grep).
- `tests/test_api_paper_status.py`: 신규 `test_paper_status_kis_metadata_fields` 추가. mvp-006-1 필드 모양 + credentials 미노출 검증.

### 2.2 KIS 설정 구조

`Settings` (frozen dataclass)에 5필드 추가:

| 필드 | 타입 | 기본값 | repr |
| --- | --- | --- | --- |
| `kis_env` | `str \| None` | `None` | 노출 |
| `kis_account_no` | `str \| None` | `None` | **제외(`repr=False`)** |
| `kis_app_key` | `str \| None` | `None` | **제외(`repr=False`)** |
| `kis_app_secret` | `str \| None` | `None` | **제외(`repr=False`)** |
| `allow_market_orders` | `bool` | `False` | 노출 |

`load_settings()` 동작:
1. `TRADING_MODE != "paper"` → `ValueError` (mvp-005 유지).
2. `LIVE_TRADING_ENABLED` truthy → `ValueError` (mvp-005 유지).
3. **`ALLOW_MARKET_ORDERS` truthy → `ValueError` (mvp-006-1 신규).**
4. KIS_* 환경변수를 `_str_env`로 정규화하여 채움. 누락은 `None`(Alpaca-only 사용자 보호).

KIS 키 자체 검증은 `KisBroker.__init__`에서만 수행하여, KIS를 사용하지 않는 시나리오에서는 시스템이 그대로 시작 가능.

### 2.3 .env와 .env.example 사용 방식

- **`.env`**: 실제 KIS 키/계좌번호는 여기에만. 루트 `.gitignore`의 `.env` / `.env.*` 룰과 프로젝트 `.gitignore`의 `.env` 룰 양쪽에서 Git 추가 차단.
- **`.env.example`**: placeholder만(`your_kis_paper_account_no`, `your_kis_app_key`, `your_kis_app_secret`). `KIS_ENV=paper`는 명시적 기본값. URL/endpoint 절대 없음.
- 사람이 해야 할 매핑(`.env` 기존 `KIS_PAPER_*` → `KIS_*`)은 SSH 셸에서 직접 수행(채팅 외부).

### 2.4 실제 key/secret/account 노출 여부

- `Settings.kis_account_no`, `kis_app_key`, `kis_app_secret`은 `field(repr=False)` — dataclass 자동 생성 `__repr__`에서 제외.
- `KisBroker.__repr__`: `KisBroker(env='paper', account=<set>, app_key=<set>, app_secret=<set>)` 패턴. raw 값 절대 노출 안 함.
- `/paper/status` 응답: bool flag(`kis_config_loaded`)와 `kis_secret_exposed: false` 만. raw 값 일체 미포함.
- `app/api/server.py`: KIS broker 인스턴스 자체를 `app.state`에 저장하지 않아 credentials retention 0.
- `.env.example`/소스 코드/`patch.md`/`review.md` 어디에도 실제 KIS key/secret/account 없음.

### 2.5 KIS adapter에서 무엇이 TODO인지

`app/broker/kis.py`에서 다음 메서드는 모두 `NotImplementedError` + 명시적 TODO 메시지(공식 문서 reference 안내 포함):

- `authenticate()` — OAuth/토큰 endpoint, payload, 응답 shape 미정.
- `refresh_token()` — refresh endpoint, payload 미정.
- `get_account()` — 계좌 조회 TR ID, endpoint, payload 미정.
- `get_positions()` — 포지션 조회 TR ID, endpoint, payload 미정.
- `get_quote(symbol)` — 시세 조회 TR ID, endpoint, payload 미정.
- `get_open_orders()` — 미체결 주문 조회 TR ID, endpoint, payload 미정.
- `place_order(broker_order)` — 주문 endpoint, payload, OMS-only 통합 절차 미정. "DO NOT WIRE without OMS-only execution + RiskEngine guard" 명시.
- `cancel_order(broker_order_id)` — 취소 endpoint 미정.
- `replace_order(broker_order_id, broker_order)` — 정정 endpoint 미정.

`healthcheck()`만 정적 dict 반환(`connected: False`, `reason: skeleton`).

BrokerAdapter Protocol 호환 메서드(`submit`/`cancel`/`open_orders`/`positions`)는 위 KIS-스타일 메서드로 위임만 — 따라서 OMS가 KIS broker로 라우팅되더라도 결국 `NotImplementedError`로 fail-closed. (참고: 본 단계 OMS는 `PaperBroker`로 와이어링되어 있으므로 KIS는 활성 경로 아님.)

### 2.6 live trading이 계속 차단되어 있는지

mvp-005의 live 차단 5단 + mvp-006-1의 6단째가 모두 작동:

| 단 | 위치 | 동작 |
| --- | --- | --- |
| 1 | `Settings.live_trading_enabled = False` (기본값) | 정상 경로에서 항상 False |
| 2 | `load_settings()`의 `LIVE_TRADING_ENABLED` truthy → `ValueError` | env 활성화 시도 차단 |
| 3 | `RiskEngine.evaluate()` — paper 강제 / live 차단 | RiskEngine 진입 시 차단 |
| 4 | `OMS.place()` 시작부 — `live_trading_enabled` 체크 | OMS 진입 시 차단 |
| 5 | `POST /paper/run` 핸들러 — live 시 503 | API 진입 시 차단 |
| 6 | `KisBroker.__init__` — `KIS_ENV != "paper"` → `RuntimeError` | KIS 어댑터 인스턴스화 차단 |

추가 차단(market orders): `Settings.allow_market_orders = False` 기본값 + `load_settings()`가 `ALLOW_MARKET_ORDERS=true` 검출 시 `ValueError`. `OrderType`에 MARKET 멤버 없음(grep 확인: `OrderType.MARKET` 등장 0건; `PRE_MARKET`는 `Session` enum의 다른 멤버).

### 2.7 실행한 테스트

호스트에 `pytest` 미설치로 pytest 자체는 실행하지 못함(Remaining TODOs 참고). 하지만 다음 정적 검증은 통과:

- `python3 -m compileall -f app tests`: **exit 0**. 신규 `app/broker/kis.py`, `tests/test_kis_config.py`, `tests/test_broker_interface.py` 포함 28개 `.py` 파일 모두 컴파일 성공.
- `grep -RIn 'OrderType\.MARKET' app/`: 0건.
- `grep -RInE "from app\.broker\.kis\b|import app\.broker\.kis\b" app/strategy/`: 0건.
- `grep -nE "import requests|from requests|import httpx|from httpx|import aiohttp|from aiohttp" app/broker/kis.py`: 0건.
- `grep -nE "https?://" app/broker/kis.py`: 0건(URL 코드 하드코딩 없음).
- `grep -RIn "live_trading_enabled\s*=\s*True" app/ tests/`: 2건(`tests/test_oms.py:28`, `tests/test_risk_engine.py:26` — 둘 다 reject 동작을 검증하는 negative test).

신규/수정 테스트 파일(`test_kis_config.py` 5개, `test_broker_interface.py` 11개, `test_api_paper_status.py` 새 함수 1개)은 작성 완료. pytest가 설치된 환경에서 실행하면 호환되도록 mvp-005 기존 fixture(`settings`, `make_snapshot`)를 그대로 활용.

## 3. Safety Confirmation

- live trading 차단 6단 그대로 (위 §2.6 표).
- 실계좌 어댑터 없음. KIS도 paper-only 가드 + 네트워크 미구현.
- 시장가 주문 차단 유지: `OrderType.MARKET` 부재, `ALLOW_MARKET_ORDERS=true` reject.
- mvp-005의 Strategy/OMS/RiskEngine/Broker 격리 유지: `app/strategy/`가 `app.broker.kis` 미import (grep 확인).
- `KisBroker`가 외부 HTTP 라이브러리(`requests`/`httpx`/`aiohttp`) 미import (grep 확인).
- KIS endpoint URL, TR ID, payload 코드 하드코딩 없음.
- 실제 KIS key/secret/account 코드/문서/.env.example/응답/log/patch 어디에도 없음.
- `Settings.kis_account_no`/`kis_app_key`/`kis_app_secret`은 `field(repr=False)`. `KisBroker.__repr__` 마스킹.
- `/paper/status` 응답에 raw secret/key/account 미포함. `kis_secret_exposed: false` literal.
- `.env` 미접촉. 루트/프로젝트 `.gitignore`로 보호 확인.
- `git commit`/`push`/`merge`/`deploy` 자동화 없음.
- 임의 shell 입력 UI/API 신설 없음.

## 4. Test Results

```text
$ python3 -m compileall -f app tests
Listing 'app'...
Compiling 'app/__init__.py'...
Listing 'app/api'...
Compiling 'app/api/__init__.py'...
Compiling 'app/api/routes.py'...
Compiling 'app/api/server.py'...
Listing 'app/broker'...
Compiling 'app/broker/__init__.py'...
Compiling 'app/broker/alpaca_paper.py'...
Compiling 'app/broker/base.py'...
Compiling 'app/broker/kis.py'...
Compiling 'app/broker/paper.py'...
Compiling 'app/config.py'...
Listing 'app/domain'...
Compiling 'app/domain/__init__.py'...
Compiling 'app/domain/enums.py'...
Compiling 'app/domain/market.py'...
Compiling 'app/domain/orders.py'...
Compiling 'app/main.py'...
Listing 'app/oms'...
Compiling 'app/oms/__init__.py'...
Compiling 'app/oms/manager.py'...
Listing 'app/risk'...
Compiling 'app/risk/__init__.py'...
Compiling 'app/risk/engine.py'...
Listing 'app/runtime'...
Compiling 'app/runtime/__init__.py'...
Compiling 'app/runtime/paper_runner.py'...
Listing 'app/strategy'...
Compiling 'app/strategy/__init__.py'...
Compiling 'app/strategy/base.py'...
Compiling 'app/strategy/inputs.py'...
Compiling 'app/strategy/premarket_gap.py'...
Listing 'tests'...
Compiling 'tests/__init__.py'...
Compiling 'tests/conftest.py'...
Compiling 'tests/test_alpaca_paper_stub.py'...
Compiling 'tests/test_api_paper_status.py'...
Compiling 'tests/test_broker_interface.py'...
Compiling 'tests/test_config.py'...
Compiling 'tests/test_flow.py'...
Compiling 'tests/test_kis_config.py'...
Compiling 'tests/test_models.py'...
Compiling 'tests/test_oms.py'...
Compiling 'tests/test_paper_broker.py'...
Compiling 'tests/test_paper_runner.py'...
Compiling 'tests/test_risk_engine.py'...
Compiling 'tests/test_strategy_premarket_gap.py'...

compileall exit=0
```

```text
$ python3 -m pytest -p no:cacheprovider
(NOT RUN — pytest not installed on host; see Remaining TODOs)
```

저장소 루트:

```text
$ git diff --stat
 docs/ai/jobs/mvp-004/request.ko.md |  78 +++++-
 web/public/app.js                  | 141 +++++++++-
 web/public/index.html              | 144 ++++++----
 web/public/style.css               |  74 ++++--
 web/server.js                      | 527 +++++++++++++++++++++++++++++++++----
 5 files changed, 823 insertions(+), 141 deletions(-)
```

위 `git diff --stat`은 mvp-006-1과 무관한 pre-existing dirty (mvp-004 잔재 + 별도 GUI 작업)다. mvp-006-1의 모든 변경은 `projects/paper-trading/` 아래(전체 untracked)에 있어 `git diff`에 잡히지 않는다.

```text
$ git status --short
... (mvp-006-1 변경은 projects/ 아래 untracked tree 안에 있음)
?? docs/ai/jobs/mvp-006-1/
?? projects/
... (그 외 기존 dirty/untracked 항목들)
```

정적 안전 검증:

```text
$ grep -RIn 'OrderType\.MARKET' app/    # → 0 lines
$ grep -RInE "from app\.broker\.kis\b|import app\.broker\.kis\b" app/strategy/    # → 0 lines
$ grep -nE "import requests|from requests|import httpx|from httpx|import aiohttp|from aiohttp" app/broker/kis.py    # → 0 lines
$ grep -nE "https?://" app/broker/kis.py    # → 0 lines
$ grep -RIn "live_trading_enabled\s*=\s*True" app/ tests/
tests/test_oms.py:28: live_settings = replace(settings, live_trading_enabled=True)
tests/test_risk_engine.py:26: decision = RiskEngine(replace(settings, live_trading_enabled=True)).evaluate(intent())
# both are negative tests verifying rejection
```

## 5. Remaining TODOs

1. **호스트에 dev 의존성 설치 후 pytest 직접 실행** (필수, mvp-005부터 이월된 액션):
   ```bash
   cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
   python3 -m pip install fastapi 'uvicorn[standard]' 'pydantic>=2' python-dotenv pytest httpx
   python3 -m pytest -p no:cacheprovider
   ```
   기대: mvp-005 19개 + mvp-006-1 신규 17개 안팎 모두 PASS.

2. **사용자 `.env` 키 매핑**: 현재 `.env`에 `KIS_PAPER_API_BASE`/`KIS_PAPER_ACCOUNT`/`KIS_PAPER_APP_KEY`/`KIS_PAPER_APP_SECRET`로 들어가 있는 키를 `KIS_ENV=paper`/`KIS_ACCOUNT_NO`/`KIS_APP_KEY`/`KIS_APP_SECRET`로 SSH 셸에서 직접 변경 필요. 채팅 외부에서 수행. 채팅에서 다시 노출하지 말 것. 이미 누출된 키는 KIS 개발자 포털에서 rotate 권장.

3. **다음 mvp 후보**: mvp-007(인증/계좌/시세 sub-client 분리 + 토큰 상태 머신 + healthcheck 강화) — 이미 plan/codex-task 작성됨, 본 작업 위에 빌드 가능.

4. **워크트리 정리**: `git diff --stat`이 보고하는 5개 modified 파일은 mvp-006-1과 무관한 prior dirty. commit 시 staging을 다음으로 한정:
   ```bash
   git add projects/paper-trading docs/ai/jobs/mvp-006-1
   git diff --cached --stat   # 검증
   ```
   mvp-004 / 별도 GUI 작업은 별도 commit으로 분리.

## Verdict

READY FOR REVIEW
