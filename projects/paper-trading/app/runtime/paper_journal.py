import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.domain.fills import Fill


@dataclass(frozen=True)
class OrderLogEntry:
    broker_order_id: str
    oms_id: str
    symbol: str
    status: str
    reason: str | None = None
    created_at: datetime | None = None


@dataclass(frozen=True)
class TradeLogEntry:
    broker_order_id: str
    oms_id: str
    symbol: str
    quantity: int
    price: Decimal
    currency: str
    commission: Decimal
    filled_at: datetime

    @classmethod
    def from_fill(cls, fill: Fill) -> "TradeLogEntry":
        return cls(
            broker_order_id=fill.broker_order_id,
            oms_id=fill.oms_id,
            symbol=fill.symbol,
            quantity=fill.quantity,
            price=fill.price,
            currency=fill.currency,
            commission=fill.commission,
            filled_at=fill.filled_at,
        )


class PaperJournal:
    def __init__(self, log_dir: Path | str | None = None) -> None:
        self.orders: list[OrderLogEntry] = []
        self.trades: list[TradeLogEntry] = []
        self._log_dir = Path(log_dir) if log_dir else None
        if self._log_dir is not None:
            self._log_dir.mkdir(parents=True, exist_ok=True)

    def record_order(self, entry: OrderLogEntry) -> None:
        self.orders.append(entry)
        self._append("orders.jsonl", entry)

    def record_trade(self, entry: TradeLogEntry) -> None:
        self.trades.append(entry)
        self._append("trades.jsonl", entry)

    def rejected_order(self, *, broker_order_id: str, oms_id: str, symbol: str, reason: str) -> None:
        self.record_order(
            OrderLogEntry(
                broker_order_id=broker_order_id,
                oms_id=oms_id,
                symbol=symbol,
                status="rejected",
                reason=reason,
                created_at=datetime.now(timezone.utc),
            )
        )

    def _append(self, filename: str, entry: object) -> None:
        if self._log_dir is None:
            return
        with (self._log_dir / filename).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_jsonable(asdict(entry)), sort_keys=True) + "\n")


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value
