"""Unit tests for application configuration settings."""

import os
from typing import Generator
from unittest.mock import patch

import pytest

from techpulse.api.core.config import Settings, get_settings


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Remove TECHPULSE_ environment variables for clean test state."""
    env_vars = [k for k in os.environ if k.startswith("TECHPULSE_")]
    original_values = {k: os.environ.pop(k) for k in env_vars}
    get_settings.cache_clear()
    yield
    os.environ.update(original_values)
    get_settings.cache_clear()


class TestEnvironmentSetting:
    """Test suite for ENVIRONMENT configuration."""

    def test_environment_defaults_to_development(self, clean_env: None) -> None:
        """Verify environment defaults to development when not set."""
        settings = Settings()
        assert settings.environment == "development"

    def test_environment_reads_from_env_var(self, clean_env: None) -> None:
        """Verify environment reads from TECHPULSE_ENVIRONMENT."""
        with patch.dict(os.environ, {"TECHPULSE_ENVIRONMENT": "production"}):
            settings = Settings()
            assert settings.environment == "production"

    def test_environment_accepts_staging(self, clean_env: None) -> None:
        """Verify environment accepts staging value."""
        with patch.dict(os.environ, {"TECHPULSE_ENVIRONMENT": "staging"}):
            settings = Settings()
            assert settings.environment == "staging"


class TestLogLevelSetting:
    """Test suite for LOG_LEVEL configuration."""

    def test_log_level_defaults_to_info(self, clean_env: None) -> None:
        """Verify log_level defaults to INFO when not set."""
        settings = Settings()
        assert settings.log_level == "INFO"

    def test_log_level_reads_from_env_var(self, clean_env: None) -> None:
        """Verify log_level reads from TECHPULSE_LOG_LEVEL."""
        with patch.dict(os.environ, {"TECHPULSE_LOG_LEVEL": "DEBUG"}):
            settings = Settings()
            assert settings.log_level == "DEBUG"

    def test_log_level_accepts_warning(self, clean_env: None) -> None:
        """Verify log_level accepts WARNING value."""
        with patch.dict(os.environ, {"TECHPULSE_LOG_LEVEL": "WARNING"}):
            settings = Settings()
            assert settings.log_level == "WARNING"

    def test_log_level_accepts_error(self, clean_env: None) -> None:
        """Verify log_level accepts ERROR value."""
        with patch.dict(os.environ, {"TECHPULSE_LOG_LEVEL": "ERROR"}):
            settings = Settings()
            assert settings.log_level == "ERROR"

    def test_log_level_accepts_critical(self, clean_env: None) -> None:
        """Verify log_level accepts CRITICAL value."""
        with patch.dict(os.environ, {"TECHPULSE_LOG_LEVEL": "CRITICAL"}):
            settings = Settings()
            assert settings.log_level == "CRITICAL"


class TestLogJsonFormatSetting:
    """Test suite for LOG_JSON_FORMAT configuration."""

    def test_log_json_format_defaults_to_none(self, clean_env: None) -> None:
        """Verify log_json_format defaults to None for auto-detection."""
        settings = Settings()
        assert settings.log_json_format is None

    def test_log_json_format_reads_true_from_env(self, clean_env: None) -> None:
        """Verify log_json_format reads true from environment."""
        with patch.dict(os.environ, {"TECHPULSE_LOG_JSON_FORMAT": "true"}):
            settings = Settings()
            assert settings.log_json_format is True

    def test_log_json_format_reads_false_from_env(self, clean_env: None) -> None:
        """Verify log_json_format reads false from environment."""
        with patch.dict(os.environ, {"TECHPULSE_LOG_JSON_FORMAT": "false"}):
            settings = Settings()
            assert settings.log_json_format is False


class TestEffectiveLogJsonFormat:
    """Test suite for get_effective_log_json_format method."""

    def test_production_environment_returns_true(self, clean_env: None) -> None:
        """Verify production environment auto-detects to JSON format."""
        with patch.dict(os.environ, {"TECHPULSE_ENVIRONMENT": "production"}):
            settings = Settings()
            assert settings.get_effective_log_json_format() is True

    def test_development_environment_returns_false(self, clean_env: None) -> None:
        """Verify development environment auto-detects to console format."""
        settings = Settings()
        assert settings.get_effective_log_json_format() is False

    def test_staging_environment_returns_false(self, clean_env: None) -> None:
        """Verify staging environment auto-detects to console format."""
        with patch.dict(os.environ, {"TECHPULSE_ENVIRONMENT": "staging"}):
            settings = Settings()
            assert settings.get_effective_log_json_format() is False

    def test_explicit_true_overrides_environment(self, clean_env: None) -> None:
        """Verify explicit true overrides environment auto-detection."""
        with patch.dict(
            os.environ,
            {
                "TECHPULSE_ENVIRONMENT": "development",
                "TECHPULSE_LOG_JSON_FORMAT": "true",
            },
        ):
            settings = Settings()
            assert settings.get_effective_log_json_format() is True

    def test_explicit_false_overrides_production(self, clean_env: None) -> None:
        """Verify explicit false overrides production auto-detection."""
        with patch.dict(
            os.environ,
            {
                "TECHPULSE_ENVIRONMENT": "production",
                "TECHPULSE_LOG_JSON_FORMAT": "false",
            },
        ):
            settings = Settings()
            assert settings.get_effective_log_json_format() is False
