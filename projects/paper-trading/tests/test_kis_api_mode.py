import pytest

from app.broker.kis_http import KisApiMode


def test_default_is_mock():
    assert KisApiMode.parse(None) is KisApiMode.MOCK
    assert KisApiMode.parse("") is KisApiMode.MOCK


def test_valid_modes():
    assert KisApiMode.parse("mock") is KisApiMode.MOCK
    assert KisApiMode.parse("paper") is KisApiMode.PAPER
    assert KisApiMode.parse("live") is KisApiMode.LIVE


def test_invalid_mode_raises():
    with pytest.raises(ValueError):
        KisApiMode.parse("production")
