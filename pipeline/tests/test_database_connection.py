from sqlalchemy import text

from healthcare_pipeline.config.database import SessionFactory


def test_database_connection() -> None:
    with SessionFactory() as session:
        result = session.execute(text("SELECT 1")).scalar_one()

    assert result == 1