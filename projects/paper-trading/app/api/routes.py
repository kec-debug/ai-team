from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.domain.market import StrategyInput
from app.strategy import STRATEGY_NAMES

router = APIRouter()


class PaperRunRequest(BaseModel):
    snapshots: list[StrategyInput]
    strategy: str = "premarket_gap_volume_breakout"


class PaperRunResponse(BaseModel):
    results: list[dict[str, Any]]
    summary: dict[str, int]


@router.get("/healthz")
def healthz() -> dict[str, bool]:
    return {"ok": True}


@router.get("/paper/status")
def paper_status(request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    broker = request.app.state.broker
    session_router = getattr(request.app.state, "session_router", None)
    portfolio = getattr(request.app.state, "portfolio", None)
    kis_broker = getattr(request.app.state, "kis_broker", None)
    kis_loaded = bool(
        settings.kis_env
        and settings.kis_account_no
        and settings.kis_app_key
        and settings.kis_app_secret
    )
    kis_health = kis_broker.healthcheck() if kis_broker else {}
    market_health = kis_health.get("market_data", {})
    kis_order_entry_mode = "disabled"
    if kis_broker is not None:
        settings_safe = (
            settings.trading_mode.value == "paper"
            and settings.live_trading_enabled is False
            and settings.allow_market_orders is False
            and settings.kis_env == "paper"
            and settings.kill_switch_engaged is False
        )
        kis_order_entry_mode = "not_implemented" if settings_safe else "disabled"
    kis_order_entry_ready = kis_broker is not None and kis_order_entry_mode != "disabled"
    capabilities = (
        kis_broker.capabilities()
        if kis_broker
        else {
            "submission": False,
            "cancel": False,
            "replace": False,
            "open_orders": False,
            "fills": False,
            "order_status": False,
        }
    )
    session_policy = session_router.policy_for_us() if session_router is not None else None
    portfolio_snapshot = portfolio.get_snapshot() if portfolio is not None else None
    return {
        "ok": True,
        "mode": settings.trading_mode.value,
        "live_enabled": settings.live_trading_enabled,
        "strategies": list(STRATEGY_NAMES),
        "safety": {
            "paper_only": True,
            "live_trading_disabled": not settings.live_trading_enabled,
            "market_orders_disabled": True,
            "strategy_emits_non_executable_only": True,
            "oms_required": True,
        },
        # mvp-006-1: broker/runtime metadata + KIS configurability flags.
        # Credentials are never included in this response.
        "broker_type": type(broker).__name__,
        "broker_environment": "paper",
        "live_trading_enabled": settings.live_trading_enabled,
        "market_orders_allowed": settings.allow_market_orders,
        "kis_config_loaded": kis_loaded,
        "kis_authenticated": bool(kis_health.get("authenticated", False)),
        "kis_account_loaded": bool(kis_health.get("account_loaded", False)),
        "kis_market_data_available": bool(market_health.get("connected", False)),
        "last_broker_error": kis_health.get("last_error") if kis_broker else None,
        "account_no_masked": kis_broker.account.masked_account_no() if kis_broker else "<unset>",
        "secret_exposed": False,
        "configured_brokers": list(getattr(request.app.state, "configured_brokers", [])),
        "kis_order_entry_ready": kis_order_entry_ready,
        "kis_order_entry_mode": kis_order_entry_mode,
        "kis_order_methods_fail_closed": True,
        "kill_switch_engaged": bool(settings.kill_switch_engaged),
        "kis_order_submission_available": bool(capabilities.get("submission", False)),
        "kis_cancel_available": bool(capabilities.get("cancel", False)),
        "kis_replace_available": bool(capabilities.get("replace", False)),
        "kis_open_orders_available": bool(capabilities.get("open_orders", False)),
        "kis_fills_available": bool(capabilities.get("fills", False)),
        "session": {
            "market": "US",
            "current": session_policy.session.value if session_policy else None,
            "orders_allowed": bool(session_policy.orders_allowed) if session_policy else False,
            "allowed_strategies": list(session_policy.allowed_strategies) if session_policy else [],
        },
        "portfolio": {
            "positions_count": len(portfolio_snapshot.positions) if portfolio_snapshot else 0,
            "market_value": str(portfolio_snapshot.market_value) if portfolio_snapshot else "0",
            "realized_pnl": str(portfolio_snapshot.realized_pnl) if portfolio_snapshot else "0",
        },
    }


@router.post("/paper/run", response_model=PaperRunResponse)
def paper_run(payload: PaperRunRequest, request: Request) -> PaperRunResponse:
    if payload.strategy not in STRATEGY_NAMES:
        raise HTTPException(status_code=400, detail="Unknown strategy")
    settings = request.app.state.settings
    if settings.live_trading_enabled:
        raise HTTPException(status_code=503, detail="Live trading is disabled in Phase 1")
    if payload.strategy != request.app.state.strategy.name:
        raise HTTPException(status_code=400, detail="Strategy is not active")

    run_results = request.app.state.runner.run_once(payload.snapshots)
    results = []
    for item in run_results:
        results.append(
            {
                "symbol": item.symbol,
                "strategy": item.strategy.model_dump(mode="json"),
                "oms_ack": item.oms_ack.__dict__ if item.oms_ack else None,
                "oms_error": item.oms_error,
            }
        )
    return PaperRunResponse(
        results=results,
        summary={
            "total": len(results),
            "passed": sum(1 for item in run_results if item.strategy.passed),
            "submitted": sum(1 for item in run_results if item.oms_ack is not None),
            "blocked": sum(1 for item in run_results if not item.strategy.passed),
        },
    )
