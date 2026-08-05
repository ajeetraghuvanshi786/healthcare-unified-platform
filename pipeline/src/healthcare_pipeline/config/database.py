from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from healthcare_pipeline.config.settings import get_settings


def create_database_engine() -> Engine:
    """Create the shared SQLAlchemy database engine."""

    settings = get_settings()

    return create_engine(
        settings.database_url,
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