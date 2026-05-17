from dataclasses import dataclass, field, replace

import pytest

from app.broker.kis import KisAuthClient, KisAuthError
from app.broker.kis_http import SafeKisHttpClient
from app.broker.kis_token_cache import InMemoryTokenCache


def _paper_settings(settings):
    return replace(
        settings,
        kis_env="paper",
        kis_app_key="fake-key",
        kis_app_secret="fake-secret",
        kis_api_mode="paper",
    )


def _mock_settings(settings):
    return replace(_paper_settings(settings), kis_api_mode="mock")


@dataclass
class FakeTransport:
    response: dict
    calls: list = field(default_factory=list)
    raises: Exception | None = None

    def request(self, method, url, headers, payload):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "path": url.split(":29443", 1)[-1],
                "payload": dict(payload or {}),
            }
        )
        if self.raises:
            raise self.raises
        return dict(self.response)


def _make_client(settings_obj, transport):
    cache = InMemoryTokenCache()
    http = SafeKisHttpClient(settings=settings_obj, token_cache=cache, transport=transport)
    return KisAuthClient(settings=settings_obj, http=http, token_cache=cache), cache


def test_authenticate_mock_mode_fail_closed(settings):
    s = _mock_settings(settings)
    cache = InMemoryTokenCache()
    http = SafeKisHttpClient(settings=s, token_cache=cache)
    auth = KisAuthClient(settings=s, http=http, token_cache=cache)
    with pytest.raises(KisAuthError, match="mock_mode_no_network"):
        auth.authenticate()


def test_authenticate_paper_happy_path(settings):
    s = _paper_settings(settings)
    transport = FakeTransport(
        response={
            "access_token": "fake-token-abc",
            "token_type": "Bearer",
            "expires_in": 86400,
        }
    )
    auth, _cache = _make_client(s, transport)
    auth.authenticate()
    assert auth.is_authenticated()
    assert auth.get_access_token() == "fake-token-abc"
    assert len(transport.calls) == 1
    call = transport.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/oauth2/tokenP")
    assert call["payload"]["grant_type"] == "client_credentials"
    assert call["payload"]["appkey"] == "fake-key"


def test_authenticate_rejects_missing_access_token(settings):
    s = _paper_settings(settings)
    transport = FakeTransport(response={"token_type": "Bearer", "expires_in": 86400})
    auth, _cache = _make_client(s, transport)
    with pytest.raises(KisAuthError, match="invalid_token_response"):
        auth.authenticate()


def test_authenticate_rejects_wrong_token_type(settings):
    s = _paper_settings(settings)
    transport = FakeTransport(response={"access_token": "x", "token_type": "basic", "expires_in": 86400})
    auth, _cache = _make_client(s, transport)
    with pytest.raises(KisAuthError, match="invalid_token_type"):
        auth.authenticate()


def test_authenticate_rejects_bad_expires_in(settings):
    s = _paper_settings(settings)
    transport = FakeTransport(response={"access_token": "x", "token_type": "Bearer", "expires_in": "soon"})
    auth, _cache = _make_client(s, transport)
    with pytest.raises(KisAuthError, match="invalid_expires_in"):
        auth.authenticate()


def test_authenticate_uses_cache_on_second_call(settings):
    s = _paper_settings(settings)
    transport = FakeTransport(response={"access_token": "x", "token_type": "Bearer", "expires_in": 86400})
    auth, _cache = _make_client(s, transport)
    auth.authenticate()
    auth.clear_token()
    auth.authenticate()
    assert len(transport.calls) == 1


def test_revoke_clears_local_and_cache(settings):
    s = _paper_settings(settings)
    transport = FakeTransport(response={"access_token": "x", "token_type": "Bearer", "expires_in": 86400})
    auth, cache = _make_client(s, transport)
    auth.authenticate()
    transport.response = {"code": 200, "message": "ok"}
    auth.revoke()
    assert auth.is_authenticated() is False
    assert cache.get() is None
    revoke_calls = [call for call in transport.calls if call["url"].endswith("/oauth2/revokeP")]
    assert len(revoke_calls) == 1
