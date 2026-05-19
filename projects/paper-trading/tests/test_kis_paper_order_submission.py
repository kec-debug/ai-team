import json
import pathlib
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest

from app.broker.kis import (
    KIS_OVERSEAS_ORDER_PATH,
    KIS_PAPER_ORDER_EXCHANGES,
    KIS_PAPER_ORDER_TR_ID_US_BUY,
    KIS_PAPER_ORDER_TR_ID_US_SELL,
    KIS_PAPER_ORDER_TR_IDS,
    KisBroker,
    KisOrderRejectedError,
    KisOrderRequest,
    MockOrderTransport,
    UrllibOrderTransport,
    _build_paper_order_body,
    _select_paper_order_tr_id,
)
from app.domain.enums import OrderType, Side, TradingMode
from app.domain.orders import BrokerOrder, OrderIntent
from app.oms.manager import OMS
from app.risk.engine import RiskEngine


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


def _broker_order(**overrides) -> BrokerOrder:
    now = datetime.now(timezone.utc)
    data = {
        "symbol": "AAPL",
        "side": Side.BUY,
        "quantity": 10,
        "order_type": OrderType.LIMIT,
        "limit_price": Decimal("100.50"),
        "risk_token": "rt",
        "created_at": now,
        "oms_id": "oms-1",
        "submitted_at": now,
        "quote_timestamp": now,
    }
    data.update(overrides)
    return BrokerOrder(**data)


def _order_request(**overrides) -> KisOrderRequest:
    data = {
        "symbol": "AAPL",
        "market": "US",
        "side": Side.BUY,
        "quantity": 10,
        "order_type": OrderType.LIMIT,
        "limit_price": Decimal("100.50"),
        "extended_hours": False,
        "account_no_masked": "***8-01",
        "broker_environment": "paper",
        "idempotency_key": "kis-paper-oms-1",
    }
    data.update(overrides)
    return KisOrderRequest(**data)


class FakeOrderTransport:
    def __init__(self, response: dict[str, Any] | None = None, exc: Exception | None = None) -> None:
        self._response = response
        self._exc = exc
        self.calls: list[dict[str, Any]] = []

    def submit_order(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc
        if self._response is None:
            raise AssertionError("FakeOrderTransport response not set")
        return self._response


def _authenticated_broker(settings, **overrides):
    broker = KisBroker(_settings(settings, **overrides))
    broker.auth._store_token("fake-access-token", 120)
    return broker


def _success_response(**overrides):
    data = {
        "rt_cd": "0",
        "msg_cd": "APBK001",
        "msg1": "ok",
        "output": {
            "KRX_FWDG_ORD_ORGNO": "00123",
            "ODNO": "0000123456",
            "ORD_TMD": "091501",
        },
    }
    data.update(overrides)
    return data


def _transport_kwargs(**overrides):
    data = {
        "base_url": "https://openapivts.koreainvestment.com:29443",
        "access_token": "fake-access-token",
        "app_key": "fake-key-XYZ",
        "app_secret": "fake-secret-XYZ",
        "tr_id": KIS_PAPER_ORDER_TR_ID_US_BUY,
        "body": _build_paper_order_body(
            cano="12345678",
            acnt_prdt_cd="01",
            exchange="NASD",
            request=_order_request(),
        ),
    }
    data.update(overrides)
    return data


def test_select_paper_order_tr_id_maps_side_correctly():
    assert _select_paper_order_tr_id(Side.BUY) == KIS_PAPER_ORDER_TR_ID_US_BUY
    assert _select_paper_order_tr_id(Side.SELL) == KIS_PAPER_ORDER_TR_ID_US_SELL
    assert KIS_PAPER_ORDER_TR_IDS == {KIS_PAPER_ORDER_TR_ID_US_BUY, KIS_PAPER_ORDER_TR_ID_US_SELL}


def test_build_paper_order_body_buy_omits_sll_type():
    body = _build_paper_order_body(
        cano="12345678",
        acnt_prdt_cd="01",
        exchange="NASD",
        request=_order_request(side=Side.BUY),
    )
    assert body["ORD_DVSN"] == "00"
    assert body["ORD_SVR_DVSN_CD"] == "0"
    assert "SLL_TYPE" not in body


def test_build_paper_order_body_sell_sets_sll_type_zero_zero():
    body = _build_paper_order_body(
        cano="12345678",
        acnt_prdt_cd="01",
        exchange="NASD",
        request=_order_request(side=Side.SELL),
    )
    assert body["SLL_TYPE"] == "00"


def test_build_paper_order_body_contains_only_catalog_keys():
    buy_keys = set(
        _build_paper_order_body(
            cano="12345678",
            acnt_prdt_cd="01",
            exchange="NASD",
            request=_order_request(side=Side.BUY),
        )
    )
    sell_keys = set(
        _build_paper_order_body(
            cano="12345678",
            acnt_prdt_cd="01",
            exchange="NASD",
            request=_order_request(side=Side.SELL),
        )
    )

    assert buy_keys == {
        "CANO",
        "ACNT_PRDT_CD",
        "OVRS_EXCG_CD",
        "PDNO",
        "ORD_QTY",
        "OVRS_ORD_UNPR",
        "ORD_DVSN",
        "ORD_SVR_DVSN_CD",
    }
    assert sell_keys == buy_keys | {"SLL_TYPE"}


def test_build_paper_order_body_quantity_and_price_are_strings():
    body = _build_paper_order_body(
        cano="12345678",
        acnt_prdt_cd="01",
        exchange="NASD",
        request=_order_request(quantity=7, limit_price=Decimal("100.50")),
    )
    assert body["ORD_QTY"] == "7"
    assert body["OVRS_ORD_UNPR"] == "100.50"


def test_place_order_dry_run_path_unchanged(settings):
    broker = KisBroker(_settings(settings, kis_order_dry_run=True))
    fake = FakeOrderTransport(_success_response())
    broker._order_transport = fake

    ack = broker.place_order(_broker_order())

    assert ack.status == "dry_run"
    assert ack.broker_order_id is None
    assert broker.last_order_preview is not None
    assert fake.calls == []


def test_place_order_dry_run_disabled_requires_authentication(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(KisOrderRejectedError, match="authentication_required"):
        broker.place_order(_broker_order())


def test_place_order_dry_run_disabled_blocked_by_preflight(settings):
    broker = _authenticated_broker(settings)
    with pytest.raises(KisOrderRejectedError, match="quantity_invalid"):
        broker.place_order(_broker_order(quantity=0))


def test_place_order_dry_run_disabled_blocked_by_live_trading(settings):
    broker = _authenticated_broker(settings, live_trading_enabled=True)
    with pytest.raises(KisOrderRejectedError, match="live_trading_enabled"):
        broker.place_order(_broker_order())


def test_place_order_dry_run_disabled_blocked_by_market_order_type(settings):
    broker = _authenticated_broker(settings)
    with pytest.raises(KisOrderRejectedError, match="order_type_not_limit"):
        broker.place_order(_broker_order(order_type=OrderType.MARKET))


def test_place_order_dry_run_disabled_blocked_by_allow_market_orders(settings):
    broker = _authenticated_broker(settings, allow_market_orders=True)
    with pytest.raises(KisOrderRejectedError, match="market_orders_allowed_flag_set"):
        broker.place_order(_broker_order())


def test_place_order_dry_run_disabled_blocked_by_kill_switch(settings):
    broker = _authenticated_broker(settings, kill_switch_engaged=True)
    with pytest.raises(KisOrderRejectedError, match="kill_switch_engaged"):
        broker.place_order(_broker_order())


def test_place_order_dry_run_disabled_mock_mode_fails_closed(settings):
    broker = _authenticated_broker(settings, kis_api_mode="mock")
    with pytest.raises(KisOrderRejectedError, match="mock_mode_no_network"):
        broker.place_order(_broker_order())


def test_place_order_happy_path_buy(settings):
    broker = _authenticated_broker(settings)
    fake = FakeOrderTransport(_success_response())
    broker._order_transport = fake

    ack = broker.place_order(_broker_order(side=Side.BUY))

    assert ack.status == "submitted"
    assert ack.broker_order_id == "0000123456"
    assert broker.last_order_response is not None
    assert broker.last_order_response.raw_response_sanitized["output"]["ODNO"] == "0000123456"
    assert fake.calls[0]["tr_id"] == KIS_PAPER_ORDER_TR_ID_US_BUY
    assert fake.calls[0]["body"]["OVRS_EXCG_CD"] == "NASD"
    assert "SLL_TYPE" not in fake.calls[0]["body"]


def test_place_order_happy_path_sell(settings):
    broker = _authenticated_broker(settings)
    fake = FakeOrderTransport(_success_response())
    broker._order_transport = fake

    ack = broker.place_order(_broker_order(side=Side.SELL))

    assert ack.status == "submitted"
    assert ack.broker_order_id == "0000123456"
    assert fake.calls[0]["tr_id"] == KIS_PAPER_ORDER_TR_ID_US_SELL
    assert fake.calls[0]["body"]["SLL_TYPE"] == "00"


def test_place_order_uses_correct_tr_id_per_side(settings):
    for side, expected in ((Side.BUY, KIS_PAPER_ORDER_TR_ID_US_BUY), (Side.SELL, KIS_PAPER_ORDER_TR_ID_US_SELL)):
        broker = _authenticated_broker(settings)
        fake = FakeOrderTransport(_success_response())
        broker._order_transport = fake
        broker.place_order(_broker_order(side=side))
        assert fake.calls[0]["tr_id"] == expected


def test_place_order_kis_rejection_propagates(settings):
    broker = _authenticated_broker(settings)
    broker._order_transport = FakeOrderTransport({"rt_cd": "1", "msg_cd": "EGW001", "msg1": "rejected"})

    with pytest.raises(KisOrderRejectedError, match="kis_error:EGW001") as exc:
        broker.place_order(_broker_order())
    assert exc.value.reason == "kis_error:EGW001"
    assert broker.last_error == "kis_error:EGW001"


def test_place_order_malformed_response_fails_closed(settings):
    broker = _authenticated_broker(settings)
    broker._order_transport = FakeOrderTransport({"output": {"ODNO": "0000123456"}})

    with pytest.raises(KisOrderRejectedError, match="malformed_response"):
        broker.place_order(_broker_order())


def test_place_order_http_404_fails_closed(settings):
    broker = _authenticated_broker(settings)
    broker._order_transport = FakeOrderTransport(exc=KisOrderRejectedError("http_404"))

    with pytest.raises(KisOrderRejectedError, match="http_404"):
        broker.place_order(_broker_order())


def test_place_order_transport_error_fails_closed(settings):
    broker = _authenticated_broker(settings)
    broker._order_transport = FakeOrderTransport(exc=KisOrderRejectedError("transport_error"))

    with pytest.raises(KisOrderRejectedError, match="transport_error"):
        broker.place_order(_broker_order())


def test_urllib_order_transport_rejects_live_host():
    transport = UrllibOrderTransport()
    live_host = "openapi" + ".koreainvestment.com:9443"
    with pytest.raises(KisOrderRejectedError, match="disallowed_host"):
        transport.submit_order(**_transport_kwargs(base_url=f"https://{live_host}"))


def test_urllib_order_transport_rejects_unsupported_tr_id():
    transport = UrllibOrderTransport()
    with pytest.raises(KisOrderRejectedError, match="disallowed_tr_id"):
        transport.submit_order(**_transport_kwargs(tr_id="TTTT" + "1002U"))


def test_urllib_order_transport_rejects_invalid_exchange():
    transport = UrllibOrderTransport()
    body = dict(_transport_kwargs()["body"])
    body["OVRS_EXCG_CD"] = "SEHK"
    with pytest.raises(KisOrderRejectedError, match="invalid_exchange"):
        transport.submit_order(**_transport_kwargs(body=body))


def test_urllib_order_transport_rejects_invalid_ord_dvsn():
    transport = UrllibOrderTransport()
    body = dict(_transport_kwargs()["body"])
    body["ORD_DVSN"] = "32"
    with pytest.raises(KisOrderRejectedError, match="ord_dvsn_not_limit"):
        transport.submit_order(**_transport_kwargs(body=body))


def test_place_order_response_sanitization_redacts_secrets(settings):
    broker = _authenticated_broker(settings)
    broker._order_transport = FakeOrderTransport(
        _success_response(
            appkey="fake-key-XYZ",
            appsecret="fake-secret-XYZ",
            account_no="12345678-01",
            access_token="fake-access-token",
            authorization="Bearer fake-access-token",
        )
    )

    broker.place_order(_broker_order())
    rendered = json.dumps(broker.last_order_response.raw_response_sanitized, sort_keys=True)

    for forbidden in ("fake-key-XYZ", "fake-secret-XYZ", "12345678", "fake-access-token", "Bearer fake-access-token"):
        assert forbidden not in rendered


def test_place_order_exceptions_and_repr_do_not_expose_secrets(settings):
    broker = _authenticated_broker(settings)
    broker._order_transport = FakeOrderTransport(exc=KisOrderRejectedError("transport_error"))
    haystacks = [repr(broker)]

    with pytest.raises(KisOrderRejectedError) as exc_info:
        broker.place_order(_broker_order())
    haystacks.append(str(exc_info.value))

    broker._order_transport = FakeOrderTransport(_success_response(access_token="fake-access-token"))
    broker.place_order(_broker_order())
    haystacks.append(repr(broker.last_order_response))
    haystacks.append(json.dumps(broker.last_order_response.raw_response_sanitized, sort_keys=True))

    for forbidden in ("fake-key-XYZ", "fake-secret-XYZ", "12345678", "fake-access-token", "Bearer fake-access-token"):
        for haystack in haystacks:
            assert forbidden not in haystack


def test_place_order_via_oms_passes_riskengine(settings):
    configured = _settings(settings, max_order_notional_usd=Decimal("100000"))
    broker = KisBroker(configured)
    broker.auth._store_token("fake-access-token", 120)
    broker._order_transport = FakeOrderTransport(_success_response())
    oms = OMS(configured, RiskEngine(configured), broker)
    intent = OrderIntent(
        symbol="AAPL",
        side=Side.BUY,
        quantity=10,
        order_type=OrderType.LIMIT,
        limit_price=Decimal("100.50"),
        quote_timestamp=datetime.now(timezone.utc),
    )

    ack = oms.place(intent)

    assert ack.status == "submitted"
    assert ack.broker_order_id == "0000123456"


def test_kis_module_does_not_introduce_live_tr_ids():
    text = (pathlib.Path(__file__).resolve().parents[1] / "app" / "broker" / "kis.py").read_text(encoding="utf-8")
    forbidden = (
        "TTTT" + "1002U",
        "TTTT" + "1006U",
        "TTTT" + "1004U",
        "TTTS" + "1002U",
        "TTTS" + "1001U",
        "TTTS" + "0307U",
        "TTTS" + "0308U",
        "TTTS" + "0309U",
        "TTTT" + "3014U",
        "TTTT" + "3016U",
        "TTTT" + "3017U",
        "TTTS" + "3013U",
        "TTTS" + "3018R",
        "TTTT" + "3039R",
        "TTTS" + "3014R",
        "TTTS" + "6036U",
        "TTTS" + "6037U",
        "TTTS" + "6038U",
        "TTTS" + "6058R",
        "TTTS" + "6059R",
    )
    for tr_id in forbidden:
        assert tr_id not in text


def test_kis_paper_order_transport_uses_only_paper_base_url():
    transport = UrllibOrderTransport()
    paper_url = "https://openapivts.koreainvestment.com:29443"
    live_url = "https://" + "openapi" + ".koreainvestment.com:9443"
    other_url = "https://example.invalid"

    for base_url in (live_url, other_url):
        with pytest.raises(KisOrderRejectedError, match="disallowed_host"):
            transport.submit_order(**_transport_kwargs(base_url=base_url))
    assert KIS_OVERSEAS_ORDER_PATH == "/uapi/overseas-stock/v1/trading/order"
    assert "openapivts.koreainvestment.com:29443" in paper_url
    assert KIS_PAPER_ORDER_EXCHANGES == {"NASD", "NYSE", "AMEX"}
