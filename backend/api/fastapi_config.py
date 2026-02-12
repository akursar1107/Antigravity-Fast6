"""FastAPI Configuration and Settings Management"""
from functools import lru_cache
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """FastAPI application settings with environment variable support."""

    # App environment
    environment: str = "development"
    debug: bool = False

    # Database
    database_path: str = "data/fast6.db"

    # JWT Security
    secret_key: str = "dev-secret-key-change-in-production-use-env-var"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 days

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS Origins (comma-separated in env, e.g. CORS_ORIGINS=http://localhost:3000,https://app.example.com)
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8501",
        "http://localhost:8000",
    ]

    # NFL Configuration
    current_season: int = 2025
    current_week: int = 1

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return list(v) if v else []

    @model_validator(mode="after")
    def validate_production_secret(self) -> "Settings":
        if self.environment == "production" and "dev-secret" in self.secret_key.lower():
            raise ValueError(
                "SECRET_KEY must be set to a secure value in production. "
                "Use a long random string (e.g. openssl rand -hex 32)."
            )
        return self

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)"""
    return Settings()


# Default settings instance
settings = get_settings()
