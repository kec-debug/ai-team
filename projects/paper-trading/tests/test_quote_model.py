from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.domain.quote import Quote


def _q(**overrides) -> Quote:
    data = {
        "symbol": "AAPL",
        "last": Decimal("100"),
        "bid": Decimal("99.95"),
        "ask": Decimal("100.05"),
        "volume": 1_000_000,
        "timestamp": datetime.now(timezone.utc),
        "source": "synthetic",
    }
    data.update(overrides)
    return Quote(**data)


def test_quote_happy_path():
    q = _q()
    assert q.symbol == "AAPL"
    assert q.source == "synthetic"
    assert q.bid_ask_present is True


def test_quote_allows_synthetic_bid_ask_marker():
    q = _q(last=Decimal("100"), bid=Decimal("100"), ask=Decimal("100"), bid_ask_present=False)
    assert q.bid_ask_present is False


def test_quote_rejects_lowercase_symbol():
    with pytest.raises(ValueError, match="uppercase"):
        _q(symbol="aapl")


def test_quote_rejects_non_positive_last():
    with pytest.raises(ValueError, match="last"):
        _q(last=Decimal("0"))


def test_quote_rejects_non_positive_bid():
    with pytest.raises(ValueError, match="bid"):
        _q(bid=Decimal("0"))


def test_quote_rejects_ask_lower_than_bid():
    with pytest.raises(ValueError, match="ask"):
        _q(bid=Decimal("100"), ask=Decimal("99"))


def test_quote_rejects_negative_volume():
    with pytest.raises(ValueError, match="volume"):
        _q(volume=-1)


def test_quote_rejects_naive_timestamp():
    with pytest.raises(ValueError, match="timezone-aware"):
        _q(timestamp=datetime(2026, 5, 15, 9, 0, 0))


def test_quote_rejects_empty_source():
    with pytest.raises(ValueError, match="source"):
        _q(source="")


def test_quote_spread_pct():
    q = _q(last=Decimal("100"), bid=Decimal("99.5"), ask=Decimal("100.5"))
    assert q.spread_pct == Decimal("0.01")


def test_quote_is_stale_old():
    old = datetime.now(timezone.utc) - timedelta(seconds=120)
    q = _q(timestamp=old)
    assert q.is_stale(datetime.now(timezone.utc), max_age_seconds=60) is True


def test_quote_is_fresh_recent():
    recent = datetime.now(timezone.utc) - timedelta(seconds=5)
    q = _q(timestamp=recent)
    assert q.is_stale(datetime.now(timezone.utc), max_age_seconds=60) is False


def test_quote_is_stale_rejects_naive_now():
    q = _q()
    with pytest.raises(ValueError, match="timezone-aware"):
        q.is_stale(datetime(2026, 5, 15, 9, 0, 0), max_age_seconds=60)


def test_quote_frozen_dataclass_immutable():
    q = _q()
    with pytest.raises(FrozenInstanceError):
        q.last = Decimal("999")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        q.bid_ask_present = False  # type: ignore[misc]
