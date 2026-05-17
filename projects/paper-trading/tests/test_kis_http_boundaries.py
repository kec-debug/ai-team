from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
import pathlib

import pytest

from app.broker.kis import (
    KisAuthError,
    KisBroker,
    KisCashBalance,
    KisConfigError,
    KisDataUnavailableError,
    KisHttpClient,
    KisOrderRejectedError,
    KisPosition,
)
from app.domain.enums import OrderType, Side, TradingMode
from app.domain.orders import BrokerOrder


def _settings(settings, **overrides):
    data = {
        "kis_env": "paper",
        "kis_account_no": "12345678",
        "kis_app_key": "fake-key",
        "kis_app_secret": "fake-secret",
    }
    data.update(overrides)
    return replace(settings, **data)


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


def test_http_client_has_conservative_defaults_and_no_endpoint(settings):
    client = KisHttpClient(_settings(settings))
    assert client.timeout_seconds == 5.0
    assert client.max_retries == 1
    with pytest.raises(NotImplementedError, match="official KIS endpoint"):
        client.request("POST", "/unknown")


def test_auth_token_storage_and_expiry_state(settings):
    broker = KisBroker(_settings(settings))
    broker.auth._store_token("fake-token", 120)

    assert broker.auth.is_authenticated() is True
    assert broker.auth.get_access_token() == "fake-token"
    assert broker.auth.token_expires_at_relative().startswith("in_")
    assert "fake-token" not in repr(broker.auth)

    broker.auth.clear_token()
    assert broker.auth.is_authenticated() is False
    assert broker.auth.get_access_token() is None


def test_authenticate_fails_closed_without_official_endpoint(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(KisAuthError, match="mock_mode_no_network"):
        broker.authenticate()
    assert broker.auth.last_error == "mock_mode_no_network"


def test_authenticate_rejects_non_paper_and_live(settings):
    with pytest.raises(KisConfigError, match="live_mode_not_supported_yet"):
        KisBroker(_settings(settings, kis_env="paper")).auth.__class__(
            _settings(settings, kis_env="live")
        ).authenticate()

    with pytest.raises(KisAuthError, match="live_trading_enabled"):
        KisBroker(_settings(settings, live_trading_enabled=False)).auth.__class__(
            _settings(settings, live_trading_enabled=True)
        ).authenticate()


def test_account_queries_require_authentication(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(KisAuthError, match="authentication required"):
        broker.get_account()
    with pytest.raises(KisAuthError, match="authentication required"):
        broker.account.get_positions()
    with pytest.raises(KisAuthError, match="authentication required"):
        broker.account.get_cash_balance()


def test_account_parsers_return_internal_models_and_sanitize(settings):
    broker = KisBroker(_settings(settings))
    positions = broker.account.parse_positions_response(
        {
            "account_no": "12345678",
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": "2",
                    "avg_price": "100.50",
                    "market_value": "201.00",
                }
            ],
        }
    )
    cash = broker.account.parse_cash_balance_response(
        {
            "account_no": "12345678",
            "cash": {
                "currency": "USD",
                "cash": "1000.25",
                "withdrawable_cash": "900.25",
            },
        }
    )

    assert positions == [
        KisPosition(
            symbol="AAPL",
            quantity=2,
            avg_price=Decimal("100.50"),
            market_value=Decimal("201.00"),
        )
    ]
    assert cash == KisCashBalance(
        currency="USD",
        cash=Decimal("1000.25"),
        withdrawable_cash=Decimal("900.25"),
    )
    assert broker.account.positions_loaded() is True
    assert broker.account.cash_balance_loaded() is True


def test_market_data_symbol_validation_and_healthcheck(settings):
    broker = KisBroker(_settings(settings))

    with pytest.raises(KisDataUnavailableError, match="invalid_symbol"):
        broker.get_quote("bad symbol!")

    health = broker.market_data.healthcheck_market_data()
    assert health["connected"] is False
    assert health["available"] is False
    assert health["auth_present"] is False
    assert health["last_error"] == "invalid_symbol"


def test_market_data_requires_auth_before_unimplemented_endpoint(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(KisAuthError, match="authentication required"):
        broker.get_quote("AAPL")

    broker.auth._store_token("fake-token", 120)
    with pytest.raises(NotImplementedError, match="confirm market data endpoint"):
        broker.get_quote("AAPL")


def test_order_dry_run_does_not_send_http_and_sanitizes_payload(settings):
    broker = KisBroker(_settings(settings, kis_order_dry_run=True))
    ack = broker.place_order(_broker_order())

    assert ack.status == "dry_run"
    assert ack.broker_order_id is None
    assert broker.last_order_preview is not None
    preview = broker.last_order_preview.payload_sanitized
    assert preview["account_no"] == "<redacted>"
    assert preview["app_key"] == "<redacted>"
    assert "fake-key" not in repr(preview)
    assert "12345678" not in repr(preview)


def test_order_live_http_fails_closed_without_official_endpoint(settings):
    broker = KisBroker(_settings(settings, kis_order_dry_run=False))
    with pytest.raises(NotImplementedError, match="order endpoint"):
        broker.place_order(_broker_order())
    assert broker.last_error == "official_kis_order_endpoint_required"


def test_order_guards_still_reject_unsafe_settings(settings):
    with pytest.raises(RuntimeError, match="live"):
        KisBroker(_settings(settings, kis_env="live"))

    broker = KisBroker(_settings(settings, live_trading_enabled=True))
    with pytest.raises(KisOrderRejectedError, match="live_trading_enabled"):
        broker.place_order(_broker_order())

    broker = KisBroker(_settings(settings, trading_mode=TradingMode.LIVE))
    with pytest.raises(KisOrderRejectedError, match="trading_mode_not_paper"):
        broker.place_order(_broker_order())


def test_cancel_replace_queries_fail_closed(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(NotImplementedError, match="cancel_order"):
        broker.cancel_order("broker-1")
    with pytest.raises(NotImplementedError, match="replace_order"):
        broker.replace_order("broker-1", _broker_order())
    with pytest.raises(NotImplementedError, match="get_open_orders"):
        broker.get_open_orders()
    with pytest.raises(NotImplementedError, match="get_fills"):
        broker.get_fills()
    with pytest.raises(NotImplementedError, match="get_order_status"):
        broker.get_order_status("broker-1")


def test_kis_modules_do_not_import_third_party_http_libs():
    broker_dir = pathlib.Path(__file__).resolve().parents[1] / "app" / "broker"
    forbidden = (
        "import requests",
        "import httpx",
        "import aiohttp",
        "import urllib3",
        "from requests",
        "from httpx",
        "from aiohttp",
    )
    for path in broker_dir.glob("kis*.py"):
        text = path.read_text(encoding="utf-8")
        for needle in forbidden:
            assert needle not in text, f"{path.name}: {needle}"


def test_kis_http_has_no_live_transport_class():
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "broker" / "kis_http.py").read_text(encoding="utf-8")
    assert "LiveTransport" not in src
    assert "class Live" not in src
