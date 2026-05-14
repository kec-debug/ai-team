import secrets
from datetime import datetime, timezone

from app.config import Settings
from app.domain.enums import TradingMode
from app.domain.orders import BrokerOrder, Order, OrderAck, OrderIntent


class OMS:
    def __init__(self, settings: Settings, risk, broker) -> None:
        self._settings = settings
        self._risk = risk
        self._broker = broker

    def place(self, intent: OrderIntent) -> OrderAck:
        if self._settings.live_trading_enabled:
            raise RuntimeError("OMS refuses live trading in Phase 1")
        if self._broker.mode != TradingMode.PAPER:
            raise RuntimeError("OMS rejects non-paper broker")

        decision = self._risk.evaluate(intent)
        if not decision.approved or not decision.risk_token:
            raise RuntimeError(f"RiskEngine rejected: {decision.reason}")

        now = datetime.now(timezone.utc)
        order = Order(
            symbol=intent.symbol,
            side=intent.side,
            quantity=intent.quantity,
            order_type=intent.order_type,
            limit_price=intent.limit_price,
            risk_token=decision.risk_token,
            created_at=now,
            stop_price=intent.stop_price,
            client_tag=intent.client_tag,
        )
        broker_order = BrokerOrder(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            order_type=order.order_type,
            limit_price=order.limit_price,
            risk_token=order.risk_token,
            created_at=order.created_at,
            oms_id=secrets.token_hex(8),
            submitted_at=now,
            stop_price=order.stop_price,
            client_tag=order.client_tag,
            quote_timestamp=intent.quote_timestamp,
        )
        return self._broker.submit(broker_order)
