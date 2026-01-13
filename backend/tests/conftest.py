"""Global test fixtures for the backend test suite."""

from typing import Generator

import pytest
from prometheus_client import REGISTRY

from techpulse.api.metrics import reset_instrumentator


def _clear_prometheus_registry() -> None:
    """Clear all custom collectors from the prometheus registry.

    Required to prevent 'Duplicated timeseries' errors when tests
    create multiple FastAPI applications with metrics instrumentation.
    """
    collectors_to_remove = []
    for collector in REGISTRY._names_to_collectors.values():
        if hasattr(collector, "_name"):
            collectors_to_remove.append(collector)

    for collector in set(collectors_to_remove):
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass


@pytest.fixture(autouse=True)
def reset_prometheus_state() -> Generator[None, None, None]:
    """Reset prometheus metrics state before and after each test.

    This fixture ensures clean prometheus registry state for tests that
    create FastAPI applications with metrics instrumentation.
    """
    _clear_prometheus_registry()
    reset_instrumentator()
    yield
    _clear_prometheus_registry()
    reset_instrumentator()
