from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

from app.broker.kis import KisOrderResponse, sanitize_kis_response
from app.domain.enums import Side


def _settings(settings):
    return replace(
        settings,
        kis_env="paper",
        kis_account_no="12345678",
        kis_app_key="fake-key",
        kis_app_secret="fake-secret",
    )


def test_kis_order_response_fields_are_internal_and_sanitized(settings):
    response = KisOrderResponse(
        internal_order_id="oms-42",
        broker_order_id=None,
        broker="KisBroker",
        status="rejected",
        submitted_at=datetime.now(timezone.utc),
        symbol="AAPL",
        side=Side.BUY,
        quantity=10,
        limit_price=Decimal("100"),
        raw_response_sanitized=sanitize_kis_response(
            {"account_no": "12345678", "message": "blocked"},
            _settings(settings),
        ),
    )

    assert response.internal_order_id == "oms-42"
    assert response.raw_response_sanitized["account_no"] == "<redacted>"
    assert "12345678" not in repr(response)


def test_sanitize_kis_response_redacts_sensitive_keys(settings):
    sanitized = sanitize_kis_response(
        {
            "appKey": "visible-by-key",
            "app_secret": "visible-by-key",
            "accountNo": "visible-by-key",
            "access_token": "visible-by-key",
            "Authorization": "visible-by-key",
            "tr_key": "visible-by-key",
        },
        _settings(settings),
    )

    assert set(sanitized.values()) == {"<redacted>"}


def test_sanitize_kis_response_redacts_sensitive_values_recursively(settings):
    sanitized = sanitize_kis_response(
        {
            "outer": {
                "safe": "ok",
                "key_value": "fake-key",
                "items": [{"secret_value": "fake-secret"}, "12345678"],
            }
        },
        _settings(settings),
    )

    assert sanitized["outer"]["safe"] == "ok"
    assert sanitized["outer"]["key_value"] == "<redacted>"
    assert sanitized["outer"]["items"][0]["secret_value"] == "<redacted>"
    assert sanitized["outer"]["items"][1] == "<redacted>"


def test_sanitize_kis_response_handles_none_and_non_dict(settings):
    assert sanitize_kis_response(None, _settings(settings)) == {}
    assert sanitize_kis_response("not-a-dict", _settings(settings)) == {}
