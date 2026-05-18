from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.enums import Side
from app.domain.fills import Fill


class PaperAccountError(ValueError):
    pass


@dataclass
class PaperAccount:
    """Cash ledger only; positions and PnL remain owned by PortfolioService.

    Keeping cash and portfolio state separate avoids hidden exchange-rate or
    mark-to-market behavior inside account settlement.
    """

    cash: dict[str, Decimal] = field(default_factory=lambda: {"USD": Decimal("100000")})
    realized_pnl: dict[str, Decimal] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized: dict[str, Decimal] = {}
        for currency, amount in self.cash.items():
            if currency != currency.upper():
                raise PaperAccountError("currency must be uppercase")
            normalized[currency] = Decimal(amount)
        self.cash = normalized

    def cash_balance(self, currency: str) -> Decimal:
        if currency != currency.upper():
            raise PaperAccountError("currency must be uppercase")
        return self.cash.get(currency, Decimal("0"))

    def apply_fill(self, fill: Fill) -> None:
        currency = fill.currency
        gross = fill.price * fill.quantity
        current = self.cash_balance(currency)

        if fill.side == Side.BUY:
            total_cost = gross + fill.commission
            if current < total_cost:
                raise PaperAccountError("insufficient_cash")
            self.cash[currency] = current - total_cost
            return

        self.cash[currency] = current + gross - fill.commission
        self.realized_pnl[currency] = self.realized_pnl.get(currency, Decimal("0"))
