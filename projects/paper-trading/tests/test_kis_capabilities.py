from dataclasses import replace

from app.broker.kis import KisBroker


def _settings(settings):
    return replace(
        settings,
        kis_env="paper",
        kis_account_no="12345678",
        kis_app_key="fake-key",
        kis_app_secret="fake-secret",
    )


def test_kis_capabilities_fail_closed(settings):
    broker = KisBroker(_settings(settings))

    assert broker.capabilities() == {
        "submission": False,
        "cancel": False,
        "replace": False,
        "open_orders": False,
        "fills": False,
        "order_status": False,
    }
    assert broker.healthcheck()["capabilities"] == broker.capabilities()
