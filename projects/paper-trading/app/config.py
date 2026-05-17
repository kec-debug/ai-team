import os
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dotenv import load_dotenv

from app.domain.enums import Session, TradingMode


TRUE_VALUES = {"true", "1", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    trading_mode: TradingMode = TradingMode.PAPER
    live_trading_enabled: bool = False
    alpaca_paper_api_base: str | None = None
    alpaca_paper_key_id: str | None = None
    alpaca_paper_secret_key: str | None = None
    paper_starting_cash: Decimal = Decimal("100000")
    max_order_notional_usd: Decimal = Decimal("5000")
    max_open_positions: int = 20
    symbol_allowlist: tuple[str, ...] = ()
    premarket_gap_min_pct: Decimal = Decimal("0.05")
    premarket_min_volume: int = 100_000
    premarket_max_spread_pct: Decimal = Decimal("0.003")
    premarket_max_quote_age_seconds: int = 60
    premarket_min_relative_volume: Decimal = Decimal("1.5")
    premarket_breakout_tolerance_pct: Decimal = Decimal("0.001")
    # KIS Open API (모의투자) — credentials are masked from repr.
    kis_env: str | None = None
    kis_account_no: str | None = field(default=None, repr=False)
    kis_app_key: str | None = field(default=None, repr=False)
    kis_app_secret: str | None = field(default=None, repr=False)
    allow_market_orders: bool = False
    kill_switch_engaged: bool = False
    kis_order_dry_run: bool = True
    dry_run_reports_dir: str = "reports/dry_run"
    dry_run_max_errors_before_auto_stop: int = 10
    dry_run_max_ticks: int | None = None
    kis_api_mode: str = "mock"
    kis_base_url_paper: str = "https://openapivts.koreainvestment.com:29443"
    kis_base_url_live: str = "https://openapi.koreainvestment.com:9443"
    kis_oauth_timeout_seconds: float = 5.0
    kis_oauth_max_retries: int = 1
    kis_token_expiry_safety_seconds: int = 60
    kis_token_cache_path: str | None = field(default=None, repr=False)


def _decimal_env(name: str, default: Decimal) -> Decimal:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal for {name}") from exc


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid integer for {name}") from exc


def _symbols(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    return tuple(symbol.strip().upper() for symbol in raw.split(",") if symbol.strip())


def _str_env(name: str) -> str | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    value = raw.strip()
    return value or None


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in TRUE_VALUES


def _project_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def load_settings() -> Settings:
    env_file = _project_dir() / ".env"
    if env_file.is_file():
        load_dotenv(dotenv_path=env_file, override=False)
    else:
        load_dotenv(override=False)
    mode = TradingMode(os.getenv("TRADING_MODE", TradingMode.PAPER.value).lower())
    if mode != TradingMode.PAPER:
        raise ValueError("Phase 1 only supports paper trading")

    live_enabled = os.getenv("LIVE_TRADING_ENABLED", "false").lower() in TRUE_VALUES
    if live_enabled:
        raise ValueError("Live trading is disabled in Phase 1")

    if _bool_env("ALLOW_MARKET_ORDERS", False):
        raise ValueError(
            "ALLOW_MARKET_ORDERS=true is rejected in this phase (market orders disabled)"
        )

    kis_api_mode = _str_env("KIS_API_MODE") or "mock"
    if kis_api_mode not in {"mock", "paper", "live"}:
        raise ValueError(f"invalid KIS_API_MODE: {kis_api_mode!r}")

    return Settings(
        trading_mode=mode,
        live_trading_enabled=live_enabled,
        alpaca_paper_api_base=os.getenv("ALPACA_PAPER_API_BASE") or None,
        alpaca_paper_key_id=os.getenv("ALPACA_PAPER_KEY_ID") or None,
        alpaca_paper_secret_key=os.getenv("ALPACA_PAPER_SECRET_KEY") or None,
        paper_starting_cash=_decimal_env("PAPER_STARTING_CASH", Decimal("100000")),
        max_order_notional_usd=_decimal_env("MAX_ORDER_NOTIONAL_USD", Decimal("5000")),
        max_open_positions=_int_env("MAX_OPEN_POSITIONS", 20),
        symbol_allowlist=_symbols(os.getenv("SYMBOL_ALLOWLIST")),
        premarket_gap_min_pct=_decimal_env("STRATEGY_PREMARKET_GAP_MIN_PCT", Decimal("0.05")),
        premarket_min_volume=_int_env("STRATEGY_PREMARKET_MIN_VOLUME", 100_000),
        premarket_max_spread_pct=_decimal_env("STRATEGY_PREMARKET_MAX_SPREAD_PCT", Decimal("0.003")),
        premarket_max_quote_age_seconds=_int_env("STRATEGY_PREMARKET_MAX_QUOTE_AGE_SECONDS", 60),
        premarket_min_relative_volume=_decimal_env("STRATEGY_PREMARKET_MIN_RELATIVE_VOLUME", Decimal("1.5")),
        premarket_breakout_tolerance_pct=_decimal_env("STRATEGY_PREMARKET_BREAKOUT_TOLERANCE_PCT", Decimal("0.001")),
        kis_env=_str_env("KIS_ENV"),
        kis_account_no=_str_env("KIS_ACCOUNT_NO"),
        kis_app_key=_str_env("KIS_APP_KEY"),
        kis_app_secret=_str_env("KIS_APP_SECRET"),
        allow_market_orders=False,
        kill_switch_engaged=_bool_env("KILL_SWITCH_ENGAGED", False),
        kis_order_dry_run=_bool_env("KIS_ORDER_DRY_RUN", True),
        dry_run_reports_dir=_str_env("DRY_RUN_REPORTS_DIR") or "reports/dry_run",
        dry_run_max_errors_before_auto_stop=_int_env("DRY_RUN_MAX_ERRORS_BEFORE_AUTO_STOP", 10),
        dry_run_max_ticks=(_int_env("DRY_RUN_MAX_TICKS", 0) or None) if os.getenv("DRY_RUN_MAX_TICKS") else None,
        kis_api_mode=kis_api_mode,
        kis_base_url_paper=_str_env("KIS_BASE_URL_PAPER") or "https://openapivts.koreainvestment.com:29443",
        kis_base_url_live=_str_env("KIS_BASE_URL_LIVE") or "https://openapi.koreainvestment.com:9443",
        kis_oauth_timeout_seconds=float(_str_env("KIS_OAUTH_TIMEOUT_SECONDS") or "5.0"),
        kis_oauth_max_retries=int(_str_env("KIS_OAUTH_MAX_RETRIES") or "1"),
        kis_token_expiry_safety_seconds=int(_str_env("KIS_TOKEN_EXPIRY_SAFETY_SECONDS") or "60"),
        kis_token_cache_path=_str_env("KIS_TOKEN_CACHE_PATH"),
    )
