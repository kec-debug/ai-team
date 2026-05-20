import json
import pathlib
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest

from app.broker.kis import (
    KIS_OVERSEAS_CANCEL_REPLACE_PATH,
    KIS_OVERSEAS_ORDER_PATH,
    KIS_PAPER_CANCEL_REPLACE_TR_ID_US,
    KIS_PAPER_CANCEL_REPLACE_TR_IDS,
    KIS_PAPER_ORDER_ALL_TR_IDS,
    KIS_PAPER_ORDER_EXCHANGES,
    KIS_PAPER_ORDER_TR_ID_US_BUY,
    KIS_RVSE_CNCL_DVSN_CANCEL,
    KIS_RVSE_CNCL_DVSN_REPLACE,
    KisBroker,
    KisOrderRejectedError,
    KisOrderResponse,
    MockOrderTransport,
    UrllibOrderTransport,
    _build_paper_cancel_body,
    _build_paper_replace_body,
)
from app.domain.enums import OrderType, Side
from app.domain.orders import BrokerOrder


CATALOG_CANCEL_REPLACE_KEYS = {
    "CANO",
    "ACNT_PRDT_CD",
    "OVRS_EXCG_CD",
    "PDNO",
    "ORGN_ODNO",
    "RVSE_CNCL_DVSN_CD",
    "ORD_QTY",
    "OVRS_ORD_UNPR",
}


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


class FakeOrderTransport:
    def __init__(
        self,
        responses: list[dict[str, Any]] | None = None,
        exc: Exception | None = None,
    ) -> None:
        self._responses = list(responses or [])
        self._exc = exc
        self.calls: list[dict[str, Any]] = []

    def submit_order(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc
        if not self._responses:
            raise AssertionError("FakeOrderTransport responses exhausted")
        return self._responses.pop(0)


class RaiseOnCallOrderTransport:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def submit_order(self, **kwargs):
        self.calls.append(kwargs)
        raise AssertionError("transport should not be called")


def _success_response(odno: str = "NEW_ODNO_999", **overrides):
    data = {
        "rt_cd": "0",
        "msg_cd": "APBK001",
        "msg1": "ok",
        "output": {
            "KRX_FWDG_ORD_ORGNO": "00123",
            "ODNO": odno,
            "ORD_TMD": "093015",
        },
    }
    data.update(overrides)
    return data


def _seed_history(broker: KisBroker, **overrides) -> KisOrderResponse:
    now = datetime.now(timezone.utc)
    data = {
        "internal_order_id": "oms-1",
        "broker_order_id": "OLD_ODNO_111",
        "broker": "KisBroker",
        "status": "submitted",
        "submitted_at": now,
        "symbol": "AAPL",
        "side": Side.BUY,
        "quantity": 10,
        "limit_price": Decimal("100.50"),
        "raw_response_sanitized": {"rt_cd": "0", "output": {"ODNO": "OLD_ODNO_111"}},
        "exchange": "NASD",
    }
    data.update(overrides)
    entry = KisOrderResponse(**data)
    assert entry.broker_order_id is not None
    broker._order_history[entry.broker_order_id] = entry
    return entry


def _authenticated_broker(settings, **overrides) -> KisBroker:
    broker = KisBroker(_settings(settings, **overrides))
    broker.auth._store_token("fake-access-token", 120)
    return broker


def _transport_kwargs(**overrides):
    body = _build_paper_cancel_body(
        cano="12345678",
        acnt_prdt_cd="01",
        exchange="NASD",
        symbol="AAPL",
        origin_odno="OLD_ODNO_111",
        original_qty=10,
    )
    data = {
        "base_url": "https://openapivts.koreainvestment.com:29443",
        "access_token": "fake-access-token",
        "app_key": "fake-key-XYZ",
        "app_secret": "fake-secret-XYZ",
        "tr_id": KIS_PAPER_CANCEL_REPLACE_TR_ID_US,
        "path": KIS_OVERSEAS_CANCEL_REPLACE_PATH,
        "body": body,
    }
    data.update(overrides)
    return data


def test_build_paper_cancel_body_contains_only_catalog_keys():
    body = _build_paper_cancel_body(
        cano="12345678",
        acnt_prdt_cd="01",
        exchange="NASD",
        symbol="AAPL",
        origin_odno="OLD_ODNO_111",
        original_qty=10,
    )
    assert set(body) == CATALOG_CANCEL_REPLACE_KEYS
    assert "ORD_DVSN" not in body
    assert "SLL_TYPE" not in body
    assert "MGCO_APTM_ODNO" not in body
    assert "CTAC_TLNO" not in body
    assert "ORD_SVR_DVSN_CD" not in body


def test_build_paper_cancel_body_sets_dvsn_02_and_unpr_zero_string():
    body = _build_paper_cancel_body(
        cano="12345678",
        acnt_prdt_cd="01",
        exchange="NASD",
        symbol="AAPL",
        origin_odno="OLD_ODNO_111",
        original_qty=7,
    )
    assert body["RVSE_CNCL_DVSN_CD"] == KIS_RVSE_CNCL_DVSN_CANCEL
    assert body["ORD_QTY"] == "7"
    assert body["OVRS_ORD_UNPR"] == "0"


def test_build_paper_replace_body_contains_only_catalog_keys():
    body = _build_paper_replace_body(
        cano="12345678",
        acnt_prdt_cd="01",
        exchange="NASD",
        symbol="AAPL",
        origin_odno="OLD_ODNO_111",
        new_qty=8,
        new_limit_price=Decimal("101.25"),
    )
    assert set(body) == CATALOG_CANCEL_REPLACE_KEYS
    assert "ORD_DVSN" not in body
    assert "SLL_TYPE" not in body
    assert "MGCO_APTM_ODNO" not in body
    assert "CTAC_TLNO" not in body
    assert "ORD_SVR_DVSN_CD" not in body


def test_build_paper_replace_body_sets_dvsn_01_and_new_qty_price():
    body = _build_paper_replace_body(
        cano="12345678",
        acnt_prdt_cd="01",
        exchange="NASD",
        symbol="AAPL",
        origin_odno="OLD_ODNO_111",
        new_qty=8,
        new_limit_price=Decimal("101.25"),
    )
    assert body["RVSE_CNCL_DVSN_CD"] == KIS_RVSE_CNCL_DVSN_REPLACE
    assert body["ORD_QTY"] == "8"
    assert body["OVRS_ORD_UNPR"] == "101.25"


def test_cancel_replace_constants_use_only_us_paper_tr_id():
    assert KIS_PAPER_CANCEL_REPLACE_TR_ID_US == "VTTT1004U"
    assert KIS_PAPER_CANCEL_REPLACE_TR_IDS == frozenset({"VTTT1004U"})
    assert KIS_PAPER_ORDER_ALL_TR_IDS == {
        KIS_PAPER_ORDER_TR_ID_US_BUY,
        "VTTT1001U",
        "VTTT1004U",
    }
    assert KIS_OVERSEAS_CANCEL_REPLACE_PATH == "/uapi/overseas-stock/v1/trading/order-rvsecncl"


def test_cancel_order_unknown_broker_order_id_fails_closed(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(KisOrderRejectedError, match="unknown_broker_order_id"):
        broker.cancel_order("missing")


def test_cancel_order_dry_run_returns_none_without_http(settings):
    broker = _authenticated_broker(settings, kis_order_dry_run=True)
    broker._order_transport = RaiseOnCallOrderTransport()
    entry = _seed_history(broker)

    assert broker.cancel_order(entry.broker_order_id or "") is None
    assert broker.last_order_preview is not None
    assert broker.last_order_preview.payload_sanitized["operation"] == "cancel"
    assert broker._order_transport.calls == []


def test_cancel_order_dry_run_disabled_requires_authentication(settings):
    broker = KisBroker(_settings(settings))
    entry = _seed_history(broker)
    with pytest.raises(KisOrderRejectedError, match="authentication_required"):
        broker.cancel_order(entry.broker_order_id or "")


def test_cancel_order_dry_run_disabled_blocked_by_live_trading(settings):
    broker = _authenticated_broker(settings, live_trading_enabled=True)
    entry = _seed_history(broker)
    with pytest.raises(KisOrderRejectedError, match="live_trading_enabled"):
        broker.cancel_order(entry.broker_order_id or "")


def test_cancel_order_dry_run_disabled_blocked_by_kis_env_not_paper(settings):
    with pytest.raises(RuntimeError, match="live env is disabled"):
        KisBroker(_settings(settings, kis_env="live"))


def test_cancel_order_dry_run_disabled_blocked_by_kill_switch(settings):
    broker = _authenticated_broker(settings, kill_switch_engaged=True)
    entry = _seed_history(broker)
    with pytest.raises(KisOrderRejectedError, match="kill_switch_engaged"):
        broker.cancel_order(entry.broker_order_id or "")


def test_cancel_order_dry_run_disabled_blocked_by_allow_market_orders(settings):
    broker = _authenticated_broker(settings, allow_market_orders=True)
    entry = _seed_history(broker)
    with pytest.raises(KisOrderRejectedError, match="market_orders_allowed_flag_set"):
        broker.cancel_order(entry.broker_order_id or "")


def test_cancel_order_dry_run_disabled_mock_mode_fails_closed(settings):
    broker = _authenticated_broker(settings, kis_api_mode="mock")
    entry = _seed_history(broker)
    with pytest.raises(KisOrderRejectedError, match="mock_mode_no_network"):
        broker.cancel_order(entry.broker_order_id or "")


def test_cancel_order_happy_path(settings):
    broker = _authenticated_broker(settings)
    entry = _seed_history(broker)
    broker._order_transport = FakeOrderTransport([_success_response(odno="OLD_ODNO_111")])

    assert broker.cancel_order(entry.broker_order_id or "") is None

    stored = broker._order_history[entry.broker_order_id or ""]
    assert stored.status == "cancelled"
    call = broker._order_transport.calls[0]
    assert call["tr_id"] == KIS_PAPER_CANCEL_REPLACE_TR_ID_US
    assert call["path"] == KIS_OVERSEAS_CANCEL_REPLACE_PATH
    assert call["body"] == _build_paper_cancel_body(
        cano="12345678",
        acnt_prdt_cd="01",
        exchange="NASD",
        symbol="AAPL",
        origin_odno="OLD_ODNO_111",
        original_qty=10,
    )


def test_cancel_order_kis_rejection_propagates(settings):
    broker = _authenticated_broker(settings)
    entry = _seed_history(broker)
    broker._order_transport = FakeOrderTransport([{"rt_cd": "1", "msg_cd": "EGW001", "msg1": "no"}])

    with pytest.raises(KisOrderRejectedError, match="kis_error:EGW001"):
        broker.cancel_order(entry.broker_order_id or "")


def test_cancel_order_malformed_response_fails_closed(settings):
    broker = _authenticated_broker(settings)
    entry = _seed_history(broker)
    broker._order_transport = FakeOrderTransport([{"output": {"ODNO": "OLD_ODNO_111"}}])

    with pytest.raises(KisOrderRejectedError, match="malformed_response"):
        broker.cancel_order(entry.broker_order_id or "")


def test_cancel_order_already_cancelled_fails_closed(settings):
    broker = _authenticated_broker(settings)
    entry = _seed_history(broker, status="cancelled")
    with pytest.raises(KisOrderRejectedError, match="not_cancellable_state"):
        broker.cancel_order(entry.broker_order_id or "")


def test_cancel_order_after_replace_targets_old_id_fails_closed(settings):
    broker = _authenticated_broker(settings)
    old = _seed_history(broker)
    broker._order_transport = FakeOrderTransport([_success_response(odno="NEW_ODNO_999")])
    ack = broker.replace_order(old.broker_order_id or "", _broker_order(quantity=8, limit_price=Decimal("101.25")))

    with pytest.raises(KisOrderRejectedError, match="not_cancellable_state"):
        broker.cancel_order(old.broker_order_id or "")

    broker._order_transport = FakeOrderTransport([_success_response(odno=ack.broker_order_id or "")])
    assert broker.cancel_order(ack.broker_order_id or "") is None


def test_replace_order_unknown_broker_order_id_fails_closed(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(KisOrderRejectedError, match="unknown_broker_order_id"):
        broker.replace_order("missing", _broker_order())


def test_replace_order_runs_preflight_first(settings):
    broker = _authenticated_broker(settings)
    _seed_history(broker)
    with pytest.raises(KisOrderRejectedError, match="quantity_invalid"):
        broker.replace_order("missing", _broker_order(quantity=0))


def test_replace_order_blocked_by_live_trading(settings):
    broker = _authenticated_broker(settings, live_trading_enabled=True)
    entry = _seed_history(broker)
    with pytest.raises(KisOrderRejectedError, match="live_trading_enabled"):
        broker.replace_order(entry.broker_order_id or "", _broker_order())


def test_replace_order_blocked_by_market_order_type(settings):
    broker = _authenticated_broker(settings)
    entry = _seed_history(broker)
    with pytest.raises(KisOrderRejectedError, match="order_type_not_limit"):
        broker.replace_order(entry.broker_order_id or "", _broker_order(order_type=OrderType.MARKET))


def test_replace_order_blocked_by_allow_market_orders(settings):
    broker = _authenticated_broker(settings, allow_market_orders=True)
    entry = _seed_history(broker)
    with pytest.raises(KisOrderRejectedError, match="market_orders_allowed_flag_set"):
        broker.replace_order(entry.broker_order_id or "", _broker_order())


def test_replace_order_symbol_mismatch_fails_closed(settings):
    broker = _authenticated_broker(settings)
    entry = _seed_history(broker)
    broker._order_transport = RaiseOnCallOrderTransport()
    with pytest.raises(KisOrderRejectedError, match="symbol_mismatch"):
        broker.replace_order(entry.broker_order_id or "", _broker_order(symbol="MSFT"))
    assert broker._order_transport.calls == []


def test_replace_order_side_mismatch_fails_closed(settings):
    broker = _authenticated_broker(settings)
    entry = _seed_history(broker)
    broker._order_transport = RaiseOnCallOrderTransport()
    with pytest.raises(KisOrderRejectedError, match="side_mismatch"):
        broker.replace_order(entry.broker_order_id or "", _broker_order(side=Side.SELL))
    assert broker._order_transport.calls == []


def test_replace_order_dry_run_returns_dry_run_ack_without_http(settings):
    broker = _authenticated_broker(settings, kis_order_dry_run=True)
    entry = _seed_history(broker)
    broker._order_transport = RaiseOnCallOrderTransport()

    ack = broker.replace_order(entry.broker_order_id or "", _broker_order(quantity=8, limit_price=Decimal("101.25")))

    assert ack.status == "dry_run"
    assert ack.broker_order_id is None
    assert broker.last_order_preview is not None
    assert broker.last_order_preview.payload_sanitized["operation"] == "replace"
    assert broker._order_transport.calls == []


def test_replace_order_dry_run_disabled_requires_authentication(settings):
    broker = KisBroker(_settings(settings))
    entry = _seed_history(broker)
    with pytest.raises(KisOrderRejectedError, match="authentication_required"):
        broker.replace_order(entry.broker_order_id or "", _broker_order())


def test_replace_order_dry_run_disabled_mock_mode_fails_closed(settings):
    broker = _authenticated_broker(settings, kis_api_mode="mock")
    entry = _seed_history(broker)
    with pytest.raises(KisOrderRejectedError, match="mock_mode_no_network"):
        broker.replace_order(entry.broker_order_id or "", _broker_order())


def test_replace_order_happy_path(settings):
    broker = _authenticated_broker(settings)
    entry = _seed_history(broker)
    broker._order_transport = FakeOrderTransport([_success_response(odno="NEW_ODNO_999")])

    ack = broker.replace_order(
        entry.broker_order_id or "",
        _broker_order(quantity=8, limit_price=Decimal("101.25")),
    )

    assert ack.status == "replacement_submitted"
    assert ack.broker_order_id == "NEW_ODNO_999"
    call = broker._order_transport.calls[0]
    assert call["tr_id"] == KIS_PAPER_CANCEL_REPLACE_TR_ID_US
    assert call["path"] == KIS_OVERSEAS_CANCEL_REPLACE_PATH
    assert call["body"]["RVSE_CNCL_DVSN_CD"] == KIS_RVSE_CNCL_DVSN_REPLACE
    assert call["body"]["ORD_QTY"] == "8"
    assert call["body"]["OVRS_ORD_UNPR"] == "101.25"


def test_replace_order_preserves_old_history_entry(settings):
    broker = _authenticated_broker(settings)
    old = _seed_history(broker)
    broker._order_transport = FakeOrderTransport([_success_response(odno="NEW_ODNO_999")])

    broker.replace_order(old.broker_order_id or "", _broker_order(quantity=8, limit_price=Decimal("101.25")))

    stored = broker._order_history[old.broker_order_id or ""]
    assert stored.status == "replaced"
    assert stored.replacement_broker_order_id == "NEW_ODNO_999"
    assert stored.replaces_broker_order_id is None
    assert stored.broker_order_id == old.broker_order_id


def test_replace_order_creates_new_history_entry(settings):
    broker = _authenticated_broker(settings)
    old = _seed_history(broker)
    broker._order_transport = FakeOrderTransport([_success_response(odno="NEW_ODNO_999")])

    broker.replace_order(old.broker_order_id or "", _broker_order(quantity=8, limit_price=Decimal("101.25")))

    new = broker._order_history["NEW_ODNO_999"]
    assert new.status == "replacement_submitted"
    assert new.replaces_broker_order_id == old.broker_order_id
    assert new.replacement_broker_order_id is None
    assert new.symbol == old.symbol
    assert new.side == old.side
    assert new.exchange == old.exchange
    assert new.quantity == 8
    assert new.limit_price == Decimal("101.25")
    assert broker.last_order_response == new


def test_replace_order_does_not_overwrite_old_id(settings):
    broker = _authenticated_broker(settings)
    old = _seed_history(broker)
    broker._order_transport = FakeOrderTransport([_success_response(odno="NEW_ODNO_999")])

    broker.replace_order(old.broker_order_id or "", _broker_order(quantity=8, limit_price=Decimal("101.25")))

    assert old.broker_order_id in broker._order_history
    assert broker._order_history[old.broker_order_id or ""].broker_order_id == old.broker_order_id
    assert broker._order_history[old.broker_order_id or ""].broker_order_id != "NEW_ODNO_999"


def test_replace_order_chained_replace_works(settings):
    broker = _authenticated_broker(settings)
    old = _seed_history(broker)
    broker._order_transport = FakeOrderTransport(
        [
            _success_response(odno="NEW_ODNO_222"),
            _success_response(odno="NEW_ODNO_333"),
        ]
    )

    ack2 = broker.replace_order(old.broker_order_id or "", _broker_order(quantity=8, limit_price=Decimal("101.25")))
    ack3 = broker.replace_order(ack2.broker_order_id or "", _broker_order(quantity=6, limit_price=Decimal("102.25"), oms_id="oms-2"))

    assert set(broker._order_history) == {"OLD_ODNO_111", "NEW_ODNO_222", "NEW_ODNO_333"}
    assert broker._order_history["OLD_ODNO_111"].status == "replaced"
    assert broker._order_history["OLD_ODNO_111"].replacement_broker_order_id == "NEW_ODNO_222"
    assert broker._order_history["NEW_ODNO_222"].status == "replaced"
    assert broker._order_history["NEW_ODNO_222"].replacement_broker_order_id == "NEW_ODNO_333"
    assert broker._order_history["NEW_ODNO_222"].replaces_broker_order_id == "OLD_ODNO_111"
    assert broker._order_history[ack3.broker_order_id or ""].status == "replacement_submitted"
    assert broker._order_history[ack3.broker_order_id or ""].replaces_broker_order_id == "NEW_ODNO_222"


def test_replace_order_kis_rejection_propagates(settings):
    broker = _authenticated_broker(settings)
    entry = _seed_history(broker)
    broker._order_transport = FakeOrderTransport([{"rt_cd": "1", "msg_cd": "EGW002", "msg1": "no"}])

    with pytest.raises(KisOrderRejectedError, match="kis_error:EGW002"):
        broker.replace_order(entry.broker_order_id or "", _broker_order())


def test_replace_order_malformed_response_fails_closed_missing_rt_cd(settings):
    broker = _authenticated_broker(settings)
    entry = _seed_history(broker)
    broker._order_transport = FakeOrderTransport([{"output": {"ODNO": "NEW_ODNO_999"}}])

    with pytest.raises(KisOrderRejectedError, match="malformed_response"):
        broker.replace_order(entry.broker_order_id or "", _broker_order())


def test_replace_order_malformed_response_fails_closed_missing_odno(settings):
    broker = _authenticated_broker(settings)
    entry = _seed_history(broker)
    broker._order_transport = FakeOrderTransport([{"rt_cd": "0", "output": {}}])

    with pytest.raises(KisOrderRejectedError, match="malformed_response"):
        broker.replace_order(entry.broker_order_id or "", _broker_order())


def test_urllib_order_transport_rejects_live_cancel_tr_id():
    transport = UrllibOrderTransport()
    with pytest.raises(KisOrderRejectedError, match="disallowed_tr_id"):
        transport.submit_order(**_transport_kwargs(tr_id="TTTS" + "1003U"))


def test_urllib_order_transport_rejects_path_tr_id_mismatch_order_to_rvsecncl():
    transport = UrllibOrderTransport()
    with pytest.raises(KisOrderRejectedError, match="path_tr_id_mismatch"):
        transport.submit_order(**_transport_kwargs(tr_id=KIS_PAPER_ORDER_TR_ID_US_BUY, path=KIS_OVERSEAS_CANCEL_REPLACE_PATH))


def test_urllib_order_transport_rejects_path_tr_id_mismatch_rvsecncl_to_order():
    transport = UrllibOrderTransport()
    with pytest.raises(KisOrderRejectedError, match="path_tr_id_mismatch"):
        transport.submit_order(**_transport_kwargs(path=KIS_OVERSEAS_ORDER_PATH))


def test_urllib_order_transport_rejects_invalid_rvse_cncl_dvsn():
    transport = UrllibOrderTransport()
    body = dict(_transport_kwargs()["body"])
    body["RVSE_CNCL_DVSN_CD"] = "03"
    with pytest.raises(KisOrderRejectedError, match="invalid_rvse_cncl_dvsn"):
        transport.submit_order(**_transport_kwargs(body=body))


def test_urllib_order_transport_rejects_non_us_exchange_for_cancel():
    transport = UrllibOrderTransport()
    body = dict(_transport_kwargs()["body"])
    body["OVRS_EXCG_CD"] = "LSE"
    with pytest.raises(KisOrderRejectedError, match="invalid_exchange"):
        transport.submit_order(**_transport_kwargs(body=body))


def test_cancel_order_rejects_non_us_exchange_in_history(settings):
    broker = _authenticated_broker(settings)
    entry = _seed_history(broker, exchange="LSE")
    with pytest.raises(KisOrderRejectedError, match="invalid_exchange"):
        broker.cancel_order(entry.broker_order_id or "")


def test_replace_order_rejects_non_us_exchange_in_history(settings):
    broker = _authenticated_broker(settings)
    entry = _seed_history(broker, exchange="LSE")
    with pytest.raises(KisOrderRejectedError, match="invalid_exchange"):
        broker.replace_order(entry.broker_order_id or "", _broker_order())


def test_kis_module_does_not_introduce_live_cancel_replace_tr_ids():
    text = (pathlib.Path(__file__).resolve().parents[1] / "app" / "broker" / "kis.py").read_text(encoding="utf-8")
    for forbidden in ("TTTT" + "1004U", "TTTS" + "1003U", "TTTS" + "0309U"):
        assert forbidden not in text


def test_kis_module_does_not_introduce_asia_paper_cancel_replace_tr_ids():
    assert KIS_PAPER_CANCEL_REPLACE_TR_IDS == frozenset({"VTTT1004U"})
    assert len(KIS_PAPER_CANCEL_REPLACE_TR_IDS) == 1


def test_capabilities_unchanged_after_cancel_replace_implementation(settings):
    broker = KisBroker(_settings(settings))
    assert broker.capabilities() == {
        "submission": False,
        "cancel": False,
        "replace": False,
        "open_orders": False,
        "fills": False,
        "order_status": False,
    }


def test_healthcheck_order_execution_implemented_remains_false(settings):
    broker = KisBroker(_settings(settings))
    health = broker.healthcheck()
    assert health["order_execution_implemented"] is False
    assert health["order_methods_fail_closed"] is True


def test_get_open_orders_still_not_implemented_after_cancel_replace(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(NotImplementedError, match="get_open_orders"):
        broker.get_open_orders()


def test_get_fills_still_not_implemented_after_cancel_replace(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(NotImplementedError, match="get_fills"):
        broker.get_fills()


def test_get_order_status_still_not_implemented_after_cancel_replace(settings):
    broker = KisBroker(_settings(settings))
    with pytest.raises(NotImplementedError, match="get_order_status"):
        broker.get_order_status("any-id")


def test_cancel_replace_response_sanitization_redacts_secrets(settings):
    broker = _authenticated_broker(settings)
    cancel_entry = _seed_history(broker, broker_order_id="CANCEL_ODNO")
    replace_entry = _seed_history(broker, broker_order_id="REPLACE_ODNO")
    broker._order_transport = FakeOrderTransport(
        [
            _success_response(
                odno="CANCEL_ODNO",
                appkey="fake-key-XYZ",
                access_token="Bearer fake-access-token",
                output={"ODNO": "CANCEL_ODNO", "appsecret": "fake-secret-XYZ"},
            ),
            _success_response(
                odno="NEW_ODNO_999",
                appkey="fake-key-XYZ",
                access_token="Bearer fake-access-token",
                output={"ODNO": "NEW_ODNO_999", "appsecret": "fake-secret-XYZ"},
            ),
        ]
    )

    broker.cancel_order(cancel_entry.broker_order_id or "")
    broker.replace_order(replace_entry.broker_order_id or "", _broker_order(quantity=8, limit_price=Decimal("101.25")))
    rendered = json.dumps([entry.raw_response_sanitized for entry in broker._order_history.values()], sort_keys=True)

    for forbidden in ("fake-key-XYZ", "fake-secret-XYZ", "Bearer fake-access-token"):
        assert forbidden not in rendered


def test_cancel_replace_exceptions_and_repr_do_not_expose_secrets(settings):
    haystacks: list[str] = []
    broker = _authenticated_broker(settings)
    _seed_history(broker)
    haystacks.append(repr(broker))

    for action in (
        lambda: broker.cancel_order("missing"),
        lambda: broker.replace_order("missing", _broker_order()),
    ):
        with pytest.raises(KisOrderRejectedError) as exc_info:
            action()
        haystacks.append(str(exc_info.value))

    broker._order_transport = FakeOrderTransport([_success_response(odno="NEW_ODNO_999", access_token="fake-access-token")])
    broker.replace_order("OLD_ODNO_111", _broker_order(quantity=8, limit_price=Decimal("101.25")))
    haystacks.append(repr(list(broker._order_history.values())))
    haystacks.append(json.dumps([entry.raw_response_sanitized for entry in broker._order_history.values()], sort_keys=True))

    for forbidden in ("fake-key-XYZ", "fake-secret-XYZ", "12345678", "fake-access-token", "Bearer "):
        for haystack in haystacks:
            assert forbidden not in haystack


def test_mock_order_transport_signature_accepts_path():
    with pytest.raises(KisOrderRejectedError, match="mock_mode_no_network"):
        MockOrderTransport().submit_order(**_transport_kwargs())


def test_cancel_replace_exchange_allowlist_stays_us_only():
    assert KIS_PAPER_ORDER_EXCHANGES == frozenset({"NASD", "NYSE", "AMEX"})
