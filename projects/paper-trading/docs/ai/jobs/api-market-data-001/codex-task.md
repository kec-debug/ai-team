# Codex 작업 지시문 — api-market-data-001

## 0. 너의 역할

너는 Codex 구현자다. 이 문서와 `plan.md` 만 따른다. 범위를 임의로 넓히지 않는다. 안전 규칙을 위반하지 않는다. commit / push / merge / deploy 는 절대 하지 않는다. `.env`, secret, API key, token, 계좌번호 raw 값을 읽지도 쓰지도 노출하지도 않는다.

## 1. 컨텍스트 요약

`docs/kis/MISSING_MARKET_DATA_VALUES.md` 에 KIS 해외주식 시세 catalog 가 `Confirmed: yes` 로 확정됐다. 본 작업은 `KisMarketDataClient.get_quote(symbol, *, exchange="NAS")` 본문을 구현해, 모의 도메인 `https://openapivts.koreainvestment.com:29443` 의 `GET /uapi/overseas-price/v1/quotations/price` (TR ID `HHDFS00000300`) 응답을 broker-agnostic `Quote` 도메인 모델로 매핑한다.

확정된 값 (catalog `Confirmed: yes`):

- Base URL (모의): `https://openapivts.koreainvestment.com:29443`.
- Path: `/uapi/overseas-price/v1/quotations/price`.
- HTTP method: `GET`.
- TR ID: `HHDFS00000300`.
- Query: `AUTH=` (빈 문자열 또는 null), `EXCD=<거래소코드>`, `SYMB=<종목코드>`. EXCD 허용값: `HKS/NYS/NAS/AMS/TSE/SHS/SZS/SHI/SZI/HSX/HNX/BAY/BAQ/BAA`.
- Headers (Y 표시): `content-type: application/json; charset=utf-8`, `authorization: Bearer ${access_token}`, `appkey`, `appsecret`, `tr_id: HHDFS00000300`. `custtype` 은 현재체결가에서 옵션이므로 본 작업에서는 보내지 않는다.
- 응답 (현재체결가): `rt_cd` (성공 시 `"0"`), `output.last` (체결가, 문자열), `output.tvol` (당일 누적 거래량, 문자열), `output.rsym` (`D` + EXCD 3자리 + SYMB). bid/ask 없음. 거래소 timestamp 없음 → 응답 수신 시각을 사용.

## 2. 절대 금지

- live trading 활성화. `LIVE_TRADING_ENABLED=true`. live 도메인 (`openapi.koreainvestment.com:9443`) 호출.
- `ALLOW_MARKET_ORDERS=true`. `OrderType.MARKET` 가드 우회. kill switch 변경.
- 주문 / 취소 / replace / 잔고 / 체결 / 오픈주문 endpoint 구현. `KisBroker.place_order` 등은 그대로 NotImplementedError 유지 (dry-run preview 만 동작).
- `HHDFS00000300` 외 임의 TR ID 추가. `HHDFS76200100`, `HHDFS76200200`, `HHDFS76220000`, 또는 주문 TR ID 등을 코드/문서/테스트에 추가하지 않는다.
- KIS endpoint / 헤더 / payload / 응답 필드 추측. catalog `Confirmed: yes` 행 외 항목 사용 금지.
- 외부 HTTP 라이브러리: `import requests`, `import httpx`, `import aiohttp`, `import urllib3`, `from requests …`, `from httpx …`, `from aiohttp …`. stdlib `urllib.request`, `urllib.parse`, `urllib.error` 만 허용.
- Strategy / Agent / LLM 이 `app.broker.kis` 또는 `app.broker.kis_quote_mapper` 를 직접 import 하는 경로 추가.
- Agent / LLM 이 executable order 를 생성하게 하는 변경.
- FX 변환 함수 / 환율 상수 도입.
- `.env`, `.env.example` 읽기 / 수정. 실제 app key / app secret / access token / 계좌번호 / Bearer token 을 코드 / 문서 / 테스트 / patch / docstring 어디에도 기록.
- `app/api/*`, `app/static/*`, `app/main.py`, `app/broker/kis_http.py`, `app/broker/kis_token_cache.py`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/base.py`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/config.py`, `app/domain/enums.py`, `app/domain/orders.py`, `app/domain/fills.py`, `app/domain/market.py`, `docs/kis/*` 변경.
- 새 env 변수 추가 (catalog 후속 항목 `KIS_MARKET_DATA_APP_KEY` 등은 별 job 으로).
- 자동 git commit / push / merge / deploy.

## 3. 수정·생성 파일 화이트리스트

수정 (MODIFY):

- `projects/paper-trading/app/domain/quote.py` — `bid_ask_present: bool = True` 필드 추가.
- `projects/paper-trading/app/broker/kis_quote_mapper.py` — `kis_raw_quote_to_domain` 구현.
- `projects/paper-trading/app/broker/kis.py` — 시장데이터 transport 추가, `KisMarketDataClient.get_quote/get_last_price/healthcheck_market_data/__init__/__repr__` 변경, `KisBroker.get_quote` 시그니처 변경.
- `projects/paper-trading/tests/test_quote_model.py` — `bid_ask_present` 관련 테스트 추가.
- `projects/paper-trading/tests/test_kis_quote_mapper.py` — happy / 실패 경로 테스트로 재작성.
- `projects/paper-trading/tests/test_kis_market_data_client.py` — happy / 실패 / healthcheck / repr 테스트로 재작성.
- `projects/paper-trading/tests/test_kis_http_boundaries.py` — `test_market_data_requires_auth_before_unimplemented_endpoint` 의 두 번째 assertion 1-2 줄만 갱신. 그 외 모든 함수/assertion 절대 변경 금지.
- `projects/paper-trading/tests/test_broker_interface.py` — `test_kis_healthcheck_returns_disconnected_dict` 의 `reason` 매칭 assertion 1 줄만 갱신. 그 외 모든 함수/assertion 절대 변경 금지.
- `projects/paper-trading/README.md` — 시장데이터 동작 1-2 줄 안내 추가.

생성 (NEW):

- `projects/paper-trading/docs/ai/jobs/api-market-data-001/patch.md` — 구현 후 너의 요약.

위 목록에 없는 파일은 절대 수정/생성하지 않는다. 특히 `kis_http.py`, `app/api/*`, `app/static/*`, `app/main.py`, `app/config.py`, `app/broker/paper.py`, `.env*` 는 변경 금지.

## 4. 단계별 작업

### 4.1 `app/domain/quote.py` — `bid_ask_present` 필드 추가

- 기존 `currency: str = "USD"` 필드 뒤에 다음 한 줄을 추가:

  ```python
  bid_ask_present: bool = True
  ```

- `__post_init__` 본문은 변경하지 않는다. synthetic 케이스 (bid == ask == last) 는 기존 invariant 를 자연스럽게 통과한다.
- 모듈 docstring 1 줄 추가 가능 ("`bid_ask_present` 가 False 면 bid/ask 는 last 와 동일한 synthetic 값").
- 그 외 method (`spread_pct`, `is_stale`) 변경 금지.

### 4.2 `app/broker/kis_quote_mapper.py` — 매퍼 구현

기존 NotImplementedError raise 본문을 다음 구현으로 교체.

- import: `from datetime import datetime`, `from decimal import Decimal`, `from app.domain.enums import Session`, `from app.domain.quote import Quote`. (timezone 미사용 시 import 생략.)
- 시그니처:

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

- 검증 순서:
  1. `raw is None` → `raise ValueError("raw quote payload is None")`.
  2. `if not isinstance(raw, dict): raise ValueError("malformed_response: raw is not dict")`.
  3. `if not symbol: raise ValueError("symbol must be non-empty")`. `symbol_upper = symbol.strip().upper()`. `if not symbol_upper: raise ValueError("symbol must be non-empty")`.
  4. `if received_at.tzinfo is None: raise ValueError("received_at must be timezone-aware")`.
  5. `rt_cd = raw.get("rt_cd")`. `if rt_cd not in (None, "0"): raise ValueError(f"kis_error:{raw.get('msg_cd') or raw.get('msg1') or 'unknown'}")`. (transport 가 우선 검증하지만 mapper 도 방어적.)
  6. `output = raw.get("output")`. `if not isinstance(output, dict): raise ValueError("malformed_response: output missing")`.
  7. `last_raw = output.get("last")`. `if last_raw in (None, ""): raise ValueError("malformed_response: last missing")`.
  8. `tvol_raw = output.get("tvol")`. `if tvol_raw in (None, ""): raise ValueError("malformed_response: tvol missing")`.
- 변환:
  - `last = Decimal(str(last_raw).replace(",", ""))`. `if last <= 0: raise ValueError("malformed_response: last not positive")`.
  - `volume = int(Decimal(str(tvol_raw).replace(",", "")))`. `if volume < 0: raise ValueError("malformed_response: volume negative")`.
- 옵션 `rsym` 검증:
  - `rsym = output.get("rsym")`.
  - `if isinstance(rsym, str) and len(rsym) >= 4 and rsym[0] == "D"`:
    - 다음 3 자리는 EXCD, 그 뒤가 SYMB. `rsym_symbol = rsym[4:].strip().upper()`.
    - 일치하지 않아도 silent: `symbol_upper` 를 그대로 사용 (로그 금지).
- Quote 생성:

  ```python
  return Quote(
      symbol=symbol_upper,
      last=last,
      bid=last,
      ask=last,
      volume=volume,
      timestamp=received_at,
      source=source,
      session=session,
      currency=currency,
      bid_ask_present=False,
  )
  ```

- Quote 의 `__post_init__` 에서 raise 되는 ValueError 도 호출자가 잡지 않는다 (그대로 전파).
- 모듈 docstring 을 새 동작에 맞게 갱신 (NotImplementedError 언급 제거).

### 4.3 `app/broker/kis.py` — 시장데이터 transport + 클라이언트 본문

#### 4.3.1 상단 추가 import

```python
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Protocol
import json
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote as urlquote
from urllib.request import Request, urlopen

from app.broker.kis_http import KisApiMode  # 이미 import 되어 있음
from app.broker.kis_quote_mapper import kis_raw_quote_to_domain
from app.domain.quote import Quote
```

`KisApiMode` 이미 import 되어 있는지 확인 후 중복 없이 추가.

#### 4.3.2 모듈 상수

```python
KIS_OVERSEAS_PRICE_PATH = "/uapi/overseas-price/v1/quotations/price"
KIS_OVERSEAS_PRICE_TR_ID = "HHDFS00000300"
KIS_PAPER_MARKET_DATA_HOSTS: frozenset[str] = frozenset({
    "openapivts.koreainvestment.com:29443",
})
KIS_ALLOWED_EXCHANGES: frozenset[str] = frozenset({
    "HKS", "NYS", "NAS", "AMS", "TSE", "SHS", "SZS", "SHI", "SZI",
    "HSX", "HNX", "BAY", "BAQ", "BAA",
})
```

#### 4.3.3 Protocol + 두 transport

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
    ) -> tuple[dict[str, Any], datetime]: ...


@dataclass
class MockMarketDataTransport:
    def get_quote(self, **_kwargs: Any) -> tuple[dict[str, Any], datetime]:
        raise KisDataUnavailableError("mock_mode_no_network")


@dataclass
class UrllibMarketDataTransport:
    timeout_seconds: float = 5.0
    max_retries: int = 1
    backoff_seconds: float = 2.0

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
        # 1. validate
        if exchange not in KIS_ALLOWED_EXCHANGES:
            raise KisDataUnavailableError("invalid_exchange")
        host = _kis_extract_host(base_url)
        if host not in KIS_PAPER_MARKET_DATA_HOSTS:
            raise KisDataUnavailableError("disallowed_host")
        # 2. build URL
        url = (
            base_url.rstrip("/")
            + KIS_OVERSEAS_PRICE_PATH
            + "?AUTH="
            + "&EXCD=" + urlquote(exchange, safe="")
            + "&SYMB=" + urlquote(symbol, safe="")
        )
        # 3. headers
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {access_token}",
            "appkey": app_key,
            "appsecret": app_secret,
            "tr_id": KIS_OVERSEAS_PRICE_TR_ID,
        }
        # 4. attempt loop
        attempts = 0
        last_exc: Exception | None = None
        while attempts <= self.max_retries:
            attempts += 1
            try:
                req = Request(url=url, data=None, headers=headers, method="GET")
                with urlopen(req, timeout=self.timeout_seconds) as resp:
                    body = resp.read()
                received_at = datetime.now(timezone.utc)
                try:
                    response = json.loads(body.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    raise KisDataUnavailableError("invalid_response_body") from exc
                if not isinstance(response, dict):
                    raise KisDataUnavailableError("invalid_response_body")
                rt_cd = response.get("rt_cd")
                if rt_cd not in (None, "0"):
                    code = response.get("msg_cd") or response.get("msg1") or "unknown"
                    raise KisDataUnavailableError(f"kis_error:{code}")
                return response, received_at
            except HTTPError as exc:
                if exc.code >= 500 and attempts <= self.max_retries:
                    last_exc = exc
                    time.sleep(self.backoff_seconds)
                    continue
                raise KisDataUnavailableError(f"http_{exc.code}") from exc
            except (URLError, TimeoutError, socket.timeout) as exc:
                if attempts <= self.max_retries:
                    last_exc = exc
                    time.sleep(self.backoff_seconds)
                    continue
                raise KisDataUnavailableError("transport_error") from exc
        raise KisDataUnavailableError("transport_error_after_retries") from last_exc


def _kis_extract_host(url: str) -> str:
    if "://" not in url:
        return ""
    rest = url.split("://", 1)[1]
    return rest.split("/", 1)[0]
```

- 위 transport 의 raise 메시지는 short tag 만 포함하고 access_token / app_key / app_secret / 계좌번호 / response body 원문을 절대 포함하지 않는다.
- `__cause__` 로 urllib 예외를 연결할 수 있지만, str(exception) 또는 logging 으로 노출하지 말 것. (테스트가 `pytest.raises` 의 `match=` 로 tag 만 검사하도록.)

#### 4.3.4 `KisMarketDataClient` 본문 교체

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

    def __repr__(self) -> str:
        kind = "mock" if isinstance(self._transport, MockMarketDataTransport) else "paper"
        return f"KisMarketDataClient(<{kind}>)"

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
            tag = f"malformed_response:{exc}"
            self._last_error = tag
            raise KisDataUnavailableError(tag) from exc
        self._last_error = None
        return quote

    def get_last_price(self, symbol: str, *, exchange: str = "NAS") -> Decimal:
        return self.get_quote(symbol, exchange=exchange).last

    def healthcheck_market_data(self) -> dict[str, Any]:
        mock = isinstance(self._transport, MockMarketDataTransport)
        auth_present = self._auth.is_authenticated()
        connected = (not mock) and auth_present
        available = connected
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

    def _validate_symbol(self, symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not normalized or not normalized.replace(".", "").isalnum():
            self._last_error = "invalid_symbol"
            raise KisDataUnavailableError("invalid_symbol")
        return normalized

    @property
    def last_error(self) -> str | None:
        return self._last_error
```

- 기존 stub `self._http = KisHttpClient(settings)` 라인은 더 이상 사용하지 않으므로 제거. (단, 모듈 어디서도 `KisMarketDataClient._http` 를 참조하지 않는지 확인. test_kis_http_boundaries 의 `KisHttpClient` 테스트는 `KisHttpClient(_settings(settings))` 를 직접 생성하므로 영향 없음.)

#### 4.3.5 `KisBroker.get_quote`

```python
def get_quote(self, symbol: str, *, exchange: str = "NAS") -> Quote:
    return self._market_data.get_quote(symbol, exchange=exchange)
```

다른 KisBroker 메서드 (`place_order`, `cancel_order`, `replace_order`, `get_account`, `get_positions`, `get_open_orders`, `get_fills`, `get_order_status`, `capabilities`, `healthcheck`, `_to_kis_request`, `_dry_run_preview`, `__repr__` 등) 는 변경하지 않는다. `KisHttpClient` 클래스도 변경하지 않는다 (`request()` 가 그대로 NotImplementedError 를 raise — `test_http_client_has_conservative_defaults_and_no_endpoint` 통과 유지).

### 4.4 `tests/test_quote_model.py` — `bid_ask_present` 테스트 추가

기존 테스트는 그대로 두고 다음을 추가한다:

```python
def test_quote_bid_ask_present_defaults_true():
    q = _q()
    assert q.bid_ask_present is True


def test_quote_synthetic_bid_ask_when_absent():
    last = Decimal("100")
    q = _q(bid=last, ask=last, bid_ask_present=False)
    assert q.bid == q.ask == q.last == last
    assert q.bid_ask_present is False
    assert q.spread_pct == Decimal("0")


def test_quote_frozen_includes_bid_ask_present():
    q = _q()
    with pytest.raises(FrozenInstanceError):
        q.bid_ask_present = False  # type: ignore[misc]
```

`_q(...)` helper 에 `bid_ask_present` 키를 받을 수 있도록 dict.update 가 그대로 동작하는지 확인 (현재 helper 는 dict.update 후 `Quote(**data)` 호출이므로 신규 키도 그대로 통과).

### 4.5 `tests/test_kis_quote_mapper.py` — 실동작 테스트로 재작성

기존 3 테스트 (NotImplementedError, None raw, empty symbol) 는 일부만 유지·갱신한다.

```python
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.broker.kis_quote_mapper import kis_raw_quote_to_domain
from app.domain.quote import Quote


NOW = datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc)


def _raw(last="100.50", tvol="1000000", rsym="DNASAAPL", rt_cd="0"):
    return {
        "rt_cd": rt_cd,
        "msg_cd": "",
        "msg1": "",
        "output": {"last": last, "tvol": tvol, "rsym": rsym},
    }


def test_mapper_happy_path():
    quote = kis_raw_quote_to_domain(_raw(), symbol="AAPL", received_at=NOW)
    assert isinstance(quote, Quote)
    assert quote.symbol == "AAPL"
    assert quote.last == Decimal("100.50")
    assert quote.bid == quote.ask == quote.last
    assert quote.bid_ask_present is False
    assert quote.volume == 1_000_000
    assert quote.timestamp == NOW
    assert quote.source == "kis_paper"
    assert quote.currency == "USD"


def test_mapper_rejects_none_raw():
    with pytest.raises(ValueError, match="None"):
        kis_raw_quote_to_domain(None, symbol="AAPL", received_at=NOW)


def test_mapper_rejects_empty_symbol():
    with pytest.raises(ValueError, match="symbol"):
        kis_raw_quote_to_domain(_raw(), symbol="", received_at=NOW)


def test_mapper_rejects_naive_received_at():
    naive = datetime(2026, 5, 18, 10, 0, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        kis_raw_quote_to_domain(_raw(), symbol="AAPL", received_at=naive)


def test_mapper_rejects_kis_error():
    raw = _raw()
    raw["rt_cd"] = "1"
    raw["msg_cd"] = "EFGS9999"
    with pytest.raises(ValueError, match="kis_error:EFGS9999"):
        kis_raw_quote_to_domain(raw, symbol="AAPL", received_at=NOW)


def test_mapper_rejects_missing_output():
    raw = {"rt_cd": "0"}
    with pytest.raises(ValueError, match="output missing"):
        kis_raw_quote_to_domain(raw, symbol="AAPL", received_at=NOW)


def test_mapper_rejects_missing_last():
    raw = _raw(last="")
    with pytest.raises(ValueError, match="last missing"):
        kis_raw_quote_to_domain(raw, symbol="AAPL", received_at=NOW)


def test_mapper_rejects_missing_tvol():
    raw = _raw(tvol="")
    with pytest.raises(ValueError, match="tvol missing"):
        kis_raw_quote_to_domain(raw, symbol="AAPL", received_at=NOW)


def test_mapper_rejects_non_positive_last():
    raw = _raw(last="0")
    with pytest.raises(ValueError, match="last not positive"):
        kis_raw_quote_to_domain(raw, symbol="AAPL", received_at=NOW)


def test_mapper_handles_comma_separated_values():
    raw = _raw(last="1,234.56", tvol="1,000,000")
    quote = kis_raw_quote_to_domain(raw, symbol="AAPL", received_at=NOW)
    assert quote.last == Decimal("1234.56")
    assert quote.volume == 1_000_000


def test_mapper_tolerates_rsym_mismatch_silently():
    raw = _raw(rsym="DNYSTSLA")
    quote = kis_raw_quote_to_domain(raw, symbol="AAPL", received_at=NOW)
    assert quote.symbol == "AAPL"  # 입력 symbol 우선
```

### 4.6 `tests/test_kis_market_data_client.py` — 실동작 테스트로 재작성

기존 NotImplementedError 테스트 (`test_market_data_methods_fail_closed`, `test_kis_get_quote_still_fail_closed_after_mvp023`) 는 새 동작에 맞게 갱신한다. `test_market_data_healthcheck_disconnected` 와 `test_market_data_repr_does_not_expose_secrets` 도 새 메시지로 갱신.

```python
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.broker.kis import (
    KisAuthClient,
    KisAuthError,
    KisDataUnavailableError,
    KisMarketDataClient,
    MockMarketDataTransport,
    UrllibMarketDataTransport,
)


def _settings(settings):
    return replace(
        settings,
        kis_env="paper",
        kis_account_no="12345678",
        kis_app_key="fake-key",
        kis_app_secret="fake-secret",
    )


def _auth_with_token(settings):
    auth = KisAuthClient(_settings(settings))
    auth._store_token("fake-token", 120)
    return auth


class _FakeTransport:
    def __init__(self, response=None, received_at=None, raises=None):
        self._response = response
        self._received_at = received_at or datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc)
        self._raises = raises
        self.calls: list[dict] = []

    def get_quote(self, **kwargs):
        self.calls.append(kwargs)
        if self._raises is not None:
            raise self._raises
        return self._response, self._received_at


def _ok_response(last="100.50", tvol="1000000"):
    return {"rt_cd": "0", "output": {"last": last, "tvol": tvol, "rsym": "DNASAAPL"}}


def test_get_quote_requires_authentication(settings):
    auth = KisAuthClient(_settings(settings))
    md = KisMarketDataClient(_settings(settings), auth, transport=_FakeTransport(_ok_response()))
    with pytest.raises(KisAuthError, match="authentication required"):
        md.get_quote("AAPL")
    assert md.last_error == "authentication_required"


def test_get_quote_rejects_invalid_symbol(settings):
    md = KisMarketDataClient(_settings(settings), _auth_with_token(settings), transport=_FakeTransport(_ok_response()))
    with pytest.raises(KisDataUnavailableError, match="invalid_symbol"):
        md.get_quote("bad symbol!")


def test_get_quote_happy_path_returns_quote(settings):
    transport = _FakeTransport(_ok_response())
    md = KisMarketDataClient(_settings(settings), _auth_with_token(settings), transport=transport)
    quote = md.get_quote("AAPL")
    assert quote.symbol == "AAPL"
    assert quote.last == Decimal("100.50")
    assert quote.bid == quote.ask == quote.last
    assert quote.bid_ask_present is False
    assert quote.source == "kis_paper"
    assert transport.calls[0]["exchange"] == "NAS"
    assert transport.calls[0]["symbol"] == "AAPL"
    assert md.last_error is None


def test_get_quote_propagates_kis_data_unavailable(settings):
    transport = _FakeTransport(raises=KisDataUnavailableError("kis_error:EFGS9999"))
    md = KisMarketDataClient(_settings(settings), _auth_with_token(settings), transport=transport)
    with pytest.raises(KisDataUnavailableError, match="kis_error:EFGS9999"):
        md.get_quote("AAPL")
    assert md.last_error == "kis_error:EFGS9999"


def test_get_quote_wraps_mapper_value_error(settings):
    transport = _FakeTransport({"rt_cd": "0", "output": {}})
    md = KisMarketDataClient(_settings(settings), _auth_with_token(settings), transport=transport)
    with pytest.raises(KisDataUnavailableError, match="malformed_response"):
        md.get_quote("AAPL")
    assert md.last_error and md.last_error.startswith("malformed_response")


def test_get_last_price_returns_decimal(settings):
    md = KisMarketDataClient(_settings(settings), _auth_with_token(settings), transport=_FakeTransport(_ok_response()))
    assert md.get_last_price("AAPL") == Decimal("100.50")


def test_default_transport_is_mock_in_mock_mode(settings):
    md = KisMarketDataClient(_settings(settings), KisAuthClient(_settings(settings)))
    assert isinstance(md._transport, MockMarketDataTransport)


def test_default_transport_is_urllib_in_paper_mode(settings):
    paper_settings = replace(_settings(settings), kis_api_mode="paper")
    md = KisMarketDataClient(paper_settings, KisAuthClient(paper_settings))
    assert isinstance(md._transport, UrllibMarketDataTransport)


def test_mock_transport_fails_closed_with_auth(settings):
    md = KisMarketDataClient(_settings(settings), _auth_with_token(settings))
    with pytest.raises(KisDataUnavailableError, match="mock_mode_no_network"):
        md.get_quote("AAPL")


def test_urllib_transport_rejects_invalid_exchange():
    transport = UrllibMarketDataTransport()
    with pytest.raises(KisDataUnavailableError, match="invalid_exchange"):
        transport.get_quote(
            base_url="https://openapivts.koreainvestment.com:29443",
            access_token="t",
            app_key="k",
            app_secret="s",
            exchange="LSE",
            symbol="AAPL",
        )


def test_urllib_transport_rejects_disallowed_host():
    transport = UrllibMarketDataTransport()
    with pytest.raises(KisDataUnavailableError, match="disallowed_host"):
        transport.get_quote(
            base_url="https://evil.example.com",
            access_token="t",
            app_key="k",
            app_secret="s",
            exchange="NAS",
            symbol="AAPL",
        )


def test_healthcheck_mock_mode(settings):
    md = KisMarketDataClient(_settings(settings), KisAuthClient(_settings(settings)))
    h = md.healthcheck_market_data()
    assert h["connected"] is False
    assert h["available"] is False
    assert h["reason"] == "mock_mode_no_network"
    assert h["auth_present"] is False


def test_healthcheck_paper_mode_without_auth(settings):
    paper_settings = replace(_settings(settings), kis_api_mode="paper")
    md = KisMarketDataClient(paper_settings, KisAuthClient(paper_settings))
    h = md.healthcheck_market_data()
    assert h["connected"] is False
    assert h["reason"] == "authentication_required"


def test_healthcheck_paper_mode_with_auth(settings):
    paper_settings = replace(_settings(settings), kis_api_mode="paper")
    auth = KisAuthClient(paper_settings)
    auth._store_token("fake-token", 120)
    md = KisMarketDataClient(paper_settings, auth)
    h = md.healthcheck_market_data()
    assert h["connected"] is True
    assert h["available"] is True
    assert h["reason"] == "ready"


def test_repr_does_not_expose_secrets(settings):
    md = KisMarketDataClient(_settings(settings), _auth_with_token(settings), transport=_FakeTransport(_ok_response()))
    text = repr(md)
    for needle in ("fake-key", "fake-secret", "fake-token", "12345678", "Bearer"):
        assert needle not in text
    assert "mock" in text or "paper" in text
```

### 4.7 `tests/test_kis_http_boundaries.py` — 좁은 갱신

오직 `test_market_data_requires_auth_before_unimplemented_endpoint` 의 두 번째 `pytest.raises(NotImplementedError, match="confirm market data endpoint")` 블록만 다음으로 교체:

```python
    broker.auth._store_token("fake-token", 120)
    with pytest.raises(KisDataUnavailableError, match="mock_mode_no_network"):
        broker.get_quote("AAPL")
```

함수 상단의 첫 번째 `pytest.raises(KisAuthError, match="authentication required")` 는 그대로 유지. 다른 함수들 (`test_http_client_has_conservative_defaults_and_no_endpoint`, `test_auth_token_storage_and_expiry_state`, `test_authenticate_*`, `test_account_*`, `test_market_data_symbol_validation_and_healthcheck`, `test_order_*`, `test_cancel_replace_*`, `test_kis_modules_do_not_import_third_party_http_libs`, `test_kis_http_has_no_live_transport_class`) 절대 변경 금지.

`test_market_data_symbol_validation_and_healthcheck` 는 mock 모드에서 `health["connected"] is False`, `health["available"] is False`, `health["auth_present"] is False` 그리고 `health["last_error"] == "invalid_symbol"` 을 기대한다. 새 healthcheck 도 이 4 개 모두 만족한다 (mock → connected/available False; auth 없음 → auth_present False; symbol validate 실패 후 last_error=invalid_symbol). 따라서 이 함수는 변경하지 않는다.

### 4.8 `tests/test_broker_interface.py` — 좁은 갱신

`test_kis_healthcheck_returns_disconnected_dict` 의 다음 두 줄을 교체:

```python
    reason = h["market_data"]["reason"].lower()
    assert "skeleton" in reason or "not implemented" in reason
```

→ 

```python
    reason = h["market_data"]["reason"].lower()
    assert any(
        needle in reason
        for needle in ("skeleton", "not implemented", "mock_mode_no_network", "authentication_required")
    )
```

그 외 모든 assertion 과 다른 함수 (`test_kis_broker_has_all_required_methods`, `test_kis_broker_exposes_sub_clients`, `test_kis_broker_mode_is_paper`, `test_kis_broker_missing_env_fails_closed`, `test_kis_broker_live_env_rejected`, `test_kis_broker_missing_credentials_fails_closed`, `test_kis_place_cancel_replace_not_implemented`, `test_kis_protocol_methods_delegate_to_not_implemented`, `test_kis_data_methods_not_implemented`, `test_kis_broker_has_get_fills_and_get_order_status`, `test_kis_order_request_class_is_exported`, `test_kis_broker_capabilities_are_exported_and_fail_closed`, `test_kis_broker_repr_masks_secrets`, `test_strategy_package_does_not_import_kis`, `test_agent_package_does_not_import_kis_if_present`, `test_kis_module_does_not_import_http_libraries`) 절대 변경 금지.

### 4.9 `README.md` — 1-2 줄 안내

KIS 관련 섹션 또는 시장데이터 안내 위치에 다음 한국어 문장을 1-2 줄로 추가:

> `KisMarketDataClient.get_quote(symbol, exchange="NAS")` 는 모의 도메인 `openapivts.koreainvestment.com:29443` 의 해외주식 현재체결가 (`HHDFS00000300`) 를 stdlib `urllib.request` 로 호출해 broker-agnostic `Quote` 도메인 모델로 반환한다. 현재체결가에는 bid/ask 와 거래소 timestamp 가 없으므로 `bid = ask = last`, `bid_ask_present=False`, `timestamp = 응답 수신 시각` 으로 채운다.

live trading / 실주문 / `Bearer` token / app key / app secret / 계좌번호 안내는 추가하지 않는다.

### 4.10 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

전체 PASS 여야 한다. 실패 테스트가 있으면 무엇이 무엇 때문에 실패하는지 명확히 확인하고, 본 작업 범위 내에서 수정한다. 범위를 벗어난 테스트 수정이 더 필요하다고 판단되면 거기서 멈추고 `patch.md` 에 그 사실을 기록한다.

마지막에 `projects/paper-trading/docs/ai/jobs/api-market-data-001/patch.md` 를 작성한다:

```markdown
# api-market-data-001 — Codex 구현 요약

## 변경된 파일
- ...

## 새/갱신된 동작
- `KisMarketDataClient.get_quote(symbol, exchange='NAS')` 가 KIS 모의 도메인 `HHDFS00000300` 호출 후 `Quote` 반환.
- `Quote.bid_ask_present` 필드 추가, 현재체결가 매핑은 synthetic bid==ask==last + bid_ask_present=False.
- ...

## 테스트 결과
- compileall: OK
- pytest: N passed
- 신규/갱신된 테스트 함수 목록

## 안전 회귀 확인
- live trading / 시장가 / 실주문 / KIS 주문 endpoint 변동 없음
- TR ID 는 `HHDFS00000300` 한 개만 사용
- secret / 계좌번호 / access token / Bearer 노출 없음
- 외부 HTTP 라이브러리 import 없음 (stdlib `urllib.request` 만)
- Strategy / Agent 가 `app.broker.kis` 를 import 하지 않음
- 자동 git commit / push / merge / deploy 수행 안 함

## 알려진 한계 / 후속 작업
- ...
```

## 5. 자가 점검 (구현 후 PR 전)

- [ ] `import requests`/`httpx`/`aiohttp`/`urllib3` 가 어디에도 없다.
- [ ] `HHDFS00000300` 외 TR ID 가 코드/문서/테스트에 없다.
- [ ] `/uapi/overseas-price/v1/quotations/price` 외 KIS 시장데이터 경로가 없다.
- [ ] host allowlist 가 `openapivts.koreainvestment.com:29443` 한 개로 유지.
- [ ] `KisBroker.place_order` 가 dry-run 외에서는 NotImplementedError, cancel/replace/fills/get_order_status/get_open_orders 도 NotImplementedError.
- [ ] `Quote` 에 추가된 필드는 `bid_ask_present: bool = True` 하나뿐.
- [ ] mapper / market data client / transport / `__repr__` / exception message 어디에도 secret/token/계좌번호 원문이 흘러나가지 않는다.
- [ ] `app/api/*`, `app/static/*`, `app/main.py`, `app/config.py`, `app/broker/kis_http.py` 가 unchanged.
- [ ] `python -m compileall app tests` 와 `python -m pytest -p no:cacheprovider` 가 전부 통과.
- [ ] `.env` 가 unchanged.
- [ ] commit / push / merge / deploy 를 너가 직접 실행하지 않았다.
