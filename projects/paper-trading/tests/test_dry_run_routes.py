import shutil
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.server import create_app


PROJECT_DIR = Path(__file__).resolve().parents[1]
TEST_REPORTS_DIR = PROJECT_DIR / "reports" / "test_runs"


def _clean_reports():
    shutil.rmtree(TEST_REPORTS_DIR, ignore_errors=True)


def _prepare_env(monkeypatch):
    monkeypatch.setenv("TRADING_MODE", "paper")
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "false")
    monkeypatch.setenv("ALLOW_MARKET_ORDERS", "false")
    monkeypatch.setenv("KILL_SWITCH_ENGAGED", "false")
    monkeypatch.setenv("DRY_RUN_REPORTS_DIR", "reports/test_runs")
    monkeypatch.delenv("KIS_ACCOUNT_NO", raising=False)
    monkeypatch.delenv("KIS_APP_KEY", raising=False)
    monkeypatch.delenv("KIS_APP_SECRET", raising=False)
    _clean_reports()


def test_dry_run_start_then_status_then_stop(monkeypatch):
    _prepare_env(monkeypatch)
    try:
        with TestClient(create_app()) as client:
            started = client.post("/paper/dry-run/start")
            assert started.status_code == 200
            assert started.json()["state"] == "running"

            status = client.get("/paper/dry-run/status")
            assert status.status_code == 200
            assert status.json()["state"] == "running"

            stopped = client.post("/paper/dry-run/stop")
            assert stopped.status_code == 200
            assert stopped.json()["state"] == "stopped"
    finally:
        _clean_reports()


def test_dry_run_start_twice_returns_409(monkeypatch):
    _prepare_env(monkeypatch)
    try:
        with TestClient(create_app()) as client:
            assert client.post("/paper/dry-run/start").status_code == 200
            assert client.post("/paper/dry-run/start").status_code == 409
    finally:
        _clean_reports()


def test_dry_run_stop_when_not_running_returns_409(monkeypatch):
    _prepare_env(monkeypatch)
    try:
        with TestClient(create_app()) as client:
            assert client.post("/paper/dry-run/stop").status_code == 409
    finally:
        _clean_reports()


def test_dry_run_tick_when_not_running_returns_409(monkeypatch):
    _prepare_env(monkeypatch)
    try:
        with TestClient(create_app()) as client:
            assert client.post("/paper/dry-run/tick", json={"snapshots": []}).status_code == 409
    finally:
        _clean_reports()


def test_dry_run_tick_with_snapshot_evaluates(monkeypatch, make_snapshot):
    _prepare_env(monkeypatch)
    try:
        with TestClient(create_app()) as client:
            client.post("/paper/dry-run/start")
            response = client.post(
                "/paper/dry-run/tick",
                json={"snapshots": [make_snapshot().model_dump(mode="json")]},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["tick"]["snapshots_evaluated"] == 1
            assert body["summary"]["counters"]["ticks_total"] == 1
    finally:
        _clean_reports()


def test_dry_run_status_no_credentials_in_response(monkeypatch):
    _prepare_env(monkeypatch)
    monkeypatch.setenv("KIS_ACCOUNT_NO", "12345678")
    monkeypatch.setenv("KIS_APP_KEY", "fake-key")
    monkeypatch.setenv("KIS_APP_SECRET", "fake-secret")
    try:
        with TestClient(create_app()) as client:
            client.post("/paper/dry-run/start")
            response = client.get("/paper/dry-run/status")
            assert response.status_code == 200
            for needle in ("12345678", "fake-key", "fake-secret", "KIS_APP_KEY", "KIS_APP_SECRET"):
                assert needle not in response.text
    finally:
        _clean_reports()


def test_dry_run_kill_switch_blocks_tick(monkeypatch, make_snapshot):
    _prepare_env(monkeypatch)
    monkeypatch.setenv("KILL_SWITCH_ENGAGED", "true")
    try:
        with TestClient(create_app()) as client:
            client.post("/paper/dry-run/start")
            response = client.post(
                "/paper/dry-run/tick",
                json={"snapshots": [make_snapshot(current_price=Decimal("106")).model_dump(mode="json")]},
            )
            assert response.status_code == 200
            assert response.json()["tick"]["status"] == "blocked_kill_switch"
    finally:
        _clean_reports()


def test_paper_status_includes_dry_run_running(monkeypatch):
    _prepare_env(monkeypatch)
    try:
        with TestClient(create_app()) as client:
            response = client.get("/paper/status")
            assert response.status_code == 200
            body = response.json()
            assert "dry_run_running" in body
            assert body["dry_run_running"] is False
    finally:
        _clean_reports()
