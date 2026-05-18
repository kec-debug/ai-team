from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from app.domain.enums import Side
from app.domain.fills import Fill


@dataclass
class Position:
    symbol: str
    quantity: int = 0
    avg_price: Decimal = Decimal("0")
    currency: str = "USD"
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
    unrealized_pnl: Decimal = Decimal("0")
    realized_pnl_by_currency: dict[str, Decimal] = field(default_factory=dict)
    market_value_by_currency: dict[str, Decimal] = field(default_factory=dict)
    unrealized_pnl_by_currency: dict[str, Decimal] = field(default_factory=dict)
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
        currency: str = "USD",
    ) -> Position:
        if quantity <= 0:
            raise ValueError("fill quantity must be positive")
        if price <= 0:
            raise ValueError("fill price must be positive")
        if commission < 0:
            raise ValueError("commission must be non-negative")
        if currency != currency.upper():
            raise ValueError("currency must be uppercase")

        symbol = symbol.upper()
        position = self._snapshot.positions.get(symbol) or Position(
            symbol=symbol,
            currency=currency,
        )
        if position.currency != currency:
            raise ValueError("position currency cannot change")
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

    def apply_trade(self, fill: Fill) -> Position:
        return self.apply_fill(
            symbol=fill.symbol,
            side=fill.side,
            quantity=fill.quantity,
            price=fill.price,
            commission=fill.commission,
            currency=fill.currency,
        )

    def mark_price(self, symbol: str, price: Decimal, currency: str | None = None) -> None:
        if price <= 0:
            raise ValueError("mark price must be positive")
        if currency is not None and currency != currency.upper():
            raise ValueError("currency must be uppercase")
        position = self._snapshot.positions.get(symbol.upper())
        if position is None:
            return
        if currency is not None and position.currency != currency:
            raise ValueError("mark currency must match position currency")
        position.last_price = price
        position.updated_at = datetime.now(timezone.utc)
        self._recalculate_totals()

    def _recalculate_totals(self) -> None:
        realized_by_currency: dict[str, Decimal] = {}
        market_by_currency: dict[str, Decimal] = {}
        unrealized_by_currency: dict[str, Decimal] = {}
        for position in self._snapshot.positions.values():
            currency = position.currency
            realized_by_currency[currency] = (
                realized_by_currency.get(currency, Decimal("0")) + position.realized_pnl
            )
            market_by_currency[currency] = (
                market_by_currency.get(currency, Decimal("0")) + position.market_value
            )
            mark = position.last_price if position.last_price is not None else position.avg_price
            unrealized = position.quantity * (mark - position.avg_price)
            unrealized_by_currency[currency] = (
                unrealized_by_currency.get(currency, Decimal("0")) + unrealized
            )

        self._snapshot.realized_pnl_by_currency = realized_by_currency
        self._snapshot.market_value_by_currency = market_by_currency
        self._snapshot.unrealized_pnl_by_currency = unrealized_by_currency
        self._snapshot.realized_pnl = sum(realized_by_currency.values(), Decimal("0"))
        self._snapshot.market_value = sum(market_by_currency.values(), Decimal("0"))
        self._snapshot.unrealized_pnl = sum(unrealized_by_currency.values(), Decimal("0"))
        self._snapshot.updated_at = datetime.now(timezone.utc)
