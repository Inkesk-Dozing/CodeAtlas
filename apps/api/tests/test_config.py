import pytest
from pydantic import ValidationError

from config import Settings, get_settings


def test_settings_default_development():
    settings = Settings()
    assert settings.environment == "development"
    assert settings.is_production is False
    assert settings.database_url.startswith("postgresql")
    assert settings.redis_url.startswith("redis")
    assert settings.version == "0.1.0"


def test_settings_cached_singleton():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_settings_invalid_database_url():
    with pytest.raises(ValidationError) as exc_info:
        Settings(database_url="sqlite:///test.db")
    assert "DATABASE_URL" in str(exc_info.value)


def test_settings_invalid_redis_url():
    with pytest.raises(ValidationError) as exc_info:
        Settings(redis_url="http://localhost:6379")
    assert "REDIS_URL" in str(exc_info.value)


def test_settings_production_requires_secure_secrets():
    with pytest.raises(ValidationError) as exc_info:
        Settings(environment="production")
    assert "JWT_SECRET" in str(exc_info.value)


def test_settings_production_valid_configuration(tmp_path):
    private_key_file = tmp_path / "private.pem"
    private_key_file.write_text("dummy-rsa-key")

    prod_settings = Settings(
        environment="production",
        jwt_secret="super-secure-production-secret-key-32chars",
        jwt_private_key_path=str(private_key_file),
        github_webhook_secret="super-secure-github-webhook-secret-production",
    )
    assert prod_settings.is_production is True
    assert prod_settings.environment == "production"
