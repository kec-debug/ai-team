# Codex Task — mvp-009: KIS 모의투자 주문 흐름 (내부 경계 + 변환 + sanitization, HTTP 없음)

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-009/plan.md` and `docs/ai/jobs/mvp-009/request.ko.md` first.
>
> **중요**: 본 작업은 mvp-006-1 / mvp-007 위에 빌드되며 **mvp-008을 흡수**한다. mvp-008(`docs/ai/jobs/mvp-008/`) plan/codex-task는 deprecated — 본 작업이 그 scope를 모두 포함한다. Codex는 mvp-009 단독으로 작업한다.

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-009`
- 대상 디렉터리: `projects/paper-trading/`
- 본 작업은 KIS 모의투자 주문의 **내부 경계 + 변환 모델 + 응답 sanitization + idempotency 키 + capabilities 노출 + 안전 가드 + 테스트**만 만든다. 실제 KIS HTTP 호출/실주문은 본 작업에 포함되지 않는다(공식 문서 미확인).

## 사전 점검 (Codex 첫 단계)

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
test -f app/broker/kis.py && grep -q "class KisBroker" app/broker/kis.py && echo "OK KisBroker"
grep -q "class KisAuthClient" app/broker/kis.py && echo "OK KisAuthClient"
grep -q "class KisAccountClient" app/broker/kis.py && echo "OK KisAccountClient"
grep -q "class KisMarketDataClient" app/broker/kis.py && echo "OK KisMarketDataClient"
grep -q "kis_env" app/config.py && echo "OK Settings.kis_env"
grep -q "kis_authenticated" app/api/routes.py && echo "OK routes.py KIS status"
grep -q "secret_exposed" app/api/routes.py && echo "OK routes.py secret_exposed"
test -d .venv && echo "OK venv"
```

위 8개 모두 OK여야 mvp-007 land 상태. 누락이면 멈춤 + Remaining TODOs.

`kill_switch_engaged`이 `app/config.py`에 이미 존재할 수도 있음(mvp-008 absorb로 이전 세션에 추가됐을 가능성). idempotent 추가 — 이미 있으면 그대로 두고 진행.

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials, API key, token, account number 변경/생성/읽기 금지.
- 실제 KIS app key/secret/account/URL/TR ID/payload를 어떤 파일에도 쓰지 않는다. 테스트는 가짜 값만(`"12345678"`, `"fake-key"`, `"fake-secret"`).
- KIS endpoint URL, TR ID, header, payload를 코드/문서에 하드코딩 금지. 공식 문서 확인 없이 추측 금지.
- 외부 HTTP 라이브러리(`requests`, `httpx`, `aiohttp`, `urllib3` 등) `app/broker/kis.py`에 import 금지.
- 네트워크 호출/소켓 시도 금지.
- 실주문 코드 신설 금지. 모든 KIS 주문 메서드는 `NotImplementedError` 또는 `KisOrderRejectedError`로 최종 fail-closed.
- live trading 활성화 금지.
- `OrderType`에 MARKET 멤버 추가 금지.
- RiskEngine/OMS 우회 코드 경로 신설 금지.
- Strategy 패키지가 `app.broker.kis*` import 금지(grep 검증).
- OMS의 `_risk`/`_broker` private 유지. OMS에 KIS 라우팅 신설 금지(여전히 PaperBroker만).
- `/paper/status`나 어떤 응답에 raw key/secret/account/access_token 노출 금지.
- `KisOrderRequest`에 raw `account_no` 필드 추가 금지.
- `KisOrderResponse.raw_response_sanitized`에 sanitize 거치지 않은 원본 dict 저장 금지.
- 임의 shell 명령 입력 UI/API 신설 금지.
- 본 작업 범위 외 파일 변경 금지. mvp-001..mvp-008 산출물 미변경.
- `pip install` 실행 금지.
- `app/domain/*`, `app/broker/{base,paper,alpaca_paper}.py`, `app/oms/`, `app/runtime/`, `app/strategy/*`, `app/main.py`, `app/api/server.py` 미수정.

## 수정 허용 위치

### 신규

- `projects/paper-trading/tests/test_kis_order_preflight.py`
- `projects/paper-trading/tests/test_kis_order_request_model.py`
- `projects/paper-trading/tests/test_kis_order_response_model.py`
- `projects/paper-trading/tests/test_kill_switch.py`
- `projects/paper-trading/tests/test_kis_capabilities.py`
- `docs/ai/jobs/mvp-009/patch.md`

### 수정 가능

- `projects/paper-trading/app/config.py` (`kill_switch_engaged` 추가, idempotent)
- `projects/paper-trading/app/risk/engine.py` (kill switch 최상단 reject)
- `projects/paper-trading/app/broker/kis.py` (KisOrderRejectedError, KisOrderRequest with market+idempotency_key, KisOrderResponse, sanitize_kis_response, validate_kis_order_request, _idempotency_key_for, _to_kis_request, capabilities, get_fills, get_order_status, place_order/cancel_order/replace_order pre-flight)
- `projects/paper-trading/app/api/routes.py` (`/paper/status`에 9개 신규 필드)
- `projects/paper-trading/.env.example` (`KILL_SWITCH_ENGAGED=false`, idempotent)
- `projects/paper-trading/README.md` (mvp-009 단락)
- `projects/paper-trading/tests/test_broker_interface.py`
- `projects/paper-trading/tests/test_api_paper_status.py`
- `projects/paper-trading/tests/test_risk_engine.py`

### 절대 미수정

- `app/domain/{enums,orders,market}.py`
- `app/broker/{base,paper,alpaca_paper}.py`
- `app/oms/manager.py`
- `app/runtime/paper_runner.py`
- `app/strategy/*` 전부
- `app/api/server.py`
- `app/main.py`
- mvp-001..mvp-008 산출물 (mvp-008 plan/codex-task는 deprecated, 그대로 둠)
- 기존 테스트 중 본 작업이 다루지 않는 것: `test_alpaca_paper_stub.py`, `test_config.py`, `test_models.py`, `test_oms.py`, `test_paper_broker.py`, `test_flow.py`, `test_paper_runner.py`, `test_strategy_premarket_gap.py`, `test_kis_config.py`, `test_kis_auth_client.py`, `test_kis_account_client.py`, `test_kis_market_data_client.py`
- 루트 `.gitignore`, 프로젝트 `.gitignore`

## 구현 작업

`plan.md` §4 코드를 그대로 따른다. 다음은 빠뜨리기 쉬운 항목:

### 1) `app/config.py`

`Settings`에 `kill_switch_engaged: bool = False`(없으면) + `load_settings()`에서 `_bool_env("KILL_SWITCH_ENGAGED", False)` 로딩. 기존 코드 보존.

### 2) `app/risk/engine.py`

`RiskEngine.evaluate(intent)` **최상단**(다른 모든 검사 전)에:

```python
if self._settings.kill_switch_engaged:
    return RiskDecision(approved=False, reason="kill_switch_engaged", risk_token=None)
```

기존 검사 로직은 그대로 유지.

### 3) `app/broker/kis.py`

기존 코드(mvp-006-1/007의 `KisError`, `KisConfigError`, `KisAuthError`, `KisDataUnavailableError`, `KisAuthClient`, `KisAccountClient`, `KisMarketDataClient`, `KisBroker`)는 보존.

#### 3.1 신규 exception

```python
class KisOrderRejectedError(KisError):
    def __init__(self, reason: str) -> None:
        super().__init__(f"KIS order rejected: {reason}")
        self.reason = reason
```

#### 3.2 신규 frozen dataclass

```python
@dataclass(frozen=True)
class KisOrderRequest:
    symbol: str
    market: str
    side: Side
    quantity: int
    order_type: OrderType
    limit_price: Decimal
    extended_hours: bool
    account_no_masked: str
    broker_environment: str
    idempotency_key: str


@dataclass(frozen=True)
class KisOrderResponse:
    internal_order_id: str
    broker_order_id: str | None
    broker: str
    status: str
    submitted_at: datetime
    symbol: str
    side: Side
    quantity: int
    limit_price: Decimal
    raw_response_sanitized: dict[str, Any]
```

(imports: `dataclass`, `Decimal`, `Side`, `OrderType`, `datetime`, `Any` — 기존 import 재사용 또는 추가.)

#### 3.3 `sanitize_kis_response` 모듈 함수

`plan.md` §4.4.4 코드 그대로. 핵심:
- 입력이 None / non-dict → 빈 dict 반환
- 키 이름 case-insensitive 매칭 set: `app_key`, `appkey`, `appKey`, `app_secret`, `appsecret`, `appSecret`, `account_no`, `accountNo`, `cano`, `acct_no`, `access_token`, `accessToken`, `authorization`, `Authorization`, `tr_key`, `trKey`, `secret`
- `settings.kis_app_key`/`kis_app_secret`/`kis_account_no` 값과 일치하는 string 값 → `"<redacted>"`
- 중첩 dict/list 재귀

#### 3.4 `validate_kis_order_request` 모듈 함수

`plan.md` §4.4.5 코드 그대로. 8개 reject 사유 short reason code(`trading_mode_not_paper`, `live_trading_enabled`, `market_orders_allowed_flag_set`, `kis_env_not_paper`, `kill_switch_engaged`, `order_type_not_limit`, `quantity_invalid`, `limit_price_invalid`).

#### 3.5 `KisBroker` 메서드

`plan.md` §4.4.6 그대로:

- `_idempotency_key_for(broker_order)` — deterministic: `f"kis-paper-{broker_order.oms_id}"`.
- `_to_kis_request(broker_order)` — masked account 사용, `market="US"`, `extended_hours=False` 기본, idempotency_key.
- `capabilities() -> dict[str, bool]` — 6개 키 모두 False.
- `place_order(broker_order)` — `validate_kis_order_request` → `_to_kis_request` → `NotImplementedError`.
- `cancel_order(broker_order_id)` — settings 4개 가드(paper/live/env/kill_switch) → `NotImplementedError`.
- `replace_order(broker_order_id, broker_order)` — `validate_kis_order_request` → `_to_kis_request` → `NotImplementedError`.
- `get_fills() -> list[OrderAck]` — `NotImplementedError` + TODO.
- `get_order_status(broker_order_id) -> dict[str, Any]` — `NotImplementedError` + TODO.
- 기존 `get_open_orders` 유지 (mvp-007 NotImplementedError).
- `healthcheck()`에 `"capabilities": self.capabilities()` 추가 (선택, 일관성).

### 4) `app/api/routes.py`

`/paper/status` 핸들러 안에서:

```python
# mvp-008 absorbed
kis_order_entry_mode = "disabled"
if kis_broker is not None:
    settings_safe = (
        settings.trading_mode.value == "paper"
        and settings.live_trading_enabled is False
        and settings.allow_market_orders is False
        and settings.kis_env == "paper"
        and settings.kill_switch_engaged is False
    )
    kis_order_entry_mode = "not_implemented" if settings_safe else "disabled"
kis_order_entry_ready = (kis_broker is not None) and (kis_order_entry_mode != "disabled")
capabilities = kis_broker.capabilities() if kis_broker else {
    "submission": False, "cancel": False, "replace": False,
    "open_orders": False, "fills": False, "order_status": False,
}
```

응답 dict에 추가(9개):

```python
"kis_order_entry_ready": kis_order_entry_ready,
"kis_order_entry_mode": kis_order_entry_mode,
"kis_order_methods_fail_closed": True,
"kill_switch_engaged": bool(settings.kill_switch_engaged),
"kis_order_submission_available": bool(capabilities.get("submission", False)),
"kis_cancel_available": bool(capabilities.get("cancel", False)),
"kis_replace_available": bool(capabilities.get("replace", False)),
"kis_open_orders_available": bool(capabilities.get("open_orders", False)),
"kis_fills_available": bool(capabilities.get("fills", False)),
```

기존 mvp-005/006-1/007 필드는 그대로 유지. raw credentials 응답에 미포함.

### 5) `.env.example`

`ALLOW_MARKET_ORDERS=false` 다음에(없으면):

```
KILL_SWITCH_ENGAGED=false
```

다른 라인 변경 금지.

### 6) `projects/paper-trading/README.md`

`plan.md` §4.7 단락(주문 흐름 안전 가드 + 내부 변환 모델 + Kill switch + Capabilities) 추가. KIS 섹션 안에. 기존 단락 변경 없음.

### 7) 테스트

`plan.md` §4.8의 코드 그대로 사용. 핵심:

- **모든 테스트가 가짜 값만 사용** — `"12345678"`, `"fake-key"`, `"fake-secret"`, `"oms-42"`. 실제 KIS 값 절대 미사용.
- `test_kis_order_request_model.py`: `market`, `idempotency_key` 필드 존재 확인 + `account_no` 부재 확인 + idempotency_key deterministic 확인.
- `test_kis_order_response_model.py`: `KisOrderResponse` 10개 필드 + `sanitize_kis_response` 4가지 시나리오(키 이름 매칭, 값 매칭, 중첩, None/empty).
- `test_kis_capabilities.py`: 6개 키, 모두 False.
- `test_kill_switch.py`: RiskEngine + KIS pre-flight 양쪽 reject.
- `test_kis_order_preflight.py`: 8개 사유 + 정상 통과 후 NotImplementedError.
- `test_broker_interface.py` 보정: 신규 exports + `get_fills`/`get_order_status` 메서드 + `capabilities` 호출.
- `test_api_paper_status.py` 보정: 9개 신규 필드 + raw 미노출 텍스트 검사 양쪽 시나리오.
- `test_risk_engine.py` 보정: kill switch reject.

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

mvp-007 시점 74개 + 본 작업 신규 약 28–34개 모두 PASS. 종료코드 0.

호스트 의존성 미설치라 실패 시 작업 멈춤 + Remaining TODOs에 명령 명시(이미 `.venv`가 있으므로 거의 발생 안 함).

### 9) `docs/ai/jobs/mvp-009/patch.md`

`plan.md` §4.10 템플릿(섹션 1–5 + Implementation Summary 9단락) 그대로 채운다. 실제 KIS 값 미인용.

## 완료 정의 (Done)

- 사전 점검 통과(또는 멈춤 + Remaining TODOs).
- `Settings.kill_switch_engaged` 보장 + env 로딩(idempotent).
- `RiskEngine.evaluate` 최상단 kill switch reject, reason `"kill_switch_engaged"`.
- `app/broker/kis.py`에 `KisOrderRejectedError`, `KisOrderRequest`(market+idempotency_key 포함), `KisOrderResponse`, `sanitize_kis_response`, `validate_kis_order_request`, `KisBroker._idempotency_key_for`, `KisBroker._to_kis_request`, `KisBroker.capabilities`, `KisBroker.get_fills`, `KisBroker.get_order_status` 추가.
- `KisBroker.place_order`/`cancel_order`/`replace_order` 모두 pre-flight 후 `NotImplementedError`.
- `KisOrderRequest`에 raw `account_no` 부재. `account_no_masked` 존재.
- `KisOrderResponse.raw_response_sanitized`는 `sanitize_kis_response` 결과만 보유.
- `/paper/status`에 9개 신규 필드 추가, raw credentials 미노출.
- `.env.example`에 `KILL_SWITCH_ENGAGED=false`.
- 신규 5개 테스트 파일 + 기존 3개 테스트 확장 모두 PASS.
- mvp-007 시점 74개 + mvp-009 신규 약 28–34개 = 약 102–108개 PASS.
- 외부 HTTP 라이브러리 import 0건(grep).
- KIS URL/TR ID 코드 0건(grep).
- Strategy 패키지가 `app.broker.kis*` import 0건.
- `OrderType`에 MARKET 멤버 없음.
- `git diff --stat`에 mvp-009 외 변경 없음.
- `.env` staged/committed 없음.
- `patch.md` 5섹션 + Implementation Summary 9단락 완성.
- commit/push/merge/deploy 자동화 없음.
