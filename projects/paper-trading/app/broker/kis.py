"""KIS Open API broker adapter skeleton.

This module only implements configuration validation, token/account state
helpers, masking, and static health checks. KIS HTTP calls are intentionally
not implemented until endpoints, TR IDs, payloads, and response shapes are
confirmed from official KIS Open API documentation.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from app.config import Settings
from app.broker.kis_http import (
    KisApiMode,
    KisAuthError,
    KisConfigError,
    KisHttpError,
    SafeKisHttpClient,
)
from app.broker.kis_token_cache import (
    FileTokenCache,
    InMemoryTokenCache,
    TokenCache,
    TokenRecord,
)
from app.domain.enums import OrderType, Side, TradingMode
from app.domain.orders import BrokerOrder, OrderAck


class KisError(Exception):
    """Base for KIS adapter errors."""


class KisDataUnavailableError(KisError):
    """Market data unavailable or stale."""


class KisOrderRejectedError(KisError):
    """Order rejected by KIS adapter pre-flight guard."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"KIS order rejected: {reason}")
        self.reason = reason


@dataclass(frozen=True)
class KisPosition:
    symbol: str
    quantity: int
    avg_price: Decimal
    market_value: Decimal


@dataclass(frozen=True)
class KisCashBalance:
    currency: str
    cash: Decimal
    withdrawable_cash: Decimal


@dataclass(frozen=True)
class KisDryRunPreview:
    request: "KisOrderRequest"
    payload_sanitized: dict[str, Any]


class KisHttpClient:
    """HTTP boundary for future KIS calls.

    Endpoint paths, TR IDs, and payload shapes are intentionally absent until
    verified from official KIS documentation.
    """

    def __init__(self, settings: Settings, timeout_seconds: float = 5.0, max_retries: int = 1) -> None:
        self._settings = settings
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def request(self, method: str, path: str, headers: dict[str, Any] | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError(
            "KIS HTTP request(): official KIS endpoint path, TR ID, headers, and payload are required"
        )

    def sanitized_preview(self, payload: dict[str, Any] | None) -> dict[str, Any]:
        return sanitize_kis_response(payload or {}, self._settings)


@dataclass(frozen=True)
class KisOrderRequest:
    """Internal KIS order request model with no raw account number."""

    symbol: str
    market: str
    side: Side
    quantity: int
    order_type: OrderType
    limit_price: Decimal
    extended_hours: bool
    account_no_masked: str
    broker_environment: str
    idempotency_key: str


@dataclass(frozen=True)
class KisOrderResponse:
    """Internal KIS order response model with sanitized raw broker response."""

    internal_order_id: str
    broker_order_id: str | None
    broker: str
    status: str
    submitted_at: datetime
    symbol: str
    side: Side
    quantity: int
    limit_price: Decimal
    raw_response_sanitized: dict[str, Any]


SENSITIVE_RESPONSE_KEYS = {
    "app_key",
    "appkey",
    "appsecret",
    "app_secret",
    "account_no",
    "accountno",
    "cano",
    "acct_no",
    "access_token",
    "accesstoken",
    "authorization",
    "tr_key",
    "trkey",
    "secret",
}


def sanitize_kis_response(raw: dict[str, Any] | None, settings: Settings) -> dict[str, Any]:
    """Return a copy of a KIS response with credentials/account values redacted."""
    if not isinstance(raw, dict):
        return {}

    sensitive_values = {
        value
        for value in (settings.kis_app_key, settings.kis_app_secret, settings.kis_account_no)
        if value
    }

    def sanitize_value(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: sanitize_field(key, nested) for key, nested in value.items()}
        if isinstance(value, list):
            return [sanitize_value(item) for item in value]
        if isinstance(value, str) and value in sensitive_values:
            return "<redacted>"
        return value

    def sanitize_field(key: str, value: Any) -> Any:
        normalized = key.replace("-", "_").lower()
        if normalized in SENSITIVE_RESPONSE_KEYS:
            return "<redacted>"
        return sanitize_value(value)

    return {key: sanitize_field(key, value) for key, value in raw.items()}


def _decimal_from(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value).replace(",", ""))


def _int_from(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(Decimal(str(value).replace(",", "")))


def _validate_paper_settings(settings: Settings) -> None:
    if settings.trading_mode != TradingMode.PAPER:
        raise KisOrderRejectedError("trading_mode_not_paper")
    if settings.live_trading_enabled:
        raise KisOrderRejectedError("live_trading_enabled")
    if settings.kis_env != "paper":
        raise KisOrderRejectedError("kis_env_not_paper")


def validate_kis_order_request(settings: Settings, broker_order: BrokerOrder) -> None:
    """Pre-flight guards for KIS order paths."""
    if settings.trading_mode != TradingMode.PAPER:
        raise KisOrderRejectedError("trading_mode_not_paper")
    if settings.live_trading_enabled:
        raise KisOrderRejectedError("live_trading_enabled")
    if settings.allow_market_orders:
        raise KisOrderRejectedError("market_orders_allowed_flag_set")
    if settings.kis_env != "paper":
        raise KisOrderRejectedError("kis_env_not_paper")
    if settings.kill_switch_engaged:
        raise KisOrderRejectedError("kill_switch_engaged")
    if broker_order.order_type not in (OrderType.LIMIT, OrderType.STOP_LIMIT):
        raise KisOrderRejectedError("order_type_not_limit")
    if broker_order.quantity is None or broker_order.quantity <= 0:
        raise KisOrderRejectedError("quantity_invalid")
    if broker_order.limit_price is None or broker_order.limit_price <= 0:
        raise KisOrderRejectedError("limit_price_invalid")
    if broker_order.quote_timestamp is None:
        raise KisOrderRejectedError("stale_quote")
    quote_age = (broker_order.submitted_at - broker_order.quote_timestamp).total_seconds()
    if quote_age > settings.premarket_max_quote_age_seconds:
        raise KisOrderRejectedError("stale_quote")


class KisAuthClient:
    """KIS authentication token lifecycle state machine.

    Network calls are not implemented in this phase. The local token state is
    testable without HTTP.
    """

    def __init__(
        self,
        settings: Settings,
        http: SafeKisHttpClient | None = None,
        token_cache: TokenCache | None = None,
    ) -> None:
        if not settings.kis_app_key or not settings.kis_app_secret:
            raise KisConfigError("KIS_APP_KEY / KIS_APP_SECRET missing in .env")
        self._settings = settings
        if token_cache is None:
            if settings.kis_token_cache_path and KisApiMode.parse(settings.kis_api_mode) is KisApiMode.PAPER:
                token_cache = FileTokenCache(settings.kis_token_cache_path)
            else:
                token_cache = InMemoryTokenCache()
        self._cache: TokenCache = token_cache
        if http is None:
            http = SafeKisHttpClient(settings=settings, token_cache=token_cache)
        self._http = http
        self._access_token: str | None = None
        self._expires_at: datetime | None = None
        self._last_error: str | None = None

    def __repr__(self) -> str:
        token_state = "<set>" if self._access_token else "<unset>"
        return f"KisAuthClient(env={self._settings.kis_env!r}, token={token_state})"

    def is_authenticated(self) -> bool:
        if not self._access_token or not self._expires_at:
            return False
        safety = max(0, self._settings.kis_token_expiry_safety_seconds)
        return datetime.now(timezone.utc) + timedelta(seconds=safety) < self._expires_at

    def get_access_token(self) -> str | None:
        if self.is_authenticated():
            return self._access_token
        return None

    def clear_token(self) -> None:
        self._access_token = None
        self._expires_at = None

    def token_expires_at_relative(self) -> str | None:
        if self._expires_at is None:
            return None
        remaining = int((self._expires_at - datetime.now(timezone.utc)).total_seconds())
        if remaining <= 0:
            return "expired"
        return f"in_{remaining}s"

    def _store_token(self, access_token: str, expires_in_seconds: int) -> None:
        if not access_token:
            raise KisAuthError("KIS access token missing")
        self._access_token = access_token
        self._expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
        self._last_error = None

    def authenticate(self) -> None:
        try:
            _validate_paper_settings(self._settings)
        except KisOrderRejectedError as exc:
            self._last_error = exc.reason
            raise KisAuthError(exc.reason) from exc
        mode = KisApiMode.parse(self._settings.kis_api_mode)
        if mode is KisApiMode.MOCK:
            self._last_error = "mock_mode_no_network"
            raise KisAuthError("mock_mode_no_network")
        cached = self._cache.get()
        safety = max(0, self._settings.kis_token_expiry_safety_seconds)
        if cached is not None and not cached.is_expiring_soon(safety):
            self._store_token(cached.access_token, cached.expires_in_seconds())
            return
        body = {
            "grant_type": "client_credentials",
            "appkey": self._settings.kis_app_key,
            "appsecret": self._settings.kis_app_secret,
        }
        headers = {"content-type": "application/json; charset=utf-8"}
        try:
            response = self._http.request("POST", "/oauth2/tokenP", headers=headers, payload=body)
        except (KisAuthError, KisHttpError) as exc:
            self._last_error = str(exc)
            raise
        access_token = response.get("access_token")
        token_type = response.get("token_type")
        expires_in = response.get("expires_in")
        if not isinstance(access_token, str) or not access_token:
            self._last_error = "invalid_token_response"
            raise KisAuthError("invalid_token_response")
        if token_type != "Bearer":
            self._last_error = "invalid_token_type"
            raise KisAuthError("invalid_token_type")
        if not isinstance(expires_in, int) or expires_in <= 0:
            self._last_error = "invalid_expires_in"
            raise KisAuthError("invalid_expires_in")
        self._store_token(access_token, int(expires_in))
        now = datetime.now(timezone.utc)
        assert self._expires_at is not None
        self._cache.set(TokenRecord(access_token=access_token, expires_at=self._expires_at, issued_at=now))

    def refresh_token(self) -> None:
        try:
            _validate_paper_settings(self._settings)
        except KisOrderRejectedError as exc:
            self._last_error = exc.reason
            raise KisAuthError(exc.reason) from exc
        self.clear_token()
        self._cache.clear()
        self.authenticate()

    def revoke(self) -> None:
        try:
            _validate_paper_settings(self._settings)
        except KisOrderRejectedError as exc:
            self._last_error = exc.reason
            raise KisAuthError(exc.reason) from exc
        token = self._access_token
        if not token:
            self._cache.clear()
            return
        body = {
            "appkey": self._settings.kis_app_key,
            "appsecret": self._settings.kis_app_secret,
            "token": token,
        }
        headers = {"content-type": "application/json; charset=utf-8"}
        try:
            self._http.request("POST", "/oauth2/revokeP", headers=headers, payload=body)
        finally:
            self.clear_token()
            self._cache.clear()

    @property
    def last_error(self) -> str | None:
        return self._last_error


class KisAccountClient:
    """KIS account/positions/cash query skeleton."""

    def __init__(self, settings: Settings, auth: KisAuthClient) -> None:
        if not settings.kis_account_no:
            raise KisConfigError("KIS_ACCOUNT_NO missing in .env")
        self._settings = settings
        self._auth = auth
        self._account_loaded = False
        self._positions_loaded = False
        self._cash_balance_loaded = False
        self._last_error: str | None = None

    def __repr__(self) -> str:
        return f"KisAccountClient(account={self.masked_account_no()})"

    def masked_account_no(self) -> str:
        account_no = self._settings.kis_account_no or ""
        if len(account_no) <= 4:
            return "***"
        return f"***{account_no[-4:]}"

    def is_loaded(self) -> bool:
        return self._account_loaded

    def positions_loaded(self) -> bool:
        return self._positions_loaded

    def cash_balance_loaded(self) -> bool:
        return self._cash_balance_loaded

    def _require_auth(self) -> None:
        if not self._auth.is_authenticated():
            self._last_error = "authentication_required"
            raise KisAuthError("KIS authentication required")

    def get_account(self) -> dict[str, Any]:
        self._require_auth()
        self._last_error = "official_kis_account_endpoint_required"
        raise NotImplementedError(
            "KIS get_account(): TODO — confirm account endpoint, TR ID, payload, and response shape "
            "from KIS Open API official documentation. Do not invent endpoints."
        )

    def get_positions(self) -> list[KisPosition]:
        self._require_auth()
        self._last_error = "official_kis_positions_endpoint_required"
        raise NotImplementedError(
            "KIS get_positions(): TODO — confirm positions endpoint, TR ID, payload, and response shape "
            "from KIS Open API official documentation. Do not invent endpoints."
        )

    def get_cash_balance(self) -> KisCashBalance:
        self._require_auth()
        self._last_error = "official_kis_cash_balance_endpoint_required"
        raise NotImplementedError(
            "KIS get_cash_balance(): TODO — confirm balance endpoint, TR ID, payload, and response shape "
            "from KIS Open API official documentation. Do not invent endpoints."
        )

    def parse_positions_response(self, raw: dict[str, Any]) -> list[KisPosition]:
        sanitized = sanitize_kis_response(raw, self._settings)
        rows = sanitized.get("positions") or sanitized.get("output") or []
        positions: list[KisPosition] = []
        if isinstance(rows, dict):
            rows = [rows]
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict):
                continue
            symbol = str(row.get("symbol") or row.get("pdno") or row.get("ticker") or "").upper()
            if not symbol:
                continue
            positions.append(
                KisPosition(
                    symbol=symbol,
                    quantity=_int_from(row.get("quantity") or row.get("qty") or row.get("hldg_qty")),
                    avg_price=_decimal_from(row.get("avg_price") or row.get("pchs_avg_pric")),
                    market_value=_decimal_from(row.get("market_value") or row.get("evlu_amt")),
                )
            )
        self._positions_loaded = True
        return positions

    def parse_cash_balance_response(self, raw: dict[str, Any]) -> KisCashBalance:
        sanitized = sanitize_kis_response(raw, self._settings)
        source = sanitized.get("cash") if isinstance(sanitized.get("cash"), dict) else sanitized
        balance = KisCashBalance(
            currency=str(source.get("currency") or source.get("crcy_cd") or "USD"),
            cash=_decimal_from(source.get("cash") or source.get("dnca_tot_amt")),
            withdrawable_cash=_decimal_from(source.get("withdrawable_cash") or source.get("nxdy_excc_amt")),
        )
        self._cash_balance_loaded = True
        return balance

    @property
    def last_error(self) -> str | None:
        return self._last_error


class KisMarketDataClient:
    """KIS market data query skeleton."""

    def __init__(self, settings: Settings, auth: KisAuthClient) -> None:
        self._settings = settings
        self._auth = auth
        self._http = KisHttpClient(settings)
        self._last_error: str | None = None

    def __repr__(self) -> str:
        return "KisMarketDataClient(<disconnected>)"

    def get_quote(self, symbol: str) -> dict[str, Any]:
        self._validate_symbol(symbol)
        if not self._auth.is_authenticated():
            self._last_error = "authentication_required"
            raise KisAuthError("KIS authentication required")
        self._last_error = "official_kis_quote_endpoint_required"
        raise NotImplementedError(
            "KIS get_quote(): TODO — confirm market data endpoint, TR ID, payload, and response shape "
            "from KIS Open API official documentation. Do not invent endpoints."
        )

    def get_last_price(self, symbol: str) -> Any:
        quote = self.get_quote(symbol)
        return quote.get("last_price")

    def healthcheck_market_data(self) -> dict[str, Any]:
        return {
            "connected": False,
            "available": False,
            "reason": "skeleton — KIS Open API market data HTTP calls not implemented in this phase",
            "auth_required": True,
            "auth_present": self._auth.is_authenticated(),
            "last_error": self._last_error,
        }

    def _validate_symbol(self, symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not normalized or not normalized.replace(".", "").isalnum():
            self._last_error = "invalid_symbol"
            raise KisDataUnavailableError("invalid_symbol")
        return normalized

    @property
    def last_error(self) -> str | None:
        return self._last_error


class KisBroker:
    """KIS Paper broker adapter skeleton.

    Order execution is intentionally not wired. OMS continues to use PaperBroker
    in this phase.
    """

    mode = TradingMode.PAPER

    def __init__(self, settings: Settings) -> None:
        env = settings.kis_env
        if env is None:
            raise RuntimeError("KIS_ENV missing in .env")
        if env != "paper":
            raise RuntimeError(
                f"KIS_ENV={env!r}: only 'paper' allowed in this phase; live env is disabled"
            )
        if not settings.kis_account_no:
            raise RuntimeError("KIS_ACCOUNT_NO missing in .env")
        if not settings.kis_app_key:
            raise RuntimeError("KIS_APP_KEY missing in .env")
        if not settings.kis_app_secret:
            raise RuntimeError("KIS_APP_SECRET missing in .env")
        self._settings = settings
        self._auth = KisAuthClient(settings)
        self._account = KisAccountClient(settings, self._auth)
        self._market_data = KisMarketDataClient(settings, self._auth)
        self._last_error: str | None = None
        self._last_order_preview: KisDryRunPreview | None = None

    def __repr__(self) -> str:
        return (
            f"KisBroker(env={self._settings.kis_env!r}, "
            f"account={self._account.masked_account_no()}, app_key=<set>, app_secret=<set>)"
        )

    @property
    def auth(self) -> KisAuthClient:
        return self._auth

    @property
    def account(self) -> KisAccountClient:
        return self._account

    @property
    def market_data(self) -> KisMarketDataClient:
        return self._market_data

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def authenticate(self) -> None:
        return self._auth.authenticate()

    def refresh_token(self) -> None:
        return self._auth.refresh_token()

    def get_account(self) -> dict[str, Any]:
        return self._account.get_account()

    def get_positions(self) -> dict[str, int]:
        positions = self._account.get_positions()
        return {position.symbol: position.quantity for position in positions}

    def get_quote(self, symbol: str) -> dict[str, Any]:
        return self._market_data.get_quote(symbol)

    def get_open_orders(self) -> list[OrderAck]:
        raise NotImplementedError(
            "KIS get_open_orders(): TODO — confirm open-orders endpoint, TR ID, payload, and response shape "
            "from KIS Open API official documentation. Do not invent endpoints."
        )

    def place_order(self, broker_order: BrokerOrder) -> OrderAck:
        validate_kis_order_request(self._settings, broker_order)
        request = self._to_kis_request(broker_order)
        if self._settings.kis_order_dry_run:
            self._last_order_preview = self._dry_run_preview(request)
            return OrderAck(
                oms_id=broker_order.oms_id,
                broker_order_id=None,
                status="dry_run",
                mode=self.mode,
            )
        self._last_error = "official_kis_order_endpoint_required"
        raise NotImplementedError(
            "KIS place_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard. "
            "Pre-flight passed but order endpoint HTTP transmission is intentionally not implemented until KIS Open API "
            "endpoints/TR IDs/payloads are confirmed from official documentation."
        )

    def cancel_order(self, broker_order_id: str) -> None:
        _validate_paper_settings(self._settings)
        if self._settings.allow_market_orders:
            raise KisOrderRejectedError("market_orders_allowed_flag_set")
        if self._settings.kill_switch_engaged:
            raise KisOrderRejectedError("kill_switch_engaged")
        self._last_error = "official_kis_cancel_endpoint_required"
        raise NotImplementedError("KIS cancel_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard.")

    def replace_order(self, broker_order_id: str, broker_order: BrokerOrder) -> OrderAck:
        validate_kis_order_request(self._settings, broker_order)
        self._to_kis_request(broker_order)
        raise NotImplementedError("KIS replace_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard.")

    def get_fills(self) -> list[OrderAck]:
        raise NotImplementedError(
            "KIS get_fills(): TODO — confirm fills endpoint, TR ID, payload, and response shape "
            "from KIS Open API official documentation. Do not invent endpoints."
        )

    def get_order_status(self, broker_order_id: str) -> dict[str, Any]:
        raise NotImplementedError(
            "KIS get_order_status(): TODO — confirm order status endpoint, TR ID, payload, and response shape "
            "from KIS Open API official documentation. Do not invent endpoints."
        )

    def capabilities(self) -> dict[str, bool]:
        return {
            "submission": False,
            "cancel": False,
            "replace": False,
            "open_orders": False,
            "fills": False,
            "order_status": False,
        }

    @property
    def last_order_preview(self) -> KisDryRunPreview | None:
        return self._last_order_preview

    def _idempotency_key_for(self, broker_order: BrokerOrder) -> str:
        return f"kis-paper-{broker_order.oms_id}"

    def _to_kis_request(self, broker_order: BrokerOrder) -> KisOrderRequest:
        return KisOrderRequest(
            symbol=broker_order.symbol,
            market="US",
            side=broker_order.side,
            quantity=broker_order.quantity,
            order_type=broker_order.order_type,
            limit_price=broker_order.limit_price,
            extended_hours=False,
            account_no_masked=self._account.masked_account_no(),
            broker_environment=self._settings.kis_env or "paper",
            idempotency_key=self._idempotency_key_for(broker_order),
        )

    def _dry_run_preview(self, request: KisOrderRequest) -> KisDryRunPreview:
        payload = {
            "symbol": request.symbol,
            "market": request.market,
            "side": request.side.value,
            "quantity": request.quantity,
            "order_type": request.order_type.value,
            "limit_price": str(request.limit_price),
            "account_no": request.account_no_masked,
            "idempotency_key": request.idempotency_key,
            "app_key": self._settings.kis_app_key,
        }
        return KisDryRunPreview(
            request=request,
            payload_sanitized=sanitize_kis_response(payload, self._settings),
        )

    def healthcheck(self) -> dict[str, Any]:
        market = self._market_data.healthcheck_market_data()
        return {
            "broker": "KisBroker",
            "environment": self._settings.kis_env,
            "config_loaded": True,
            "authenticated": self._auth.is_authenticated(),
            "token_expires_at": self._auth.token_expires_at_relative(),
            "account_loaded": self._account.is_loaded(),
            "positions_loaded": self._account.positions_loaded(),
            "cash_balance_loaded": self._account.cash_balance_loaded(),
            "market_data": market,
            "last_error": self._last_error,
            "order_execution_implemented": False,
            "order_methods_fail_closed": True,
            "order_dry_run": self._settings.kis_order_dry_run,
            "capabilities": self.capabilities(),
        }

    def submit(self, broker_order: BrokerOrder) -> OrderAck:
        return self.place_order(broker_order)

    def cancel(self, broker_order_id: str) -> None:
        return self.cancel_order(broker_order_id)

    def open_orders(self) -> list[OrderAck]:
        return self.get_open_orders()

    def positions(self) -> dict[str, int]:
        return self.get_positions()
