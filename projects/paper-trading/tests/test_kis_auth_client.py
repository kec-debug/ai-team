from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from app.broker.kis import KisAuthClient, KisConfigError


def _settings(settings):
    return replace(
        settings,
        kis_env="paper",
        kis_account_no="12345678",
        kis_app_key="fake-key",
        kis_app_secret="fake-secret",
    )


def test_auth_client_requires_credentials(settings):
    with pytest.raises(KisConfigError):
        KisAuthClient(replace(_settings(settings), kis_app_key=None))
    with pytest.raises(KisConfigError):
        KisAuthClient(replace(_settings(settings), kis_app_secret=None))


def test_auth_client_initial_state_not_authenticated(settings):
    auth = KisAuthClient(_settings(settings))
    assert auth.is_authenticated() is False
    assert auth.get_access_token() is None
    assert auth.last_error is None


def test_auth_client_token_state_machine(settings):
    auth = KisAuthClient(_settings(settings))
    auth._access_token = "tok-FAKE"  # type: ignore[attr-defined]
    auth._expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)  # type: ignore[attr-defined]
    assert auth.is_authenticated() is True
    assert auth.get_access_token() == "tok-FAKE"

    auth.clear_token()
    assert auth.is_authenticated() is False
    assert auth.get_access_token() is None


def test_auth_client_expired_token_is_not_returned(settings):
    auth = KisAuthClient(_settings(settings))
    auth._access_token = "tok-FAKE"  # type: ignore[attr-defined]
    auth._expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)  # type: ignore[attr-defined]
    assert auth.is_authenticated() is False
    assert auth.get_access_token() is None


def test_auth_client_network_methods_fail_closed(settings):
    auth = KisAuthClient(_settings(settings))
    with pytest.raises(NotImplementedError, match="official documentation"):
        auth.authenticate()
    with pytest.raises(NotImplementedError, match="official documentation"):
        auth.refresh_token()


def test_auth_client_repr_masks_secrets_and_token(settings):
    auth = KisAuthClient(_settings(settings))
    auth._access_token = "tok-FAKE"  # type: ignore[attr-defined]
    text = repr(auth)
    assert "fake-key" not in text
    assert "fake-secret" not in text
    assert "tok-FAKE" not in text
    assert "token=<set>" in text
