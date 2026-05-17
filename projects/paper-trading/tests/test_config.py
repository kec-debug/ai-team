import pytest

from app.config import load_settings


def test_load_settings_defaults_to_paper(monkeypatch):
    monkeypatch.delenv("TRADING_MODE", raising=False)
    monkeypatch.delenv("LIVE_TRADING_ENABLED", raising=False)
    monkeypatch.delenv("KIS_ORDER_DRY_RUN", raising=False)
    settings = load_settings()
    assert settings.trading_mode.value == "paper"
    assert settings.live_trading_enabled is False
    assert settings.kis_order_dry_run is True


def test_load_settings_rejects_live_mode(monkeypatch):
    monkeypatch.setenv("TRADING_MODE", "live")
    with pytest.raises(ValueError, match="Phase 1 only supports paper trading"):
        load_settings()


def test_load_settings_rejects_live_enabled(monkeypatch):
    monkeypatch.setenv("TRADING_MODE", "paper")
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "true")
    with pytest.raises(ValueError, match="Live trading is disabled"):
        load_settings()


def test_load_settings_reads_kis_order_dry_run(monkeypatch):
    monkeypatch.setenv("TRADING_MODE", "paper")
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "false")
    monkeypatch.setenv("KIS_ORDER_DRY_RUN", "false")
    settings = load_settings()
    assert settings.kis_order_dry_run is False
