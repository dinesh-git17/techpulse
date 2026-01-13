"""Structured logging configuration for the API layer.

This module configures structlog with environment-aware output formats:
JSON for production log aggregation, and colored console output for
local development.
"""

import logging
import sys
from typing import Literal

import structlog
from structlog.types import Processor


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


def configure_logging(log_format: Literal["json", "console"] = "console") -> None:
    """Configure structlog with the specified output format.

    Sets up structlog processors and configures the standard library
    logging to use structlog for consistent log output across the
    application.

    Args:
        log_format: Output format - 'json' for structured production logs,
            'console' for human-readable development logs.
    """
    processors: list[Processor]
    if log_format == "json":
        processors = _get_json_processors()
    else:
        processors = _get_console_processors()

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        root_logger.addHandler(handler)
