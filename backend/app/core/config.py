"""Application configuration using Pydantic settings.

All values can be overridden with environment variables (see .env.example).
"""
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Core ---
    PROJECT_NAME: str = "AI BI Platform"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)

    # --- Security ---
    SECRET_KEY: str = Field(default="change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # --- CORS ---
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # --- Database ---
    POSTGRES_USER: str = "biuser"
    POSTGRES_PASSWORD: str = "bipassword"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "aibi"
    DATABASE_URL: str | None = None

    # --- Uploads ---
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 100
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=["csv", "xlsx", "xls", "json"]
    )

    # --- LLM ---
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str | None = None
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: str | None = None

    @field_validator("BACKEND_CORS_ORIGINS", "ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @property
    def sqlalchemy_database_uri(self) -> str:
        """Return the effective SQLAlchemy database URI."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor used across the app."""
    return Settings()


settings = get_settings()
