from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[4]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Typed application configuration loaded from environment variables."""

    app_env: str = Field(default="local")
    log_level: str = Field(default="INFO")
    database_url: str

    project_root: Path = Field(default=PROJECT_ROOT)

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def incoming_data_directory(self) -> Path:
        return self.project_root / "data" / "incoming"

    @property
    def processed_data_directory(self) -> Path:
        return self.project_root / "data" / "processed"

    @property
    def rejected_data_directory(self) -> Path:
        return self.project_root / "data" / "rejected"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return one cached Settings instance for the application process."""

    return Settings()