import os
import pytest

from app.config import Settings, load_settings


KIS_ENV_KEYS = (
    "TRADING_MODE",
    "LIVE_TRADING_ENABLED",
    "ALLOW_MARKET_ORDERS",
    "KIS_ENV",
    "KIS_ACCOUNT_NO",
    "KIS_APP_KEY",
    "KIS_APP_SECRET",
)


def _clear_kis_env(monkeypatch):
    for key in KIS_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_load_settings_default_paper_and_live_disabled(monkeypatch):
    _clear_kis_env(monkeypatch)
    monkeypatch.setenv("TRADING_MODE", "paper")
    s = load_settings()
    assert s.live_trading_enabled is False
    assert s.allow_market_orders is False
    assert s.kis_env is None
    assert s.kis_account_no is None
    assert s.kis_app_key is None
    assert s.kis_app_secret is None


def test_load_settings_reads_kis_env_vars(monkeypatch):
    _clear_kis_env(monkeypatch)
    monkeypatch.setenv("TRADING_MODE", "paper")
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "false")
    monkeypatch.setenv("ALLOW_MARKET_ORDERS", "false")
    monkeypatch.setenv("KIS_ENV", "paper")
    monkeypatch.setenv("KIS_ACCOUNT_NO", "fake-account-1")
    monkeypatch.setenv("KIS_APP_KEY", "fake-app-key")
    monkeypatch.setenv("KIS_APP_SECRET", "fake-app-secret")
    s = load_settings()
    assert s.kis_env == "paper"
    assert s.kis_account_no == "fake-account-1"
    assert s.kis_app_key == "fake-app-key"
    assert s.kis_app_secret == "fake-app-secret"


def test_settings_repr_does_not_expose_secrets(monkeypatch):
    _clear_kis_env(monkeypatch)
    monkeypatch.setenv("TRADING_MODE", "paper")
    monkeypatch.setenv("KIS_ENV", "paper")
    monkeypatch.setenv("KIS_ACCOUNT_NO", "fake-account-XYZ")
    monkeypatch.setenv("KIS_APP_KEY", "fake-app-key-XYZ")
    monkeypatch.setenv("KIS_APP_SECRET", "fake-app-secret-XYZ")
    s = load_settings()
    text = repr(s)
    assert "fake-app-secret-XYZ" not in text
    assert "fake-app-key-XYZ" not in text
    assert "fake-account-XYZ" not in text


def test_allow_market_orders_true_is_rejected(monkeypatch):
    _clear_kis_env(monkeypatch)
    monkeypatch.setenv("TRADING_MODE", "paper")
    monkeypatch.setenv("ALLOW_MARKET_ORDERS", "true")
    with pytest.raises(ValueError, match="ALLOW_MARKET_ORDERS"):
        load_settings()


def test_env_example_contains_no_real_secrets():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, ".env.example"), "r", encoding="utf-8") as f:
        content = f.read()
    # No realistic key prefixes should appear in .env.example.
    for forbidden in ("PSNFD", "PKID", "AKIA", "sk-", "ghp_"):
        assert forbidden not in content
    # Known placeholder pattern must be present.
    assert "your_kis_app_key" in content
    assert "your_kis_app_secret" in content
