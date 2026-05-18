from datetime import datetime, timezone
from decimal import Decimal

from app.broker.paper import PaperBroker
from app.domain.enums import OrderType, Session, Side, TradingMode
from app.domain.orders import BrokerOrder
from app.domain.quote import Quote


def broker_order(order_type=OrderType.LIMIT, quantity=1, side=Side.BUY):
    return BrokerOrder(
        symbol="AAPL",
        side=side,
        quantity=quantity,
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
    ack = PaperBroker().submit(broker_order(OrderType.MARKET))
    assert ack.status == "accepted"


def test_paper_broker_tick_fills_limit_buy():
    now = datetime.now(timezone.utc)
    broker = PaperBroker()
    ack = broker.submit(broker_order(quantity=2))
    fills = broker.tick(
        Quote("AAPL", Decimal("99"), Decimal("98"), Decimal("99"), 100, now, "test", Session.REGULAR),
        now,
    )
    assert len(fills) == 1
    assert fills[0].broker_order_id == ack.broker_order_id
    assert fills[0].quantity == 2
    assert broker.positions()["AAPL"] == 2


def test_paper_broker_tick_partial_fill_keeps_remainder_open():
    now = datetime.now(timezone.utc)
    broker = PaperBroker(max_fill_ratio_of_volume=Decimal("0.1"))
    broker.submit(broker_order(quantity=10))
    fills = broker.tick(
        Quote("AAPL", Decimal("99"), Decimal("98"), Decimal("99"), 50, now, "test", Session.REGULAR),
        now,
    )
    assert fills[0].quantity == 5
    assert broker.open_orders()[0].quantity == 5


def test_paper_broker_tick_rejects_stale_quote():
    now = datetime.now(timezone.utc)
    old = datetime(2026, 1, 1, tzinfo=timezone.utc)
    broker = PaperBroker(max_quote_age_seconds=1)
    broker.submit(broker_order())
    fills = broker.tick(
        Quote("AAPL", Decimal("99"), Decimal("98"), Decimal("99"), 100, old, "test", Session.REGULAR),
        now,
    )
    assert fills == []


def test_paper_broker_tick_rejects_disallowed_session():
    now = datetime.now(timezone.utc)
    broker = PaperBroker(allowed_sessions={Session.REGULAR})
    broker.submit(broker_order())
    fills = broker.tick(
        Quote("AAPL", Decimal("99"), Decimal("98"), Decimal("99"), 100, now, "test", Session.PRE_MARKET),
        now,
    )
    assert fills == []


def test_paper_broker_tick_allows_missing_session_for_backward_compat():
    now = datetime.now(timezone.utc)
    broker = PaperBroker(allowed_sessions={Session.REGULAR})
    broker.submit(broker_order())
    fills = broker.tick(
        Quote("AAPL", Decimal("99"), Decimal("98"), Decimal("99"), 100, now, "test"),
        now,
    )
    assert len(fills) == 1


def test_paper_broker_cancel_all_clears_orders():
    broker = PaperBroker()
    broker.submit(broker_order())
    broker.submit(broker_order())
    assert broker.cancel_all() == 2
    assert broker.open_orders() == []
