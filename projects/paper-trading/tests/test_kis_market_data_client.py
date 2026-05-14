from dataclasses import replace

import pytest

from app.broker.kis import KisAuthClient, KisMarketDataClient


def _settings(settings):
    return replace(
        settings,
        kis_env="paper",
        kis_account_no="12345678",
        kis_app_key="fake-key",
        kis_app_secret="fake-secret",
    )


def _market_data(settings):
    auth = KisAuthClient(_settings(settings))
    return KisMarketDataClient(_settings(settings), auth)


def test_market_data_methods_fail_closed(settings):
    market_data = _market_data(settings)
    with pytest.raises(NotImplementedError, match="official documentation"):
        market_data.get_quote("AAPL")
    with pytest.raises(NotImplementedError, match="official documentation"):
        market_data.get_last_price("AAPL")


def test_market_data_healthcheck_disconnected(settings):
    market_data = _market_data(settings)
    result = market_data.healthcheck_market_data()
    assert result["connected"] is False
    assert result["auth_required"] is True
    assert result["auth_present"] is False
    assert "skeleton" in result["reason"]


def test_market_data_repr_does_not_expose_secrets(settings):
    market_data = _market_data(settings)
    text = repr(market_data)
    assert "fake-key" not in text
    assert "fake-secret" not in text
    assert "12345678" not in text
    assert "disconnected" in text
