# Codex Task — mvp-007: KIS Open API 인증 / 계좌 / 시세 구조 (HTTP 없음)

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-007/plan.md` and `docs/ai/jobs/mvp-007/request.ko.md` first.

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-007`
- 대상 디렉터리: `projects/paper-trading/`
- 본 작업은 mvp-006-1 위에 빌드된다. mvp-006-1이 먼저 구현되어 있어야 한다.
- **본 작업에서 실제 HTTP 호출은 만들지 않는다.** KIS Open API endpoint/TR ID/payload는 공식 문서 확인이 필요하며, Codex는 공식 문서를 직접 확인할 수 없다. 학습 데이터의 KIS endpoint 지식은 "공식 문서 기준"으로 간주하지 않는다.

## 사전 점검 (Codex 첫 단계)

작업 시작 직후 다음을 확인:

```bash
# in projects/paper-trading
test -f app/broker/kis.py && grep -q "class KisBroker" app/broker/kis.py && echo "kis.py OK"
grep -q "kis_env" app/config.py && echo "config.py KIS fields OK"
grep -q "kis_config_loaded\|kis_secret_exposed\|broker_type" app/api/routes.py && echo "routes.py KIS status OK"
grep -q "KIS_ENV\|KIS_APP_KEY\|KIS_APP_SECRET\|KIS_ACCOUNT_NO" .env.example && echo "env.example OK"
```

위 중 어느 하나라도 누락이면:
1. `patch.md` Remaining TODOs에 "mvp-006-1을 먼저 구현해야 함 — 누락된 파일/필드 목록" 기록.
2. mvp-007 작업을 중단.
3. `git status --short`과 `git diff --stat`은 그대로 patch.md에 인용.

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials 변경/생성/읽기 금지(테스트는 `monkeypatch`/`replace`로 흉내).
- 실제 KIS app key/secret/account 값을 어떤 파일에도 쓰지 않는다.
- KIS endpoint URL, TR ID, header, payload를 코드/문서에 하드코딩 금지(공식 문서 확인 전).
- `app/broker/kis.py`에 외부 HTTP 라이브러리(`requests`, `httpx`, `aiohttp`, `urllib3` 등) import 금지.
- `app/broker/kis.py`에 네트워크 호출/소켓 시도 금지.
- 실주문 코드 신설 금지. `place_order`/`cancel_order`/`replace_order`/`submit`/`cancel` 모두 `NotImplementedError` 유지.
- live trading 활성화 금지.
- `OrderType`에 MARKET 멤버 추가 금지.
- RiskEngine/OMS 우회 코드 경로 신설 금지.
- Strategy 패키지가 `app.broker.kis*` import 금지.
- OMS의 `_risk`/`_broker` private 유지.
- `/paper/status`나 어떤 응답에 raw key/secret/account/access_token 노출 금지.
- 임의 shell 명령 입력 UI/API 신설 금지.
- 본 작업 범위 외 파일 변경 금지. mvp-001..mvp-006-1 산출물(plan/codex-task/patch/review 문서) 미변경.
- `pip install` 실행 금지.

## 수정 허용 위치

### 신규

- `projects/paper-trading/tests/test_kis_auth_client.py`
- `projects/paper-trading/tests/test_kis_account_client.py`
- `projects/paper-trading/tests/test_kis_market_data_client.py`
- `docs/ai/jobs/mvp-007/patch.md`

### 수정 가능

- `projects/paper-trading/app/broker/kis.py` (mvp-006-1에서 만든 `KisBroker`에 sub-client 추가 + 위임)
- `projects/paper-trading/app/api/server.py` (KisBroker 인스턴스를 `app.state.kis_broker`에 보관)
- `projects/paper-trading/app/api/routes.py` (`/paper/status` 응답 확장 + `secret_exposed` 이름 통일)
- `projects/paper-trading/tests/test_broker_interface.py` (sub-client 노출 + healthcheck 확장 assertion)
- `projects/paper-trading/tests/test_api_paper_status.py` (신규 필드 + 이름 통일)
- `projects/paper-trading/README.md` (KIS client 구조 + TODO 경계 단락)

### 절대 미수정

- `projects/paper-trading/app/config.py` (mvp-006-1에서 완료)
- `projects/paper-trading/app/domain/*`
- `projects/paper-trading/app/broker/{base,paper,alpaca_paper}.py`
- `projects/paper-trading/app/risk/engine.py`
- `projects/paper-trading/app/oms/manager.py`
- `projects/paper-trading/app/strategy/*`
- `projects/paper-trading/app/runtime/paper_runner.py`
- `projects/paper-trading/app/main.py`
- 기존 테스트(mvp-005): `test_config.py`, `test_models.py`, `test_risk_engine.py`, `test_oms.py`, `test_paper_broker.py`, `test_alpaca_paper_stub.py`, `test_flow.py`, `test_paper_runner.py`, `test_strategy_premarket_gap.py`
- mvp-006-1의 `test_kis_config.py` (변경 없음)
- 루트 `.gitignore`, 프로젝트 `.gitignore`
- mvp-001..mvp-006-1 산출물

## 구현 작업

### 1) `app/broker/kis.py` 확장

mvp-006-1에서 만든 `KisBroker`는 그대로 유지하면서, 다음을 추가/리팩터한다. `plan.md` §4.2 코드를 그대로 따른다.

#### 1.1 예외 클래스 (모듈 상단)

```python
class KisError(Exception): ...
class KisConfigError(KisError): ...
class KisAuthError(KisError): ...
class KisDataUnavailableError(KisError): ...
```

#### 1.2 `KisAuthClient`

`plan.md` §4.2.2 코드 그대로:
- `__init__(settings)`: `kis_app_key`/`kis_app_secret` 누락 시 `KisConfigError`.
- 내부 상태: `_access_token: str | None = None`, `_expires_at: datetime | None = None`, `_last_error: str | None = None`.
- `is_authenticated()`: 토큰 존재 + 만료 시각 비교(`datetime.now(timezone.utc)` 사용).
- `get_access_token()`: `is_authenticated()` True면 토큰 반환, 아니면 None. **네트워크 호출 트리거 금지.**
- `clear_token()`: 둘 다 None.
- `authenticate()` / `refresh_token()`: `NotImplementedError`에 메시지 "TODO — confirm ... from KIS Open API official documentation. Do not invent endpoints." 포함.
- `__repr__`: `KisAuthClient(env={env!r}, token=<set>|<unset>)`. 절대 key/secret 미포함.
- `last_error` property: `_last_error` 반환.

#### 1.3 `KisAccountClient`

`plan.md` §4.2.3 그대로:
- `__init__(settings, auth)`: `kis_account_no` 누락 시 `KisConfigError`.
- `masked_account_no()` 구현: 길이 ≤ 4면 `"***"`, 아니면 `f"***{acc[-4:]}"`.
- `is_loaded()`: bool 반환(기본 False).
- `get_account/get_positions/get_cash_balance`: `NotImplementedError` + TODO 메시지.
- `__repr__`: `KisAccountClient(account=<masked>)`. raw account 미노출.

#### 1.4 `KisMarketDataClient`

`plan.md` §4.2.4 그대로:
- `__init__(settings, auth)`.
- `get_quote(symbol)` / `get_last_price(symbol)`: `NotImplementedError` + TODO.
- `healthcheck_market_data()` 구현: 정적 dict 반환(`connected: False`, `reason: "skeleton — ..."`, `auth_required: True`, `auth_present: self._auth.is_authenticated()`).
- `__repr__`: `KisMarketDataClient(<disconnected>)`.

#### 1.5 `KisBroker` 리팩터

mvp-006-1의 `KisBroker.__init__` 검증 로직(KIS_ENV/account/key/secret 검사)을 그대로 유지하면서, 다음을 추가:

- 컴포지션: `self._auth = KisAuthClient(settings)`, `self._account = KisAccountClient(settings, self._auth)`, `self._market_data = KisMarketDataClient(settings, self._auth)`, `self._last_error: str | None = None`.
- property로 노출: `auth`, `account`, `market_data`, `last_error`.
- `__repr__` 유지(mvp-006-1).
- 메서드 위임:
  - `authenticate()` → `self._auth.authenticate()`
  - `refresh_token()` → `self._auth.refresh_token()`
  - `get_account()` → `self._account.get_account()`
  - `get_positions()` → `self._account.get_positions()`
  - `get_quote(symbol)` → `self._market_data.get_quote(symbol)`
  - `get_open_orders()` → `NotImplementedError` (mvp-006-1 그대로)
  - `place_order(broker_order)` → `NotImplementedError` 메시지에 "DO NOT WIRE without OMS-only + RiskEngine" 유지
  - `cancel_order/replace_order` → `NotImplementedError`
  - `submit/cancel/open_orders/positions` (BrokerAdapter 호환) → 동일 위임
- `healthcheck()` 강화:

  ```python
  def healthcheck(self) -> dict:
      market = self._market_data.healthcheck_market_data()
      return {
          "broker": "KisBroker",
          "environment": self._settings.kis_env,
          "config_loaded": True,
          "authenticated": self._auth.is_authenticated(),
          "account_loaded": self._account.is_loaded(),
          "market_data": market,
          "last_error": self._last_error,
          "order_execution_implemented": False,
      }
  ```

import 허용: `typing.Any`, `datetime` (timezone aware), `app.config.Settings`, `app.domain.enums.TradingMode`, `app.domain.orders.{BrokerOrder, OrderAck}`. 그 외(특히 HTTP 라이브러리) 금지.

### 2) `app/api/server.py` 변경

mvp-006-1 코드에서 `KisBroker(settings)`를 인스턴스 폐기로 시도하던 부분을, **인스턴스 보관**으로 바꾼다:

```python
kis_broker = None
configured_brokers: list[str] = []
try:
    from app.broker.kis import KisBroker
    kis_broker = KisBroker(settings)
    configured_brokers.append("KisBroker")
except RuntimeError:
    pass
```

lifespan 안:

```python
app.state.configured_brokers = configured_brokers
app.state.kis_broker = kis_broker  # None or KisBroker instance
```

- `except RuntimeError`만. broad `Exception` 금지.
- 활성 broker는 여전히 `PaperBroker`(OMS 와이어링 미변경).

### 3) `app/api/routes.py` 변경

mvp-006-1의 `/paper/status` 응답에 다음 필드 추가/조정:

- 추가: `kis_authenticated`, `kis_account_loaded`, `kis_market_data_available`, `last_broker_error`, `account_no_masked`.
- 이름 통일: `kis_secret_exposed` → `secret_exposed` (해당 키를 제거하고 새 키로 추가).
- 응답 산출 로직은 `plan.md` §4.4 코드 그대로 따른다.

`account_no_masked` 산출 시 `request.app.state.kis_broker.account.masked_account_no()` 호출. broker가 None이면 `"<unset>"`.

raw `settings.kis_account_no`, `settings.kis_app_key`, `settings.kis_app_secret`을 응답 dict의 어떤 분기에도 넣지 않는다.

### 4) 테스트

`plan.md` §4.5 코드를 그대로 사용. 핵심 테스트 ID 매핑:

- `tests/test_kis_auth_client.py`: credentials 검증 / 초기 상태 / NotImplementedError / repr 마스킹 / 토큰 상태 머신 (총 ~5 개).
- `tests/test_kis_account_client.py`: account_no 검증 / 마스킹 (짧음/긴 케이스) / repr 마스킹 / 메서드 NotImplementedError / is_loaded 초기 False (총 ~6 개).
- `tests/test_kis_market_data_client.py`: get_quote/get_last_price NotImplementedError / healthcheck disconnected dict (총 ~3 개).
- `tests/test_broker_interface.py` 보정 (mvp-006-1 기존): sub-client property 노출 / healthcheck 확장 / last_error 초기 None.
- `tests/test_api_paper_status.py` 보정 (mvp-006-1 기존): 신규 status 필드 + `secret_exposed` 이름 통일 + raw 미노출 텍스트 검사.

테스트가 `settings` fixture를 사용한다면, mvp-005에서 만든 `tests/conftest.py`의 fixture를 그대로 활용. 필요 시 fixture에 KIS 필드 채운 변형을 helper로 추가.

테스트에서 fake 값으로 `k`, `s`, `tok-FAKE`, `50187996`(이미 PII 아님, 예시) 같은 placeholder만 사용. 실제 KIS 키/시크릿 사용 금지.

### 5) `projects/paper-trading/README.md` 변경

`plan.md` §4.6의 "## KIS Open API ... 클라이언트 구조 (mvp-007)" 단락 + "### 무엇이 TODO인가" 단락을 추가. 기존 mvp-005/mvp-006-1 README 내용은 보존.

### 6) 검증

`projects/paper-trading`에서:

```bash
python -m compileall app tests
python -m pytest -p no:cacheprovider
```

저장소 루트에서:

```bash
git diff --stat
git status --short
```

기존(mvp-005) 19개 + mvp-006-1 약 17개 + mvp-007 신규 약 25개 모두 PASS. `compileall`/`pytest` 종료코드 0.

호스트에 `pytest` 등 미설치면 작업을 멈추고 `patch.md` Remaining TODOs에 `python3 -m pip install fastapi 'uvicorn[standard]' 'pydantic>=2' python-dotenv pytest httpx` 명령 기록.

### 7) `docs/ai/jobs/mvp-007/patch.md`

`plan.md` §4.8 템플릿(Implementation Summary 9단락 + Safety Confirmation + Test Results + Remaining TODOs) 그대로 채운다. 실제 KIS 값 미인용.

## 완료 정의 (Done)

- mvp-006-1 사전 점검 통과(또는 누락이면 작업 멈춤 + Remaining TODOs 기록).
- `app/broker/kis.py`에 `KisError` 계층 + 3개 sub-client + `KisBroker` 컴포지션 구현.
- 모든 client의 HTTP 메서드(`authenticate`/`refresh_token`/`get_account`/`get_positions`/`get_cash_balance`/`get_quote`/`get_last_price`) NotImplementedError + "TODO" 메시지.
- 토큰 상태 머신(`is_authenticated`/`get_access_token`/`clear_token`)이 HTTP 없이 동작.
- 계좌번호 마스킹(`masked_account_no`)이 `***xxxx` 패턴.
- `healthcheck_market_data()`와 `KisBroker.healthcheck()`가 정적 disconnected dict 반환.
- 모든 client `__repr__`가 secret/key/account/token 미노출.
- `app/api/server.py`가 `KisBroker`를 `app.state.kis_broker`에 보관(실패 시 None).
- `/paper/status`에 `kis_authenticated`/`kis_account_loaded`/`kis_market_data_available`/`last_broker_error`/`account_no_masked`/`secret_exposed` 필드, raw 값 미노출.
- `secret_exposed`로 이름 통일(`kis_secret_exposed` 잔재 없음).
- `app/strategy/`가 `app.broker.kis*` import 0건(grep).
- `app/broker/kis.py`에 HTTP 라이브러리 import 0건.
- `app/broker/kis.py`에 KIS URL/TR ID 하드코딩 0건.
- mvp-007 신규 테스트 3개 파일 + 보정 2개 파일 모두 PASS.
- mvp-005 19개 + mvp-006-1 약 17개 회귀 PASS.
- `OrderType`에 MARKET 멤버 없음.
- `git diff --stat`에 mvp-007 외 변경 없음.
- `.env` staged/committed 없음.
- `patch.md` 5섹션 + Implementation Summary 9단락 채움.
- commit/push/merge/deploy 자동화 없음.
