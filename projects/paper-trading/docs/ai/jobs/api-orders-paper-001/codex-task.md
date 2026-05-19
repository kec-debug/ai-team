# api-orders-paper-001 — Codex 구현 지시문

You are Codex, implementing the plan at `docs/ai/jobs/api-orders-paper-001/plan.md` inside the `projects/paper-trading` package.

Read first (in order):

1. `docs/ai/CLAUDE_CODEX_WORKFLOW.md` (root) — workflow + safety rules.
2. `docs/ai/jobs/api-orders-paper-001/request.ko.md` — original Korean request.
3. `docs/ai/jobs/api-orders-paper-001/plan.md` — this task's plan. Stay within scope.
4. `docs/kis/MISSING_OFFICIAL_VALUES.md` (root) — official KIS catalog. Use only `Confirmed: yes` paper-supported rows in §4 (`VTTT1002U` US BUY + `VTTT1001U` US SELL only). Do not invent.
5. `projects/paper-trading/app/broker/kis.py` — current adapter (skeleton + market data + account + dry-run order).
6. `projects/paper-trading/app/broker/kis_http.py` — SafeKisHttpClient / MockTransport / UrllibTransport for OAuth. **Do not modify.**
7. `projects/paper-trading/app/oms/manager.py` — OMS contract that calls `broker.submit(broker_order)`.
8. `projects/paper-trading/tests/test_kis_order_preflight.py`, `tests/test_kis_order_request_model.py`, `tests/test_kis_order_response_model.py`, `tests/test_broker_interface.py`, `tests/test_kis_capabilities.py`, `tests/test_api_paper_status.py` — existing order-related regressions.

## Absolute prohibitions (block immediately if any apply)

- Do not enable live trading. Do not set `LIVE_TRADING_ENABLED=true`. Do not call live KIS endpoints. Do not add the live base URL (`https://openapi.koreainvestment.com:9443`) to any new code path.
- Do not implement cancel, replace, fill, open-order, or order-status endpoints. `KisBroker.cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` must keep their current `NotImplementedError` behavior unchanged.
- Do not introduce live TR_IDs (`TTTT1002U`, `TTTT1006U`, `TTTT1004U`, `TTTS1002U`, `TTTS1001U`, `TTTS0307U`, `TTTS0308U`, `TTTS0309U`, `TTTT3014U`, `TTTT3016U`, `TTTT3017U`, `TTTS3013U`) or paper-unsupported TR_IDs (`TTTS3018R`, `TTTT3039R`, `TTTS3014R`, `TTTS6036U`, `TTTS6037U`, `TTTS6038U`, `TTTS6058R`, `TTTS6059R`). Only `VTTT1002U` and `VTTT1001U` may appear in code, tests, and docs. In tests that need to demonstrate a transport gate, construct forbidden TR_ID strings by **string concatenation** (e.g., `"TTTT" + "1002U"`) so module-level grep stays clean.
- Do not invent KIS endpoints, TR IDs, headers, body fields, or response fields. Only use `Confirmed: yes` paper-supported rows in `docs/kis/MISSING_OFFICIAL_VALUES.md` §4.
- Do not import external HTTP libraries (`requests`, `httpx`, `aiohttp`, `urllib3`). Use only stdlib `urllib.request` / `urllib.parse` / `urllib.error` / `socket`.
- Do not change `app/broker/kis_http.py`. `ALLOWED_PATHS_API_AUTH_001` stays `{/oauth2/tokenP, /oauth2/revokeP}`.
- Do not modify `validate_kis_order_request`, `_validate_paper_settings`, `_to_kis_request`, `_dry_run_preview`, `_idempotency_key_for`, `_split_kis_account_no`, `KisAuthClient`, `KisAccountClient`, `KisMarketDataClient`, `sanitize_kis_response`, `KisOrderRequest`, `KisOrderResponse`, `KisPosition`, `KisCashBalance`, `KisDryRunPreview` — they stay as today.
- Do not change `OrderType.MARKET` guards, `OrderType` enum, `Side` enum, `BrokerOrder`, `OrderAck`, or any `app/domain/*`.
- Do not change `KisBroker.capabilities()` (`submission` stays `False`) or `KisBroker.healthcheck()["order_execution_implemented"]` (stays `False`) or `KisBroker.healthcheck()["order_methods_fail_closed"]` (stays `True`). These status flags are preserved to keep `app/api/routes.py` and `test_api_paper_status` unchanged.
- Do not modify `app/api/*`, `app/static/*`, `app/main.py`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/config.py`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/base.py`, `app/broker/kis_http.py`, `app/broker/kis_token_cache.py`, `app/broker/kis_quote_mapper.py`, or `app/domain/*`.
- Do not introduce FX conversion functions, exchange rate constants, base-currency aggregation, or new env variables.
- Do not read or modify `.env` / `.env.example`. Do not log or write actual app keys, app secrets, account numbers, access tokens, Bearer tokens, or PII anywhere — code, tests, docstrings, patch.md, or commit messages.
- Do not add Strategy/Agent/LLM imports of `app.broker.kis` or direct `KisBroker.place_order` calls. Orders must flow Strategy → RiskEngine → OMS → KisBroker.
- Do not run `git commit`, `git push`, `git merge`, PR creation, or deployment commands.

## Allowed file changes

| Path | Action |
| --- | --- |
| `projects/paper-trading/app/broker/kis.py` | Modify per §1 below. |
| `projects/paper-trading/tests/test_kis_paper_order_submission.py` | Create per §3. |
| `projects/paper-trading/tests/test_kis_order_preflight.py` | Narrow modify per §4 (one function). |
| `projects/paper-trading/tests/test_broker_interface.py` | Narrow modify per §4 (one assertion in one function). |
| `projects/paper-trading/README.md` | Optional 1-2 line note. May skip. |
| `projects/paper-trading/docs/ai/jobs/api-orders-paper-001/patch.md` | Create per §6. |

No other files. If you believe another file must change, stop and explain in `patch.md` instead of editing it.

## 1. Changes to `app/broker/kis.py`

### 1.1 New constants (place near `KIS_OVERSEAS_BALANCE_*` block)

```python
# docs/kis/MISSING_OFFICIAL_VALUES.md §4.2 / §4.4 / §4.5 / §4.9 (paper VTTT1002U / VTTT1001U only).
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

No other TR_ID strings (live, modify-cancel, reserve, daytime, algo) may appear anywhere in the file.

### 1.2 Helper functions

Add near other module-level helpers (after `_split_kis_account_no`):

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

- `OVRS_ORD_UNPR` uses `format(Decimal, "f")` so e.g. `Decimal("100.50")` becomes `"100.50"` (no scientific notation, no thousands separators).
- BUY omits `SLL_TYPE`. SELL sets `SLL_TYPE="00"`. (Catalog §4.4: "제거=매수, `00`=매도".)
- Do not add `CTAC_TLNO`, `MGCO_APTM_ODNO`, `START_TIME`, `END_TIME`, `ALGO_ORD_TMD_DVSN_CD`, or any other field. Paper does not need them.

### 1.3 `KisOrderTransport` Protocol + transports

Add inside `app/broker/kis.py` (after `UrllibAccountTransport`):

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

- Every failure converts to `KisOrderRejectedError` with one of the short tags above. Never put `HTTPError.read()` body, app key, app secret, or access token into the message.
- `KisOrderRejectedError.reason` (already defined on the class) carries the same short tag — verify it auto-populates from `__init__`.

### 1.4 `KisBroker.__init__` augmentation

At the end of `__init__` (after the existing assignments), add:

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

- Tests inject by setting `broker._order_transport = fake`.
- `KisAuthClient` / `KisAccountClient` / `KisMarketDataClient` constructions stay as today.

### 1.5 New `place_order` body

Replace the current `place_order` body with the version below. Everything before the `if self._settings.kis_order_dry_run:` line keeps the existing semantics (preflight + `_to_kis_request`). The dry-run branch returns the same dry-run ack. Only the post-dry-run branch is new.

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
    exchange = "NASD"  # paper default; catalog §4.9 paper exchanges (NASD/NYSE/AMEX)
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
    if "rt_cd" not in sanitized:
        self._last_error = "malformed_response"
        raise KisOrderRejectedError("malformed_response")
    rt_cd = sanitized.get("rt_cd")
    if rt_cd != "0":
        code = sanitized.get("msg_cd") or sanitized.get("msg1") or "unknown"
        self._last_error = f"kis_error:{code}"
        raise KisOrderRejectedError(f"kis_error:{code}")

    output_raw = sanitized.get("output")
    output = output_raw if isinstance(output_raw, dict) else {}
    odno_value = output.get("ODNO")
    odno = str(odno_value).strip() if odno_value is not None else ""
    odno_or_none = odno or None

    response_record = KisOrderResponse(
        internal_order_id=broker_order.oms_id,
        broker_order_id=odno_or_none,
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
        broker_order_id=odno_or_none,
        status="submitted",
        mode=self.mode,
    )
```

**Decision recorded by Codex:** if response lacks `rt_cd`, the broker fails closed with `malformed_response`. This is stricter than the plan's "alternative processing" note and is the safer of the two choices.

### 1.6 `last_order_response` property

After `last_order_preview` property:

```python
@property
def last_order_response(self) -> KisOrderResponse | None:
    return self._last_order_response
```

### 1.7 No other changes to `kis.py`

- `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` unchanged.
- `capabilities()` returns the same dict with `submission=False`.
- `healthcheck()` keeps `order_execution_implemented=False` and `order_methods_fail_closed=True`.
- `KisAuthClient`, `KisAccountClient`, `KisMarketDataClient`, `sanitize_kis_response`, `_to_kis_request`, `_dry_run_preview`, `_idempotency_key_for`, `_split_kis_account_no`, `validate_kis_order_request`, `_validate_paper_settings`, `KisHttpClient`, `KisOrderRequest`, `KisOrderResponse`, `KisPosition`, `KisCashBalance`, `KisDryRunPreview`, constants for OAuth / market data / account — all unchanged.

## 2. Imports

`app/broker/kis.py` already imports `json`, `socket`, `time`, `datetime`, `timezone`, `Decimal`, `Any`, `Protocol`, `HTTPError`, `URLError`, `Request`, `urlopen`, `dataclass`, `Side`, `OrderType`, `TradingMode`, `BrokerOrder`, `OrderAck`. Reuse. Do not add `requests`, `httpx`, `aiohttp`, `urllib3`.

## 3. New test file `tests/test_kis_paper_order_submission.py`

Use the existing `settings` fixture from `tests/conftest.py`. Provide local helpers analogous to `tests/test_kis_account_client.py`:

```python
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest

from app.broker.kis import (
    KIS_OVERSEAS_ORDER_PATH,
    KIS_PAPER_ORDER_EXCHANGES,
    KIS_PAPER_ORDER_TR_ID_US_BUY,
    KIS_PAPER_ORDER_TR_ID_US_SELL,
    KIS_PAPER_ORDER_TR_IDS,
    KisAuthClient,
    KisAuthError,
    KisBroker,
    KisConfigError,
    KisOrderRejectedError,
    KisOrderRequest,
    KisOrderResponse,
    MockOrderTransport,
    UrllibOrderTransport,
    _build_paper_order_body,
    _select_paper_order_tr_id,
)
from app.domain.enums import OrderType, Side, TradingMode
from app.domain.orders import BrokerOrder, OrderIntent


def _settings(settings, **overrides):
    data = {
        "kis_env": "paper",
        "kis_account_no": "12345678-01",
        "kis_app_key": "fake-key-XYZ",
        "kis_app_secret": "fake-secret-XYZ",
        "kis_api_mode": "paper",
        "kis_order_dry_run": False,
    }
    data.update(overrides)
    return replace(settings, **data)


def _broker_order(**overrides) -> BrokerOrder:
    now = datetime.now(timezone.utc)
    data = {
        "symbol": "AAPL",
        "side": Side.BUY,
        "quantity": 10,
        "order_type": OrderType.LIMIT,
        "limit_price": Decimal("100.50"),
        "risk_token": "rt",
        "created_at": now,
        "oms_id": "oms-1",
        "submitted_at": now,
        "quote_timestamp": now,
    }
    data.update(overrides)
    return BrokerOrder(**data)


class FakeOrderTransport:
    def __init__(self, response: dict[str, Any] | None = None, exc: Exception | None = None) -> None:
        self._response = response
        self._exc = exc
        self.calls: list[dict[str, Any]] = []

    def submit_order(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc
        if self._response is None:
            raise AssertionError("FakeOrderTransport response not set")
        return self._response


def _authenticated_broker(settings, **overrides):
    broker = KisBroker(_settings(settings, **overrides))
    broker.auth._store_token("fake-access-token", 120)
    return broker
```

Implement the 29 tests listed in plan §5. Names verbatim:

1. `test_select_paper_order_tr_id_maps_side_correctly`
2. `test_build_paper_order_body_buy_omits_sll_type`
3. `test_build_paper_order_body_sell_sets_sll_type_zero_zero`
4. `test_build_paper_order_body_contains_only_catalog_keys`
5. `test_build_paper_order_body_quantity_and_price_are_strings`
6. `test_place_order_dry_run_path_unchanged`
7. `test_place_order_dry_run_disabled_requires_authentication`
8. `test_place_order_dry_run_disabled_blocked_by_preflight`
9. `test_place_order_dry_run_disabled_blocked_by_live_trading`
10. `test_place_order_dry_run_disabled_blocked_by_market_order_type`
11. `test_place_order_dry_run_disabled_blocked_by_allow_market_orders`
12. `test_place_order_dry_run_disabled_blocked_by_kill_switch`
13. `test_place_order_dry_run_disabled_mock_mode_fails_closed`
14. `test_place_order_happy_path_buy`
15. `test_place_order_happy_path_sell`
16. `test_place_order_uses_correct_tr_id_per_side`
17. `test_place_order_kis_rejection_propagates`
18. `test_place_order_malformed_response_fails_closed` — response without `rt_cd` raises `KisOrderRejectedError("malformed_response")`. (Codex chose strict mode in §1.5.)
19. `test_place_order_http_404_fails_closed`
20. `test_place_order_transport_error_fails_closed`
21. `test_urllib_order_transport_rejects_live_host` — build the forbidden host as `"openapi" + ".koreainvestment.com:9443"` so it does not appear as a single literal in the file.
22. `test_urllib_order_transport_rejects_unsupported_tr_id` — use `"TTTT" + "1002U"` (live BUY) so the file does not literally contain the live TR_ID.
23. `test_urllib_order_transport_rejects_invalid_exchange`
24. `test_urllib_order_transport_rejects_invalid_ord_dvsn`
25. `test_place_order_response_sanitization_redacts_secrets`
26. `test_place_order_exceptions_and_repr_do_not_expose_secrets`
27. `test_place_order_via_oms_passes_riskengine` — full OMS chain. Wire RiskEngine + OMS + KisBroker(FakeOrderTransport injected after construction) and place via `oms.place(intent)`. Confirm `ack.status == "submitted"` and `ack.broker_order_id == "0000123456"`. Confirm Strategy code is NOT involved (this is an OMS-level test). Use a settings fixture where `paper_starting_cash` is high enough for RiskEngine to approve.
28. `test_kis_module_does_not_introduce_live_tr_ids` — read `app/broker/kis.py` as text and assert each forbidden TR_ID (constructed by string concatenation inside the test) is not a substring. Iterate over `("TTTT1002U", "TTTT1006U", "TTTT1004U", "TTTS1002U", "TTTS1001U", "TTTS0307U", "TTTS0308U", "TTTS0309U", "TTTT3014U", "TTTT3016U", "TTTT3017U", "TTTS3013U", "TTTS3018R", "TTTT3039R", "TTTS3014R", "TTTS6036U", "TTTS6037U", "TTTS6038U", "TTTS6058R", "TTTS6059R")` where each tuple element is itself a `"TTT" + "T1002U"` style concatenation so the test file also stays grep-clean.
29. `test_kis_paper_order_transport_uses_only_paper_base_url` — confirm `UrllibOrderTransport.submit_order` raises `disallowed_host` whenever `base_url` is anything other than the paper allowlist. Construct `kis_base_url_live` value via concatenation as in test 21.

Test 18 assertion behavior depends on Codex's §1.5 decision (strict `malformed_response`). Match the implementation.

For test 21–22 and test 28–29, the forbidden literal must be assembled via string concatenation in test source so that `grep -rn "TTTT1002U" app tests` (etc.) stays at 0 lines in the test file. Pytest still evaluates the runtime string normally.

For secret-leak assertions, the forbidden values are:
- `"fake-key-XYZ"`, `"fake-secret-XYZ"`, `"12345678"` (the digits-only account form), `"fake-access-token"`, `"Bearer fake-access-token"`.
Iterate over `repr(broker)`, `repr(broker.last_order_response)`, `str(exc)` for every raised exception, and `json.dumps(broker.last_order_response.raw_response_sanitized)`. Each must not contain any of the forbidden substrings.

## 4. Narrow modifications

### 4.1 `tests/test_kis_order_preflight.py`

Only modify `test_place_order_valid_input_with_dry_run_disabled_reaches_notimplemented`. Replace its body with:

```python
def test_place_order_valid_input_with_dry_run_disabled_requires_auth(settings):
    broker = KisBroker(replace(_settings(settings), kis_order_dry_run=False))
    with pytest.raises(KisOrderRejectedError, match="authentication_required"):
        broker.place_order(_broker_order())
```

- The function name change is optional. If kept, the body still raises `KisOrderRejectedError`, but the name then misleads — prefer renaming.
- The import already exposes `KisOrderRejectedError`.
- Do NOT touch any other function in this file. Specifically keep:
  - `test_preflight_passes_for_valid_paper_limit_order`
  - `test_preflight_allows_stop_limit_order`
  - `test_preflight_rejects_non_paper_trading_mode`
  - `test_preflight_rejects_live_trading_enabled`
  - `test_preflight_rejects_allow_market_orders_flag`
  - `test_preflight_rejects_kis_env_not_paper`
  - `test_preflight_rejects_kill_switch_engaged`
  - `test_preflight_rejects_non_limit_order_type`
  - `test_preflight_rejects_zero_quantity`
  - `test_preflight_rejects_zero_limit_price`
  - `test_preflight_rejects_missing_quote_timestamp`
  - `test_preflight_rejects_stale_quote_timestamp`
  - `test_place_order_runs_preflight_before_notimplemented` — keep as-is (uses dry-run=True default and expects KisOrderRejectedError from quantity_invalid)
  - `test_place_order_valid_input_reaches_notimplemented` — keep as-is (uses dry-run=True default and asserts `status == "dry_run"`)

### 4.2 `tests/test_broker_interface.py`

Only modify the `broker_no_dry_run.place_order(...)` block inside `test_kis_place_cancel_replace_not_implemented`. Replace:

```python
broker_no_dry_run = KisBroker(replace(_configured(settings), kis_order_dry_run=False))
with pytest.raises(NotImplementedError, match="order endpoint"):
    broker_no_dry_run.place_order(_broker_order())
```

with:

```python
broker_no_dry_run = KisBroker(replace(_configured(settings), kis_order_dry_run=False))
with pytest.raises(KisOrderRejectedError, match="authentication_required"):
    broker_no_dry_run.place_order(_broker_order())
```

- Note: the `_configured` helper uses `kis_account_no="fake-acc"`, but since auth is missing, the auth check fires first and `_split_kis_account_no` is never reached. Behavior is preserved.
- The cancel_order / replace_order `pytest.raises(NotImplementedError)` assertions in the same function MUST remain intact.
- Do NOT touch other functions: `test_broker_protocol_has_required_methods`, `test_kis_broker_constructs_in_paper`, `test_kis_broker_rejects_missing_env`, `test_kis_broker_rejects_live_env`, `test_kis_broker_missing_credentials_fails_closed`, `test_kis_protocol_methods_delegate_to_not_implemented`, `test_kis_data_methods_not_implemented`, `test_kis_broker_has_get_fills_and_get_order_status`, `test_kis_order_request_class_is_exported`, `test_kis_broker_capabilities_are_exported_and_fail_closed`, `test_kis_healthcheck_returns_disconnected_dict`, `test_kis_broker_repr_masks_secrets`, `test_strategy_package_does_not_import_kis`, and the rest of the file.

If any of those functions begin to fail because of your kis.py changes, you have overreached. Fix the implementation, not the test.

## 5. Verification commands

Run from `projects/paper-trading`:

```bash
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

Both must PASS. Also run the safety greps and include their (clean) output in `patch.md`:

```bash
grep -rnE "^(from|import) (requests|httpx|aiohttp|urllib3)" app/broker tests
grep -rn "TTTT1002U\|TTTT1006U\|TTTT1004U\|TTTS1002U\|TTTS1001U\|TTTS0307U\|TTTS0308U\|TTTS0309U\|TTTT3014U\|TTTT3016U\|TTTT3017U\|TTTS3013U" app tests
grep -rn "TTTS3018R\|TTTT3039R\|TTTS3014R\|TTTS6036U\|TTTS6037U\|TTTS6038U\|TTTS6058R\|TTTS6059R" app tests
grep -rn "openapi.koreainvestment.com:9443" app tests
grep -rn "ALLOW_MARKET_ORDERS=true\|allow_market_orders=True" app
grep -rn "Bearer eyJ" app tests docs/ai/jobs/api-orders-paper-001 || true
grep -rn "from app.broker.kis" app/strategy 2>/dev/null || true
grep -rn "from app.broker.kis" app/agent 2>/dev/null || true
```

Expected:
- External HTTP imports: 0 lines.
- Live / paper-unsupported TR_IDs in code/tests: 0 lines.
- Live base URL: only the existing pre-job line(s) in `app/config.py` (`kis_base_url_live` default + reject message) — do NOT modify these; quote them in patch.md notes if they appear.
- `ALLOW_MARKET_ORDERS=true` literal: only the existing reject-message line in `app/config.py` — do NOT modify; quote in patch.md if it appears.
- Real `Bearer eyJ` JWT tokens: 0 (matches in plan/codex-task instruction text are OK).
- Strategy/Agent KIS imports: 0 lines.

## 6. `patch.md` contents

Create `projects/paper-trading/docs/ai/jobs/api-orders-paper-001/patch.md` with these sections in order:

1. **Files Changed** — list every modified/created file.
2. **Implementation Summary** —
   - Endpoint used: POST `/uapi/overseas-stock/v1/trading/order` (catalog §4.2 paper row).
   - TR_IDs used: `VTTT1002U` (US BUY) and `VTTT1001U` (US SELL). No other TR_ID.
   - Body fields: `CANO`, `ACNT_PRDT_CD`, `OVRS_EXCG_CD="NASD"`, `PDNO`, `ORD_QTY`, `OVRS_ORD_UNPR`, `ORD_DVSN="00"` (LIMIT), `ORD_SVR_DVSN_CD="0"`, plus `SLL_TYPE="00"` on SELL only.
   - Response fields parsed: `rt_cd`, `msg_cd`, `msg1`, `output.ODNO`, `output.KRX_FWDG_ORD_ORGNO`, `output.ORD_TMD`.
   - `KisOrderRejectedError("malformed_response")` decision: strict (rt_cd absent → reject).
3. **Dry-run behavior** — explain that `kis_order_dry_run=True` short-circuits to `OrderAck(status="dry_run")` + sanitized preview, no HTTP, no transport call. `kis_order_dry_run=False` proceeds only after preflight + auth + 10-digit account split.
4. **Live (paper) submission conditions** — list all gates: preflight (`validate_kis_order_request`), `is_authenticated` + `get_access_token`, `_split_kis_account_no`, exchange/TR_ID/host/ORD_DVSN allowlists in `UrllibOrderTransport`.
5. **Fail-closed scope** — `cancel_order`, `replace_order`, `get_open_orders`, `get_fills`, `get_order_status` remain NotImplementedError; live TR_IDs and unsupported endpoints not added; capabilities `submission=False` preserved; `order_execution_implemented=False` preserved.
6. **Safety confirmation** — no secret/account/token leakage, live trading off, market-order guard intact, `OrderType.MARKET` 3-layer guard intact, `OrderType.STOP` not introduced, `app/broker/kis_http.py` unchanged, Strategy/Agent imports clean, `app/api/*` / `app/static/*` / `app/main.py` / `app/config.py` / `.env` untouched, `docs/kis/MISSING_OFFICIAL_VALUES.md` untouched.
7. **Safety grep output** — verbatim output for each grep in §5 above. Annotate any pre-existing `app/config.py` lines.
8. **Test Results** — compileall + pytest summary. Highlight 29 new tests and confirm no other existing test was broken.
9. **Remaining TODOs** — list as separate follow-up jobs:
   - `api-orders-paper-cancel-001` for `VTTT1004U` paper modify/cancel (`/order-rvsecncl`).
   - `api-orders-paper-fills-001` for `VTTS3035R` paper executions inquiry (`/inquire-ccnl`) — note paper sheet constraints.
   - Status surface job for routes.py update (advertise dry-run vs submitted via `capabilities()["submission"]` and `kis_order_entry_mode`).
10. **Claude verification prompt** — paste this exact text:

    > Read `docs/ai/jobs/api-orders-paper-001/plan.md` and `docs/ai/jobs/api-orders-paper-001/patch.md`. Run `git diff` on the working tree. Verify: (a) only `app/broker/kis.py`, `tests/test_kis_paper_order_submission.py`, the narrow `tests/test_kis_order_preflight.py` change, and the narrow `tests/test_broker_interface.py` change were modified; (b) only `VTTT1002U` and `VTTT1001U` and the paper `/uapi/overseas-stock/v1/trading/order` POST path were introduced; (c) body fields are exactly `CANO`, `ACNT_PRDT_CD`, `OVRS_EXCG_CD`, `PDNO`, `ORD_QTY`, `OVRS_ORD_UNPR`, `ORD_DVSN="00"`, `ORD_SVR_DVSN_CD="0"`, plus `SLL_TYPE="00"` on SELL only — nothing else; (d) response parser uses only `rt_cd`/`msg_cd`/`msg1`/`output.ODNO`/`output.KRX_FWDG_ORD_ORGNO`/`output.ORD_TMD`; (e) `kis_order_dry_run=True` returns `OrderAck(status="dry_run")` with no transport call; (f) `kis_order_dry_run=False` requires authentication, valid 10-digit account, paper host, paper TR_ID, paper exchange, ORD_DVSN="00"; (g) all order failures use `KisOrderRejectedError` with short tags; (h) `KisOrderResponse.raw_response_sanitized` is always passed through `sanitize_kis_response`; (i) `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` keep their NotImplementedError; (j) `capabilities()["submission"]` stays `False` and `healthcheck()["order_execution_implemented"]` stays `False`; (k) no live TR_ID, no paper-unsupported TR_ID, no live base URL, no external HTTP library; (l) no app key, app secret, access token, Bearer token, or raw account number appears in code, repr, exceptions, or test capture; (m) `OrderType.MARKET` 3-layer guard, `OrderType.STOP` absence, `ALLOW_MARKET_ORDERS=true` reject, and kill-switch behavior unchanged; (n) Strategy / Agent do not import `app.broker.kis`; (o) OMS → RiskEngine → KisBroker chain still routes orders correctly; (p) `app/broker/kis_http.py`, `app/api/*`, `app/static/*`, `app/main.py`, `app/config.py`, `.env`, `.env.example`, and `docs/kis/MISSING_OFFICIAL_VALUES.md` are unchanged; (q) full pytest passes cleanly. Output verdict `APPROVE`, `REQUEST CHANGES`, or `BLOCK` per `prompts/claude.md` rules.

11. **Follow-up Codex prompt rules** (used only if Claude returns REQUEST CHANGES or BLOCK):

    - Quote Claude's specific finding(s) verbatim under `## Findings`.
    - For each finding, write a `## Required change` block stating (a) the exact code/test edit required, (b) why this fix is in scope of api-orders-paper-001 (vs requiring a new job), (c) the corresponding safety rule from `prompts/claude.md` that the fix must preserve.
    - Re-state the absolute prohibitions and verification commands.
    - Do not expand scope: if Claude's finding requires changes outside `app/broker/kis.py` / the new test file / the two narrow test edits / `patch.md` / optional `README.md`, escalate to the human instead of expanding scope.
    - End with: "Update `patch.md` (do not create a new one). Append a `## Follow-up <N>` section explaining what changed and re-run verification. Do not commit / push / merge."

12. **Status footer**: `READY FOR REVIEW`.

Stop. Do not commit, push, merge, deploy, or modify `.env`. Hand off to the human, who will run `git diff` and invoke Claude review.
