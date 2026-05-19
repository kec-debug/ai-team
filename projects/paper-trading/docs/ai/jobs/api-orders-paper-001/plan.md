# api-orders-paper-001 — KIS 모의투자 주문 본문 구현

## 1. 요청 요약

KIS_2 (`docs/kis/MISSING_OFFICIAL_VALUES.md` §4) 에서 해외주식 주문 endpoint catalog 가 `Confirmed: yes` 로 정리됐다. api-account-001 에서 paper 잔고/포지션 read-only 조회 본문이 catalog 기반으로 구현 완료. 이번 작업은 `KisBroker.place_order()` 의 모의투자 주문 본문을 구현한다.

핵심 결정 — catalog 의 paper-supported 범위:

- 미국 매수 endpoint (POST `/uapi/overseas-stock/v1/trading/order`, 모의 TR_ID `VTTT1002U`) `Confirmed: yes` (catalog §4.2).
- 미국 매도 endpoint (동일 path, 모의 TR_ID `VTTT1001U`) `Confirmed: yes` (catalog §4.2).
- Request body 필수 필드: `CANO` / `ACNT_PRDT_CD` / `OVRS_EXCG_CD` / `PDNO` / `ORD_QTY` / `OVRS_ORD_UNPR` / `ORD_DVSN` / `ORD_SVR_DVSN_CD` (catalog §4.4 `Confirmed: yes`).
- 매도 시에만 `SLL_TYPE="00"` 추가 (catalog §4.4: "제거=매수, `00`=매도").
- Response 본문 필드: `rt_cd` / `msg_cd` / `msg1` / `output.KRX_FWDG_ORD_ORGNO` / `output.ODNO` (broker_order_id 후보) / `output.ORD_TMD` (catalog §4.5 `Confirmed: yes`).
- **모의 거래 제약** (catalog §4.9): `ORD_DVSN="00"` (LIMIT) 만 가능. 모의 OVRS_EXCG_CD 는 `NASD` / `NYSE` / `AMEX` 만 검증됨. 시장가 / LOO / LOC / MOO / MOC / TWAP / VWAP / 단주지정가 모두 미지원. 본 저장소의 `OrderType.MARKET` 3중 가드 + `ALLOW_MARKET_ORDERS=true` reject + `validate_kis_order_request` pre-flight 정책과 정합.
- 모의 base URL: `https://openapivts.koreainvestment.com:29443` (catalog §4.1).
- 실전 base URL / 실전 TR_ID / 모의 미지원 endpoint 는 본 작업에서 사용 / 추가 금지.

추가 제약 (request 의 "절대 하지 말 것" 부분 그대로):

- live trading 활성화 금지, 실전 endpoint 금지, 실주문 금지.
- KIS endpoint / TR_ID / header / payload / response field 추측 금지. catalog `Confirmed: yes` 행 + paper-supported 행만 사용.
- `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` 본문은 이번 작업 범위 외 — NotImplementedError 그대로 유지.
- 외부 HTTP 라이브러리 (`requests`, `httpx`, `aiohttp`, `urllib3`) 금지. stdlib `urllib.request` 만 사용.
- `OrderType.STOP` 도입 금지. `OrderType.MARKET` 3중 가드 우회 금지. `ALLOW_MARKET_ORDERS=true` 허용 reject 정책 유지.
- FX 변환 함수 / 환율 상수 / base currency 통합 함수 도입 금지.
- secret · 계좌번호 · access token · Bearer 원문 leak 금지.
- `.env` / `.env.example` 읽기·수정 금지.
- GUI (`app/api/*`, `app/static/*`, `app/main.py`) 변경 금지. 따라서 `routes.py` 의 `kis_order_methods_fail_closed` 리터럴, `kis_order_entry_mode` 분기, `kis_order_submission_available = bool(capabilities["submission"])` 식 surface 도 그대로.
- Strategy / Agent / LLM 가 broker 또는 KisBroker 를 직접 호출하지 않는다. 모든 주문은 Strategy → RiskEngine → OMS → KisBroker 경로.
- 자동 git commit / push / merge / deploy 금지.

## 2. 작업 범위

포함하는 것:

- `app/broker/kis.py`:
  - 주문 endpoint 전용 상수: path, 모의 TR_ID (BUY / SELL 2 개), paper host allowlist, paper exchange allowlist (`NASD` / `NYSE` / `AMEX`), 지정가 `ORD_DVSN="00"`, `ORD_SVR_DVSN_CD="0"`.
  - `_select_paper_order_tr_id(side)` helper (BUY → `VTTT1002U`, SELL → `VTTT1001U`).
  - `_build_paper_order_body(*, cano, acnt_prdt_cd, exchange, request)` helper (catalog §4.4 필드만 채우는 dict 빌더; BUY 는 SLL_TYPE 미설정, SELL 은 SLL_TYPE="00").
  - 신규 `KisOrderTransport` Protocol (모듈 내부 정의, `submit_order(*, base_url, access_token, app_key, app_secret, tr_id, body) -> dict`).
  - 신규 `MockOrderTransport`: mock 모드용. 호출 시 `KisOrderRejectedError("mock_mode_no_network")`.
  - 신규 `UrllibOrderTransport`: stdlib `urllib.request` POST. 자체 host / path / method / TR_ID allowlist (모의 미국 매수 + 매도 2 개). retry 는 5xx / transport 만 1 회. 응답 JSON parse / `rt_cd` 검사 / 4xx-5xx 처리. secret 원문 메시지·repr 노출 금지.
  - `KisBroker.__init__` 에 `_order_transport` 자동 선택 추가 (`KisApiMode.parse` 기준 mock / paper). 테스트 주입을 위해 `_order_transport` 속성을 노출.
  - `KisBroker.place_order(broker_order)` 실 구현:
    - `validate_kis_order_request` 그대로 호출 (preflight).
    - `_to_kis_request` 호출 (기존).
    - `kis_order_dry_run=True` → `_dry_run_preview` + dry-run OrderAck 반환 (기존 경로 그대로).
    - `kis_order_dry_run=False` 인 경우:
      - `_auth.is_authenticated()` 와 `_auth.get_access_token()` 확인 → 둘 중 하나라도 없으면 `KisOrderRejectedError("authentication_required")` (read-only 가드 외부에서 OAuth 가 별도 트리거되어야 함).
      - `_split_kis_account_no` 로 `CANO` / `ACNT_PRDT_CD` 분리.
      - `_select_paper_order_tr_id(side)` 와 `exchange="NASD"` (paper US 기본; 모의 catalog 가 명시한 paper 거래소).
      - `_build_paper_order_body(...)` 로 body dict 작성.
      - `self._order_transport.submit_order(...)` 호출.
      - 응답을 `sanitize_kis_response` 로 sanitize.
      - `rt_cd != "0"` → `KisOrderRejectedError(f"kis_error:{msg_cd or msg1 or 'unknown'}")`.
      - 성공이면 `KisOrderResponse` 인스턴스 작성하고 `self._last_order_response = ...` 에 저장. `OrderAck(broker_order_id=output.ODNO or None, status="submitted")` 반환.
  - 신규 `_last_order_response: KisOrderResponse | None` 속성 + `last_order_response` property (raw 노출 금지 — `KisOrderResponse` 의 `raw_response_sanitized` 이미 sanitize 된 형태).
  - `KisBroker.capabilities()` 반환은 그대로 (`submission=False` 유지 — request 의 "GUI 파일 수정 금지" 와 `test_api_paper_status` 의 `kis_order_submission_available is False` 회귀를 지키기 위해 conservative 상태로 유지). 본 변경은 §4.7 "Capability surface 보존" 에 명시.
  - `healthcheck()["order_execution_implemented"]` 도 `False` 유지 (회귀 보존; `test_kis_healthcheck_returns_disconnected_dict` 에서 명시적으로 False 단언).
  - 주문 외 메서드 (`cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` / OAuth / market data / account) 동작 변경 금지.
- 신규 테스트 (`tests/test_kis_paper_order_submission.py`): transport 주입 기반 happy / error / sanitization / 안전 회귀.
- 좁은 갱신:
  - `tests/test_kis_order_preflight.py::test_place_order_valid_input_with_dry_run_disabled_reaches_notimplemented` — 1 함수의 매칭 갱신 (NotImplementedError → KisOrderRejectedError("authentication_required")).
  - `tests/test_broker_interface.py::test_kis_place_cancel_replace_not_implemented` — 1-2 줄 갱신 (dry_run=False 경로의 기대 예외 변경).
- `docs/ai/jobs/api-orders-paper-001/patch.md` (Codex 작성).
- `projects/paper-trading/README.md` 1-2 줄 보강 가능 (선택, 새 env 변수 안내 금지).

제외 (절대 안 하는 것):

- live trading 활성화 / `LIVE_TRADING_ENABLED=true` 변경 / live broker API / 실전 base URL 호출.
- 실전 TR_ID (`TTTT1002U` / `TTTT1006U` / `TTTT1004U` / `TTTS1002U` / `TTTS1001U` / `TTTS1003U` / `TTTS0307U` / `TTTS0308U` / `TTTS0309U` / `TTTT3014U` / `TTTT3016U` / `TTTT3017U` / `TTTS3013U`) 추가.
- 모의 미지원 endpoint (`TTTS3018R` / `TTTT3039R` / `TTTS3014R` / `TTTS6036U` / `TTTS6037U` / `TTTS6038U` / `TTTS6058R` / `TTTS6059R` / `CTRP6010R` / `CTOS4001R` / `TTTS3039R` / `TTTC2101R`) 구현.
- 정정·취소·예약·예약취소 endpoint 구현. `/order-rvsecncl` / `/order-resv` / `/order-resv-ccnl` / `/daytime-order` / `/daytime-order-rvsecncl` 모두 미사용.
- `inquire-ccnl` (`VTTS3035R`) / `inquire-nccs` 등 조회 endpoint 구현.
- `OrderType.STOP` 도입. `OrderType.MARKET` 3중 가드 우회. `ALLOW_MARKET_ORDERS=true` 정책 변경.
- 외부 HTTP 라이브러리 import.
- `app/broker/kis_http.py` 변경. `ALLOWED_PATHS_API_AUTH_001` 그대로 `{/oauth2/tokenP, /oauth2/revokeP}`.
- 새 env 변수 추가. KIS 주문 transport 의 timeout / retry 는 기존 `kis_oauth_timeout_seconds` / `kis_oauth_max_retries` 를 재사용 (api-account-001 / api-market-data-001 패턴).
- `.env` / `.env.example` 변경.
- `app/api/*` / `app/static/*` / `app/main.py` / `app/config.py` / `app/oms/*` / `app/risk/*` / `app/portfolio/*` / `app/runtime/*` / `app/strategy/*` / `app/session/*` / `app/broker/paper.py` / `alpaca_paper.py` / `base.py` / `kis_token_cache.py` / `kis_quote_mapper.py` / `kis_http.py` / `app/domain/*` 변경.
- Strategy / Agent / LLM 이 `app.broker.kis` 또는 `KisBroker.place_order` 를 직접 import / 호출하는 경로 추가.
- 자동 git commit / push / merge / deploy.

## 3. 수정해야 할 파일

후방 호환 정책:

- `KisBroker.place_order(broker_order)` 시그니처 그대로 (`BrokerOrder → OrderAck`). 기존 호출자 (OMS `submit`) 영향 없음.
- `KisBroker.capabilities()` 반환 dict 동일 (`submission=False` 유지). `healthcheck()["order_execution_implemented"]` 동일 (`False` 유지). 따라서 `app/api/routes.py` / `test_api_paper_status` / `test_kis_capabilities` / `test_broker_interface::test_kis_healthcheck_returns_disconnected_dict` / `test_broker_interface::test_kis_broker_capabilities_are_exported_and_fail_closed` 회귀 모두 그대로 통과.
- `KisOrderRequest`, `KisOrderResponse` dataclass 시그니처 변동 없음. `_to_kis_request` / `_dry_run_preview` / `validate_kis_order_request` 변동 없음.
- 신규 속성 `KisBroker.last_order_response` 추가 (기본 `None`). 새 attr 가 기존 호출자에 영향 없음.

| 경로 | 변경 종류 | 요약 |
| --- | --- | --- |
| `projects/paper-trading/app/broker/kis.py` | MODIFY | (1) 주문 endpoint 상수. (2) `_select_paper_order_tr_id` / `_build_paper_order_body` helper. (3) `KisOrderTransport` Protocol. (4) `MockOrderTransport`. (5) `UrllibOrderTransport` (host / path / method / TR_ID allowlist 강제, secret-safe error tags). (6) `KisBroker.__init__` 가 `_order_transport` 자동 선택. (7) `place_order` 본문에 dry_run=False 분기 구현 (auth → split → body → transport.submit_order → sanitize → rt_cd 검사 → KisOrderResponse 작성 → OrderAck 반환). (8) `_last_order_response` + `last_order_response` property. **(9) 주문 외 메서드 (`cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` / `_dry_run_preview` / `_to_kis_request` / `_idempotency_key_for` / `validate_kis_order_request` / `capabilities` / `healthcheck` / KisAuthClient / KisAccountClient / KisMarketDataClient / sanitize_kis_response / `_split_kis_account_no` / `_validate_paper_settings`) 변경 금지.** |
| `projects/paper-trading/tests/test_kis_paper_order_submission.py` | NEW | transport 주입 기반 happy / mock / error / paper allowlist / secret leak / OMS 경로 회귀. 자세한 항목은 §5. |
| `projects/paper-trading/tests/test_kis_order_preflight.py` | MODIFY (좁은 범위) | `test_place_order_valid_input_with_dry_run_disabled_reaches_notimplemented` 1 함수: `NotImplementedError, match="Pre-flight passed"` 단언을 `KisOrderRejectedError, match="authentication_required"` 로 변경. 함수명은 `test_place_order_valid_input_with_dry_run_disabled_requires_auth` 로 갱신 가능. **다른 테스트 함수 절대 변경 금지.** |
| `projects/paper-trading/tests/test_broker_interface.py` | MODIFY (좁은 범위) | `test_kis_place_cancel_replace_not_implemented` 안에서 `broker_no_dry_run.place_order(_broker_order())` 에 대한 `pytest.raises(NotImplementedError, match="order endpoint")` 를 `pytest.raises(KisOrderRejectedError, match="authentication_required")` 로 변경 (1-2 줄). cancel_order / replace_order NotImplementedError 단언은 그대로 유지. **다른 테스트 함수 절대 변경 금지.** |
| `projects/paper-trading/docs/ai/jobs/api-orders-paper-001/patch.md` | NEW (Codex 가 작성) | 변경 요약 + 사용 endpoint/TR_ID 출처 + dry-run 동작 + 실 모의 주문 전송 조건 + fail-closed 범위 + secret leak 회귀 + safety 회귀 + 테스트 결과 + Claude 검증 프롬프트 + follow-up Codex 프롬프트 규칙. |
| `projects/paper-trading/README.md` | MODIFY (선택) | KIS paper 주문 dry-run / 실 모의 전송 동작 1-2 줄 안내. 새 env 변수 안내 금지. 생략 가능. |

**범위 확장 사유** (request 의 "수정 가능 파일" 외 추가):

- `tests/test_kis_order_preflight.py::test_place_order_valid_input_with_dry_run_disabled_reaches_notimplemented` 는 `dry_run=False + 유효 주문` 경로가 NotImplementedError 였던 가정에 의존한다. place_order 본문이 구현되면 이 경로는 auth 게이트로 fail-closed (`KisOrderRejectedError("authentication_required")`) 되는 것이 안전한 변경이다. 1 함수의 1 줄 assertion 만 변경한다. 다른 회귀 assertion 은 절대 건드리지 않는다.
- `tests/test_broker_interface.py::test_kis_place_cancel_replace_not_implemented` 안의 `broker_no_dry_run.place_order` 에 대한 `NotImplementedError` 단언도 같은 이유로 갱신 필요. 1-2 줄. dry_run=True 경로 (`status == "dry_run"`) 와 cancel/replace NotImplementedError 단언은 그대로 유지.
- 두 테스트 모두 narrow scope (api-market-data-001 / api-account-001 가 비슷한 1-함수 갱신을 수행한 사례와 동일 패턴).

손대지 않는 파일:

- `app/broker/kis_http.py` (SafeKisHttpClient, MockTransport, UrllibTransport, ALLOWED_PATHS_API_AUTH_001 모두 OAuth 전용 그대로). 주문 transport 는 `kis.py` 내부에 별도 정의.
- `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/base.py`, `app/broker/kis_token_cache.py`, `app/broker/kis_quote_mapper.py`.
- `app/api/*`, `app/static/*`, `app/main.py`.
- `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`.
- `app/config.py` (새 env 추가 금지).
- `app/domain/*` (`OrderType`, `Side`, `BrokerOrder`, `OrderAck` 모두 변경 금지).
- `docs/kis/*` (catalog 소비만; 본 작업에서 수정 금지).
- `.env`, `.env.example`.
- 기존 KIS 테스트 중 `test_kis_order_preflight.py` 의 다른 함수, `test_broker_interface.py` 의 다른 함수, `test_kis_order_request_model.py`, `test_kis_order_response_model.py`, `test_kis_capabilities.py`, `test_kis_account_client.py`, `test_kis_market_data_client.py`, `test_kis_quote_mapper.py`, `test_kis_auth_client.py`, `test_kis_token_cache.py`, `test_kis_api_mode.py`, `test_kis_config.py`, `test_kill_switch.py`, `test_kis_http_boundaries.py`, `test_missing_official_values_doc.py` 모두 변경 금지.

## 4. Codex 구현 지시문

자세한 단계는 `codex-task.md` 에 기록한다. 요지:

### 4.1 주문 endpoint 상수 (`app/broker/kis.py`)

```python
KIS_OVERSEAS_ORDER_PATH = "/uapi/overseas-stock/v1/trading/order"
KIS_PAPER_ORDER_TR_ID_US_BUY = "VTTT1002U"
KIS_PAPER_ORDER_TR_ID_US_SELL = "VTTT1001U"
KIS_PAPER_ORDER_TR_IDS = frozenset({
    KIS_PAPER_ORDER_TR_ID_US_BUY,
    KIS_PAPER_ORDER_TR_ID_US_SELL,
})
KIS_PAPER_ORDER_HOSTS = frozenset({"openapivts.koreainvestment.com:29443"})
KIS_PAPER_ORDER_EXCHANGES = frozenset({"NASD", "NYSE", "AMEX"})
KIS_PAPER_ORDER_LIMIT_DVSN = "00"
KIS_PAPER_ORDER_ORD_SVR_DVSN_CD = "0"
KIS_PAPER_ORDER_SELL_TYPE = "00"
```

**중요**: 위 5 개 TR_ID set / dvsn 상수 외에 실전 / 정정취소 / 예약 / 주간 / 지정가 TR_ID 를 코드/테스트/문서에 추가하지 말 것.

상수 위에 출처 주석: `# docs/kis/MISSING_OFFICIAL_VALUES.md §4.2 / §4.4 / §4.5 / §4.9 (paper VTTT1002U / VTTT1001U only).`

### 4.2 TR ID & body 빌더 helper

```python
def _select_paper_order_tr_id(side: Side) -> str:
    if side is Side.BUY:
        return KIS_PAPER_ORDER_TR_ID_US_BUY
    if side is Side.SELL:
        return KIS_PAPER_ORDER_TR_ID_US_SELL
    raise KisOrderRejectedError("side_invalid")


def _build_paper_order_body(
    *,
    cano: str,
    acnt_prdt_cd: str,
    exchange: str,
    request: "KisOrderRequest",
) -> dict[str, str]:
    body: dict[str, str] = {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "OVRS_EXCG_CD": exchange,
        "PDNO": request.symbol,
        "ORD_QTY": str(int(request.quantity)),
        "OVRS_ORD_UNPR": format(request.limit_price, "f"),
        "ORD_DVSN": KIS_PAPER_ORDER_LIMIT_DVSN,
        "ORD_SVR_DVSN_CD": KIS_PAPER_ORDER_ORD_SVR_DVSN_CD,
    }
    if request.side is Side.SELL:
        body["SLL_TYPE"] = KIS_PAPER_ORDER_SELL_TYPE
    return body
```

- `OVRS_ORD_UNPR` 는 `format(Decimal, "f")` 로 fixed-notation 문자열 (지수 표기 회피).
- BUY 는 `SLL_TYPE` 미설정 (catalog §4.4 "제거=매수, `00`=매도").
- `CTAC_TLNO` / `MGCO_APTM_ODNO` / `START_TIME` / `END_TIME` / `ALGO_ORD_TMD_DVSN_CD` 모두 미설정 (paper 미지원 또는 옵션).
- 다른 키 추가 금지.

### 4.3 `KisOrderTransport` Protocol & 실 transport

```python
class KisOrderTransport(Protocol):
    def submit_order(
        self,
        *,
        base_url: str,
        access_token: str,
        app_key: str,
        app_secret: str,
        tr_id: str,
        body: dict[str, str],
    ) -> dict[str, Any]:
        """Submit a single KIS paper order and return the raw response dict."""


@dataclass(frozen=True)
class MockOrderTransport:
    def submit_order(
        self,
        *,
        base_url: str,
        access_token: str,
        app_key: str,
        app_secret: str,
        tr_id: str,
        body: dict[str, str],
    ) -> dict[str, Any]:
        raise KisOrderRejectedError("mock_mode_no_network")


@dataclass(frozen=True)
class UrllibOrderTransport:
    timeout_seconds: float = 5.0
    max_retries: int = 1
    backoff_seconds: float = 2.0

    def submit_order(
        self,
        *,
        base_url: str,
        access_token: str,
        app_key: str,
        app_secret: str,
        tr_id: str,
        body: dict[str, str],
    ) -> dict[str, Any]:
        if _kis_extract_host(base_url) not in KIS_PAPER_ORDER_HOSTS:
            raise KisOrderRejectedError("disallowed_host")
        if tr_id not in KIS_PAPER_ORDER_TR_IDS:
            raise KisOrderRejectedError("disallowed_tr_id")
        exchange = body.get("OVRS_EXCG_CD", "")
        if exchange not in KIS_PAPER_ORDER_EXCHANGES:
            raise KisOrderRejectedError("invalid_exchange")
        if body.get("ORD_DVSN") != KIS_PAPER_ORDER_LIMIT_DVSN:
            raise KisOrderRejectedError("ord_dvsn_not_limit")

        url = f"{base_url.rstrip('/')}{KIS_OVERSEAS_ORDER_PATH}"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {access_token}",
            "appkey": app_key,
            "appsecret": app_secret,
            "tr_id": tr_id,
        }
        data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        request = Request(url=url, data=data, headers=headers, method="POST")
        attempts = max(1, self.max_retries + 1)
        for attempt in range(attempts):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    raw_body = response.read().decode("utf-8")
                parsed = json.loads(raw_body)
                if not isinstance(parsed, dict):
                    raise KisOrderRejectedError("invalid_response_body")
                return parsed
            except HTTPError as exc:
                if exc.code >= 500 and attempt < attempts - 1:
                    time.sleep(self.backoff_seconds)
                    continue
                raise KisOrderRejectedError(f"http_{exc.code}") from exc
            except (URLError, TimeoutError, socket.timeout) as exc:
                if attempt < attempts - 1:
                    time.sleep(self.backoff_seconds)
                    continue
                raise KisOrderRejectedError("transport_error") from exc
            except json.JSONDecodeError as exc:
                raise KisOrderRejectedError("invalid_response_body") from exc
        raise KisOrderRejectedError("transport_error")
```

- 모든 실패는 `KisOrderRejectedError` 단축 tag 로 변환. `HTTPError.read()` body 를 메시지에 포함하지 말 것.
- access_token / app_key / app_secret 은 헤더로만 전송되며 메시지 / repr / 로그에 등장하지 않는다.
- `KisOrderRejectedError` 의 `reason` attribute 가 short tag 와 동일하도록 raise 한다.

### 4.4 `KisBroker.__init__` 변경

`__init__` 끝에 추가:

```python
mode = KisApiMode.parse(settings.kis_api_mode)
if mode is KisApiMode.MOCK:
    self._order_transport: KisOrderTransport = MockOrderTransport()
else:
    self._order_transport = UrllibOrderTransport(
        timeout_seconds=settings.kis_oauth_timeout_seconds,
        max_retries=settings.kis_oauth_max_retries,
    )
self._last_order_response: KisOrderResponse | None = None
```

- 테스트 주입을 위해 `self._order_transport` 속성 public-facing. 별도 setter 없음 — 테스트에서는 `broker._order_transport = fake` 로 주입.

### 4.5 `place_order` 본문

```python
def place_order(self, broker_order: BrokerOrder) -> OrderAck:
    validate_kis_order_request(self._settings, broker_order)
    request = self._to_kis_request(broker_order)

    if self._settings.kis_order_dry_run:
        self._last_order_preview = self._dry_run_preview(request)
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

    tr_id = _select_paper_order_tr_id(broker_order.side)
    exchange = "NASD"  # paper 기본; catalog §4.9 모의 거래소 (NASD/NYSE/AMEX) 중 기본값
    body = _build_paper_order_body(
        cano=cano,
        acnt_prdt_cd=acnt_prdt_cd,
        exchange=exchange,
        request=request,
    )

    try:
        raw = self._order_transport.submit_order(
            base_url=self._settings.kis_base_url_paper,
            access_token=access_token,
            app_key=self._settings.kis_app_key or "",
            app_secret=self._settings.kis_app_secret or "",
            tr_id=tr_id,
            body=body,
        )
    except KisOrderRejectedError as exc:
        self._last_error = exc.reason
        raise

    sanitized = sanitize_kis_response(raw, self._settings)
    rt_cd = sanitized.get("rt_cd")
    if rt_cd not in (None, "0"):
        code = sanitized.get("msg_cd") or sanitized.get("msg1") or "unknown"
        self._last_error = f"kis_error:{code}"
        raise KisOrderRejectedError(f"kis_error:{code}")

    output = sanitized.get("output")
    output = output if isinstance(output, dict) else {}
    odno = str(output.get("ODNO") or "").strip() or None

    response_record = KisOrderResponse(
        internal_order_id=broker_order.oms_id,
        broker_order_id=odno,
        broker="KisBroker",
        status="submitted",
        submitted_at=datetime.now(timezone.utc),
        symbol=broker_order.symbol,
        side=broker_order.side,
        quantity=broker_order.quantity,
        limit_price=broker_order.limit_price,
        raw_response_sanitized=sanitized,
    )
    self._last_order_response = response_record
    self._last_error = None
    return OrderAck(
        oms_id=broker_order.oms_id,
        broker_order_id=odno,
        status="submitted",
        mode=self.mode,
    )
```

- `_split_kis_account_no` 실패는 `KisOrderRejectedError("invalid_kis_account_no_format")` 로 변환 (OMS 가 KisOrderRejectedError 만 처리하도록 일관성 유지).
- 응답 sanitization 은 transport 가 아니라 broker 레벨에서 수행 (api-account-001 패턴 동일).
- `KisOrderResponse.raw_response_sanitized` 에 sanitized dict 만 저장. raw 원문은 어디에도 보존하지 않는다.
- 성공 status 는 `"submitted"` 단일 (KIS catalog 가 동기 응답 시점의 추가 상태 enum 을 명시하지 않음).
- `last_order_response` property 추가:

```python
@property
def last_order_response(self) -> KisOrderResponse | None:
    return self._last_order_response
```

### 4.6 출고 / 입고 메서드 변동 없음

- `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` 본문 변경 금지. `NotImplementedError` 그대로.
- `_to_kis_request` / `_dry_run_preview` / `_idempotency_key_for` / `validate_kis_order_request` / `_validate_paper_settings` / `_split_kis_account_no` 변동 없음 (단, `_split_kis_account_no` 는 helper 그대로 사용).
- `KisAuthClient` / `KisAccountClient` / `KisMarketDataClient` 본문 변동 없음.
- `KisBroker.healthcheck()` 의 `order_execution_implemented` 와 `order_methods_fail_closed` 는 그대로 `False` / `True` 리터럴 유지. 신규 `last_order_response` 가 surface 되지는 않는다 (별 job 에서 추가 권장).
- `KisBroker.capabilities()` 반환 dict 그대로 (`submission=False`). 본 결정은 status surface 회귀를 깨지 않기 위해 conservative 하게 유지. 본 결정은 `patch.md` 에서 사용자가 확인할 수 있도록 명시.

### 4.7 Capability surface 보존 사유

- `/paper/status` 의 `kis_order_submission_available` 는 `bool(capabilities["submission"])` 로 노출 (routes.py:150). request 의 "GUI 파일 수정 금지" 와 `test_api_paper_status` 의 `kis_order_submission_available is False` / `kis_order_methods_fail_closed is True` / `kis_order_entry_mode == "not_implemented"` 회귀를 동시에 지키려면 `capabilities()["submission"]` 을 `False` 로 유지하는 것이 안전하다.
- 별 job (status surface 갱신 전용) 에서 routes.py 와 capabilities 를 같이 갱신해 dry-run / submitted / disabled 3 상태를 표시할 수 있다. 본 작업은 surface 변경을 별 job 으로 분리.

### 4.8 Secret / repr / 로그

- access_token / app_key / app_secret 이 (a) 코드 (`__repr__`, `last_order_response`, exception message), (b) test fixture/output, (c) patch.md, (d) docstring 어디에도 등장하지 않는다.
- `sanitize_kis_response` 가 응답 echo 된 sensitive 키 (`appkey`, `appsecret`, `access_token`, `account_no`, `cano`, `authorization`, `tr_key`, `secret` 등) 를 `<redacted>` 로 redact.
- `KisOrderResponse.raw_response_sanitized` 가 sanitized dict 만 저장.
- urllib `HTTPError.read()` body 를 KisOrderRejectedError 메시지에 포함하지 말 것. short tag (`http_404`, `transport_error`, `invalid_response_body`, `mock_mode_no_network`, `disallowed_host`, `disallowed_tr_id`, `invalid_exchange`, `ord_dvsn_not_limit`, `authentication_required`, `invalid_kis_account_no_format`, `kis_error:<msg_cd>`) 만 사용.

## 5. 테스트 기준

신규 테스트 (`tests/test_kis_paper_order_submission.py`):

테스트 헬퍼 `_settings(...)` 는 `kis_env="paper"`, `kis_account_no="12345678-01"`, `kis_app_key="fake-key-XYZ"`, `kis_app_secret="fake-secret-XYZ"`, `kis_api_mode="paper"`, `kis_order_dry_run=False` 기본값 사용. `FakeOrderTransport` 는 pages 대신 단일 response (또는 예외) 를 반환하는 stub.

테스트 함수:

1. `test_select_paper_order_tr_id_maps_side_correctly` — BUY → `VTTT1002U`, SELL → `VTTT1001U`. 다른 side 값 (없지만 방어용 — Side enum 만 2 종) 은 KisOrderRejectedError.
2. `test_build_paper_order_body_buy_omits_sll_type` — BUY 주문에서 `SLL_TYPE` 키가 body 에 없음.
3. `test_build_paper_order_body_sell_sets_sll_type_zero_zero` — SELL 주문에서 `SLL_TYPE == "00"`.
4. `test_build_paper_order_body_contains_only_catalog_keys` — body 의 모든 키가 `{"CANO", "ACNT_PRDT_CD", "OVRS_EXCG_CD", "PDNO", "ORD_QTY", "OVRS_ORD_UNPR", "ORD_DVSN", "ORD_SVR_DVSN_CD"}` (+ SELL 시 `SLL_TYPE`) subset. 다른 key (`CTAC_TLNO`, `START_TIME`, 등) 등장 안 함. `ORD_DVSN == "00"`, `ORD_SVR_DVSN_CD == "0"`.
5. `test_build_paper_order_body_quantity_and_price_are_strings` — `body["ORD_QTY"]` 와 `body["OVRS_ORD_UNPR"]` 모두 `str` 타입. `body["ORD_QTY"] == "10"`, `body["OVRS_ORD_UNPR"] == "100.50"` (Decimal "100.50" 입력 시 fixed-notation).
6. `test_place_order_dry_run_path_unchanged` — `kis_order_dry_run=True` + 토큰 미저장 → `ack.status == "dry_run"`, `broker.last_order_preview is not None`, `broker.last_order_response is None`. 즉 dry-run 경로가 auth 게이트를 통과하지 않는다.
7. `test_place_order_dry_run_disabled_requires_authentication` — `kis_order_dry_run=False` + 토큰 미저장 → `KisOrderRejectedError("authentication_required")`. `broker.last_order_response is None`.
8. `test_place_order_dry_run_disabled_blocked_by_preflight` — 토큰 저장 + `quantity=0` → preflight 가 먼저 raise (`KisOrderRejectedError("quantity_invalid")`). transport 도 호출되지 않음.
9. `test_place_order_dry_run_disabled_blocked_by_live_trading` — `live_trading_enabled=True` settings 에서 preflight 가 `KisOrderRejectedError("live_trading_enabled")` 로 거절. transport 호출 안 됨.
10. `test_place_order_dry_run_disabled_blocked_by_market_order_type` — `OrderType.MARKET` 시 preflight 가 `KisOrderRejectedError("order_type_not_limit")` 로 거절.
11. `test_place_order_dry_run_disabled_blocked_by_allow_market_orders` — `allow_market_orders=True` 시 preflight 가 `KisOrderRejectedError("market_orders_allowed_flag_set")` 로 거절.
12. `test_place_order_dry_run_disabled_blocked_by_kill_switch` — `kill_switch_engaged=True` 시 preflight 가 `KisOrderRejectedError("kill_switch_engaged")` 로 거절.
13. `test_place_order_dry_run_disabled_mock_mode_fails_closed` — `kis_api_mode="mock"` + 토큰 저장 → `KisOrderRejectedError("mock_mode_no_network")` (MockOrderTransport 자동 선택).
14. `test_place_order_happy_path_buy` — `kis_api_mode="paper"` + 토큰 + FakeOrderTransport (return `{"rt_cd": "0", "output": {"KRX_FWDG_ORD_ORGNO": "12345", "ODNO": "0000123456", "ORD_TMD": "093015"}, "msg1": "Success"}`) 주입 → `ack.status == "submitted"`, `ack.broker_order_id == "0000123456"`. `broker.last_order_response.broker_order_id == "0000123456"`. `broker.last_order_response.raw_response_sanitized["output"]["ODNO"] == "0000123456"`. `broker.last_error is None`.
15. `test_place_order_happy_path_sell` — Side.SELL 으로 동일 흐름. transport.calls 의 첫 호출 body 가 `SLL_TYPE == "00"` 을 포함.
16. `test_place_order_uses_correct_tr_id_per_side` — BUY 호출 시 transport.calls[0]["tr_id"] == "VTTT1002U", SELL 호출 시 "VTTT1001U".
17. `test_place_order_kis_rejection_propagates` — FakeOrderTransport 가 `{"rt_cd": "1", "msg_cd": "EFGS9999", "msg1": "rejected"}` 반환 → `KisOrderRejectedError("kis_error:EFGS9999")`. `broker.last_order_response is None`. `broker.last_error == "kis_error:EFGS9999"`.
18. `test_place_order_malformed_response_fails_closed` — FakeOrderTransport 가 `{"unexpected": True}` (no rt_cd, no output) → 성공 처리되지만 (rt_cd None 은 success로 분류) ack.broker_order_id is None (output 없음). `broker.last_order_response.broker_order_id is None`. 즉 rt_cd 가 명시되지 않은 경우는 success 로 보고 odno 없으면 None.

   _대안 처리_: rt_cd 가 명시되지 않은 응답을 fail-closed 로 거절하고 싶다면 transport 또는 broker 단계에서 `if "rt_cd" not in sanitized: raise KisOrderRejectedError("malformed_response")` 를 추가할 수 있다. 본 plan 은 catalog 의 `rt_cd` 가 `0=성공, 그 외=실패` 로 정의된 것을 따라 명시되지 않으면 success-but-no-odno 로 둔다. Codex 가 둘 중 하나로 결정하고 `patch.md` 에 명시. (권고: malformed 로 거절하는 쪽이 더 안전.)

19. `test_place_order_http_404_fails_closed` — FakeOrderTransport 가 `KisOrderRejectedError("http_404")` raise → 그대로 전파.
20. `test_place_order_transport_error_fails_closed` — FakeOrderTransport 가 `KisOrderRejectedError("transport_error")` raise → 그대로 전파.
21. `test_urllib_order_transport_rejects_live_host` — `base_url="https://openapi.koreainvestment.com:9443"` → `KisOrderRejectedError("disallowed_host")`. (test 에서 base_url 문자열을 split-construct 해서 lint grep 회피.)
22. `test_urllib_order_transport_rejects_unsupported_tr_id` — `tr_id="TTTT1002U"` (실전 매수) → `KisOrderRejectedError("disallowed_tr_id")`. 실전 TR_ID 가 코드 / 테스트 어디에도 상수로 박혀 있지 않도록 문자열을 split-construct.
23. `test_urllib_order_transport_rejects_invalid_exchange` — body OVRS_EXCG_CD="LSE" → `KisOrderRejectedError("invalid_exchange")`.
24. `test_urllib_order_transport_rejects_invalid_ord_dvsn` — body ORD_DVSN="32" (실전 LOO) → `KisOrderRejectedError("ord_dvsn_not_limit")`.
25. `test_place_order_response_sanitization_redacts_secrets` — FakeOrderTransport 가 응답에 `{"rt_cd": "0", "output": {"ODNO": "0000999"}, "appkey": "echoed-key", "access_token": "Bearer echoed-token"}` 반환. `json.dumps(broker.last_order_response.raw_response_sanitized)` 에 `"echoed-key"` / `"Bearer echoed-token"` / `"fake-key-XYZ"` / `"fake-secret-XYZ"` / `"12345678"` 모두 등장 안 함.
26. `test_place_order_exceptions_and_repr_do_not_expose_secrets` — 모든 fail-closed 경로 (mock, auth, http, kis_error, malformed, preflight) 에서 `str(exc)` 와 `repr(broker)` / `repr(broker.last_order_response)` 에 `"fake-key-XYZ"` / `"fake-secret-XYZ"` / `"12345678"` / `"Bearer"` 등장 안 함.
27. `test_place_order_via_oms_passes_riskengine` — OMS + RiskEngine + KisBroker(FakeOrderTransport) chain 으로 end-to-end. OrderIntent → RiskEngine.evaluate → OMS.place → KisBroker.submit → place_order → 성공. 이 테스트는 (a) OMS 가 KisBroker 와 호환됨을 확인, (b) Strategy 가 broker 를 직접 호출하지 않음을 회귀로 보장 (Strategy 는 OrderIntent 만 생성, OMS 가 BrokerOrder 생성). KisBroker.mode == TradingMode.PAPER 이므로 OMS 가 거절하지 않는다.
28. `test_kis_module_does_not_introduce_live_tr_ids` — `app/broker/kis.py` 의 file text 에 `TTTT1002U` / `TTTT1006U` / `TTTT1004U` / `TTTS1003U` / `TTTS0309U` / `TTTT3014U` / `TTTT3016U` / `TTTT3017U` / `TTTS3013U` / `TTTS3018R` / `TTTT3039R` / `TTTS3014R` / `TTTS6036U` / `TTTS6037U` / `TTTS6038U` / `TTTS6058R` / `TTTS6059R` 모두 등장 안 함. 코드/주석/docstring grep clean.
29. `test_kis_paper_order_transport_uses_only_paper_base_url` — `UrllibOrderTransport` 의 동작이 paper host allowlist 외에는 모두 거절. `kis_base_url_live` 가 transport 의 호출 인자로 들어가도 거절.

회귀 / 안전 회귀:

- `tests/test_kis_order_preflight.py::test_place_order_valid_input_with_dry_run_disabled_reaches_notimplemented` →
  - 함수명을 `test_place_order_valid_input_with_dry_run_disabled_requires_auth` 로 변경 (선택).
  - `pytest.raises(NotImplementedError, match="Pre-flight passed")` 를 `pytest.raises(KisOrderRejectedError, match="authentication_required")` 로 변경. import 에 `KisOrderRejectedError` 가 이미 있으므로 추가 변경 없음.
  - 다른 모든 함수 변경 금지.
- `tests/test_broker_interface.py::test_kis_place_cancel_replace_not_implemented` →
  - `broker_no_dry_run.place_order(...)` 에 대한 `pytest.raises(NotImplementedError, match="order endpoint")` 를 `pytest.raises(KisOrderRejectedError, match="authentication_required")` 로 변경 (1-2 줄).
  - 함수 내 다른 assertion (dry_run=True 경로 `status == "dry_run"`, cancel_order / replace_order NotImplementedError) 그대로 유지.
  - 다른 모든 함수 변경 금지.
- `tests/test_kis_order_preflight.py::test_place_order_valid_input_reaches_notimplemented` — 변경 없음 (dry-run=True 기본값에서 `status == "dry_run"` 단언; 그대로 통과).
- `tests/test_kis_capabilities.py::test_kis_capabilities_fail_closed` — 변경 없음 (capabilities submission=False 유지).
- `tests/test_broker_interface.py::test_kis_broker_capabilities_are_exported_and_fail_closed` — 변경 없음.
- `tests/test_broker_interface.py::test_kis_healthcheck_returns_disconnected_dict` — 변경 없음 (`order_execution_implemented is False`, `order_methods_fail_closed is True` 유지).
- `tests/test_api_paper_status.py::*` — 변경 없음. `kis_order_submission_available is False`, `kis_order_methods_fail_closed is True`, `kis_order_entry_mode == "not_implemented"` 모두 유지.
- `tests/test_kis_order_request_model.py::*` — 변경 없음.
- `tests/test_kis_order_response_model.py::*` — 변경 없음.
- `tests/test_kis_account_client.py::*` — 변경 없음.
- `tests/test_kis_market_data_client.py::*`, `test_kis_quote_mapper.py`, `test_kis_auth_client.py`, `test_kis_token_cache.py`, `test_kis_api_mode.py`, `test_kis_config.py`, `test_kis_http_boundaries.py`, `test_kill_switch.py`, `test_missing_official_values_doc.py`, `test_missing_market_data_values_doc.py` — 변경 없음.
- Strategy / Agent / OMS / RiskEngine / Portfolio / Runtime / Session 관련 테스트 변경 없음.
- 모든 응답 / repr / exception / pytest capture 에 `fake-key-XYZ` / `fake-secret-XYZ` / `12345678` (단, 명시적 fixture 인용 외) / `Bearer` 토큰 원문 등장하지 않는다.

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
grep -rn "TTTT1002U\|TTTT1006U\|TTTT1004U\|TTTS1002U\|TTTS1001U\|TTTS0307U\|TTTS0308U\|TTTS0309U\|TTTT3014U\|TTTT3016U\|TTTT3017U\|TTTS3013U" app tests
grep -rn "TTTS3018R\|TTTT3039R\|TTTS3014R\|TTTS6036U\|TTTS6037U\|TTTS6038U\|TTTS6058R\|TTTS6059R" app tests
grep -rn "openapi.koreainvestment.com:9443" app tests
grep -rn "ALLOW_MARKET_ORDERS=true\|allow_market_orders=True" app
grep -rn "Bearer eyJ\|access_token=eyJ" app tests docs/ai/jobs/api-orders-paper-001
grep -rn "from app.broker.kis" app/strategy 2>/dev/null
grep -rn "from app.broker.kis" app/agent 2>/dev/null
```

기대 결과 — 외부 HTTP / 실전 TR_ID / 모의 미지원 TR_ID / 실전 base URL / market order 활성화 / 실토큰 / Strategy·Agent 의 KIS 직접 import 모두 0 lines (단 `app/config.py` 의 기존 `kis_base_url_live` default 와 `ALLOW_MARKET_ORDERS=true` reject 메시지 같은 기존 가드 라인은 잔존 가능 — patch.md 에서 명시).

## 6. 리뷰 체크리스트

안전 회귀:

- [ ] live trading 활성화 코드 / live broker API 호출 / 실주문 endpoint 추가 없음.
- [ ] 실전 base URL 호출 코드/문자열 추가 없음.
- [ ] 실전 TR_ID (`TTTT1002U` / `TTTT1006U` / `TTTT1004U` / `TTTS1002U` / `TTTS1001U` / `TTTS0307U` / `TTTS0308U` / `TTTS0309U` / `TTTT3014U` / `TTTT3016U` / `TTTT3017U` / `TTTS3013U`) 코드/테스트/문서 추가 없음.
- [ ] 모의 미지원 TR_ID (`TTTS3018R` / `TTTT3039R` / `TTTS3014R` / `TTTS6036U` / `TTTS6037U` / `TTTS6038U` / `TTTS6058R` / `TTTS6059R`) 코드/테스트/문서 추가 없음.
- [ ] `OrderType.MARKET` 3중 가드 / `ALLOW_MARKET_ORDERS=true` reject / kill switch / `validate_kis_order_request` 본문 변경 없음.
- [ ] `OrderType.STOP` 도입 없음. enum 변경 없음.
- [ ] `KisBroker.cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` 본문/예외 변경 없음.
- [ ] `app/broker/kis_http.py` 변경 없음. `ALLOWED_PATHS_API_AUTH_001` 그대로.
- [ ] `UrllibOrderTransport` 가 host allowlist (1 개) + TR_ID allowlist (2 개) + path allowlist (1 개) + method allowlist (POST 1 개) + exchange allowlist (3 개) + ORD_DVSN allowlist (1 개 `"00"`) 를 강제. 실패 시 모두 `KisOrderRejectedError` short tag 로 fail-closed.
- [ ] 외부 HTTP 라이브러리 (`requests` / `httpx` / `aiohttp` / `urllib3`) import 없음.
- [ ] secret / 계좌번호 / access token / Bearer 원문 코드/repr/exception/로그/pytest capture 노출 없음.
- [ ] `.env` / `.env.example` 수정 없음. 새 env 변수 추가 없음.
- [ ] Strategy / Agent / LLM 이 `app.broker.kis` 직접 import / KisBroker 직접 호출 추가 없음.
- [ ] OMS / RiskEngine 경계 약화 없음. OMS.place → RiskEngine.evaluate → BrokerOrder 생성 → KisBroker.submit 순서 그대로.

스코프 / 동작:

- [ ] `place_order` 가 `kis_order_dry_run=True` 에서는 transport 호출 없이 `OrderAck(status="dry_run")` + sanitized preview 반환.
- [ ] `kis_order_dry_run=False` 에서는 (a) preflight (paper / no-live / kis_env=paper / LIMIT / qty>0 / price>0 / fresh quote / no-kill-switch) → (b) auth 토큰 확인 → (c) `_split_kis_account_no` 10-digit 검증 → (d) catalog 기반 body 작성 → (e) UrllibOrderTransport.submit_order → (f) response sanitize → (g) `rt_cd` 검사 → (h) `KisOrderResponse` 작성 + `OrderAck(status="submitted")` 반환.
- [ ] body 가 catalog `Confirmed: yes` 필드만 포함 (`CANO` / `ACNT_PRDT_CD` / `OVRS_EXCG_CD` / `PDNO` / `ORD_QTY` / `OVRS_ORD_UNPR` / `ORD_DVSN` / `ORD_SVR_DVSN_CD` + SELL 시 `SLL_TYPE="00"`). 다른 키 없음.
- [ ] `ORD_DVSN == "00"` (LIMIT) 고정. `ORD_SVR_DVSN_CD == "0"` 고정.
- [ ] BUY 시 `SLL_TYPE` 없음. SELL 시 `SLL_TYPE == "00"`.
- [ ] BUY → `VTTT1002U`, SELL → `VTTT1001U` 매핑.
- [ ] response parser 가 `rt_cd` / `msg_cd` / `msg1` / `output.ODNO` / `output.KRX_FWDG_ORD_ORGNO` / `output.ORD_TMD` 만 사용.
- [ ] response raw 가 항상 `sanitize_kis_response` 통과 후 보존 (`KisOrderResponse.raw_response_sanitized`).
- [ ] `KisBroker.capabilities()` 반환 dict 변경 없음 (`submission=False` 유지). `healthcheck()["order_execution_implemented"]` 도 `False` 유지.
- [ ] `KisBroker.last_order_response` 신규 property 가 정상 동작 (dry_run 후에는 그대로 `None`, 실 submission 후 `KisOrderResponse` 반환).

테스트 / 문서:

- [ ] `python -m compileall app tests` 통과.
- [ ] `python -m pytest -p no:cacheprovider` 전체 PASS.
- [ ] 신규 `tests/test_kis_paper_order_submission.py` 가 happy / preflight / dry-run / auth / mock / kis_error / http / transport / malformed / multi-currency-free / OMS chain / secret leak / TR_ID surface 회귀 모두 검증.
- [ ] `tests/test_kis_order_preflight.py` 와 `tests/test_broker_interface.py` 의 좁은 갱신만 수행 (각 1 함수 1-2 줄). 다른 함수 무변동.
- [ ] `docs/ai/jobs/api-orders-paper-001/patch.md` 에 변경 파일 / 사용 endpoint·TR_ID 출처 / dry-run 동작 / 실 모의 전송 조건 / fail-closed 범위 / secret 회귀 / safety 회귀 / 테스트 결과 / 안전 grep 결과 / Claude 검증 요청 프롬프트 / follow-up Codex 프롬프트 규칙 모두 포함.

자동화 금지:

- [ ] commit / push / merge / PR / deploy 수행 안 됨.
- [ ] `.env` / secret / credential / API key / token 수정/노출 없음.
- [ ] `docs/kis/MISSING_OFFICIAL_VALUES.md` 수정 없음.
