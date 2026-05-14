import secrets

from app.domain.enums import OrderType, TradingMode
from app.domain.orders import BrokerOrder, OrderAck


class PaperBroker:
    mode = TradingMode.PAPER

    def __init__(self) -> None:
        self._open_orders: dict[str, BrokerOrder] = {}
        self._positions: dict[str, int] = {}

    def submit(self, order: BrokerOrder) -> OrderAck:
        if order.order_type not in (OrderType.LIMIT, OrderType.STOP_LIMIT):
            raise ValueError("market orders are disabled")
        broker_order_id = secrets.token_hex(8)
        self._open_orders[broker_order_id] = order
        return OrderAck(
            oms_id=order.oms_id,
            broker_order_id=broker_order_id,
            status="accepted",
            mode=self.mode,
        )

    def cancel(self, broker_order_id: str) -> None:
        self._open_orders.pop(broker_order_id, None)

    def open_orders(self) -> list[BrokerOrder]:
        return list(self._open_orders.values())

    def positions(self) -> dict[str, int]:
        return dict(self._positions)
