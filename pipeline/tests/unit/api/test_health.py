from fastapi.testclient import TestClient

from healthcare_pipeline.api.main import create_app
from healthcare_pipeline.config.settings import Settings


def test_liveness_is_public_and_does_not_require_database() -> None:
    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        _env_file=None,
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers
    assert response.headers["Cache-Control"] == "no-store"
