from dataclasses import replace

import pytest

from app.broker.alpaca_paper import AlpacaPaperBroker
from app.config import Settings


def test_alpaca_stub_fails_without_url():
    with pytest.raises(RuntimeError):
        AlpacaPaperBroker(Settings())


def test_alpaca_stub_requires_https(settings):
    with pytest.raises(RuntimeError):
        AlpacaPaperBroker(replace(settings, alpaca_paper_api_base="http://example.invalid"))


def test_alpaca_stub_methods_not_implemented(settings):
    broker = AlpacaPaperBroker(
        replace(
            settings,
            alpaca_paper_api_base="https://example.invalid",
            alpaca_paper_key_id="placeholder",
            alpaca_paper_secret_key="placeholder",
        )
    )
    with pytest.raises(NotImplementedError):
        broker.open_orders()
