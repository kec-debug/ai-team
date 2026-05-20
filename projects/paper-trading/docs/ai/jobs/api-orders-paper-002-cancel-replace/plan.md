# api-orders-paper-002-cancel-replace — KIS 모의투자 주문 취소 / 정정 구현

## 1. 요청 요약

KIS_2-check audit (`docs/ai/jobs/KIS_2-check/plan.md`, `recommendation.md`, `review.md`) 가 다섯 개 후속 기능 중 cancel_order / replace_order 만 paper-supported `Confirmed: yes` 로 READY, 나머지 세 개 (get_open_orders / get_fills / get_order_status) 는 BLOCKED-BY-DOCS 로 분류했다. 본 작업은 audit 의 권고에 따라 cancel_order / replace_order 본문만 catalog §4.2 / §4.6 의 paper-supported 행 (POST `/uapi/overseas-stock/v1/trading/order-rvsecncl`, paper 미국 정정·취소 공용 TR_ID `VTTT1004U`) 기반으로 구현한다.

audit review 에서 명시한 4 개 design gap (G1~G4) 을 본 plan 에서 모두 해소한다.

### G1 — `_order_history` 의 exchange 보존: **선택 A**

`KisOrderResponse` dataclass 에 `exchange: str = "NASD"` 필드 추가 (default 값으로 후방 호환). 선택 A 사유:

- audit review 가 식별한 4 옵션 중, dataclass 확장이 가장 명시적이고 future Asia 확장에 사전 호환적이다.
- existing 위치 인자 호출은 `internal_order_id`, `broker_order_id`, `broker`, `status`, `submitted_at`, `symbol`, `side`, `quantity`, `limit_price`, `raw_response_sanitized` 10 개 모두 명시 kwargs 인 경우만이라 default 필드 추가는 회귀 없음 (test_kis_order_response_model.py 의 KisOrderResponse 직접 생성 부분 검증 필요).
- 선택 C (NASD default 만 사용) 보다 명시적이라 G4 (Asia 제외) 의 미래 완화가 쉬워진다.

추가로 G3 해소를 위해 두 개 필드 추가:

- `replacement_broker_order_id: str | None = None` — 본 entry 가 replace 의 대상 (old) 일 때, 정정 후 생성된 new broker_order_id 를 가리킨다. cancel 시에는 None 유지.
- `replaces_broker_order_id: str | None = None` — 본 entry 가 replace 의 결과 (new) 일 때, 원본 (old) broker_order_id 를 가리킨다. place_order / cancel 시에는 None.

### G2 — cancel/replace 호출 경로: **선택 A (adapter level only)**

KisBroker.cancel_order / KisBroker.replace_order 본문만 구현한다. OMS / runtime helper / GUI / dashboard 와의 연결은 본 작업 범위 외이며 후속 runtime job 으로 분리한다. 본 작업 안에서 동작 검증은 `KisBroker.*` 직접 호출 + transport 주입 단위 테스트로 수행.

`capabilities()` 의 `cancel` / `replace` 플래그는 conservative `False` 그대로 (api-orders-paper-001 의 status surface 보호 정책과 정합). `healthcheck()["order_execution_implemented"]` 도 그대로 `False`. routes.py 와 status 테스트 회귀 없음.

### G3 — replace 후 새 ODNO 처리

성공한 정정 응답의 새 `output.ODNO` 를 다음과 같이 처리한다:

1. 원본 entry (`_order_history[old_broker_order_id]`) 의 status 를 `"submitted"` → `"replaced"` 로 갱신하고 `replacement_broker_order_id=new_odno` 를 설정한다. dataclass 가 frozen 이므로 `dataclasses.replace(entry, status="replaced", replacement_broker_order_id=new_odno, raw_response_sanitized=sanitized)` 로 갱신 사본을 만들고 dict 값 교체. **old key 는 dict 에서 제거하지 않는다** (G3 의 "기존 order id 는 유지" / "조용히 덮어쓰지 않는다" 요구).
2. 새 entry 는 `KisOrderResponse(broker_order_id=new_odno, replaces_broker_order_id=old_broker_order_id, status="replacement_submitted", symbol=old.symbol, side=old.side, quantity=new_broker_order.quantity, limit_price=new_broker_order.limit_price, exchange=old.exchange, ...)` 로 새로 생성해 `_order_history[new_odno]` 에 저장.
3. `_last_order_response` 를 새 entry 로 갱신 (place_order 와 동일 의미: 가장 최근에 활성화된 주문).
4. `OrderAck(broker_order_id=new_odno, status="replacement_submitted", mode=PAPER)` 반환.

cancel 의 경우:

1. `_order_history[broker_order_id]` 의 status 를 `"cancelled"` 로 갱신하고 `raw_response_sanitized` 를 cancel 응답으로 덮어쓴다.
2. `_last_order_response` 는 갱신하지 않음 (새 주문이 생성된 게 아니므로).
3. 함수는 `None` 반환 (기존 시그니처 유지).

### G4 — 아시아 거래소 제외

본 작업의 endpoint / TR_ID / 거래소 allowlist 는 **미국주식 (`NASD` / `NYSE` / `AMEX`) + paper 미국 정정·취소 공용 TR_ID `VTTT1004U` 1 개** 로 한정한다.

- 코드 / 테스트 / 문서에 Asia paper cancel TR_ID 추가 금지. catalog §4.2 는 "그 외 아시아는 정정취소 sheet `tr_id` 셀 본문 참조" 라고만 명시하고 본 catalog 의 paper TR_ID 칸에 채워 넣지 않았으므로 사용 불가.
- 실전 cancel TR_ID (`TTTT1004U` 미국, `TTTS1003U` 홍콩, `TTTS0309U` 일본) 추가 금지.
- transport 가 `body["OVRS_EXCG_CD"]` 를 `KIS_PAPER_ORDER_EXCHANGES` (api-orders-paper-001 의 기존 frozenset `{"NASD", "NYSE", "AMEX"}`) 안에서만 허용. SEHK / TKSE / HASE / VNSE / SHAA / SZAA 모두 transport 단계에서 `invalid_exchange` 로 fail-closed.

추가 제약 (request 의 "절대 하지 말 것" 직역, 위 G1~G4 외에):

- get_open_orders / get_fills / get_order_status 본문 구현 금지. 현재의 NotImplementedError 또는 동등 fail-closed 유지.
- live trading / 실전 endpoint / 실전 TR_ID / catalog 미확인 값 / 외부 HTTP 라이브러리 / Strategy·Agent·LLM 의 broker 직접 호출 / OMS 우회 / RiskEngine 우회 / `OrderType.MARKET` / `OrderType.STOP` / `ALLOW_MARKET_ORDERS=true` / FX 변환 / `.env` 변경 / 실 secret 기록 / GUI 파일 수정 / 자동 git commit·push·merge·deploy 모두 금지.

## 2. 작업 범위

포함하는 것:

- `app/broker/kis.py`:
  - `KisOrderResponse` 에 `exchange: str = "NASD"`, `replacement_broker_order_id: str | None = None`, `replaces_broker_order_id: str | None = None` 세 필드 추가 (default 보유, 위치 인자 호출 후방 호환).
  - 신규 상수: `KIS_OVERSEAS_CANCEL_REPLACE_PATH`, `KIS_PAPER_CANCEL_REPLACE_TR_ID_US`, `KIS_PAPER_CANCEL_REPLACE_TR_IDS` (frozenset 1 개), `KIS_PAPER_ORDER_ALL_TR_IDS` (place_order + cancel_replace 통합 allowlist), `KIS_RVSE_CNCL_DVSN_REPLACE="01"`, `KIS_RVSE_CNCL_DVSN_CANCEL="02"`, `KIS_PAPER_ORDER_CANCEL_UNPR="0"`.
  - 신규 helper:
    - `_build_paper_cancel_body(*, cano, acnt_prdt_cd, exchange, symbol, origin_odno, original_qty) -> dict[str, str]` — RVSE_CNCL_DVSN_CD="02", OVRS_ORD_UNPR="0".
    - `_build_paper_replace_body(*, cano, acnt_prdt_cd, exchange, symbol, origin_odno, new_qty, new_limit_price) -> dict[str, str]` — RVSE_CNCL_DVSN_CD="01", OVRS_ORD_UNPR=`format(new_limit_price, "f")`.
  - `UrllibOrderTransport.submit_order` 시그니처에 `path: str` keyword 추가. 내부적으로 `(tr_id → expected_path)` 매핑으로 `path != expected_path` 인 경우 `KisOrderRejectedError("path_tr_id_mismatch")` 로 거절. ORD_DVSN 검사는 place_order TR_ID 일 때만 적용, cancel_replace TR_ID 일 때는 `RVSE_CNCL_DVSN_CD ∈ {"01", "02"}` 검사 적용.
  - `MockOrderTransport.submit_order` 시그니처도 동일하게 path 추가 (어차피 raise 만 함, no-op).
  - `KisBroker.place_order` 의 transport 호출에 `path=KIS_OVERSEAS_ORDER_PATH` 추가 (기존 동작 유지).
  - `KisBroker.place_order` 가 성공 후 `_order_history[odno] = response_record` 도 함께 갱신 (기존의 `_last_order_response` 유지).
  - `KisBroker.__init__` 에 `self._order_history: dict[str, KisOrderResponse] = {}` 추가.
  - `KisBroker.cancel_order(broker_order_id)` 본문 구현 (§4 의 흐름).
  - `KisBroker.replace_order(broker_order_id, broker_order)` 본문 구현 (§4 의 흐름).
  - `KisBroker.last_order_response`, 신규 `last_order_history()` (선택) 프로퍼티 검토. **본 작업은 `last_order_response` 만 유지** 하고 history 는 internal-only (테스트가 `broker._order_history` 로 직접 접근 가능; 외부 API 노출은 후속 runtime job 으로).
  - **변경 금지**: `KisAuthClient`, `KisAccountClient`, `KisMarketDataClient`, `KisOrderRequest`, `KisPosition`, `KisCashBalance`, `KisDryRunPreview`, `sanitize_kis_response`, `validate_kis_order_request`, `_to_kis_request`, `_dry_run_preview`, `_idempotency_key_for`, `_split_kis_account_no`, `_validate_paper_settings`, `KisHttpClient`, market data transport classes, account transport classes, 모든 KIS_OVERSEAS_PRICE_* / KIS_OVERSEAS_BALANCE_* 상수, `capabilities()`, `healthcheck()`, `get_open_orders()`, `get_fills()`, `get_order_status()`.

- 신규 테스트 파일 `tests/test_kis_paper_order_cancel_replace.py`: helper / cancel / replace / transport allowlist / history preservation / secret leak / Asia 거래소 차단 / 모듈 내 live TR_ID 부재 / capability surface 보존 회귀.

- 좁은 갱신 (각 1 함수의 1-3 줄):
  - `tests/test_broker_interface.py::test_kis_place_cancel_replace_not_implemented` — cancel/replace 의 `NotImplementedError` 단언을 `KisOrderRejectedError, match="unknown_broker_order_id"` 로 변경.
  - `tests/test_broker_interface.py::test_kis_protocol_methods_delegate_to_not_implemented` — `broker.cancel("x")` 의 `NotImplementedError` 를 `KisOrderRejectedError, match="unknown_broker_order_id"` 로 변경.
  - `tests/test_kis_http_boundaries.py::test_cancel_replace_queries_fail_closed` — `broker.cancel_order("broker-1")` / `broker.replace_order("broker-1", _broker_order())` 두 단언만 `KisOrderRejectedError, match="unknown_broker_order_id"` 로 변경. **`get_open_orders` / `get_fills` / `get_order_status` 의 `NotImplementedError` 단언 3 개는 절대 변경하지 않는다.**

- `docs/ai/jobs/api-orders-paper-002-cancel-replace/patch.md` (Codex 가 작성).

- (선택) `projects/paper-trading/README.md` 1-2 줄 보강 — 새 env 변수 안내 금지. 생략 가능.

제외 (절대 안 하는 것):

- live trading / 실전 endpoint / 실전 TR_ID / catalog 미확인 값.
- Asia 거래소 cancel·replace TR_ID. 코드/테스트/문서/grep target 어디에도 등장 금지. (테스트가 transport 의 disallowed_tr_id 검증을 위해 사용할 때는 `"TTTS" + "1003U"` 같은 string concatenation 으로 작성해 grep clean 유지.)
- get_open_orders / get_fills / get_order_status 본문 구현.
- `OrderType.MARKET` 3중 가드 우회, `ALLOW_MARKET_ORDERS=true` 허용, `OrderType.STOP` 도입.
- 외부 HTTP 라이브러리.
- `app/broker/kis_http.py` 변경. `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/base.py`, `app/broker/kis_token_cache.py`, `app/broker/kis_quote_mapper.py`, `app/broker/kis_account_*` (없음) 변경.
- `app/api/*`, `app/static/*`, `app/main.py`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/domain/*` (단, `app.domain.orders` 와 `app.domain.enums` 변경 없이도 본 작업이 완료 가능), `app/config.py` 변경.
- 새 env 변수.
- `.env` / `.env.example` 변경.
- Strategy / Agent / LLM 의 broker 직접 호출.
- `docs/kis/MISSING_OFFICIAL_VALUES.md` 변경.
- 자동 git commit / push / merge / deploy.

## 3. 수정해야 할 파일

| 경로 | 변경 종류 | 요약 |
| --- | --- | --- |
| `projects/paper-trading/app/broker/kis.py` | MODIFY | (1) `KisOrderResponse` 에 3 개 default 필드 추가 (G1, G3). (2) cancel/replace 상수·helper·body builder. (3) `UrllibOrderTransport.submit_order` 시그니처에 `path` 추가 + path/tr_id 매핑 검사 + RVSE_CNCL_DVSN_CD 검사. (4) `MockOrderTransport.submit_order` 시그니처 동기화. (5) `KisBroker.__init__` 에 `_order_history` 추가. (6) `KisBroker.place_order` 가 history 갱신 + path 명시 전달. (7) `KisBroker.cancel_order` 본문. (8) `KisBroker.replace_order` 본문. (9) 주문 외 메서드 (cancel/replace 외) 변경 금지. |
| `projects/paper-trading/tests/test_kis_paper_order_cancel_replace.py` | NEW | 본문 §5 의 신규 테스트 모음. |
| `projects/paper-trading/tests/test_broker_interface.py` | MODIFY (좁은) | 2 함수 narrow 갱신 — cancel/replace 의 NotImplementedError → `KisOrderRejectedError, match="unknown_broker_order_id"`. 다른 함수 절대 변경 금지. |
| `projects/paper-trading/tests/test_kis_http_boundaries.py` | MODIFY (좁은) | 1 함수 (`test_cancel_replace_queries_fail_closed`) 의 cancel/replace 단언만 갱신. `get_open_orders` / `get_fills` / `get_order_status` 단언 3 개는 절대 변경 금지. |
| `projects/paper-trading/docs/ai/jobs/api-orders-paper-002-cancel-replace/patch.md` | NEW | Codex 가 작성. |
| `projects/paper-trading/README.md` | MODIFY (선택, 1-2 줄) | 새 env 변수 안내 금지. 생략 가능. |

**범위 확장 사유**: `tests/test_broker_interface.py` 와 `tests/test_kis_http_boundaries.py` 의 cancel/replace 회귀는 본 구현이 NotImplementedError → KisOrderRejectedError 로 fail-closed 의미를 정밀화하기 때문에 동일한 형식의 좁은 1-3 줄 갱신이 필요. api-market-data-001 / api-account-001 / api-orders-paper-001 의 동일 narrow-edit 패턴.

손대지 않는 파일:

- `app/broker/kis_http.py`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/base.py`, `app/broker/kis_token_cache.py`, `app/broker/kis_quote_mapper.py`.
- `app/api/*` (server.py / routes.py 포함), `app/static/*`, `app/main.py`.
- `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`.
- `app/config.py`, `app/domain/*` (enums / orders / quote / market / fills).
- `docs/kis/MISSING_OFFICIAL_VALUES.md`, `.env`, `.env.example`.
- `tests/test_kis_account_client.py`, `tests/test_kis_market_data_client.py`, `tests/test_kis_quote_mapper.py`, `tests/test_kis_auth_client.py`, `tests/test_kis_token_cache.py`, `tests/test_kis_api_mode.py`, `tests/test_kis_config.py`, `tests/test_kis_capabilities.py`, `tests/test_kis_order_request_model.py`, `tests/test_kis_order_response_model.py`, `tests/test_kis_order_preflight.py`, `tests/test_kis_paper_order_submission.py`, `tests/test_paper_e2e_pipeline.py`, `tests/test_paper_e2e_api.py`, `tests/test_paper_engine.py`, `tests/test_paper_runner.py`, `tests/test_oms.py`, `tests/test_risk_engine.py`, `tests/test_portfolio_service.py`, `tests/test_paper_journal.py`, `tests/test_status_modules.py`, `tests/test_api_paper_status.py`, `tests/test_kill_switch.py`, `tests/test_missing_official_values_doc.py`, `tests/test_missing_market_data_values_doc.py`, `tests/test_quote_model.py`, `tests/test_strategy_premarket_gap.py`, `tests/test_dry_run_reports.py`, `tests/test_dry_run_analyzer.py`, `tests/test_dashboard.py`, `tests/test_reports_api.py`, `tests/test_alpaca_paper_stub.py`, `tests/test_session_router.py`, `tests/test_broker_interface.py` 외 모든 함수, `tests/test_kis_http_boundaries.py` 외 모든 함수, `tests/conftest.py`.

## 4. Codex 구현 지시문

자세한 단계는 `codex-task.md` 에 기록. 요지:

### 4.1 `KisOrderResponse` 확장 (G1 + G3)

```python
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
    exchange: str = "NASD"
    replacement_broker_order_id: str | None = None
    replaces_broker_order_id: str | None = None
```

- 세 필드 모두 default 보유 → 기존 위치 인자 호출 후방 호환. test_kis_order_response_model.py 의 기존 KisOrderResponse 생성 코드 (10 개 kwargs) 는 그대로 통과.
- `status` 의 허용 값: `"submitted"` (place_order 성공), `"cancelled"` (cancel 성공 후 갱신), `"replaced"` (replace 성공 후 old entry 갱신), `"replacement_submitted"` (replace 성공 후 new entry).

### 4.2 cancel/replace 상수

```python
# docs/kis/MISSING_OFFICIAL_VALUES.md §4.2 / §4.6 (paper VTTT1004U US 정정·취소 공용 only).
KIS_OVERSEAS_CANCEL_REPLACE_PATH = "/uapi/overseas-stock/v1/trading/order-rvsecncl"
KIS_PAPER_CANCEL_REPLACE_TR_ID_US = "VTTT1004U"
KIS_PAPER_CANCEL_REPLACE_TR_IDS = frozenset({KIS_PAPER_CANCEL_REPLACE_TR_ID_US})
KIS_PAPER_ORDER_ALL_TR_IDS = KIS_PAPER_ORDER_TR_IDS | KIS_PAPER_CANCEL_REPLACE_TR_IDS
KIS_RVSE_CNCL_DVSN_REPLACE = "01"
KIS_RVSE_CNCL_DVSN_CANCEL = "02"
KIS_RVSE_CNCL_DVSN_VALUES = frozenset({KIS_RVSE_CNCL_DVSN_REPLACE, KIS_RVSE_CNCL_DVSN_CANCEL})
KIS_PAPER_CANCEL_UNPR = "0"
```

place_order TR_IDs (`KIS_PAPER_ORDER_TR_IDS`) 와 cancel/replace TR_IDs 는 별도 frozenset 으로 유지. 통합 allowlist `KIS_PAPER_ORDER_ALL_TR_IDS` 는 transport 의 1 차 게이트.

### 4.3 Body builders

```python
def _build_paper_cancel_body(
    *,
    cano: str,
    acnt_prdt_cd: str,
    exchange: str,
    symbol: str,
    origin_odno: str,
    original_qty: int,
) -> dict[str, str]:
    return {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "OVRS_EXCG_CD": exchange,
        "PDNO": symbol,
        "ORGN_ODNO": origin_odno,
        "RVSE_CNCL_DVSN_CD": KIS_RVSE_CNCL_DVSN_CANCEL,  # "02"
        "ORD_QTY": str(int(original_qty)),
        "OVRS_ORD_UNPR": KIS_PAPER_CANCEL_UNPR,  # "0"
    }


def _build_paper_replace_body(
    *,
    cano: str,
    acnt_prdt_cd: str,
    exchange: str,
    symbol: str,
    origin_odno: str,
    new_qty: int,
    new_limit_price: Decimal,
) -> dict[str, str]:
    return {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "OVRS_EXCG_CD": exchange,
        "PDNO": symbol,
        "ORGN_ODNO": origin_odno,
        "RVSE_CNCL_DVSN_CD": KIS_RVSE_CNCL_DVSN_REPLACE,  # "01"
        "ORD_QTY": str(int(new_qty)),
        "OVRS_ORD_UNPR": format(new_limit_price, "f"),
    }
```

두 body 모두 catalog §4.6 의 `Confirmed: yes` 필드만 포함. `ORD_DVSN`, `SLL_TYPE`, `CTAC_TLNO`, `MGCO_APTM_ODNO`, `START_TIME`/`END_TIME`/`ALGO_ORD_TMD_DVSN_CD` 등 다른 필드 추가 금지.

### 4.4 Transport 시그니처 확장

`KisOrderTransport` Protocol 과 `MockOrderTransport.submit_order` / `UrllibOrderTransport.submit_order` 모두 `path: str` keyword 인자 추가.

`UrllibOrderTransport.submit_order` 의 신규 게이트 순서:

```python
EXPECTED_PATH_BY_TR_ID = {
    KIS_PAPER_ORDER_TR_ID_US_BUY: KIS_OVERSEAS_ORDER_PATH,
    KIS_PAPER_ORDER_TR_ID_US_SELL: KIS_OVERSEAS_ORDER_PATH,
    KIS_PAPER_CANCEL_REPLACE_TR_ID_US: KIS_OVERSEAS_CANCEL_REPLACE_PATH,
}

def submit_order(self, *, base_url, access_token, app_key, app_secret, tr_id, path, body):
    if _kis_extract_host(base_url) not in KIS_PAPER_ORDER_HOSTS:
        raise KisOrderRejectedError("disallowed_host")
    if tr_id not in KIS_PAPER_ORDER_ALL_TR_IDS:
        raise KisOrderRejectedError("disallowed_tr_id")
    expected_path = EXPECTED_PATH_BY_TR_ID[tr_id]
    if path != expected_path:
        raise KisOrderRejectedError("path_tr_id_mismatch")
    exchange = body.get("OVRS_EXCG_CD", "")
    if exchange not in KIS_PAPER_ORDER_EXCHANGES:
        raise KisOrderRejectedError("invalid_exchange")
    if tr_id in KIS_PAPER_ORDER_TR_IDS:
        # place_order: enforce LIMIT only
        if body.get("ORD_DVSN") != KIS_PAPER_ORDER_LIMIT_DVSN:
            raise KisOrderRejectedError("ord_dvsn_not_limit")
    else:
        # cancel/replace: enforce RVSE_CNCL_DVSN_CD ∈ {"01", "02"}
        if body.get("RVSE_CNCL_DVSN_CD") not in KIS_RVSE_CNCL_DVSN_VALUES:
            raise KisOrderRejectedError("invalid_rvse_cncl_dvsn")

    url = f"{base_url.rstrip('/')}{path}"
    ...
```

URL 구성에 `path` 인자 사용 (기존 하드코딩 `KIS_OVERSEAS_ORDER_PATH` 대체).

### 4.5 `KisBroker.__init__` 보강

```python
self._order_history: dict[str, KisOrderResponse] = {}
```

(기존 `self._last_order_response: KisOrderResponse | None = None` 유지.)

### 4.6 `KisBroker.place_order` 변경 (좁은)

- transport 호출에 `path=KIS_OVERSEAS_ORDER_PATH` 추가.
- 성공 시 `_order_history[odno] = response_record` 도 함께 갱신 (기존 `_last_order_response = response_record` 유지).
- 그 외 모든 동작 무변동.

### 4.7 `KisBroker.cancel_order(broker_order_id)` 본문

```python
def cancel_order(self, broker_order_id: str) -> None:
    _validate_paper_settings(self._settings)
    if self._settings.allow_market_orders:
        raise KisOrderRejectedError("market_orders_allowed_flag_set")
    if self._settings.kill_switch_engaged:
        raise KisOrderRejectedError("kill_switch_engaged")

    entry = self._order_history.get(broker_order_id)
    if entry is None:
        self._last_error = "unknown_broker_order_id"
        raise KisOrderRejectedError("unknown_broker_order_id")
    if entry.status not in ("submitted", "replacement_submitted"):
        self._last_error = "not_cancellable_state"
        raise KisOrderRejectedError("not_cancellable_state")

    if self._settings.kis_order_dry_run:
        self._last_order_preview = self._dry_run_cancel_preview(entry)
        return None

    if not self._auth.is_authenticated():
        self._last_error = "authentication_required"
        raise KisOrderRejectedError("authentication_required")
    access_token = self._auth.get_access_token()
    if not access_token:
        self._last_error = "authentication_required"
        raise KisOrderRejectedError("authentication_required")

    try:
        cano, acnt_prdt_cd = _split_kis_account_no(self._settings.kis_account_no or "")
    except KisConfigError:
        self._last_error = "invalid_kis_account_no_format"
        raise KisOrderRejectedError("invalid_kis_account_no_format")

    body = _build_paper_cancel_body(
        cano=cano,
        acnt_prdt_cd=acnt_prdt_cd,
        exchange=entry.exchange,
        symbol=entry.symbol,
        origin_odno=broker_order_id,
        original_qty=entry.quantity,
    )

    try:
        raw = self._order_transport.submit_order(
            base_url=self._settings.kis_base_url_paper,
            access_token=access_token,
            app_key=self._settings.kis_app_key or "",
            app_secret=self._settings.kis_app_secret or "",
            tr_id=KIS_PAPER_CANCEL_REPLACE_TR_ID_US,
            path=KIS_OVERSEAS_CANCEL_REPLACE_PATH,
            body=body,
        )
    except KisOrderRejectedError as exc:
        self._last_error = exc.reason
        raise

    sanitized = sanitize_kis_response(raw, self._settings)
    if "rt_cd" not in sanitized:
        self._last_error = "malformed_response"
        raise KisOrderRejectedError("malformed_response")
    if sanitized.get("rt_cd") != "0":
        code = sanitized.get("msg_cd") or sanitized.get("msg1") or "unknown"
        self._last_error = f"kis_error:{code}"
        raise KisOrderRejectedError(f"kis_error:{code}")

    self._order_history[broker_order_id] = dataclasses.replace(
        entry,
        status="cancelled",
        raw_response_sanitized=sanitized,
    )
    self._last_error = None
    return None
```

`_dry_run_cancel_preview(entry)` helper (신규):

```python
def _dry_run_cancel_preview(self, entry: KisOrderResponse) -> KisDryRunPreview:
    payload = {
        "operation": "cancel",
        "broker_order_id": entry.broker_order_id,
        "symbol": entry.symbol,
        "exchange": entry.exchange,
        "quantity": entry.quantity,
        "tr_id": KIS_PAPER_CANCEL_REPLACE_TR_ID_US,
        "path": KIS_OVERSEAS_CANCEL_REPLACE_PATH,
        "account_no": self._account.masked_account_no(),
    }
    request = KisOrderRequest(
        symbol=entry.symbol,
        market="US",
        side=entry.side,
        quantity=entry.quantity,
        order_type=OrderType.LIMIT,
        limit_price=entry.limit_price,
        extended_hours=False,
        account_no_masked=self._account.masked_account_no(),
        broker_environment=self._settings.kis_env or "paper",
        idempotency_key=f"kis-paper-cancel-{entry.broker_order_id}",
    )
    return KisDryRunPreview(
        request=request,
        payload_sanitized=sanitize_kis_response(payload, self._settings),
    )
```

### 4.8 `KisBroker.replace_order(broker_order_id, broker_order)` 본문

```python
def replace_order(self, broker_order_id: str, broker_order: BrokerOrder) -> OrderAck:
    validate_kis_order_request(self._settings, broker_order)

    entry = self._order_history.get(broker_order_id)
    if entry is None:
        self._last_error = "unknown_broker_order_id"
        raise KisOrderRejectedError("unknown_broker_order_id")
    if entry.status not in ("submitted", "replacement_submitted"):
        self._last_error = "not_replaceable_state"
        raise KisOrderRejectedError("not_replaceable_state")
    if broker_order.symbol != entry.symbol:
        self._last_error = "symbol_mismatch"
        raise KisOrderRejectedError("symbol_mismatch")
    if broker_order.side != entry.side:
        self._last_error = "side_mismatch"
        raise KisOrderRejectedError("side_mismatch")

    request = self._to_kis_request(broker_order)

    if self._settings.kis_order_dry_run:
        self._last_order_preview = self._dry_run_replace_preview(entry, request)
        return OrderAck(
            oms_id=broker_order.oms_id,
            broker_order_id=None,
            status="dry_run",
            mode=self.mode,
        )

    if not self._auth.is_authenticated():
        self._last_error = "authentication_required"
        raise KisOrderRejectedError("authentication_required")
    access_token = self._auth.get_access_token()
    if not access_token:
        self._last_error = "authentication_required"
        raise KisOrderRejectedError("authentication_required")

    try:
        cano, acnt_prdt_cd = _split_kis_account_no(self._settings.kis_account_no or "")
    except KisConfigError:
        self._last_error = "invalid_kis_account_no_format"
        raise KisOrderRejectedError("invalid_kis_account_no_format")

    body = _build_paper_replace_body(
        cano=cano,
        acnt_prdt_cd=acnt_prdt_cd,
        exchange=entry.exchange,
        symbol=entry.symbol,
        origin_odno=broker_order_id,
        new_qty=broker_order.quantity,
        new_limit_price=broker_order.limit_price,
    )

    try:
        raw = self._order_transport.submit_order(
            base_url=self._settings.kis_base_url_paper,
            access_token=access_token,
            app_key=self._settings.kis_app_key or "",
            app_secret=self._settings.kis_app_secret or "",
            tr_id=KIS_PAPER_CANCEL_REPLACE_TR_ID_US,
            path=KIS_OVERSEAS_CANCEL_REPLACE_PATH,
            body=body,
        )
    except KisOrderRejectedError as exc:
        self._last_error = exc.reason
        raise

    sanitized = sanitize_kis_response(raw, self._settings)
    if "rt_cd" not in sanitized:
        self._last_error = "malformed_response"
        raise KisOrderRejectedError("malformed_response")
    if sanitized.get("rt_cd") != "0":
        code = sanitized.get("msg_cd") or sanitized.get("msg1") or "unknown"
        self._last_error = f"kis_error:{code}"
        raise KisOrderRejectedError(f"kis_error:{code}")

    output_raw = sanitized.get("output")
    output = output_raw if isinstance(output_raw, dict) else {}
    new_odno_value = output.get("ODNO")
    new_odno = str(new_odno_value).strip() if new_odno_value is not None else ""
    if not new_odno:
        self._last_error = "malformed_response"
        raise KisOrderRejectedError("malformed_response")

    new_response = KisOrderResponse(
        internal_order_id=broker_order.oms_id,
        broker_order_id=new_odno,
        broker="KisBroker",
        status="replacement_submitted",
        submitted_at=datetime.now(timezone.utc),
        symbol=entry.symbol,
        side=entry.side,
        quantity=broker_order.quantity,
        limit_price=broker_order.limit_price,
        raw_response_sanitized=sanitized,
        exchange=entry.exchange,
        replaces_broker_order_id=broker_order_id,
    )
    self._order_history[broker_order_id] = dataclasses.replace(
        entry,
        status="replaced",
        replacement_broker_order_id=new_odno,
        raw_response_sanitized=sanitized,
    )
    self._order_history[new_odno] = new_response
    self._last_order_response = new_response
    self._last_error = None
    return OrderAck(
        oms_id=broker_order.oms_id,
        broker_order_id=new_odno,
        status="replacement_submitted",
        mode=self.mode,
    )
```

`_dry_run_replace_preview(entry, request)` helper 와 사용 패턴은 cancel 과 대응 (operation="replace", 새 quantity / limit_price 포함).

### 4.9 import 보강

`app/broker/kis.py` 파일 상단에 이미 `from dataclasses import dataclass` 가 있으나 `dataclasses.replace` 를 위해 `from dataclasses import dataclass, replace as dataclass_replace` 또는 `import dataclasses` 추가. 기존 코드와의 이름 충돌 없게 alias 사용 권고.

### 4.10 좁은 갱신 — 기존 테스트 3 개

- `tests/test_broker_interface.py::test_kis_place_cancel_replace_not_implemented`: lines 118-121 의 cancel/replace `NotImplementedError` 단언 → `KisOrderRejectedError, match="unknown_broker_order_id"`.
- `tests/test_broker_interface.py::test_kis_protocol_methods_delegate_to_not_implemented`: line 127-128 의 `broker.cancel("x")` `NotImplementedError` 단언 → `KisOrderRejectedError, match="unknown_broker_order_id"`.
- `tests/test_kis_http_boundaries.py::test_cancel_replace_queries_fail_closed`: lines 200-204 의 cancel/replace 단언만 `KisOrderRejectedError, match="unknown_broker_order_id"` 로 변경. `get_open_orders` / `get_fills` / `get_order_status` 의 `NotImplementedError` 단언 3 개 절대 유지.

## 5. 테스트 기준

신규 `tests/test_kis_paper_order_cancel_replace.py` 함수 (정확 이름):

**Body builders & 상수**:

1. `test_build_paper_cancel_body_contains_only_catalog_keys` — `{"CANO", "ACNT_PRDT_CD", "OVRS_EXCG_CD", "PDNO", "ORGN_ODNO", "RVSE_CNCL_DVSN_CD", "ORD_QTY", "OVRS_ORD_UNPR"}` 정확 set. `ORD_DVSN`, `SLL_TYPE`, `MGCO_APTM_ODNO`, `CTAC_TLNO` 등 등장 안 함.
2. `test_build_paper_cancel_body_sets_dvsn_02_and_unpr_zero_string` — RVSE_CNCL_DVSN_CD == "02", OVRS_ORD_UNPR == "0".
3. `test_build_paper_replace_body_contains_only_catalog_keys` — 동일 key set.
4. `test_build_paper_replace_body_sets_dvsn_01_and_new_qty_price` — RVSE_CNCL_DVSN_CD == "01", ORD_QTY == new qty, OVRS_ORD_UNPR == new price format.
5. `test_cancel_replace_constants_use_only_us_paper_tr_id` — `KIS_PAPER_CANCEL_REPLACE_TR_IDS == frozenset({"VTTT1004U"})`, `KIS_PAPER_CANCEL_REPLACE_TR_ID_US == "VTTT1004U"`, `KIS_OVERSEAS_CANCEL_REPLACE_PATH == "/uapi/overseas-stock/v1/trading/order-rvsecncl"`.

**cancel_order**:

6. `test_cancel_order_unknown_broker_order_id_fails_closed` — empty history → `KisOrderRejectedError("unknown_broker_order_id")`.
7. `test_cancel_order_dry_run_returns_none_without_http` — kis_order_dry_run=True, history 에 entry 1 개 시드 + `_RaiseOnCallOrderTransport` 또는 FakeOrderTransport 가 raise 하도록 설정 → cancel_order returns None, `_last_order_preview` populated, transport 미호출.
8. `test_cancel_order_dry_run_disabled_requires_authentication` — token 없음 → `KisOrderRejectedError("authentication_required")`.
9. `test_cancel_order_dry_run_disabled_blocked_by_live_trading` — `live_trading_enabled=True` → `KisOrderRejectedError("live_trading_enabled")` (또는 `_validate_paper_settings` 의 KisOrderRejectedError reason 일치).
10. `test_cancel_order_dry_run_disabled_blocked_by_kis_env_not_paper` — `kis_env="live"` 직접 KisBroker 생성 시 RuntimeError → KisAccountClient 와 같이 직접 KisBroker._validate_paper_settings 경로 검증. 또는 settings.kis_env="paper" 그대로 두고 다른 가드 검증.
11. `test_cancel_order_dry_run_disabled_blocked_by_kill_switch` — `kill_switch_engaged=True` → `KisOrderRejectedError("kill_switch_engaged")`.
12. `test_cancel_order_dry_run_disabled_blocked_by_allow_market_orders` — `allow_market_orders=True` → `KisOrderRejectedError("market_orders_allowed_flag_set")`.
13. `test_cancel_order_dry_run_disabled_mock_mode_fails_closed` — `kis_api_mode="mock"` (MockOrderTransport 자동 선택) → `KisOrderRejectedError("mock_mode_no_network")`.
14. `test_cancel_order_happy_path` — place_order 로 history 시드 → FakeOrderTransport 가 `{"rt_cd":"0", "output":{"ODNO":"...","ORD_TMD":"...","KRX_FWDG_ORD_ORGNO":"..."}}` 반환 → cancel_order returns None. history entry status == "cancelled". transport.calls[0]["tr_id"] == "VTTT1004U", `path` == "/uapi/.../order-rvsecncl". body == `_build_paper_cancel_body(...)`.
15. `test_cancel_order_kis_rejection_propagates` — FakeOrderTransport 가 rt_cd != "0" 반환 → `KisOrderRejectedError("kis_error:...")`.
16. `test_cancel_order_malformed_response_fails_closed` — rt_cd 누락 → `KisOrderRejectedError("malformed_response")`.
17. `test_cancel_order_already_cancelled_fails_closed` — cancel 성공 후 같은 broker_order_id 재호출 → `KisOrderRejectedError("not_cancellable_state")`.
18. `test_cancel_order_after_replace_targets_old_id_fails_closed` — replace 성공 후 old broker_order_id 의 status 가 "replaced" 이므로 cancel(old_id) → `KisOrderRejectedError("not_cancellable_state")`. new broker_order_id 로 cancel 은 정상.

**replace_order**:

19. `test_replace_order_unknown_broker_order_id_fails_closed` — empty history → `KisOrderRejectedError("unknown_broker_order_id")`.
20. `test_replace_order_runs_preflight_first` — invalid new BrokerOrder (e.g., quantity=0) → preflight 가 `KisOrderRejectedError("quantity_invalid")` 로 가장 먼저 거절. history 검색 도달 전.
21. `test_replace_order_blocked_by_live_trading` — `live_trading_enabled=True` + valid new order → preflight 에서 `KisOrderRejectedError("live_trading_enabled")`.
22. `test_replace_order_blocked_by_market_order_type` — `OrderType.MARKET` new order → preflight 에서 `KisOrderRejectedError("order_type_not_limit")`.
23. `test_replace_order_blocked_by_allow_market_orders` — `allow_market_orders=True` → preflight 에서 `KisOrderRejectedError("market_orders_allowed_flag_set")`.
24. `test_replace_order_symbol_mismatch_fails_closed` — history entry.symbol="AAPL", new BrokerOrder.symbol="MSFT" → `KisOrderRejectedError("symbol_mismatch")`. transport 미호출.
25. `test_replace_order_side_mismatch_fails_closed` — history entry.side=BUY, new BrokerOrder.side=SELL → `KisOrderRejectedError("side_mismatch")`.
26. `test_replace_order_dry_run_returns_dry_run_ack_without_http` — kis_order_dry_run=True + valid input + history seeded → ack.status == "dry_run", broker_order_id None, `_last_order_preview` populated, transport 미호출.
27. `test_replace_order_dry_run_disabled_requires_authentication` — no token → `KisOrderRejectedError("authentication_required")`.
28. `test_replace_order_dry_run_disabled_mock_mode_fails_closed` — `kis_api_mode="mock"` → `KisOrderRejectedError("mock_mode_no_network")`.
29. `test_replace_order_happy_path` — place_order (qty=10, price=100.50) 로 history 시드, FakeOrderTransport 가 `{"rt_cd":"0", "output":{"ODNO":"NEW_ODNO_999","ORD_TMD":"093015","KRX_FWDG_ORD_ORGNO":"12345"}}` 반환 → ack.status == "replacement_submitted", ack.broker_order_id == "NEW_ODNO_999". transport.calls[0]["tr_id"] == "VTTT1004U", body["RVSE_CNCL_DVSN_CD"] == "01", body["ORD_QTY"] == new qty str, body["OVRS_ORD_UNPR"] == new price formatted.
30. `test_replace_order_preserves_old_history_entry` — replace 성공 후 `broker._order_history[old_id]` 가 여전히 존재. status == "replaced". `replacement_broker_order_id` == new_odno. `replaces_broker_order_id` is None.
31. `test_replace_order_creates_new_history_entry` — replace 성공 후 `broker._order_history[new_odno]` 가 존재. status == "replacement_submitted". `replaces_broker_order_id` == old_id. `replacement_broker_order_id` is None. symbol/side/exchange 가 old entry 와 일치. quantity / limit_price 는 새 값.
32. `test_replace_order_does_not_overwrite_old_id` — replace 성공 후 `broker._order_history[old_id].broker_order_id` 여전히 old_id (자기 자신). new_odno 와 다름.
33. `test_replace_order_chained_replace_works` — replace 두 번 연속: id1 → id2 → id3. `broker._order_history` 에 세 entry 모두 존재. id1.status=="replaced" + replacement=id2. id2.status=="replaced" + replacement=id3 + replaces=id1. id3.status=="replacement_submitted" + replaces=id2.
34. `test_replace_order_kis_rejection_propagates`.
35. `test_replace_order_malformed_response_fails_closed_missing_rt_cd`.
36. `test_replace_order_malformed_response_fails_closed_missing_odno` — rt_cd=="0" 인데 output.ODNO 없음 → `KisOrderRejectedError("malformed_response")`.

**Transport allowlist (cancel/replace 전용)**:

37. `test_urllib_order_transport_rejects_live_cancel_tr_id` — `tr_id="TTTS" + "1003U"` (홍콩 실전 정정취소) → `KisOrderRejectedError("disallowed_tr_id")`. 본 테스트에서 forbidden 리터럴은 string concatenation 으로 작성.
38. `test_urllib_order_transport_rejects_path_tr_id_mismatch_order_to_rvsecncl` — `tr_id="VTTT1002U"` (place_order BUY) + `path="/uapi/overseas-stock/v1/trading/order-rvsecncl"` → `KisOrderRejectedError("path_tr_id_mismatch")`.
39. `test_urllib_order_transport_rejects_path_tr_id_mismatch_rvsecncl_to_order` — `tr_id="VTTT1004U"` + `path="/uapi/overseas-stock/v1/trading/order"` → `KisOrderRejectedError("path_tr_id_mismatch")`.
40. `test_urllib_order_transport_rejects_invalid_rvse_cncl_dvsn` — body 에 `RVSE_CNCL_DVSN_CD="03"` (또는 누락) → `KisOrderRejectedError("invalid_rvse_cncl_dvsn")`.
41. `test_urllib_order_transport_rejects_non_us_exchange_for_cancel` — body 에 `OVRS_EXCG_CD="SEHK"` (홍콩) → `KisOrderRejectedError("invalid_exchange")`. forbidden 리터럴은 `"SE" + "HK"` 등 concatenation 으로 작성하지 않아도 됨 (SEHK 는 grep target 이 아님 — Asia 거래소 코드는 catalog 행에서 정보 목적으로 등장).

**Asia 거래소 절대 차단 (G4)**:

42. `test_cancel_order_rejects_non_us_exchange_in_history` — history entry 의 exchange="SEHK" 등 paper US allowlist 외 값일 때 cancel 시도 → transport `invalid_exchange` 로 fail-closed. 실제로는 place_order 가 NASD/NYSE/AMEX 외 거래소를 만들지 않으므로 unit 테스트에서 직접 history 에 SEHK entry 를 주입해 검증.
43. `test_replace_order_rejects_non_us_exchange_in_history` — 동일.

**Module surface (grep 회귀)**:

44. `test_kis_module_does_not_introduce_live_cancel_replace_tr_ids` — `app/broker/kis.py` 의 file text 가 다음 string concatenation 으로 작성된 forbidden 값들 모두 미포함 — `"TTTT" + "1004U"`, `"TTTS" + "1003U"`, `"TTTS" + "0309U"`. (live 정정·취소 TR_ID 3 종.)
45. `test_kis_module_does_not_introduce_asia_paper_cancel_replace_tr_ids` — catalog §4.2 가 "그 외 아시아는 정정취소 sheet `tr_id` 셀 본문 참조" 라고만 명시했으므로, Asia paper 정정·취소 TR_ID 가 모듈에 추가되지 않았음을 회귀 보호. 단 구체 TR_ID 명이 catalog 행에 명시되지 않아 grep target 으로 만들 string 이 없음 — 이 테스트는 `KIS_PAPER_CANCEL_REPLACE_TR_IDS` set 의 크기가 정확히 1 임을 단언하는 것으로 대체.

**Capability surface 보존 (G2 선택 A 회귀)**:

46. `test_capabilities_unchanged_after_cancel_replace_implementation` — `broker.capabilities()` 가 `{"submission": False, "cancel": False, "replace": False, "open_orders": False, "fills": False, "order_status": False}` 그대로.
47. `test_healthcheck_order_execution_implemented_remains_false` — `broker.healthcheck()["order_execution_implemented"] is False`. `order_methods_fail_closed is True` 유지.

**Other 3 methods 미구현 유지 (BLOCKED-BY-DOCS)**:

48. `test_get_open_orders_still_not_implemented_after_cancel_replace` — `broker.get_open_orders()` 가 여전히 `NotImplementedError`.
49. `test_get_fills_still_not_implemented_after_cancel_replace` — `broker.get_fills()` 가 여전히 `NotImplementedError`.
50. `test_get_order_status_still_not_implemented_after_cancel_replace` — `broker.get_order_status("any-id")` 가 여전히 `NotImplementedError`.

**Secret leak 회귀**:

51. `test_cancel_replace_response_sanitization_redacts_secrets` — FakeOrderTransport 가 응답에 `{"appkey":"fake-key-XYZ", "access_token":"Bearer test-token", "rt_cd":"0", "output":{"ODNO":"NEW","appsecret":"fake-secret-XYZ"}}` 반환 → cancel/replace 성공 후 `broker._order_history[...]raw_response_sanitized` 의 `json.dumps(...)` 에 `"fake-key-XYZ"`, `"fake-secret-XYZ"`, `"Bearer test-token"` 모두 등장 안 함.
52. `test_cancel_replace_exceptions_and_repr_do_not_expose_secrets` — 모든 fail-closed 경로 (unknown_id / auth / mock / kis_error / malformed / preflight) 에서 `str(exc)`, `repr(broker)`, `repr(broker._order_history.values())` 에 `fake-key-XYZ`, `fake-secret-XYZ`, `12345678`, `fake-access-token`, `Bearer ` 등장 안 함.

**기존 테스트 좁은 갱신** (별도 함수가 아니라 narrow edit):

- `tests/test_broker_interface.py::test_kis_place_cancel_replace_not_implemented` — cancel/replace 단언 변경.
- `tests/test_broker_interface.py::test_kis_protocol_methods_delegate_to_not_implemented` — `broker.cancel("x")` 단언 변경.
- `tests/test_kis_http_boundaries.py::test_cancel_replace_queries_fail_closed` — cancel/replace 단언 변경. get_open_orders / get_fills / get_order_status 단언 절대 유지.

**기존 테스트 영향 없음 (재확인)**:

- `tests/test_kis_paper_order_submission.py` — 본 작업이 `place_order` 의 transport 호출에 `path=KIS_OVERSEAS_ORDER_PATH` 를 추가하지만, FakeOrderTransport.submit_order(**kwargs) 가 추가 kwarg 를 흡수하므로 회귀 0. 기존 단언 (transport.calls[0]["tr_id"] 등) 그대로 통과.
- `tests/test_paper_e2e_pipeline.py::test_e2e_kis_dry_run_returns_dry_run_ack_without_http` — `_RaiseOnCallOrderTransport.submit_order(**kwargs)` 도 추가 kwarg 흡수. 회귀 0.
- `tests/test_kis_order_response_model.py` — `KisOrderResponse` 새 필드 3 개 모두 default 보유. 기존 직접 생성 코드 (10 kwargs) 그대로 통과.
- `tests/test_kis_capabilities.py`, `tests/test_api_paper_status.py`, `tests/test_broker_interface.py::test_kis_healthcheck_returns_disconnected_dict`, `tests/test_broker_interface.py::test_kis_broker_capabilities_are_exported_and_fail_closed` — capabilities / healthcheck 동작 무변동.
- Strategy / OMS / RiskEngine / Portfolio / Runtime / Session 관련 테스트 — 무변동.

검증 명령:

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

전체 PASS 가 완료 조건.

안전 grep (Codex 가 patch.md 에 결과 첨부):

```bash
grep -rnE "^(from|import) (requests|httpx|aiohttp|urllib3)" app/broker tests
grep -rn "TTTT1002U\|TTTT1006U\|TTTT1004U\|TTTS1002U\|TTTS1001U\|TTTS0307U\|TTTS0308U\|TTTS0309U\|TTTS1003U\|TTTT3014U\|TTTT3016U\|TTTT3017U\|TTTS3013U" app tests
grep -rn "TTTS3018R\|TTTT3039R\|TTTS3014R\|TTTS6036U\|TTTS6037U\|TTTS6038U\|TTTS6058R\|TTTS6059R" app tests
grep -rn "openapi.koreainvestment.com:9443" app tests
grep -rn "ALLOW_MARKET_ORDERS=true\|allow_market_orders=True" app
grep -rn "Bearer eyJ" app tests docs/ai/jobs/api-orders-paper-002-cancel-replace || true
grep -rn "from app.broker.kis" app/strategy app/agent 2>/dev/null || true
```

기대 결과:
- 외부 HTTP 라이브러리: 0 lines.
- live / Asia paper 정정·취소 TR_ID: 0 lines.
- 모의 미지원 TR_ID: 0 lines.
- live base URL / `ALLOW_MARKET_ORDERS=true` literal: 기존 `app/config.py` 가드 라인만 (사전 존재).
- `Bearer eyJ`: 기존 testfile / job-instruction 텍스트만.
- Strategy / Agent KIS import: 0 lines.

## 6. 리뷰 체크리스트

안전 회귀:

- [ ] live trading 활성화 코드 / live broker API / 실주문 endpoint 추가 없음.
- [ ] 실전 정정·취소 base URL / 실전 TR_ID (`TTTT1004U` / `TTTS1003U` / `TTTS0309U` 등) 추가 없음.
- [ ] Asia paper 정정·취소 TR_ID 추가 없음. `KIS_PAPER_CANCEL_REPLACE_TR_IDS` set 크기 == 1.
- [ ] 모의 미지원 TR_ID 추가 없음.
- [ ] `OrderType.MARKET` 3중 가드 / `ALLOW_MARKET_ORDERS=true` reject / kill switch / `validate_kis_order_request` 변경 없음.
- [ ] `OrderType.STOP` 도입 없음.
- [ ] `app/broker/kis_http.py` 변경 없음.
- [ ] `UrllibOrderTransport` 가 host (1 개) + path (2 개 — order + order-rvsecncl) + method (POST 1 개) + TR_ID (3 개 — 2 place + 1 cancel/replace) + exchange (3 개) + 각 TR_ID 별 dvsn 검사 strict allowlist 강제. 실패 시 모두 short tag.
- [ ] 외부 HTTP 라이브러리 import 없음.
- [ ] secret / 계좌번호 / token / Bearer 원문 코드 / repr / exception / 로그 / pytest capture 노출 없음.
- [ ] `.env` / `.env.example` / `app/config.py` 수정 없음.
- [ ] Strategy / Agent / LLM 의 `app.broker.kis` 직접 import 없음.

스코프 / 동작:

- [ ] `KisOrderResponse` 에 `exchange="NASD"`, `replacement_broker_order_id=None`, `replaces_broker_order_id=None` default 필드만 추가 (G1, G3).
- [ ] G2 — KisBroker adapter level 만 구현. OMS / runtime / GUI 연결 없음.
- [ ] G3 — replace 후 old entry status="replaced" + replacement_broker_order_id 설정. new entry status="replacement_submitted" + replaces_broker_order_id 설정. old key 제거 안 됨.
- [ ] G4 — US 거래소 (`NASD` / `NYSE` / `AMEX`) 만 지원. Asia 거래소 history 가 들어와도 transport 가 `invalid_exchange` 로 차단.
- [ ] `cancel_order` 가 catalog §4.6 의 `RVSE_CNCL_DVSN_CD="02"` + `OVRS_ORD_UNPR="0"` 정책 준수.
- [ ] `replace_order` 가 catalog §4.6 의 `RVSE_CNCL_DVSN_CD="01"` + new ORD_QTY / OVRS_ORD_UNPR 정책 준수. 신규 ODNO 가 `output.ODNO` 에서 추출.
- [ ] dry-run 모드: cancel 은 None 반환 + `_last_order_preview` 설정 + transport 미호출. replace 는 `OrderAck(status="dry_run", broker_order_id=None)` + `_last_order_preview` 설정 + transport 미호출.
- [ ] `_order_history` lookup 실패 시 `KisOrderRejectedError("unknown_broker_order_id")`.
- [ ] cancel 후 같은 broker_order_id 재호출 시 `KisOrderRejectedError("not_cancellable_state")`.
- [ ] replace 시 symbol/side mismatch → fail-closed.
- [ ] response sanitize 가 항상 적용.
- [ ] `capabilities()` 모든 플래그 False 유지. `healthcheck()["order_execution_implemented"]` False 유지.
- [ ] `get_open_orders` / `get_fills` / `get_order_status` `NotImplementedError` 유지.

테스트 / 문서:

- [ ] `python -m compileall app tests` 통과.
- [ ] `python -m pytest -p no:cacheprovider` 전체 PASS.
- [ ] 신규 `tests/test_kis_paper_order_cancel_replace.py` 가 §5 의 50+ 회귀 모두 검증.
- [ ] 기존 3 개 narrow 갱신만 수행 (`test_broker_interface.py` 2 함수, `test_kis_http_boundaries.py` 1 함수). 다른 함수 무변동.
- [ ] `docs/ai/jobs/api-orders-paper-002-cancel-replace/patch.md` 에 수정 파일 / G1~G4 해결 방식 / 사용 endpoint·TR_ID 출처 / dry-run 동작 / 실 전송 조건 / fail-closed 범위 / secret 회귀 / safety 회귀 / 테스트 결과 / 안전 grep 결과 / Claude 검증 프롬프트 / follow-up Codex 프롬프트 규칙 모두 포함.

자동화 금지:

- [ ] commit / push / merge / PR / deploy 수행 없음.
- [ ] `.env` / secret / credential / API key / token 수정·노출 없음.
- [ ] `docs/kis/MISSING_OFFICIAL_VALUES.md` 변경 없음.
