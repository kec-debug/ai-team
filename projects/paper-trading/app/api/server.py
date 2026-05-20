from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api.routes import router
from app.broker.paper import PaperBroker
from app.config import load_settings
from app.domain.enums import Session
from app.oms.manager import OMS
from app.portfolio import PortfolioService
from app.risk.engine import RiskEngine
from app.runtime.paper_runner import PaperRunner
from app.runtime.paper_engine import PaperEngine
from app.session import SessionRouter
from app.strategy import create_strategy


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings = load_settings()
        starting_cash = dict(
            settings.paper_starting_cash_by_currency
            or {settings.paper_base_currency: settings.paper_starting_cash}
        )
        project_dir = Path(__file__).resolve().parents[2]
        risk = RiskEngine(settings)
        broker = PaperBroker(
            max_quote_age_seconds=settings.paper_max_quote_age_seconds,
            allowed_sessions={Session(session) for session in settings.paper_allowed_sessions},
            max_fill_ratio_of_volume=settings.paper_max_fill_ratio_of_volume,
            commission_per_share=settings.paper_commission_per_share,
            commission_per_fill=settings.paper_commission_per_fill,
        )
        oms = OMS(settings, risk, broker)
        strategy = create_strategy("premarket_gap_volume_breakout", settings)
        session_router = SessionRouter()
        portfolio = PortfolioService()
        paper_engine = PaperEngine(settings, broker=broker, portfolio=portfolio)

        # Probe optional brokers — record which ones are instantiable given
        # current .env. The KIS adapter is never wired into OMS in this phase;
        # we only surface its configurability on /paper/status.
        configured_brokers: list[str] = []
        kis_broker = None
        try:
            from app.broker.kis import KisBroker

            kis_broker = KisBroker(settings)
            configured_brokers.append("KisBroker")
        except RuntimeError:
            pass

        app.state.settings = settings
        app.state.risk = risk
        app.state.broker = broker
        app.state.oms = oms
        app.state.strategy = strategy
        app.state.runner = PaperRunner(settings, strategy, oms)
        app.state.paper_engine = paper_engine
        app.state.paper_starting_cash = starting_cash
        app.state.project_dir = project_dir
        app.state.paper_last_error = None
        from app.runtime.dry_run import DryRunController

        app.state.dry_run_controller = DryRunController(settings, app.state.runner, project_dir)
        app.state.session_router = session_router
        app.state.portfolio = portfolio
        app.state.configured_brokers = configured_brokers
        app.state.kis_broker = kis_broker
        yield

    app = FastAPI(title="Paper Trading Runtime", lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()
