from functools import lru_cache
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "CodeAtlas API"
    version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"

    database_url: str = "postgresql+asyncpg://codeatlas:codeatlas_dev@localhost:5432/codeatlas"
    database_url_sync: str = "postgresql+psycopg2://codeatlas:codeatlas_dev@localhost:5432/codeatlas"
    database_pool_size: int = 20
    database_max_overflow: int = 40

    redis_url: str = "redis://localhost:6379/0"
    use_celery: bool = False
    celery_worker_concurrency: int = 4

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "codeatlas"

    ollama_url: str = "http://localhost:11434"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_chat_model: str = "codellama:7b"

    github_app_id: str = "123456"
    github_app_private_key_path: str = "./private-key.pem"
    github_webhook_secret: str = "change-me-webhook-secret"
    github_client_id: str = ""
    github_client_secret: str = ""

    jwt_secret: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "RS256"
    jwt_private_key_path: str = ""
    jwt_access_expiry_minutes: int = 30
    jwt_refresh_expiry_days: int = 30
    jwt_issuer: str = "https://auth.codeatlas.dev"
    jwt_audience: str = "codeatlas-api"

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    ingestion_retry_max: int = 3
    ingestion_retry_base_delay: int = 5
    ingestion_timeout_seconds: int = 600

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v or not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError(
                "DATABASE_URL must be a valid PostgreSQL connection URI (e.g. postgresql+asyncpg://...)"
            )
        return v

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        if not v or not v.startswith(("redis://", "rediss://")):
            raise ValueError("REDIS_URL must be a valid Redis connection URI (e.g. redis://...)")
        return v

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.environment == "production":
            insecure_jwt = not self.jwt_secret or self.jwt_secret == "change-me-to-a-long-random-string"
            no_rsa_key = not self.jwt_private_key_path or not Path(self.jwt_private_key_path).exists()
            if insecure_jwt and no_rsa_key:
                raise ValueError(
                    "Production requires a secure non-default JWT_SECRET or a valid JWT_PRIVATE_KEY_PATH"
                )

            if not self.github_webhook_secret or self.github_webhook_secret == "change-me-webhook-secret":
                raise ValueError("Production requires a non-default GITHUB_WEBHOOK_SECRET")

        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def private_key(self) -> str | None:
        path = Path(self.github_app_private_key_path)
        if path.exists():
            return path.read_text()
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
