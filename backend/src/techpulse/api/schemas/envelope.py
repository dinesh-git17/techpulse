"""Standardized response envelope for API responses.

This module defines the ResponseEnvelope generic model that wraps all
successful API responses with consistent metadata for pagination,
request tracking, and timestamps.
"""

from datetime import datetime, timezone
from typing import Generic, Optional, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field

T = TypeVar("T")


class Meta(BaseModel):
    """Metadata for API responses.

    Provides consistent metadata across all API responses including
    request tracking, timestamps, and pagination information.

    Attributes:
        request_id: Unique identifier for request tracing.
        timestamp: ISO 8601 timestamp of response generation.
        total_count: Total number of items available (for paginated responses).
        page: Current page number (1-indexed).
        page_size: Number of items per page.
        has_more: Whether additional pages exist.
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for request tracing.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 timestamp of response generation.",
    )
    total_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total number of items available.",
    )
    page: Optional[int] = Field(
        default=None,
        ge=1,
        description="Current page number (1-indexed).",
    )
    page_size: Optional[int] = Field(
        default=None,
        ge=1,
        description="Number of items per page.",
    )
    has_more: Optional[bool] = Field(
        default=None,
        description="Whether additional pages exist.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-15T10:30:00Z",
                "total_count": 100,
                "page": 1,
                "page_size": 20,
                "has_more": True,
            }
        }
    }


class ResponseEnvelope(BaseModel, Generic[T]):
    """Generic response envelope wrapping API response data.

    All successful API responses are wrapped in this envelope to provide
    consistent structure with metadata. The data field contains the
    actual response payload.

    Type Parameters:
        T: The type of the response data payload.

    Attributes:
        data: The response payload of type T.
        meta: Response metadata including request_id and pagination.

    Example:
        >>> envelope = ResponseEnvelope(
        ...     data={"id": 1, "name": "Python"},
        ...     meta=Meta(total_count=1)
        ... )
    """

    data: T = Field(
        description="The response payload.",
    )
    meta: Meta = Field(
        default_factory=Meta,
        description="Response metadata.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": {"id": 1, "name": "Example"},
                "meta": {
                    "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "total_count": 1,
                    "page": 1,
                    "page_size": 20,
                    "has_more": False,
                },
            }
        }
    }


def create_envelope(
    data: T,
    total_count: Optional[int] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    request_id: Optional[str] = None,
) -> ResponseEnvelope[T]:
    """Create a ResponseEnvelope with computed metadata.

    Convenience function for creating response envelopes with automatic
    has_more calculation based on pagination parameters.

    Args:
        data: The response payload.
        total_count: Total number of items available.
        page: Current page number (1-indexed).
        page_size: Number of items per page.
        request_id: Optional request ID (generated if not provided).

    Returns:
        A ResponseEnvelope containing the data and computed metadata.
    """
    has_more: Optional[bool] = None
    if total_count is not None and page is not None and page_size is not None:
        has_more = (page * page_size) < total_count

    meta = Meta(
        request_id=request_id or str(uuid4()),
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )

    return ResponseEnvelope(data=data, meta=meta)
