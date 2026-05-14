import pytest

from app.config import load_settings


def test_load_settings_defaults_to_paper(monkeypatch):
    monkeypatch.delenv("TRADING_MODE", raising=False)
    monkeypatch.delenv("LIVE_TRADING_ENABLED", raising=False)
    settings = load_settings()
    assert settings.trading_mode.value == "paper"
    assert settings.live_trading_enabled is False


def test_load_settings_rejects_live_mode(monkeypatch):
    monkeypatch.setenv("TRADING_MODE", "live")
    with pytest.raises(ValueError, match="Phase 1 only supports paper trading"):
        load_settings()


def test_load_settings_rejects_live_enabled(monkeypatch):
    monkeypatch.setenv("TRADING_MODE", "paper")
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "true")
    with pytest.raises(ValueError, match="Live trading is disabled"):
        load_settings()
