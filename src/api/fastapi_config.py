"""FastAPI Configuration and Settings Management"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from datetime import timedelta


class Settings(BaseSettings):
    """FastAPI application settings with environment variable support"""
    
    # App environment
    environment: str = "development"
    debug: bool = True
    
    # Database
    database_path: str = "data/fast6.db"
    
    # JWT Security
    secret_key: str = "dev-secret-key-change-in-production-use-env-var"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 days (friend group style)
    
    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # CORS Origins
    cors_origins: list = [
        "http://localhost:3000",      # Next.js dev
        "http://localhost:8501",       # Streamlit (parallel development)
        "http://localhost:8000",       # FastAPI itself
        "https://fast6.vercel.app",    # Vercel deployment
    ]
    
    # NFL Configuration
    current_season: int = 2025
    current_week: int = 1
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)"""
    return Settings()


# Default settings instance
settings = get_settings()
