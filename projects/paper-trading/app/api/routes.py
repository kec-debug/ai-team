import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.domain.enums import OrderType, Session, Side
from app.domain.market import StrategyInput
from app.domain.orders import OrderIntent
from app.domain.quote import Quote
from app.ops.preflight import LiveValidationStatus, PreflightItem, compute_live_validation_status
from app.reports.dry_run_analyzer import analyze_run, find_latest_run_dir, write_analysis_files
from app.runtime.paper_status import (
    build_paper_account_status,
    build_paper_engine_status,
    build_paper_journal_status,
    build_paper_positions_status,
)
from app.strategy import STRATEGY_NAMES

router = APIRouter()

_DASHBOARD_HTML_PATH = Path(__file__).resolve().parents[1] / "static" / "dashboard.html"


class PaperRunRequest(BaseModel):
    snapshots: list[StrategyInput]
    strategy: str = "premarket_gap_volume_breakout"


class DryRunTickRequest(BaseModel):
    snapshots: list[StrategyInput] = []


class AnalyzeRequest(BaseModel):
    run_dir: str | None = None


class PaperRunResponse(BaseModel):
    results: list[dict[str, Any]]
    summary: dict[str, int]


class PaperOrderSimulateRequest(BaseModel):
    symbol: str
    side: Side
    quantity: int = Field(gt=0)
    order_type: OrderType
    limit_price: Decimal = Field(gt=Decimal("0"))
    stop_price: Decimal | None = None
    mock_bid: Decimal = Field(gt=Decimal("0"))
    mock_ask: Decimal = Field(gt=Decimal("0"))
    mock_last: Decimal = Field(gt=Decimal("0"))
    mock_volume: int = Field(ge=0)
    currency: str = "USD"
    session: Session | None = Session.REGULAR


@router.get("/healthz")
def healthz() -> dict[str, bool]:
    return {"ok": True}


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page() -> HTMLResponse:
    return HTMLResponse(content=_DASHBOARD_HTML_PATH.read_text(encoding="utf-8"))


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
    dry_run_controller = getattr(request.app.state, "dry_run_controller", None)
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
        "kis_token_expires_at_masked_or_relative": kis_health.get("token_expires_at"),
        "kis_account_loaded": bool(kis_health.get("account_loaded", False)),
        "kis_positions_loaded": bool(kis_health.get("positions_loaded", False)),
        "kis_cash_balance_loaded": bool(kis_health.get("cash_balance_loaded", False)),
        "kis_market_data_available": bool(market_health.get("connected", False)),
        "last_broker_error": kis_health.get("last_error") if kis_broker else None,
        "kis_last_error": kis_health.get("last_error") if kis_broker else None,
        "last_error": getattr(request.app.state, "paper_last_error", None),
        "account_no_masked": kis_broker.account.masked_account_no() if kis_broker else "<unset>",
        "secret_exposed": False,
        "configured_brokers": list(getattr(request.app.state, "configured_brokers", [])),
        "kis_order_entry_ready": kis_order_entry_ready,
        "kis_order_entry_mode": kis_order_entry_mode,
        "kis_order_methods_fail_closed": True,
        "kill_switch_engaged": bool(settings.kill_switch_engaged),
        "kis_order_dry_run": bool(settings.kis_order_dry_run),
        "dry_run_running": bool(dry_run_controller and dry_run_controller.is_running()),
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


@router.get("/paper/account")
def paper_account(request: Request) -> dict[str, Any]:
    engine = _paper_engine(request)
    return {
        "starting_cash": _decimal_map(request.app.state.paper_starting_cash),
        "cash": _decimal_map(engine.cash_by_currency()),
        "realized_pnl": _decimal_map(engine.account.realized_pnl),
        "safety": _safety_flags(request),
        "secret_exposed": False,
    }


@router.get("/paper/positions")
def paper_positions(request: Request) -> dict[str, Any]:
    snapshot = _paper_engine(request).portfolio.get_snapshot()
    return {
        "positions_count": len(snapshot.positions),
        "positions": [_position_dict(position) for position in snapshot.positions.values()],
        "realized_pnl": str(snapshot.realized_pnl),
        "unrealized_pnl": str(snapshot.unrealized_pnl),
        "market_value": str(snapshot.market_value),
        "realized_pnl_by_currency": _decimal_map(snapshot.realized_pnl_by_currency),
        "unrealized_pnl_by_currency": _decimal_map(snapshot.unrealized_pnl_by_currency),
        "market_value_by_currency": _decimal_map(snapshot.market_value_by_currency),
        "secret_exposed": False,
    }


@router.get("/paper/fills")
def paper_fills(request: Request) -> dict[str, Any]:
    journal = _paper_engine(request).journal
    return {
        "fills": [_trade_dict(entry) for entry in journal.trades],
        "rejected_orders": [_order_log_dict(entry) for entry in journal.orders],
        "recent_orders": [_order_log_dict(entry) for entry in reversed(journal.orders[-50:])],
        "secret_exposed": False,
    }


@router.get("/paper/engine/status")
def paper_engine_status(request: Request) -> dict[str, Any]:
    engine = _paper_engine(request)
    return {
        "account": build_paper_account_status(engine, request.app.state.paper_starting_cash),
        "portfolio": build_paper_positions_status(engine),
        "journal": build_paper_journal_status(engine, limit=50),
        "engine": build_paper_engine_status(engine, project_dir=request.app.state.project_dir),
        "safety": _safety_flags(request),
        "secret_exposed": False,
    }


def _serialize_preflight_item(item: PreflightItem) -> dict[str, Any]:
    return {
        "key": item.key,
        "label_ko": item.label_ko,
        "passed": item.passed,
        "detail_ko": item.detail_ko,
    }


def _serialize_live_validation_status(
    status: LiveValidationStatus, *, include_checklist: bool
) -> dict[str, Any]:
    payload = {
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
        payload["items"] = [_serialize_preflight_item(item) for item in status.items]
    return payload


@router.get("/ops/status")
def ops_status(request: Request) -> dict[str, Any]:
    paper_payload = paper_status(request)
    status = compute_live_validation_status(
        settings=request.app.state.settings,
        paper_engine=getattr(request.app.state, "paper_engine", None),
        kis_broker=getattr(request.app.state, "kis_broker", None),
        paper_status_payload=paper_payload,
    )
    return _serialize_live_validation_status(status, include_checklist=False)


@router.get("/ops/preflight")
def ops_preflight(request: Request) -> dict[str, Any]:
    paper_payload = paper_status(request)
    status = compute_live_validation_status(
        settings=request.app.state.settings,
        paper_engine=getattr(request.app.state, "paper_engine", None),
        kis_broker=getattr(request.app.state, "kis_broker", None),
        paper_status_payload=paper_payload,
    )
    return _serialize_live_validation_status(status, include_checklist=True)


@router.get("/paper/orders")
def paper_orders(request: Request) -> dict[str, Any]:
    broker = request.app.state.broker
    return {
        "open_orders": [_broker_order_dict(order) for order in broker.open_orders()],
        "secret_exposed": False,
    }


@router.post("/paper/order/simulate")
def paper_order_simulate(payload: PaperOrderSimulateRequest, request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    engine = _paper_engine(request)
    cash_before = _decimal_map(engine.cash_by_currency())
    if settings.trading_mode.value != "paper" or settings.live_trading_enabled:
        request.app.state.paper_last_error = "paper_trading_required"
        return _simulation_response(
            request,
            accepted=False,
            filled=False,
            reason="paper_trading_required",
            fills=[],
            cash_before=cash_before,
            order=None,
            risk_result={"approved": False, "reason": "paper_trading_required"},
        )
    if payload.mock_ask < payload.mock_bid:
        request.app.state.paper_last_error = "invalid_quote_spread"
        return _simulation_response(
            request,
            accepted=False,
            filled=False,
            reason="invalid_quote_spread",
            fills=[],
            cash_before=cash_before,
            order=None,
            risk_result={"approved": False, "reason": "invalid_quote_spread"},
        )

    symbol = payload.symbol.strip().upper()
    currency = payload.currency.strip().upper()
    if not symbol or currency != payload.currency.strip():
        request.app.state.paper_last_error = "invalid_symbol_or_currency"
        return _simulation_response(
            request,
            accepted=False,
            filled=False,
            reason="invalid_symbol_or_currency",
            fills=[],
            cash_before=cash_before,
            order=None,
            risk_result={"approved": False, "reason": "invalid_symbol_or_currency"},
        )

    intent = OrderIntent(
        symbol=symbol,
        side=payload.side,
        quantity=payload.quantity,
        order_type=payload.order_type,
        limit_price=payload.limit_price,
        stop_price=payload.stop_price,
        currency=currency,
        client_tag="manual_dashboard",
        quote_timestamp=datetime.now(timezone.utc),
    )
    order_preview = _order_preview(intent, payload)
    decision = request.app.state.risk.evaluate(intent)
    risk_result = {
        "approved": decision.approved,
        "reason": decision.reason,
        "risk_token_present": bool(decision.risk_token),
        "summary_ko": _risk_summary_ko(decision.approved, decision.reason),
    }
    if not decision.approved:
        request.app.state.paper_last_error = decision.reason
        return _simulation_response(
            request,
            accepted=False,
            filled=False,
            reason=decision.reason,
            fills=[],
            cash_before=cash_before,
            order=order_preview,
            risk_result=risk_result,
        )

    precheck_reason = _precheck_account(engine, payload, symbol, currency)
    if precheck_reason is not None:
        request.app.state.paper_last_error = precheck_reason
        return _simulation_response(
            request,
            accepted=False,
            filled=False,
            reason=precheck_reason,
            fills=[],
            cash_before=cash_before,
            order=order_preview,
            risk_result=risk_result,
        )

    try:
        ack = request.app.state.oms.place(intent)
    except RuntimeError as exc:
        reason = str(exc)
        request.app.state.paper_last_error = reason
        return _simulation_response(
            request,
            accepted=False,
            filled=False,
            reason=reason,
            fills=[],
            cash_before=cash_before,
            order=order_preview,
            risk_result=risk_result,
        )

    quote = Quote(
        symbol=symbol,
        last=payload.mock_last,
        bid=payload.mock_bid,
        ask=payload.mock_ask,
        volume=payload.mock_volume,
        timestamp=datetime.now(timezone.utc),
        source="manual_dashboard_mock",
        session=payload.session,
        currency=currency,
    )
    trades = engine.on_quote(quote)
    fills = [_trade_dict(trade) for trade in trades if trade.oms_id == ack.oms_id]
    reason = "filled" if fills else "no_fill"
    request.app.state.paper_last_error = None if fills else reason
    return _simulation_response(
        request,
        accepted=True,
        filled=bool(fills),
        reason=reason,
        fills=fills,
        cash_before=cash_before,
        order={**order_preview, "oms_id": ack.oms_id, "broker_order_id": ack.broker_order_id},
        risk_result=risk_result,
    )


def _paper_engine(request: Request):
    engine = getattr(request.app.state, "paper_engine", None)
    if engine is None:
        raise HTTPException(status_code=500, detail="paper engine unavailable")
    return engine


def _decimal_map(values: dict[str, Decimal]) -> dict[str, str]:
    return {key: str(value) for key, value in values.items()}


def _position_dict(position) -> dict[str, Any]:
    mark = position.last_price if position.last_price is not None else position.avg_price
    unrealized = position.quantity * (mark - position.avg_price)
    return {
        "symbol": position.symbol,
        "quantity": position.quantity,
        "avg_price": str(position.avg_price),
        "currency": position.currency,
        "realized_pnl": str(position.realized_pnl),
        "unrealized_pnl": str(unrealized),
        "last_price": str(position.last_price) if position.last_price is not None else None,
        "market_value": str(position.market_value),
        "updated_at": position.updated_at.isoformat(),
    }


def _trade_dict(entry) -> dict[str, Any]:
    return {
        "broker_order_id": entry.broker_order_id,
        "oms_id": entry.oms_id,
        "symbol": entry.symbol,
        "side": entry.side.value,
        "quantity": entry.quantity,
        "price": str(entry.price),
        "currency": entry.currency,
        "commission": str(entry.commission),
        "filled_at": entry.filled_at.isoformat(),
    }


def _order_log_dict(entry) -> dict[str, Any]:
    return {
        "broker_order_id": entry.broker_order_id,
        "oms_id": entry.oms_id,
        "symbol": entry.symbol,
        "status": entry.status,
        "reason": entry.reason,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


def _broker_order_dict(order) -> dict[str, Any]:
    return {
        "symbol": order.symbol,
        "side": order.side.value,
        "quantity": order.quantity,
        "order_type": order.order_type.value,
        "limit_price": str(order.limit_price),
        "stop_price": str(order.stop_price) if order.stop_price is not None else None,
        "currency": order.currency,
        "submitted_at": order.submitted_at.isoformat(),
        "client_tag": order.client_tag,
    }


def _order_preview(intent: OrderIntent, payload: PaperOrderSimulateRequest) -> dict[str, Any]:
    return {
        "symbol": intent.symbol,
        "side": intent.side.value,
        "side_ko": "매수" if intent.side == Side.BUY else "매도",
        "quantity": intent.quantity,
        "order_type": intent.order_type.value,
        "order_type_ko": _order_type_ko(intent.order_type),
        "limit_price": str(intent.limit_price),
        "stop_price": str(intent.stop_price) if intent.stop_price is not None else None,
        "currency": intent.currency,
        "mock_quote": {
            "last": str(payload.mock_last),
            "bid": str(payload.mock_bid),
            "ask": str(payload.mock_ask),
            "volume": payload.mock_volume,
        },
    }


def _safety_flags(request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    return {
        "mode": settings.trading_mode.value,
        "paper_only": settings.trading_mode.value == "paper",
        "live_trading_enabled": settings.live_trading_enabled,
        "live_trading_disabled": not settings.live_trading_enabled,
        "allow_market_orders": settings.allow_market_orders,
        "allow_paper_market_orders": settings.allow_paper_market_orders,
        "real_broker_orders_enabled": False,
        "oms_required": True,
        "risk_engine_required": True,
        "summary_ko": "모의거래 전용입니다. 실거래는 꺼져 있고 실제 주문은 불가능합니다.",
    }


def _snapshot_state(request: Request) -> dict[str, Any]:
    engine = _paper_engine(request)
    snapshot = engine.portfolio.get_snapshot()
    return {
        "cash": _decimal_map(engine.cash_by_currency()),
        "positions": [_position_dict(position) for position in snapshot.positions.values()],
        "open_orders": [_broker_order_dict(order) for order in request.app.state.broker.open_orders()],
        "realized_pnl": str(snapshot.realized_pnl),
        "unrealized_pnl": str(snapshot.unrealized_pnl),
        "market_value": str(snapshot.market_value),
        "realized_pnl_by_currency": _decimal_map(snapshot.realized_pnl_by_currency),
        "unrealized_pnl_by_currency": _decimal_map(snapshot.unrealized_pnl_by_currency),
        "market_value_by_currency": _decimal_map(snapshot.market_value_by_currency),
    }


def _simulation_response(
    request: Request,
    accepted: bool,
    filled: bool,
    reason: str,
    fills: list[dict[str, Any]],
    cash_before: dict[str, str],
    order: dict[str, Any] | None,
    risk_result: dict[str, Any],
) -> dict[str, Any]:
    state = _snapshot_state(request)
    summary_ko = _paper_order_summary_ko(accepted=accepted, filled=filled, reason=reason)
    return {
        "accepted": accepted,
        "rejected": not accepted,
        "filled": filled,
        "reason": reason,
        "rejection_reason": None if accepted else reason,
        "summary_ko": summary_ko,
        "user_message_ko": summary_ko,
        "risk_result": risk_result,
        "order": order,
        "fills": fills,
        "cash_before": cash_before,
        "cash_after": state["cash"],
        "cash": state["cash"],
        "positions": state["positions"],
        "open_orders": state["open_orders"],
        "realized_pnl": state["realized_pnl"],
        "unrealized_pnl": state["unrealized_pnl"],
        "market_value": state["market_value"],
        "safety": _safety_flags(request),
        "safety_flags": _safety_flags(request),
        "last_error": getattr(request.app.state, "paper_last_error", None),
        "secret_exposed": False,
    }


def _order_type_ko(order_type: OrderType) -> str:
    if order_type == OrderType.LIMIT:
        return "지정가"
    if order_type == OrderType.STOP_LIMIT:
        return "스탑 지정가"
    if order_type == OrderType.MARKET:
        return "시장가"
    return order_type.value


def _reason_ko(reason: str | None) -> str:
    reasons = {
        None: "없음",
        "filled": "체결됨",
        "no_fill": "조건에 맞지 않아 아직 체결되지 않음",
        "insufficient_cash": "현금이 부족합니다",
        "insufficient_position": "보유 수량이 부족합니다",
        "paper_market_orders_disabled": "시장가 모의 주문은 기본값에서 비활성화되어 있습니다",
        "paper_trading_required": "모의거래 모드가 필요합니다",
        "invalid_quote_spread": "모의 매도호가가 매수호가보다 낮습니다",
        "invalid_symbol_or_currency": "종목 코드 또는 통화 형식이 올바르지 않습니다",
        "max_order_notional_exceeded": "주문 금액이 허용 한도를 초과했습니다",
        "symbol_not_allowed": "허용된 종목 목록에 없는 종목입니다",
        "kill_switch_engaged": "킬 스위치가 켜져 있어 주문할 수 없습니다",
        "live_trading_disabled": "실거래가 차단되어 있습니다",
    }
    return reasons.get(reason, str(reason))


def _paper_order_summary_ko(*, accepted: bool, filled: bool, reason: str) -> str:
    if filled:
        return "모의 주문이 체결되었습니다. 현금, 보유 종목, 체결 내역이 업데이트되었습니다."
    if accepted:
        return "모의 주문은 접수되었지만 아직 체결되지 않았습니다. 사유: " + _reason_ko(reason)
    return "모의 주문이 거절되었습니다. 사유: " + _reason_ko(reason)


def _risk_summary_ko(approved: bool, reason: str) -> str:
    if approved:
        return "리스크 검사를 통과했습니다."
    return "리스크 검사에서 거절되었습니다. 사유: " + _reason_ko(reason)


def _report_user_summary(summary: dict[str, Any]) -> dict[str, Any]:
    counters = summary.get("counters", summary)
    ticks_total = int(counters.get("ticks_total", summary.get("ticks_total", 0)) or 0)
    candidates_seen = int(counters.get("candidates_seen", summary.get("candidates_seen", 0)) or 0)
    orders_created = int(
        counters.get("dry_run_orders_created", summary.get("dry_run_orders_created", 0)) or 0
    )
    fills_count = int(counters.get("fills_count", summary.get("fills_count", 0)) or 0)
    rejected_count = int(
        counters.get("rejected_count", counters.get("candidates_blocked", 0)) or 0
    )
    errors_total = int(counters.get("errors_total", summary.get("errors_total", 0)) or 0)
    explanations: list[str] = []
    if ticks_total == 0:
        explanations.append("아직 실행된 tick이 없습니다. Dry-run을 시작하고 tick을 실행해 보세요.")
    if candidates_seen == 0:
        explanations.append(
            "이번 tick에서는 주문 후보가 발생하지 않았습니다. 전략 조건에 맞는 종목이 없거나 입력된 snapshot이 부족합니다."
        )
    if orders_created == 0:
        explanations.append("이번 실행에서는 주문이 생성되지 않았습니다.")
    if fills_count > 0:
        explanations.append("모의 체결이 발생했습니다. 체결 내역과 포지션을 확인하세요.")
    if errors_total > 0:
        explanations.append("오류가 발생했습니다. 마지막 오류와 로그를 확인하세요.")
    if not explanations:
        explanations.append("실행은 정상입니다. 후보와 주문 수를 확인해 다음 테스트를 진행하세요.")
    suggestions: list[str] = []
    if candidates_seen == 0:
        suggestions.append("전략 조건을 만족하는 snapshot을 넣거나, 대시보드의 예시 모의 주문을 실행해 보세요.")
    if orders_created == 0:
        suggestions.append("주문 생성 조건과 RiskEngine 거절 사유를 확인하세요.")
    if errors_total == 0 and orders_created > 0:
        suggestions.append("체결 여부를 확인하려면 mock quote 가격과 거래량을 조정해 보세요.")
    return {
        "실행 상태": "오류 있음" if errors_total else "정상",
        "Tick 수": ticks_total,
        "후보 수": candidates_seen,
        "생성된 주문 수": orders_created,
        "체결 수": fills_count,
        "거절 수": rejected_count,
        "오류 수": errors_total,
        "한글 해석": explanations,
        "다음 행동 제안": suggestions,
    }


def _precheck_account(engine, payload: PaperOrderSimulateRequest, symbol: str, currency: str) -> str | None:
    if payload.side == Side.SELL:
        position = engine.portfolio.get_snapshot().positions.get(symbol)
        held = position.quantity if position is not None else 0
        if held < payload.quantity:
            return "insufficient_position"
    price = _execution_price(payload)
    if price is None:
        return None
    commission = (
        engine.broker._commission_per_share * Decimal(payload.quantity)  # noqa: SLF001
        + engine.broker._commission_per_fill  # noqa: SLF001
    )
    if payload.side == Side.BUY:
        required_cash = price * payload.quantity + commission
        if engine.account.cash_balance(currency) < required_cash:
            return "insufficient_cash"
        return None
    return None


def _execution_price(payload: PaperOrderSimulateRequest) -> Decimal | None:
    if payload.order_type == OrderType.MARKET:
        return payload.mock_ask if payload.side == Side.BUY else payload.mock_bid
    if payload.order_type == OrderType.LIMIT:
        if payload.side == Side.BUY and payload.mock_ask <= payload.limit_price:
            return payload.mock_ask
        if payload.side == Side.SELL and payload.mock_bid >= payload.limit_price:
            return payload.mock_bid
        return None
    if payload.order_type == OrderType.STOP_LIMIT:
        if payload.stop_price is None:
            return None
        if payload.side == Side.BUY:
            if payload.mock_last < payload.stop_price or payload.mock_ask > payload.limit_price:
                return None
            return payload.mock_ask
        if payload.mock_last > payload.stop_price or payload.mock_bid < payload.limit_price:
            return None
        return payload.mock_bid
    return None


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


@router.get("/paper/report/summary")
def paper_report_summary(request: Request) -> dict[str, Any]:
    controller = request.app.state.dry_run_controller
    summary = controller.summary()
    return {
        "summary": summary,
        "user_summary": _report_user_summary(summary),
        "secret_exposed": False,
    }


@router.post("/paper/dry-run/start")
def dry_run_start(request: Request) -> dict[str, Any]:
    controller = request.app.state.dry_run_controller
    try:
        controller.start()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return controller.summary()


@router.post("/paper/dry-run/stop")
def dry_run_stop(request: Request) -> dict[str, Any]:
    controller = request.app.state.dry_run_controller
    try:
        controller.stop(reason="manual")
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return controller.summary()


@router.post("/paper/dry-run/tick")
def dry_run_tick(payload: DryRunTickRequest, request: Request) -> dict[str, Any]:
    controller = request.app.state.dry_run_controller
    try:
        result = controller.tick(payload.snapshots)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "tick": {
            "status": result.status,
            "snapshots_evaluated": result.snapshots_evaluated,
            "candidates_passed": result.candidates_passed,
            "candidates_blocked": result.candidates_blocked,
            "oms_acks": result.oms_acks,
            "oms_errors": result.oms_errors,
        },
        "summary": controller.summary(),
    }


@router.get("/paper/dry-run/status")
def dry_run_status(request: Request) -> dict[str, Any]:
    return request.app.state.dry_run_controller.summary()


def _reports_base(settings) -> Path:
    raw = Path(settings.dry_run_reports_dir)
    if raw.is_absolute():
        raise HTTPException(status_code=500, detail="dry_run_reports_dir misconfigured")
    project_dir = Path(__file__).resolve().parents[2]
    base = (project_dir / raw).resolve()
    if base != project_dir and project_dir not in base.parents:
        raise HTTPException(status_code=500, detail="reports dir outside project")
    return base


def _resolve_run_dir(settings, run_dir_request: str | None) -> Path:
    base = _reports_base(settings)
    if run_dir_request is None:
        latest = find_latest_run_dir(base)
        if latest is None:
            raise HTTPException(status_code=404, detail="no run directories")
        return latest
    candidate = (base / run_dir_request).resolve()
    if candidate != base and base not in candidate.parents:
        raise HTTPException(status_code=400, detail="run_dir outside reports directory")
    if not candidate.is_dir():
        raise HTTPException(status_code=404, detail="run_dir not found")
    return candidate


@router.post("/reports/dry-run/analyze")
def reports_analyze(payload: AnalyzeRequest, request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    run_dir = _resolve_run_dir(settings, payload.run_dir)
    result = analyze_run(run_dir)
    paths = write_analysis_files(result)
    base = _reports_base(settings)
    return {
        "run_dir": run_dir.name,
        "files": {key: str(path.relative_to(base)) for key, path in paths.items()},
        "summary": json.loads(paths["summary"].read_text(encoding="utf-8")),
        "user_summary": _report_user_summary(json.loads(paths["summary"].read_text(encoding="utf-8"))),
    }


@router.get("/reports/dry-run/latest")
def reports_latest(request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    run_dir = _resolve_run_dir(settings, None)
    summary_path = run_dir / "analysis_summary.json"
    if not summary_path.is_file():
        result = analyze_run(run_dir)
        write_analysis_files(result)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return {
        "run_dir": run_dir.name,
        "summary": summary,
        "user_summary": _report_user_summary(summary),
    }
