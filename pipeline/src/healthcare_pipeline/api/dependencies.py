from __future__ import annotations

from collections.abc import Generator
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from healthcare_pipeline.application.runtime import ApplicationRuntime


def get_request_session(request: Request) -> Generator[Session, None, None]:
    factory = cast(sessionmaker[Session], request.app.state.session_factory)
    session = factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_runtime(request: Request) -> ApplicationRuntime:
    return cast(ApplicationRuntime, request.app.state.runtime)


DatabaseSession = Annotated[Session, Depends(get_request_session)]
Runtime = Annotated[ApplicationRuntime, Depends(get_runtime)]
