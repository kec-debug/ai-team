from datetime import datetime, timezone
from decimal import Decimal

from app.broker.paper import PaperBroker
from app.config import Settings
from app.domain.enums import OrderType, Session, Side
from app.domain.orders import BrokerOrder
from app.domain.quote import Quote
from app.portfolio.account import PaperAccount
from app.runtime.paper_engine import PaperEngine
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
