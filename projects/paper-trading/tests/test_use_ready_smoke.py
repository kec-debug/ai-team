from fastapi.testclient import TestClient

from app.api.server import create_app


def test_smoke_healthz():
    with TestClient(create_app()) as client:
        assert client.get("/healthz").json() == {"ok": True}


def test_smoke_paper_status_keys_present():
    with TestClient(create_app()) as client:
        body = client.get("/paper/status").json()
    for key in (
        "mode",
        "live_enabled",
        "market_orders_allowed",
        "kis_order_dry_run",
        "secret_exposed",
        "kill_switch_engaged",
    ):
        assert key in body


def test_smoke_ops_status_keys_present():
    with TestClient(create_app()) as client:
        body = client.get("/ops/status").json()
    for key in (
        "live_trading_enabled",
        "trading_mode",
        "live_validation_ready",
        "banner_level",
        "banner_text_ko",
        "secret_exposed",
    ):
        assert key in body


def test_smoke_ops_preflight_includes_checklist():
    with TestClient(create_app()) as client:
        body = client.get("/ops/preflight").json()
    assert "items" in body
    assert len(body["items"]) == 14


def test_smoke_dry_run_lifecycle():
    with TestClient(create_app()) as client:
        assert client.post("/paper/dry-run/start").status_code == 200
        try:
            assert client.post("/paper/dry-run/tick", json={"snapshots": []}).status_code == 200
            status = client.get("/paper/dry-run/status").json()
            assert status["state"] == "running"
        finally:
            assert client.post("/paper/dry-run/stop").status_code == 200


def test_smoke_paper_order_simulate_demo():
    payload = {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 1,
        "order_type": "limit",
        "limit_price": "100",
        "stop_price": None,
        "mock_bid": "99",
        "mock_ask": "100",
        "mock_last": "100",
        "mock_volume": 100,
        "currency": "USD",
    }
    with TestClient(create_app()) as client:
        body = client.post("/paper/order/simulate", json=payload).json()
    assert body["accepted"] is True
    assert body["safety_flags"]["mode"] == "paper"
    assert body["safety_flags"]["live_trading_enabled"] is False


def test_smoke_reports_latest_after_analyze():
    with TestClient(create_app()) as client:
        client.post("/paper/dry-run/start")
        try:
            client.post("/paper/dry-run/tick", json={"snapshots": []})
        finally:
            client.post("/paper/dry-run/stop")
        analyze = client.post("/reports/dry-run/analyze", json={"run_dir": None})
    assert analyze.status_code in (200, 404)


def test_smoke_no_secrets_in_combined_responses():
    forbidden = (
        "KIS_APP_KEY",
        "KIS_APP_SECRET",
        "KIS_ACCOUNT_NO",
        "app_secret",
        "access_token",
        "Bearer ",
    )
    with TestClient(create_app()) as client:
        endpoints = [
            "/paper/status",
            "/ops/status",
            "/ops/preflight",
            "/paper/account",
            "/paper/positions",
            "/paper/fills",
            "/paper/engine/status",
        ]
        for path in endpoints:
            text = client.get(path).text
            for needle in forbidden:
                assert needle not in text, f"{path} leaked {needle!r}"


def test_smoke_ops_routes_are_get_only():
    with TestClient(create_app()) as client:
        for verb in ("post", "put", "delete"):
            fn = getattr(client, verb)
            assert fn("/ops/status").status_code == 405
            assert fn("/ops/preflight").status_code == 405


def test_smoke_dashboard_loads_html():
    with TestClient(create_app()) as client:
        response = client.get("/dashboard")
    assert response.status_code == 200
    assert "<html" in response.text or "<!doctype" in response.text.lower()
    assert "원본 데이터 보기" in response.text
