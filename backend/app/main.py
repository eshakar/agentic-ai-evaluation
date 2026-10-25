from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes import health
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.store import close_storage, init_storage


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_storage()  # connect to MongoDB (or fall back to files)
    yield
    await close_storage()


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title="Agentic AI Evaluation",
        description="Run agents over eval sets; score outputs, tool trajectories and quality.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(api_router)
    return app


app = create_app()
