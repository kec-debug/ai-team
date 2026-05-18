from typing import Protocol

from app.domain.enums import TradingMode
from app.domain.orders import BrokerOrder, OrderAck


class BrokerAdapter(Protocol):
    """Phase 1: only paper-mode adapters are usable."""

    mode: TradingMode

    def submit(self, order: BrokerOrder) -> OrderAck:
        ...

    def cancel(self, broker_order_id: str) -> None:
        ...

    def open_orders(self) -> list[BrokerOrder]:
        ...

    def positions(self) -> dict[str, int]:
        ...
