"""Structured logging configuration for the API layer.

This module configures structlog with environment-aware output formats:
JSON for production log aggregation, and colored console output for
local development. Log level is configurable via environment variable.
"""

import logging
import sys
from typing import Literal

import structlog
from structlog.types import Processor

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

_LOG_LEVEL_MAP: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def _get_log_level_int(level: LogLevel) -> int:
    """Convert string log level to logging module constant.

    Args:
        level: Log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        Corresponding logging module integer constant.
    """
    return _LOG_LEVEL_MAP[level]


def _get_json_processors() -> list[Processor]:
    """Build processor chain for JSON log output.

    Returns:
        List of structlog processors for JSON formatting.
    """
    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ]


def _get_console_processors() -> list[Processor]:
    """Build processor chain for console log output.

    Returns:
        List of structlog processors for colored console formatting.
    """
    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(colors=True),
    ]


def configure_logging(
    json_format: bool = False,
    log_level: LogLevel = "INFO",
) -> None:
    """Configure structlog with the specified output format and level.

    Sets up structlog processors and configures the standard library
    logging to use structlog for consistent log output across the
    application.

    Args:
        json_format: True for structured JSON production logs,
            False for human-readable colored console logs.
        log_level: Minimum log level to emit (DEBUG, INFO, WARNING,
            ERROR, CRITICAL). Defaults to INFO.
    """
    processors: list[Processor]
    if json_format:
        processors = _get_json_processors()
    else:
        processors = _get_console_processors()

    level_int = _get_log_level_int(log_level)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level_int),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level_int)

    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level_int)
        root_logger.addHandler(handler)
