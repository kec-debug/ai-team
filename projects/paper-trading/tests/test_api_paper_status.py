from fastapi.testclient import TestClient

from app.api.server import create_app


KIS_ENV_KEYS = (
    "KIS_ENV",
    "KIS_ACCOUNT_NO",
    "KIS_APP_KEY",
    "KIS_APP_SECRET",
)


def _clear_kis_env(monkeypatch):
    for key in KIS_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_healthz():
    with TestClient(create_app()) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_paper_status_safety_flags():
    with TestClient(create_app()) as client:
        response = client.get("/paper/status")
    assert response.status_code == 200
    body = response.json()
    assert body["live_enabled"] is False
    assert "premarket_gap_volume_breakout" in body["strategies"]
    assert body["safety"]["strategy_emits_non_executable_only"] is True


def test_paper_status_kis_metadata_fields(monkeypatch):
    _clear_kis_env(monkeypatch)
    with TestClient(create_app()) as client:
        response = client.get("/paper/status")
    assert response.status_code == 200
    body = response.json()
    # mvp-006-1 fields
    assert body["broker_type"] == "PaperBroker"
    assert body["broker_environment"] == "paper"
    assert body["live_trading_enabled"] is False
    assert body["market_orders_allowed"] is False
    assert isinstance(body["kis_config_loaded"], bool)
    assert body["kis_authenticated"] is False
    assert body["kis_account_loaded"] is False
    assert body["kis_market_data_available"] is False
    assert body["last_broker_error"] is None
    assert body["account_no_masked"] == "<unset>"
    assert body["secret_exposed"] is False
    assert "kis_" + "secret_exposed" not in body
    assert isinstance(body["configured_brokers"], list)
    # Credentials must never appear in the response body.
    body_text = response.text
    for needle in ("KIS_APP_KEY", "KIS_APP_SECRET", "KIS_ACCOUNT_NO"):
        assert needle not in body_text


def test_paper_status_with_kis_config_masks_account(monkeypatch):
    monkeypatch.setenv("TRADING_MODE", "paper")
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "false")
    monkeypatch.setenv("ALLOW_MARKET_ORDERS", "false")
    monkeypatch.setenv("KIS_ENV", "paper")
    monkeypatch.setenv("KIS_ACCOUNT_NO", "12345678")
    monkeypatch.setenv("KIS_APP_KEY", "fake-key")
    monkeypatch.setenv("KIS_APP_SECRET", "fake-secret")

    with TestClient(create_app()) as client:
        response = client.get("/paper/status")

    assert response.status_code == 200
    body = response.json()
    assert body["kis_config_loaded"] is True
    assert body["configured_brokers"] == ["KisBroker"]
    assert body["kis_authenticated"] is False
    assert body["kis_account_loaded"] is False
    assert body["kis_market_data_available"] is False
    assert body["last_broker_error"] is None
    assert body["account_no_masked"] == "***5678"
    assert body["secret_exposed"] is False

    body_text = response.text
    for needle in ("12345678", "fake-key", "fake-secret", "KIS_APP_KEY", "KIS_APP_SECRET"):
        assert needle not in body_text
