from decimal import Decimal

import pytest

from app.domain.enums import OrderType, Side
from app.domain.orders import OrderIntent


def test_order_type_has_no_market():
    assert "MARKET" not in OrderType.__members__


def test_order_intent_requires_uppercase_symbol():
    with pytest.raises(ValueError):
        OrderIntent("aapl", Side.BUY, 1, OrderType.LIMIT, Decimal("10"))


def test_order_intent_requires_positive_values():
    with pytest.raises(ValueError):
        OrderIntent("AAPL", Side.BUY, 0, OrderType.LIMIT, Decimal("10"))
    with pytest.raises(ValueError):
        OrderIntent("AAPL", Side.BUY, 1, OrderType.LIMIT, Decimal("0"))
