"""KIS Open API broker adapter skeleton.

This module only implements configuration validation, token/account state
helpers, masking, and static health checks. KIS HTTP calls are intentionally
not implemented until endpoints, TR IDs, payloads, and response shapes are
confirmed from official KIS Open API documentation.
"""

from datetime import datetime, timezone
from typing import Any

from app.config import Settings
from app.domain.enums import TradingMode
from app.domain.orders import BrokerOrder, OrderAck


class KisError(Exception):
    """Base for KIS adapter errors."""


class KisConfigError(KisError):
    """Configuration missing/invalid."""


class KisAuthError(KisError):
    """Authentication/token error."""


class KisDataUnavailableError(KisError):
    """Market data unavailable or stale."""


class KisAuthClient:
    """KIS authentication token lifecycle state machine.

    Network calls are not implemented in this phase. The local token state is
    testable without HTTP.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.kis_app_key or not settings.kis_app_secret:
            raise KisConfigError("KIS_APP_KEY / KIS_APP_SECRET missing in .env")
        self._settings = settings
        self._access_token: str | None = None
        self._expires_at: datetime | None = None
        self._last_error: str | None = None

    def __repr__(self) -> str:
        token_state = "<set>" if self._access_token else "<unset>"
        return f"KisAuthClient(env={self._settings.kis_env!r}, token={token_state})"

    def is_authenticated(self) -> bool:
        if not self._access_token or not self._expires_at:
            return False
        return datetime.now(timezone.utc) < self._expires_at

    def get_access_token(self) -> str | None:
        if self.is_authenticated():
            return self._access_token
        return None

    def clear_token(self) -> None:
        self._access_token = None
        self._expires_at = None

    def authenticate(self) -> None:
        raise NotImplementedError(
            "KIS authenticate(): TODO — confirm OAuth/token endpoint, payload, and response shape "
            "from KIS Open API official documentation. Do not invent endpoints."
        )

    def refresh_token(self) -> None:
        raise NotImplementedError(
            "KIS refresh_token(): TODO — confirm refresh endpoint and payload from KIS Open API "
            "official documentation. Do not invent endpoints."
        )

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

    def get_account(self) -> dict[str, Any]:
        raise NotImplementedError(
            "KIS get_account(): TODO — confirm account endpoint, TR ID, payload, and response shape "
            "from KIS Open API official documentation. Do not invent endpoints."
        )

    def get_positions(self) -> dict[str, int]:
        raise NotImplementedError(
            "KIS get_positions(): TODO — confirm positions endpoint, TR ID, payload, and response shape "
            "from KIS Open API official documentation. Do not invent endpoints."
        )

    def get_cash_balance(self) -> dict[str, Any]:
        raise NotImplementedError(
            "KIS get_cash_balance(): TODO — confirm balance endpoint, TR ID, payload, and response shape "
            "from KIS Open API official documentation. Do not invent endpoints."
        )

    @property
    def last_error(self) -> str | None:
        return self._last_error


class KisMarketDataClient:
    """KIS market data query skeleton."""

    def __init__(self, settings: Settings, auth: KisAuthClient) -> None:
        self._settings = settings
        self._auth = auth
        self._last_error: str | None = None

    def __repr__(self) -> str:
        return "KisMarketDataClient(<disconnected>)"

    def get_quote(self, symbol: str) -> dict[str, Any]:
        raise NotImplementedError(
            "KIS get_quote(): TODO — confirm market data endpoint, TR ID, payload, and response shape "
            "from KIS Open API official documentation. Do not invent endpoints."
        )

    def get_last_price(self, symbol: str) -> Any:
        raise NotImplementedError(
            "KIS get_last_price(): TODO — confirm market data endpoint, TR ID, payload, and response shape "
            "from KIS Open API official documentation. Do not invent endpoints."
        )

    def healthcheck_market_data(self) -> dict[str, Any]:
        return {
            "connected": False,
            "reason": "skeleton — KIS Open API market data HTTP calls not implemented in this phase",
            "auth_required": True,
            "auth_present": self._auth.is_authenticated(),
        }

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
        return self._account.get_positions()

    def get_quote(self, symbol: str) -> dict[str, Any]:
        return self._market_data.get_quote(symbol)

    def get_open_orders(self) -> list[OrderAck]:
        raise NotImplementedError(
            "KIS get_open_orders(): TODO — confirm open-orders endpoint, TR ID, payload, and response shape "
            "from KIS Open API official documentation. Do not invent endpoints."
        )

    def place_order(self, broker_order: BrokerOrder) -> OrderAck:
        raise NotImplementedError(
            "KIS place_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard."
        )

    def cancel_order(self, broker_order_id: str) -> None:
        raise NotImplementedError("KIS cancel_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard.")

    def replace_order(self, broker_order_id: str, broker_order: BrokerOrder) -> OrderAck:
        raise NotImplementedError("KIS replace_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard.")

    def healthcheck(self) -> dict[str, Any]:
        market = self._market_data.healthcheck_market_data()
        return {
            "broker": "KisBroker",
            "environment": self._settings.kis_env,
            "config_loaded": True,
            "authenticated": self._auth.is_authenticated(),
            "account_loaded": self._account.is_loaded(),
            "market_data": market,
            "last_error": self._last_error,
            "order_execution_implemented": False,
        }

    def submit(self, broker_order: BrokerOrder) -> OrderAck:
        return self.place_order(broker_order)

    def cancel(self, broker_order_id: str) -> None:
        return self.cancel_order(broker_order_id)

    def open_orders(self) -> list[OrderAck]:
        return self.get_open_orders()

    def positions(self) -> dict[str, int]:
        return self.get_positions()
