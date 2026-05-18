from datetime import datetime, timezone
from unittest.mock import Mock

from app.domain.enums import TradingMode
from app.runtime.paper_engine import IntentSubmitResult, SubmitIntentsBatchResult
from app.runtime.paper_runner import PaperRunner
from app.strategy.premarket_gap import PremarketGapVolumeBreakoutStrategy


def _ok_batch(intent):
    return SubmitIntentsBatchResult(
        submitted_count=1,
        accepted_count=1,
        rejected_count=0,
        risk_rejected_count=0,
        oms_rejected_count=0,
        results=(
            IntentSubmitResult(
                intent=intent,
                accepted=True,
                oms_id="oms-x",
                broker_order_id="br-y",
                status="accepted",
                rejected_by=None,
                reason=None,
                submitted_at=datetime.now(timezone.utc),
            ),
        ),
        accepted_oms_ids=("oms-x",),
        accepted_broker_order_ids=("br-y",),
    )


def _reject_batch(intent, reason="RiskEngine rejected: symbol_not_allowed", by="risk_engine"):
    return SubmitIntentsBatchResult(
        submitted_count=1,
        accepted_count=0,
        rejected_count=1,
        risk_rejected_count=1 if by == "risk_engine" else 0,
        oms_rejected_count=0 if by == "risk_engine" else 1,
        results=(
            IntentSubmitResult(
                intent=intent,
                accepted=False,
                oms_id=None,
                broker_order_id=None,
                status=None,
                rejected_by=by,
                reason=reason,
                submitted_at=None,
            ),
        ),
        accepted_oms_ids=(),
        accepted_broker_order_ids=(),
    )


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


def test_paper_runner_routes_through_paper_engine_when_provided(settings, make_snapshot):
    paper_engine = Mock()
    paper_engine.submit_intents.side_effect = lambda intents: _ok_batch(intents[0])
    runner = PaperRunner(
        settings,
        PremarketGapVolumeBreakoutStrategy(settings),
        paper_engine=paper_engine,
    )

    result = runner.run_once([make_snapshot()])

    assert result[0].oms_ack is not None
    assert result[0].oms_ack.status == "accepted"
    assert result[0].oms_ack.oms_id == "oms-x"
    assert result[0].oms_ack.broker_order_id == "br-y"
    assert result[0].oms_ack.mode is TradingMode.PAPER
    assert result[0].oms_error is None
    assert paper_engine.submit_intents.call_count == 1


def test_paper_runner_paper_engine_rejection_captured_in_oms_error(settings, make_snapshot):
    paper_engine = Mock()
    paper_engine.submit_intents.side_effect = lambda intents: _reject_batch(intents[0])
    runner = PaperRunner(
        settings,
        PremarketGapVolumeBreakoutStrategy(settings),
        paper_engine=paper_engine,
    )

    result = runner.run_once([make_snapshot()])

    assert result[0].oms_ack is None
    assert result[0].oms_error == "RiskEngine rejected: symbol_not_allowed"


def test_paper_runner_requires_oms_or_paper_engine(settings):
    strategy = PremarketGapVolumeBreakoutStrategy(settings)

    try:
        PaperRunner(settings, strategy)
    except ValueError as exc:
        assert str(exc) == "PaperRunner requires oms or paper_engine"
    else:
        raise AssertionError("PaperRunner should require oms or paper_engine")
