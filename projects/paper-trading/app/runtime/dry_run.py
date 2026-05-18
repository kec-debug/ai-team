"""Long-running paper dry-run controller.

The controller is a synchronous stateful wrapper around PaperRunner. It never
calls KIS directly and never starts a background loop; callers drive ticks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import Settings
from app.domain.market import StrategyInput
from app.runtime.dry_run_report import append_event, append_order, make_run_dir, write_summary
from app.runtime.paper_runner import PaperRunner


STATE_IDLE = "idle"
STATE_RUNNING = "running"
STATE_STOPPED = "stopped"
STATE_AUTO_STOPPED = "auto_stopped"


@dataclass
class DryRunCounters:
    ticks_total: int = 0
    candidates_seen: int = 0
    candidates_blocked: int = 0
    candidates_passed_risk: int = 0
    dry_run_orders_created: int = 0
    dry_run_orders_rejected: int = 0
    oms_rejections: int = 0
    risk_rejections: int = 0
    stale_quote_rejections: int = 0
    spread_rejections: int = 0
    market_order_rejections: int = 0
    kis_fail_closed_count: int = 0
    errors_total: int = 0
    last_error: str | None = None
    kill_switch_blocked_ticks: int = 0


@dataclass
class DryRunState:
    state: str = STATE_IDLE
    started_at: datetime | None = None
    stopped_at: datetime | None = None
    last_tick_at: datetime | None = None
    stop_reason: str | None = None
    run_dir: Path | None = None
    counters: DryRunCounters = field(default_factory=DryRunCounters)


@dataclass(frozen=True)
class DryRunTickResult:
    status: str
    snapshots_evaluated: int
    candidates_passed: int
    candidates_blocked: int
    oms_acks: int
    oms_errors: int


class DryRunController:
    def __init__(self, settings: Settings, paper_runner: PaperRunner, base_dir: Path) -> None:
        self._settings = settings
        self._runner = paper_runner
        self._base_dir = Path(base_dir).resolve()
        self._state = DryRunState()

    @property
    def state(self) -> DryRunState:
        return self._state

    def is_running(self) -> bool:
        return self._state.state == STATE_RUNNING

    def start(self) -> DryRunState:
        if self.is_running():
            raise RuntimeError("dry-run already running")
        now = datetime.now(timezone.utc)
        run_dir = make_run_dir(self._reports_dir(), now)
        self._state = DryRunState(
            state=STATE_RUNNING,
            started_at=now,
            run_dir=run_dir,
            counters=DryRunCounters(),
        )
        self._write_summary()
        return self._state

    def stop(self, reason: str = "manual") -> DryRunState:
        if not self.is_running():
            raise RuntimeError("dry-run not running")
        self._state.state = STATE_STOPPED if reason == "manual" else STATE_AUTO_STOPPED
        self._state.stopped_at = datetime.now(timezone.utc)
        self._state.stop_reason = reason
        self._write_summary()
        return self._state

    def tick(self, snapshots: list[StrategyInput]) -> DryRunTickResult:
        if not self.is_running():
            raise RuntimeError("dry-run not running")
        now = datetime.now(timezone.utc)
        counters = self._state.counters
        self._state.last_tick_at = now
        counters.ticks_total += 1

        if self._settings.kill_switch_engaged:
            counters.kill_switch_blocked_ticks += 1
            self._append_event(
                {
                    "ts": now.isoformat(),
                    "type": "tick_blocked",
                    "reason": "kill_switch_engaged",
                    "snapshots": len(snapshots),
                }
            )
            self._write_summary()
            return DryRunTickResult(
                status="blocked_kill_switch",
                snapshots_evaluated=0,
                candidates_passed=0,
                candidates_blocked=0,
                oms_acks=0,
                oms_errors=0,
            )

        try:
            results = self._runner.run_once(snapshots)
        except Exception as exc:
            counters.errors_total += 1
            counters.last_error = type(exc).__name__
            self._append_event(
                {
                    "ts": now.isoformat(),
                    "type": "runner_error",
                    "error_class": type(exc).__name__,
                }
            )
            self._maybe_auto_stop()
            self._write_summary()
            return DryRunTickResult(
                status="auto_stopped" if not self.is_running() else "ok",
                snapshots_evaluated=0,
                candidates_passed=0,
                candidates_blocked=0,
                oms_acks=0,
                oms_errors=1,
            )

        counters.candidates_seen += len(results)
        passed = blocked = oms_acks = oms_errors = 0
        for item in results:
            self._append_event(
                {
                    "ts": now.isoformat(),
                    "type": "tick_result",
                    "symbol": item.symbol,
                    "passed": item.strategy.passed,
                    "blockers": list(item.strategy.blockers),
                    "oms_status": item.oms_ack.status if item.oms_ack else None,
                    "oms_error": item.oms_error,
                }
            )
            if item.strategy.passed:
                passed += 1
                counters.candidates_passed_risk += 1
                if item.oms_ack is not None:
                    oms_acks += 1
                    counters.dry_run_orders_created += 1
                    self._append_order(self._order_row(now, item))
                else:
                    oms_errors += 1
                    counters.oms_rejections += 1
                    counters.dry_run_orders_rejected += 1
                    self._classify_oms_error(item.oms_error)
            else:
                blocked += 1
                counters.candidates_blocked += 1
                self._classify_strategy_blockers(item.strategy.blockers)

        if self._settings.dry_run_max_ticks and counters.ticks_total >= self._settings.dry_run_max_ticks:
            self._auto_stop("max_ticks_reached")
            self._write_summary()
            return DryRunTickResult("max_ticks_reached", len(results), passed, blocked, oms_acks, oms_errors)

        self._maybe_auto_stop()
        self._write_summary()
        return DryRunTickResult(
            status="auto_stopped" if not self.is_running() else "ok",
            snapshots_evaluated=len(results),
            candidates_passed=passed,
            candidates_blocked=blocked,
            oms_acks=oms_acks,
            oms_errors=oms_errors,
        )

    def summary(self) -> dict[str, Any]:
        state = self._state
        counters = state.counters
        uptime = 0
        if state.started_at is not None:
            end = state.stopped_at or datetime.now(timezone.utc)
            uptime = int((end - state.started_at).total_seconds())
        return {
            "state": state.state,
            "running": self.is_running(),
            "started_at": state.started_at.isoformat() if state.started_at else None,
            "stopped_at": state.stopped_at.isoformat() if state.stopped_at else None,
            "last_tick_at": state.last_tick_at.isoformat() if state.last_tick_at else None,
            "stop_reason": state.stop_reason,
            "uptime_seconds": uptime,
            "run_dir": self._relative_run_dir(),
            "counters": vars(counters).copy(),
            "config": {
                "kis_order_dry_run": bool(self._settings.kis_order_dry_run),
                "live_trading_enabled": bool(self._settings.live_trading_enabled),
                "allow_market_orders": bool(self._settings.allow_market_orders),
                "kill_switch_engaged": bool(self._settings.kill_switch_engaged),
                "max_errors_before_auto_stop": self._settings.dry_run_max_errors_before_auto_stop,
                "max_ticks": self._settings.dry_run_max_ticks,
            },
            "secret_exposed": False,
        }

    def _reports_dir(self) -> Path:
        raw_path = Path(self._settings.dry_run_reports_dir)
        if raw_path.is_absolute():
            raise RuntimeError("dry_run_reports_dir must be a project-relative path")
        reports_dir = (self._base_dir / raw_path).resolve()
        if reports_dir != self._base_dir and self._base_dir not in reports_dir.parents:
            raise RuntimeError("dry_run_reports_dir must stay inside project directory")
        return reports_dir

    def _relative_run_dir(self) -> str | None:
        if self._state.run_dir is None:
            return None
        return str(self._state.run_dir.relative_to(self._base_dir))

    def _append_event(self, event: dict[str, Any]) -> None:
        if self._state.run_dir is not None:
            append_event(self._state.run_dir, event)

    def _append_order(self, order: dict[str, Any]) -> None:
        if self._state.run_dir is not None:
            append_order(self._state.run_dir, order)

    def _write_summary(self) -> None:
        if self._state.run_dir is not None:
            write_summary(self._state.run_dir, self.summary())

    def _maybe_auto_stop(self) -> None:
        if self._state.counters.errors_total >= self._settings.dry_run_max_errors_before_auto_stop:
            self._auto_stop("error_threshold")

    def _auto_stop(self, reason: str) -> None:
        if not self.is_running():
            return
        self._state.state = STATE_AUTO_STOPPED
        self._state.stopped_at = datetime.now(timezone.utc)
        self._state.stop_reason = reason

    def _classify_strategy_blockers(self, blockers: list[str]) -> None:
        counters = self._state.counters
        for reason in blockers:
            if reason == "stale_quote":
                counters.stale_quote_rejections += 1
            if "spread" in reason:
                counters.spread_rejections += 1
            if "market" in reason or reason == "order_type_not_limit":
                counters.market_order_rejections += 1

    def _classify_oms_error(self, error: str | None) -> None:
        if not error:
            return
        counters = self._state.counters
        lowered = error.lower()
        if "riskengine rejected" in lowered:
            counters.risk_rejections += 1
        if "market" in lowered:
            counters.market_order_rejections += 1
        if "notimplemented" in lowered or "not implemented" in lowered:
            counters.kis_fail_closed_count += 1
        counters.last_error = error

    def _order_row(self, now: datetime, item: Any) -> dict[str, Any]:
        intent = item.strategy.non_executable_order_intent
        return {
            "ts": now.isoformat(),
            "symbol": item.symbol,
            "side": intent.side.value if intent else "",
            "quantity": intent.quantity if intent else "",
            "limit_price": str(intent.limit_price) if intent else "",
            "order_type": intent.order_type.value if intent else "",
            "oms_status": item.oms_ack.status if item.oms_ack else "",
            "broker_environment": "paper",
            "idempotency_key": "",
        }
