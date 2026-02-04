"""
Configuration settings for the Signal Transceiver application.
Uses Pydantic Settings for environment variable management.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = Field(default="Signal Transceiver", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    secret_key: str = Field(default="your-super-secret-key", env="SECRET_KEY")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/app.db",
        env="DATABASE_URL"
    )

    # API Settings
    api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Admin Settings
    admin_api_key: str = Field(default="admin-secret-key", env="ADMIN_API_KEY")

    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
