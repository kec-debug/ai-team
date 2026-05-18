# api-market-data-001 — KIS 해외주식 현재체결가 기반 Quote 구현

## 1. 요청 요약

`docs/kis/MISSING_MARKET_DATA_VALUES.md` 가 공식값으로 채워지면서 KIS 해외주식 현재체결가의 endpoint·TR ID·EXCD 코드·요청 헤더·query 파라미터·응답 필드가 `Confirmed: yes` 로 확정됐다. 본 작업은 `KisMarketDataClient.get_quote()` 의 본문을 구현해서, 모의 도메인 `https://openapivts.koreainvestment.com:29443` 의 `GET /uapi/overseas-price/v1/quotations/price` (TR ID `HHDFS00000300`) 호출 결과를 broker-agnostic `Quote` 도메인 모델로 매핑한다.

핵심 제약:

- 현재체결가에는 bid/ask 가 없다. Quote 모델에서 명시적으로 안전하게 처리한다.
- 현재체결가에는 거래소 timestamp 가 없다. 응답 수신 시각을 timestamp 로 보수적으로 사용한다.
- 외부 HTTP 라이브러리 (`requests`, `httpx`, `aiohttp`, `urllib3`) 금지. stdlib `urllib.request` 만 사용.
- KIS endpoint / TR ID / payload / header 추측 금지. catalog 의 `Confirmed: yes` 항목만 사용.
- `HHDFS00000300` 외 TR ID 사용 금지.
- live trading / 실주문 / 주문 endpoint 구현 금지. 기존 paper / dry-run 안전 경계는 변동 없음.
- secret · 계좌번호 · access token · Bearer token 은 코드 / 로그 / 테스트 / patch / docstring 어디에도 기록 금지.
- `.env` 읽기 / 수정 금지.
- GUI (`app/api/*`, `app/static/*`, `app/main.py`) 변경 금지. 단 dashboard 가 이미 `/paper/status` 의 `kis_market_data_available` 을 보고 있으므로, `healthcheck_market_data()` 의 값 변화만으로 표시가 갱신되도록 한다 (API 변경 없음).

## 2. 작업 범위

포함하는 것:

- `app/domain/quote.py`: `bid_ask_present: bool = True` 필드 추가 (default True, 기존 호출 전부 후방 호환). 검증 규칙은 그대로 (`bid > 0`, `ask >= bid`).
- `app/broker/kis_quote_mapper.py`: `kis_raw_quote_to_domain(raw, symbol, *, received_at, source="kis_paper", currency="USD", session=None) -> Quote` 구현. 현재체결가 응답 `output.last` 와 `output.tvol` 로 Quote 생성. `bid = ask = last` (synthetic), `bid_ask_present=False`, `timestamp = received_at`. `rsym` 이 있으면 파싱해서 symbol 일치를 검증 (불일치 시 입력 symbol 우선).
- `app/broker/kis.py`:
  - 신규 `KisMarketDataTransport` Protocol (모듈 내부 정의).
  - 신규 `UrllibMarketDataTransport` (stdlib `urllib.request` GET, host/path/method/TR ID allowlist 1개씩).
  - 신규 `MockMarketDataTransport` (mock 모드용, 호출 시 `KisDataUnavailableError("mock_mode_no_network")`).
  - `KisMarketDataClient.__init__` 에 `transport: KisMarketDataTransport | None = None` 추가 (테스트 주입용). 기본값은 `kis_api_mode` 에 따라 위 두 transport 중 선택.
  - `KisMarketDataClient.get_quote(symbol, *, exchange: str = "NAS") -> Quote` 본문 구현. 검증 → 인증 확인 → transport.get_quote 호출 → mapper 로 Quote 변환 → 반환.
  - `KisMarketDataClient.get_last_price(symbol, *, exchange: str = "NAS") -> Decimal` 가 `quote.last` 반환.
  - `KisMarketDataClient.healthcheck_market_data()` 업데이트: `connected` = transport 가 mock 이 아닐 때 True, `available` = `connected and auth.is_authenticated()`, `reason` = mock/auth/ready 분기.
  - `KisBroker.get_quote(symbol)` 반환 타입을 `Quote` 로 변경 (내부적으로 동일 메서드 위임). 기존 호출 (`test_broker_interface`, `test_kis_http_boundaries`) 가 영향을 받으므로 plan §3 에서 명시.
- 테스트 갱신/추가 (자세한 항목은 §5).
- README 한 줄 갱신.

제외 (절대 안 하는 것):

- live trading 활성화 / `LIVE_TRADING_ENABLED=true` 변경 / live broker API 구현.
- 주문 / 취소 / 잔고 / 체결 endpoint 구현. `KisAccountClient`, `KisBroker.place_order/cancel/replace` 등 NotImplementedError 유지.
- `OrderType.MARKET` 가드 우회. `ALLOW_MARKET_ORDERS=true` 변경. kill switch 변경.
- 외부 HTTP 라이브러리 import. `urllib3` 도 금지 (stdlib `urllib.request` 만).
- `HHDFS00000300` 외 TR ID. `HHDFS76200100`(호가), `HHDFS76200200`(현재가상세), `HHDFS76220000`(복수종목) 등을 코드/문서에 추가하지 않는다.
- 실전 도메인 (`openapi.koreainvestment.com:9443`) 호출. 본 작업은 모의 도메인 (`openapivts.koreainvestment.com:29443`) 만 사용 (catalog 의 "모의 도메인 — 해외주식 현재체결가" 행과 일치).
- 새 env 변수 추가. `KIS_MARKET_DATA_APP_KEY` 등 catalog 가 언급한 후속 변수는 별 job 으로.
- `.env` / secret 파일 변경.
- `app/api/`, `app/static/`, `app/main.py`, `app/broker/kis_http.py`, `app/broker/kis_token_cache.py`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/oms/`, `app/risk/`, `app/portfolio/`, `app/runtime/`, `app/strategy/`, `app/session/`, `app/config.py` 변경.
- Strategy / Agent / LLM 이 `app.broker.kis` 를 직접 import 하는 경로 추가 (`test_strategy_package_does_not_import_kis` / `test_agent_package_does_not_import_kis_if_present` 회귀 유지).
- 자동 git commit / push / merge / deploy.

## 3. 수정해야 할 파일

후방 호환 정책:

- 기존 `Quote(symbol, last, bid, ask, volume, timestamp, source, session, currency)` 위치 인자 호출은 모두 그대로 동작한다. 신규 `bid_ask_present: bool = True` 는 끝에 추가하여 default 사용 시 기존 동작과 동일.
- 기존 `kis_raw_quote_to_domain(raw, symbol, source="kis_paper")` 호출은 `received_at` 이 필수가 되므로 시그니처가 바뀐다. 단, 기존 호출 site 는 mapper 의 NotImplementedError 테스트뿐이며, 본 작업에서 해당 테스트를 갱신한다. mapper 외부 호출은 없다.
- `KisMarketDataClient.get_quote(symbol)` 가 `dict` → `Quote` 로 변경된다. 호출 site 는 `KisBroker.get_quote`, `test_kis_market_data_client`, `test_kis_http_boundaries`, `test_broker_interface`. 모두 본 작업 범위에서 갱신.

| 경로 | 변경 종류 | 요약 |
| --- | --- | --- |
| `projects/paper-trading/app/domain/quote.py` | MODIFY | `bid_ask_present: bool = True` 필드 추가. `__post_init__` 변경 없음 (synthetic bid==ask==last 케이스는 기존 invariant 통과). docstring 한 줄. |
| `projects/paper-trading/app/broker/kis_quote_mapper.py` | MODIFY | `kis_raw_quote_to_domain(raw, symbol, *, received_at, source="kis_paper", currency="USD", session=None) -> Quote` 구현. NotImplementedError 제거. raw 검증 (`rt_cd`/`output`/`output.last`/`output.tvol`). `rsym` 파싱 helper. fail-closed (잘못된 입력은 ValueError). |
| `projects/paper-trading/app/broker/kis.py` | MODIFY | (1) `KisMarketDataTransport` Protocol. (2) `UrllibMarketDataTransport` (host/path/method/TR ID allowlist 1개). (3) `MockMarketDataTransport`. (4) `KisMarketDataClient.__init__(...)` 에 transport 주입. (5) `get_quote(symbol, *, exchange="NAS") -> Quote` 본문. (6) `get_last_price(symbol, *, exchange="NAS") -> Decimal` 본문. (7) `healthcheck_market_data()` 업데이트. (8) `KisBroker.get_quote` 반환 타입을 Quote 로. (9) `KisHttpClient.request` 는 그대로 NotImplementedError 유지 (시장데이터는 별도 transport 사용). 다른 broker 메서드 (주문/계좌/취소/replace/fills 등) 동작은 변경 금지. |
| `projects/paper-trading/tests/test_kis_market_data_client.py` | MODIFY | NotImplementedError-only 테스트를 실동작 테스트로 재작성. 자세한 항목은 §5. |
| `projects/paper-trading/tests/test_kis_quote_mapper.py` | MODIFY | NotImplementedError 테스트를 실동작 테스트로 재작성. |
| `projects/paper-trading/tests/test_quote_model.py` | MODIFY | `bid_ask_present` 기본값 True, 명시 False 허용 (synthetic bid==ask==last), frozen 유지 검증. 기존 검증 테스트는 그대로. |
| `projects/paper-trading/tests/test_kis_http_boundaries.py` | MODIFY (좁은 범위) | `test_market_data_requires_auth_before_unimplemented_endpoint` 의 두 번째 assertion 만 새 동작 (`KisDataUnavailableError("mock_mode_no_network")`) 에 맞게 갱신. **다른 테스트 (주문/취소/replace/auth/account/HTTP lib 금지 등) 는 절대 변경 금지.** |
| `projects/paper-trading/tests/test_broker_interface.py` | MODIFY (좁은 범위) | `test_kis_healthcheck_returns_disconnected_dict` 의 `reason` 매칭만 새 표현 (`"skeleton" in reason or "not implemented" in reason or "mock_mode_no_network" in reason or "authentication_required" in reason`) 으로 갱신. `test_kis_data_methods_not_implemented` 가 `get_quote("AAPL")` 에 대해 `KisAuthError("authentication required")` 를 기대하는 부분은 그대로 통과 (auth 게이트 유지). 다른 테스트 변경 금지. |
| `projects/paper-trading/README.md` | MODIFY | KIS market data 섹션 (있다면) 또는 KIS 관련 섹션에 1-2 줄 안내 추가. 새 env 변수 안내 금지. |
| `projects/paper-trading/docs/ai/jobs/api-market-data-001/patch.md` | NEW (Codex 가 작성) | 변경 요약 + 테스트 결과. |

**범위 확장 사유** (request 의 "수정 가능 파일" 목록 외 추가):

- `tests/test_kis_http_boundaries.py` 와 `tests/test_broker_interface.py` 는 현재 "get_quote 호출 시 NotImplementedError 또는 skeleton reason" 을 강제하는 회귀 테스트를 포함한다. 본 작업이 실 구현으로 전환하므로 해당 assertion 만 갱신하지 않으면 "전체 pytest 통과" 조건을 만족할 수 없다. 두 파일은 각 1 개 함수의 1-2 줄 assertion 만 좁게 변경한다. 다른 보안/회귀 assertion (third-party HTTP 금지, mock mode, no live transport, place_order NotImplementedError, sanitize, repr masking 등) 은 절대 건드리지 않는다.

손대지 않는 파일 (대표적):

- `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/base.py`.
- `app/broker/kis_http.py` (SafeKisHttpClient, MockTransport, UrllibTransport, ALLOWED_PATHS_API_AUTH_001 등은 OAuth 전용 그대로 유지. 시장데이터 transport 는 `kis.py` 내부에 별도 정의).
- `app/broker/kis_token_cache.py`.
- `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/main.py`, `app/api/*`, `app/static/*`.
- `app/config.py` (새 env 추가 금지).
- `app/domain/enums.py`, `app/domain/orders.py`, `app/domain/fills.py`, `app/domain/market.py` (Quote 외 domain 변경 금지).
- `docs/kis/*` (catalog 자체는 본 작업에서 수정하지 않는다; 본 작업은 catalog 의 `Confirmed: yes` 행만 소비).
- `.env`, `.env.example`.

## 4. Codex 구현 지시문

자세한 단계는 `codex-task.md` 에 기록한다. 요지:

### 4.1 Quote 모델 변경 (`app/domain/quote.py`)

- 신규 필드: `bid_ask_present: bool = True` (currency 뒤). 새 필드는 default 가 있어 기존 위치 인자 호출/dataclass 직렬화에 영향 없음.
- `__post_init__` 변경 없음. synthetic case (bid == ask == last) 는 기존 invariant 통과 (`bid > 0`, `ask >= bid`).
- docstring 1 줄 보강.

### 4.2 Quote mapper (`app/broker/kis_quote_mapper.py`)

```python
def kis_raw_quote_to_domain(
    raw: dict[str, Any] | None,
    symbol: str,
    *,
    received_at: datetime,
    source: str = "kis_paper",
    currency: str = "USD",
    session: Session | None = None,
) -> Quote:
    ...
```

요구사항:

- `raw is None` → `ValueError("raw quote payload is None")`.
- `symbol` 빈 문자열 → `ValueError("symbol must be non-empty")`. 대문자 정규화는 호출측이 보장하지만 mapper 도 `symbol.strip().upper()` 적용.
- `received_at.tzinfo` 가 없으면 → `ValueError("received_at must be timezone-aware")`.
- `raw.get("rt_cd")` 가 `"0"` 이 아니면 → `ValueError("kis_error:<msg_cd or msg1>")` (호출측 transport 가 이미 검증하지만 방어적으로 한 번 더).
- `output = raw.get("output")` 가 dict 가 아니면 → `ValueError("malformed_response: output missing")`.
- `last_str = output.get("last")`. `tvol_str = output.get("tvol")`. 둘 중 하나라도 없거나 빈 문자열 → `ValueError("malformed_response: last or tvol missing")`.
- `last = Decimal(str(last_str).replace(",", ""))`. `last <= 0` → `ValueError("malformed_response: last not positive")`.
- `volume = int(Decimal(str(tvol_str).replace(",", "")))`. `volume < 0` → `ValueError("malformed_response: volume negative")`.
- 옵션: `rsym = output.get("rsym")` 가 있으면 `D{EXCD3자리}{SYMB}` 형태로 파싱해 symbol 검증. 불일치하면 입력 symbol 우선 (warning 로그 없음 — 로그 금지 정책). 파싱 실패는 무시.
- Quote 생성: `Quote(symbol=symbol_upper, last=last, bid=last, ask=last, volume=volume, timestamp=received_at, source=source, session=session, currency=currency, bid_ask_present=False)`.
- `source` 가 빈 문자열이면 ValueError ("source must be non-empty") — 이는 Quote.__post_init__ 에서 강제.

### 4.3 KIS market data transport (`app/broker/kis.py`)

전역 상수:

```python
KIS_OVERSEAS_PRICE_PATH = "/uapi/overseas-price/v1/quotations/price"
KIS_OVERSEAS_PRICE_TR_ID = "HHDFS00000300"
KIS_PAPER_MARKET_DATA_HOSTS = frozenset({"openapivts.koreainvestment.com:29443"})
KIS_ALLOWED_EXCHANGES = frozenset(
    {"HKS", "NYS", "NAS", "AMS", "TSE", "SHS", "SZS", "SHI", "SZI",
     "HSX", "HNX", "BAY", "BAQ", "BAA"}
)
```

Protocol:

```python
class KisMarketDataTransport(Protocol):
    def get_quote(
        self,
        *,
        base_url: str,
        access_token: str,
        app_key: str,
        app_secret: str,
        exchange: str,
        symbol: str,
    ) -> tuple[dict[str, Any], datetime]:
        ...
```

반환은 `(raw_response_dict, received_at_utc)`.

`UrllibMarketDataTransport`:

- `timeout_seconds: float`, `max_retries: int`, `backoff_seconds: float` 필드.
- `get_quote(...)`:
  - host = `_extract_host(base_url)` (kis_http.py 의 동일 헬퍼를 재정의하거나 `urllib.parse.urlsplit` 사용). host 가 `KIS_PAPER_MARKET_DATA_HOSTS` 에 없으면 `KisDataUnavailableError("disallowed_host")`.
  - exchange 가 `KIS_ALLOWED_EXCHANGES` 에 없으면 `KisDataUnavailableError("invalid_exchange")`.
  - URL: `f"{base_url.rstrip('/')}{KIS_OVERSEAS_PRICE_PATH}?AUTH=&EXCD={exchange}&SYMB={urllib.parse.quote(symbol)}"`. `AUTH` 는 catalog 의 "공백 또는 Null" 정책에 따라 빈 문자열.
  - headers: `{"content-type": "application/json; charset=utf-8", "authorization": f"Bearer {access_token}", "appkey": app_key, "appsecret": app_secret, "tr_id": KIS_OVERSEAS_PRICE_TR_ID}`.
  - GET 만 사용. body 없음.
  - retry: 5xx 또는 transport error 시 `max_retries` 까지 (1 회 권장). `socket.timeout`, `TimeoutError`, `URLError` 처리.
  - 응답 JSON 파싱 실패 → `KisDataUnavailableError("invalid_response_body")`.
  - `rt_cd != "0"` → `KisDataUnavailableError(f"kis_error:{msg_cd or msg1 or 'unknown'}")`.
  - 정상 응답이면 `(response_dict, datetime.now(timezone.utc))` 반환.
  - **로그 금지**: access_token / app_key / app_secret / Authorization 헤더를 stdout / stderr / repr / exception message 에 절대 포함하지 말 것. raised exception 의 `__cause__` 는 urllib 의 HTTPError/URLError 인스턴스가 될 수 있는데, 이를 그대로 노출하지 말고 안전 메시지로 래핑.

`MockMarketDataTransport`:

- `get_quote(...)` → `raise KisDataUnavailableError("mock_mode_no_network")`.

### 4.4 `KisMarketDataClient` 본문

```python
class KisMarketDataClient:
    def __init__(
        self,
        settings: Settings,
        auth: KisAuthClient,
        transport: KisMarketDataTransport | None = None,
    ) -> None:
        self._settings = settings
        self._auth = auth
        self._last_error: str | None = None
        if transport is not None:
            self._transport = transport
        else:
            mode = KisApiMode.parse(settings.kis_api_mode)
            if mode is KisApiMode.MOCK:
                self._transport = MockMarketDataTransport()
            else:
                self._transport = UrllibMarketDataTransport(
                    timeout_seconds=settings.kis_oauth_timeout_seconds,
                    max_retries=settings.kis_oauth_max_retries,
                )

    def get_quote(self, symbol: str, *, exchange: str = "NAS") -> Quote:
        normalized = self._validate_symbol(symbol)
        if not self._auth.is_authenticated():
            self._last_error = "authentication_required"
            raise KisAuthError("KIS authentication required")
        access_token = self._auth.get_access_token()
        if not access_token:
            self._last_error = "authentication_required"
            raise KisAuthError("KIS authentication required")
        try:
            raw, received_at = self._transport.get_quote(
                base_url=self._settings.kis_base_url_paper,
                access_token=access_token,
                app_key=self._settings.kis_app_key or "",
                app_secret=self._settings.kis_app_secret or "",
                exchange=exchange,
                symbol=normalized,
            )
        except KisDataUnavailableError as exc:
            self._last_error = str(exc)
            raise
        try:
            quote = kis_raw_quote_to_domain(
                raw,
                symbol=normalized,
                received_at=received_at,
                source="kis_paper",
                currency="USD",
            )
        except ValueError as exc:
            self._last_error = f"malformed_response:{exc}"
            raise KisDataUnavailableError(self._last_error) from exc
        self._last_error = None
        return quote

    def get_last_price(self, symbol: str, *, exchange: str = "NAS") -> Decimal:
        quote = self.get_quote(symbol, exchange=exchange)
        return quote.last

    def healthcheck_market_data(self) -> dict[str, Any]:
        mock = isinstance(self._transport, MockMarketDataTransport)
        auth_present = self._auth.is_authenticated()
        connected = not mock
        available = connected and auth_present
        if mock:
            reason = "mock_mode_no_network"
        elif not auth_present:
            reason = "authentication_required"
        else:
            reason = "ready"
        return {
            "connected": connected,
            "available": available,
            "reason": reason,
            "auth_required": True,
            "auth_present": auth_present,
            "last_error": self._last_error,
        }
```

`__repr__` 은 secret 노출 금지를 유지하기 위해 다음 형태:

- mock 모드: `"KisMarketDataClient(<mock>)"`.
- paper 모드: `"KisMarketDataClient(<paper, urllib>)"`.

기존 `"disconnected"` 문자열은 더 이상 항상 정확하지 않으므로 위처럼 변경. (테스트가 `"disconnected"` 를 강제하지 않게 본 작업의 test 갱신에서 함께 처리. `test_market_data_repr_does_not_expose_secrets` 의 `"disconnected" in text` assertion 은 `"mock" in text or "paper" in text` 로 좁게 갱신.)

### 4.5 `KisBroker.get_quote`

- 시그니처 변경: `def get_quote(self, symbol: str, *, exchange: str = "NAS") -> Quote: return self._market_data.get_quote(symbol, exchange=exchange)`.
- 기존 `dict[str, Any]` 타입 힌트를 `Quote` 로 변경.
- 다른 메서드 (`place_order`, `cancel_order`, `replace_order`, `get_account`, `get_positions`, `get_fills`, `get_open_orders`, `get_order_status`, `capabilities`, `healthcheck`) 동작 변경 없음.

### 4.6 Healthcheck dashboard 표시

- `app/api/routes.py:131` 의 `kis_market_data_available` 은 `kis_health.get("market_data", {})["connected"]` 를 그대로 사용 (`bool(...)`). 본 작업에서는 routes.py 변경 없음. 새 reason 문자열 (`mock_mode_no_network`, `authentication_required`, `ready`) 은 `last_broker_error` / `last_error` 필드를 통해서만 노출되지 않으므로, dashboard 에서 reason 직접 표시는 후속 작업으로 분리. `test_api_paper_status` 가 `kis_market_data_available is False` 를 강제하므로, 인증되지 않은 기본 상태에서 `connected` 가 False 여야 한다. paper mode (urllib) 에서도 auth 가 없으면 `connected` 는 True 지만 `available` 은 False 다 — `kis_market_data_available` 은 `connected` 만 본다. 이 의미 차이를 다음 항으로 보정.

**중요한 회귀**: 기존 `test_api_paper_status.py:59,105` 가 `kis_market_data_available is False` 를 강제한다. 새 `healthcheck_market_data` 에서 paper-mode urllib 트랜스포트 + 인증 미존재 상태는 `connected=True` 가 되어 `kis_market_data_available=True` 가 된다. 이는 회귀다.

→ 해결: `kis_market_data_available` 의 의미를 "auth 까지 통과해 실제로 시세를 받을 수 있는가" 로 일치시킨다. `connected` 의 의미를 "transport 가 mock 이 아님" 으로 둘 거면, `kis_market_data_available` 은 `connected and available` 또는 `available` 만 봐야 한다.

가장 안전하고 routes.py 를 건드리지 않는 방안: `healthcheck_market_data()["connected"]` 의 정의를 **"transport 가 mock 이 아니고 + auth 가 있을 때"** 로 정한다 (`connected = (not mock) and auth_present`). `available` 은 `connected` 와 동의어로 둔다.

→ 위 코드의 `connected` 정의를 `connected = (not mock) and auth_present` 로 수정.

→ test_kis_broker_healthcheck_returns_disconnected_dict 와 test_api_paper_status 가 auth 없는 상태에서 `connected` False 를 그대로 기대하므로 회귀 통과.

(plan 의 코드 블록은 가이드이며 codex-task.md 에서 위 정정을 반영한 최종 형태로 명시한다.)

### 4.7 secret / repr / 로그

- `__repr__` 가 `app_key`, `app_secret`, `access_token`, `kis_account_no` 의 원문을 절대 포함하지 않는다.
- 예외 메시지에 secret 을 포함하지 않는다. urllib `HTTPError` 의 `read()` body 에 KIS 가 secret echo 를 보낼 가능성은 낮지만, 본 transport 는 body 를 그대로 메시지에 넣지 않고 `http_<code>` 또는 `transport_error` 등 단축 메시지만 사용한다.
- pytest 에서 capture 된 stdout/stderr 에 secret 이 등장하지 않는다 (`test_*_does_not_expose_secrets` 식 회귀 유지).
- `KisHttpError`/`KisAuthError` 의 message 와 `last_error` 필드는 short tag (`mock_mode_no_network`, `authentication_required`, `disallowed_host`, `invalid_exchange`, `http_404`, `transport_error`, `kis_error:<msg_cd>`, `malformed_response:<reason>`) 만 사용.

## 5. 테스트 기준

신규 / 갱신 테스트:

`tests/test_quote_model.py` (갱신):

- 기본 happy path: `bid_ask_present` default True.
- `Quote(symbol, last, last, last, volume, ts, "kis_paper", bid_ask_present=False)` 가 invariant 통과.
- frozen 유지: `q.bid_ask_present = True` 가 `FrozenInstanceError`.
- 기존 invariant 테스트 (last/bid/ask/volume/source/timestamp/uppercase) 그대로.

`tests/test_kis_quote_mapper.py` (갱신, NotImplementedError 테스트 제거):

- raw=None → ValueError.
- symbol="" → ValueError.
- received_at naive datetime → ValueError.
- raw 가 dict 가 아닌 경우 (예: list) → ValueError.
- raw.rt_cd != "0" → ValueError("kis_error:...").
- raw.output 누락 → ValueError("malformed_response: output missing").
- output.last 누락 또는 "" → ValueError.
- output.tvol 누락 또는 "" → ValueError.
- output.last 가 음수 → ValueError.
- output.last="100.50", output.tvol="1000000" → Quote(last=Decimal("100.50"), bid=Decimal("100.50"), ask=Decimal("100.50"), volume=1000000, bid_ask_present=False, source="kis_paper", currency="USD").
- output.rsym="DNASAAPL" + 입력 symbol="AAPL" → 일치 OK.
- output.rsym="DNYS TSLA" 등 비정상 → 입력 symbol 우선, 예외 없음.
- 쉼표 포함 가격 ("1,234.56") 도 Decimal 로 파싱.

`tests/test_kis_market_data_client.py` (갱신, NotImplementedError 테스트 제거):

- 헬퍼: `FakeMarketDataTransport` 가 고정 응답 또는 예외를 반환.
- `get_quote("AAPL")` no auth → `KisAuthError("KIS authentication required")`. `last_error == "authentication_required"`.
- mock-mode 기본 (transport 자동 선택) + auth 있음 → `KisDataUnavailableError("mock_mode_no_network")`.
- Fake transport 가 정상 응답 + auth 있음 → 반환은 `Quote`. `quote.last == Decimal("100.50")`, `quote.volume == 1000000`, `quote.bid == quote.ask == quote.last`, `quote.bid_ask_present is False`, `quote.source == "kis_paper"`.
- Fake transport 가 KisDataUnavailableError("kis_error:EFGS9999") → 그대로 전파, `last_error == "kis_error:EFGS9999"`.
- Fake transport 가 정상이지만 mapper 가 ValueError → `KisDataUnavailableError("malformed_response:...")` 로 변환.
- `get_quote("bad symbol!")` → `KisDataUnavailableError("invalid_symbol")` 변동 없음.
- `exchange="LSE"` (allowlist 외) → Fake transport 의존이지만 실제 UrllibMarketDataTransport 에서는 `KisDataUnavailableError("invalid_exchange")`. 본 테스트에서는 UrllibMarketDataTransport 인스턴스를 직접 만들어 검증.
- `get_last_price("AAPL", exchange="NAS")` → Decimal.
- `healthcheck_market_data()`:
  - mock 모드 기본: `connected False`, `available False`, `reason == "mock_mode_no_network"`.
  - paper 모드 + auth 없음 + UrllibMarketDataTransport 주입: `connected False`, `reason == "authentication_required"`.
  - paper 모드 + auth 있음: `connected True`, `available True`, `reason == "ready"`.
- `repr(market_data)` 가 fake-key / fake-secret / 계좌번호 / access_token 원문을 포함하지 않는다. "mock" 또는 "paper" 마커 포함.

`tests/test_kis_quote_mapper.py` 의 추가:

- `kis_raw_quote_to_domain` 가 `Quote` 의 invariant 위반 (e.g. last=0) 시 ValueError.

`tests/test_kis_http_boundaries.py` (좁은 갱신):

- `test_market_data_requires_auth_before_unimplemented_endpoint`:
  - 첫 번째 assertion (auth 없음 → KisAuthError) 유지.
  - 두 번째 assertion 만: `with pytest.raises(KisDataUnavailableError, match="mock_mode_no_network"): broker.get_quote("AAPL")` 로 변경. (auth 토큰 저장 후 mock-mode 트랜스포트가 fail-closed.)
- 다른 테스트 (KIS_HTTP no live transport, third-party HTTP lib forbidden, place_order, cancel_order, replace_order, get_open_orders, get_fills, get_order_status, account parsers, OAuth, secret sanitation 등) 절대 변경 금지.

`tests/test_broker_interface.py` (좁은 갱신):

- `test_kis_healthcheck_returns_disconnected_dict`:
  - `reason = h["market_data"]["reason"].lower()` 다음 줄을:
    `assert any(needle in reason for needle in ("skeleton", "not implemented", "mock_mode_no_network", "authentication_required"))` 로 갱신.
  - 다른 assertion (`h["broker"] == "KisBroker"`, `connected is False` 등) 절대 변경 금지.
- `test_kis_data_methods_not_implemented` 는 `broker.get_quote("AAPL")` 에 대해 `KisAuthError` 를 기대 — 그대로 통과 (auth 게이트 유지).
- 다른 테스트 변경 금지.

`tests/test_api_paper_status.py` (변경 없음):

- `body["kis_market_data_available"] is False` 가 유지되려면 `kis_health["market_data"]["connected"]` 가 False 여야 한다. `connected = (not mock) and auth_present` 정의로 paper-mode + no-auth → False, mock-mode → False. 두 케이스 모두 회귀 통과.

회귀 / 안전 회귀:

- `test_kis_modules_do_not_import_third_party_http_libs` 통과 — kis.py / kis_quote_mapper.py 가 `requests`/`httpx`/`aiohttp`/`urllib3` 를 import 하지 않는다. `urllib.request` 와 `urllib.parse` 만 사용.
- `test_kis_module_does_not_import_http_libraries` 통과.
- `test_kis_http_has_no_live_transport_class` 통과 (kis_http.py 변경 없음).
- `test_strategy_package_does_not_import_kis`, `test_agent_package_does_not_import_kis_if_present` 통과 (Strategy / Agent 가 `app.broker.kis` 를 import 하지 않는다).
- `test_paper_e2e_*` (paper 엔진 / OMS / RiskEngine 회귀) 통과 — 본 작업이 paper 경로를 건드리지 않음.
- `test_kis_order_preflight`, `test_kis_capabilities` 통과 (주문/취소/replace 동작 변경 없음).
- 모든 응답/repr 에 raw `fake-key`/`fake-secret`/계좌번호 (fixture 의 `12345678`/`fake-acc`)/`Bearer` 토큰 원문이 등장하지 않는다.

검증 명령:

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

전체 PASS 가 완료 조건.

## 6. 리뷰 체크리스트

안전 회귀:

- [ ] live trading 활성화 코드 / live broker API 호출 / 실주문 endpoint 가 추가되지 않았다.
- [ ] `OrderType.MARKET` 3중 가드 / `ALLOW_MARKET_ORDERS=true` 변경 / kill switch 변경 없음.
- [ ] `KisBroker.place_order` 가 dry-run 외에서는 여전히 `NotImplementedError("...order endpoint...")`. 취소/replace/fills/get_order_status 도 그대로 NotImplementedError.
- [ ] `app/broker/kis_http.py` 는 변경되지 않았다. `ALLOWED_PATHS_API_AUTH_001` 는 그대로 `{tokenP, revokeP}` 이며 시장데이터 path 가 추가되지 않았다.
- [ ] 시장데이터 transport 가 host allowlist (모의 도메인 1 개) 와 path allowlist (`/uapi/overseas-price/v1/quotations/price` 1 개) 와 TR ID allowlist (`HHDFS00000300` 1 개) 와 method allowlist (`GET` 1 개) 를 강제한다.
- [ ] `HHDFS76200100`/`HHDFS76200200`/`HHDFS76220000`/주문 TR ID 등 다른 식별자가 코드/문서/테스트에 추가되지 않았다.
- [ ] 외부 HTTP 라이브러리 (`requests`, `httpx`, `aiohttp`, `urllib3`) import 없음.
- [ ] secret/계좌번호/access token/Bearer 원문이 코드/repr/exception message/로그/테스트 캡처에 등장하지 않는다.
- [ ] `.env` 가 수정되지 않았다. 새 env 변수가 추가되지 않았다.

스코프 / 동작:

- [ ] `Quote` 모델은 신규 `bid_ask_present: bool = True` 1 개 필드만 추가. invariant 변동 없음. 기존 Quote 호출 모두 후방 호환.
- [ ] `kis_quote_mapper.kis_raw_quote_to_domain` 가 catalog 의 `Confirmed: yes` 필드 (`output.last`, `output.tvol`, `output.rsym`, `rt_cd`) 만 사용하며 `bid = ask = last`, `bid_ask_present=False`, `timestamp=received_at` 으로 매핑.
- [ ] `KisMarketDataClient.get_quote` 가 인증 → transport → mapper → Quote 의 4 단계로 동작하고 모든 실패가 `KisAuthError` 또는 `KisDataUnavailableError` 로 fail-closed.
- [ ] `KisBroker.get_quote` 가 `Quote` 를 반환한다.
- [ ] `healthcheck_market_data()` 가 mock/auth/ready 3 상태를 reason 으로 보고하며, `connected = (not mock) and auth_present` 정의를 따른다.
- [ ] Strategy / Agent 가 `app.broker.kis` 또는 `app.broker.kis_quote_mapper` 를 import 하지 않는다.
- [ ] `app/api/*`, `app/static/*`, `app/main.py` 변경 없음.

테스트 / 문서:

- [ ] `python -m compileall app tests` 통과.
- [ ] `python -m pytest -p no:cacheprovider` 전체 PASS.
- [ ] `test_kis_market_data_client.py`, `test_kis_quote_mapper.py`, `test_quote_model.py` 가 실동작·실패 경로·secret leak 회귀를 검증.
- [ ] `test_kis_http_boundaries.py` 와 `test_broker_interface.py` 가 좁은 범위 (각각 1 개 함수의 1-2 줄 assertion) 만 갱신됐고 그 외 assertion 모두 그대로.
- [ ] README 가 1-2 줄로 신규 동작을 안내. 새 env 변수 안내 없음.
- [ ] `docs/ai/jobs/api-market-data-001/patch.md` 에 변경 파일/테스트 결과/안전 회귀 항목이 요약돼 있다.

자동화 금지:

- [ ] commit / push / merge / PR / deploy 가 수행되지 않았다.
- [ ] `.env` / secret / credential / API key / token 이 수정/노출되지 않았다.
