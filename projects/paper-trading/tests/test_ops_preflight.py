from dataclasses import replace
from decimal import Decimal

from app.config import Settings
from app.ops.preflight import compute_live_validation_status


class _Journal:
    def __init__(self, trades=None):
        self.trades = list(trades or [])


class _PaperEngine:
    def __init__(self, trades=None):
        self.journal = _Journal(trades)


def _payload(**overrides):
    payload = {
        "mode": "paper",
        "live_trading_enabled": False,
        "market_orders_allowed": False,
        "kis_order_dry_run": True,
        "kill_switch_engaged": False,
        "broker_type": "PaperBroker",
        "kis_config_loaded": True,
        "kis_authenticated": True,
        "kis_market_data_available": True,
        "kis_account_loaded": True,
        "kis_order_entry_ready": False,
        "secret_exposed": False,
    }
    payload.update(overrides)
    return payload


def _status(settings=None, paper_engine=None, payload=None):
    return compute_live_validation_status(
        settings=settings or Settings(symbol_allowlist=("AAPL",)),
        paper_engine=paper_engine if paper_engine is not None else _PaperEngine(trades=[object()]),
        kis_broker=None,
        paper_status_payload=payload or _payload(),
    )


def test_live_validation_ready_true_when_all_required_status_inputs_pass():
    status = _status()
    assert status.live_validation_ready is True
    assert status.banner_level == "info"
    assert len(status.items) == 14


def test_ready_false_when_no_recent_paper_activity():
    status = _status(paper_engine=_PaperEngine())
    assert status.live_validation_ready is False


def test_ready_false_when_paper_engine_missing():
    status = compute_live_validation_status(
        settings=Settings(symbol_allowlist=("AAPL",)),
        paper_engine=None,
        kis_broker=None,
        paper_status_payload=_payload(),
    )
    assert status.live_validation_ready is False
    items = {item.key: item.passed for item in status.items}
    assert items["dashboard_simulation_available"] is False
    assert items["paper_journal_writable"] is False


def test_live_enabled_escalates_danger_and_ready_false():
    status = _status(payload=_payload(live_trading_enabled=True))
    assert status.live_validation_ready is False
    assert status.banner_level == "danger"
    assert "live trading" in status.banner_text_ko


def test_market_orders_allowed_escalates_danger_and_ready_false():
    status = _status(payload=_payload(market_orders_allowed=True))
    assert status.live_validation_ready is False
    assert status.banner_level == "danger"
    assert "시장가" in status.banner_text_ko


def test_secret_exposed_escalates_danger_and_ready_false():
    status = _status(payload=_payload(secret_exposed=True))
    assert status.live_validation_ready is False
    assert status.banner_level == "danger"
    assert "secret" in status.banner_text_ko


def test_kill_switch_engaged_warns_and_ready_false():
    status = _status(payload=_payload(kill_switch_engaged=True))
    assert status.live_validation_ready is False
    assert status.banner_level == "warning"
    assert "kill switch" in status.banner_text_ko


def test_kis_config_loaded_without_auth_warns():
    status = _status(payload=_payload(kis_authenticated=False))
    assert status.banner_level == "warning"
    assert "인증 토큰" in status.banner_text_ko


def test_kis_config_missing_ready_false():
    status = _status(payload=_payload(kis_config_loaded=False, kis_authenticated=False))
    assert status.live_validation_ready is False
    items = {item.key: item.passed for item in status.items}
    assert items["kis_config_loaded_confirmed"] is False


def test_dry_run_false_ready_false():
    status = _status(payload=_payload(kis_order_dry_run=False))
    assert status.live_validation_ready is False
    items = {item.key: item.passed for item in status.items}
    assert items["kis_dry_run_enabled_confirmed"] is False


def test_non_paper_mode_ready_false():
    status = _status(payload=_payload(mode="live"))
    assert status.live_validation_ready is False
    items = {item.key: item.passed for item in status.items}
    assert items["paper_mode_confirmed"] is False


def test_optional_limits_are_reported_when_configured():
    settings = Settings(
        symbol_allowlist=("AAPL",),
        live_validation_daily_loss_limit_usd=Decimal("25"),
        live_validation_max_orders_per_day=3,
    )
    status = _status(settings=settings)
    items = {item.key: item for item in status.items}
    assert items["daily_loss_limit_configured"].passed is True
    assert items["max_orders_per_day_configured"].passed is True
    assert "25" in items["daily_loss_limit_configured"].detail_ko
    assert "3" in items["max_orders_per_day_configured"].detail_ko


def test_symbol_allowlist_item_requires_symbols():
    status = _status(settings=Settings(symbol_allowlist=()))
    items = {item.key: item.passed for item in status.items}
    assert items["symbol_allowlist_configured"] is False


def test_manual_test_item_is_false_by_default():
    status = _status()
    items = {item.key: item.passed for item in status.items}
    assert items["recent_test_passed_manual"] is False


def test_settings_replace_variants_work_for_reporting_fields():
    settings = replace(
        Settings(symbol_allowlist=("AAPL",)),
        live_validation_daily_loss_limit_usd=Decimal("10.50"),
    )
    status = _status(settings=settings)
    items = {item.key: item for item in status.items}
    assert items["daily_loss_limit_configured"].passed is True
