from dataclasses import replace
from decimal import Decimal

import pytest

from app.broker.paper import PaperBroker
from app.oms.manager import OMS
from app.risk.engine import RiskEngine
from app.runtime.dry_run import DryRunController
from app.runtime.paper_runner import PaperRunner
from app.strategy.premarket_gap import PremarketGapVolumeBreakoutStrategy


def _controller(settings, tmp_path, runner=None, reports_dir="reports"):
    local_settings = replace(settings, dry_run_reports_dir=reports_dir)
    if runner is None:
        runner = PaperRunner(
            local_settings,
            PremarketGapVolumeBreakoutStrategy(local_settings),
            OMS(local_settings, RiskEngine(local_settings), PaperBroker()),
        )
    return DryRunController(local_settings, runner, tmp_path)


def test_start_creates_running_state_and_run_dir(settings, tmp_path):
    controller = _controller(settings, tmp_path)
    state = controller.start()
    assert state.state == "running"
    assert state.run_dir is not None
    assert state.run_dir.is_dir()
    assert tmp_path in state.run_dir.parents


def test_double_start_raises(settings, tmp_path):
    controller = _controller(settings, tmp_path)
    controller.start()
    with pytest.raises(RuntimeError, match="already running"):
        controller.start()


def test_stop_transitions_to_stopped(settings, tmp_path):
    controller = _controller(settings, tmp_path)
    controller.start()
    state = controller.stop()
    assert state.state == "stopped"
    assert state.stop_reason == "manual"


def test_tick_increments_counters(settings, tmp_path, make_snapshot):
    controller = _controller(settings, tmp_path)
    controller.start()
    result = controller.tick([make_snapshot()])
    summary = controller.summary()
    assert result.snapshots_evaluated == 1
    assert summary["counters"]["ticks_total"] == 1
    assert summary["counters"]["candidates_seen"] == 1
    assert result.oms_acks == 1


def test_tick_blocked_candidate_increments_blocked_counter(settings, tmp_path, make_snapshot):
    controller = _controller(settings, tmp_path)
    controller.start()
    result = controller.tick([make_snapshot(current_price=Decimal("102"), premarket_high=Decimal("102"))])
    summary = controller.summary()
    assert result.candidates_blocked == 1
    assert summary["counters"]["candidates_blocked"] == 1
    assert summary["counters"]["candidates_passed_risk"] == 0


def test_kill_switch_blocks_tick(settings, tmp_path, make_snapshot):
    controller = _controller(replace(settings, kill_switch_engaged=True), tmp_path)
    controller.start()
    result = controller.tick([make_snapshot()])
    summary = controller.summary()
    assert result.status == "blocked_kill_switch"
    assert result.snapshots_evaluated == 0
    assert summary["counters"]["kill_switch_blocked_ticks"] == 1
    assert summary["counters"]["candidates_seen"] == 0


def test_auto_stop_after_max_ticks(settings, tmp_path, make_snapshot):
    controller = _controller(replace(settings, dry_run_max_ticks=2), tmp_path)
    controller.start()
    assert controller.tick([make_snapshot()]).status == "ok"
    assert controller.tick([make_snapshot()]).status == "max_ticks_reached"
    summary = controller.summary()
    assert summary["state"] == "auto_stopped"
    assert summary["stop_reason"] == "max_ticks_reached"


class RaisingRunner:
    def run_once(self, snapshots):
        raise RuntimeError("forced runner failure")


def test_auto_stop_after_error_threshold(settings, tmp_path, make_snapshot):
    local_settings = replace(settings, dry_run_reports_dir="reports", dry_run_max_errors_before_auto_stop=2)
    controller = DryRunController(local_settings, RaisingRunner(), tmp_path)
    controller.start()
    assert controller.tick([make_snapshot()]).status == "ok"
    assert controller.tick([make_snapshot()]).status == "auto_stopped"
    summary = controller.summary()
    assert summary["state"] == "auto_stopped"
    assert summary["stop_reason"] == "error_threshold"
    assert summary["counters"]["errors_total"] == 2


def test_summary_has_secret_exposed_false(settings, tmp_path):
    controller = _controller(settings, tmp_path)
    controller.start()
    assert controller.summary()["secret_exposed"] is False


def test_absolute_report_path_is_rejected(settings, tmp_path):
    controller = _controller(settings, tmp_path, reports_dir=str(tmp_path / "reports"))
    with pytest.raises(RuntimeError, match="project-relative"):
        controller.start()
