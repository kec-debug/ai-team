# live-validation-001 — Codex 구현 지시문

You are Codex, implementing the plan at `docs/ai/jobs/live-validation-001/plan.md`.

**This job is live-validation PREPARATION only.** It must NOT add any code that enables live trading, sends real orders, toggles `KIS_ORDER_DRY_RUN=false`, allows market orders, or activates any live arm mechanism. The user has framed this as a read-only readiness UX + preflight checklist job. Treat any temptation to add a `POST /ops/arm` or `POST /ops/live/enable` as an immediate STOP signal.

Read first (in order):

1. `docs/ai/CLAUDE_CODEX_WORKFLOW.md` (root) — workflow + safety rules.
2. `docs/ai/jobs/live-validation-001/request.ko.md` — user request.
3. `docs/ai/jobs/live-validation-001/plan.md` — this task's plan.
4. `docs/ai/MASTER_TRADING_ROADMAP.md` (root) — Phase 5 safety conditions.
5. `projects/paper-trading/app/api/routes.py` — existing endpoint patterns (especially `paper_status` at line 72, `paper_engine_status` at 208, `_safety_flags` at 451).
6. `projects/paper-trading/app/api/server.py` — how `paper_engine` / `kis_broker` are attached to `app.state`.
7. `projects/paper-trading/app/static/dashboard.html` — existing structure to extend (do NOT remove existing sections).
8. `projects/paper-trading/app/config.py` — existing Settings + env helpers.
9. `projects/paper-trading/tests/test_paper_e2e_api.py`, `tests/test_dashboard.py`, `tests/test_api_paper_status.py` — patterns for new tests.

## Absolute prohibitions (any violation = immediate STOP)

- **Do not** enable live trading. Do not add code that sets `live_trading_enabled=True`. Do not add code that calls live KIS endpoints.
- **Do not** add a live arm button, live activation button, "live trading enable" toggle, `KIS_ORDER_DRY_RUN=false` toggle, or `ALLOW_MARKET_ORDERS=true` toggle to dashboard, ops endpoints, or any UI element.
- **Do not** add any `POST` / `PUT` / `DELETE` / `PATCH` route under `/ops/*`. All ops routes are GET only.
- **Do not** add a route that calls `KisBroker.place_order` / `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status`. The dashboard already exposes `/paper/order/simulate` (paper only); do not add a parallel live route.
- **Do not** change `KisBroker.place_order` / `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` bodies.
- **Do not** change `validate_kis_order_request`, `_validate_paper_settings`, `_split_kis_account_no`, `OrderType.MARKET` / `OrderType.STOP_LIMIT` guards.
- **Do not** introduce `OrderType.STOP`, FX conversion functions, exchange rate constants, or base-currency aggregation.
- **Do not** invent KIS endpoints, TR IDs, payloads, headers, or response fields. The new ops endpoints do not need any catalog values.
- **Do not** import external HTTP libraries (`requests`, `httpx`, `aiohttp`, `urllib3`, `openpyxl`, `pandas`). The new ops code is pure-Python in-process.
- **Do not** read or modify `.env`, `.env.example`. Do not log or write actual app keys, app secrets, account numbers, access tokens, or Bearer tokens anywhere — code, tests, docstrings, patch.md.
- **Do not** modify `docs/kis/MISSING_OFFICIAL_VALUES.md`.
- **Do not** add Strategy / Agent / LLM imports of broker modules.
- **Do not** modify `app/broker/*`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/domain/*`, `app/api/server.py`, `app/main.py`.
- **Do not** run `git commit`, `git push`, `git merge`, PR creation, or deployment.

If you discover that completing the job requires modifying a forbidden file, STOP and document in `patch.md` under `## Out-of-scope discovery` instead of editing.

## Allowed file changes

| Path | Action |
| --- | --- |
| `app/ops/__init__.py` | Create. Package marker + re-export `compute_live_validation_status`. |
| `app/ops/preflight.py` | Create per §1 below. |
| `app/api/routes.py` | Modify (additive only): add two `@router.get("/ops/...")` handlers + private serializer helper. |
| `app/config.py` | Modify (additive only): add 2 settings fields + env loaders. Existing fields untouched. |
| `app/static/dashboard.html` | Modify (additive only): banner + 2 sections + CSS + JS. Existing sections untouched. |
| `projects/paper-trading/README.md` | Modify: add "운영자 가이드 (한국어)" section at end. |
| `tests/test_ops_preflight.py` | Create per §3. |
| `tests/test_ops_endpoints.py` | Create per §3. |
| `tests/test_dashboard.py` | Modify (additive only): add ~4 narrow tests. Existing assertions untouched. |
| `docs/ai/jobs/live-validation-001/patch.md` | Create per §5. |

No other files. If a code or test change feels necessary elsewhere, STOP.

## 1. `app/ops/preflight.py`

```python
"""Live validation preflight evaluation — read-only, pure functions.

This module computes a readiness summary for live validation but never
enables anything. `live_validation_ready=True` is a UX hint only; the
codebase contains no path that uses this flag to relax any safety gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.config import Settings
from app.domain.enums import TradingMode


@dataclass(frozen=True)
class PreflightItem:
    key: str
    label_ko: str
    passed: bool
    detail_ko: str


@dataclass(frozen=True)
class LiveValidationStatus:
    live_trading_enabled: bool
    trading_mode: str
    market_orders_allowed: bool
    kis_order_dry_run: bool
    kill_switch_engaged: bool
    broker_type: str
    kis_config_loaded: bool
    kis_authenticated: bool
    kis_market_data_available: bool
    kis_account_loaded: bool
    kis_order_entry_ready: bool
    live_validation_ready: bool
    banner_level: str
    banner_text_ko: str
    items: tuple[PreflightItem, ...]


_BANNER_SAFE = (
    "현재 시스템은 paper / dry-run 전용입니다. "
    "live trading 은 비활성화되어 있으며, 실제 주문은 전송되지 않습니다."
)
_BANNER_DANGER_LIVE = "위험: live trading 값이 true 입니다. 주문 기능은 차단되어야 합니다."
_BANNER_DANGER_MARKET = "위험: 시장가 주문 허용 값이 true 입니다. 시스템은 fail-closed 해야 합니다."
_BANNER_DANGER_SECRET = "위험: secret 노출 가능성이 감지되었습니다."
_BANNER_WARN_KILL = "주의: kill switch 가 engaged 입니다. 새 주문이 차단됩니다."
_BANNER_WARN_AUTH = "주의: KIS config 는 로드됐으나 인증 토큰이 없습니다."


def compute_live_validation_status(
    *,
    settings: Settings,
    paper_engine,  # PaperEngine | None
    kis_broker,    # KisBroker | None
    paper_status_payload: dict[str, Any],
) -> LiveValidationStatus:
    """Compute readiness status. Pure function (no side effects).

    Inputs already evaluated by caller (paper_status_payload from /paper/status).
    """
    trading_mode = paper_status_payload.get("mode", "")
    live_enabled = bool(paper_status_payload.get("live_trading_enabled", False))
    market_allowed = bool(paper_status_payload.get("market_orders_allowed", False))
    dry_run = bool(paper_status_payload.get("kis_order_dry_run", False))
    kill_switch = bool(paper_status_payload.get("kill_switch_engaged", False))
    broker_type = str(paper_status_payload.get("broker_type", "<unknown>"))
    kis_config_loaded = bool(paper_status_payload.get("kis_config_loaded", False))
    kis_authenticated = bool(paper_status_payload.get("kis_authenticated", False))
    kis_market_data_available = bool(paper_status_payload.get("kis_market_data_available", False))
    kis_account_loaded = bool(paper_status_payload.get("kis_account_loaded", False))
    kis_order_entry_ready = bool(paper_status_payload.get("kis_order_entry_ready", False))
    secret_exposed = bool(paper_status_payload.get("secret_exposed", False))

    has_recent_paper = _has_recent_paper_activity(paper_engine)

    # ready calculation — STRICT AND
    ready = (
        trading_mode == "paper"
        and live_enabled is False
        and market_allowed is False
        and dry_run is True
        and kill_switch is False
        and kis_config_loaded
        and secret_exposed is False
        and has_recent_paper
    )

    # banner level escalation
    if live_enabled or market_allowed or secret_exposed:
        banner_level = "danger"
        if live_enabled:
            banner_text = _BANNER_DANGER_LIVE
        elif market_allowed:
            banner_text = _BANNER_DANGER_MARKET
        else:
            banner_text = _BANNER_DANGER_SECRET
    elif kill_switch:
        banner_level = "warning"
        banner_text = _BANNER_WARN_KILL
    elif kis_config_loaded and not kis_authenticated:
        banner_level = "warning"
        banner_text = _BANNER_WARN_AUTH
    else:
        banner_level = "info"
        banner_text = _BANNER_SAFE

    items: tuple[PreflightItem, ...] = (
        PreflightItem("paper_mode_confirmed", "Paper mode 확인", trading_mode == "paper", f"trading_mode={trading_mode!r}"),
        PreflightItem("live_disabled_confirmed", "Live disabled 확인", live_enabled is False, f"live_trading_enabled={live_enabled}"),
        PreflightItem("market_orders_disabled_confirmed", "Market order disabled 확인", market_allowed is False, f"allow_market_orders={market_allowed}"),
        PreflightItem("kis_dry_run_enabled_confirmed", "KIS dry-run enabled 확인", dry_run is True, f"kis_order_dry_run={dry_run}"),
        PreflightItem("secret_exposed_false_confirmed", "Secret exposed false 확인", secret_exposed is False, f"secret_exposed={secret_exposed}"),
        PreflightItem("kill_switch_off_confirmed", "Kill switch off 확인", kill_switch is False, f"kill_switch_engaged={kill_switch}"),
        PreflightItem("kis_config_loaded_confirmed", "KIS config loaded 확인", kis_config_loaded, f"kis_config_loaded={kis_config_loaded}"),
        PreflightItem("dashboard_simulation_available", "Dashboard simulation 가능 확인", paper_engine is not None, "paper_engine is " + ("present" if paper_engine is not None else "missing")),
        PreflightItem("paper_journal_writable", "Paper journal 기록 가능 확인", paper_engine is not None and hasattr(paper_engine, "journal"), "journal " + ("present" if paper_engine is not None and hasattr(paper_engine, "journal") else "missing")),
        PreflightItem("report_generation_available", "Report 생성 가능 확인", paper_engine is not None, "engine present"),
        PreflightItem("daily_loss_limit_configured", "1일 손실 제한 설정 확인", settings.live_validation_daily_loss_limit_usd is not None, _detail_optional(settings.live_validation_daily_loss_limit_usd, "USD")),
        PreflightItem("max_orders_per_day_configured", "최대 주문 수 제한 설정 확인", settings.live_validation_max_orders_per_day is not None, _detail_optional(settings.live_validation_max_orders_per_day, "orders/day")),
        PreflightItem("symbol_allowlist_configured", "허용 종목 whitelist 확인", len(settings.symbol_allowlist) > 0, f"{len(settings.symbol_allowlist)} symbol(s)"),
        PreflightItem("recent_test_passed_manual", "최근 테스트 통과 여부 수동 확인", False, "수동 확인 필요 — 운영자가 별도 확인"),
    )

    return LiveValidationStatus(
        live_trading_enabled=live_enabled,
        trading_mode=trading_mode,
        market_orders_allowed=market_allowed,
        kis_order_dry_run=dry_run,
        kill_switch_engaged=kill_switch,
        broker_type=broker_type,
        kis_config_loaded=kis_config_loaded,
        kis_authenticated=kis_authenticated,
        kis_market_data_available=kis_market_data_available,
        kis_account_loaded=kis_account_loaded,
        kis_order_entry_ready=kis_order_entry_ready,
        live_validation_ready=ready,
        banner_level=banner_level,
        banner_text_ko=banner_text,
        items=items,
    )


def _detail_optional(value, unit: str) -> str:
    if value is None:
        return "not configured"
    return f"configured at {value} {unit}"


def _has_recent_paper_activity(paper_engine) -> bool:
    if paper_engine is None:
        return False
    journal = getattr(paper_engine, "journal", None)
    if journal is None:
        return False
    trades = getattr(journal, "trades", None) or []
    return len(trades) > 0
```

## 2. `app/api/routes.py` additive endpoints

Insert near other `/paper/*` endpoints (after `paper_engine_status` is a natural place):

```python
from app.ops.preflight import LiveValidationStatus, PreflightItem, compute_live_validation_status


def _serialize_preflight_item(item: PreflightItem) -> dict[str, Any]:
    return {"key": item.key, "label_ko": item.label_ko, "passed": item.passed, "detail_ko": item.detail_ko}


def _serialize_live_validation_status(status: LiveValidationStatus, *, include_checklist: bool) -> dict[str, Any]:
    base = {
        "live_trading_enabled": status.live_trading_enabled,
        "trading_mode": status.trading_mode,
        "market_orders_allowed": status.market_orders_allowed,
        "kis_order_dry_run": status.kis_order_dry_run,
        "kill_switch_engaged": status.kill_switch_engaged,
        "broker_type": status.broker_type,
        "kis_config_loaded": status.kis_config_loaded,
        "kis_authenticated": status.kis_authenticated,
        "kis_market_data_available": status.kis_market_data_available,
        "kis_account_loaded": status.kis_account_loaded,
        "kis_order_entry_ready": status.kis_order_entry_ready,
        "live_validation_ready": status.live_validation_ready,
        "banner_level": status.banner_level,
        "banner_text_ko": status.banner_text_ko,
        "secret_exposed": False,
    }
    if include_checklist:
        base["items"] = [_serialize_preflight_item(i) for i in status.items]
    return base


@router.get("/ops/status")
def ops_status(request: Request) -> dict[str, Any]:
    paper_payload = paper_status(request)
    settings = request.app.state.settings
    paper_engine = getattr(request.app.state, "paper_engine", None)
    kis_broker = getattr(request.app.state, "kis_broker", None)
    status = compute_live_validation_status(
        settings=settings,
        paper_engine=paper_engine,
        kis_broker=kis_broker,
        paper_status_payload=paper_payload,
    )
    return _serialize_live_validation_status(status, include_checklist=False)


@router.get("/ops/preflight")
def ops_preflight(request: Request) -> dict[str, Any]:
    paper_payload = paper_status(request)
    settings = request.app.state.settings
    paper_engine = getattr(request.app.state, "paper_engine", None)
    kis_broker = getattr(request.app.state, "kis_broker", None)
    status = compute_live_validation_status(
        settings=settings,
        paper_engine=paper_engine,
        kis_broker=kis_broker,
        paper_status_payload=paper_payload,
    )
    return _serialize_live_validation_status(status, include_checklist=True)
```

**Strictly GET only.** No POST / PUT / DELETE / PATCH under `/ops/*`. If FastAPI's automatic 405 handling doesn't suffice for a regression test, the test can explicitly call `client.post("/ops/status")` and assert 405.

## 3. `app/config.py` additive fields

Add two fields to the `@dataclass(frozen=True) class Settings:` block (place after `kill_switch_engaged`):

```python
live_validation_daily_loss_limit_usd: Decimal | None = None
live_validation_max_orders_per_day: int | None = None
```

Add two helpers (near `_decimal_env` / `_int_env`):

```python
def _optional_decimal_env(name: str) -> Decimal | None:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return None
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal for {name}") from exc


def _optional_int_env(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid integer for {name}") from exc
```

In `load_settings()` return statement, add:

```python
live_validation_daily_loss_limit_usd=_optional_decimal_env("LIVE_VALIDATION_DAILY_LOSS_LIMIT_USD"),
live_validation_max_orders_per_day=_optional_int_env("LIVE_VALIDATION_MAX_ORDERS_PER_DAY"),
```

**Do not** modify `.env.example`. **Do not** add these settings as gates anywhere — they are status-reporting only.

## 4. Dashboard additions

Add to `app/static/dashboard.html`:

1. **Banner** at the top of `<body>` (before all other sections):

   ```html
   <div id="ops-banner" class="banner banner-info" role="status">
     <strong id="ops-banner-icon">ℹ️ 안내</strong>
     <span id="ops-banner-text">현재 시스템은 paper / dry-run 전용입니다. live trading 은 비활성화되어 있으며, 실제 주문은 전송되지 않습니다.</span>
   </div>
   ```

2. **Section: Live Validation 준비 상태** (after KIS status section, before manual paper order section):

   ```html
   <section id="live-validation-readiness">
     <h2>🛡️ Live Validation 준비 상태</h2>
     <p class="muted">아래 상태는 read-only 입니다. live 활성화는 본 화면에서 불가능하며, 별도 절차로만 가능합니다.</p>
     <table>
       <tbody>
         <tr><th>live_trading_enabled</th><td id="lv-live-trading-enabled">-</td></tr>
         <tr><th>trading_mode</th><td id="lv-trading-mode">-</td></tr>
         <tr><th>market_orders_allowed</th><td id="lv-market-orders-allowed">-</td></tr>
         <tr><th>kis_order_dry_run</th><td id="lv-kis-order-dry-run">-</td></tr>
         <tr><th>kill_switch_engaged</th><td id="lv-kill-switch">-</td></tr>
         <tr><th>broker_type</th><td id="lv-broker-type">-</td></tr>
         <tr><th>kis_config_loaded</th><td id="lv-kis-config-loaded">-</td></tr>
         <tr><th>kis_authenticated</th><td id="lv-kis-authenticated">-</td></tr>
         <tr><th>kis_market_data_available</th><td id="lv-kis-market-data">-</td></tr>
         <tr><th>kis_account_loaded</th><td id="lv-kis-account-loaded">-</td></tr>
         <tr><th>kis_order_entry_ready</th><td id="lv-kis-order-entry-ready">-</td></tr>
         <tr><th>live_validation_ready</th><td id="lv-validation-ready">-</td></tr>
       </tbody>
     </table>
   </section>
   ```

3. **Section: Preflight Checklist** (immediately after Live Validation Readiness section):

   ```html
   <section id="preflight-checklist">
     <h2>✅ Preflight Checklist</h2>
     <ul id="preflight-items"></ul>
   </section>
   ```

4. **CSS additions** (in existing `<style>` block):

   ```css
   .banner { padding: 0.8em 1em; margin-bottom: 1em; border-radius: 6px; font-size: 1em; }
   .banner-info { background: #e3f2fd; color: #0d47a1; border: 1px solid #90caf9; }
   .banner-warning { background: #fff3e0; color: #e65100; border: 2px solid #ffb74d; }
   .banner-danger { background: #ffebee; color: #b71c1c; border: 3px solid #ef5350; font-weight: bold; }
   .muted { color: #666; font-size: 0.9em; }
   .check-pass { color: #2e7d32; }
   .check-fail { color: #c62828; }
   #preflight-items { list-style: none; padding: 0; }
   #preflight-items li { padding: 0.3em 0; }
   ```

5. **JS additions**: extend `ENDPOINTS` with `opsStatus: "/ops/status"` + `opsPreflight: "/ops/preflight"`. Add `refreshOpsStatus()` + `renderChecklist()` functions, and call `refreshOpsStatus()` in the existing dashboard refresh cycle.

   ```javascript
   async function refreshOpsStatus() {
     try {
       const ops = await fetchJson(ENDPOINTS.opsPreflight);
       setText("lv-live-trading-enabled", String(ops.live_trading_enabled));
       setText("lv-trading-mode", ops.trading_mode);
       setText("lv-market-orders-allowed", String(ops.market_orders_allowed));
       setText("lv-kis-order-dry-run", String(ops.kis_order_dry_run));
       setText("lv-kill-switch", String(ops.kill_switch_engaged));
       setText("lv-broker-type", ops.broker_type);
       setText("lv-kis-config-loaded", String(ops.kis_config_loaded));
       setText("lv-kis-authenticated", String(ops.kis_authenticated));
       setText("lv-kis-market-data", String(ops.kis_market_data_available));
       setText("lv-kis-account-loaded", String(ops.kis_account_loaded));
       setText("lv-kis-order-entry-ready", String(ops.kis_order_entry_ready));
       setText("lv-validation-ready", ops.live_validation_ready ? "READY" : "NOT READY");
       const banner = document.getElementById("ops-banner");
       banner.className = "banner banner-" + ops.banner_level;
       document.getElementById("ops-banner-icon").textContent =
         ops.banner_level === "danger" ? "⚠️ 위험"
         : ops.banner_level === "warning" ? "⚠️ 주의"
         : "ℹ️ 안내";
       document.getElementById("ops-banner-text").textContent = " " + ops.banner_text_ko;
       renderChecklist(ops.items);
     } catch (err) {
       console.error("ops status failed", err);
     }
   }
   function renderChecklist(items) {
     const ul = document.getElementById("preflight-items");
     ul.innerHTML = "";
     for (const item of items) {
       const li = document.createElement("li");
       li.className = item.passed ? "check-pass" : "check-fail";
       li.textContent = (item.passed ? "✅ " : "❌ ") + item.label_ko + " — " + item.detail_ko;
       ul.appendChild(li);
     }
   }
   ```

   Call `refreshOpsStatus()` from the existing refresh function so it runs on initial load + each refresh tick.

**Forbidden additions** (do not create):

- `<button id="btn-arm-live">`, `<button id="btn-enable-live">`, `<button id="btn-disable-dry-run">`, `<button id="btn-allow-market">`, or any UI that toggles `live_trading_enabled` / `kis_order_dry_run` / `allow_market_orders` / `kill_switch_engaged`.
- Any `fetch(..., { method: "POST" })` against `/ops/*`.
- Any inline `<script>` that mutates `app.state.*` server-side.

## 5. README operator guide

Append to `projects/paper-trading/README.md` (place at the end; do not remove existing content):

(use the Korean operator guide template from plan.md §4.4 verbatim)

The section must explicitly contain the sentence:

> 본 시스템은 `live_validation_ready=READY` 가 표시되어도 실제 live 주문을 전송할 코드 경로를 보유하지 않습니다.

## 6. Tests

### 6.1 `tests/test_ops_preflight.py`

Pure-function tests of `compute_live_validation_status` with fabricated `paper_status_payload` dicts. ~15 tests as listed in plan §5. Use `dataclasses.replace(settings, ...)` for variants. Helper `_payload(**overrides)` for the payload dict.

For "no recent paper activity" test, pass `paper_engine=None` or a mock with empty `journal.trades`.

### 6.2 `tests/test_ops_endpoints.py`

```python
from fastapi.testclient import TestClient

from app.api.server import create_app


def test_get_ops_status_returns_all_flags():
    with TestClient(create_app()) as client:
        response = client.get("/ops/status")
    assert response.status_code == 200
    body = response.json()
    for key in (
        "live_trading_enabled", "trading_mode", "market_orders_allowed",
        "kis_order_dry_run", "kill_switch_engaged", "broker_type",
        "kis_config_loaded", "kis_authenticated", "kis_market_data_available",
        "kis_account_loaded", "kis_order_entry_ready", "live_validation_ready",
        "banner_level", "banner_text_ko", "secret_exposed",
    ):
        assert key in body
    assert body["secret_exposed"] is False
    # /ops/status should NOT include checklist
    assert "items" not in body


def test_get_ops_preflight_returns_checklist():
    with TestClient(create_app()) as client:
        response = client.get("/ops/preflight")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert len(body["items"]) == 14
    for item in body["items"]:
        assert set(item) == {"key", "label_ko", "passed", "detail_ko"}


def test_ops_endpoints_are_get_only():
    with TestClient(create_app()) as client:
        assert client.post("/ops/status").status_code == 405
        assert client.post("/ops/preflight").status_code == 405
        assert client.put("/ops/status").status_code == 405
        assert client.delete("/ops/preflight").status_code == 405


def test_ops_endpoints_do_not_expose_secrets():
    forbidden = ("KIS_APP_KEY", "KIS_APP_SECRET", "KIS_ACCOUNT_NO", "app_secret", "access_token", "Bearer ")
    with TestClient(create_app()) as client:
        responses = [client.get("/ops/status"), client.get("/ops/preflight")]
    for response in responses:
        for needle in forbidden:
            assert needle not in response.text


def test_routes_has_no_mutating_ops_routes():
    import pathlib
    text = (pathlib.Path(__file__).resolve().parents[1] / "app" / "api" / "routes.py").read_text(encoding="utf-8")
    for verb in ("post", "put", "delete", "patch"):
        # forbidden mutating routes under /ops/
        # built via concat to keep grep clean on this test file itself
        prefix = '@router.' + verb + '("/ops/'
        assert prefix not in text


def test_default_banner_is_info_in_safe_paper_setup():
    with TestClient(create_app()) as client:
        response = client.get("/ops/status").json()
    # Default paper setup → safe info banner
    assert response["banner_level"] == "info"
    assert "paper / dry-run 전용" in response["banner_text_ko"]


def test_default_ready_false_without_recent_paper_activity():
    """Fresh server start with no paper trades yet → ready=False."""
    with TestClient(create_app()) as client:
        response = client.get("/ops/preflight").json()
    assert response["live_validation_ready"] is False
    # The "수동 확인 필요" item should also be False by default
    manual = next(i for i in response["items"] if i["key"] == "recent_test_passed_manual")
    assert manual["passed"] is False


def test_ops_preflight_ready_becomes_true_after_recent_simulation():
    """After at least one paper fill, the recent-activity gate flips green."""
    from tests.test_paper_e2e_api import _order_payload  # reuse paper-ux-001 helper
    with TestClient(create_app()) as client:
        client.post("/paper/order/simulate", json=_order_payload())
        response = client.get("/ops/preflight").json()
    # ready may still be False (manual item, daily-loss-limit etc.) but
    # the dashboard_simulation_available + recent activity items should pass.
    keys = {i["key"]: i["passed"] for i in response["items"]}
    assert keys["paper_mode_confirmed"] is True
    assert keys["live_disabled_confirmed"] is True
    assert keys["market_orders_disabled_confirmed"] is True
    assert keys["kis_dry_run_enabled_confirmed"] is True
    assert keys["secret_exposed_false_confirmed"] is True
    assert keys["dashboard_simulation_available"] is True
```

### 6.3 `tests/test_dashboard.py` additive

Add four tests at the end of the file (do not touch existing tests):

```python
def test_dashboard_has_live_validation_readiness_section():
    response = TestClient(create_app()).get("/dashboard")
    assert "Live Validation 준비 상태" in response.text


def test_dashboard_has_preflight_checklist_section():
    response = TestClient(create_app()).get("/dashboard")
    assert "Preflight Checklist" in response.text


def test_dashboard_has_safety_banner_text():
    response = TestClient(create_app()).get("/dashboard")
    assert "paper / dry-run 전용" in response.text
    assert "live trading 은 비활성화되어 있으며" in response.text


def test_dashboard_has_no_live_arm_or_enable_buttons():
    response = TestClient(create_app()).get("/dashboard")
    forbidden_ids = (
        'id="btn-arm-live"',
        'id="btn-enable-live"',
        'id="btn-disable-dry-run"',
        'id="btn-allow-market"',
        'id="btn-toggle-kill-switch"',
    )
    for marker in forbidden_ids:
        assert marker not in response.text
```

## 7. Verification commands

Run from `projects/paper-trading`:

```bash
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

Both must PASS. Confirm test count = 520 baseline + ~26 new = ~546 passed.

Also run safety greps and include in `patch.md`:

```bash
grep -rnE "^(from|import) (requests|httpx|aiohttp|urllib3|openpyxl|pandas)" app/ops app/api tests/test_ops_*.py
grep -rn "live_trading_enabled = True\|live_trading_enabled=True" app/ops app/api app/static
grep -rnE "@router\.(post|put|delete|patch)\(\"/ops/" app
grep -rn "kis_broker.place_order\|kis_broker.cancel_order\|kis_broker.replace_order" app/ops app/api app/static
grep -rn "Bearer eyJ\|access_token=eyJ\|appkey=PS" app/ops app/api app/static
```

Expected: all 0 lines.

## 8. `patch.md` contents

Create `projects/paper-trading/docs/ai/jobs/live-validation-001/patch.md` with these sections:

1. **Files Changed**
2. **Implementation Summary** — banner + 2 sections + 2 endpoints + 2 settings fields + README.
3. **Live Validation Readiness Display Method** — describe banner / readiness card / checklist.
4. **Preflight Checklist Items** — list all 14.
5. **Why Real Live Orders Are Impossible** — cite: no live endpoint added; KisBroker order methods unchanged; OMS path unchanged; dashboard has no arm button; `/ops/*` GET-only; `KIS_ORDER_DRY_RUN=true` default + `load_settings` `ALLOW_MARKET_ORDERS=true` reject preserved; `live_validation_ready` is UX hint only with no code path consuming it.
6. **Safety Confirmation** — no secret/account/token exposure, `live_trading_enabled` False, market guard intact, KIS endpoints unchanged, no external HTTP libs, `.env*` untouched.
7. **Safety grep output** — verbatim.
8. **Test Results** — compileall + pytest summary (520 baseline + new = ~546).
9. **Remaining TODOs** — `live-validation-002` (future) would handle manual arm + actual live transmission with separate explicit user approval + Phase 5 condition recheck. Do not start this job; this patch's contribution is preparation only.
10. **Claude verification prompt**:

    > Read `docs/ai/jobs/live-validation-001/plan.md` and `patch.md`. Run `git diff`. Verify: (a) no live trading was enabled; (b) no live arm / enable / disable-dry-run / allow-market button exists on the dashboard; (c) `/ops/status` and `/ops/preflight` are GET-only with no mutating verbs; (d) `KisBroker.place_order` / cancel / replace / get_open_orders / get_fills / get_order_status bodies are unchanged; (e) `validate_kis_order_request` and OMS / RiskEngine / Strategy / broker boundaries are unchanged; (f) no external HTTP library imports were added; (g) no real app key / app secret / account number / Bearer token / access token appears anywhere; (h) `.env` / `.env.example` are unchanged; (i) `docs/kis/MISSING_OFFICIAL_VALUES.md` is unchanged; (j) `live_validation_ready=True` is a UX hint only — no code path consumes it to relax any safety; (k) banner escalates to danger when `live_trading_enabled` / `market_orders_allowed` / `secret_exposed` is True; (l) full pytest passes (520 baseline + new tests). Output verdict `APPROVE`, `REQUEST CHANGES`, or `BLOCK`.

11. **Follow-up Codex prompt rules** (used only if Claude returns REQUEST CHANGES or BLOCK):

    - Quote findings verbatim under `## Findings`.
    - For each finding, write `## Required change` with the exact edit, why it is in scope of live-validation-001 prep (NOT activation), and the safety rule preserved.
    - Re-state absolute prohibitions and verification commands.
    - Do not expand scope: any change outside the allowed file list requires human approval.
    - End with: "Update `patch.md` (do not create a new one). Append a `## Follow-up <N>` section explaining what changed and re-run verification. Do not commit / push / merge."

12. **Status footer**: `READY FOR REVIEW`.

Stop. Do not commit, push, merge, deploy, or modify `.env`. Hand off to the human, who will run `git diff` and invoke Claude review.
