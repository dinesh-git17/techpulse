"""Trend schema models for API responses.

This module defines the Pydantic models for trend data returned
by the /trends endpoint, including monthly data points and
technology-grouped time series.
"""

from pydantic import BaseModel, Field


class TrendDataPoint(BaseModel):
    """Represents a single month's trend data for a technology.

    Attributes:
        month: The month in YYYY-MM format.
        count: Number of job mentions for this technology in the month.
    """

    month: str = Field(
        description="Month in YYYY-MM format.",
        json_schema_extra={"example": "2024-01"},
    )
    count: int = Field(
        ge=0,
        description="Number of job mentions for this technology.",
        json_schema_extra={"example": 1523},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "month": "2024-01",
                "count": 1523,
            }
        }
    }


class TechnologyTrend(BaseModel):
    """Represents trend data for a single technology over time.

    Contains the technology identifier and an array of monthly data points
    sorted chronologically.

    Attributes:
        tech_key: Unique identifier for the technology.
        name: Human-readable display name.
        data: List of monthly data points in chronological order.
    """

    tech_key: str = Field(
        description="Unique identifier for the technology.",
        json_schema_extra={"example": "python"},
    )
    name: str = Field(
        description="Human-readable display name.",
        json_schema_extra={"example": "Python"},
    )
    data: list[TrendDataPoint] = Field(
        description="Monthly data points in chronological order.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "tech_key": "python",
                "name": "Python",
                "data": [
                    {"month": "2024-01", "count": 1523},
                    {"month": "2024-02", "count": 1412},
                ],
            }
        }
    }
