from fastapi.testclient import TestClient

from app.api.server import create_app


ENV_KEYS = (
    "TRADING_MODE",
    "LIVE_TRADING_ENABLED",
    "ALLOW_MARKET_ORDERS",
    "KIS_ENV",
    "KIS_ACCOUNT_NO",
    "KIS_APP_KEY",
    "KIS_APP_SECRET",
    "KILL_SWITCH_ENGAGED",
    "KIS_ORDER_DRY_RUN",
)


def _isolated_project(monkeypatch, tmp_path):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("app.config._project_dir", lambda: tmp_path)
    (tmp_path / ".env").write_text("", encoding="utf-8")


def test_get_ops_status_returns_all_flags(monkeypatch, tmp_path):
    _isolated_project(monkeypatch, tmp_path)
    with TestClient(create_app()) as client:
        response = client.get("/ops/status")
    assert response.status_code == 200
    body = response.json()
    for key in (
        "live_trading_enabled",
        "trading_mode",
        "market_orders_allowed",
        "kis_order_dry_run",
        "kill_switch_engaged",
        "broker_type",
        "kis_config_loaded",
        "kis_authenticated",
        "kis_market_data_available",
        "kis_account_loaded",
        "kis_order_entry_ready",
        "live_validation_ready",
        "banner_level",
        "banner_text_ko",
        "secret_exposed",
    ):
        assert key in body
    assert body["secret_exposed"] is False
    assert "items" not in body


def test_get_ops_preflight_returns_checklist(monkeypatch, tmp_path):
    _isolated_project(monkeypatch, tmp_path)
    with TestClient(create_app()) as client:
        response = client.get("/ops/preflight")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert len(body["items"]) == 14
    for item in body["items"]:
        assert set(item) == {"key", "label_ko", "passed", "detail_ko"}


def test_ops_endpoints_are_get_only(monkeypatch, tmp_path):
    _isolated_project(monkeypatch, tmp_path)
    with TestClient(create_app()) as client:
        assert client.post("/ops/status").status_code == 405
        assert client.post("/ops/preflight").status_code == 405
        assert client.put("/ops/status").status_code == 405
        assert client.delete("/ops/preflight").status_code == 405


def test_ops_endpoints_do_not_expose_secrets(monkeypatch, tmp_path):
    _isolated_project(monkeypatch, tmp_path)
    forbidden = (
        "KIS_APP_KEY",
        "KIS_APP_SECRET",
        "KIS_ACCOUNT_NO",
        "app_secret",
        "access_token",
        "Bearer ",
    )
    with TestClient(create_app()) as client:
        responses = [client.get("/ops/status"), client.get("/ops/preflight")]
    for response in responses:
        assert response.status_code == 200
        for needle in forbidden:
            assert needle not in response.text


def test_routes_has_no_mutating_ops_routes():
    import pathlib

    text = (
        pathlib.Path(__file__).resolve().parents[1] / "app" / "api" / "routes.py"
    ).read_text(encoding="utf-8")
    for verb in ("post", "put", "delete", "patch"):
        prefix = '@router.' + verb + '("/ops/'
        assert prefix not in text


def test_default_banner_is_info_in_safe_paper_setup(monkeypatch, tmp_path):
    _isolated_project(monkeypatch, tmp_path)
    with TestClient(create_app()) as client:
        body = client.get("/ops/status").json()
    assert body["banner_level"] == "info"
    assert "paper / dry-run 전용" in body["banner_text_ko"]


def test_default_ready_false_without_recent_paper_activity(monkeypatch, tmp_path):
    _isolated_project(monkeypatch, tmp_path)
    with TestClient(create_app()) as client:
        body = client.get("/ops/preflight").json()
    assert body["live_validation_ready"] is False
    manual = next(item for item in body["items"] if item["key"] == "recent_test_passed_manual")
    assert manual["passed"] is False


def test_ops_preflight_after_recent_simulation_keeps_safe_flags(monkeypatch, tmp_path):
    from tests.test_paper_e2e_api import _order_payload

    _isolated_project(monkeypatch, tmp_path)
    with TestClient(create_app()) as client:
        client.post("/paper/order/simulate", json=_order_payload())
        body = client.get("/ops/preflight").json()
    keys = {item["key"]: item["passed"] for item in body["items"]}
    assert keys["paper_mode_confirmed"] is True
    assert keys["live_disabled_confirmed"] is True
    assert keys["market_orders_disabled_confirmed"] is True
    assert keys["kis_dry_run_enabled_confirmed"] is True
    assert keys["secret_exposed_false_confirmed"] is True
    assert keys["dashboard_simulation_available"] is True


def test_live_validation_ready_matches_preflight_items(monkeypatch, tmp_path):
    _isolated_project(monkeypatch, tmp_path)
    with TestClient(create_app()) as client:
        body = client.get("/ops/preflight").json()
    assert body["live_validation_ready"] is all(item["passed"] for item in body["items"])


def test_ops_secret_exposed_serialization_is_not_overwritten(monkeypatch, tmp_path):
    _isolated_project(monkeypatch, tmp_path)

    def exposed_payload(_request):
        return {
            "mode": "paper",
            "live_trading_enabled": False,
            "market_orders_allowed": False,
            "kis_order_dry_run": True,
            "kill_switch_engaged": False,
            "broker_type": "PaperBroker",
            "kis_config_loaded": True,
            "kis_authenticated": False,
            "kis_market_data_available": False,
            "kis_account_loaded": False,
            "kis_order_entry_ready": True,
            "kis_order_submission_available": False,
            "secret_exposed": True,
        }

    monkeypatch.setattr("app.api.routes.paper_status", exposed_payload)
    with TestClient(create_app()) as client:
        body = client.get("/ops/status").json()
    assert body["secret_exposed"] is True
    assert body["live_validation_ready"] is False


def test_ops_kis_order_entry_ready_uses_submission_capability(monkeypatch, tmp_path):
    _isolated_project(monkeypatch, tmp_path)
    with TestClient(create_app()) as client:
        body = client.get("/ops/status").json()
    assert body["kis_order_entry_ready"] is False
