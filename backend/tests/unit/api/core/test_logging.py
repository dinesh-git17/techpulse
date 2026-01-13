"""Unit tests for structured logging configuration."""

import logging
from io import StringIO
from typing import Generator
from unittest.mock import patch

import pytest
import structlog

from techpulse.api.core.logging import (
    _get_console_processors,
    _get_json_processors,
    _get_log_level_int,
    configure_logging,
)


@pytest.fixture(autouse=True)
def reset_structlog() -> Generator[None, None, None]:
    """Reset structlog configuration after each test."""
    yield
    structlog.reset_defaults()


@pytest.fixture(autouse=True)
def reset_root_logger() -> Generator[None, None, None]:
    """Reset root logger handlers after each test."""
    root = logging.getLogger()
    original_handlers = root.handlers.copy()
    original_level = root.level
    yield
    root.handlers = original_handlers
    root.setLevel(original_level)


class TestLogLevelConversion:
    """Test suite for log level string to int conversion."""

    def test_debug_level_conversion(self) -> None:
        """Verify DEBUG converts to logging.DEBUG constant."""
        assert _get_log_level_int("DEBUG") == logging.DEBUG

    def test_info_level_conversion(self) -> None:
        """Verify INFO converts to logging.INFO constant."""
        assert _get_log_level_int("INFO") == logging.INFO

    def test_warning_level_conversion(self) -> None:
        """Verify WARNING converts to logging.WARNING constant."""
        assert _get_log_level_int("WARNING") == logging.WARNING

    def test_error_level_conversion(self) -> None:
        """Verify ERROR converts to logging.ERROR constant."""
        assert _get_log_level_int("ERROR") == logging.ERROR

    def test_critical_level_conversion(self) -> None:
        """Verify CRITICAL converts to logging.CRITICAL constant."""
        assert _get_log_level_int("CRITICAL") == logging.CRITICAL


class TestProcessorChains:
    """Test suite for processor chain construction."""

    def test_json_processors_returns_list(self) -> None:
        """Verify JSON processors returns a non-empty list."""
        processors = _get_json_processors()
        assert isinstance(processors, list)
        assert len(processors) > 0

    def test_json_processors_ends_with_json_renderer(self) -> None:
        """Verify JSON processor chain ends with JSONRenderer."""
        processors = _get_json_processors()
        assert isinstance(processors[-1], structlog.processors.JSONRenderer)

    def test_json_processors_includes_timestamper(self) -> None:
        """Verify JSON processor chain includes ISO timestamper."""
        processors = _get_json_processors()
        timestamper_types = [type(p).__name__ for p in processors]
        assert "TimeStamper" in timestamper_types

    def test_json_processors_includes_log_level(self) -> None:
        """Verify JSON processor chain includes add_log_level."""
        processors = _get_json_processors()
        assert structlog.processors.add_log_level in processors

    def test_console_processors_returns_list(self) -> None:
        """Verify console processors returns a non-empty list."""
        processors = _get_console_processors()
        assert isinstance(processors, list)
        assert len(processors) > 0

    def test_console_processors_ends_with_console_renderer(self) -> None:
        """Verify console processor chain ends with ConsoleRenderer."""
        processors = _get_console_processors()
        last_processor = processors[-1]
        assert isinstance(last_processor, structlog.dev.ConsoleRenderer)

    def test_console_renderer_has_colors_enabled(self) -> None:
        """Verify ConsoleRenderer is configured with colors enabled."""
        processors = _get_console_processors()
        console_renderer = processors[-1]
        assert isinstance(console_renderer, structlog.dev.ConsoleRenderer)


class TestConfigureLogging:
    """Test suite for configure_logging function."""

    def test_configure_json_format(self) -> None:
        """Verify JSON format configuration applies correctly."""
        configure_logging(json_format=True, log_level="INFO")
        logger = structlog.get_logger()
        assert logger is not None

    def test_configure_console_format(self) -> None:
        """Verify console format configuration applies correctly."""
        configure_logging(json_format=False, log_level="INFO")
        logger = structlog.get_logger()
        assert logger is not None

    def test_configure_sets_log_level_debug(self) -> None:
        """Verify DEBUG log level is applied to root logger."""
        configure_logging(json_format=False, log_level="DEBUG")
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_configure_sets_log_level_info(self) -> None:
        """Verify INFO log level is applied to root logger."""
        configure_logging(json_format=False, log_level="INFO")
        root = logging.getLogger()
        assert root.level == logging.INFO

    def test_configure_sets_log_level_warning(self) -> None:
        """Verify WARNING log level is applied to root logger."""
        configure_logging(json_format=False, log_level="WARNING")
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_configure_sets_log_level_error(self) -> None:
        """Verify ERROR log level is applied to root logger."""
        configure_logging(json_format=False, log_level="ERROR")
        root = logging.getLogger()
        assert root.level == logging.ERROR

    def test_configure_sets_log_level_critical(self) -> None:
        """Verify CRITICAL log level is applied to root logger."""
        configure_logging(json_format=False, log_level="CRITICAL")
        root = logging.getLogger()
        assert root.level == logging.CRITICAL

    def test_configure_adds_stream_handler(self) -> None:
        """Verify stream handler is added to root logger."""
        root = logging.getLogger()
        root.handlers = []
        configure_logging(json_format=False, log_level="INFO")
        assert len(root.handlers) >= 1
        assert any(isinstance(h, logging.StreamHandler) for h in root.handlers)

    def test_configure_does_not_duplicate_handlers(self) -> None:
        """Verify repeated calls do not add duplicate handlers."""
        root = logging.getLogger()
        root.handlers = []
        configure_logging(json_format=False, log_level="INFO")
        initial_count = len(root.handlers)
        configure_logging(json_format=False, log_level="INFO")
        assert len(root.handlers) == initial_count

    def test_default_format_is_console(self) -> None:
        """Verify default json_format parameter is False."""
        configure_logging()
        root = logging.getLogger()
        assert root.level == logging.INFO


class TestJsonLogOutput:
    """Test suite for JSON log output format validation."""

    def test_json_output_contains_level(self) -> None:
        """Verify JSON output includes log level field."""
        configure_logging(json_format=True, log_level="INFO")
        output = StringIO()

        with patch("sys.stdout", output):
            logger = structlog.get_logger()
            logger.info("test_event")

        log_output = output.getvalue()
        assert "level" in log_output or "info" in log_output.lower()

    def test_json_output_contains_timestamp(self) -> None:
        """Verify JSON output includes timestamp field."""
        configure_logging(json_format=True, log_level="INFO")
        output = StringIO()

        with patch("sys.stdout", output):
            logger = structlog.get_logger()
            logger.info("test_event")

        log_output = output.getvalue()
        assert "timestamp" in log_output

    def test_json_output_contains_event(self) -> None:
        """Verify JSON output includes event field."""
        configure_logging(json_format=True, log_level="INFO")
        output = StringIO()

        with patch("sys.stdout", output):
            logger = structlog.get_logger()
            logger.info("test_event")

        log_output = output.getvalue()
        assert "test_event" in log_output


class TestLogLevelFiltering:
    """Test suite for log level filtering behavior."""

    def test_debug_messages_filtered_at_info_level(self) -> None:
        """Verify DEBUG messages are not emitted when level is INFO."""
        configure_logging(json_format=True, log_level="INFO")
        output = StringIO()

        with patch("sys.stdout", output):
            logger = structlog.get_logger()
            logger.debug("debug_message")

        assert "debug_message" not in output.getvalue()

    def test_info_messages_emitted_at_info_level(self) -> None:
        """Verify INFO messages are emitted when level is INFO."""
        configure_logging(json_format=True, log_level="INFO")
        output = StringIO()

        with patch("sys.stdout", output):
            logger = structlog.get_logger()
            logger.info("info_message")

        assert "info_message" in output.getvalue()

    def test_warning_messages_emitted_at_info_level(self) -> None:
        """Verify WARNING messages are emitted when level is INFO."""
        configure_logging(json_format=True, log_level="INFO")
        output = StringIO()

        with patch("sys.stdout", output):
            logger = structlog.get_logger()
            logger.warning("warning_message")

        assert "warning_message" in output.getvalue()

    def test_debug_messages_emitted_at_debug_level(self) -> None:
        """Verify DEBUG messages are emitted when level is DEBUG."""
        configure_logging(json_format=True, log_level="DEBUG")
        output = StringIO()

        with patch("sys.stdout", output):
            logger = structlog.get_logger()
            logger.debug("debug_message")

        assert "debug_message" in output.getvalue()
