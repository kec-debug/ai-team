# api-account-001 — Codex 구현 지시문

You are Codex, implementing the plan at `docs/ai/jobs/api-account-001/plan.md` inside the `projects/paper-trading` package.

Read first (in order):

1. `docs/ai/CLAUDE_CODEX_WORKFLOW.md` (root) — workflow + safety rules.
2. `docs/ai/jobs/api-account-001/request.ko.md` — original Korean request.
3. `docs/ai/jobs/api-account-001/plan.md` — this task's plan. Stay within scope.
4. `docs/kis/MISSING_OFFICIAL_VALUES.md` (root) — official KIS catalog. Use only `Confirmed: yes` paper-supported rows. Do not invent endpoints/TR IDs.
5. `projects/paper-trading/app/broker/kis.py` — current skeleton (KisAuthClient, KisAccountClient, KisMarketDataClient, KisBroker, sanitize_kis_response, validate_kis_order_request, etc.).
6. `projects/paper-trading/app/broker/kis_http.py` — SafeKisHttpClient / MockTransport / UrllibTransport for OAuth. **Do not modify.**
7. `projects/paper-trading/tests/test_kis_http_boundaries.py` — existing account-related regressions.

## Absolute prohibitions (block immediately if any apply)

- Do not enable live trading. Do not set `LIVE_TRADING_ENABLED=true` anywhere. Do not call live KIS endpoints. Do not add the live base URL (`https://openapi.koreainvestment.com:9443`) to any new code path.
- Do not implement order, cancel, modify, fill, or open-order endpoints. `KisBroker.place_order` / `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` must keep their current `NotImplementedError` / dry-run behavior unchanged.
- Do not invent KIS endpoints, TR IDs, headers, request fields, or response field names. Only use rows marked `Confirmed: yes` and `paper-supported` in `docs/kis/MISSING_OFFICIAL_VALUES.md`. Add `<TBD>` or `Confirmed: no` values nowhere.
- Do not add live TR IDs (`TTTS3012R`, `CTRP6504R`, `CTRP6010R`, `CTOS4001R`, `TTTS3039R`, `TTTC2101R`) to code/tests/docs. The only TR ID this task introduces is `VTTS3012R` (paper inquire-balance).
- Do not import external HTTP libraries (`requests`, `httpx`, `aiohttp`, `urllib3`). Use only stdlib `urllib.request` / `urllib.parse` / `urllib.error` / `socket`.
- Do not change `app/broker/kis_http.py`. `ALLOWED_PATHS_API_AUTH_001` stays `{/oauth2/tokenP, /oauth2/revokeP}`.
- Do not change `OrderType.MARKET` guards, `ALLOW_MARKET_ORDERS` behavior, kill-switch behavior, or `validate_kis_order_request`.
- Do not introduce FX conversion functions, exchange rate constants, or base-currency aggregation helpers. Multi-currency values must remain per-currency.
- Do not read or modify `.env` / `.env.example`. Do not log or write actual app keys, app secrets, account numbers, access tokens, Bearer tokens, or PII anywhere — code, tests, docstrings, patch.md, or commit messages.
- Do not modify `app/api/*`, `app/static/*`, `app/main.py`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/config.py`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/base.py`, `app/broker/kis_token_cache.py`, `app/broker/kis_quote_mapper.py`, or `app/domain/*` (other than what is listed below).
- Do not add new env variables, new Settings fields, or change `app/config.py`.
- Do not add Strategy/Agent/LLM imports of `app.broker.kis` or `KisAccountClient`. Strategy / Agent stay broker-agnostic.
- Do not run `git commit`, `git push`, `git merge`, PR creation, or deployment commands. The human runs git.

## Allowed file changes

| Path | Action |
| --- | --- |
| `projects/paper-trading/app/broker/kis.py` | Modify per §1 below. |
| `projects/paper-trading/tests/test_kis_account_client.py` | Create per §3. |
| `projects/paper-trading/tests/test_kis_http_boundaries.py` | Narrow modify per §4 (one function only). |
| `projects/paper-trading/README.md` | Optional 1-2 line note about paper KIS account read-only (no env var mention). May skip. |
| `projects/paper-trading/docs/ai/jobs/api-account-001/patch.md` | Create per §6. |

No other files. If you believe another file must change, stop and ask in `patch.md` instead of changing it.

## 1. Changes to `app/broker/kis.py`

### 1.1 Constants (add near `KIS_OVERSEAS_PRICE_PATH` block)

```python
KIS_OVERSEAS_BALANCE_PATH = "/uapi/overseas-stock/v1/trading/inquire-balance"
KIS_OVERSEAS_BALANCE_TR_ID_PAPER = "VTTS3012R"
KIS_PAPER_ACCOUNT_HOSTS = frozenset({"openapivts.koreainvestment.com:29443"})
KIS_PAPER_ACCOUNT_EXCHANGES = frozenset({"NASD", "NYSE", "AMEX"})
KIS_PAPER_ACCOUNT_CURRENCIES = frozenset({"USD", "HKD", "CNY", "JPY", "VND"})
KIS_BALANCE_MAX_PAGES = 10
```

Source citation in a comment immediately above: `# docs/kis/MISSING_OFFICIAL_VALUES.md §2.2 / §2.3 / §2.4 / §2.6 (paper VTTS3012R only).` Do not include URLs or real catalog body excerpts.

### 1.2 `_split_kis_account_no` module-level helper

```python
def _split_kis_account_no(account_no: str) -> tuple[str, str]:
    digits = (account_no or "").replace("-", "").strip()
    if len(digits) != 10 or not digits.isdigit():
        raise KisConfigError("invalid_kis_account_no_format")
    return digits[:8], digits[8:]
```

- Accepts `"12345678-01"` and `"1234567801"`. Anything else (including the 8-digit-only legacy fixture form) raises `KisConfigError`.
- Place near other module-level helpers (after `_int_from`).

### 1.3 Extend `KisPosition`

```python
@dataclass(frozen=True)
class KisPosition:
    symbol: str
    quantity: int
    avg_price: Decimal
    market_value: Decimal
    currency: str = "USD"
    exchange: str = ""
```

- Add `currency` and `exchange` at the end with defaults. Do not add `__post_init__`. Do not add other fields in this task.

### 1.4 New `KisAccountTransport` Protocol + transports

Add inside `app/broker/kis.py` (after `UrllibMarketDataTransport`):

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
        """Return one page of the KIS overseas balance response (raw)."""


@dataclass(frozen=True)
class MockAccountTransport:
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
        raise KisDataUnavailableError("mock_mode_no_network")


@dataclass(frozen=True)
class UrllibAccountTransport:
    timeout_seconds: float = 5.0
    max_retries: int = 1
    backoff_seconds: float = 2.0

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
        if _kis_extract_host(base_url) not in KIS_PAPER_ACCOUNT_HOSTS:
            raise KisDataUnavailableError("disallowed_host")
        if tr_id != KIS_OVERSEAS_BALANCE_TR_ID_PAPER:
            raise KisDataUnavailableError("disallowed_tr_id")
        if ovrs_excg_cd not in KIS_PAPER_ACCOUNT_EXCHANGES:
            raise KisDataUnavailableError("invalid_exchange")
        if tr_crcy_cd not in KIS_PAPER_ACCOUNT_CURRENCIES:
            raise KisDataUnavailableError("invalid_currency")

        url = (
            f"{base_url.rstrip('/')}{KIS_OVERSEAS_BALANCE_PATH}"
            f"?CANO={urlquote(cano)}&ACNT_PRDT_CD={urlquote(acnt_prdt_cd)}"
            f"&OVRS_EXCG_CD={urlquote(ovrs_excg_cd)}&TR_CRCY_CD={urlquote(tr_crcy_cd)}"
            f"&CTX_AREA_FK200={urlquote(ctx_area_fk200)}"
            f"&CTX_AREA_NK200={urlquote(ctx_area_nk200)}"
        )
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {access_token}",
            "appkey": app_key,
            "appsecret": app_secret,
            "tr_id": tr_id,
            "tr_cont": tr_cont,
        }
        request = Request(url=url, data=None, headers=headers, method="GET")
        attempts = max(1, self.max_retries + 1)
        for attempt in range(attempts):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    body = response.read().decode("utf-8")
                parsed = json.loads(body)
                if not isinstance(parsed, dict):
                    raise KisDataUnavailableError("invalid_response_body")
                rt_cd = parsed.get("rt_cd")
                if rt_cd not in (None, "0"):
                    code = parsed.get("msg_cd") or parsed.get("msg1") or "unknown"
                    raise KisDataUnavailableError(f"kis_error:{code}")
                return parsed
            except HTTPError as exc:
                if exc.code >= 500 and attempt < attempts - 1:
                    time.sleep(self.backoff_seconds)
                    continue
                raise KisDataUnavailableError(f"http_{exc.code}") from exc
            except (URLError, TimeoutError, socket.timeout) as exc:
                if attempt < attempts - 1:
                    time.sleep(self.backoff_seconds)
                    continue
                raise KisDataUnavailableError("transport_error") from exc
            except json.JSONDecodeError as exc:
                raise KisDataUnavailableError("invalid_response_body") from exc
        raise KisDataUnavailableError("transport_error")
```

- **Secret hygiene**: never echo `access_token` / `app_key` / `app_secret` into exception messages. Only the short tags above. The `from exc` chaining keeps the original urllib error attached, but the user-visible message stays sanitized.

### 1.5 `KisAccountClient` rewrite

Replace the body (keep imports / dataclass / `__repr__` / `masked_account_no` / `is_loaded` / `positions_loaded` / `cash_balance_loaded` / `last_error` / `_require_auth`). Add `_validate_paper_account_query` and the three implemented methods. Update `parse_*_response` per §1.6.

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

    # ... keep masked_account_no, is_loaded, positions_loaded, cash_balance_loaded as-is ...

    def _require_auth(self) -> None:
        if not self._auth.is_authenticated():
            self._last_error = "authentication_required"
            raise KisAuthError("KIS authentication required")

    def _validate_paper_account_query(self) -> None:
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

    def get_account(self, *, exchange: str = "NASD", currency: str = "USD") -> dict[str, Any]:
        self._require_auth()
        self._validate_paper_account_query()
        pages: list[dict[str, Any]] = list(self._iter_balance_pages(exchange=exchange, currency=currency))
        aggregated_output1: list[dict[str, Any]] = []
        last_output2: dict[str, Any] = {}
        for page in pages:
            rows = page.get("output1")
            if isinstance(rows, list):
                aggregated_output1.extend(row for row in rows if isinstance(row, dict))
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
                continue
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

    def get_cash_balance(self) -> KisCashBalance:
        self._require_auth()
        self._validate_paper_account_query()
        self._last_error = "paper_cash_balance_not_available_official_field_missing"
        raise KisDataUnavailableError(
            "paper_cash_balance_not_available_official_field_missing"
        )

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
        for _ in range(KIS_BALANCE_MAX_PAGES):
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
            next_fk = str(sanitized.get("ctx_area_fk200") or "").strip()
            next_nk = str(sanitized.get("ctx_area_nk200") or "").strip()
            if not next_fk and not next_nk:
                return
            ctx_fk = next_fk
            ctx_nk = next_nk
            tr_cont = "N"
        self._last_error = "balance_pagination_cap_exceeded"
        raise KisDataUnavailableError("balance_pagination_cap_exceeded")
```

- Add `from typing import Iterator` if not already imported (it may need to be added via `from collections.abc import Iterator` — prefer `collections.abc.Iterator` to stay modern; check existing imports first and reuse the project's pattern).

### 1.6 Rewrite `parse_positions_response` and `parse_cash_balance_response`

```python
def parse_positions_response(self, raw: dict[str, Any]) -> list[KisPosition]:
    sanitized = sanitize_kis_response(raw, self._settings)
    rt_cd = sanitized.get("rt_cd")
    if rt_cd not in (None, "0"):
        code = sanitized.get("msg_cd") or sanitized.get("msg1") or "unknown"
        raise KisDataUnavailableError(f"kis_error:{code}")
    rows = sanitized.get("output1")
    if rows is None:
        rows = []
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
    # Catalog gap: paper-supported endpoints do not expose a confirmed
    # (cash, withdrawable_cash) pair. Fail closed rather than guess.
    raise KisDataUnavailableError(
        "paper_cash_balance_not_available_official_field_missing"
    )
```

- Drop all legacy domestic-stock alias fields (`pdno`, `hldg_qty`, `qty`, `dnca_tot_amt`, `nxdy_excc_amt`, generic `symbol`/`quantity`/`avg_price`/`market_value`/`crcy_cd`/`cash` keys).

### 1.7 `KisBroker` integration

- `KisBroker.__init__` already constructs `KisAccountClient(settings, self._auth)`. With `transport=None`, the client auto-selects `MockAccountTransport` or `UrllibAccountTransport` based on `KisApiMode.parse(settings.kis_api_mode)`. No code change required here.
- `KisBroker.get_account()` and `get_positions()` stay as thin delegations. Confirm signatures still match (return type and default args).
- Do NOT add new capabilities to `capabilities()`. Account/positions reads are exposed via healthcheck flags, not capability booleans.
- Do NOT touch `place_order`, `cancel_order`, `replace_order`, `get_open_orders`, `get_fills`, `get_order_status`, `_to_kis_request`, `_dry_run_preview`, `last_order_preview`, `validate_kis_order_request`.

## 2. Imports

- `app/broker/kis.py` already imports `from urllib.parse import quote as urlquote, urlsplit` and `from urllib.request import Request, urlopen`. Reuse.
- Add `from collections.abc import Iterator` if needed (or use `Iterator` from `typing` if the file already does — match existing style).
- Do not add `requests`, `httpx`, `aiohttp`, `urllib3`.

## 3. New test file `tests/test_kis_account_client.py`

Use the existing `settings` fixture conftest pattern (look at `tests/conftest.py` for `settings`). Build local helpers:

```python
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest

from app.broker.kis import (
    KIS_BALANCE_MAX_PAGES,
    KisAccountClient,
    KisAuthClient,
    KisAuthError,
    KisBroker,
    KisCashBalance,
    KisConfigError,
    KisDataUnavailableError,
    KisPosition,
    UrllibAccountTransport,
    _split_kis_account_no,
)
from app.domain.enums import TradingMode


def _settings(settings, **overrides):
    data = {
        "kis_env": "paper",
        "kis_account_no": "12345678-01",
        "kis_app_key": "fake-key-XYZ",
        "kis_app_secret": "fake-secret-XYZ",
        "kis_api_mode": "paper",
    }
    data.update(overrides)
    return replace(settings, **data)


class FakeAccountTransport:
    def __init__(self, pages: list[dict[str, Any]] | None = None, exc: Exception | None = None):
        self._pages = list(pages or [])
        self._exc = exc
        self.calls: list[dict[str, Any]] = []

    def get_balance(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc
        if not self._pages:
            raise AssertionError("FakeAccountTransport exhausted")
        return self._pages.pop(0)
```

Tests to cover (each in its own function, names below):

1. `test_split_kis_account_no_accepts_dashed_and_plain`
2. `test_split_kis_account_no_rejects_short_and_nondigit`
3. `test_get_account_requires_authentication` (no token → KisAuthError("KIS authentication required"))
4. `test_get_account_blocks_live_trading_enabled` (token stored, `live_trading_enabled=True` → KisAuthError("live_trading_enabled"))
5. `test_get_account_blocks_non_paper_kis_env` (KisAccountClient direct, settings with `kis_env="live"` → KisAuthError("kis_env_not_paper")) — must not go through KisBroker which would refuse construction.
6. `test_get_account_blocks_kill_switch` (token + kill_switch_engaged → KisAuthError("kill_switch_engaged"))
7. `test_get_account_mock_mode_fails_closed` (kis_api_mode="mock", token → KisDataUnavailableError("mock_mode_no_network"))
8. `test_get_account_single_page_happy` (FakeAccountTransport returns 1 page, asserts pages_loaded==1, output1/output2 aggregate)
9. `test_get_account_pagination_two_pages_and_tr_cont` (page1 ctx_area_fk200="K1", nk200="N1"; page2 empty ctx; asserts second call received tr_cont="N", ctx_area_fk200="K1", ctx_area_nk200="N1"; pages_loaded==2)
10. `test_get_account_pagination_cap_exceeded` (always non-empty ctx → KIS_BALANCE_MAX_PAGES calls then KisDataUnavailableError("balance_pagination_cap_exceeded"))
11. `test_get_account_kis_error_propagates` (FakeAccountTransport raises KisDataUnavailableError("kis_error:EFGS9999") → propagated; account_loaded False)
12. `test_get_positions_maps_catalog_fields_and_drops_zero_qty`
13. `test_get_positions_multi_currency_separate_calls_no_aggregation` (two FakeAccountTransports — or single fake with parameterized response — for `currency="USD"` and `currency="HKD"`; verify positions stay in their currencies, no FX conversion)
14. `test_urllib_account_transport_rejects_live_host` (base_url="https://openapi.koreainvestment.com:9443" → KisDataUnavailableError("disallowed_host"))
15. `test_urllib_account_transport_rejects_unsupported_tr_id` (tr_id="TTTS3012R" → KisDataUnavailableError("disallowed_tr_id"))
16. `test_urllib_account_transport_rejects_invalid_exchange` (ovrs_excg_cd="LSE" → KisDataUnavailableError("invalid_exchange"))
17. `test_urllib_account_transport_rejects_invalid_currency` (tr_crcy_cd="EUR" → KisDataUnavailableError("invalid_currency"))
18. `test_get_cash_balance_fail_closed_with_clear_reason` (token + paper → KisDataUnavailableError("paper_cash_balance_not_available_official_field_missing"); cash_balance_loaded False)
19. `test_parse_positions_response_uses_catalog_fields_only` (input with `ovrs_pdno` / `ovrs_cblc_qty` / `pchs_avg_pric` / `ovrs_stck_evlu_amt` / `tr_crcy_cd` / `ovrs_excg_cd` → KisPosition; input with legacy `pdno`/`hldg_qty` → empty list (symbol missing) confirming legacy fields are ignored)
20. `test_parse_cash_balance_response_fails_closed`
21. `test_get_account_sanitizes_echoed_secrets` (FakeAccountTransport returns page with `"appkey": "fake-key-XYZ"`, `"access_token": "Bearer eyJfake"`, etc. → resulting dict serialized via `json.dumps(result)` does not contain those literals; sensitive keys redacted)
22. `test_account_client_repr_and_exceptions_do_not_expose_secrets` (over all fail-closed paths and on `repr(client)` / `repr(broker)`, none of `"fake-key-XYZ"` / `"fake-secret-XYZ"` / `"12345678"` / `"Bearer"` appear in the rendered text)
23. `test_kis_broker_healthcheck_reflects_account_state` (token stored + FakeAccountTransport injected via `broker._account._transport = fake`; after `broker.get_account()`, `broker.healthcheck()["account_loaded"] is True`, `cash_balance_loaded is False`. After successful `get_positions`, `positions_loaded is True`.)

For Test 5 (non-paper kis_env), construct `KisAccountClient` directly with `settings.kis_env="live"` so the KisBroker live guard does not preempt it. Then a token must be installed on a fake auth object that returns `is_authenticated() True`. Use a small `FakeAuth` helper, or instantiate `KisAuthClient` with paper settings and monkey-patch `is_authenticated`/`get_access_token`.

For Test 22, capture `repr(client)` and `repr(broker)` strings; also capture `str(exc)` for each raised exception. Assertions:

```python
forbidden = ("fake-key-XYZ", "fake-secret-XYZ", "12345678", "Bearer eyJ")
for haystack in haystacks:
    for needle in forbidden:
        assert needle not in haystack
```

Do not use real KIS app key/secret/account fixtures. The fake values above are explicit non-credentials.

## 4. Narrow modify of `tests/test_kis_http_boundaries.py`

Only change `test_account_parsers_return_internal_models_and_sanitize`. Replace its body so the input dict uses catalog field names and the expected `KisPosition` includes `currency` and `exchange`. Also change the cash assertion to `pytest.raises(KisDataUnavailableError, match="paper_cash_balance_not_available")`. Concrete shape:

```python
def test_account_parsers_return_internal_models_and_sanitize(settings):
    broker = KisBroker(_settings(settings))
    positions = broker.account.parse_positions_response(
        {
            "rt_cd": "0",
            "output1": [
                {
                    "ovrs_pdno": "AAPL",
                    "ovrs_cblc_qty": "2",
                    "pchs_avg_pric": "100.50",
                    "ovrs_stck_evlu_amt": "201.00",
                    "tr_crcy_cd": "USD",
                    "ovrs_excg_cd": "NASD",
                    # echoed secret-like keys must be redacted by sanitize_kis_response
                    "appkey": "fake-key",
                    "access_token": "Bearer XYZ",
                }
            ],
        }
    )

    assert positions == [
        KisPosition(
            symbol="AAPL",
            quantity=2,
            avg_price=Decimal("100.50"),
            market_value=Decimal("201.00"),
            currency="USD",
            exchange="NASD",
        )
    ]
    assert broker.account.positions_loaded() is True

    with pytest.raises(
        KisDataUnavailableError,
        match="paper_cash_balance_not_available",
    ):
        broker.account.parse_cash_balance_response({"output3": {"foo": "bar"}})
    assert broker.account.cash_balance_loaded() is False
```

Do NOT change any other function in this file. Specifically do not touch:

- `test_http_client_has_conservative_defaults_and_no_endpoint`
- `test_auth_token_storage_and_expiry_state`
- `test_authenticate_fails_closed_without_official_endpoint`
- `test_authenticate_rejects_non_paper_and_live`
- `test_account_queries_require_authentication` (the cash_balance call still raises `KisAuthError("authentication required")` because `_require_auth` runs first — unchanged behavior)
- `test_market_data_symbol_validation_and_healthcheck`
- `test_market_data_requires_auth_before_unimplemented_endpoint`
- `test_order_dry_run_does_not_send_http_and_sanitizes_payload`
- `test_order_live_http_fails_closed_without_official_endpoint`
- `test_order_guards_still_reject_unsafe_settings`
- `test_cancel_replace_queries_fail_closed`
- `test_kis_modules_do_not_import_third_party_http_libs`
- `test_kis_http_has_no_live_transport_class`

If any of those start failing due to your changes, you have overreached — fix the implementation, not the test.

## 5. Verification commands

Run from `projects/paper-trading`:

```bash
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

Both must PASS with zero regressions.

Also run the safety greps and include their (clean) output in `patch.md`:

```bash
grep -rnE "^(from|import) (requests|httpx|aiohttp|urllib3)" app/broker tests
grep -rn "TTTS3012R\|CTRP6504R\|CTRP6010R\|CTOS4001R\|TTTS3039R\|TTTC2101R" app tests
grep -rn "openapi.koreainvestment.com:9443" app tests
grep -rn "ALLOW_MARKET_ORDERS=true\|allow_market_orders=True" app
grep -rn "Bearer eyJ" app tests docs/ai/jobs/api-account-001 || true
grep -rn "from app.broker.kis" app/strategy 2>/dev/null || true
grep -rn "from app.broker.kis" app/agent 2>/dev/null || true
```

Expected: all 0 lines (or `||true`-tolerant 0 lines).

## 6. `patch.md` contents (Codex writes after implementation)

Create `projects/paper-trading/docs/ai/jobs/api-account-001/patch.md` with these sections in order:

1. **Files Changed** — list every modified/created file.
2. **Implementation Summary** — what `get_account` / `get_positions` / `get_cash_balance` now do; cite the catalog row(s) and TR_ID used (`VTTS3012R`); explicitly state that `get_cash_balance` is fail-closed and why (catalog gap: VTTS3007R needs per-symbol input, VTRP6504R paper limits to `output3` whose sub-fields are `<TBD>`).
3. **Implemented scope** — bullet list of what works (single-page balance, pagination up to `KIS_BALANCE_MAX_PAGES`, per-currency reporting, sanitization, secret-leak protection).
4. **Fail-closed scope** — bullet list of what remains fail-closed (`get_cash_balance`, all order endpoints, all paper-unsupported account endpoints, all live endpoints).
5. **Safety Confirmation** — confirm no secret/account/token leakage, live trading off, market-order guard intact, `app/broker/kis_http.py` unchanged, Strategy/Agent imports clean, `app/api/*` / `app/static/*` / `app/main.py` / `app/config.py` / `.env` untouched.
6. **Safety grep output** — verbatim output (or "0 lines") for each grep in §5 above.
7. **Test Results** — compileall + pytest output (the summary line, not full transcript). Highlight new test file count and that no existing test was broken.
8. **Remaining TODOs** — note that paper cash balance still needs catalog work on VTRP6504R `output3` sub-fields, and that paper buying-power read (per-symbol) could be a follow-up `api-buying-power-001` job.
9. **Claude verification prompt** — exact text to paste into Claude in review mode. Suggested:

   > Read `docs/ai/jobs/api-account-001/plan.md` and `docs/ai/jobs/api-account-001/patch.md`. Run `git diff` on the working tree. Verify: (a) only `app/broker/kis.py`, `tests/test_kis_account_client.py`, and the narrow `tests/test_kis_http_boundaries.py` change were modified; (b) only `VTTS3012R` and the paper inquire-balance path were introduced (no other TR IDs, no live base URL, no live TR IDs); (c) `get_account` / `get_positions` use only catalog `Confirmed: yes` fields (`output1[].ovrs_pdno` / `ovrs_cblc_qty` / `pchs_avg_pric` / `ovrs_stck_evlu_amt` / `tr_crcy_cd` / `ovrs_excg_cd`); (d) `get_cash_balance` is fail-closed; (e) `_split_kis_account_no` enforces 10-digit format; (f) `_validate_paper_account_query` blocks live/non-paper/kill-switch; (g) `app/broker/kis_http.py` and the OAuth `ALLOWED_PATHS_API_AUTH_001` set are unchanged; (h) no third-party HTTP imports; (i) Strategy/Agent do not import `app.broker.kis`; (j) all order endpoints (`place_order` / `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status`) keep their NotImplementedError/dry-run behavior; (k) `OrderType.MARKET` 3-layer guard, `ALLOW_MARKET_ORDERS=true` block, and kill-switch behavior unchanged; (l) `.env`, `.env.example`, and `docs/kis/MISSING_OFFICIAL_VALUES.md` unchanged; (m) pytest passes cleanly; (n) no secret / app key / app secret / account number / Bearer token literal appears in code, repr, exception messages, log output, or pytest captures. Output verdict `APPROVE`, `REQUEST CHANGES`, or `BLOCK` per `prompts/claude.md` rules.

10. **Follow-up Codex prompt rules (only used if Claude returns REQUEST CHANGES or BLOCK)**:

    Rules for composing a follow-up Codex task if Claude blocks:

    - Quote Claude's specific finding(s) verbatim under a `## Findings` header — one finding per bullet, file + line if Claude referenced them.
    - For each finding, write a `## Required change` block that states (a) the exact code/test edit required, (b) why this fix is in scope of api-account-001 (vs needing a new job), (c) the corresponding safety rule from `prompts/claude.md` that the fix must keep intact.
    - Re-state the absolute prohibitions section verbatim at the top.
    - Re-state the verification commands.
    - Do not expand scope: if Claude's finding requires changes outside `app/broker/kis.py` / the two test files / `patch.md` / optional `README.md`, escalate to the human instead of expanding scope.
    - The follow-up prompt must end with: "Update `patch.md` (do not create a new one). Append a `## Follow-up <N>` section explaining what changed and re-run verification. Do not commit / push / merge."

11. **Status footer**: `READY FOR REVIEW`.

Stop. Do not commit, push, merge, deploy, or modify `.env`. Hand off to the human, who will run `git diff` and invoke Claude review.
