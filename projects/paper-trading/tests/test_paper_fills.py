from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.domain.enums import Side
from app.domain.fills import Fill


def test_fill_requires_positive_quantity():
    with pytest.raises(ValueError, match="quantity"):
        Fill(
            broker_order_id="broker",
            oms_id="oms",
            symbol="AAPL",
            side=Side.BUY,
            quantity=0,
            price=Decimal("10"),
            currency="USD",
            commission=Decimal("0"),
            liquidity="simulated",
            filled_at=datetime.now(timezone.utc),
        )


def test_fill_requires_uppercase_currency():
    with pytest.raises(ValueError, match="currency"):
        Fill(
            broker_order_id="broker",
            oms_id="oms",
            symbol="AAPL",
            side=Side.BUY,
            quantity=1,
            price=Decimal("10"),
            currency="usd",
            commission=Decimal("0"),
            liquidity="simulated",
            filled_at=datetime.now(timezone.utc),
        )
