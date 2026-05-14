from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from app.domain.enums import Side


@dataclass
class Position:
    symbol: str
    quantity: int = 0
    avg_price: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    last_price: Decimal | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def market_value(self) -> Decimal:
        price = self.last_price if self.last_price is not None else self.avg_price
        return abs(self.quantity) * price


@dataclass
class PortfolioSnapshot:
    positions: dict[str, Position] = field(default_factory=dict)
    realized_pnl: Decimal = Decimal("0")
    market_value: Decimal = Decimal("0")
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PortfolioService:
    def __init__(self) -> None:
        self._snapshot = PortfolioSnapshot()

    def get_snapshot(self) -> PortfolioSnapshot:
        self._recalculate_totals()
        return self._snapshot

    def apply_fill(
        self,
        symbol: str,
        side: Side,
        quantity: int,
        price: Decimal,
        commission: Decimal = Decimal("0"),
    ) -> Position:
        if quantity <= 0:
            raise ValueError("fill quantity must be positive")
        if price <= 0:
            raise ValueError("fill price must be positive")

        symbol = symbol.upper()
        position = self._snapshot.positions.get(symbol) or Position(symbol=symbol)
        signed_qty = quantity if side == Side.BUY else -quantity
        old_qty = position.quantity
        new_qty = old_qty + signed_qty

        if old_qty == 0 or (old_qty > 0 and signed_qty > 0) or (old_qty < 0 and signed_qty < 0):
            gross_cost = abs(old_qty) * position.avg_price + abs(signed_qty) * price
            position.avg_price = gross_cost / abs(new_qty) if new_qty else Decimal("0")
        else:
            closing_qty = min(abs(old_qty), abs(signed_qty))
            pnl_per_unit = price - position.avg_price
            if old_qty < 0:
                pnl_per_unit = -pnl_per_unit
            position.realized_pnl += closing_qty * pnl_per_unit - commission
            if new_qty == 0:
                position.avg_price = Decimal("0")
            elif (old_qty > 0 > new_qty) or (old_qty < 0 < new_qty):
                position.avg_price = price

        position.quantity = new_qty
        position.last_price = price
        position.updated_at = datetime.now(timezone.utc)
        self._snapshot.positions[symbol] = position
        self._recalculate_totals()
        return position

    def mark_price(self, symbol: str, price: Decimal) -> None:
        if price <= 0:
            raise ValueError("mark price must be positive")
        position = self._snapshot.positions.get(symbol.upper())
        if position is None:
            return
        position.last_price = price
        position.updated_at = datetime.now(timezone.utc)
        self._recalculate_totals()

    def _recalculate_totals(self) -> None:
        self._snapshot.realized_pnl = sum(
            (position.realized_pnl for position in self._snapshot.positions.values()),
            Decimal("0"),
        )
        self._snapshot.market_value = sum(
            (position.market_value for position in self._snapshot.positions.values()),
            Decimal("0"),
        )
        self._snapshot.updated_at = datetime.now(timezone.utc)
