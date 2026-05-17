import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.server import create_app


DASHBOARD_PATH = Path(__file__).resolve().parents[1] / "app" / "static" / "dashboard.html"


def _html() -> str:
    return DASHBOARD_PATH.read_text(encoding="utf-8")


def test_dashboard_returns_html():
    with TestClient(create_app()) as client:
        response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Paper Trading Dashboard" in response.text


def test_dashboard_safety_banner_present():
    text = _html()
    for marker in ("paper / dry-run only", "live trading disabled", "market orders disabled", "no real orders"):
        assert marker in text


def test_dashboard_has_required_sections_and_buttons():
    text = _html()
    for marker in (
        "Paper trading 상태",
        "KIS 상태",
        "Dry-run 상태",
        "최신 리포트",
        "상태 새로고침",
        "Dry-run 시작",
        "Tick 1회 실행",
        "Dry-run 중지",
        "리포트 분석",
        "최신 리포트 보기",
    ):
        assert marker in text


def test_dashboard_has_no_forbidden_strings():
    text = _html()
    forbidden = (
        "KIS_APP_KEY",
        "KIS_APP_SECRET",
        "KIS_ACCOUNT_NO",
        "Enable live trading",
        "live trading 활성화",
        "Allow market orders",
        "Submit real order",
        "Place real order",
    )
    for marker in forbidden:
        assert marker not in text


def test_dashboard_endpoint_urls_are_whitelisted():
    text = _html()
    expected = {
        "/paper/status",
        "/paper/dry-run/status",
        "/paper/dry-run/start",
        "/paper/dry-run/stop",
        "/paper/dry-run/tick",
        "/reports/dry-run/analyze",
        "/reports/dry-run/latest",
    }
    found = set(re.findall(r'"(/(?:paper|reports)/[^"]+)"', text))
    assert found == expected


def test_dashboard_does_not_include_form_action():
    assert "<form" not in _html().lower()


def test_dashboard_has_no_paper_run_endpoint():
    assert "/paper/run" not in _html()


def test_dashboard_has_no_external_assets_or_frameworks():
    text = _html().lower()
    assert "script src=" not in text
    assert "stylesheet" not in text
    assert "https://" not in text
    assert "http://" not in text
