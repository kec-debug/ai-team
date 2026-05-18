from decimal import Decimal

import pytest

from app.domain.enums import Side
from app.portfolio import PortfolioService


def test_portfolio_service_tracks_long_position_and_realized_pnl():
    portfolio = PortfolioService()

    opened = portfolio.apply_fill("aapl", Side.BUY, 10, Decimal("100"))
    assert opened.symbol == "AAPL"
    assert opened.quantity == 10
    assert opened.avg_price == Decimal("100")

    closed = portfolio.apply_fill("AAPL", Side.SELL, 4, Decimal("110"), Decimal("1"))
    assert closed.quantity == 6
    assert closed.realized_pnl == Decimal("39")

    snapshot = portfolio.get_snapshot()
    assert snapshot.positions["AAPL"].quantity == 6
    assert snapshot.realized_pnl == Decimal("39")


def test_portfolio_service_updates_market_value_from_marks():
    portfolio = PortfolioService()
    portfolio.apply_fill("MSFT", Side.BUY, 2, Decimal("50"))
    portfolio.mark_price("MSFT", Decimal("55"))

    snapshot = portfolio.get_snapshot()
    assert snapshot.market_value == Decimal("110")
    assert snapshot.unrealized_pnl == Decimal("10")
    assert snapshot.market_value_by_currency["USD"] == Decimal("110")
    assert snapshot.unrealized_pnl_by_currency["USD"] == Decimal("10")


def test_portfolio_service_tracks_per_currency_without_conversion():
    portfolio = PortfolioService()
    portfolio.apply_fill("AAPL", Side.BUY, 1, Decimal("100"), currency="USD")
    portfolio.apply_fill("7203", Side.BUY, 2, Decimal("50"), currency="JPY")

    snapshot = portfolio.get_snapshot()
    assert snapshot.market_value_by_currency == {
        "USD": Decimal("100"),
        "JPY": Decimal("100"),
    }
    assert snapshot.market_value == Decimal("200")


def test_portfolio_service_rejects_invalid_fills():
    portfolio = PortfolioService()

    with pytest.raises(ValueError, match="quantity"):
        portfolio.apply_fill("AAPL", Side.BUY, 0, Decimal("100"))
    with pytest.raises(ValueError, match="price"):
        portfolio.apply_fill("AAPL", Side.BUY, 1, Decimal("0"))
