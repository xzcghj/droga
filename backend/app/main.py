"""Punkt wejścia aplikacji FastAPI."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import geocode, meetups, meta, participants
from app.api.errors import register_error_handlers
from app.config import Settings
from app.container import Container, build_container
from app.db.session import init_db, make_engine

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None, container: Container | None = None) -> FastAPI:
    settings = settings or Settings()
    container = container or build_container(settings)

    engine = make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        init_db(engine)
        yield

    app = FastAPI(title="Pół Drogi", version="1.0.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.container = container

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
        expose_headers=["Location"],
    )
    register_error_handlers(app)
    app.include_router(meta.router, prefix=API_PREFIX)
    app.include_router(meetups.router, prefix=API_PREFIX)
    app.include_router(participants.router, prefix=API_PREFIX)
    app.include_router(geocode.router, prefix=API_PREFIX)
    return app


app = create_app()
