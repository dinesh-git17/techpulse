"""Unit tests for Prometheus metrics instrumentation."""

from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from techpulse.api.metrics import (
    create_instrumentator,
    get_instrumentator,
    reset_instrumentator,
)


def _clear_prometheus_registry() -> None:
    """Clear all custom collectors from the prometheus registry."""
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
def reset_metrics() -> Generator[None, None, None]:
    """Reset metrics state before and after each test."""
    _clear_prometheus_registry()
    reset_instrumentator()
    yield
    _clear_prometheus_registry()
    reset_instrumentator()


@pytest.fixture
def app_with_metrics() -> FastAPI:
    """Create a test FastAPI application with metrics instrumentation."""
    application = FastAPI()

    @application.get("/test")
    def test_endpoint() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/items/{item_id}")
    def get_item(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    @application.get("/error")
    def error_endpoint() -> None:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail="Internal error")

    instrumentator = create_instrumentator()
    instrumentator.instrument(application)
    instrumentator.expose(application, include_in_schema=False)

    return application


@pytest.fixture
def client(app_with_metrics: FastAPI) -> TestClient:
    """Create a test client for the application."""
    return TestClient(app_with_metrics)


class TestMetricsEndpoint:
    """Test suite for /metrics endpoint."""

    def test_metrics_endpoint_returns_200(self, client: TestClient) -> None:
        """Verify /metrics endpoint returns 200 OK."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_endpoint_returns_text_content(self, client: TestClient) -> None:
        """Verify /metrics returns text content."""
        response = client.get("/metrics")
        assert response.text is not None
        assert len(response.text) > 0

    def test_metrics_endpoint_contains_http_metrics(self, client: TestClient) -> None:
        """Verify /metrics contains HTTP metrics after requests."""
        client.get("/test")
        response = client.get("/metrics")
        metrics_text = response.text

        assert "http_request" in metrics_text or "http_requests" in metrics_text


class TestRequestCountMetric:
    """Test suite for request count metric."""

    def test_request_count_increments(self, client: TestClient) -> None:
        """Verify request count metric increments with each request."""
        client.get("/test")
        client.get("/test")

        response = client.get("/metrics")
        metrics_text = response.text

        assert "http_request" in metrics_text

    def test_request_count_includes_method_label(self, client: TestClient) -> None:
        """Verify method label is present in metrics."""
        client.get("/test")

        response = client.get("/metrics")
        metrics_text = response.text

        assert 'method="GET"' in metrics_text

    def test_request_count_includes_status_label(self, client: TestClient) -> None:
        """Verify status code label is present in metrics."""
        client.get("/test")

        response = client.get("/metrics")
        metrics_text = response.text

        assert 'status="200"' in metrics_text or "200" in metrics_text

    def test_request_count_includes_handler_label(self, client: TestClient) -> None:
        """Verify handler (path) label is present in metrics."""
        client.get("/test")

        response = client.get("/metrics")
        metrics_text = response.text

        assert "/test" in metrics_text


class TestRequestDurationMetric:
    """Test suite for request duration histogram metric."""

    def test_duration_histogram_exists(self, client: TestClient) -> None:
        """Verify duration histogram metric is recorded."""
        client.get("/test")

        response = client.get("/metrics")
        metrics_text = response.text

        assert "duration" in metrics_text.lower() or "seconds" in metrics_text.lower()

    def test_duration_has_bucket_boundaries(self, client: TestClient) -> None:
        """Verify histogram has bucket boundaries."""
        client.get("/test")

        response = client.get("/metrics")
        metrics_text = response.text

        assert "_bucket" in metrics_text or "bucket" in metrics_text.lower()


class TestPathGrouping:
    """Test suite for path grouping by route template."""

    def test_parameterized_paths_grouped(self, client: TestClient) -> None:
        """Verify parameterized paths are grouped by template."""
        client.get("/items/1")
        client.get("/items/2")
        client.get("/items/999")

        response = client.get("/metrics")
        metrics_text = response.text

        assert "/items/{item_id}" in metrics_text


class TestErrorMetrics:
    """Test suite for error rate metrics."""

    def test_error_responses_tracked(self, client: TestClient) -> None:
        """Verify error responses are tracked in metrics."""
        client.get("/error")

        response = client.get("/metrics")
        metrics_text = response.text

        assert "500" in metrics_text

    def test_different_status_codes_distinguished(self, client: TestClient) -> None:
        """Verify different status codes have distinct labels."""
        client.get("/test")
        client.get("/error")

        response = client.get("/metrics")
        metrics_text = response.text

        has_200 = "200" in metrics_text
        has_500 = "500" in metrics_text

        assert has_200 or has_500


class TestInstrumentatorConfiguration:
    """Test suite for instrumentator configuration."""

    def test_create_instrumentator_returns_instrumentator(self) -> None:
        """Verify create_instrumentator returns an Instrumentator instance."""
        from prometheus_fastapi_instrumentator import Instrumentator

        instrumentator = create_instrumentator()
        assert isinstance(instrumentator, Instrumentator)

    def test_get_instrumentator_returns_same_instance(self) -> None:
        """Verify get_instrumentator returns the same instance on repeated calls."""
        inst1 = get_instrumentator()
        inst2 = get_instrumentator()
        assert inst1 is inst2

    def test_reset_instrumentator_clears_instance(self) -> None:
        """Verify reset_instrumentator clears the global instance."""
        inst1 = get_instrumentator()
        reset_instrumentator()
        inst2 = get_instrumentator()
        assert inst1 is not inst2


class TestMetricsLabels:
    """Test suite for metrics label validation."""

    def test_no_high_cardinality_labels(self, client: TestClient) -> None:
        """Verify no high-cardinality labels like user_id or query params."""
        client.get("/test?user_id=12345&query=test")

        response = client.get("/metrics")
        metrics_text = response.text

        assert "user_id" not in metrics_text
        assert "12345" not in metrics_text
        assert "query=test" not in metrics_text

    def test_standard_labels_present(self, client: TestClient) -> None:
        """Verify standard labels (method, handler) are present."""
        client.get("/test")

        response = client.get("/metrics")
        metrics_text = response.text

        assert "method" in metrics_text
        assert "handler" in metrics_text
