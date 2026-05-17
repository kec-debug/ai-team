from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.broker.kis import KisBroker, KisOrderRejectedError, validate_kis_order_request
from app.domain.enums import OrderType, Side, TradingMode
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


def test_preflight_passes_for_valid_paper_limit_order(settings):
    assert validate_kis_order_request(_settings(settings), _broker_order()) is None


def test_preflight_allows_stop_limit_order(settings):
    assert validate_kis_order_request(
        _settings(settings),
        _broker_order(order_type=OrderType.STOP_LIMIT),
    ) is None


def test_preflight_rejects_non_paper_trading_mode(settings):
    bad = replace(_settings(settings), trading_mode=TradingMode.LIVE)
    with pytest.raises(KisOrderRejectedError, match="trading_mode_not_paper") as exc:
        validate_kis_order_request(bad, _broker_order())
    assert exc.value.reason == "trading_mode_not_paper"


def test_preflight_rejects_live_trading_enabled(settings):
    bad = replace(_settings(settings), live_trading_enabled=True)
    with pytest.raises(KisOrderRejectedError, match="live_trading_enabled") as exc:
        validate_kis_order_request(bad, _broker_order())
    assert exc.value.reason == "live_trading_enabled"


def test_preflight_rejects_allow_market_orders_flag(settings):
    bad = replace(_settings(settings), allow_market_orders=True)
    with pytest.raises(KisOrderRejectedError, match="market_orders_allowed_flag_set") as exc:
        validate_kis_order_request(bad, _broker_order())
    assert exc.value.reason == "market_orders_allowed_flag_set"


def test_preflight_rejects_kis_env_not_paper(settings):
    bad = replace(_settings(settings), kis_env="live")
    with pytest.raises(KisOrderRejectedError, match="kis_env_not_paper") as exc:
        validate_kis_order_request(bad, _broker_order())
    assert exc.value.reason == "kis_env_not_paper"


def test_preflight_rejects_kill_switch_engaged(settings):
    bad = replace(_settings(settings), kill_switch_engaged=True)
    with pytest.raises(KisOrderRejectedError, match="kill_switch_engaged") as exc:
        validate_kis_order_request(bad, _broker_order())
    assert exc.value.reason == "kill_switch_engaged"


def test_preflight_rejects_non_limit_order_type(settings):
    assert "MARKET" not in OrderType.__members__
    bad_order = _broker_order(order_type=None)  # type: ignore[arg-type]
    with pytest.raises(KisOrderRejectedError, match="order_type_not_limit") as exc:
        validate_kis_order_request(_settings(settings), bad_order)
    assert exc.value.reason == "order_type_not_limit"


def test_preflight_rejects_zero_quantity(settings):
    with pytest.raises(KisOrderRejectedError, match="quantity_invalid") as exc:
        validate_kis_order_request(_settings(settings), _broker_order(quantity=0))
    assert exc.value.reason == "quantity_invalid"


def test_preflight_rejects_zero_limit_price(settings):
    with pytest.raises(KisOrderRejectedError, match="limit_price_invalid") as exc:
        validate_kis_order_request(
            _settings(settings),
            _broker_order(limit_price=Decimal("0")),
        )
    assert exc.value.reason == "limit_price_invalid"


def test_preflight_rejects_missing_quote_timestamp(settings):
    with pytest.raises(KisOrderRejectedError, match="stale_quote") as exc:
        validate_kis_order_request(
            _settings(settings),
            _broker_order(quote_timestamp=None),
        )
    assert exc.value.reason == "stale_quote"


def test_preflight_rejects_stale_quote_timestamp(settings):
    now = datetime.now(timezone.utc)
    with pytest.raises(KisOrderRejectedError, match="stale_quote") as exc:
        validate_kis_order_request(
            _settings(settings),
            _broker_order(
                submitted_at=now,
                quote_timestamp=now - timedelta(seconds=settings.premarket_max_quote_age_seconds + 1),
            ),
        )
    assert exc.value.reason == "stale_quote"


def test_place_order_runs_preflight_before_notimplemented(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(KisOrderRejectedError, match="quantity_invalid"):
        broker.place_order(_broker_order(quantity=0))


def test_place_order_valid_input_reaches_notimplemented(settings):
    broker = KisBroker(_settings(settings))
    ack = broker.place_order(_broker_order())
    assert ack.status == "dry_run"
    assert broker.last_order_preview is not None


def test_place_order_valid_input_with_dry_run_disabled_reaches_notimplemented(settings):
    broker = KisBroker(replace(_settings(settings), kis_order_dry_run=False))
    with pytest.raises(NotImplementedError, match="Pre-flight passed"):
        broker.place_order(_broker_order())
