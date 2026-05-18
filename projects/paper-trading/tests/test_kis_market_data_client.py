from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.broker.kis import (
    KisAuthClient,
    KisAuthError,
    KisDataUnavailableError,
    KisMarketDataClient,
    UrllibMarketDataTransport,
)


def _settings(settings, **overrides):
    data = {
        "kis_env": "paper",
        "kis_account_no": "12345678",
        "kis_app_key": "fake-key",
        "kis_app_secret": "fake-secret",
    }
    data.update(overrides)
    return replace(settings, **data)


class FakeTransport:
    def __init__(self, raw=None, error: Exception | None = None) -> None:
        self.raw = raw or {"rt_cd": "0", "output": {"last": "191.23", "tvol": "1000"}}
        self.error = error
        self.calls: list[dict[str, str]] = []

    def get_quote(self, **kwargs):
        self.calls.append(
            {
                "base_url": kwargs["base_url"],
                "exchange": kwargs["exchange"],
                "symbol": kwargs["symbol"],
            }
        )
        if self.error is not None:
            raise self.error
        return self.raw, datetime(2026, 5, 18, 12, 0, tzinfo=timezone.utc)


def _client(settings, transport=None, **overrides):
    configured = _settings(settings, **overrides)
    auth = KisAuthClient(configured)
    return KisMarketDataClient(configured, auth, transport=transport), auth


def test_market_data_requires_auth_before_transport(settings):
    transport = FakeTransport()
    market_data, _auth = _client(settings, transport=transport)

    with pytest.raises(KisAuthError, match="authentication required"):
        market_data.get_quote("AAPL")
    with pytest.raises(KisAuthError, match="authentication required"):
        market_data.get_last_price("AAPL")
    assert transport.calls == []


def test_market_data_get_quote_maps_confirmed_response(settings):
    transport = FakeTransport()
    market_data, auth = _client(settings, transport=transport)
    auth._store_token("fake-token", 120)

    quote = market_data.get_quote("aapl")

    assert quote.symbol == "AAPL"
    assert quote.last == Decimal("191.23")
    assert quote.bid == quote.last
    assert quote.ask == quote.last
    assert quote.volume == 1000
    assert quote.source == "kis_paper"
    assert quote.bid_ask_present is False
    assert transport.calls == [
        {
            "base_url": "https://openapivts.koreainvestment.com:29443",
            "exchange": "NAS",
            "symbol": "AAPL",
        }
    ]
    assert market_data.last_error is None


def test_market_data_get_last_price_returns_decimal(settings):
    market_data, auth = _client(settings, transport=FakeTransport())
    auth._store_token("fake-token", 120)

    assert market_data.get_last_price("AAPL") == Decimal("191.23")


def test_market_data_transport_error_sets_last_error(settings):
    market_data, auth = _client(settings, transport=FakeTransport(error=KisDataUnavailableError("transport_error")))
    auth._store_token("fake-token", 120)

    with pytest.raises(KisDataUnavailableError, match="transport_error"):
        market_data.get_quote("AAPL")
    assert market_data.last_error == "transport_error"


def test_market_data_malformed_response_fails_closed(settings):
    market_data, auth = _client(settings, transport=FakeTransport(raw={"rt_cd": "0", "output": {"last": "", "tvol": "1"}}))
    auth._store_token("fake-token", 120)

    with pytest.raises(KisDataUnavailableError, match="malformed_response"):
        market_data.get_quote("AAPL")
    assert market_data.last_error is not None
    assert market_data.last_error.startswith("malformed_response")


def test_market_data_healthcheck_mock_mode_no_network(settings):
    market_data, _auth = _client(settings)

    result = market_data.healthcheck_market_data()
    assert result["connected"] is False
    assert result["available"] is False
    assert result["auth_required"] is True
    assert result["auth_present"] is False
    assert result["reason"] == "mock_mode_no_network"


def test_market_data_healthcheck_available_with_authenticated_transport(settings):
    market_data, auth = _client(settings, transport=FakeTransport())
    auth._store_token("fake-token", 120)

    result = market_data.healthcheck_market_data()
    assert result["connected"] is True
    assert result["available"] is True
    assert result["auth_present"] is True
    assert result["reason"] is None


def test_market_data_repr_does_not_expose_secrets(settings):
    market_data, _auth = _client(settings)
    text = repr(market_data)
    assert "fake-key" not in text
    assert "fake-secret" not in text
    assert "12345678" not in text
    assert "mock" in text


def test_market_data_invalid_symbol_fails_closed(settings):
    market_data, _auth = _client(settings, transport=FakeTransport())

    with pytest.raises(KisDataUnavailableError, match="invalid_symbol"):
        market_data.get_quote("bad symbol!")


def test_urllib_transport_rejects_unconfirmed_exchange_without_network():
    transport = UrllibMarketDataTransport()

    with pytest.raises(KisDataUnavailableError, match="invalid_exchange"):
        transport.get_quote(
            base_url="https://openapivts.koreainvestment.com:29443",
            access_token="fake-token",
            app_key="fake-key",
            app_secret="fake-secret",
            exchange="BAD",
            symbol="AAPL",
        )


def test_urllib_transport_rejects_non_paper_host_without_network():
    transport = UrllibMarketDataTransport()

    with pytest.raises(KisDataUnavailableError, match="paper_market_data_host_required"):
        transport.get_quote(
            base_url="https://example.invalid",
            access_token="fake-token",
            app_key="fake-key",
            app_secret="fake-secret",
            exchange="NAS",
            symbol="AAPL",
        )
