"""Prometheus metrics instrumentation for the API layer.

This module configures prometheus-fastapi-instrumentator to collect RED
metrics (Rate, Error, Duration) for all API endpoints. Metrics are exposed
at the /metrics endpoint in Prometheus text format.

Default metrics provided:
- http_requests_total: Counter with labels (method, handler, status)
- http_request_duration_seconds: Histogram with labels (method, handler)
- http_requests_inprogress: Gauge for in-flight requests
"""

from prometheus_fastapi_instrumentator import Instrumentator

_instrumentator: Instrumentator | None = None


def create_instrumentator() -> Instrumentator:
    """Create and configure the Prometheus instrumentator.

    Configures metrics collection with route template grouping to prevent
    cardinality explosion. Standard labels (method, handler, status) are
    applied automatically by the default instrumentation.

    Configuration choices:
    - should_group_status_codes=False: Keep individual status codes (200, 404, 500)
      rather than grouping (2xx, 4xx, 5xx) for precise error rate calculation.
    - should_ignore_untemplated=True: Ignore requests to paths without route
      templates to prevent cardinality explosion from arbitrary paths.
    - should_instrument_requests_inprogress=True: Track in-flight requests
      for concurrency monitoring.
    - excluded_handlers: Skip health check endpoints to avoid noise in metrics.

    Returns:
        Configured Instrumentator instance ready for FastAPI integration.
    """
    return Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/health", "/health/live", "/health/ready"],
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    )


def get_instrumentator() -> Instrumentator:
    """Retrieve the global instrumentator instance.

    Creates the instrumentator on first access using lazy initialization.

    Returns:
        The global Instrumentator instance.
    """
    global _instrumentator
    if _instrumentator is None:
        _instrumentator = create_instrumentator()
    return _instrumentator


def reset_instrumentator() -> None:
    """Reset the global instrumentator instance.

    Primarily used for testing to ensure clean state between tests.
    """
    global _instrumentator
    _instrumentator = None
