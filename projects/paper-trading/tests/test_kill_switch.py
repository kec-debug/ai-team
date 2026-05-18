from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.broker.kis import KisOrderRejectedError, validate_kis_order_request
from app.domain.enums import OrderType, Side
from app.domain.orders import BrokerOrder, OrderIntent
from app.risk.engine import RiskEngine


def _settings(settings):
    return replace(
        settings,
        kis_env="paper",
        kis_account_no="12345678",
        kis_app_key="fake-key",
        kis_app_secret="fake-secret",
    )


def _broker_order() -> BrokerOrder:
    now = datetime.now(timezone.utc)
    return BrokerOrder(
        symbol="AAPL",
        side=Side.BUY,
        quantity=10,
        order_type=OrderType.LIMIT,
        limit_price=Decimal("100"),
        risk_token="rt",
        created_at=now,
        oms_id="oms-1",
        submitted_at=now,
        quote_timestamp=now,
    )


def test_risk_engine_rejects_when_kill_switch_engaged(settings):
    s = replace(settings, kill_switch_engaged=True, symbol_allowlist=("AAPL",))
    intent = OrderIntent(
        symbol="AAPL",
        side=Side.BUY,
        quantity=10,
        order_type=OrderType.LIMIT,
        limit_price=Decimal("100"),
    )
    decision = RiskEngine(s).evaluate(intent)
    assert decision.approved is False
    assert decision.reason == "kill_switch_engaged"


def test_kis_preflight_rejects_when_kill_switch_engaged(settings):
    s = replace(_settings(settings), kill_switch_engaged=True)
    with pytest.raises(KisOrderRejectedError, match="kill_switch_engaged") as exc:
        validate_kis_order_request(s, _broker_order())
    assert exc.value.reason == "kill_switch_engaged"


def test_kill_switch_default_off(settings):
    assert settings.kill_switch_engaged is False
