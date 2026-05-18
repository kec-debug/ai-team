from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.runtime.paper_engine import PaperEngine


def _decimal_map(values: dict[str, Decimal]) -> dict[str, str]:
    return {key: str(value) for key, value in values.items()}


def mask_paper_log_dir(log_dir, project_dir: Path) -> str:
    if log_dir is None:
        return "disabled"
    path = Path(log_dir)
    if not path.is_absolute():
        return path.as_posix()

    resolved = path.resolve()
    project_resolved = project_dir.resolve()
    try:
        return resolved.relative_to(project_resolved).as_posix()
    except ValueError:
        parts = resolved.parts[-2:]
        return "…/" + "/".join(parts)


def build_paper_account_status(
    engine: PaperEngine,
    starting_cash: dict[str, Decimal],
) -> dict[str, Any]:
    snapshot = engine.portfolio.get_snapshot()
    starting = _decimal_map(starting_cash)
    cash = _decimal_map(engine.cash_by_currency())
    realized = _decimal_map(snapshot.realized_pnl_by_currency)
    return {
        "starting_cash": starting,
        "cash": cash,
        "realized_pnl_by_currency": realized,
        "currencies": sorted(set(starting) | set(cash) | set(realized)),
        "secret_exposed": False,
    }


def build_paper_positions_status(engine: PaperEngine) -> dict[str, Any]:
    snapshot = engine.portfolio.get_snapshot()
    positions = []
    for position in snapshot.positions.values():
        mark = position.last_price if position.last_price is not None else position.avg_price
        unrealized = position.quantity * (mark - position.avg_price)
        positions.append(
            {
                "symbol": position.symbol,
                "quantity": position.quantity,
                "avg_price": str(position.avg_price),
                "last_price": str(position.last_price) if position.last_price is not None else None,
                "market_value": str(position.market_value),
                "currency": position.currency,
                "realized_pnl": str(position.realized_pnl),
                "unrealized_pnl": str(unrealized),
                "updated_at": position.updated_at.isoformat(),
            }
        )
    return {
        "positions_count": len(snapshot.positions),
        "positions": positions,
        "market_value_by_currency": _decimal_map(snapshot.market_value_by_currency),
        "realized_pnl_by_currency": _decimal_map(snapshot.realized_pnl_by_currency),
        "unrealized_pnl_by_currency": _decimal_map(snapshot.unrealized_pnl_by_currency),
        "secret_exposed": False,
    }


def build_paper_journal_status(engine: PaperEngine, *, limit: int = 50) -> dict[str, Any]:
    trades = list(reversed(engine.journal.trades[-limit:]))
    orders = list(reversed(engine.journal.orders[-limit:]))
    return {
        "recent_fills": [
            {
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
            for entry in trades
        ],
        "recent_orders": [
            {
                "broker_order_id": entry.broker_order_id,
                "oms_id": entry.oms_id,
                "symbol": entry.symbol,
                "status": entry.status,
                "reason": entry.reason,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
            }
            for entry in orders
        ],
        "fills_count": len(engine.journal.trades),
        "orders_count": len(engine.journal.orders),
        "secret_exposed": False,
    }


def build_paper_engine_status(engine: PaperEngine, *, project_dir: Path) -> dict[str, Any]:
    last_fill_at = engine.journal.trades[-1].filled_at if engine.journal.trades else None
    last_order_at = engine.journal.orders[-1].created_at if engine.journal.orders else None
    journal_times = [value for value in (last_fill_at, last_order_at) if value is not None]
    last_journal_entry_at = max(journal_times) if journal_times else None
    return {
        "paper_engine_enabled": True,
        "paper_journal_enabled": engine.journal is not None,
        "paper_journal_persistent_logging": bool(engine.journal._log_dir),
        "paper_journal_log_dir_masked": mask_paper_log_dir(engine.journal._log_dir, project_dir),
        "last_fill_at": last_fill_at.isoformat() if isinstance(last_fill_at, datetime) else None,
        "last_trade_at": last_fill_at.isoformat() if isinstance(last_fill_at, datetime) else None,
        "last_journal_entry_at": (
            last_journal_entry_at.isoformat()
            if isinstance(last_journal_entry_at, datetime)
            else None
        ),
        "secret_exposed": False,
    }
