"""Application configuration using Pydantic BaseSettings.

This module provides type-safe configuration management through environment
variables with sensible defaults for local development.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings use the TECHPULSE_ prefix and can be overridden via
    environment variables. The settings are validated at startup to
    ensure type safety and provide clear error messages for
    misconfiguration.

    Attributes:
        db_path: Path to the DuckDB database file.
        api_host: Host address for the API server to bind to.
        api_port: Port number for the API server.
        log_format: Logging output format (json for production, console for dev).
        cors_origins: Comma-separated list of allowed CORS origins.
        redis_url: Redis connection URL for caching (Upstash).
        cache_ttl_seconds: Default TTL for cache entries in seconds.
        cache_lock_timeout_seconds: Lock expiry timeout for stampede prevention.
        cache_purge_api_key: API key for cache purge endpoint authentication.
    """

    model_config = SettingsConfigDict(
        env_prefix="TECHPULSE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_path: Path = Field(
        default=Path("data/techpulse.duckdb"),
        description="Path to the DuckDB database file.",
    )

    api_host: str = Field(
        default="0.0.0.0",
        description="Host address for the API server to bind to.",
    )

    api_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port number for the API server.",
    )

    log_format: Literal["json", "console"] = Field(
        default="console",
        description="Logging format: 'json' for production, 'console' for dev.",
    )

    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed CORS origins.",
    )

    redis_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("UPSTASH_REDIS_URL", "TECHPULSE_REDIS_URL"),
        description="Redis connection URL for caching (Upstash).",
    )

    cache_ttl_seconds: int = Field(
        default=86400,
        ge=1,
        description="Default TTL for cache entries in seconds.",
    )

    cache_lock_timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Lock expiry timeout for stampede prevention in seconds.",
    )

    cache_purge_api_key: str | None = Field(
        default=None,
        description="API key for cache purge endpoint authentication.",
    )

    def get_cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list.

        Returns:
            List of origin URLs stripped of whitespace.
        """
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Retrieve cached application settings.

    Uses LRU cache to ensure settings are loaded once and reused
    across the application lifecycle.

    Returns:
        Validated Settings instance.
    """
    return Settings()
