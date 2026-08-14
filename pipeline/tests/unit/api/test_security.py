import pytest
from pydantic import SecretStr

from healthcare_pipeline.config.settings import Settings


def test_security_secrets_have_no_insecure_default() -> None:
    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        api_auth_token=None,
        identity_hmac_secret=None,
        identity_encryption_key_hex=None,
        _env_file=None,
    )
    with pytest.raises(RuntimeError, match="API_AUTH_TOKEN"):
        settings.require_api_auth_token()
    with pytest.raises(RuntimeError, match="IDENTITY_HMAC_SECRET"):
        settings.require_identity_hmac_secret()
    with pytest.raises(RuntimeError, match="IDENTITY_ENCRYPTION_KEY_HEX"):
        settings.require_identity_encryption_key()


def test_security_rejects_template_placeholders() -> None:
    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        api_auth_token=SecretStr("<generate-at-least-32-random-characters>"),
        identity_hmac_secret=SecretStr("<generate-at-least-32-random-characters>"),
        identity_encryption_key_hex=SecretStr("<generate-exactly-64-hex-characters>"),
        _env_file=None,
    )
    with pytest.raises(RuntimeError, match="template placeholder"):
        settings.require_api_auth_token()
    with pytest.raises(RuntimeError, match="template placeholder"):
        settings.require_identity_hmac_secret()
    with pytest.raises(RuntimeError, match="template placeholder"):
        settings.require_identity_encryption_key()
