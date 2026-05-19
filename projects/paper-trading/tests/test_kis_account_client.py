import json
from dataclasses import replace
from decimal import Decimal
from typing import Any

import pytest

from app.broker.kis import (
    KIS_BALANCE_MAX_PAGES,
    KIS_OVERSEAS_BALANCE_TR_ID_PAPER,
    KisAccountClient,
    KisAuthClient,
    KisAuthError,
    KisBroker,
    KisConfigError,
    KisDataUnavailableError,
    KisPosition,
    UrllibAccountTransport,
    _split_kis_account_no,
)


def _settings(settings, **overrides):
    data = {
        "kis_env": "paper",
        "kis_account_no": "12345678-01",
        "kis_app_key": "fake-key-XYZ",
        "kis_app_secret": "fake-secret-XYZ",
        "kis_api_mode": "paper",
    }
    data.update(overrides)
    return replace(settings, **data)


class FakeAccountTransport:
    def __init__(self, pages: list[dict[str, Any]] | None = None, exc: Exception | None = None):
        self._pages = list(pages or [])
        self._exc = exc
        self.calls: list[dict[str, Any]] = []

    def get_balance(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc
        if not self._pages:
            raise AssertionError("FakeAccountTransport exhausted")
        return self._pages.pop(0)


class FakeAuth:
    def is_authenticated(self) -> bool:
        return True

    def get_access_token(self) -> str:
        return "fake-access-token"


def _auth(settings, *, token: bool = True) -> KisAuthClient:
    auth = KisAuthClient(settings)
    if token:
        auth._store_token("fake-access-token", 120)
    return auth


def _client(settings, *, pages: list[dict[str, Any]] | None = None, token: bool = True) -> KisAccountClient:
    fake = FakeAccountTransport(pages or [{"rt_cd": "0", "output1": [], "output2": {}}])
    return KisAccountClient(settings, _auth(settings, token=token), transport=fake)


def _transport_kwargs(**overrides):
    data = {
        "base_url": "https://openapivts.koreainvestment.com:29443",
        "access_token": "fake-access-token",
        "app_key": "fake-key-XYZ",
        "app_secret": "fake-secret-XYZ",
        "tr_id": KIS_OVERSEAS_BALANCE_TR_ID_PAPER,
        "cano": "12345678",
        "acnt_prdt_cd": "01",
        "ovrs_excg_cd": "NASD",
        "tr_crcy_cd": "USD",
        "ctx_area_fk200": "",
        "ctx_area_nk200": "",
        "tr_cont": "",
    }
    data.update(overrides)
    return data


def test_split_kis_account_no_accepts_dashed_and_plain():
    assert _split_kis_account_no("12345678-01") == ("12345678", "01")
    assert _split_kis_account_no("1234567801") == ("12345678", "01")


def test_split_kis_account_no_rejects_short_and_nondigit():
    with pytest.raises(KisConfigError, match="invalid_kis_account_no_format"):
        _split_kis_account_no("12345678")
    with pytest.raises(KisConfigError, match="invalid_kis_account_no_format"):
        _split_kis_account_no("12345678-AA")


def test_get_account_requires_authentication(settings):
    client = _client(_settings(settings), token=False)
    with pytest.raises(KisAuthError, match="KIS authentication required"):
        client.get_account()


def test_get_account_blocks_live_trading_enabled(settings):
    client = _client(_settings(settings, live_trading_enabled=True))
    with pytest.raises(KisAuthError, match="live_trading_enabled"):
        client.get_account()


def test_get_account_blocks_non_paper_kis_env(settings):
    configured = _settings(settings, kis_env="live")
    client = KisAccountClient(configured, FakeAuth(), transport=FakeAccountTransport())
    with pytest.raises(KisAuthError, match="kis_env_not_paper"):
        client.get_account()


def test_get_account_blocks_kill_switch(settings):
    client = _client(_settings(settings, kill_switch_engaged=True))
    with pytest.raises(KisAuthError, match="kill_switch_engaged"):
        client.get_account()


def test_get_account_mock_mode_fails_closed(settings):
    configured = _settings(settings, kis_api_mode="mock")
    client = KisAccountClient(configured, _auth(configured))
    with pytest.raises(KisDataUnavailableError, match="mock_mode_no_network"):
        client.get_account()


def test_get_account_single_page_happy(settings):
    page = {
        "rt_cd": "0",
        "output1": [{"ovrs_pdno": "AAPL", "ovrs_cblc_qty": "2"}],
        "output2": {"tot_pftrt": "1.23"},
    }
    client = _client(_settings(settings), pages=[page])

    result = client.get_account()

    assert result["pages_loaded"] == 1
    assert result["output1"] == page["output1"]
    assert result["output2"] == page["output2"]
    assert result["tr_id"] == KIS_OVERSEAS_BALANCE_TR_ID_PAPER
    assert client.is_loaded() is True


def test_get_account_pagination_two_pages_and_tr_cont(settings):
    fake = FakeAccountTransport(
        [
            {"rt_cd": "0", "output1": [{"ovrs_pdno": "AAPL"}], "ctx_area_fk200": "K1", "ctx_area_nk200": "N1"},
            {"rt_cd": "0", "output1": [{"ovrs_pdno": "MSFT"}], "ctx_area_fk200": "", "ctx_area_nk200": ""},
        ]
    )
    configured = _settings(settings)
    client = KisAccountClient(configured, _auth(configured), transport=fake)

    result = client.get_account()

    assert result["pages_loaded"] == 2
    assert [row["ovrs_pdno"] for row in result["output1"]] == ["AAPL", "MSFT"]
    assert fake.calls[0]["tr_cont"] == ""
    assert fake.calls[1]["tr_cont"] == "N"
    assert fake.calls[1]["ctx_area_fk200"] == "K1"
    assert fake.calls[1]["ctx_area_nk200"] == "N1"


def test_get_account_pagination_cap_exceeded(settings):
    fake = FakeAccountTransport(
        [{"rt_cd": "0", "ctx_area_fk200": f"K{i}", "ctx_area_nk200": f"N{i}"} for i in range(KIS_BALANCE_MAX_PAGES)]
    )
    configured = _settings(settings)
    client = KisAccountClient(configured, _auth(configured), transport=fake)

    with pytest.raises(KisDataUnavailableError, match="balance_pagination_cap_exceeded"):
        client.get_account()
    assert len(fake.calls) == KIS_BALANCE_MAX_PAGES
    assert client.is_loaded() is False


def test_get_account_kis_error_propagates(settings):
    fake = FakeAccountTransport(exc=KisDataUnavailableError("kis_error:EFGS9999"))
    configured = _settings(settings)
    client = KisAccountClient(configured, _auth(configured), transport=fake)

    with pytest.raises(KisDataUnavailableError, match="kis_error:EFGS9999"):
        client.get_account()
    assert client.is_loaded() is False


def test_get_positions_maps_catalog_fields_and_drops_zero_qty(settings):
    client = _client(
        _settings(settings),
        pages=[
            {
                "rt_cd": "0",
                "output1": [
                    {
                        "ovrs_pdno": "aapl",
                        "ovrs_cblc_qty": "2",
                        "pchs_avg_pric": "100.50",
                        "ovrs_stck_evlu_amt": "201.00",
                        "tr_crcy_cd": "USD",
                        "ovrs_excg_cd": "NASD",
                    },
                    {"ovrs_pdno": "MSFT", "ovrs_cblc_qty": "0"},
                ],
            }
        ],
    )

    assert client.get_positions() == [
        KisPosition("AAPL", 2, Decimal("100.50"), Decimal("201.00"), "USD", "NASD")
    ]
    assert client.positions_loaded() is True


def test_get_positions_multi_currency_separate_calls_no_aggregation(settings):
    configured = _settings(settings)
    usd_client = _client(
        configured,
        pages=[
            {
                "rt_cd": "0",
                "output1": [
                    {
                        "ovrs_pdno": "AAPL",
                        "ovrs_cblc_qty": "1",
                        "tr_crcy_cd": "USD",
                        "ovrs_excg_cd": "NASD",
                    }
                ],
            }
        ],
    )
    hkd_client = _client(
        configured,
        pages=[
            {
                "rt_cd": "0",
                "output1": [
                    {
                        "ovrs_pdno": "0700",
                        "ovrs_cblc_qty": "3",
                        "tr_crcy_cd": "HKD",
                        "ovrs_excg_cd": "NASD",
                    }
                ],
            }
        ],
    )

    usd_positions = usd_client.get_positions(currency="USD")
    hkd_positions = hkd_client.get_positions(currency="HKD")

    assert usd_positions[0].currency == "USD"
    assert hkd_positions[0].currency == "HKD"
    assert usd_positions[0].market_value == Decimal("0")
    assert hkd_positions[0].market_value == Decimal("0")


def test_urllib_account_transport_rejects_live_host():
    transport = UrllibAccountTransport()
    live_host = "openapi" + ".koreainvestment.com:9443"
    with pytest.raises(KisDataUnavailableError, match="disallowed_host"):
        transport.get_balance(**_transport_kwargs(base_url=f"https://{live_host}"))


def test_urllib_account_transport_rejects_unsupported_tr_id():
    transport = UrllibAccountTransport()
    with pytest.raises(KisDataUnavailableError, match="disallowed_tr_id"):
        transport.get_balance(**_transport_kwargs(tr_id="UNSUPPORTED_TR_ID"))


def test_urllib_account_transport_rejects_invalid_exchange():
    transport = UrllibAccountTransport()
    with pytest.raises(KisDataUnavailableError, match="invalid_exchange"):
        transport.get_balance(**_transport_kwargs(ovrs_excg_cd="LSE"))


def test_urllib_account_transport_rejects_invalid_currency():
    transport = UrllibAccountTransport()
    with pytest.raises(KisDataUnavailableError, match="invalid_currency"):
        transport.get_balance(**_transport_kwargs(tr_crcy_cd="EUR"))


def test_get_cash_balance_fail_closed_with_clear_reason(settings):
    client = _client(_settings(settings))
    with pytest.raises(KisDataUnavailableError, match="paper_cash_balance_not_available_official_field_missing"):
        client.get_cash_balance()
    assert client.cash_balance_loaded() is False


def test_parse_positions_response_uses_catalog_fields_only(settings):
    client = _client(_settings(settings))

    positions = client.parse_positions_response(
        {
            "rt_cd": "0",
            "output1": [
                {
                    "ovrs_pdno": "AAPL",
                    "ovrs_cblc_qty": "2",
                    "pchs_avg_pric": "100.50",
                    "ovrs_stck_evlu_amt": "201.00",
                    "tr_crcy_cd": "USD",
                    "ovrs_excg_cd": "NASD",
                }
            ],
        }
    )
    legacy = client.parse_positions_response(
        {"rt_cd": "0", "output1": [{"pdno": "MSFT", "hldg_qty": "7"}]}
    )

    assert positions == [
        KisPosition("AAPL", 2, Decimal("100.50"), Decimal("201.00"), "USD", "NASD")
    ]
    assert legacy == []


def test_parse_cash_balance_response_fails_closed(settings):
    client = _client(_settings(settings))
    with pytest.raises(KisDataUnavailableError, match="paper_cash_balance_not_available_official_field_missing"):
        client.parse_cash_balance_response({"output3": {"foo": "bar"}})
    assert client.cash_balance_loaded() is False


def test_get_account_sanitizes_echoed_secrets(settings):
    configured = _settings(settings)
    client = _client(
        configured,
        pages=[
            {
                "rt_cd": "0",
                "output1": [
                    {
                        "ovrs_pdno": "AAPL",
                        "appkey": "fake-key-XYZ",
                        "appsecret": "fake-secret-XYZ",
                        "access_token": "Bearer test-token",
                    }
                ],
                "output2": {"account_no": "12345678-01"},
            }
        ],
    )

    rendered = json.dumps(client.get_account(), sort_keys=True)

    assert "fake-key-XYZ" not in rendered
    assert "fake-secret-XYZ" not in rendered
    assert "Bearer test-token" not in rendered
    assert "12345678-01" not in rendered


def test_account_client_repr_and_exceptions_do_not_expose_secrets(settings):
    configured = _settings(settings)
    client = KisAccountClient(
        configured,
        _auth(configured),
        transport=FakeAccountTransport(exc=KisDataUnavailableError("transport_error")),
    )
    broker = KisBroker(configured)
    haystacks = [repr(client), repr(broker)]

    with pytest.raises(KisDataUnavailableError) as exc_info:
        client.get_account()
    haystacks.append(str(exc_info.value))

    forbidden = ("fake-key-XYZ", "fake-secret-XYZ", "12345678", "Bearer test-token")
    for haystack in haystacks:
        for needle in forbidden:
            assert needle not in haystack


def test_kis_broker_healthcheck_reflects_account_state(settings):
    broker = KisBroker(_settings(settings))
    broker.auth._store_token("fake-access-token", 120)
    broker.account._transport = FakeAccountTransport([{"rt_cd": "0", "output1": [], "output2": {}}])

    broker.get_account()
    health = broker.healthcheck()

    assert health["account_loaded"] is True
    assert health["cash_balance_loaded"] is False

    broker.account._transport = FakeAccountTransport(
        [{"rt_cd": "0", "output1": [{"ovrs_pdno": "AAPL", "ovrs_cblc_qty": "1"}]}]
    )
    broker.get_positions()

    assert broker.healthcheck()["positions_loaded"] is True
