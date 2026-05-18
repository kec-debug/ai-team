from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.enums import Side


@dataclass(frozen=True)
class Fill:
    broker_order_id: str
    oms_id: str
    symbol: str
    side: Side
    quantity: int
    price: Decimal
    currency: str
    commission: Decimal
    liquidity: str
    filled_at: datetime

    def __post_init__(self) -> None:
        if not self.broker_order_id:
            raise ValueError("broker_order_id must be non-empty")
        if not self.oms_id:
            raise ValueError("oms_id must be non-empty")
        if not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be non-empty uppercase")
        if self.quantity <= 0:
            raise ValueError("fill quantity must be positive")
        if self.price <= 0:
            raise ValueError("fill price must be positive")
        if self.currency != self.currency.upper():
            raise ValueError("currency must be uppercase")
        if self.commission < 0:
            raise ValueError("commission must be non-negative")
        if not self.liquidity:
            raise ValueError("liquidity must be non-empty")
        if self.filled_at.tzinfo is None:
            raise ValueError("filled_at must be timezone-aware")
