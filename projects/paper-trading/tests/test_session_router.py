from datetime import datetime, timezone

from app.domain.enums import Session
from app.session import SessionRouter


def test_session_router_resolves_us_premarket_regular_after_hours_and_closed():
    router = SessionRouter()

    assert router.resolve_us(datetime(2026, 1, 5, 13, 0, tzinfo=timezone.utc)) == Session.PRE_MARKET
    assert router.resolve_us(datetime(2026, 1, 5, 15, 0, tzinfo=timezone.utc)) == Session.REGULAR
    assert router.resolve_us(datetime(2026, 1, 5, 22, 0, tzinfo=timezone.utc)) == Session.AFTER_HOURS
    assert router.resolve_us(datetime(2026, 1, 4, 15, 0, tzinfo=timezone.utc)) == Session.CLOSED


def test_default_session_policy_allows_only_current_premarket_strategy():
    router = SessionRouter()
    policy = router.policy_for_session(Session.PRE_MARKET)

    assert policy.orders_allowed is True
    assert policy.strategy_allowed("premarket_gap_volume_breakout") is True
    assert policy.strategy_allowed("agent_direct_order") is False
    assert policy.symbol_allowed("aapl") is True


def test_default_session_policy_fails_closed_outside_premarket():
    router = SessionRouter()

    assert router.policy_for_session(Session.REGULAR).orders_allowed is False
    assert router.policy_for_session(Session.AFTER_HOURS).orders_allowed is False
    assert router.policy_for_session(Session.CLOSED).orders_allowed is False
