from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from healthcare_pipeline.api.middleware import RequestIdMiddleware
from healthcare_pipeline.api.routes.health import router as health_router
from healthcare_pipeline.api.routes.master_patients import router as identity_router
from healthcare_pipeline.api.routes.processing import router as processing_router
from healthcare_pipeline.application.runtime import ApplicationRuntime
from healthcare_pipeline.config.database import SessionFactory, create_database_engine
from healthcare_pipeline.config.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    custom_engine: Engine | None = None
    factory: sessionmaker[Session]

    if settings is None:
        factory = SessionFactory
    else:
        custom_engine = create_database_engine(resolved.database_url)
        factory = sessionmaker(
            bind=custom_engine,
            class_=Session,
            autoflush=False,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if custom_engine is not None:
            custom_engine.dispose()

    app = FastAPI(
        title="Healthcare Unified Platform API",
        version="0.1.0",
        docs_url="/docs" if resolved.api_docs_enabled else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = resolved
    app.state.runtime = ApplicationRuntime(resolved)
    app.state.session_factory = factory
    app.add_middleware(RequestIdMiddleware)
    app.include_router(health_router)
    app.include_router(processing_router)
    app.include_router(identity_router)
    return app


app = create_app()
