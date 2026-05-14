from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.broker.paper import PaperBroker
from app.config import load_settings
from app.oms.manager import OMS
from app.risk.engine import RiskEngine
from app.runtime.paper_runner import PaperRunner
from app.strategy import create_strategy


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings = load_settings()
        risk = RiskEngine(settings)
        broker = PaperBroker()
        oms = OMS(settings, risk, broker)
        strategy = create_strategy("premarket_gap_volume_breakout", settings)

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
        app.state.broker = broker
        app.state.oms = oms
        app.state.strategy = strategy
        app.state.runner = PaperRunner(settings, strategy, oms)
        app.state.configured_brokers = configured_brokers
        app.state.kis_broker = kis_broker
        yield

    app = FastAPI(title="Paper Trading Runtime", lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()
