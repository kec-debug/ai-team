from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.enums import OrderType, Side, TradingMode


@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    side: Side
    quantity: int
    order_type: OrderType
    limit_price: Decimal
    stop_price: Decimal | None = None
    client_tag: str | None = None
    quote_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        if self.symbol != self.symbol.upper():
            raise ValueError("symbol must be uppercase")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.limit_price <= 0:
            raise ValueError("limit_price must be positive")


@dataclass(frozen=True)
class Order:
    symbol: str
    side: Side
    quantity: int
    order_type: OrderType
    limit_price: Decimal
    risk_token: str
    created_at: datetime
    stop_price: Decimal | None = None
    client_tag: str | None = None


@dataclass(frozen=True)
class BrokerOrder:
    symbol: str
    side: Side
    quantity: int
    order_type: OrderType
    limit_price: Decimal
    risk_token: str
    created_at: datetime
    oms_id: str
    submitted_at: datetime
    stop_price: Decimal | None = None
    client_tag: str | None = None
    quote_timestamp: datetime | None = None


@dataclass(frozen=True)
class OrderAck:
    oms_id: str
    broker_order_id: str | None
    status: str
    mode: TradingMode
