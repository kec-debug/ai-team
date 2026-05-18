from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.broker.kis_quote_mapper import kis_raw_quote_to_domain
from app.domain.enums import Session


def _received_at() -> datetime:
    return datetime(2026, 5, 18, 12, 0, tzinfo=timezone.utc)


def test_mapper_converts_confirmed_overseas_price_response():
    quote = kis_raw_quote_to_domain(
        {"rt_cd": "0", "output": {"last": "191.23", "tvol": "1,234", "rsym": "DNASAAPL"}},
        symbol="aapl",
        received_at=_received_at(),
        session=Session.REGULAR,
    )

    assert quote.symbol == "AAPL"
    assert quote.last == Decimal("191.23")
    assert quote.bid == Decimal("191.23")
    assert quote.ask == Decimal("191.23")
    assert quote.volume == 1234
    assert quote.timestamp == _received_at()
    assert quote.source == "kis_paper"
    assert quote.session is Session.REGULAR
    assert quote.currency == "USD"
    assert quote.bid_ask_present is False


def test_mapper_rejects_none_raw():
    with pytest.raises(ValueError, match="None"):
        kis_raw_quote_to_domain(None, symbol="AAPL", received_at=_received_at())


def test_mapper_rejects_non_dict_raw():
    with pytest.raises(ValueError, match="raw is not dict"):
        kis_raw_quote_to_domain("bad", symbol="AAPL", received_at=_received_at())  # type: ignore[arg-type]


def test_mapper_rejects_empty_symbol():
    with pytest.raises(ValueError, match="symbol"):
        kis_raw_quote_to_domain({"output": {"last": "1", "tvol": "0"}}, symbol="", received_at=_received_at())


def test_mapper_rejects_naive_received_at():
    with pytest.raises(ValueError, match="timezone-aware"):
        kis_raw_quote_to_domain(
            {"output": {"last": "1", "tvol": "0"}},
            symbol="AAPL",
            received_at=datetime(2026, 5, 18, 12, 0),
        )


def test_mapper_rejects_kis_error_response():
    with pytest.raises(ValueError, match="kis_error:EGW001"):
        kis_raw_quote_to_domain(
            {"rt_cd": "1", "msg_cd": "EGW001", "output": {"last": "1", "tvol": "0"}},
            symbol="AAPL",
            received_at=_received_at(),
        )


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ({}, "output missing"),
        ({"output": {"tvol": "10"}}, "last missing"),
        ({"output": {"last": "", "tvol": "10"}}, "last missing"),
        ({"output": {"last": "100"}}, "tvol missing"),
        ({"output": {"last": "0", "tvol": "10"}}, "last not positive"),
        ({"output": {"last": "100", "tvol": "-1"}}, "volume negative"),
    ],
)
def test_mapper_rejects_malformed_output(raw, message):
    with pytest.raises(ValueError, match=message):
        kis_raw_quote_to_domain(raw, symbol="AAPL", received_at=_received_at())
