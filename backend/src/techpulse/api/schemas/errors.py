"""RFC 7807 Problem Details error response schema.

This module defines the ProblemDetail model for standardized error
responses following the RFC 7807 specification for HTTP API errors.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ProblemDetail(BaseModel):
    """RFC 7807 Problem Details response model.

    Provides a standardized error response format as specified in
    RFC 7807 (Problem Details for HTTP APIs). All API errors are
    returned in this format for consistent client handling.

    Attributes:
        type: URI reference identifying the problem type.
        title: Short, human-readable summary of the problem.
        status: HTTP status code for this occurrence.
        detail: Human-readable explanation specific to this occurrence.
        instance: URI reference identifying the specific occurrence.

    Example:
        >>> error = ProblemDetail(
        ...     type="https://techpulse.dev/errors/record-not-found",
        ...     title="Record Not Found",
        ...     status=404,
        ...     detail="Technology with key 'unknown_tech' does not exist.",
        ...     instance="/api/v1/technologies/unknown_tech"
        ... )
    """

    type: str = Field(
        description="URI reference identifying the problem type.",
    )
    title: str = Field(
        description="Short, human-readable summary of the problem.",
    )
    status: int = Field(
        ge=400,
        le=599,
        description="HTTP status code for this occurrence.",
    )
    detail: str = Field(
        description="Human-readable explanation specific to this occurrence.",
    )
    instance: Optional[str] = Field(
        default=None,
        description="URI reference identifying the specific occurrence.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "https://techpulse.dev/errors/record-not-found",
                "title": "Record Not Found",
                "status": 404,
                "detail": "Technology with key 'unknown_tech' does not exist.",
                "instance": "/api/v1/technologies/unknown_tech",
            }
        }
    }


ERROR_TYPE_BASE = "https://techpulse.dev/errors"


def create_problem_detail(
    error_type: str,
    title: str,
    status: int,
    detail: str,
    instance: Optional[str] = None,
) -> ProblemDetail:
    """Create a ProblemDetail with the standard type URI prefix.

    Convenience function for creating ProblemDetail instances with
    consistent URI formatting for error types.

    Args:
        error_type: Error type suffix (e.g., "record-not-found").
        title: Short summary of the problem.
        status: HTTP status code.
        detail: Detailed explanation of the error.
        instance: Optional URI of the specific occurrence.

    Returns:
        A ProblemDetail instance with fully-qualified type URI.
    """
    return ProblemDetail(
        type=f"{ERROR_TYPE_BASE}/{error_type}",
        title=title,
        status=status,
        detail=detail,
        instance=instance,
    )
