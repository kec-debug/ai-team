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
    assert "모의거래 대시보드" in response.text


def test_dashboard_safety_banner_present():
    text = _html()
    for marker in ("모의거래 전용", "실거래 꺼짐", "실제 주문 불가능", "실제 브로커 호출 없음"):
        assert marker in text


def test_dashboard_has_required_sections_and_buttons():
    text = _html()
    for marker in (
        "안전 상태",
        "현재 모드",
        "실거래 상태",
        "실제 주문 가능 여부",
        "수동 모의 주문",
        "바로 모의테스트 해보기",
        "예시 모의 주문 실행",
        "계좌 / 손익",
        "시작 현금",
        "현재 현금",
        "통화별 현금",
        "통화별 실현 손익",
        "통화별 평가 손익",
        "보유 종목",
        "보유 종목 수",
        "주문 내역",
        "체결 내역",
        "매수",
        "매도",
        "실현 손익",
        "평가 손익",
        "최근 거절 주문",
        "Paper Engine 상태",
        "Paper Engine 활성",
        "Journal 활성",
        "Persistent 로그 경로",
        "마지막 체결 시각",
        "마지막 거래 시각",
        "KIS 상태",
        "Dry-run 상태",
        "최신 리포트 해석",
        "한글 해석",
        "다음 행동 제안",
        "상태 새로고침",
        "모의 주문 실행",
        "Dry-run 시작",
        "Tick 1회 실행",
        "Dry-run 중지",
        "리포트 분석",
        "최신 리포트 보기",
        "Overview",
        "Paper Training",
        "Agent Research",
        "Strategy Lab",
        "Orders / Fills",
        "Portfolio",
        "Reports",
        "Live Validation",
        "Risk / Ops",
        "Training 시작",
        "Agent 분석 실행",
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
        "ticks_total",
        "candidates_seen",
        "dry_run_orders_created",
    )
    for marker in forbidden:
        assert marker not in text


def test_dashboard_endpoint_urls_are_whitelisted():
    text = _html()
    expected = {
        "/paper/status",
        "/paper/account",
        "/paper/positions",
        "/paper/fills",
        "/paper/orders",
        "/paper/order/simulate",
        "/paper/engine/status",
        "/paper/report/summary",
        "/paper/training/status",
        "/paper/training/start",
        "/paper/training/stop",
        "/paper/training/tick",
        "/paper/training/runs",
        "/paper/dry-run/status",
        "/paper/dry-run/start",
        "/paper/dry-run/stop",
        "/paper/dry-run/tick",
        "/reports/latest",
        "/reports/dry-run/analyze",
        "/reports/dry-run/latest",
    }
    found = set(re.findall(r'"(/(?:paper|reports)/[^"]+)"', text))
    assert found == expected


def test_dashboard_manual_order_form_has_no_action():
    text = _html().lower()
    assert '<form id="paper-order-form"' in text
    assert "action=" not in text


def test_dashboard_has_no_paper_run_endpoint():
    assert "/paper/run" not in _html()


def test_dashboard_has_no_external_assets_or_frameworks():
    text = _html().lower()
    assert "script src=" not in text
    assert "stylesheet" not in text
    assert "https://" not in text
    assert "http://" not in text


def test_dashboard_has_live_validation_readiness_section():
    response = TestClient(create_app()).get("/dashboard")
    assert response.status_code == 200
    assert "Live Validation 준비 상태" in response.text


def test_dashboard_has_preflight_checklist_section():
    response = TestClient(create_app()).get("/dashboard")
    assert response.status_code == 200
    assert "Preflight Checklist" in response.text


def test_dashboard_has_live_toggle_and_agent_visual_markers():
    text = _html()
    for marker in (
        "Live Validation 켜기",
        "Live Validation 끄기",
        "실전 주문 준비 요청",
        "실전 주문 준비 해제",
        "KIS 인증 확인",
        "KIS 계좌 동기화",
        "분석 종목 수",
        "주요 종목",
        "분석 후보 흐름",
        "매물대·눌림목·큰손 흐름",
        "agent-symbol-chart",
        "KIS API 모드",
        "KIS 연결 해석",
        'id="btn-live-validation-arm"',
        'id="btn-live-validation-disarm"',
        'id="btn-live-order-entry-request"',
    ):
        assert marker in text


def test_dashboard_has_safety_banner_text():
    response = TestClient(create_app()).get("/dashboard")
    assert response.status_code == 200
    assert "paper / dry-run 전용" in response.text
    assert "live trading 은 비활성화되어 있으며" in response.text


def test_dashboard_has_no_live_arm_or_enable_buttons():
    response = TestClient(create_app()).get("/dashboard")
    assert response.status_code == 200
    forbidden_ids = (
        'id="btn-arm-live"',
        'id="btn-enable-live"',
        'id="btn-disable-dry-run"',
        'id="btn-allow-market"',
        'id="btn-toggle-kill-switch"',
    )
    for marker in forbidden_ids:
        assert marker not in response.text
