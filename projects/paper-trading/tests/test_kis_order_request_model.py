from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

from app.broker.kis import KisBroker, KisOrderRequest
from app.domain.enums import OrderType, Side
from app.domain.orders import BrokerOrder


def _settings(settings):
    return replace(
        settings,
        kis_env="paper",
        kis_account_no="12345678",
        kis_app_key="fake-key",
        kis_app_secret="fake-secret",
    )


def _broker_order(**overrides) -> BrokerOrder:
    now = datetime.now(timezone.utc)
    data = {
        "symbol": "AAPL",
        "side": Side.BUY,
        "quantity": 10,
        "order_type": OrderType.LIMIT,
        "limit_price": Decimal("100"),
        "risk_token": "rt",
        "created_at": now,
        "oms_id": "oms-1",
        "submitted_at": now,
        "quote_timestamp": now,
    }
    data.update(overrides)
    return BrokerOrder(**data)


def test_kis_order_request_contains_no_raw_account_field():
    fields_set = set(KisOrderRequest.__dataclass_fields__)
    assert "account_no" not in fields_set
    assert "account_no_masked" in fields_set
    assert "market" in fields_set
    assert "idempotency_key" in fields_set


def test_to_kis_request_uses_masked_account(settings):
    broker = KisBroker(_settings(settings))
    req = broker._to_kis_request(_broker_order())
    assert req.account_no_masked == "***5678"
    assert req.account_no_masked.startswith("***")
    assert "12345678" not in repr(req)
    assert req.idempotency_key == "kis-paper-oms-1"


def test_to_kis_request_preserves_order_fields(settings):
    broker = KisBroker(_settings(settings))
    broker_order = _broker_order(quantity=42, limit_price=Decimal("99.50"))
    req = broker._to_kis_request(broker_order)
    assert req.symbol == broker_order.symbol
    assert req.market == "US"
    assert req.side == broker_order.side
    assert req.quantity == 42
    assert req.order_type == OrderType.LIMIT
    assert req.limit_price == Decimal("99.50")
    assert req.extended_hours is False
    assert req.broker_environment == "paper"


def test_idempotency_key_is_deterministic(settings):
    broker = KisBroker(_settings(settings))
    first = broker._idempotency_key_for(_broker_order(oms_id="oms-42"))
    second = broker._idempotency_key_for(_broker_order(oms_id="oms-42"))
    assert first == second == "kis-paper-oms-42"
