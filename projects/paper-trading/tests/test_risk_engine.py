from dataclasses import replace
from decimal import Decimal

from app.config import Settings
from app.domain.enums import OrderType, Side, TradingMode
from app.domain.orders import OrderIntent
from app.risk.engine import RiskEngine


def intent(symbol="AAPL", quantity=10, limit=Decimal("100")):
    return OrderIntent(symbol, Side.BUY, quantity, OrderType.LIMIT, limit)


def test_risk_allows_valid_intent(settings):
    decision = RiskEngine(settings).evaluate(intent())
    assert decision.approved
    assert decision.risk_token


def test_risk_rejects_non_paper(settings):
    decision = RiskEngine(replace(settings, trading_mode=TradingMode.LIVE)).evaluate(intent())
    assert not decision.approved


def test_risk_rejects_live_enabled(settings):
    decision = RiskEngine(replace(settings, live_trading_enabled=True)).evaluate(intent())
    assert not decision.approved


def test_risk_engine_kill_switch_at_top(settings):
    bad = replace(
        settings,
        kill_switch_engaged=True,
        trading_mode=TradingMode.LIVE,
        live_trading_enabled=True,
    )
    decision = RiskEngine(bad).evaluate(intent())
    assert decision.approved is False
    assert decision.reason == "kill_switch_engaged"


def test_risk_rejects_allowlist(settings):
    decision = RiskEngine(settings).evaluate(intent(symbol="TSLA"))
    assert decision.reason == "symbol_not_allowed"


def test_risk_rejects_notional(settings):
    decision = RiskEngine(settings).evaluate(intent(quantity=1000, limit=Decimal("100")))
    assert decision.reason == "max_order_notional_exceeded"
