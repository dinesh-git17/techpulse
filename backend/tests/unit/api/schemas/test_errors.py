"""Unit tests for RFC 7807 error schemas."""

import pytest

from techpulse.api.schemas.errors import (
    ERROR_TYPE_BASE,
    ProblemDetail,
    create_problem_detail,
)


class TestProblemDetail:
    """Test suite for ProblemDetail model."""

    def test_required_fields(self) -> None:
        """Verify all required fields can be set."""
        problem = ProblemDetail(
            type="https://example.com/error",
            title="Error Title",
            status=400,
            detail="Error details here",
        )
        assert problem.type == "https://example.com/error"
        assert problem.title == "Error Title"
        assert problem.status == 400
        assert problem.detail == "Error details here"

    def test_instance_defaults_to_none(self) -> None:
        """Verify instance field defaults to None."""
        problem = ProblemDetail(
            type="https://example.com/error",
            title="Error",
            status=500,
            detail="Details",
        )
        assert problem.instance is None

    def test_instance_can_be_set(self) -> None:
        """Verify instance field can be set."""
        problem = ProblemDetail(
            type="https://example.com/error",
            title="Error",
            status=404,
            detail="Not found",
            instance="/api/v1/items/123",
        )
        assert problem.instance == "/api/v1/items/123"

    def test_status_minimum_400(self) -> None:
        """Verify status must be at least 400."""
        with pytest.raises(ValueError):
            ProblemDetail(
                type="https://example.com/error",
                title="Error",
                status=399,
                detail="Details",
            )

    def test_status_maximum_599(self) -> None:
        """Verify status must be at most 599."""
        with pytest.raises(ValueError):
            ProblemDetail(
                type="https://example.com/error",
                title="Error",
                status=600,
                detail="Details",
            )

    def test_status_400_valid(self) -> None:
        """Verify status 400 is valid."""
        problem = ProblemDetail(
            type="https://example.com/error",
            title="Bad Request",
            status=400,
            detail="Invalid input",
        )
        assert problem.status == 400

    def test_status_599_valid(self) -> None:
        """Verify status 599 is valid."""
        problem = ProblemDetail(
            type="https://example.com/error",
            title="Error",
            status=599,
            detail="Details",
        )
        assert problem.status == 599

    def test_serialization_to_dict(self) -> None:
        """Verify ProblemDetail serializes to dict correctly."""
        problem = ProblemDetail(
            type="https://techpulse.dev/errors/not-found",
            title="Not Found",
            status=404,
            detail="Resource not found",
            instance="/api/v1/items/999",
        )
        data = problem.model_dump()
        assert data["type"] == "https://techpulse.dev/errors/not-found"
        assert data["title"] == "Not Found"
        assert data["status"] == 404
        assert data["detail"] == "Resource not found"
        assert data["instance"] == "/api/v1/items/999"

    def test_json_serialization(self) -> None:
        """Verify ProblemDetail serializes to JSON."""
        problem = ProblemDetail(
            type="https://example.com/error",
            title="Error",
            status=500,
            detail="Server error",
        )
        json_str = problem.model_dump_json()
        assert "https://example.com/error" in json_str
        assert "Error" in json_str
        assert "500" in json_str


class TestErrorTypeBase:
    """Test suite for ERROR_TYPE_BASE constant."""

    def test_error_type_base_value(self) -> None:
        """Verify ERROR_TYPE_BASE has expected value."""
        assert ERROR_TYPE_BASE == "https://techpulse.dev/errors"

    def test_error_type_base_is_https(self) -> None:
        """Verify ERROR_TYPE_BASE uses HTTPS."""
        assert ERROR_TYPE_BASE.startswith("https://")


class TestCreateProblemDetail:
    """Test suite for create_problem_detail helper function."""

    def test_creates_problem_with_full_type_uri(self) -> None:
        """Verify create_problem_detail prefixes error type."""
        problem = create_problem_detail(
            error_type="not-found",
            title="Not Found",
            status=404,
            detail="Resource not found",
        )
        assert problem.type == f"{ERROR_TYPE_BASE}/not-found"

    def test_sets_all_fields(self) -> None:
        """Verify create_problem_detail sets all fields correctly."""
        problem = create_problem_detail(
            error_type="validation-error",
            title="Validation Error",
            status=422,
            detail="Invalid data",
            instance="/api/v1/items",
        )
        assert problem.title == "Validation Error"
        assert problem.status == 422
        assert problem.detail == "Invalid data"
        assert problem.instance == "/api/v1/items"

    def test_instance_defaults_to_none(self) -> None:
        """Verify instance defaults to None when not provided."""
        problem = create_problem_detail(
            error_type="error",
            title="Error",
            status=500,
            detail="Details",
        )
        assert problem.instance is None

    def test_various_error_types(self) -> None:
        """Verify various error types are handled correctly."""
        error_types = [
            "database-connection-error",
            "record-not-found",
            "query-execution-error",
            "data-validation-error",
            "internal-error",
        ]
        for error_type in error_types:
            problem = create_problem_detail(
                error_type=error_type,
                title="Test",
                status=500,
                detail="Test",
            )
            assert problem.type == f"{ERROR_TYPE_BASE}/{error_type}"
