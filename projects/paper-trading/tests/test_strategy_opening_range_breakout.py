"""strategy-002 — Opening Range Breakout tests."""

import pathlib
import re
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.domain.enums import OrderType, Session, Side, TradingMode
from app.domain.market import StrategyInput
from app.strategy import STRATEGY_NAMES, create_strategy
from app.strategy.opening_range_breakout import OpeningRangeBreakoutStrategy


@pytest.fixture
def orb_settings(settings):
    return replace(settings, symbol_allowlist=("AAPL",))


@pytest.fixture
def orb_snapshot():
    def _make(**overrides) -> StrategyInput:
        data = {
            "symbol": "AAPL",
            "market": "US",
            "session": Session.REGULAR,
            "previous_close": Decimal("100"),
            "current_price": Decimal("106"),
            "premarket_high": Decimal("106"),
            "premarket_volume": 200_000,
            "bid": Decimal("105.90"),
            "ask": Decimal("106.00"),
            "timestamp": datetime.now(timezone.utc),
            "relative_volume": Decimal("2.0"),
            "opening_range_high": Decimal("105"),
            "opening_range_low": Decimal("103"),
            "vwap": Decimal("104"),
        }
        data.update(overrides)
        return StrategyInput(**data)

    return _make


# ── Registry ──────────────────────────────────────────────────────────────────


def test_strategy_registered_in_strategy_names():
    assert "opening_range_breakout" in STRATEGY_NAMES


def test_create_strategy_returns_orb_instance(orb_settings):
    strategy = create_strategy("opening_range_breakout", orb_settings)
    assert isinstance(strategy, OpeningRangeBreakoutStrategy)
    assert strategy.name == "opening_range_breakout"


# ── Happy path ────────────────────────────────────────────────────────────────


def test_breakout_above_opening_range_passes(orb_settings, orb_snapshot):
    strategy = OpeningRangeBreakoutStrategy(orb_settings)
    result = strategy.evaluate(orb_snapshot())
    assert result.passed is True
    assert result.blockers == []
    assert "above_opening_range_high" in result.reasons
    assert "relative_volume_above_threshold" in result.reasons
    assert "price_above_vwap" in result.reasons
    assert "quote_fresh" in result.reasons


def test_intent_is_limit_buy_non_executable(orb_settings, orb_snapshot):
    strategy = OpeningRangeBreakoutStrategy(orb_settings)
    result = strategy.evaluate(orb_snapshot())
    assert result.non_executable_order_intent is not None
    intent = result.non_executable_order_intent
    assert intent.order_type == OrderType.LIMIT
    assert intent.side == Side.BUY
    assert intent.symbol == "AAPL"
    assert intent.client_tag == "opening_range_breakout"
    assert intent.limit_price == Decimal("106.00")


def test_score_scales_with_breakout_magnitude(orb_settings, orb_snapshot):
    strategy = OpeningRangeBreakoutStrategy(orb_settings)
    # Just barely above the high: score should be small
    small_result = strategy.evaluate(
        orb_snapshot(current_price=Decimal("105.1"), opening_range_high=Decimal("105")),
    )
    # Large breakout: score should be capped at 1.0
    large_result = strategy.evaluate(
        orb_snapshot(current_price=Decimal("120"), opening_range_high=Decimal("105")),
    )
    assert small_result.score is not None and small_result.score < large_result.score
    assert large_result.score == 1.0


# ── Blockers ──────────────────────────────────────────────────────────────────


def test_blocked_when_session_not_regular(orb_settings, orb_snapshot):
    strategy = OpeningRangeBreakoutStrategy(orb_settings)
    result = strategy.evaluate(orb_snapshot(session=Session.PRE_MARKET))
    assert result.passed is False
    assert "not_regular_session" in result.blockers


def test_blocked_when_opening_range_high_missing(orb_settings, orb_snapshot):
    strategy = OpeningRangeBreakoutStrategy(orb_settings)
    result = strategy.evaluate(orb_snapshot(opening_range_high=None))
    assert result.passed is False
    assert "no_opening_range_data" in result.blockers


def test_blocked_when_price_below_opening_range_high(orb_settings, orb_snapshot):
    strategy = OpeningRangeBreakoutStrategy(orb_settings)
    result = strategy.evaluate(
        orb_snapshot(current_price=Decimal("100"), opening_range_high=Decimal("105")),
    )
    assert result.passed is False
    assert "not_above_opening_range_high" in result.blockers
    assert result.non_executable_order_intent is None


def test_blocked_when_relative_volume_below_threshold(orb_settings, orb_snapshot):
    strategy = OpeningRangeBreakoutStrategy(orb_settings)
    result = strategy.evaluate(orb_snapshot(relative_volume=Decimal("0.5")))
    assert result.passed is False
    assert "relative_volume_below_threshold" in result.blockers


def test_blocked_when_relative_volume_missing(orb_settings, orb_snapshot):
    strategy = OpeningRangeBreakoutStrategy(orb_settings)
    result = strategy.evaluate(orb_snapshot(relative_volume=None))
    assert result.passed is False
    assert "relative_volume_missing" in result.blockers


def test_blocked_when_price_below_vwap(orb_settings, orb_snapshot):
    strategy = OpeningRangeBreakoutStrategy(orb_settings)
    result = strategy.evaluate(
        orb_snapshot(current_price=Decimal("106"), vwap=Decimal("108")),
    )
    assert result.passed is False
    assert "price_below_vwap" in result.blockers


def test_vwap_optional_passes_when_missing(orb_settings, orb_snapshot):
    strategy = OpeningRangeBreakoutStrategy(orb_settings)
    result = strategy.evaluate(orb_snapshot(vwap=None))
    # vwap=None means no vwap check; other gates still apply
    assert result.passed is True
    assert "price_above_vwap" not in result.reasons


def test_blocked_when_spread_too_wide(orb_settings, orb_snapshot):
    strategy = OpeningRangeBreakoutStrategy(orb_settings)
    result = strategy.evaluate(
        orb_snapshot(bid=Decimal("100"), ask=Decimal("106")),
    )
    assert result.passed is False
    assert "spread_above_threshold" in result.blockers


def test_blocked_when_quote_stale(orb_settings, orb_snapshot):
    strategy = OpeningRangeBreakoutStrategy(orb_settings)
    stale = datetime.now(timezone.utc) - timedelta(
        seconds=orb_settings.premarket_max_quote_age_seconds + 1
    )
    result = strategy.evaluate(orb_snapshot(timestamp=stale))
    assert result.passed is False
    assert "stale_quote" in result.blockers


def test_blocked_when_live_trading_enabled(orb_settings, orb_snapshot):
    strategy = OpeningRangeBreakoutStrategy(
        replace(orb_settings, live_trading_enabled=True),
    )
    result = strategy.evaluate(orb_snapshot())
    assert result.passed is False
    assert "live_trading_disabled" in result.blockers


def test_blocked_when_non_us_market(orb_settings, orb_snapshot):
    strategy = OpeningRangeBreakoutStrategy(orb_settings)
    result = strategy.evaluate(orb_snapshot(market="HK"))
    assert result.passed is False
    assert "market_not_supported" in result.blockers


# ── Isolation regression ──────────────────────────────────────────────────────


def test_strategy_does_not_import_broker_modules():
    text = (
        pathlib.Path(__file__).resolve().parents[1]
        / "app"
        / "strategy"
        / "opening_range_breakout.py"
    ).read_text(encoding="utf-8")
    forbidden = re.compile(r"^\s*(from|import)\s+app\.broker", re.MULTILINE)
    assert not forbidden.search(text)


def test_strategy_does_not_import_or_call_oms_or_riskengine():
    text = (
        pathlib.Path(__file__).resolve().parents[1]
        / "app"
        / "strategy"
        / "opening_range_breakout.py"
    ).read_text(encoding="utf-8")
    # No import of OMS/RiskEngine
    assert re.search(r"^\s*(from|import)\s+app\.(oms|risk)", text, re.MULTILINE) is None
    # No instantiation or call (docstring mention is OK)
    assert "OMS(" not in text
    assert "RiskEngine(" not in text
    assert ".place(" not in text
    assert ".evaluate_intent(" not in text


def test_market_orders_never_generated(orb_settings, orb_snapshot):
    """Confirm the strategy NEVER emits an OrderType.MARKET intent under any path."""
    strategy = OpeningRangeBreakoutStrategy(orb_settings)
    for variant in (
        orb_snapshot(),
        orb_snapshot(current_price=Decimal("110"), opening_range_high=Decimal("105")),
        orb_snapshot(current_price=Decimal("200"), opening_range_high=Decimal("105")),
    ):
        result = strategy.evaluate(variant)
        if result.non_executable_order_intent is not None:
            assert result.non_executable_order_intent.order_type == OrderType.LIMIT
