from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.api.server import create_app
from app.domain.enums import OrderType, Session
from app.domain.orders import BrokerOrder, Order, OrderIntent
from app.runtime.paper_runner import PaperRunner
from app.strategy.premarket_gap import PremarketGapVolumeBreakoutStrategy


def test_gap_above_threshold_passes(settings, make_snapshot):
    result = PremarketGapVolumeBreakoutStrategy(settings).evaluate(make_snapshot())
    assert result.passed
    assert "gap_above_threshold" in result.reasons


def test_gap_below_threshold_blocked(settings, make_snapshot):
    result = PremarketGapVolumeBreakoutStrategy(settings).evaluate(make_snapshot(current_price=Decimal("102"), premarket_high=Decimal("102")))
    assert not result.passed
    assert "gap_below_threshold" in result.blockers


def test_volume_below_threshold_blocked(settings, make_snapshot):
    result = PremarketGapVolumeBreakoutStrategy(settings).evaluate(make_snapshot(premarket_volume=99))
    assert not result.passed
    assert "volume_below_threshold" in result.blockers


def test_spread_above_threshold_blocked(settings, make_snapshot):
    result = PremarketGapVolumeBreakoutStrategy(settings).evaluate(make_snapshot(bid=Decimal("100"), ask=Decimal("106")))
    assert not result.passed
    assert "spread_above_threshold" in result.blockers


def test_not_premarket_session_blocked(settings, make_snapshot):
    result = PremarketGapVolumeBreakoutStrategy(settings).evaluate(make_snapshot(session=Session.REGULAR))
    assert not result.passed
    assert "not_premarket_session" in result.blockers


def test_stale_quote_blocked(settings, make_snapshot):
    stale = datetime.now(timezone.utc) - timedelta(minutes=5)
    result = PremarketGapVolumeBreakoutStrategy(settings).evaluate(make_snapshot(timestamp=stale))
    assert not result.passed
    assert "stale_quote" in result.blockers


def test_strategy_result_is_not_executable_order(settings, make_snapshot):
    result = PremarketGapVolumeBreakoutStrategy(settings).evaluate(make_snapshot())
    assert isinstance(result.non_executable_order_intent, OrderIntent)
    assert not isinstance(result.non_executable_order_intent, BrokerOrder)
    assert not isinstance(result.non_executable_order_intent, Order)


def test_no_market_order_generated(settings, make_snapshot):
    result = PremarketGapVolumeBreakoutStrategy(settings).evaluate(make_snapshot())
    assert result.non_executable_order_intent.order_type == OrderType.LIMIT
    assert "MARKET" not in OrderType.__members__


def test_blocked_candidate_does_not_reach_oms(settings, make_snapshot):
    oms = Mock()
    runner = PaperRunner(settings, PremarketGapVolumeBreakoutStrategy(settings), oms)
    runner.run_once([make_snapshot(premarket_volume=1)])
    assert oms.place.call_count == 0


def test_paper_run_endpoint_works(make_snapshot):
    with TestClient(create_app()) as client:
        payload = {
            "snapshots": [
                make_snapshot().model_dump(mode="json"),
                make_snapshot(premarket_volume=1).model_dump(mode="json"),
            ]
        }
        response = client.post("/paper/run", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["total"] == 2
    assert body["summary"]["passed"] == 1
    assert body["summary"]["blocked"] == 1
