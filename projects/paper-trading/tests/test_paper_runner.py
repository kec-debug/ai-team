from unittest.mock import Mock

from app.runtime.paper_runner import PaperRunner
from app.strategy.premarket_gap import PremarketGapVolumeBreakoutStrategy


def test_runner_does_not_call_oms_for_blocked(settings, make_snapshot):
    oms = Mock()
    runner = PaperRunner(settings, PremarketGapVolumeBreakoutStrategy(settings), oms)
    result = runner.run_once([make_snapshot(premarket_volume=1)])
    assert result[0].oms_ack is None
    assert oms.place.call_count == 0


def test_runner_captures_oms_error(settings, make_snapshot):
    oms = Mock()
    oms.place.side_effect = RuntimeError("risk blocked")
    runner = PaperRunner(settings, PremarketGapVolumeBreakoutStrategy(settings), oms)
    result = runner.run_once([make_snapshot()])
    assert result[0].oms_error == "risk blocked"
