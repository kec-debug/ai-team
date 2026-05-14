import pathlib
import re
from dataclasses import replace

import pytest

from datetime import datetime, timezone
from decimal import Decimal

from app.broker.kis import (
    KisAccountClient,
    KisAuthClient,
    KisBroker,
    KisMarketDataClient,
    KisOrderRejectedError,
)
from app.domain.enums import TradingMode
from app.domain.enums import OrderType, Side
from app.domain.orders import BrokerOrder


REQUIRED_METHODS = (
    # KIS-style interface
    "authenticate",
    "refresh_token",
    "get_account",
    "get_positions",
    "get_quote",
    "get_open_orders",
    "place_order",
    "cancel_order",
    "replace_order",
    "capabilities",
    "healthcheck",
    # BrokerAdapter Protocol compatibility
    "submit",
    "cancel",
    "open_orders",
    "positions",
)


def _configured(settings):
    return replace(
        settings,
        kis_env="paper",
        kis_account_no="fake-acc",
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


def test_kis_broker_has_all_required_methods(settings):
    broker = KisBroker(_configured(settings))
    for name in REQUIRED_METHODS:
        attr = getattr(broker, name)
        assert callable(attr), f"missing or non-callable: {name}"


def test_kis_broker_exposes_sub_clients(settings):
    broker = KisBroker(_configured(settings))
    assert isinstance(broker.auth, KisAuthClient)
    assert isinstance(broker.account, KisAccountClient)
    assert isinstance(broker.market_data, KisMarketDataClient)
    assert broker.last_error is None


def test_kis_broker_mode_is_paper(settings):
    broker = KisBroker(_configured(settings))
    assert broker.mode == TradingMode.PAPER


def test_kis_broker_missing_env_fails_closed(settings):
    with pytest.raises(RuntimeError, match="KIS_ENV"):
        KisBroker(settings)


def test_kis_broker_live_env_rejected(settings):
    bad = replace(_configured(settings), kis_env="live")
    with pytest.raises(RuntimeError, match="live"):
        KisBroker(bad)


@pytest.mark.parametrize("missing", ["kis_account_no", "kis_app_key", "kis_app_secret"])
def test_kis_broker_missing_credentials_fails_closed(settings, missing):
    bad = replace(_configured(settings), **{missing: None})
    with pytest.raises(RuntimeError):
        KisBroker(bad)


def test_kis_place_cancel_replace_not_implemented(settings):
    broker = KisBroker(_configured(settings))
    with pytest.raises(KisOrderRejectedError):
        broker.place_order(_broker_order(quantity=0))
    with pytest.raises(NotImplementedError):
        broker.place_order(_broker_order())
    with pytest.raises(NotImplementedError):
        broker.cancel_order("x")
    with pytest.raises(NotImplementedError):
        broker.replace_order("x", _broker_order())


def test_kis_protocol_methods_delegate_to_not_implemented(settings):
    broker = KisBroker(_configured(settings))
    with pytest.raises(NotImplementedError):
        broker.submit(_broker_order())
    with pytest.raises(NotImplementedError):
        broker.cancel("x")
    with pytest.raises(NotImplementedError):
        broker.open_orders()
    with pytest.raises(NotImplementedError):
        broker.positions()


def test_kis_data_methods_not_implemented(settings):
    broker = KisBroker(_configured(settings))
    for method, args in (
        ("authenticate", ()),
        ("refresh_token", ()),
        ("get_account", ()),
        ("get_positions", ()),
        ("get_open_orders", ()),
        ("get_quote", ("AAPL",)),
    ):
        with pytest.raises(NotImplementedError, match="TODO"):
            getattr(broker, method)(*args)


def test_kis_broker_has_get_fills_and_get_order_status(settings):
    broker = KisBroker(_configured(settings))
    assert callable(broker.get_fills)
    assert callable(broker.get_order_status)
    with pytest.raises(NotImplementedError, match="TODO"):
        broker.get_fills()
    with pytest.raises(NotImplementedError, match="TODO"):
        broker.get_order_status("oms-1")


def test_kis_order_request_class_is_exported():
    from app.broker.kis import (
        KisOrderRejectedError,
        KisOrderRequest,
        KisOrderResponse,
        sanitize_kis_response,
        validate_kis_order_request,
    )

    assert KisOrderRequest is not None
    assert KisOrderResponse is not None
    assert KisOrderRejectedError is not None
    assert callable(sanitize_kis_response)
    assert callable(validate_kis_order_request)


def test_kis_broker_capabilities_are_exported_and_fail_closed(settings):
    broker = KisBroker(_configured(settings))
    assert broker.capabilities() == {
        "submission": False,
        "cancel": False,
        "replace": False,
        "open_orders": False,
        "fills": False,
        "order_status": False,
    }


def test_kis_healthcheck_returns_disconnected_dict(settings):
    broker = KisBroker(_configured(settings))
    h = broker.healthcheck()
    assert h["broker"] == "KisBroker"
    assert h["environment"] == "paper"
    assert h["config_loaded"] is True
    assert h["authenticated"] is False
    assert h["account_loaded"] is False
    assert h["last_error"] is None
    assert h["order_execution_implemented"] is False
    assert h["order_methods_fail_closed"] is True
    assert h["capabilities"]["submission"] is False
    assert h["capabilities"]["fills"] is False
    assert h["market_data"]["connected"] is False
    reason = h["market_data"]["reason"].lower()
    assert "skeleton" in reason or "not implemented" in reason


def test_kis_broker_repr_masks_secrets(settings):
    broker = KisBroker(_configured(settings))
    text = repr(broker)
    assert "fake-key" not in text
    assert "fake-secret" not in text
    assert "fake-acc" not in text
    assert "app_key=<set>" in text
    assert "app_secret=<set>" in text


def test_strategy_package_does_not_import_kis():
    root = pathlib.Path(__file__).resolve().parent.parent / "app" / "strategy"
    pattern = re.compile(r"\bapp\.broker\.kis\b")
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not pattern.search(text), f"{path} imports app.broker.kis"


def test_kis_module_does_not_import_http_libraries():
    here = pathlib.Path(__file__).resolve().parent.parent / "app" / "broker" / "kis.py"
    text = here.read_text(encoding="utf-8")
    for forbidden in ("import requests", "from requests", "import httpx", "from httpx", "import aiohttp", "from aiohttp"):
        assert forbidden not in text, f"kis.py must not import HTTP libraries: found '{forbidden}'"
