from dataclasses import replace
from decimal import Decimal

import pytest

from app.broker.paper import PaperBroker
from app.config import Settings
from app.domain.enums import OrderType, Side, TradingMode
from app.domain.orders import OrderIntent
from app.oms.manager import OMS
from app.risk.engine import RiskEngine


class NonPaperBroker(PaperBroker):
    mode = TradingMode.LIVE


def intent(symbol="AAPL", quantity=1, limit=Decimal("100")):
    return OrderIntent(symbol, Side.BUY, quantity, OrderType.LIMIT, limit)


def test_oms_places_valid_paper_order(settings):
    ack = OMS(settings, RiskEngine(settings), PaperBroker()).place(intent())
    assert ack.status == "accepted"


def test_oms_rejects_live_enabled(settings):
    live_settings = replace(settings, live_trading_enabled=True)
    with pytest.raises(RuntimeError, match="refuses live"):
        OMS(live_settings, RiskEngine(live_settings), PaperBroker()).place(intent())


def test_oms_rejects_non_paper_broker(settings):
    with pytest.raises(RuntimeError, match="non-paper broker"):
        OMS(settings, RiskEngine(settings), NonPaperBroker()).place(intent())


def test_oms_surfaces_risk_reject(settings):
    with pytest.raises(RuntimeError, match="RiskEngine rejected"):
        OMS(settings, RiskEngine(settings), PaperBroker()).place(intent(symbol="TSLA"))


def test_oms_does_not_expose_public_risk_getter(settings):
    oms = OMS(settings, RiskEngine(settings), PaperBroker())
    assert not hasattr(oms, "risk")
    assert not hasattr(oms, "broker")
