"""Live validation preflight evaluation -- read-only, pure functions.

This module computes a readiness summary for live validation but never
enables anything. ``live_validation_ready=True`` is a UX hint only; no code
path uses this flag to relax any safety gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import Settings


@dataclass(frozen=True)
class PreflightItem:
    key: str
    label_ko: str
    passed: bool
    detail_ko: str


@dataclass(frozen=True)
class LiveValidationStatus:
    live_trading_enabled: bool
    trading_mode: str
    market_orders_allowed: bool
    kis_order_dry_run: bool
    kill_switch_engaged: bool
    broker_type: str
    kis_config_loaded: bool
    kis_authenticated: bool
    kis_market_data_available: bool
    kis_account_loaded: bool
    kis_order_entry_ready: bool
    live_validation_ready: bool
    banner_level: str
    banner_text_ko: str
    items: tuple[PreflightItem, ...]


_BANNER_SAFE = (
    "현재 시스템은 paper / dry-run 전용입니다. "
    "live trading 은 비활성화되어 있으며, 실제 주문은 전송되지 않습니다."
)
_BANNER_DANGER_LIVE = "위험: live trading 값이 true 입니다. 주문 기능은 차단되어야 합니다."
_BANNER_DANGER_MARKET = "위험: 시장가 주문 허용 값이 true 입니다. 시스템은 fail-closed 해야 합니다."
_BANNER_DANGER_SECRET = "위험: secret 노출 가능성이 감지되었습니다."
_BANNER_WARN_KILL = "주의: kill switch 가 engaged 입니다. 새 주문이 차단됩니다."
_BANNER_WARN_AUTH = "주의: KIS config 는 로드됐으나 인증 토큰이 없습니다."


def compute_live_validation_status(
    *,
    settings: Settings,
    paper_engine,
    kis_broker,
    paper_status_payload: dict[str, Any],
) -> LiveValidationStatus:
    """Compute live-validation readiness without side effects."""
    del kis_broker
    trading_mode = str(paper_status_payload.get("mode", ""))
    live_enabled = bool(paper_status_payload.get("live_trading_enabled", False))
    market_allowed = bool(paper_status_payload.get("market_orders_allowed", False))
    dry_run = bool(paper_status_payload.get("kis_order_dry_run", False))
    kill_switch = bool(paper_status_payload.get("kill_switch_engaged", False))
    broker_type = str(paper_status_payload.get("broker_type", "<unknown>"))
    kis_config_loaded = bool(paper_status_payload.get("kis_config_loaded", False))
    kis_authenticated = bool(paper_status_payload.get("kis_authenticated", False))
    kis_market_data_available = bool(paper_status_payload.get("kis_market_data_available", False))
    kis_account_loaded = bool(paper_status_payload.get("kis_account_loaded", False))
    kis_order_entry_ready = bool(paper_status_payload.get("kis_order_entry_ready", False))
    secret_exposed = bool(paper_status_payload.get("secret_exposed", False))

    has_recent_paper = _has_recent_paper_activity(paper_engine)
    ready = (
        trading_mode == "paper"
        and live_enabled is False
        and market_allowed is False
        and dry_run is True
        and kill_switch is False
        and kis_config_loaded
        and secret_exposed is False
        and has_recent_paper
    )

    if live_enabled or market_allowed or secret_exposed:
        banner_level = "danger"
        if live_enabled:
            banner_text = _BANNER_DANGER_LIVE
        elif market_allowed:
            banner_text = _BANNER_DANGER_MARKET
        else:
            banner_text = _BANNER_DANGER_SECRET
    elif kill_switch:
        banner_level = "warning"
        banner_text = _BANNER_WARN_KILL
    elif kis_config_loaded and not kis_authenticated:
        banner_level = "warning"
        banner_text = _BANNER_WARN_AUTH
    else:
        banner_level = "info"
        banner_text = _BANNER_SAFE

    items = (
        PreflightItem(
            "paper_mode_confirmed",
            "Paper mode 확인",
            trading_mode == "paper",
            f"trading_mode={trading_mode!r}",
        ),
        PreflightItem(
            "live_disabled_confirmed",
            "Live disabled 확인",
            live_enabled is False,
            f"live_trading_enabled={live_enabled}",
        ),
        PreflightItem(
            "market_orders_disabled_confirmed",
            "Market order disabled 확인",
            market_allowed is False,
            f"allow_market_orders={market_allowed}",
        ),
        PreflightItem(
            "kis_dry_run_enabled_confirmed",
            "KIS dry-run enabled 확인",
            dry_run is True,
            f"kis_order_dry_run={dry_run}",
        ),
        PreflightItem(
            "secret_exposed_false_confirmed",
            "Secret exposed false 확인",
            secret_exposed is False,
            f"secret_exposed={secret_exposed}",
        ),
        PreflightItem(
            "kill_switch_off_confirmed",
            "Kill switch off 확인",
            kill_switch is False,
            f"kill_switch_engaged={kill_switch}",
        ),
        PreflightItem(
            "kis_config_loaded_confirmed",
            "KIS config loaded 확인",
            kis_config_loaded,
            f"kis_config_loaded={kis_config_loaded}",
        ),
        PreflightItem(
            "dashboard_simulation_available",
            "Dashboard simulation 가능 확인",
            paper_engine is not None,
            "paper_engine is " + ("present" if paper_engine is not None else "missing"),
        ),
        PreflightItem(
            "paper_journal_writable",
            "Paper journal 기록 가능 확인",
            paper_engine is not None and hasattr(paper_engine, "journal"),
            "journal "
            + ("present" if paper_engine is not None and hasattr(paper_engine, "journal") else "missing"),
        ),
        PreflightItem(
            "report_generation_available",
            "Report 생성 가능 확인",
            paper_engine is not None,
            "engine present" if paper_engine is not None else "engine missing",
        ),
        PreflightItem(
            "daily_loss_limit_configured",
            "1일 손실 제한 설정 확인",
            settings.live_validation_daily_loss_limit_usd is not None,
            _detail_optional(settings.live_validation_daily_loss_limit_usd, "USD"),
        ),
        PreflightItem(
            "max_orders_per_day_configured",
            "최대 주문 수 제한 설정 확인",
            settings.live_validation_max_orders_per_day is not None,
            _detail_optional(settings.live_validation_max_orders_per_day, "orders/day"),
        ),
        PreflightItem(
            "symbol_allowlist_configured",
            "허용 종목 whitelist 확인",
            len(settings.symbol_allowlist) > 0,
            f"{len(settings.symbol_allowlist)} symbol(s)",
        ),
        PreflightItem(
            "recent_test_passed_manual",
            "최근 테스트 통과 여부 수동 확인",
            False,
            "수동 확인 필요 - 운영자가 별도 확인",
        ),
    )

    return LiveValidationStatus(
        live_trading_enabled=live_enabled,
        trading_mode=trading_mode,
        market_orders_allowed=market_allowed,
        kis_order_dry_run=dry_run,
        kill_switch_engaged=kill_switch,
        broker_type=broker_type,
        kis_config_loaded=kis_config_loaded,
        kis_authenticated=kis_authenticated,
        kis_market_data_available=kis_market_data_available,
        kis_account_loaded=kis_account_loaded,
        kis_order_entry_ready=kis_order_entry_ready,
        live_validation_ready=ready,
        banner_level=banner_level,
        banner_text_ko=banner_text,
        items=items,
    )


def _detail_optional(value, unit: str) -> str:
    if value is None:
        return "not configured"
    return f"configured at {value} {unit}"


def _has_recent_paper_activity(paper_engine) -> bool:
    if paper_engine is None:
        return False
    journal = getattr(paper_engine, "journal", None)
    if journal is None:
        return False
    trades = getattr(journal, "trades", None) or []
    return len(trades) > 0
