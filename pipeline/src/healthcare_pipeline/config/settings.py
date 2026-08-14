from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[4]
ENV_FILE = PROJECT_ROOT / ".env"


def _secret_text(secret: SecretStr | None, name: str) -> str:
    if secret is None:
        raise RuntimeError(f"{name} is required")
    value = secret.get_secret_value().strip()
    if not value:
        raise RuntimeError(f"{name} must not be blank")
    if value.startswith("<") and value.endswith(">"):
        raise RuntimeError(f"{name} must not use a template placeholder")
    return value


class Settings(BaseSettings):
    """Typed process configuration loaded from the repository-root environment file."""

    app_env: Literal["local", "test", "dev", "staging", "prod", "production"] = "local"
    log_level: str = Field(default="INFO", min_length=1, max_length=16)
    database_url: str = Field(min_length=1)

    api_auth_token: SecretStr | None = None
    identity_hmac_secret: SecretStr | None = None
    identity_encryption_key_hex: SecretStr | None = None
    identity_encryption_key_id: str = Field(default="local-v1", min_length=1, max_length=64)

    max_hl7_payload_bytes: int = Field(default=2_097_152, ge=1024, le=16_777_216)
    identity_max_candidates: int = Field(default=100, ge=1, le=1000)
    api_host: str = Field(default="127.0.0.1", min_length=1, max_length=255)
    api_port: int = Field(default=8000, ge=1, le=65535)

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

    @property
    def api_docs_enabled(self) -> bool:
        return self.app_env in {"local", "test", "dev"}

    def require_api_auth_token(self) -> str:
        value = _secret_text(self.api_auth_token, "API_AUTH_TOKEN")
        if len(value) < 32:
            raise RuntimeError("API_AUTH_TOKEN must contain at least 32 characters")
        return value

    def require_identity_hmac_secret(self) -> bytes:
        value = _secret_text(self.identity_hmac_secret, "IDENTITY_HMAC_SECRET").encode()
        if len(value) < 32:
            raise RuntimeError("IDENTITY_HMAC_SECRET must contain at least 32 bytes")
        return value

    def require_identity_encryption_key(self) -> bytes:
        raw = _secret_text(
            self.identity_encryption_key_hex,
            "IDENTITY_ENCRYPTION_KEY_HEX",
        )
        try:
            key = bytes.fromhex(raw)
        except ValueError as exc:
            raise RuntimeError("IDENTITY_ENCRYPTION_KEY_HEX must be valid hexadecimal") from exc
        if len(key) != 32:
            raise RuntimeError("IDENTITY_ENCRYPTION_KEY_HEX must encode exactly 32 bytes")
        return key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return one cached Settings instance for the application process."""

    return Settings()  # type: ignore[call-arg]
