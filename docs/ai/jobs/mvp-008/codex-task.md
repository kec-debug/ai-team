# Codex Task — mvp-008: KIS 모의투자 주문 흐름 연결 준비 (HTTP 없음)

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-008/plan.md` and `docs/ai/jobs/mvp-008/request.ko.md` first.
>
> **중요**: 본 작업은 mvp-006-1 / mvp-007 위에 빌드된다. KIS HTTP 호출, 실주문, KIS endpoint URL/TR ID/payload는 본 작업에 포함되지 않는다(공식 문서 미확인).

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-008`
- 대상 디렉터리: `projects/paper-trading/`
- 본 작업은 KIS 주문 메서드의 **pre-flight 안전 가드 + 내부 도메인 변환 모델 + kill switch + 상태 응답 확장 + 테스트**만 만든다.

## 사전 점검 (Codex 첫 단계)

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
test -f app/broker/kis.py && grep -q "class KisBroker" app/broker/kis.py && echo "OK kis.py"
grep -q "class KisAuthClient" app/broker/kis.py && echo "OK KisAuthClient"
grep -q "class KisAccountClient" app/broker/kis.py && echo "OK KisAccountClient"
grep -q "class KisMarketDataClient" app/broker/kis.py && echo "OK KisMarketDataClient"
grep -q "kis_env" app/config.py && echo "OK Settings.kis_env"
grep -q "kis_authenticated" app/api/routes.py && echo "OK routes.py KIS status"
grep -q "secret_exposed" app/api/routes.py && echo "OK routes.py secret_exposed"
test -d .venv && echo "OK venv"
```

위 8개가 모두 OK여야 mvp-006-1/007이 정상 land된 상태. 누락이면 작업을 멈추고 `patch.md` Remaining TODOs에 기록.

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials, API key, token, account number 변경/생성/읽기 금지.
- 실제 KIS app key/secret/account/URL/TR ID를 어떤 파일에도 쓰지 않는다. 테스트는 가짜 값(`"12345678"`, `"fake-key"`, `"fake-secret"`)만 사용.
- KIS endpoint URL, TR ID, header, payload를 코드/문서에 하드코딩 금지. 공식 문서 확인 없이 추측 금지.
- 외부 HTTP 라이브러리(`requests`, `httpx`, `aiohttp`, `urllib3` 등) `app/broker/kis.py`에 import 금지.
- 네트워크 호출/소켓 시도 금지.
- 실주문 코드 신설 금지. 모든 KIS 주문 메서드(`place_order`/`cancel_order`/`replace_order`/`get_open_orders`/`get_fills`/`get_order_status`)는 최종적으로 `NotImplementedError` 또는 `KisOrderRejectedError`.
- live trading 활성화 금지.
- `OrderType`에 MARKET 멤버 추가 금지.
- RiskEngine/OMS 우회 코드 경로 신설 금지.
- Strategy 패키지가 `app.broker.kis*` import 금지(기존 상태 유지, grep 검증).
- OMS의 `_risk`/`_broker` private 유지.
- `/paper/status`나 어떤 응답에 raw key/secret/account/access_token 노출 금지.
- 임의 shell 명령 입력 UI/API 신설 금지.
- 본 작업 범위 외 파일 변경 금지. mvp-001..mvp-007 산출물(plan/codex-task/patch/review 문서) 미변경.
- `pip install` 실행 금지(이미 `.venv`에 의존성 설치됨).
- `app/domain/`, `app/broker/{base,paper,alpaca_paper}.py`, `app/oms/manager.py`, `app/runtime/`, `app/strategy/*`, `app/main.py`, `app/api/server.py` 미수정.

## 수정 허용 위치

### 신규

- `projects/paper-trading/tests/test_kis_order_preflight.py`
- `projects/paper-trading/tests/test_kis_order_request_model.py`
- `projects/paper-trading/tests/test_kill_switch.py`
- `docs/ai/jobs/mvp-008/patch.md`

### 수정 가능

- `projects/paper-trading/app/config.py` (kill_switch_engaged 필드 + env 로딩)
- `projects/paper-trading/app/risk/engine.py` (kill switch 최상단 reject)
- `projects/paper-trading/app/broker/kis.py` (KisOrderRejectedError, KisOrderRequest, validate_kis_order_request, _to_kis_request, get_fills, get_order_status, place_order/cancel_order/replace_order pre-flight)
- `projects/paper-trading/app/api/routes.py` (`/paper/status`에 4개 신규 필드)
- `projects/paper-trading/.env.example` (`KILL_SWITCH_ENGAGED=false` placeholder)
- `projects/paper-trading/README.md` (KIS 주문 흐름 단락)
- `projects/paper-trading/tests/test_broker_interface.py` (신규 메서드/타입 노출 확인 추가)
- `projects/paper-trading/tests/test_api_paper_status.py` (신규 4개 필드 assertion)
- `projects/paper-trading/tests/test_risk_engine.py` (kill switch 케이스)

### 절대 미수정

- `app/domain/*` 전부
- `app/broker/base.py`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`
- `app/oms/manager.py`
- `app/runtime/paper_runner.py`
- `app/strategy/*` 전부
- `app/main.py`
- `app/api/server.py`
- 기존 테스트 중 본 작업이 다루지 않는 것: `test_alpaca_paper_stub.py`, `test_config.py`, `test_models.py`, `test_oms.py`, `test_paper_broker.py`, `test_flow.py`, `test_paper_runner.py`, `test_strategy_premarket_gap.py`, `test_kis_config.py`, `test_kis_auth_client.py`, `test_kis_account_client.py`, `test_kis_market_data_client.py`
- 루트 `.gitignore`, 프로젝트 `.gitignore`
- mvp-001..mvp-007 산출물

## 구현 작업

`plan.md` §4 코드를 그대로 따른다. 다음은 빠뜨리기 쉬운 항목 요약.

### 1) `app/config.py`

- `Settings`에 `kill_switch_engaged: bool = False` 한 필드 추가(필드 순서는 dataclass 끝쪽).
- `load_settings()`의 `Settings(...)` 생성자 인자에 한 줄 추가:
  ```python
  kill_switch_engaged=_bool_env("KILL_SWITCH_ENGAGED", False),
  ```
- `_bool_env`는 mvp-006-1에서 이미 정의됨 — 그대로 재사용.
- 기존 paper/live/market-order 가드는 변경하지 않는다.

### 2) `app/risk/engine.py`

`RiskEngine.evaluate(intent)` 함수의 **최상단**에 (모든 기존 검사 이전):

```python
if self._settings.kill_switch_engaged:
    return RiskDecision(approved=False, reason="kill_switch_engaged", risk_token=None)
```

기존 다른 검사 로직은 그대로 유지. `RiskDecision` 시그니처는 기존 코드와 정확히 일치시킨다(필드명 확인 후 작성).

### 3) `app/broker/kis.py`

`plan.md` §4.4의 모든 신규 항목을 추가. 기존 코드는 보존하되 `place_order`/`cancel_order`/`replace_order`의 body는 plan §4.4.4대로 교체(pre-flight 호출 추가).

핵심 불변식:
- `KisOrderRequest`는 `account_no` raw 필드를 가지지 않는다. `account_no_masked`만.
- `validate_kis_order_request`의 모든 reject 메시지는 short reason code만 — raw 값 포함 금지.
- `KisOrderRejectedError(reason)` 생성자가 `self.reason = reason` 보관하여 테스트가 검증 가능.
- 외부 HTTP 라이브러리 import 0건. URL 0건. TR ID 키워드 0건.
- 본 단계에서 `cancel_order(broker_order_id)`는 `broker_order_id` 자체를 메시지에 포함시키지 않는다(opaque일 수 있으나 raw 노출 회피).

### 4) `app/api/routes.py`

`/paper/status` 핸들러 안에서 `plan.md` §4.5의 로직을 추가. 응답 dict에 4개 신규 키 추가:

- `kis_order_entry_ready` (bool)
- `kis_order_entry_mode` (str: `"disabled"` | `"paper_guarded"` | `"not_implemented"`)
- `kis_order_methods_fail_closed` (True literal)
- `kill_switch_engaged` (bool, from settings)

기존 mvp-005/006-1/007 필드는 모두 보존. 어떤 분기에서도 raw `kis_app_key`/`kis_app_secret`/`kis_account_no`를 응답에 포함시키지 않는다.

### 5) `.env.example`

기존 `ALLOW_MARKET_ORDERS=false` 라인 부근에 한 줄 추가:

```
KILL_SWITCH_ENGAGED=false
```

다른 라인 변경 금지.

### 6) `projects/paper-trading/README.md`

`plan.md` §4.7의 `### 주문 흐름 안전 가드 (mvp-008)` 단락을 KIS 섹션 안에 추가. 기존 단락은 변경 없음.

### 7) 테스트

`plan.md` §4.8의 코드 그대로 사용. 다음을 반드시 충족:

- **테스트 코드에 실제 KIS 계좌번호/키 절대 미포함.** 가짜 값(`"12345678"`, `"fake-key"`, `"fake-secret"`, `"oms-1"`)만.
- `test_kis_order_request_class_is_exported` 테스트가 `KisOrderRequest`/`KisOrderRejectedError`/`validate_kis_order_request` 모두 `app.broker.kis`에서 import 가능한지 확인.
- `test_to_kis_request_uses_masked_account`가 `req.account_no_masked.startswith("***")` 확인.
- `test_place_order_runs_preflight_before_notimplemented`가 잘못된 broker_order에서 `KisOrderRejectedError`(NotImplementedError 아님) 발생을 확인.
- `test_place_order_valid_input_reaches_notimplemented`가 정상 broker_order에서 `NotImplementedError` 발생을 확인.
- kill switch 테스트가 RiskEngine 측과 KIS pre-flight 측 양쪽에서 reject되는지 모두 확인.
- `tests/test_api_paper_status.py`의 두 시나리오(KIS configured / 미configured) 모두에 신규 필드 assertion 추가. raw 미노출 검증도 양쪽에 추가.

### 8) 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

기존 74개 + 신규 약 18–22개 모두 PASS. 종료코드 0.

저장소 루트:

```bash
git diff --stat
git status --short
```

mvp-008 변경은 모두 `projects/paper-trading/`(untracked) 안. mvp-008 외 dirty(GUI 변경 등)는 그대로 — 본 작업에서 만지지 않는다.

### 9) `docs/ai/jobs/mvp-008/patch.md`

`plan.md` §4.10 템플릿(섹션 1–5 + Implementation Summary 8단락) 그대로 채운다. 실제 KIS 값/계좌번호/키 절대 인용 금지.

## 완료 정의 (Done)

- 사전 점검 8개 항목 모두 통과(또는 멈춤 + Remaining TODOs).
- `Settings.kill_switch_engaged` 추가, `KILL_SWITCH_ENGAGED` env 로딩.
- `RiskEngine.evaluate()` 최상단에 kill switch reject, reason `"kill_switch_engaged"`.
- `app/broker/kis.py`에 `KisOrderRejectedError`, `KisOrderRequest`, `validate_kis_order_request`, `KisBroker._to_kis_request`, `KisBroker.get_fills`, `KisBroker.get_order_status` 추가.
- `KisBroker.place_order`/`cancel_order`/`replace_order` 모두 pre-flight 호출 후 `NotImplementedError`로 fail-closed.
- `KisOrderRequest`에 raw `account_no` 필드 없음. `account_no_masked` 있음.
- `validate_kis_order_request`의 모든 reject 메시지가 short reason code(raw 값 미포함).
- `/paper/status` 응답에 `kis_order_entry_ready`/`kis_order_entry_mode`/`kis_order_methods_fail_closed`/`kill_switch_engaged` 추가. raw credentials 미노출.
- `.env.example`에 `KILL_SWITCH_ENGAGED=false` 추가.
- 신규 테스트 3개 파일 + 기존 3개 테스트 확장 모두 PASS.
- mvp-005 19개 + mvp-006-1 17개 + mvp-007 38개 + mvp-008 신규 18–22개 = 약 92–96개 PASS.
- 외부 HTTP 라이브러리 import 0건(grep).
- KIS URL/TR ID 코드 0건(grep).
- Strategy 패키지가 `app.broker.kis*` import 0건(grep).
- `OrderType`에 MARKET 멤버 없음.
- `git diff --stat`에 mvp-008 외 변경 없음.
- `.env` staged/committed 없음.
- `patch.md` 5섹션 + Implementation Summary 8단락 완성.
- commit/push/merge/deploy 자동화 없음.
