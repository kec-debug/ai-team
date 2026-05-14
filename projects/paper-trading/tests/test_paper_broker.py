from datetime import datetime, timezone
from decimal import Decimal

from app.broker.paper import PaperBroker
from app.domain.enums import OrderType, Side, TradingMode
from app.domain.orders import BrokerOrder


def broker_order(order_type=OrderType.LIMIT):
    return BrokerOrder(
        symbol="AAPL",
        side=Side.BUY,
        quantity=1,
        order_type=order_type,
        limit_price=Decimal("100"),
        risk_token="token",
        created_at=datetime.now(timezone.utc),
        oms_id="oms",
        submitted_at=datetime.now(timezone.utc),
    )


def test_paper_broker_accepts_limit():
    ack = PaperBroker().submit(broker_order())
    assert ack.mode == TradingMode.PAPER
    assert ack.status == "accepted"


def test_paper_broker_has_market_guard():
    assert "MARKET" not in OrderType.__members__
