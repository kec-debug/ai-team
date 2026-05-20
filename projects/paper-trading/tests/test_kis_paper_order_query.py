import json
import pathlib
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest

from app.broker.kis import (
    KIS_OVERSEAS_CCNL_PATH,
    KIS_PAPER_CCNL_TR_ID,
    KIS_PAPER_QUERY_CCLD_NCCS_DVSN,
    KIS_PAPER_QUERY_EXCHANGES,
    KIS_PAPER_QUERY_HOSTS,
    KIS_PAPER_QUERY_SLL_BUY_DVSN,
    KIS_PAPER_QUERY_SORT_SQN,
    KIS_QUERY_MAX_PAGES,
    KisAuthClient,
    KisBroker,
    KisDataUnavailableError,
    KisOrderRejectedError,
    MockQueryTransport,
    UrllibQueryTransport,
)
from app.domain.enums import TradingMode


def _settings(settings, **overrides):
    data = {
        "kis_env": "paper",
        "kis_account_no": "12345678-01",
        "kis_app_key": "fake-key-XYZ",
        "kis_app_secret": "fake-secret-XYZ",
        "kis_api_mode": "paper",
        "kis_order_dry_run": False,
    }
    data.update(overrides)
    return replace(settings, **data)


class FakeQueryTransport:
    def __init__(
        self,
        pages: list[dict[str, Any]] | None = None,
        exc: Exception | None = None,
    ) -> None:
        self._pages = list(pages or [])
        self._exc = exc
        self.calls: list[dict[str, Any]] = []

    def get_ccnl(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc
        if not self._pages:
            raise AssertionError("FakeQueryTransport exhausted")
        return self._pages.pop(0)


def _authenticated_broker(settings, **overrides) -> KisBroker:
    broker = KisBroker(_settings(settings, **overrides))
    broker.auth._store_token("fake-access-token", 120)
    return broker


def _row(**overrides: Any) -> dict[str, Any]:
    data = {
        "odno": "0000000001",
        "pdno": "AAPL",
        "sll_buy_dvsn_cd": "02",
        "ft_ord_qty": "10",
        "ft_ord_unpr3": "100.50",
        "ft_ccld_qty": "0",
        "ft_ccld_unpr3": "0",
        "ft_ccld_amt3": "0",
        "nccs_qty": "10",
        "prcs_stat_name": "전송",
        "ovrs_excg_cd": "NASD",
        "tr_crcy_cd": "USD",
        "ord_tmd": "093015",
    }
    data.update(overrides)
    return data


def _ok_page(rows: list[dict[str, Any]] | None = None, **extras: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "rt_cd": "0",
        "output": rows or [],
        "ctx_area_fk200": "",
        "ctx_area_nk200": "",
    }
    data.update(extras)
    return data


# ── Constants ─────────────────────────────────────────────────────────────────


def test_paper_query_constants_us_only():
    assert KIS_PAPER_CCNL_TR_ID == "VTTS3035R"
    assert KIS_OVERSEAS_CCNL_PATH == "/uapi/overseas-stock/v1/trading/inquire-ccnl"
    assert KIS_PAPER_QUERY_EXCHANGES == frozenset({"NASD", "NYSE", "AMEX"})
    assert KIS_PAPER_QUERY_SLL_BUY_DVSN == "00"
    assert KIS_PAPER_QUERY_CCLD_NCCS_DVSN == "00"
    assert KIS_PAPER_QUERY_SORT_SQN == "DS"
    assert KIS_PAPER_QUERY_HOSTS == frozenset({"openapivts.koreainvestment.com:29443"})


# ── Auth / paper gates ────────────────────────────────────────────────────────


def test_get_open_orders_requires_authentication(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(KisOrderRejectedError, match="authentication_required"):
        broker.get_open_orders()


def test_get_fills_requires_authentication(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(KisOrderRejectedError, match="authentication_required"):
        broker.get_fills()


def test_get_order_status_requires_authentication(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(KisOrderRejectedError, match="authentication_required"):
        broker.get_order_status("any-id")


def test_get_open_orders_mock_mode_fails_closed(settings):
    broker = KisBroker(_settings(settings, kis_api_mode="mock"))
    broker.auth._store_token("fake-access-token", 120)
    with pytest.raises(KisOrderRejectedError, match="mock_mode_no_network"):
        broker.get_open_orders()


def test_get_order_status_empty_broker_id_fails_closed(settings):
    broker = _authenticated_broker(settings)
    broker._query_transport = FakeQueryTransport([_ok_page()])
    with pytest.raises(KisOrderRejectedError, match="unknown_broker_order_id"):
        broker.get_order_status("")


def test_get_open_orders_invalid_exchange_fails_closed(settings):
    broker = _authenticated_broker(settings)
    broker._query_transport = FakeQueryTransport([_ok_page()])
    with pytest.raises(KisOrderRejectedError, match="invalid_exchange"):
        broker.get_open_orders(exchange="SEHK")


# ── Happy paths ───────────────────────────────────────────────────────────────


def test_get_open_orders_filters_by_nccs_qty(settings):
    open_row = _row(odno="OPEN001", nccs_qty="5", ft_ccld_qty="5")
    filled_row = _row(odno="FILLED002", nccs_qty="0", ft_ccld_qty="10")
    broker = _authenticated_broker(settings)
    fake = FakeQueryTransport([_ok_page([open_row, filled_row])])
    broker._query_transport = fake

    acks = broker.get_open_orders()

    assert len(acks) == 1
    assert acks[0].broker_order_id == "OPEN001"
    assert acks[0].mode is TradingMode.PAPER
    # transport call body honors paper constraints
    call = fake.calls[0]
    assert call["tr_id"] == "VTTS3035R"
    assert call["pdno"] == ""
    assert call["sll_buy_dvsn"] == "00"
    assert call["ccld_nccs_dvsn"] == "00"
    assert call["sort_sqn"] == "DS"
    assert call["ord_dt"] == ""
    assert call["ord_gno_brno"] == ""
    assert call["odno"] == ""
    assert call["ovrs_excg_cd"] == "NASD"


def test_get_fills_filters_by_filled_qty(settings):
    open_row = _row(odno="OPEN001", nccs_qty="5", ft_ccld_qty="0")
    filled_row = _row(odno="FILLED002", nccs_qty="0", ft_ccld_qty="10")
    broker = _authenticated_broker(settings)
    broker._query_transport = FakeQueryTransport([_ok_page([open_row, filled_row])])

    acks = broker.get_fills()

    assert len(acks) == 1
    assert acks[0].broker_order_id == "FILLED002"


def test_get_order_status_finds_by_odno(settings):
    target = _row(odno="TARGET777", nccs_qty="0", ft_ccld_qty="10")
    broker = _authenticated_broker(settings)
    broker._query_transport = FakeQueryTransport([_ok_page([_row(odno="OTHER"), target])])

    status = broker.get_order_status("TARGET777")

    assert status["odno"] == "TARGET777"
    assert status["ft_ccld_qty"] == "10"


def test_get_order_status_unknown_odno_fails_closed(settings):
    broker = _authenticated_broker(settings)
    broker._query_transport = FakeQueryTransport([_ok_page([_row(odno="OTHER")])])
    with pytest.raises(KisOrderRejectedError, match="unknown_broker_order_id"):
        broker.get_order_status("MISSING")


# ── Pagination ────────────────────────────────────────────────────────────────


def test_pagination_walks_pages_until_empty_ctx(settings):
    broker = _authenticated_broker(settings)
    fake = FakeQueryTransport(
        [
            _ok_page([_row(odno="P1A")], ctx_area_fk200="K1", ctx_area_nk200="N1"),
            _ok_page([_row(odno="P2A")]),  # empty ctx → stop
        ]
    )
    broker._query_transport = fake
    broker.get_open_orders()

    assert len(fake.calls) == 2
    assert fake.calls[0]["tr_cont"] == ""
    assert fake.calls[1]["tr_cont"] == "N"
    assert fake.calls[1]["ctx_area_fk200"] == "K1"
    assert fake.calls[1]["ctx_area_nk200"] == "N1"


def test_pagination_cap_exceeded_fails_closed(settings):
    broker = _authenticated_broker(settings)
    pages = [
        _ok_page([], ctx_area_fk200=f"K{i}", ctx_area_nk200=f"N{i}")
        for i in range(KIS_QUERY_MAX_PAGES)
    ]
    fake = FakeQueryTransport(pages)
    broker._query_transport = fake
    with pytest.raises(KisOrderRejectedError, match="query_pagination_cap_exceeded"):
        broker.get_open_orders()
    assert len(fake.calls) == KIS_QUERY_MAX_PAGES


# ── Error propagation ─────────────────────────────────────────────────────────


def test_kis_error_response_propagates(settings):
    broker = _authenticated_broker(settings)
    broker._query_transport = FakeQueryTransport(
        [{"rt_cd": "1", "msg_cd": "EFGS9999", "msg1": "rejected"}]
    )
    with pytest.raises(KisOrderRejectedError, match="kis_error:EFGS9999"):
        broker.get_open_orders()


def test_malformed_response_missing_rt_cd_fails_closed(settings):
    broker = _authenticated_broker(settings)
    broker._query_transport = FakeQueryTransport([{"unexpected": True}])
    with pytest.raises(KisOrderRejectedError, match="malformed_response"):
        broker.get_open_orders()


def test_transport_error_propagates(settings):
    broker = _authenticated_broker(settings)
    broker._query_transport = FakeQueryTransport(
        exc=KisDataUnavailableError("transport_error")
    )
    with pytest.raises(KisOrderRejectedError, match="transport_error"):
        broker.get_open_orders()


# ── Transport allowlists ──────────────────────────────────────────────────────


def _transport_kwargs(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "base_url": "https://openapivts.koreainvestment.com:29443",
        "access_token": "fake-access-token",
        "app_key": "fake-key-XYZ",
        "app_secret": "fake-secret-XYZ",
        "tr_id": KIS_PAPER_CCNL_TR_ID,
        "cano": "12345678",
        "acnt_prdt_cd": "01",
        "pdno": "",
        "ord_strt_dt": "20260520",
        "ord_end_dt": "20260520",
        "sll_buy_dvsn": KIS_PAPER_QUERY_SLL_BUY_DVSN,
        "ccld_nccs_dvsn": KIS_PAPER_QUERY_CCLD_NCCS_DVSN,
        "ovrs_excg_cd": "NASD",
        "sort_sqn": KIS_PAPER_QUERY_SORT_SQN,
        "ord_dt": "",
        "ord_gno_brno": "",
        "odno": "",
        "ctx_area_fk200": "",
        "ctx_area_nk200": "",
        "tr_cont": "",
    }
    data.update(overrides)
    return data


def test_urllib_query_transport_rejects_live_host():
    live_host = "openapi" + ".koreainvestment.com:9443"
    with pytest.raises(KisDataUnavailableError, match="disallowed_host"):
        UrllibQueryTransport().get_ccnl(**_transport_kwargs(base_url=f"https://{live_host}"))


def test_urllib_query_transport_rejects_live_tr_id():
    forbidden = "TTTS" + "3035R"  # live TR_ID, built via concat for grep clean
    with pytest.raises(KisDataUnavailableError, match="disallowed_tr_id"):
        UrllibQueryTransport().get_ccnl(**_transport_kwargs(tr_id=forbidden))


def test_urllib_query_transport_rejects_non_us_exchange():
    with pytest.raises(KisDataUnavailableError, match="invalid_exchange"):
        UrllibQueryTransport().get_ccnl(**_transport_kwargs(ovrs_excg_cd="SEHK"))


def test_urllib_query_transport_rejects_percent_exchange():
    with pytest.raises(KisDataUnavailableError, match="invalid_exchange"):
        UrllibQueryTransport().get_ccnl(**_transport_kwargs(ovrs_excg_cd="%"))


def test_urllib_query_transport_rejects_non_empty_pdno():
    with pytest.raises(KisDataUnavailableError, match="paper_pdno_must_be_empty"):
        UrllibQueryTransport().get_ccnl(**_transport_kwargs(pdno="AAPL"))


def test_urllib_query_transport_rejects_sll_buy_filter():
    with pytest.raises(KisDataUnavailableError, match="paper_sll_buy_dvsn_must_be_00"):
        UrllibQueryTransport().get_ccnl(**_transport_kwargs(sll_buy_dvsn="01"))


def test_urllib_query_transport_rejects_ccld_filter():
    with pytest.raises(KisDataUnavailableError, match="paper_ccld_nccs_dvsn_must_be_00"):
        UrllibQueryTransport().get_ccnl(**_transport_kwargs(ccld_nccs_dvsn="02"))


def test_urllib_query_transport_rejects_sort_sqn_override():
    with pytest.raises(KisDataUnavailableError, match="paper_sort_sqn_must_be_ds"):
        UrllibQueryTransport().get_ccnl(**_transport_kwargs(sort_sqn="AS"))


def test_urllib_query_transport_rejects_odno_search():
    with pytest.raises(KisDataUnavailableError, match="paper_odno_search_not_allowed"):
        UrllibQueryTransport().get_ccnl(**_transport_kwargs(odno="0000000001"))


# ── Capability / healthcheck surface preserved ────────────────────────────────


def test_capabilities_unchanged_after_query_implementation(settings):
    broker = _authenticated_broker(settings)
    assert broker.capabilities() == {
        "submission": False,
        "cancel": False,
        "replace": False,
        "open_orders": False,
        "fills": False,
        "order_status": False,
    }


def test_healthcheck_order_execution_implemented_remains_false(settings):
    broker = _authenticated_broker(settings)
    h = broker.healthcheck()
    assert h["order_execution_implemented"] is False
    assert h["order_methods_fail_closed"] is True


# ── Secret leak ───────────────────────────────────────────────────────────────


def test_query_response_sanitization_redacts_secrets(settings):
    page = _ok_page(
        [_row()],
        appkey="echoed-key",
        access_token="Bearer echoed-token",
    )
    broker = _authenticated_broker(settings)
    broker._query_transport = FakeQueryTransport([page])
    broker.get_open_orders()
    serialized = json.dumps(broker._last_open_orders_rows)
    assert "echoed-key" not in serialized
    assert "Bearer echoed-token" not in serialized


def test_query_exceptions_and_repr_do_not_expose_secrets(settings):
    broker = _authenticated_broker(settings)
    broker._query_transport = FakeQueryTransport(
        exc=KisDataUnavailableError("kis_error:EFGS9999"),
    )
    with pytest.raises(KisOrderRejectedError) as exc_info:
        broker.get_open_orders()
    haystacks = [repr(broker), str(exc_info.value)]
    forbidden = ("fake-key-XYZ", "fake-secret-XYZ", "12345678", "fake-access-token", "Bearer fake-access-token")
    for needle in forbidden:
        for hay in haystacks:
            assert needle not in hay


# ── Module surface ────────────────────────────────────────────────────────────


def test_kis_module_does_not_introduce_live_query_tr_id():
    path = pathlib.Path(__file__).resolve().parents[1] / "app" / "broker" / "kis.py"
    text = path.read_text(encoding="utf-8")
    forbidden_live = "TTTS" + "3035R"
    forbidden_unsupported = ("TTTS" + "3018R", "TTTT" + "3039R", "TTTS" + "3014R")
    assert forbidden_live not in text
    for tok in forbidden_unsupported:
        assert tok not in text
