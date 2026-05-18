from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.broker.paper import PaperBroker
from app.config import Settings
from app.domain.enums import OrderType, Session, Side
from app.domain.orders import BrokerOrder, Order, OrderIntent
from app.domain.quote import Quote
from app.oms.manager import OMS
from app.portfolio.account import PaperAccount
from app.risk.engine import RiskEngine
from app.runtime.paper_engine import IntentSubmitResult, PaperEngine, SubmitIntentsBatchResult
from app.runtime.paper_journal import PaperJournal


def order(quantity=1):
    now = datetime.now(timezone.utc)
    return BrokerOrder(
        symbol="AAPL",
        side=Side.BUY,
        quantity=quantity,
        order_type=OrderType.LIMIT,
        limit_price=Decimal("10"),
        risk_token="token",
        created_at=now,
        oms_id="oms",
        submitted_at=now,
    )


def quote(price=Decimal("10"), volume=100):
    now = datetime.now(timezone.utc)
    return Quote("AAPL", price, price, price, volume, now, "test", Session.REGULAR, "USD")


def _intent(
    symbol="AAPL",
    quantity=2,
    limit=Decimal("10"),
    order_type=OrderType.LIMIT,
    currency="USD",
):
    return OrderIntent(
        symbol=symbol,
        side=Side.BUY,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit,
        currency=currency,
    )


def _wire(settings, *, allowlist=None, max_fill_ratio=Decimal("1"), **overrides):
    configured = settings
    if allowlist is not None:
        configured = replace(configured, symbol_allowlist=allowlist)
    for key, value in overrides.items():
        configured = replace(configured, **{key: value})
    broker = PaperBroker(max_fill_ratio_of_volume=max_fill_ratio)
    risk = RiskEngine(configured)
    oms = OMS(configured, risk, broker)
    account = PaperAccount(cash={"USD": Decimal("100")})
    journal = PaperJournal()
    engine = PaperEngine(configured, broker=broker, account=account, journal=journal, oms=oms)
    return engine, broker, account, journal


def test_paper_engine_applies_fill_to_account_and_portfolio():
    broker = PaperBroker(max_fill_ratio_of_volume=Decimal("1"))
    broker.submit(order(quantity=2))
    account = PaperAccount(cash={"USD": Decimal("100")})
    journal = PaperJournal()
    engine = PaperEngine(Settings(), broker=broker, account=account, journal=journal)

    trades = engine.on_quote(quote())

    assert len(trades) == 1
    assert account.cash_balance("USD") == Decimal("80")
    assert engine.portfolio.get_snapshot().positions["AAPL"].quantity == 2
    assert len(journal.trades) == 1


def test_paper_engine_records_rejected_cash_without_account_change():
    broker = PaperBroker(max_fill_ratio_of_volume=Decimal("1"))
    broker.submit(order(quantity=2))
    account = PaperAccount(cash={"USD": Decimal("1")})
    journal = PaperJournal()
    engine = PaperEngine(Settings(), broker=broker, account=account, journal=journal)

    trades = engine.on_quote(quote())

    assert trades == []
    assert account.cash_balance("USD") == Decimal("1")
    assert journal.orders[0].status == "rejected"


def test_paper_engine_cash_by_currency_returns_copy():
    account = PaperAccount(cash={"USD": Decimal("100")})
    engine = PaperEngine(Settings(), account=account)
    cash = engine.cash_by_currency()
    cash["USD"] = Decimal("0")
    assert account.cash_balance("USD") == Decimal("100")


def test_submit_intents_requires_oms(settings):
    engine = PaperEngine(settings)

    with pytest.raises(RuntimeError, match="requires an OMS"):
        engine.submit_intents([_intent()])


def test_submit_intents_rejects_non_intent_input(settings):
    engine, _broker, _account, _journal = _wire(settings)
    now = datetime.now(timezone.utc)
    invalid_items = [
        order(),
        Order(
            symbol="AAPL",
            side=Side.BUY,
            quantity=1,
            order_type=OrderType.LIMIT,
            limit_price=Decimal("10"),
            risk_token="token",
            created_at=now,
        ),
        {"symbol": "AAPL"},
    ]

    for item in invalid_items:
        with pytest.raises(TypeError, match="OrderIntent only"):
            engine.submit_intents([item])  # type: ignore[list-item]


def test_submit_intents_happy_path_passes_through_risk_and_oms(settings):
    engine, broker, _account, _journal = _wire(settings)

    result = engine.submit_intents([_intent()])

    assert isinstance(result, SubmitIntentsBatchResult)
    assert isinstance(result.results[0], IntentSubmitResult)
    assert result.accepted_count == 1
    assert result.rejected_count == 0
    assert result.results[0].accepted is True
    assert result.results[0].rejected_by is None
    assert result.results[0].reason is None
    assert result.results[0].oms_id
    assert result.results[0].broker_order_id
    assert len(broker.open_orders()) == 1


def test_submit_intents_risk_rejected_does_not_reach_broker(settings):
    engine, broker, _account, _journal = _wire(settings, allowlist=("AAPL",))

    result = engine.submit_intents([_intent(symbol="TSLA")])

    assert result.accepted_count == 0
    assert result.risk_rejected_count == 1
    assert result.results[0].rejected_by == "risk_engine"
    assert result.results[0].reason is not None
    assert result.results[0].reason.startswith("RiskEngine rejected")
    assert broker.open_orders() == []


def test_submit_intents_oms_rejected_does_not_reach_broker(settings):
    engine, broker, _account, _journal = _wire(settings, live_trading_enabled=True)

    result = engine.submit_intents([_intent()])

    assert result.accepted_count == 0
    assert result.oms_rejected_count == 1
    assert result.results[0].rejected_by == "oms"
    assert result.results[0].reason == "OMS refuses live trading in Phase 1"
    assert broker.open_orders() == []


def test_submit_intents_market_order_blocked_by_default_guard(settings):
    engine, broker, _account, _journal = _wire(settings)

    result = engine.submit_intents([_intent(order_type=OrderType.MARKET)])

    assert result.accepted_count == 0
    assert result.risk_rejected_count == 1
    assert result.results[0].reason is not None
    assert "paper_market_orders_disabled" in result.results[0].reason
    assert broker.open_orders() == []


def test_submit_intents_then_on_quote_flows_fill_through_engine(settings):
    engine, _broker, account, journal = _wire(settings)
    engine.submit_intents([_intent(quantity=2, limit=Decimal("10"))])

    trades = engine.on_quote(quote())

    assert len(trades) == 1
    assert account.cash_balance("USD") == Decimal("80")
    assert engine.portfolio.get_snapshot().positions["AAPL"].quantity == 2
    assert len(journal.trades) == 1


def test_submit_intents_partial_fill_preserved(settings):
    engine, broker, _account, _journal = _wire(settings, max_fill_ratio=Decimal("0.5"))
    engine.submit_intents([_intent(quantity=10, limit=Decimal("10"))])

    trades = engine.on_quote(quote(volume=10))

    assert len(trades) == 1
    assert trades[0].quantity == 5
    assert broker.open_orders()[0].quantity == 5


def test_submit_intents_results_immutable_and_secret_free(settings):
    engine, _broker, _account, _journal = _wire(
        replace(
            settings,
            kis_app_key="fake-key",
            kis_app_secret="fake-secret",
            kis_account_no="12345678",
        )
    )

    result = engine.submit_intents([_intent()])

    with pytest.raises(FrozenInstanceError):
        result.accepted_count = 99  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.results[0].accepted = False  # type: ignore[misc]
    text = repr(result)
    assert "fake-key" not in text
    assert "fake-secret" not in text
    assert "12345678" not in text
    assert "Bearer " not in text
