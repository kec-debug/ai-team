# api-orders-paper-002-cancel-replace — Codex 구현 지시문

You are Codex, implementing the plan at `docs/ai/jobs/api-orders-paper-002-cancel-replace/plan.md` inside the `projects/paper-trading` package.

Read first (in order):

1. `docs/ai/CLAUDE_CODEX_WORKFLOW.md` (root).
2. `docs/ai/jobs/api-orders-paper-002-cancel-replace/request.ko.md`.
3. `docs/ai/jobs/api-orders-paper-002-cancel-replace/plan.md` — this task's plan. Stay within scope.
4. `docs/kis/MISSING_OFFICIAL_VALUES.md` (root) §4.2 / §4.6 / §4.8 — official catalog. Only `Confirmed: yes` paper-supported rows for US 정정·취소 may be used. The only TR_ID this job introduces is `VTTT1004U`.
5. `docs/ai/jobs/KIS_2-check/plan.md`, `recommendation.md`, `review.md` — audit decisions that gate this scope.
6. `projects/paper-trading/app/broker/kis.py` — existing adapter from api-orders-paper-001 (`KisOrderTransport` Protocol, `MockOrderTransport`, `UrllibOrderTransport`, `KisBroker.place_order`, `_last_order_response`).
7. `projects/paper-trading/app/broker/kis_http.py` — **do not modify**.
8. `projects/paper-trading/tests/test_kis_paper_order_submission.py` — patterns for transport-injection tests.
9. `projects/paper-trading/tests/test_paper_e2e_pipeline.py` — `_RaiseOnCallOrderTransport` pattern.
10. `projects/paper-trading/tests/test_broker_interface.py`, `tests/test_kis_http_boundaries.py` — existing cancel/replace regressions you will narrowly update.

## Absolute prohibitions (block immediately if any apply)

- Do not enable live trading. Do not call live KIS endpoints. Do not add the live base URL to any new code path.
- Do not introduce live TR_IDs (`TTTT1002U`, `TTTT1006U`, `TTTT1004U`, `TTTS1002U`, `TTTS1001U`, `TTTS1003U`, `TTTS0307U`, `TTTS0308U`, `TTTS0309U`, `TTTT3014U`, `TTTT3016U`, `TTTT3017U`, `TTTS3013U`). The only TR_ID this job introduces is `VTTT1004U` (paper US 정정·취소 공용). Forbidden TR_ID strings in tests must be constructed via string concatenation (e.g., `"TTTT" + "1004U"`) so the file stays grep-clean.
- Do not introduce paper-unsupported TR_IDs (`TTTS3018R`, `TTTT3039R`, `TTTS3014R`, `TTTS6036U`, `TTTS6037U`, `TTTS6038U`, `TTTS6058R`, `TTTS6059R`).
- Do not implement `get_open_orders`, `get_fills`, or `get_order_status`. They are BLOCKED-BY-DOCS per KIS_2-check audit. Keep their existing `NotImplementedError` raises intact.
- Do not implement Asian-exchange cancel/replace. `KIS_PAPER_CANCEL_REPLACE_TR_IDS` must be exactly `frozenset({"VTTT1004U"})` (size 1). `KIS_PAPER_ORDER_EXCHANGES` (from api-orders-paper-001) stays `frozenset({"NASD", "NYSE", "AMEX"})` — do not add Asia exchange codes.
- Do not invent KIS endpoints, TR IDs, headers, body fields, or response fields. Only use catalog §4.2 / §4.6 `Confirmed: yes` rows. In particular, the cancel/replace body must contain only the fields listed in §4.6 — do not add `ORD_DVSN`, `SLL_TYPE`, `CTAC_TLNO`, `MGCO_APTM_ODNO`, `ORD_SVR_DVSN_CD`, `START_TIME`/`END_TIME`/`ALGO_ORD_TMD_DVSN_CD`, or anything else.
- Do not import external HTTP libraries (`requests`, `httpx`, `aiohttp`, `urllib3`). stdlib `urllib.request` / `urllib.parse` / `urllib.error` / `socket` / `json` only.
- Do not modify `app/broker/kis_http.py`. `ALLOWED_PATHS_API_AUTH_001` stays `{/oauth2/tokenP, /oauth2/revokeP}`.
- Do not modify `validate_kis_order_request`, `_validate_paper_settings`, `_to_kis_request`, `_dry_run_preview`, `_idempotency_key_for`, `_split_kis_account_no`, `sanitize_kis_response`, `KisAuthClient`, `KisAccountClient`, `KisMarketDataClient`, `KisOrderRequest`, `KisPosition`, `KisCashBalance`, `KisDryRunPreview`, KIS_OVERSEAS_PRICE_* / KIS_OVERSEAS_BALANCE_* constants, market data transports, account transports.
- Do not change `OrderType.MARKET` guards, `OrderType` enum, `Side` enum, `BrokerOrder`, `OrderAck`, `OrderIntent`, `app/domain/*`.
- Do not change `KisBroker.capabilities()` (`submission`/`cancel`/`replace`/...all stay `False`). Do not change `KisBroker.healthcheck()["order_execution_implemented"]` (stays `False`) or `order_methods_fail_closed` (stays `True`).
- Do not modify `app/api/*`, `app/static/*`, `app/main.py`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/config.py`.
- Do not extend OMS protocol (no `OMS.cancel(...)` / `OMS.replace(...)` in this job). G2 selection A is adapter-level only.
- Do not introduce FX conversion / exchange rate constants / new env variables.
- Do not read or modify `.env` / `.env.example`. Do not write actual app keys, app secrets, account numbers, access tokens, or Bearer tokens anywhere.
- Do not modify `docs/kis/MISSING_OFFICIAL_VALUES.md`.
- Do not run `git commit`, `git push`, `git merge`, PR creation, or deployment.

## Allowed file changes

| Path | Action |
| --- | --- |
| `projects/paper-trading/app/broker/kis.py` | Modify per §1 below. |
| `projects/paper-trading/tests/test_kis_paper_order_cancel_replace.py` | Create per §3. |
| `projects/paper-trading/tests/test_broker_interface.py` | Narrow modify per §4 (2 functions, ~3 assertion lines). |
| `projects/paper-trading/tests/test_kis_http_boundaries.py` | Narrow modify per §4 (1 function, 2 assertion lines). |
| `projects/paper-trading/README.md` | Optional 1-2 line note; may skip. |
| `projects/paper-trading/docs/ai/jobs/api-orders-paper-002-cancel-replace/patch.md` | Create per §6. |

No other files. If you discover a real gap, STOP and document in `patch.md` rather than expanding scope.

## 1. Changes to `app/broker/kis.py`

### 1.1 Import addition

At the top, add `import dataclasses` (or `from dataclasses import dataclass, replace as dataclass_replace`). Use whichever style matches the existing file; `dataclasses.replace` is preferred for clarity.

### 1.2 `KisOrderResponse` extension (G1 + G3)

Locate the existing dataclass and add three default fields at the end:

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

All three defaults preserve existing kwargs-only callers. The `status` field gains four valid values across the lifecycle: `"submitted"` (place_order success), `"cancelled"` (cancel success), `"replaced"` (replace success — old entry), `"replacement_submitted"` (replace success — new entry).

### 1.3 Cancel/replace constants

Add immediately after the existing `KIS_PAPER_ORDER_*` constants block:

```python
# docs/kis/MISSING_OFFICIAL_VALUES.md §4.2 / §4.6 (paper US 정정·취소 공용 VTTT1004U only).
KIS_OVERSEAS_CANCEL_REPLACE_PATH = "/uapi/overseas-stock/v1/trading/order-rvsecncl"
KIS_PAPER_CANCEL_REPLACE_TR_ID_US = "VTTT1004U"
KIS_PAPER_CANCEL_REPLACE_TR_IDS = frozenset({KIS_PAPER_CANCEL_REPLACE_TR_ID_US})
KIS_PAPER_ORDER_ALL_TR_IDS = KIS_PAPER_ORDER_TR_IDS | KIS_PAPER_CANCEL_REPLACE_TR_IDS
KIS_RVSE_CNCL_DVSN_REPLACE = "01"
KIS_RVSE_CNCL_DVSN_CANCEL = "02"
KIS_RVSE_CNCL_DVSN_VALUES = frozenset({KIS_RVSE_CNCL_DVSN_REPLACE, KIS_RVSE_CNCL_DVSN_CANCEL})
KIS_PAPER_CANCEL_UNPR = "0"
```

No other TR_ID strings (live US, holiday, reserve, daytime, algo, or Asia paper cancel) may appear anywhere in `app/broker/kis.py`.

### 1.4 Body builder helpers (place near existing `_select_paper_order_tr_id` / `_build_paper_order_body`)

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
        "RVSE_CNCL_DVSN_CD": KIS_RVSE_CNCL_DVSN_CANCEL,
        "ORD_QTY": str(int(original_qty)),
        "OVRS_ORD_UNPR": KIS_PAPER_CANCEL_UNPR,
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
        "RVSE_CNCL_DVSN_CD": KIS_RVSE_CNCL_DVSN_REPLACE,
        "ORD_QTY": str(int(new_qty)),
        "OVRS_ORD_UNPR": format(new_limit_price, "f"),
    }
```

Both bodies contain exactly the 8 keys above. No additional fields.

### 1.5 Transport signature extension

Update the `KisOrderTransport` Protocol and both transport classes (`MockOrderTransport.submit_order`, `UrllibOrderTransport.submit_order`) to add `path: str` keyword argument:

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
        path: str,
        body: dict[str, str],
    ) -> dict[str, Any]:
        """Submit a single KIS paper order (place or cancel/replace) and return the raw response dict."""


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
        path: str,
        body: dict[str, str],
    ) -> dict[str, Any]:
        raise KisOrderRejectedError("mock_mode_no_network")
```

`UrllibOrderTransport.submit_order` body becomes:

```python
EXPECTED_PATH_BY_TR_ID: dict[str, str] = {
    KIS_PAPER_ORDER_TR_ID_US_BUY: KIS_OVERSEAS_ORDER_PATH,
    KIS_PAPER_ORDER_TR_ID_US_SELL: KIS_OVERSEAS_ORDER_PATH,
    KIS_PAPER_CANCEL_REPLACE_TR_ID_US: KIS_OVERSEAS_CANCEL_REPLACE_PATH,
}


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
        path: str,
        body: dict[str, str],
    ) -> dict[str, Any]:
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
            if body.get("ORD_DVSN") != KIS_PAPER_ORDER_LIMIT_DVSN:
                raise KisOrderRejectedError("ord_dvsn_not_limit")
        else:
            if body.get("RVSE_CNCL_DVSN_CD") not in KIS_RVSE_CNCL_DVSN_VALUES:
                raise KisOrderRejectedError("invalid_rvse_cncl_dvsn")

        url = f"{base_url.rstrip('/')}{path}"
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

URL is now `base_url + path` (path passed in). The hardcoded `KIS_OVERSEAS_ORDER_PATH` reference in the previous URL line is gone — the path comes from the caller and is validated against tr_id.

### 1.6 `KisBroker.__init__` augmentation

Add after the existing `_last_order_response` assignment:

```python
self._order_history: dict[str, KisOrderResponse] = {}
```

### 1.7 `KisBroker.place_order` narrow changes

Two changes only:

1. The transport call must now pass `path=KIS_OVERSEAS_ORDER_PATH`:

   ```python
   raw = self._order_transport.submit_order(
       base_url=self._settings.kis_base_url_paper,
       access_token=access_token,
       app_key=self._settings.kis_app_key or "",
       app_secret=self._settings.kis_app_secret or "",
       tr_id=tr_id,
       path=KIS_OVERSEAS_ORDER_PATH,
       body=body,
   )
   ```

2. On success, ALSO populate `_order_history`:

   ```python
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
       exchange=exchange,  # whatever exchange was selected — currently "NASD"
   )
   self._last_order_response = response_record
   if odno_or_none is not None:
       self._order_history[odno_or_none] = response_record
   self._last_error = None
   return OrderAck(
       oms_id=broker_order.oms_id,
       broker_order_id=odno_or_none,
       status="submitted",
       mode=self.mode,
   )
   ```

   When `output.ODNO` is missing → existing strict `KisOrderRejectedError("malformed_response")` path; history not populated (return path never reached).

   Pass the broker's selected `exchange` (currently `"NASD"`) into the `KisOrderResponse.exchange` field so cancel/replace can recover it.

3. **No other change to place_order.** All preflight / dry-run / auth / split / body / transport / sanitize logic stays identical.

### 1.8 `KisBroker.cancel_order(broker_order_id)` body

Replace the current `NotImplementedError`-raising body with the implementation from plan §4.7. Reproduced here for reference:

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
    except KisConfigError as exc:
        self._last_error = "invalid_kis_account_no_format"
        raise KisOrderRejectedError("invalid_kis_account_no_format") from exc

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

Add `_dry_run_cancel_preview` helper on `KisBroker`:

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

### 1.9 `KisBroker.replace_order(broker_order_id, broker_order)` body

Replace the current `NotImplementedError`-raising body with the implementation from plan §4.8. Reproduced:

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
    except KisConfigError as exc:
        self._last_error = "invalid_kis_account_no_format"
        raise KisOrderRejectedError("invalid_kis_account_no_format") from exc

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

Add `_dry_run_replace_preview` helper on `KisBroker`:

```python
def _dry_run_replace_preview(
    self, entry: KisOrderResponse, request: KisOrderRequest
) -> KisDryRunPreview:
    payload = {
        "operation": "replace",
        "broker_order_id": entry.broker_order_id,
        "symbol": entry.symbol,
        "exchange": entry.exchange,
        "old_quantity": entry.quantity,
        "old_limit_price": str(entry.limit_price),
        "new_quantity": request.quantity,
        "new_limit_price": str(request.limit_price),
        "tr_id": KIS_PAPER_CANCEL_REPLACE_TR_ID_US,
        "path": KIS_OVERSEAS_CANCEL_REPLACE_PATH,
        "account_no": self._account.masked_account_no(),
    }
    return KisDryRunPreview(
        request=request,
        payload_sanitized=sanitize_kis_response(payload, self._settings),
    )
```

### 1.10 Capability surface preservation

Do not change `capabilities()`. It must still return:

```python
{"submission": False, "cancel": False, "replace": False, "open_orders": False, "fills": False, "order_status": False}
```

Do not change `healthcheck()` — `order_execution_implemented` stays `False`, `order_methods_fail_closed` stays `True`. These match `test_api_paper_status`, `test_kis_capabilities_fail_closed`, `test_kis_healthcheck_returns_disconnected_dict` regressions.

### 1.11 Out-of-scope methods stay fail-closed

`get_open_orders`, `get_fills`, `get_order_status` keep their existing `NotImplementedError` raises verbatim. Do not touch them.

## 2. Imports

Existing imports in `app/broker/kis.py` cover everything except `dataclasses.replace`. Add `import dataclasses` (or `from dataclasses import replace as dataclass_replace` — match existing style; if `replace` conflicts with another name imported in the file, use `import dataclasses` and call `dataclasses.replace(...)`).

## 3. New test file `tests/test_kis_paper_order_cancel_replace.py`

Use existing `settings` fixture from `tests/conftest.py`. Provide local helpers:

```python
import json
import pathlib
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest

from app.broker.kis import (
    KIS_OVERSEAS_CANCEL_REPLACE_PATH,
    KIS_OVERSEAS_ORDER_PATH,
    KIS_PAPER_CANCEL_REPLACE_TR_ID_US,
    KIS_PAPER_CANCEL_REPLACE_TR_IDS,
    KIS_PAPER_ORDER_ALL_TR_IDS,
    KIS_PAPER_ORDER_EXCHANGES,
    KIS_PAPER_ORDER_TR_ID_US_BUY,
    KIS_PAPER_ORDER_TR_ID_US_SELL,
    KIS_RVSE_CNCL_DVSN_CANCEL,
    KIS_RVSE_CNCL_DVSN_REPLACE,
    KisAuthClient,
    KisBroker,
    KisOrderRejectedError,
    KisOrderRequest,
    KisOrderResponse,
    MockOrderTransport,
    UrllibOrderTransport,
    _build_paper_cancel_body,
    _build_paper_replace_body,
)
from app.domain.enums import OrderType, Side, TradingMode
from app.domain.orders import BrokerOrder


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
    def __init__(
        self,
        responses: list[dict[str, Any]] | None = None,
        exc: Exception | None = None,
    ):
        self._responses = list(responses or [])
        self._exc = exc
        self.calls: list[dict[str, Any]] = []

    def submit_order(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc
        if not self._responses:
            raise AssertionError("FakeOrderTransport responses exhausted")
        return self._responses.pop(0)


def _seed_history(broker, **overrides) -> KisOrderResponse:
    """Inject a KisOrderResponse directly into broker._order_history for tests."""
    now = datetime.now(timezone.utc)
    data = {
        "internal_order_id": "oms-1",
        "broker_order_id": "OLD_ODNO_111",
        "broker": "KisBroker",
        "status": "submitted",
        "submitted_at": now,
        "symbol": "AAPL",
        "side": Side.BUY,
        "quantity": 10,
        "limit_price": Decimal("100.50"),
        "raw_response_sanitized": {"rt_cd": "0", "output": {"ODNO": "OLD_ODNO_111"}},
        "exchange": "NASD",
    }
    data.update(overrides)
    entry = KisOrderResponse(**data)
    broker._order_history[entry.broker_order_id] = entry
    return entry


def _authenticated_broker(settings, **overrides):
    broker = KisBroker(_settings(settings, **overrides))
    broker.auth._store_token("fake-access-token", 120)
    return broker
```

Implement all functions listed in plan §5 (`test_build_paper_cancel_body_contains_only_catalog_keys`, ..., 50+). Names verbatim from plan §5.

Critical assertions checklist (sample — match these in the actual tests):

- Catalog field set: `set(body.keys()) == {"CANO", "ACNT_PRDT_CD", "OVRS_EXCG_CD", "PDNO", "ORGN_ODNO", "RVSE_CNCL_DVSN_CD", "ORD_QTY", "OVRS_ORD_UNPR"}` for both cancel and replace bodies.
- `body["RVSE_CNCL_DVSN_CD"] == "02"` for cancel; `"01"` for replace.
- `body["OVRS_ORD_UNPR"] == "0"` for cancel.
- `body["ORD_DVSN"]` not in body.
- For cancel dry-run: transport's FakeOrderTransport.calls is empty (or use `_RaiseOnCallOrderTransport` to assert non-invocation).
- For happy-path cancel: `transport.calls[0]["tr_id"] == "VTTT1004U"`, `transport.calls[0]["path"] == "/uapi/overseas-stock/v1/trading/order-rvsecncl"`, `broker._order_history[old_id].status == "cancelled"`.
- For happy-path replace: `ack.status == "replacement_submitted"`, `ack.broker_order_id == "NEW_ODNO_999"`, `broker._order_history[old_id].status == "replaced"`, `broker._order_history[old_id].replacement_broker_order_id == "NEW_ODNO_999"`, `broker._order_history["NEW_ODNO_999"].replaces_broker_order_id == old_id`, `broker._order_history["NEW_ODNO_999"].quantity == new_qty`, `broker._order_history["NEW_ODNO_999"].limit_price == new_price`.
- For chained replace: three entries in history after two replaces.
- For Asia exchange in history (test 42/43): `_seed_history(broker, exchange="SEHK")` → transport raises `invalid_exchange`. Use `_seed_history` helper to inject SEHK directly.
- For module surface test (test 44): `text = pathlib.Path(__file__).resolve().parents[1] / "app" / "broker" / "kis.py"; content = text.read_text(); for forbidden in ("TTTT" + "1004U", "TTTS" + "1003U", "TTTS" + "0309U"): assert forbidden not in content`.
- For module surface test (test 45): `assert KIS_PAPER_CANCEL_REPLACE_TR_IDS == frozenset({"VTTT1004U"})` and `assert len(KIS_PAPER_CANCEL_REPLACE_TR_IDS) == 1`.
- For secret-leak tests: forbidden tokens = `("fake-key-XYZ", "fake-secret-XYZ", "12345678", "fake-access-token", "Bearer fake-access-token")`. Iterate over `repr(broker)`, `json.dumps([entry.raw_response_sanitized for entry in broker._order_history.values()])`, every raised `str(exc)`.

For path/tr_id mismatch tests (38, 39), build the forbidden TR_ID literal via concatenation: `forbidden_live_tr_id = "TTTT" + "1004U"`; for transport tests pass `tr_id=forbidden_live_tr_id` and assert `disallowed_tr_id` (37) or pass the valid place_order TR_ID with the wrong path and assert `path_tr_id_mismatch` (38/39).

For `test_replace_order_runs_preflight_first` (test 20), seed history then call `broker.replace_order(old_id, _broker_order(quantity=0))`. Preflight runs FIRST (before history lookup) and should raise `KisOrderRejectedError("quantity_invalid")`.

## 4. Narrow modifications

### 4.1 `tests/test_broker_interface.py`

**Function 1**: `test_kis_place_cancel_replace_not_implemented` (line 110). Change lines 118-121:

```python
# Before:
with pytest.raises(NotImplementedError):
    broker.cancel_order("x")
with pytest.raises(NotImplementedError):
    broker.replace_order("x", _broker_order())

# After:
with pytest.raises(KisOrderRejectedError, match="unknown_broker_order_id"):
    broker.cancel_order("x")
with pytest.raises(KisOrderRejectedError, match="unknown_broker_order_id"):
    broker.replace_order("x", _broker_order())
```

**Function 2**: `test_kis_protocol_methods_delegate_to_not_implemented` (line 124). Change line 127-128:

```python
# Before:
with pytest.raises(NotImplementedError):
    broker.cancel("x")

# After:
with pytest.raises(KisOrderRejectedError, match="unknown_broker_order_id"):
    broker.cancel("x")
```

`broker.open_orders()` assertion stays `NotImplementedError` — do not touch.

Other functions in this file: **do not touch**.

### 4.2 `tests/test_kis_http_boundaries.py`

**Function**: `test_cancel_replace_queries_fail_closed` (line 199). Change lines 200-204 (cancel/replace assertions only):

```python
# Before:
def test_cancel_replace_queries_fail_closed(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(NotImplementedError, match="cancel_order"):
        broker.cancel_order("broker-1")
    with pytest.raises(NotImplementedError, match="replace_order"):
        broker.replace_order("broker-1", _broker_order())
    with pytest.raises(NotImplementedError, match="get_open_orders"):
        broker.get_open_orders()
    with pytest.raises(NotImplementedError, match="get_fills"):
        broker.get_fills()
    with pytest.raises(NotImplementedError, match="get_order_status"):
        broker.get_order_status("broker-1")

# After:
def test_cancel_replace_queries_fail_closed(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(KisOrderRejectedError, match="unknown_broker_order_id"):
        broker.cancel_order("broker-1")
    with pytest.raises(KisOrderRejectedError, match="unknown_broker_order_id"):
        broker.replace_order("broker-1", _broker_order())
    with pytest.raises(NotImplementedError, match="get_open_orders"):
        broker.get_open_orders()
    with pytest.raises(NotImplementedError, match="get_fills"):
        broker.get_fills()
    with pytest.raises(NotImplementedError, match="get_order_status"):
        broker.get_order_status("broker-1")
```

**The `get_open_orders` / `get_fills` / `get_order_status` `NotImplementedError` assertions MUST remain intact** — they are the BLOCKED-BY-DOCS regression from KIS_2-check audit.

`KisOrderRejectedError` is already imported (the test file imports it at line 14-15).

Other functions in this file: **do not touch**. Specifically, `test_kis_modules_do_not_import_third_party_http_libs` and `test_kis_http_has_no_live_transport_class` regressions must stay.

## 5. Verification commands

Run from `projects/paper-trading`:

```bash
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

Both must PASS. Also run safety greps and include output in `patch.md`:

```bash
grep -rnE "^(from|import) (requests|httpx|aiohttp|urllib3)" app/broker tests
grep -rn "TTTT1002U\|TTTT1006U\|TTTT1004U\|TTTS1002U\|TTTS1001U\|TTTS1003U\|TTTS0307U\|TTTS0308U\|TTTS0309U\|TTTT3014U\|TTTT3016U\|TTTT3017U\|TTTS3013U" app tests
grep -rn "TTTS3018R\|TTTT3039R\|TTTS3014R\|TTTS6036U\|TTTS6037U\|TTTS6038U\|TTTS6058R\|TTTS6059R" app tests
grep -rn "openapi.koreainvestment.com:9443" app tests
grep -rn "ALLOW_MARKET_ORDERS=true\|allow_market_orders=True" app
grep -rn "Bearer eyJ" app tests docs/ai/jobs/api-orders-paper-002-cancel-replace || true
grep -rn "from app.broker.kis" app/strategy app/agent 2>/dev/null || true
```

Expected:
- External HTTP imports: 0 lines.
- Live / paper-unsupported TR_IDs (including `TTTS1003U` Hong Kong live cancel): 0 lines in code or tests.
- Live base URL / `ALLOW_MARKET_ORDERS=true` literal: only pre-existing `app/config.py` guard lines (do NOT modify).
- `Bearer eyJ`: only existing test/plan/codex-task text.
- Strategy/Agent KIS imports: 0 lines.

## 6. `patch.md` contents

Create `projects/paper-trading/docs/ai/jobs/api-orders-paper-002-cancel-replace/patch.md` with these sections in order:

1. **Files Changed** — list every modified/created file.
2. **Implementation Summary** —
   - Endpoint used: POST `/uapi/overseas-stock/v1/trading/order-rvsecncl` (catalog §4.2 paper row).
   - TR_ID used: `VTTT1004U` (US 정정·취소 공용). No other TR_ID.
   - Body fields: `CANO`, `ACNT_PRDT_CD`, `OVRS_EXCG_CD`, `PDNO`, `ORGN_ODNO`, `RVSE_CNCL_DVSN_CD` ("01" replace / "02" cancel), `ORD_QTY`, `OVRS_ORD_UNPR` ("0" for cancel, new price for replace).
   - Response fields parsed: `rt_cd`, `msg_cd`, `msg1`, `output.ODNO` (strict — missing odno on replace = malformed). Other catalog response fields preserved in `raw_response_sanitized`.
3. **G1~G4 design decisions** — explicitly answer each:
   - **G1**: Selection A. `KisOrderResponse` gained three default fields: `exchange: str = "NASD"`, `replacement_broker_order_id: str | None = None`, `replaces_broker_order_id: str | None = None`. Justify: existing kwargs callers unaffected; supports future Asia expansion.
   - **G2**: Selection A. Adapter level only. No `OMS.cancel` / `OMS.replace` / runtime helper. `capabilities()["cancel"]` and `["replace"]` stay `False`. Cite api-orders-paper-001 status-surface policy.
   - **G3**: Old entry kept in `_order_history` with `status="replaced"` + `replacement_broker_order_id=new_odno`. New entry stored with `status="replacement_submitted"` + `replaces_broker_order_id=old_id`. `_last_order_response` points to new entry.
   - **G4**: `KIS_PAPER_CANCEL_REPLACE_TR_IDS` is exactly `frozenset({"VTTT1004U"})` (size 1). `KIS_PAPER_ORDER_EXCHANGES` (NASD/NYSE/AMEX) reused from api-orders-paper-001; Asia exchange codes never appear in code/tests.
4. **Dry-run behavior** — cancel returns `None` + sets `_last_order_preview`. Replace returns `OrderAck(status="dry_run", broker_order_id=None)` + sets `_last_order_preview`. Both skip the transport call.
5. **Live (paper) submission conditions** — full gate list: paper settings (`_validate_paper_settings`) + (replace only) `validate_kis_order_request` preflight + history lookup + (replace only) symbol/side match + dry-run check + auth + 10-digit account split + body builder + transport allowlists (host/path/tr_id/exchange/dvsn).
6. **Fail-closed scope** — `get_open_orders`, `get_fills`, `get_order_status` still `NotImplementedError`. capabilities flags still all `False`. `order_execution_implemented` still `False`. No live TR_IDs, no Asia paper TR_IDs.
7. **Safety confirmation** — no secret/account/token leak, live trading off, market-order/STOP guards intact, OMS/RiskEngine boundary intact, Strategy/Agent isolation, `app/broker/kis_http.py` untouched, `.env`/`.env.example`/`app/config.py`/`docs/kis/MISSING_OFFICIAL_VALUES.md` untouched.
8. **Safety grep output** — verbatim output for each grep in §5.
9. **Test Results** — compileall + pytest summary. Highlight test count delta from new file + 3 narrow updates.
10. **Remaining TODOs** — separate follow-up jobs: `KIS_3-inquire-ccnl-output-fields` (catalog gap for output[] sub-fields, blocks the three query methods); `api-orders-paper-002-query-only` (after KIS_3); status-surface job to advertise cancel/replace via capabilities; OMS protocol extension for cancel/replace (audit G2 selection A defers this).
11. **Claude verification prompt** — paste this exact text:

    > Read `docs/ai/jobs/api-orders-paper-002-cancel-replace/plan.md` and `docs/ai/jobs/api-orders-paper-002-cancel-replace/patch.md`. Run `git diff`. Verify: (a) only `app/broker/kis.py`, `tests/test_kis_paper_order_cancel_replace.py` (new), and narrow edits to `tests/test_broker_interface.py` (2 functions) + `tests/test_kis_http_boundaries.py` (1 function) were modified; (b) only `VTTT1004U` and the paper `/order-rvsecncl` POST path were introduced; no Asia paper cancel TR_ID, no live cancel TR_ID, no paper-unsupported TR_ID; (c) cancel body fields are exactly `{CANO, ACNT_PRDT_CD, OVRS_EXCG_CD, PDNO, ORGN_ODNO, RVSE_CNCL_DVSN_CD="02", ORD_QTY, OVRS_ORD_UNPR="0"}`; replace body fields are exactly the same set with `RVSE_CNCL_DVSN_CD="01"`, new ORD_QTY, new OVRS_ORD_UNPR; (d) response parser uses only `rt_cd`/`msg_cd`/`msg1`/`output.ODNO`; (e) G1~G4 design decisions are honored (KisOrderResponse +3 default fields, adapter-level only, history preservation with chain, US-only exchanges); (f) `kis_order_dry_run=True` short-circuits cancel/replace without transport call; (g) `kis_order_dry_run=False` requires auth + 10-digit account + paper host + paper TR_ID + path/tr_id match + US exchange + RVSE_CNCL_DVSN_CD ∈ {"01","02"}; (h) all failures use `KisOrderRejectedError` with short tags; (i) `KisOrderResponse.raw_response_sanitized` is always passed through `sanitize_kis_response`; (j) `get_open_orders` / `get_fills` / `get_order_status` keep their NotImplementedError; (k) `capabilities()["cancel"]` and `["replace"]` stay `False`; (l) `OrderType.MARKET` 3-layer guard, `OrderType.STOP` absence, `ALLOW_MARKET_ORDERS=true` reject, kill-switch behavior unchanged; (m) Strategy / Agent do not import `app.broker.kis`; (n) `app/broker/kis_http.py`, `app/api/*`, `app/static/*`, `app/main.py`, `app/config.py`, `.env`, `.env.example`, `docs/kis/MISSING_OFFICIAL_VALUES.md` are unchanged; (o) `_order_history` does not silently drop or overwrite old IDs after replace (G3); (p) Asia paper TR_IDs and SEHK/TKSE/HASE/VNSE/SHAA/SZAA exchange codes do not appear in code or tests; (q) full pytest passes cleanly. Output verdict `APPROVE`, `REQUEST CHANGES`, or `BLOCK`.

12. **Follow-up Codex prompt rules** (only if Claude returns REQUEST CHANGES or BLOCK):

    - Quote findings verbatim under `## Findings`.
    - For each finding, write `## Required change` stating the exact code/test edit, why it is in scope for `api-orders-paper-002-cancel-replace`, and the safety rule that must be preserved.
    - Re-state absolute prohibitions and verification commands.
    - Do not expand scope: any change outside the 4 allowed files + `patch.md` requires human approval.
    - End with: "Update `patch.md` (do not create a new one). Append a `## Follow-up <N>` section explaining what changed and re-run verification. Do not commit / push / merge."

13. **Status footer**: `READY FOR REVIEW`.

Stop. Do not commit, push, merge, deploy, or modify `.env`. Hand off to the human, who will run `git diff` and invoke Claude review.
