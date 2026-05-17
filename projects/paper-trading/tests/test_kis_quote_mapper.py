import pytest

from app.broker.kis_quote_mapper import kis_raw_quote_to_domain


def test_mapper_raises_not_implemented_with_valid_input():
    with pytest.raises(NotImplementedError, match="official documentation"):
        kis_raw_quote_to_domain({"any": "shape"}, symbol="AAPL")


def test_mapper_rejects_none_raw():
    with pytest.raises(ValueError, match="None"):
        kis_raw_quote_to_domain(None, symbol="AAPL")


def test_mapper_rejects_empty_symbol():
    with pytest.raises(ValueError, match="symbol"):
        kis_raw_quote_to_domain({"any": "shape"}, symbol="")
