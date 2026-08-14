from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from healthcare_pipeline.config.settings import get_settings


def create_database_engine(database_url: str | None = None) -> Engine:
    """Create the shared engine with PostgreSQL pooling and SQLite test compatibility."""

    resolved_url = database_url or get_settings().database_url
    if make_url(resolved_url).get_backend_name() == "sqlite":
        return create_engine(
            resolved_url,
            pool_pre_ping=True,
            echo=False,
            connect_args={"check_same_thread": False},
        )
    return create_engine(
        resolved_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        echo=False,
    )


engine = create_database_engine()

SessionFactory = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def get_database_session() -> Generator[Session, None, None]:
    """Provide a database session and guarantee that it is closed."""

    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
