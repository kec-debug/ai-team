from dataclasses import replace

import pytest

from app.broker.kis import KisAuthError, KisConfigError, KisHttpError
from app.broker.kis_http import (
    ALLOWED_PATHS_API_AUTH_001,
    MockTransport,
    SafeKisHttpClient,
    UrllibTransport,
)
from app.broker.kis_token_cache import InMemoryTokenCache


def _paper_settings(settings):
    return replace(
        settings,
        kis_env="paper",
        kis_app_key="fake-key",
        kis_app_secret="fake-secret",
        kis_api_mode="paper",
    )


def test_mock_transport_blocks_network():
    transport = MockTransport()
    with pytest.raises(KisAuthError, match="mock_mode_no_network"):
        transport.request("POST", "https://openapivts.koreainvestment.com:29443/oauth2/tokenP", {}, {"a": 1})


def test_urllib_transport_rejects_disallowed_host():
    transport = UrllibTransport()
    with pytest.raises(KisAuthError, match="disallowed_host"):
        transport.request("POST", "https://evil.example.com/oauth2/tokenP", {}, {})


def test_safe_client_rejects_unknown_path(settings):
    client = SafeKisHttpClient(
        settings=_paper_settings(settings),
        token_cache=InMemoryTokenCache(),
        transport=MockTransport(),
    )
    with pytest.raises(KisHttpError, match="path_not_allowed_by_api_auth_001"):
        client.request("POST", "/uapi/some/other/path", {}, {})


def test_safe_client_blocks_live_mode(settings):
    s = replace(_paper_settings(settings), kis_api_mode="live")
    with pytest.raises(KisConfigError, match="live_mode_not_supported_yet"):
        SafeKisHttpClient(settings=s, token_cache=InMemoryTokenCache())


def test_allowed_paths_are_just_two():
    assert ALLOWED_PATHS_API_AUTH_001 == frozenset({"/oauth2/tokenP", "/oauth2/revokeP"})
