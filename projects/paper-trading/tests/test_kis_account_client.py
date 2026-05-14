from dataclasses import replace

import pytest

from app.broker.kis import KisAccountClient, KisAuthClient, KisConfigError


def _settings(settings, account_no="12345678"):
    return replace(
        settings,
        kis_env="paper",
        kis_account_no=account_no,
        kis_app_key="fake-key",
        kis_app_secret="fake-secret",
    )


def _auth(settings):
    return KisAuthClient(_settings(settings))


def test_account_client_requires_account_no(settings):
    with pytest.raises(KisConfigError):
        KisAccountClient(replace(_settings(settings), kis_account_no=None), _auth(settings))


@pytest.mark.parametrize(
    ("account_no", "masked"),
    [
        ("12345678", "***5678"),
        ("1234", "***"),
        ("12", "***"),
    ],
)
def test_account_client_masks_account_no(settings, account_no, masked):
    account = KisAccountClient(_settings(settings, account_no), _auth(settings))
    assert account.masked_account_no() == masked


def test_account_client_initial_state_not_loaded(settings):
    account = KisAccountClient(_settings(settings), _auth(settings))
    assert account.is_loaded() is False
    assert account.last_error is None


def test_account_client_methods_fail_closed(settings):
    account = KisAccountClient(_settings(settings), _auth(settings))
    for method in ("get_account", "get_positions", "get_cash_balance"):
        with pytest.raises(NotImplementedError, match="official documentation"):
            getattr(account, method)()


def test_account_client_repr_masks_raw_account(settings):
    account = KisAccountClient(_settings(settings, "12345678"), _auth(settings))
    text = repr(account)
    assert "12345678" not in text
    assert "***5678" in text
