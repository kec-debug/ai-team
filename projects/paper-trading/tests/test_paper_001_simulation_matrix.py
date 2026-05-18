from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.broker.paper import PaperBroker
from app.config import Settings
from app.domain.enums import OrderType, Session, Side, TradingMode
from app.domain.fills import Fill
from app.domain.orders import BrokerOrder, OrderIntent
from app.domain.quote import Quote
from app.portfolio.account import PaperAccount
from app.risk.engine import RiskEngine


def make_order(
    *,
    side=Side.BUY,
    order_type=OrderType.LIMIT,
    quantity=10,
    limit=Decimal("100"),
    stop=None,
    currency="USD",
):
    now = datetime.now(timezone.utc)
    return BrokerOrder(
        symbol="AAPL",
        side=side,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit,
        risk_token="token",
        created_at=now,
        oms_id="oms",
        submitted_at=now,
        stop_price=stop,
        currency=currency,
    )


def make_quote(
    *,
    last=Decimal("100"),
    bid=Decimal("99"),
    ask=Decimal("100"),
    volume=100,
    session=Session.REGULAR,
    timestamp=None,
    currency="USD",
):
    return Quote(
        "AAPL",
        last,
        bid,
        ask,
        volume,
        timestamp or datetime.now(timezone.utc),
        "test",
        session,
        currency,
    )


@pytest.mark.parametrize(
    ("order_type", "side", "bid", "ask", "expected_price"),
    [
        (OrderType.LIMIT, Side.BUY, "99", "100", Decimal("100")),
        (OrderType.LIMIT, Side.SELL, "101", "102", Decimal("101")),
        (OrderType.MARKET, Side.BUY, "99", "101", Decimal("101")),
        (OrderType.MARKET, Side.SELL, "99", "101", Decimal("99")),
        (OrderType.STOP_LIMIT, Side.BUY, "99", "100", Decimal("100")),
        (OrderType.STOP_LIMIT, Side.SELL, "100", "101", Decimal("100")),
    ],
)
def test_tick_executes_supported_price_paths(order_type, side, bid, ask, expected_price):
    broker = PaperBroker(max_fill_ratio_of_volume=Decimal("1"))
    stop = Decimal("100") if order_type == OrderType.STOP_LIMIT else None
    broker.submit(make_order(order_type=order_type, side=side, stop=stop))
    fills = broker.tick(make_quote(last=Decimal("100"), bid=Decimal(bid), ask=Decimal(ask)))
    assert fills[0].price == expected_price


@pytest.mark.parametrize(
    ("side", "bid", "ask", "limit"),
    [
        (Side.BUY, "100", "101", Decimal("100")),
        (Side.SELL, "99", "100", Decimal("100")),
        (Side.BUY, "101", "102", Decimal("101")),
        (Side.SELL, "98", "99", Decimal("99")),
    ],
)
def test_tick_leaves_unmarketable_limit_orders_open(side, bid, ask, limit):
    broker = PaperBroker(max_fill_ratio_of_volume=Decimal("1"))
    broker.submit(make_order(side=side, limit=limit))
    fills = broker.tick(make_quote(bid=Decimal(bid), ask=Decimal(ask)))
    assert fills == []
    assert len(broker.open_orders()) == 1


@pytest.mark.parametrize(
    ("quote_session", "allowed", "fills_count"),
    [
        (Session.REGULAR, {Session.REGULAR}, 1),
        (Session.PRE_MARKET, {Session.REGULAR}, 0),
        (Session.AFTER_HOURS, {Session.AFTER_HOURS}, 1),
        (Session.CLOSED, {Session.REGULAR, Session.AFTER_HOURS}, 0),
    ],
)
def test_tick_session_matrix(quote_session, allowed, fills_count):
    broker = PaperBroker(allowed_sessions=allowed, max_fill_ratio_of_volume=Decimal("1"))
    broker.submit(make_order(quantity=1))
    fills = broker.tick(make_quote(session=quote_session))
    assert len(fills) == fills_count


@pytest.mark.parametrize(
    ("age_seconds", "expected_count"),
    [
        (0, 1),
        (60, 1),
        (61, 0),
        (-1, 0),
    ],
)
def test_tick_staleness_matrix(age_seconds, expected_count):
    now = datetime.now(timezone.utc)
    broker = PaperBroker(max_quote_age_seconds=60, max_fill_ratio_of_volume=Decimal("1"))
    broker.submit(make_order(quantity=1))
    quote = make_quote(timestamp=now - timedelta(seconds=age_seconds))
    assert len(broker.tick(quote, now)) == expected_count


@pytest.mark.parametrize(
    ("volume", "ratio", "expected_fill", "expected_open"),
    [
        (0, Decimal("1"), 0, 10),
        (9, Decimal("0.1"), 0, 10),
        (10, Decimal("0.1"), 1, 9),
        (50, Decimal("0.1"), 5, 5),
        (100, Decimal("1"), 10, 0),
    ],
)
def test_tick_partial_fill_volume_cap_matrix(volume, ratio, expected_fill, expected_open):
    broker = PaperBroker(max_fill_ratio_of_volume=ratio)
    broker.submit(make_order(quantity=10))
    fills = broker.tick(make_quote(volume=volume))
    filled_qty = sum(fill.quantity for fill in fills)
    open_qty = sum(order.quantity for order in broker.open_orders())
    assert filled_qty == expected_fill
    assert open_qty == expected_open


@pytest.mark.parametrize(
    ("cash", "side", "price", "quantity", "commission", "expected"),
    [
        (Decimal("100"), Side.BUY, Decimal("10"), 1, Decimal("0"), Decimal("90")),
        (Decimal("100"), Side.BUY, Decimal("10"), 2, Decimal("1"), Decimal("79")),
        (Decimal("0"), Side.SELL, Decimal("10"), 1, Decimal("0"), Decimal("10")),
        (Decimal("1"), Side.SELL, Decimal("10"), 2, Decimal("1"), Decimal("20")),
        (Decimal("50"), Side.BUY, Decimal("5"), 5, Decimal("0"), Decimal("25")),
    ],
)
def test_account_cash_matrix(cash, side, price, quantity, commission, expected):
    account = PaperAccount(cash={"USD": cash})
    account.apply_fill(
        Fill(
            broker_order_id="broker",
            oms_id="oms",
            symbol="AAPL",
            side=side,
            quantity=quantity,
            price=price,
            currency="USD",
            commission=commission,
            liquidity="simulated",
            filled_at=datetime.now(timezone.utc),
        )
    )
    assert account.cash_balance("USD") == expected


@pytest.mark.parametrize(
    ("settings", "reason"),
    [
        (Settings(), "paper_market_orders_disabled"),
        (Settings(allow_paper_market_orders=True, live_trading_enabled=True), "live_trading_disabled"),
        (Settings(allow_paper_market_orders=True, trading_mode=TradingMode.LIVE), "paper_trading_required"),
        (Settings(allow_paper_market_orders=True, kill_switch_engaged=True), "kill_switch_engaged"),
    ],
)
def test_market_risk_rejection_matrix(settings, reason):
    intent = OrderIntent("AAPL", Side.BUY, 1, OrderType.MARKET, Decimal("100"))
    decision = RiskEngine(settings).evaluate(intent)
    assert not decision.approved
    assert decision.reason == reason


@pytest.mark.parametrize("currency", ["USD", "JPY", "KRW", "EUR"])
def test_fill_accepts_uppercase_currency_buckets(currency):
    fill = Fill(
        broker_order_id="broker",
        oms_id="oms",
        symbol="AAPL",
        side=Side.BUY,
        quantity=1,
        price=Decimal("1"),
        currency=currency,
        commission=Decimal("0"),
        liquidity="simulated",
        filled_at=datetime.now(timezone.utc),
    )
    assert fill.currency == currency


def test_market_risk_approval_does_not_mutate_settings():
    settings = Settings(allow_paper_market_orders=True)
    decision = RiskEngine(settings).evaluate(
        OrderIntent("AAPL", Side.BUY, 1, OrderType.MARKET, Decimal("100"))
    )
    assert decision.approved
    assert replace(settings).allow_paper_market_orders is True
