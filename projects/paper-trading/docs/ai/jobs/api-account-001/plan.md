# api-account-001 — KIS 모의 계좌 / 잔고 / 포지션 read-only 조회 구현

## 1. 요청 요약

KIS_2 (`docs/kis/MISSING_OFFICIAL_VALUES.md` §2) 에서 해외주식 계좌 / 잔고 / 매수가능금액 endpoint catalog 가 `Confirmed: yes` 로 정리됐다. 본 작업은 `app/broker/kis.py` 의 `KisAccountClient.get_account()` / `get_positions()` / `get_cash_balance()` 를 catalog 의 모의투자 지원 endpoint 만 사용해서 read-only 로 구현한다.

핵심 결정 — catalog 의 모의 지원 범위:

- 잔고 조회 (`/uapi/overseas-stock/v1/trading/inquire-balance`, TR_ID 모의 `VTTS3012R`, GET) 는 모의 `Confirmed: yes`. `output1[]` (포지션 리스트) 와 `output2` (계좌 집계) 모두 catalog 에 sub-field 까지 명시. → `get_account()` 와 `get_positions()` 구현 가능.
- 매수가능금액 (`/inquire-psamount`, 모의 `VTTS3007R`) 은 종목·가격 입력이 필수 (`ITEM_CD` + `OVRS_ORD_UNPR`) 하고 응답이 "주문 가능 금액" 이지 "보유 현금" 이 아니다. `KisCashBalance(currency, cash, withdrawable_cash)` 의 의미와 일치하지 않는다.
- 체결기준 현재잔고 (`/inquire-present-balance`, 모의 `VTRP6504R`) 은 catalog 가 명시한 대로 모의에서 `output3` 만 사용 가능하고, `output3` 의 sub-field 는 KIS_2 patch.md 의 §5 "남긴 항목" 에 따라 `<TBD>`. → catalog 가 cash sub-field 를 보장하지 않으므로 추측 금지 원칙에 따라 사용 불가.
- 결제기준 잔고 / 일별거래내역 / 기간손익 / 해외증거금 통화별 (4 개) 은 catalog 가 명시한 대로 **모의투자 미지원**. → 사용 불가.

따라서:

- `get_account()`, `get_positions()` 는 잔고 endpoint (`VTTS3012R`) 의 `Confirmed: yes` 필드만 사용해 구현한다.
- `get_cash_balance()` 는 catalog 에서 "보유 현금" 을 직접 보장하는 모의 endpoint·필드가 없으므로 **fail-closed 유지** (NotImplementedError 또는 더 명확한 `KisDataUnavailableError`). 단 fail-closed 메시지는 catalog 가 모자라다는 사실을 정확히 가리키도록 변경하고, `kis_cash_balance_loaded` 는 계속 False 로 노출.

추가 제약:

- 외부 HTTP 라이브러리 (`requests`, `httpx`, `aiohttp`, `urllib3`) 금지. stdlib `urllib.request` 만 사용.
- KIS endpoint / TR ID / payload / header 추측 금지. KIS_2 catalog 의 `Confirmed: yes` 행 + 모의 지원 행만 사용.
- 실전 base URL (`https://openapi.koreainvestment.com:9443`) 호출 금지. 모의 base URL (`https://openapivts.koreainvestment.com:29443`) 만.
- 실전 TR_ID (`TTTS3012R`, `TTTS3007R`, `CTRP6504R`, `CTRP6010R`, `CTOS4001R`, `TTTS3039R`, `TTTC2101R`) 코드/문서/테스트 추가 금지.
- 주문·취소·정정·체결조회·미체결 endpoint 구현 금지. `place_order` / `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` 동작 변경 금지 (NotImplementedError 또는 dry-run 그대로).
- `OrderType.MARKET` 3중 가드 / `ALLOW_MARKET_ORDERS=true` 차단 / kill switch / live trading 가드 그대로.
- secret · 계좌번호 · access token · Bearer 원문은 코드 / 로그 / repr / 예외 메시지 / 테스트 캡처 / patch / docstring 어디에도 기록 금지.
- `.env` / `.env.example` 읽기·수정 금지.
- GUI (`app/api/*`, `app/static/*`, `app/main.py`) 변경 금지. `/paper/status` 는 이미 `kis_account_loaded` / `kis_positions_loaded` / `kis_cash_balance_loaded` 를 `KisBroker.healthcheck()` 에서 그대로 노출하므로 routes.py 수정 없이 동작이 갱신된다.

## 2. 작업 범위

포함하는 것:

- `app/broker/kis.py`:
  - 잔고 endpoint 전용 상수: path / 모의 TR_ID / paper host allowlist / 모의 거래소 allowlist (`NASD` / `NYSE` / `AMEX`) / 모의 통화 allowlist (`USD` / `HKD` / `CNY` / `JPY` / `VND`) / 최대 페이지 cap.
  - `_split_kis_account_no(account_no)` helper: KIS 계좌번호 (`12345678-01` 또는 `1234567801`) 를 `(CANO, ACNT_PRDT_CD)` 10-digit pair 로 분리. 형식 오류는 `KisConfigError`.
  - 신규 `KisAccountTransport` Protocol (모듈 내부 정의, 시그니처: `get_balance(*, base_url, access_token, app_key, app_secret, tr_id, cano, acnt_prdt_cd, ovrs_excg_cd, tr_crcy_cd, ctx_area_fk200, ctx_area_nk200, tr_cont) -> dict[str, Any]`).
  - 신규 `UrllibAccountTransport`: stdlib `urllib.request` GET. 자체 host / path / method / TR_ID allowlist (모의 1 개씩).
  - 신규 `MockAccountTransport`: mock 모드용. 호출 시 `KisDataUnavailableError("mock_mode_no_network")`.
  - `KisAccountClient.__init__` 에 `transport: KisAccountTransport | None = None` 파라미터 추가 (테스트 주입용). 기본값은 `kis_api_mode` 에 따라 위 두 transport 중 선택.
  - `KisAccountClient.get_account(*, exchange="NASD", currency="USD") -> dict[str, Any]` 본문 구현. 인증/모의/페이지 루프 → sanitized aggregate dict 반환. 성공 시 `_account_loaded = True`.
  - `KisAccountClient.get_positions(*, exchange="NASD", currency="USD") -> list[KisPosition]` 본문 구현. 내부적으로 잔고 페이지를 모두 가져와 `output1[]` 를 KisPosition 리스트로 매핑. 성공 시 `_positions_loaded = True`.
  - `KisAccountClient.get_cash_balance(*, ...)` 본문: catalog gap 으로 인해 `KisDataUnavailableError("paper_cash_balance_not_available_official_field_missing")` 로 fail-closed (현재 `NotImplementedError` 보다 더 명확한 read-only 실패 신호로 전환). `_cash_balance_loaded` 는 False 유지.
  - `KisAccountClient.parse_positions_response(raw)` 와 `parse_cash_balance_response(raw)` 를 catalog `Confirmed: yes` 필드만 사용하도록 재작성 (legacy domestic-stock 추측 필드 `pdno` / `hldg_qty` / `dnca_tot_amt` / `nxdy_excc_amt` 제거).
  - `KisPosition` 데이터클래스에 catalog 의 통화·거래소 정보를 노출하기 위해 `currency: str` (`tr_crcy_cd`) 와 `exchange: str` (`ovrs_excg_cd`) 두 필드를 default 와 함께 추가 (기존 위치 인자 호출 후방 호환).
  - `KisAccountClient._validate_paper_account_query()` 헬퍼: paper / live trading / kis_env / kill_switch 검증을 한 곳에 모은다. 위반 시 `KisAuthError` 로 fail-closed (live trading 활성 시 read-only 조회까지 차단).
- 신규 테스트 (`tests/test_kis_account_client.py`): transport 주입 기반 happy / error path + sanitization + secret leak 회귀.
- 좁은 범위 회귀 테스트 갱신 (`tests/test_kis_http_boundaries.py` 의 parser 테스트 1 개 — catalog 필드명으로 fixture 갱신).
- `docs/kis/MISSING_OFFICIAL_VALUES.md` 무변동 (catalog 는 소비만).
- `README.md` 1-2 줄 보강 가능 (선택).
- `docs/ai/jobs/api-account-001/patch.md` (Codex 가 작성).

제외 (절대 안 하는 것):

- live trading 활성화 / `LIVE_TRADING_ENABLED=true` / live broker API 호출 / 실전 base URL 사용.
- 실주문 / 취소 / 정정 / 체결 / 미체결 endpoint 구현. `KisBroker.place_order` / `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` 동작 변경 금지 (NotImplementedError 또는 dry-run 그대로).
- `OrderType.MARKET` 가드 / `ALLOW_MARKET_ORDERS=true` 변경 / kill switch 동작 변경.
- 외부 HTTP 라이브러리 import (`requests`, `httpx`, `aiohttp`, `urllib3`).
- KIS endpoint / TR_ID / header / payload 추측. catalog `<TBD>` 또는 `Confirmed: no` 행 사용 금지.
- 실전 TR_ID (`TTTS3012R`, `CTRP6504R`, `CTOS4001R`, `TTTS3039R`, `TTTC2101R`, `CTRP6010R`) 추가.
- 모의투자 미지원 endpoint (`TTTS3018R` / `CTRP6010R` / `CTOS4001R` / `TTTS3039R` / `TTTC2101R` / `TTTT3039R` / `TTTS3014R` / `TTTS6036U` / `TTTS6037U` / `TTTS6038U` / `TTTS6058R` / `TTTS6059R`) 구현.
- `app/broker/kis_http.py` 변경. `ALLOWED_PATHS_API_AUTH_001` 그대로 (`/oauth2/tokenP` + `/oauth2/revokeP` 만). 계좌 endpoint 는 별도 transport 로 처리.
- 새 env 변수 추가. KIS 계좌 분리·페이지 cap 등은 모두 코드 상수 또는 함수 인자.
- `.env` / `.env.example` 변경.
- `app/api/*`, `app/static/*`, `app/main.py`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/config.py`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/base.py`, `app/broker/kis_token_cache.py`, `app/broker/kis_quote_mapper.py` 변경.
- Strategy / Agent / LLM 이 `app.broker.kis` 또는 `KisAccountClient` 를 직접 import 하는 경로 추가 (`test_strategy_package_does_not_import_kis` / `test_agent_package_does_not_import_kis_if_present` 회귀 유지).
- 자동 git commit / push / merge / deploy.

## 3. 수정해야 할 파일

후방 호환 정책:

- `KisPosition` 에 `currency: str = "USD"`, `exchange: str = ""` 두 필드를 default 와 함께 끝에 추가한다. 기존 위치 인자 호출 (`KisPosition(symbol=..., quantity=..., avg_price=..., market_value=...)`) 는 모두 그대로 동작.
- `KisAccountClient.get_account()` 의 시그니처는 `() -> dict[str, Any]` 에서 `(*, exchange: str = "NASD", currency: str = "USD") -> dict[str, Any]` 로 확장. 기존 호출자 (`KisBroker.get_account`) 는 위임 시 기본값을 사용하므로 후방 호환.
- `KisAccountClient.get_positions()` 도 `(*, exchange="NASD", currency="USD")` 로 동일 확장. `KisBroker.get_positions()` 호출은 그대로 동작 (기본값 사용).
- `KisAccountClient.get_cash_balance()` 는 시그니처 변동 없음. 본문이 `NotImplementedError` → `KisDataUnavailableError` 로 바뀌므로 `KisBroker` 측 expose 는 변경 없음 (KisBroker 가 cash 메서드를 노출하지 않음).
- `parse_positions_response` 와 `parse_cash_balance_response` 는 catalog 필드만 사용하도록 본문 재작성. 시그니처 변동 없음. 입력에서 catalog 필드가 누락되면 빈 리스트 / `KisDataUnavailableError("malformed_response: ...")` 로 fail-closed.

| 경로 | 변경 종류 | 요약 |
| --- | --- | --- |
| `projects/paper-trading/app/broker/kis.py` | MODIFY | (1) 잔고 endpoint 상수. (2) `_split_kis_account_no` helper. (3) `KisPosition` 에 `currency`, `exchange` default 필드 추가. (4) `KisAccountTransport` Protocol. (5) `UrllibAccountTransport` (host/path/method/TR_ID allowlist 1 개씩). (6) `MockAccountTransport`. (7) `KisAccountClient.__init__` 에 transport 주입. (8) `_validate_paper_account_query()` helper. (9) `get_account` / `get_positions` / `get_cash_balance` 본문. (10) `parse_positions_response` / `parse_cash_balance_response` catalog 정렬. (11) `KisBroker.__init__` 가 KisAccountClient 인스턴스화 시 KIS_API_MODE 기준 transport 자동 선택. **주문 / 시세 / OAuth 관련 코드 (KisAuthClient / KisMarketDataClient / KisBroker.place_order 외 주문 메서드 / KisHttpClient.request / `_to_kis_request` / `_dry_run_preview` / `_validate_paper_settings` / `validate_kis_order_request` / capabilities) 변경 금지.** |
| `projects/paper-trading/tests/test_kis_account_client.py` | NEW | transport 주입으로 happy / error / pagination / sanitization / 통화·거래소 분리 / fail-closed 회귀 검증 (자세한 항목은 §5). |
| `projects/paper-trading/tests/test_kis_http_boundaries.py` | MODIFY (좁은 범위) | `test_account_parsers_return_internal_models_and_sanitize` 의 입력 dict 와 기대값을 catalog `Confirmed: yes` 필드로 정렬 (`output1[]` `ovrs_pdno` / `ovrs_cblc_qty` / `pchs_avg_pric` / `ovrs_stck_evlu_amt` / `tr_crcy_cd` / `ovrs_excg_cd`). `test_account_queries_require_authentication` 에서 `broker.account.get_cash_balance()` 가 여전히 `KisAuthError("authentication required")` 로 raise 함을 그대로 통과 (auth 게이트가 첫 번째). 다른 테스트 절대 변경 금지. |
| `projects/paper-trading/docs/ai/jobs/api-account-001/patch.md` | NEW (Codex 가 작성) | 변경 요약 + 사용 endpoint / TR_ID 출처 + 구현 / fail-closed 범위 + 테스트 결과 + secret leak 회귀 + safety 회귀 + Claude 검증 프롬프트 + follow-up Codex 프롬프트 규칙. |
| `projects/paper-trading/README.md` | MODIFY (선택, 1-2 줄) | KIS 계좌 read-only 조회가 paper 모드에서 가능해졌다는 안내. 새 env 변수 안내 금지. 생략 가능. |

**범위 확장 사유** (request 의 "수정 가능 파일" 외 추가):

- `tests/test_kis_http_boundaries.py` 의 `test_account_parsers_return_internal_models_and_sanitize` 는 현재 `symbol` / `quantity` / `avg_price` / `market_value` 같은 generic 필드명과 `cash` dict 의 generic 키로 parser 를 호출한다. "공식 response field 만 사용" 요건을 반영해서 본 fixture 를 catalog 필드명 (`ovrs_pdno` / `ovrs_cblc_qty` 등) 으로 갱신해야 한다. 1 개 함수의 input/expected 본문 갱신만 수행하고, 다른 회귀 assertion (auth gate / sanitize / repr masking / no-third-party-http / no-live-transport 등) 은 절대 변경 금지.

손대지 않는 파일:

- `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/base.py`.
- `app/broker/kis_http.py` (SafeKisHttpClient, MockTransport, UrllibTransport, ALLOWED_PATHS_API_AUTH_001 그대로). 계좌 transport 는 `kis.py` 내부 정의.
- `app/broker/kis_token_cache.py`, `app/broker/kis_quote_mapper.py`.
- `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/main.py`, `app/api/*`, `app/static/*`.
- `app/config.py` (새 env 추가 금지).
- `app/domain/*` (KisPosition 외 domain 변경 금지).
- `docs/kis/*` (catalog 자체는 본 작업에서 수정하지 않는다; catalog 의 `Confirmed: yes` 행만 소비).
- `.env`, `.env.example`.

## 4. Codex 구현 지시문

자세한 단계는 `codex-task.md` 에 기록한다. 요지:

### 4.1 잔고 endpoint 상수 (`app/broker/kis.py`)

```python
KIS_OVERSEAS_BALANCE_PATH = "/uapi/overseas-stock/v1/trading/inquire-balance"
KIS_OVERSEAS_BALANCE_TR_ID_PAPER = "VTTS3012R"
KIS_PAPER_ACCOUNT_HOSTS = frozenset({"openapivts.koreainvestment.com:29443"})
KIS_PAPER_ACCOUNT_EXCHANGES = frozenset({"NASD", "NYSE", "AMEX"})
KIS_PAPER_ACCOUNT_CURRENCIES = frozenset({"USD", "HKD", "CNY", "JPY", "VND"})
KIS_BALANCE_MAX_PAGES = 10  # safety cap against runaway pagination
```

**중요**: 실전 TR_ID (`TTTS3012R`), 미지원 TR_ID (`CTRP6504R` 등), 또는 catalog `<TBD>` 행 의 식별자는 모듈/테스트/문서에 추가하지 말 것.

### 4.2 계좌번호 분리 helper

```python
def _split_kis_account_no(account_no: str) -> tuple[str, str]:
    """Split a KIS account number into (CANO, ACNT_PRDT_CD).

    Accepts '12345678-01' or '1234567801'. Always 10 digits (8+2) after
    stripping the optional dash. Raises KisConfigError on any other format.
    """
    digits = (account_no or "").replace("-", "").strip()
    if len(digits) != 10 or not digits.isdigit():
        raise KisConfigError("invalid_kis_account_no_format")
    return digits[:8], digits[8:]
```

테스트 fixture 에는 `12345678-01` 또는 `1234567801` 같이 10 digit 형식만 사용 (기존 `12345678` 형식 fixture 는 `get_account` 를 호출하지 않는 테스트에 한해 유지 가능).

### 4.3 `KisPosition` 확장

```python
@dataclass(frozen=True)
class KisPosition:
    symbol: str
    quantity: int
    avg_price: Decimal
    market_value: Decimal
    currency: str = "USD"      # tr_crcy_cd
    exchange: str = ""          # ovrs_excg_cd
```

- 기존 위치 인자 호출 (`KisPosition("AAPL", 2, Decimal("100.50"), Decimal("201.00"))`) 후방 호환.
- `__post_init__` 추가 금지. 검증은 parser 단계에서 수행.

### 4.4 `KisAccountTransport` Protocol & 실 transport

```python
class KisAccountTransport(Protocol):
    def get_balance(
        self,
        *,
        base_url: str,
        access_token: str,
        app_key: str,
        app_secret: str,
        tr_id: str,
        cano: str,
        acnt_prdt_cd: str,
        ovrs_excg_cd: str,
        tr_crcy_cd: str,
        ctx_area_fk200: str,
        ctx_area_nk200: str,
        tr_cont: str,
    ) -> dict[str, Any]:
        """Return a single page of the KIS overseas balance response."""
```

`UrllibAccountTransport`:

- `timeout_seconds`, `max_retries`, `backoff_seconds` 필드.
- `get_balance(...)`:
  - host = `_kis_extract_host(base_url)`. `KIS_PAPER_ACCOUNT_HOSTS` 외이면 `KisDataUnavailableError("disallowed_host")`.
  - `tr_id` 가 `KIS_OVERSEAS_BALANCE_TR_ID_PAPER` 가 아니면 `KisDataUnavailableError("disallowed_tr_id")`.
  - `ovrs_excg_cd` 가 `KIS_PAPER_ACCOUNT_EXCHANGES` 외이면 `KisDataUnavailableError("invalid_exchange")`.
  - `tr_crcy_cd` 가 `KIS_PAPER_ACCOUNT_CURRENCIES` 외이면 `KisDataUnavailableError("invalid_currency")`.
  - URL = `f"{base_url.rstrip('/')}{KIS_OVERSEAS_BALANCE_PATH}?CANO={cano}&ACNT_PRDT_CD={acnt_prdt_cd}&OVRS_EXCG_CD={ovrs_excg_cd}&TR_CRCY_CD={tr_crcy_cd}&CTX_AREA_FK200={urlquote(ctx_area_fk200)}&CTX_AREA_NK200={urlquote(ctx_area_nk200)}"`. cano/acnt_prdt_cd/ovrs_excg_cd/tr_crcy_cd 값은 위에서 검증 통과한 안전한 ASCII.
  - Headers: `{"content-type": "application/json; charset=utf-8", "authorization": f"Bearer {access_token}", "appkey": app_key, "appsecret": app_secret, "tr_id": tr_id, "tr_cont": tr_cont}`. 다른 header (custtype, personalseckey, seq_no, mac_address, phone_number, ip_addr, gt_uid) 는 본 작업에서 미사용 — catalog 가 모두 옵션으로 명시했고 개인 사용자 가정이므로 미설정.
  - GET 만 사용. body 없음.
  - 재시도: 5xx 또는 transport error 시 `max_retries` 까지 (1 회 권장). `socket.timeout` / `TimeoutError` / `URLError` 처리. 4xx 는 즉시 `KisDataUnavailableError(f"http_{code}")`.
  - 응답 JSON 파싱 실패 → `KisDataUnavailableError("invalid_response_body")`.
  - `rt_cd` 가 `"0"` 이 아니면 → `KisDataUnavailableError(f"kis_error:{msg_cd or msg1 or 'unknown'}")`.
  - 정상 응답이면 `response_dict` 반환 (raw, sanitization 은 KisAccountClient 가 수행).
  - **secret 노출 금지**: access_token / app_key / app_secret / Authorization 헤더를 stdout / stderr / repr / exception message 에 절대 포함하지 말 것. urllib `HTTPError` 의 `read()` body 를 그대로 메시지에 넣지 말고 `http_<code>` / `transport_error` 같은 short tag 만 사용.

`MockAccountTransport`:

- `get_balance(...)` → `raise KisDataUnavailableError("mock_mode_no_network")`.

### 4.5 `KisAccountClient` 본문

```python
class KisAccountClient:
    def __init__(
        self,
        settings: Settings,
        auth: KisAuthClient,
        transport: KisAccountTransport | None = None,
    ) -> None:
        if not settings.kis_account_no:
            raise KisConfigError("KIS_ACCOUNT_NO missing in .env")
        self._settings = settings
        self._auth = auth
        self._account_loaded = False
        self._positions_loaded = False
        self._cash_balance_loaded = False
        self._last_error: str | None = None
        if transport is not None:
            self._transport = transport
        else:
            mode = KisApiMode.parse(settings.kis_api_mode)
            if mode is KisApiMode.MOCK:
                self._transport = MockAccountTransport()
            else:
                self._transport = UrllibAccountTransport(
                    timeout_seconds=settings.kis_oauth_timeout_seconds,
                    max_retries=settings.kis_oauth_max_retries,
                )

    def _require_auth(self) -> None:
        if not self._auth.is_authenticated():
            self._last_error = "authentication_required"
            raise KisAuthError("KIS authentication required")

    def _validate_paper_account_query(self) -> None:
        """Read-only safety gate: paper mode, no live trading, kis_env=paper, no kill switch."""
        if self._settings.trading_mode != TradingMode.PAPER:
            self._last_error = "trading_mode_not_paper"
            raise KisAuthError("trading_mode_not_paper")
        if self._settings.live_trading_enabled:
            self._last_error = "live_trading_enabled"
            raise KisAuthError("live_trading_enabled")
        if self._settings.kis_env != "paper":
            self._last_error = "kis_env_not_paper"
            raise KisAuthError("kis_env_not_paper")
        if self._settings.kill_switch_engaged:
            self._last_error = "kill_switch_engaged"
            raise KisAuthError("kill_switch_engaged")
```

- `_validate_paper_account_query` 가 `KisAuthError` 를 던지는 이유: 기존 `test_account_queries_require_authentication` 회귀 (`KisAuthError("authentication required")` 정확 매치) 를 깨지 않기 위해, paper-only 가드는 별도의 명확한 메시지 (`live_trading_enabled` 등) 를 쓰지만 동일한 예외 클래스 로 fail-closed. 호출 순서는 `_require_auth → _validate_paper_account_query` (auth 가 먼저).

#### 4.5.1 `get_account(*, exchange="NASD", currency="USD") -> dict[str, Any]`

```python
def get_account(self, *, exchange: str = "NASD", currency: str = "USD") -> dict[str, Any]:
    self._require_auth()
    self._validate_paper_account_query()
    pages = list(self._iter_balance_pages(exchange=exchange, currency=currency))
    # pages: list of sanitized response dicts (1 page = 1 dict)
    aggregated_output1: list[dict[str, Any]] = []
    last_output2: dict[str, Any] = {}
    for page in pages:
        rows = page.get("output1") or []
        if isinstance(rows, list):
            aggregated_output1.extend(item for item in rows if isinstance(item, dict))
        out2 = page.get("output2")
        if isinstance(out2, dict):
            last_output2 = out2
    self._account_loaded = True
    self._last_error = None
    return {
        "tr_id": KIS_OVERSEAS_BALANCE_TR_ID_PAPER,
        "exchange": exchange,
        "currency": currency,
        "output1": aggregated_output1,
        "output2": last_output2,
        "account_no_masked": self.masked_account_no(),
        "pages_loaded": len(pages),
    }
```

`_iter_balance_pages`:

```python
def _iter_balance_pages(
    self,
    *,
    exchange: str,
    currency: str,
) -> Iterator[dict[str, Any]]:
    cano, acnt_prdt_cd = _split_kis_account_no(self._settings.kis_account_no or "")
    access_token = self._auth.get_access_token()
    if not access_token:
        self._last_error = "authentication_required"
        raise KisAuthError("KIS authentication required")
    ctx_fk = ""
    ctx_nk = ""
    tr_cont = ""
    for page_index in range(KIS_BALANCE_MAX_PAGES):
        try:
            raw = self._transport.get_balance(
                base_url=self._settings.kis_base_url_paper,
                access_token=access_token,
                app_key=self._settings.kis_app_key or "",
                app_secret=self._settings.kis_app_secret or "",
                tr_id=KIS_OVERSEAS_BALANCE_TR_ID_PAPER,
                cano=cano,
                acnt_prdt_cd=acnt_prdt_cd,
                ovrs_excg_cd=exchange,
                tr_crcy_cd=currency,
                ctx_area_fk200=ctx_fk,
                ctx_area_nk200=ctx_nk,
                tr_cont=tr_cont,
            )
        except KisDataUnavailableError as exc:
            self._last_error = str(exc)
            raise
        sanitized = sanitize_kis_response(raw, self._settings)
        yield sanitized
        next_fk = (sanitized.get("ctx_area_fk200") or "").strip()
        next_nk = (sanitized.get("ctx_area_nk200") or "").strip()
        if not next_fk and not next_nk:
            return
        ctx_fk = next_fk
        ctx_nk = next_nk
        tr_cont = "N"
    self._last_error = "balance_pagination_cap_exceeded"
    raise KisDataUnavailableError("balance_pagination_cap_exceeded")
```

- `sanitize_kis_response` 가 raw response 의 sensitive key (`appkey`, `access_token`, `cano`, `acct_no` 등) 를 redact 하므로, `output1[]` / `output2` 에 KIS 가 echo 한 secret 값은 모두 `<redacted>` 로 마스킹된다.

#### 4.5.2 `get_positions(*, exchange="NASD", currency="USD") -> list[KisPosition]`

```python
def get_positions(self, *, exchange: str = "NASD", currency: str = "USD") -> list[KisPosition]:
    account = self.get_account(exchange=exchange, currency=currency)
    rows = account.get("output1") or []
    positions: list[KisPosition] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("ovrs_pdno") or "").strip().upper()
        if not symbol:
            continue
        quantity = _int_from(row.get("ovrs_cblc_qty"))
        if quantity == 0:
            continue  # paper KIS often returns zero-quantity rows after liquidation
        positions.append(
            KisPosition(
                symbol=symbol,
                quantity=quantity,
                avg_price=_decimal_from(row.get("pchs_avg_pric")),
                market_value=_decimal_from(row.get("ovrs_stck_evlu_amt")),
                currency=str(row.get("tr_crcy_cd") or currency).upper(),
                exchange=str(row.get("ovrs_excg_cd") or exchange).upper(),
            )
        )
    self._positions_loaded = True
    return positions
```

- `get_positions()` 가 `get_account()` 를 호출하므로 `_account_loaded` 도 True 로 갱신됨. 두 메서드 호출 시 동일 페이지 반복 호출 방지를 위해 단순 캐시 도입 금지 (read-only 단계에서는 매 호출이 fresh 데이터; caching 은 별 job).

#### 4.5.3 `get_cash_balance(*, ...) -> KisCashBalance`

```python
def get_cash_balance(self) -> KisCashBalance:
    self._require_auth()
    self._validate_paper_account_query()
    self._last_error = "paper_cash_balance_not_available_official_field_missing"
    raise KisDataUnavailableError(
        "paper_cash_balance_not_available_official_field_missing"
    )
```

- 의도: catalog 가 paper-supported endpoint 에 cash 필드를 보장하지 않으므로 read-only 조회를 fail-closed. NotImplementedError 대신 `KisDataUnavailableError` 를 쓰는 이유는 "조회 시도는 가능하지만 catalog 가 부족해 데이터 없음" 을 명확히 전달하기 위해서.
- `_cash_balance_loaded` 는 False 유지. `/paper/status` 의 `kis_cash_balance_loaded` 는 계속 False 로 노출되며 이는 "안전하게 표시" 요건을 만족한다.

### 4.6 `parse_positions_response` / `parse_cash_balance_response` catalog 정렬

```python
def parse_positions_response(self, raw: dict[str, Any]) -> list[KisPosition]:
    sanitized = sanitize_kis_response(raw, self._settings)
    rt_cd = sanitized.get("rt_cd")
    if rt_cd not in (None, "0"):
        code = sanitized.get("msg_cd") or sanitized.get("msg1") or "unknown"
        raise KisDataUnavailableError(f"kis_error:{code}")
    rows = sanitized.get("output1") or []
    if not isinstance(rows, list):
        raise KisDataUnavailableError("malformed_response: output1 not list")
    positions: list[KisPosition] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("ovrs_pdno") or "").strip().upper()
        if not symbol:
            continue
        positions.append(
            KisPosition(
                symbol=symbol,
                quantity=_int_from(row.get("ovrs_cblc_qty")),
                avg_price=_decimal_from(row.get("pchs_avg_pric")),
                market_value=_decimal_from(row.get("ovrs_stck_evlu_amt")),
                currency=str(row.get("tr_crcy_cd") or "USD").upper(),
                exchange=str(row.get("ovrs_excg_cd") or "").upper(),
            )
        )
    self._positions_loaded = True
    return positions


def parse_cash_balance_response(self, raw: dict[str, Any]) -> KisCashBalance:
    # Catalog gap: paper-supported endpoints (VTTS3012R output2, VTRP6504R output3)
    # do not expose a confirmed "total deposit cash" + "withdrawable cash" pair.
    # Fail closed instead of inventing field names.
    raise KisDataUnavailableError(
        "paper_cash_balance_not_available_official_field_missing"
    )
```

- legacy 추측 필드 (`pdno`, `hldg_qty`, `qty`, `dnca_tot_amt`, `nxdy_excc_amt`, `crcy_cd`, `account_no` 의 generic alias) 를 모두 제거. catalog `Confirmed: yes` 필드만 인식.
- `parse_cash_balance_response` 를 fail-closed 로 통일. 기존 테스트 fixture 는 §5 의 회귀 갱신 항목에서 처리.

### 4.7 `KisBroker` 위임

- `KisBroker.get_account()` / `get_positions()` 의 본문은 그대로 `self._account.get_account()` / `self._account.get_positions()` 위임. 기본값 (`NASD` / `USD`) 사용.
- `KisBroker.__init__` 가 `KisAccountClient(settings, auth)` 를 인스턴스화할 때 자동 transport 선택이 적용됨 (KisAccountClient 내부에서 처리).
- 주문 / 시세 관련 메서드 변경 없음. `place_order` / `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` 모두 NotImplementedError 또는 dry-run 그대로 유지.
- `capabilities()` 는 그대로 `{"submission": False, "cancel": False, ...}`. 본 작업은 capability 추가 없음 (read-only 조회는 capability 가 아니라 healthcheck 의 `account_loaded` / `positions_loaded` 로 노출).
- `healthcheck()` 는 그대로 `account_loaded` / `positions_loaded` / `cash_balance_loaded` 를 `self._account` 의 상태에서 읽어 옴.

### 4.8 secret / repr / 로그

- `__repr__` 가 `app_key` / `app_secret` / `access_token` / `kis_account_no` 원문을 절대 포함하지 않는다 (기존 정책 유지).
- 예외 메시지에 secret / 계좌번호 / token 을 포함하지 않는다. short tag (`mock_mode_no_network`, `authentication_required`, `disallowed_host`, `disallowed_tr_id`, `invalid_exchange`, `invalid_currency`, `http_<code>`, `transport_error`, `kis_error:<msg_cd>`, `paper_cash_balance_not_available_official_field_missing`, `balance_pagination_cap_exceeded`, `malformed_response: ...`, `trading_mode_not_paper`, `live_trading_enabled`, `kis_env_not_paper`, `kill_switch_engaged`, `invalid_kis_account_no_format`) 만 사용.
- urllib `HTTPError` 의 `read()` body 를 그대로 메시지에 포함하지 않는다.
- `pytest` capture 된 stdout/stderr 에 secret 이 등장하지 않는다 (`assert "fake-key" not in capsys.readouterr().out` 식 회귀 추가).

## 5. 테스트 기준

신규 테스트 (`tests/test_kis_account_client.py`):

테스트 헬퍼 `_settings(...)` 는 `kis_env="paper"`, `kis_account_no="12345678-01"`, `kis_app_key="fake-key"`, `kis_app_secret="fake-secret"`, `kis_api_mode="paper"` 기본값 사용. `FakeAccountTransport` 는 사전 정의된 페이지 리스트를 순차 반환하거나 예외를 던지는 stub.

- `test_get_account_no_auth_fails_closed`: 새 broker, 토큰 미저장 상태에서 `broker.get_account()` → `KisAuthError("KIS authentication required")`. `account.last_error == "authentication_required"`.
- `test_get_account_with_paper_violation_fails_closed`: `live_trading_enabled=True` settings 에서 토큰 저장 후 `broker.get_account()` → `KisAuthError("live_trading_enabled")`. `last_error == "live_trading_enabled"`. 마찬가지로 `kis_env="live"` 는 KisBroker 생성자에서 RuntimeError 로 차단되므로 KisAccountClient 직접 인스턴스화 + `_validate_paper_account_query()` 호출 분기는 unit 테스트로 (KisAccountClient(settings, auth)).
- `test_get_account_mock_mode_fails_closed`: 토큰 저장 + `kis_api_mode="mock"` 으로 transport 자동 선택 → `KisDataUnavailableError("mock_mode_no_network")`. `account_loaded` False.
- `test_get_account_single_page_happy`: FakeAccountTransport 가 단일 페이지 `{"rt_cd":"0", "output1":[...], "output2":{...}, "ctx_area_fk200":"", "ctx_area_nk200":""}` 반환. `result["pages_loaded"] == 1`. `result["output1"]` 길이 일치. `account_loaded is True`. `last_error is None`.
- `test_get_account_pagination_two_pages`: FakeAccountTransport 가 page1 (`ctx_area_fk200="K1"`, `ctx_area_nk200="N1"`) → page2 (`ctx_area_fk200=""`, `ctx_area_nk200=""`). `pages_loaded == 2`. 두 페이지의 output1 가 모두 aggregate. page2 호출 시 transport 가 받은 `tr_cont == "N"`, `ctx_area_fk200 == "K1"`, `ctx_area_nk200 == "N1"` 임을 verify.
- `test_get_account_pagination_cap_raises`: FakeAccountTransport 가 항상 non-empty `ctx_area_fk200` 반환 → `KIS_BALANCE_MAX_PAGES` 횟수 호출 후 `KisDataUnavailableError("balance_pagination_cap_exceeded")`. `account_loaded is False`.
- `test_get_account_response_kis_error_fails_closed`: FakeAccountTransport 가 `KisDataUnavailableError("kis_error:EFGS9999")` 던짐 → 전파. `last_error == "kis_error:EFGS9999"`. `account_loaded False`.
- `test_get_positions_happy_path_maps_catalog_fields`: page1 `output1` 에 `ovrs_pdno="AAPL"`, `ovrs_cblc_qty="3"`, `pchs_avg_pric="180.25"`, `ovrs_stck_evlu_amt="540.75"`, `tr_crcy_cd="USD"`, `ovrs_excg_cd="NASD"`, 그리고 `ovrs_pdno=""` 또는 `ovrs_cblc_qty="0"` 인 추가 행 → `KisPosition(symbol="AAPL", quantity=3, avg_price=Decimal("180.25"), market_value=Decimal("540.75"), currency="USD", exchange="NASD")` 하나만 반환. zero-quantity / empty-symbol 행 필터링 확인. `positions_loaded is True`.
- `test_get_positions_multi_currency_separated`: FakeAccountTransport 가 USD 호출 (`exchange="NASD"`, `currency="USD"`) 에 USD 행, HKD 호출 (`exchange="NYSE"` 등 — 단 paper 허용 거래소 내 HKD 통화 조합 불가하므로 본 테스트는 직접 client 인스턴스 + FakeTransport 로 currency 인자 검증) 시 두 호출의 `KisPosition.currency` 가 분리됨을 확인. FX 변환 없음 검증 (값 합산 금지).
- `test_get_positions_exchange_currency_validation`: 직접 `UrllibAccountTransport` 인스턴스 + 모의 host base_url 로 `get_balance(...)` 호출 시 `ovrs_excg_cd="LSE"` → `KisDataUnavailableError("invalid_exchange")`. `tr_crcy_cd="EUR"` → `KisDataUnavailableError("invalid_currency")`. `tr_id="VTTS3012R"` 외 → `KisDataUnavailableError("disallowed_tr_id")`. base_url 이 실전 도메인 → `KisDataUnavailableError("disallowed_host")`.
- `test_get_cash_balance_fail_closed`: 토큰 저장 + paper mode → `KisDataUnavailableError("paper_cash_balance_not_available_official_field_missing")`. `cash_balance_loaded is False`. `last_error` 동일 메시지.
- `test_split_kis_account_no_valid_and_invalid`: `_split_kis_account_no("12345678-01") == ("12345678", "01")`. `_split_kis_account_no("1234567801") == ("12345678", "01")`. `_split_kis_account_no("12345678")` → KisConfigError. `_split_kis_account_no("abcd")` → KisConfigError. `_split_kis_account_no("")` → KisConfigError.
- `test_kis_position_repr_does_not_leak_account_no`: `KisPosition(symbol="AAPL", ...)` 의 repr 에 계좌번호 (`"12345678"`) 가 등장하지 않는다 (KisPosition 는 계좌번호를 보유하지 않으므로 trivially OK; 회귀 보호).
- `test_get_account_repr_and_exceptions_do_not_leak_secrets`: `_settings(kis_app_key="fake-key-XYZ", kis_app_secret="fake-secret-XYZ", kis_account_no="12345678-01")`. 모든 fail-closed 경로 (`mock_mode_no_network`, `authentication_required`, `live_trading_enabled`, `paper_cash_balance_not_available_official_field_missing`, `balance_pagination_cap_exceeded`) 에서 exception 의 `str(exc)` 와 `repr(account_client)` 에 `"fake-key-XYZ"` / `"fake-secret-XYZ"` / `"12345678"` 가 등장하지 않는다.
- `test_get_account_sanitizes_response`: FakeAccountTransport 가 응답에 `{"appkey": "fake-key-XYZ", "access_token": "Bearer eyJ..."}` 같은 echo 를 포함. `result` 의 raw text dump 에서 sensitive 값이 `<redacted>` 로 마스킹.
- `test_get_account_sets_loaded_flags_correctly`: 성공 후 `is_loaded() True`, `positions_loaded()` 는 `get_positions()` 호출 전까지 False. `get_positions()` 성공 후 `positions_loaded() True`. `cash_balance_loaded()` 는 항상 False.
- `test_kis_broker_healthcheck_reflects_account_state`: `KisBroker` 생성 + `auth._store_token("fake-token", 120)` + FakeAccountTransport 주입 (테스트에서는 `broker._account._transport = FakeAccountTransport(...)` 로 주입). `broker.account.get_account()` 호출 후 `broker.healthcheck()["account_loaded"] is True`. `cash_balance_loaded is False` 유지.

회귀 / 안전 회귀 (기존 테스트 영향):

- `test_kis_http_boundaries.test_account_parsers_return_internal_models_and_sanitize`:
  - 입력 dict 를 catalog `Confirmed: yes` 필드명으로 갱신:
    ```python
    positions = broker.account.parse_positions_response({
        "rt_cd": "0",
        "output1": [
            {
                "ovrs_pdno": "AAPL",
                "ovrs_cblc_qty": "2",
                "pchs_avg_pric": "100.50",
                "ovrs_stck_evlu_amt": "201.00",
                "tr_crcy_cd": "USD",
                "ovrs_excg_cd": "NASD",
                # echoed secret-like keys must be redacted
                "appkey": "fake-key",
                "access_token": "Bearer XYZ",
            }
        ],
    })
    ```
  - 기대값을 `KisPosition(symbol="AAPL", quantity=2, avg_price=Decimal("100.50"), market_value=Decimal("201.00"), currency="USD", exchange="NASD")` 로 갱신.
  - `cash = broker.account.parse_cash_balance_response({...})` 호출은 더이상 happy path 가 아니므로 `pytest.raises(KisDataUnavailableError, match="paper_cash_balance_not_available")` 로 변경. `broker.account.cash_balance_loaded() is False` 확인.
  - `positions_loaded is True` 검증 유지.
  - 다른 assertion (sanitize / repr masking / no third-party HTTP / no live transport) 절대 변경 금지.
- `test_kis_http_boundaries.test_account_queries_require_authentication`:
  - `broker.account.get_cash_balance()` 가 여전히 `KisAuthError("authentication required")` 로 raise — auth gate 가 첫 번째이므로 기존 매칭 그대로 통과. 변경 없음.
- `test_kis_http_boundaries.test_kis_modules_do_not_import_third_party_http_libs` 변경 없음. `app/broker/kis.py` 가 `requests` / `httpx` / `aiohttp` / `urllib3` 를 import 하지 않음 — stdlib `urllib.request` / `urllib.parse` 만.
- `test_kis_http_boundaries.test_kis_http_has_no_live_transport_class` 변경 없음. `kis_http.py` 미변경.
- `test_kis_modules_do_not_import_http_libraries` (있다면) 변경 없음.
- `test_strategy_package_does_not_import_kis`, `test_agent_package_does_not_import_kis_if_present` 통과 — Strategy / Agent 가 `app.broker.kis` 를 import 하지 않는다.
- `test_api_paper_status.test_paper_status_kis_metadata_fields` 와 `test_paper_status_with_kis_config_masks_account` 통과 — startup 시 `_account_loaded` / `_positions_loaded` / `_cash_balance_loaded` 모두 False 유지 (auto-trigger 없음).
- `test_kis_capabilities`, `test_kis_order_preflight`, `test_kis_order_request_model`, `test_kis_order_response_model`, `test_kis_auth_client`, `test_kis_token_cache`, `test_kis_market_data_client`, `test_kis_quote_mapper`, `test_kis_api_mode`, `test_kis_config`, `test_kill_switch`, `test_broker_interface` 모두 통과 — 주문 / OAuth / 시세 / capability / kill switch / 기타 경로 동작 변경 없음.
- `test_missing_official_values_doc` (있다면) 통과 — 본 작업은 catalog 본문을 수정하지 않는다.
- `test_paper_e2e_*`, `test_paper_runner`, `test_paper_engine`, `test_oms`, `test_risk_engine`, `test_portfolio_service` 등 paper 경로 변경 없음.
- 모든 응답 / repr / exception / pytest capture 에 raw `fake-key` / `fake-secret` / `12345678` (단, 의도된 fixture 인용 외) / `Bearer` 토큰 원문이 등장하지 않는다.

검증 명령:

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

전체 PASS 가 완료 조건.

안전 grep (Codex 가 patch.md 에 결과 첨부):

```bash
grep -rnE "import (requests|httpx|aiohttp|urllib3)" app/broker
grep -rnE "from (requests|httpx|aiohttp|urllib3)" app/broker
grep -rn "TTTS3012R\|CTRP6504R\|CTRP6010R\|CTOS4001R\|TTTS3039R\|TTTC2101R" app tests
grep -rn "openapi.koreainvestment.com:9443" app tests
grep -rn "ALLOW_MARKET_ORDERS=true\|allow_market_orders=True" app
grep -rn "Bearer eyJ\|access_token=eyJ" app tests docs/ai/jobs/api-account-001
grep -rn "from app.broker.kis" app/strategy app/agent 2>/dev/null
```

기대 결과 — 외부 HTTP / 실전 TR_ID / 실전 base URL / market order 활성화 / 실토큰 / Strategy·Agent 의 KIS 직접 import 모두 0 lines.

## 6. 리뷰 체크리스트

안전 회귀:

- [ ] live trading 활성화 코드 / live broker API 호출 / 실주문 endpoint 가 추가되지 않았다.
- [ ] 실전 base URL (`https://openapi.koreainvestment.com:9443`) 호출 코드/문자열이 추가되지 않았다.
- [ ] 실전 TR_ID (`TTTS3012R` / `CTRP6504R` / `CTRP6010R` / `CTOS4001R` / `TTTS3039R` / `TTTC2101R`) 가 코드/테스트/문서에 추가되지 않았다.
- [ ] 모의투자 미지원 TR_ID (`TTTS3018R` / `CTRP6010R` / `CTOS4001R` / `TTTS3039R` / `TTTC2101R` / `TTTT3039R` / `TTTS3014R` / `TTTS6036U` / `TTTS6037U` / `TTTS6038U` / `TTTS6058R` / `TTTS6059R`) 가 추가되지 않았다.
- [ ] `OrderType.MARKET` 3중 가드 / `ALLOW_MARKET_ORDERS=true` 변경 / kill switch 변경 없음.
- [ ] `KisBroker.place_order` 가 dry-run 외에서는 여전히 NotImplementedError. 취소/replace/fills/open_orders/order_status 도 그대로 NotImplementedError.
- [ ] `app/broker/kis_http.py` 는 변경되지 않았다. `ALLOWED_PATHS_API_AUTH_001` 는 그대로 `{tokenP, revokeP}` 이며 계좌 path 가 추가되지 않았다.
- [ ] `UrllibAccountTransport` 가 host allowlist (모의 도메인 1 개) + path allowlist (`/uapi/overseas-stock/v1/trading/inquire-balance` 1 개) + method allowlist (`GET` 1 개) + TR_ID allowlist (`VTTS3012R` 1 개) + exchange allowlist (`NASD` / `NYSE` / `AMEX`) + currency allowlist (`USD` / `HKD` / `CNY` / `JPY` / `VND`) 를 강제한다.
- [ ] 외부 HTTP 라이브러리 (`requests`, `httpx`, `aiohttp`, `urllib3`) import 없음.
- [ ] secret / 계좌번호 / access token / Bearer 원문이 코드 / repr / exception message / 로그 / pytest capture 에 등장하지 않는다.
- [ ] `.env` / `.env.example` 수정되지 않았다. 새 env 변수 추가되지 않았다.
- [ ] Strategy / Agent / LLM 가 `app.broker.kis` 또는 `KisAccountClient` 를 직접 import 하지 않는다.

스코프 / 동작:

- [ ] `KisAccountClient.get_account(*, exchange="NASD", currency="USD")` 가 catalog `VTTS3012R` `Confirmed: yes` 필드 (`rt_cd`, `output1[]`, `output2`, `ctx_area_fk200`, `ctx_area_nk200`) 만 사용한다.
- [ ] `KisAccountClient.get_positions(*, exchange="NASD", currency="USD")` 가 `output1[].ovrs_pdno` / `ovrs_cblc_qty` / `pchs_avg_pric` / `ovrs_stck_evlu_amt` / `tr_crcy_cd` / `ovrs_excg_cd` 만 사용해 `KisPosition` 으로 매핑한다.
- [ ] `KisAccountClient.get_cash_balance()` 가 `KisDataUnavailableError("paper_cash_balance_not_available_official_field_missing")` 로 fail-closed. `_cash_balance_loaded` False 유지.
- [ ] `KisPosition` 에 `currency` 와 `exchange` 가 default 와 함께 추가되고 기존 위치 인자 호출이 후방 호환된다.
- [ ] `_split_kis_account_no` 가 `12345678-01` / `1234567801` 만 허용하고 그 외는 `KisConfigError`.
- [ ] 페이지 cap (`KIS_BALANCE_MAX_PAGES`) 이 강제되어 runaway pagination 이 차단된다.
- [ ] `_require_auth` 가 `_validate_paper_account_query` 보다 먼저 호출되어 기존 `KisAuthError("authentication required")` 회귀가 그대로 통과한다.
- [ ] FX 변환 함수 / 환율 상수 / base currency 통합 함수 도입 없음. 통화별 값은 통화별 호출로만 분리 보고.
- [ ] `parse_positions_response` 가 legacy domestic-stock 추측 필드 (`pdno` / `hldg_qty` / `qty` / generic `symbol` / `quantity` / `avg_price` / `market_value`) 를 더이상 인식하지 않는다.
- [ ] `parse_cash_balance_response` 가 fail-closed 로 통일됐다 (`KisDataUnavailableError`).
- [ ] `KisBroker.get_account()` / `get_positions()` 위임이 그대로 동작. `capabilities()` 변경 없음.
- [ ] `KisBroker.healthcheck()` 의 `account_loaded` / `positions_loaded` / `cash_balance_loaded` 가 `KisAccountClient` 의 flag 와 일치.

테스트 / 문서:

- [ ] `python -m compileall app tests` 통과.
- [ ] `python -m pytest -p no:cacheprovider` 전체 PASS.
- [ ] 신규 `tests/test_kis_account_client.py` 가 happy / pagination / error / sanitization / multi-currency / secret leak / fail-closed 회귀를 모두 검증한다.
- [ ] `tests/test_kis_http_boundaries.py` 의 `test_account_parsers_return_internal_models_and_sanitize` 만 catalog 필드명으로 fixture 갱신됐고, 다른 테스트는 절대 변경되지 않았다.
- [ ] `docs/ai/jobs/api-account-001/patch.md` 에 변경 파일 / 사용 endpoint·TR_ID 출처 / 구현 범위 / fail-closed 범위 / secret 회귀 / safety 회귀 / 테스트 결과 / 안전 grep 결과 / Claude 검증 요청 프롬프트 / follow-up Codex 프롬프트 규칙이 모두 포함됐다.

자동화 금지:

- [ ] commit / push / merge / PR / deploy 가 수행되지 않았다.
- [ ] `.env` / secret / credential / API key / token 이 수정/노출되지 않았다.
- [ ] `docs/kis/MISSING_OFFICIAL_VALUES.md` 가 수정되지 않았다.
