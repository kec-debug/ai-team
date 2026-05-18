from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.domain.enums import Side
from app.domain.fills import Fill
from app.portfolio.account import PaperAccount, PaperAccountError


def fill(side=Side.BUY, quantity=1, price=Decimal("10"), currency="USD", commission=Decimal("0")):
    return Fill(
        broker_order_id="broker",
        oms_id="oms",
        symbol="AAPL",
        side=side,
        quantity=quantity,
        price=price,
        currency=currency,
        commission=commission,
        liquidity="simulated",
        filled_at=datetime.now(timezone.utc),
    )


def test_paper_account_buy_debits_currency_cash():
    account = PaperAccount(cash={"USD": Decimal("100")})
    account.apply_fill(fill(quantity=2, price=Decimal("10"), commission=Decimal("1")))
    assert account.cash_balance("USD") == Decimal("79")


def test_paper_account_sell_credits_currency_cash():
    account = PaperAccount(cash={"USD": Decimal("10")})
    account.apply_fill(fill(side=Side.SELL, quantity=2, price=Decimal("10"), commission=Decimal("1")))
    assert account.cash_balance("USD") == Decimal("29")


def test_paper_account_rejects_insufficient_cash():
    account = PaperAccount(cash={"USD": Decimal("5")})
    with pytest.raises(PaperAccountError, match="insufficient_cash"):
        account.apply_fill(fill(quantity=1, price=Decimal("10")))


def test_paper_account_keeps_currency_buckets_separate():
    account = PaperAccount(cash={"USD": Decimal("100"), "JPY": Decimal("100")})
    account.apply_fill(fill(quantity=1, price=Decimal("10"), currency="USD"))
    account.apply_fill(fill(quantity=1, price=Decimal("20"), currency="JPY"))
    assert account.cash == {"USD": Decimal("90"), "JPY": Decimal("80")}


def test_paper_account_rejects_lowercase_currency():
    with pytest.raises(PaperAccountError, match="currency"):
        PaperAccount(cash={"usd": Decimal("100")})
