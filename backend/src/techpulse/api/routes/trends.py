"""Trends endpoint for technology time series data.

This module provides the GET /trends endpoint for retrieving monthly
trend data for specified technologies within a date range.
"""

import re
from datetime import date
from typing import Annotated, Optional

import duckdb
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from techpulse.api.cache import cached
from techpulse.api.dao.trend import TrendDAO
from techpulse.api.db.manager import get_db_cursor
from techpulse.api.main import v1_router
from techpulse.api.schemas.envelope import ResponseEnvelope, create_envelope
from techpulse.api.schemas.trend import TechnologyTrend

TECH_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

MAX_TECHNOLOGIES = 10
MAX_DATE_RANGE_MONTHS = 60


class TrendRequest(BaseModel):
    """Request parameters for the trends endpoint.

    Validates and parses query parameters for trend data requests.
    Tech IDs are required while dates default to the trailing 12 months.

    Attributes:
        tech_ids: List of technology keys to query.
        start_date: Start of date range (defaults to 12 months ago).
        end_date: End of date range (defaults to today).
    """

    tech_ids: list[str] = Field(
        min_length=1,
        description="List of technology keys to query (required, at least one).",
    )
    start_date: Optional[date] = Field(
        default=None,
        description="Start of date range in ISO 8601 format (YYYY-MM-DD).",
    )
    end_date: Optional[date] = Field(
        default=None,
        description="End of date range in ISO 8601 format (YYYY-MM-DD).",
    )

    @field_validator("tech_ids", mode="after")
    @classmethod
    def validate_tech_id_format(cls, value: list[str]) -> list[str]:
        """Validate that each tech_id matches the allowed format.

        Args:
            value: List of tech_ids to validate.

        Returns:
            The validated list of tech_ids.

        Raises:
            ValueError: If any tech_id contains invalid characters.
        """
        invalid_ids = [
            tech_id for tech_id in value if not TECH_ID_PATTERN.match(tech_id)
        ]
        if invalid_ids:
            raise ValueError(
                f"Invalid tech_id format: {invalid_ids}. "
                "Only alphanumeric characters, hyphens, and underscores allowed."
            )
        return value

    def get_date_range(self) -> tuple[date, date]:
        """Return the effective date range with defaults applied.

        If start_date is not provided, defaults to 12 months before end_date.
        If end_date is not provided, defaults to today.

        Returns:
            Tuple of (start_date, end_date) with defaults applied.
        """
        effective_end = self.end_date or date.today()
        if self.start_date:
            effective_start = self.start_date
        else:
            year = effective_end.year - 1
            month = effective_end.month
            day = min(effective_end.day, 28)
            effective_start = date(year, month, day)
        return effective_start, effective_end


def parse_tech_ids(
    tech_ids: Annotated[
        Optional[str],
        Query(
            description="Comma-separated list of technology keys (required).",
            examples=["python,react", "python"],
        ),
    ] = None,
) -> list[str]:
    """Parse and validate tech_ids query parameter.

    Args:
        tech_ids: Comma-separated string of technology keys.

    Returns:
        List of validated technology key strings.

    Raises:
        HTTPException: If tech_ids is missing, empty, or contains invalid format.
    """
    if not tech_ids:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "https://techpulse.dev/errors/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": "tech_ids parameter is required and must not be empty.",
            },
        )

    parsed = [tid.strip() for tid in tech_ids.split(",") if tid.strip()]

    if not parsed:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "https://techpulse.dev/errors/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": "tech_ids parameter is required and must not be empty.",
            },
        )

    invalid_ids = [tid for tid in parsed if not TECH_ID_PATTERN.match(tid)]
    if invalid_ids:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "https://techpulse.dev/errors/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": f"Invalid tech_id format: {invalid_ids}. "
                "Only alphanumeric characters, hyphens, and underscores allowed.",
            },
        )

    if len(parsed) > MAX_TECHNOLOGIES:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "https://techpulse.dev/errors/limit-exceeded",
                "title": "Limit Exceeded",
                "status": 422,
                "detail": f"Maximum {MAX_TECHNOLOGIES} technologies allowed "
                f"per request. Received {len(parsed)}.",
            },
        )

    return parsed


def parse_date(
    param_name: str,
    value: Optional[str],
) -> Optional[date]:
    """Parse an ISO 8601 date string.

    Args:
        param_name: Name of the parameter (for error messages).
        value: Date string in YYYY-MM-DD format, or None.

    Returns:
        Parsed date object, or None if value is None.

    Raises:
        HTTPException: If the date format is invalid.
    """
    if value is None:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "https://techpulse.dev/errors/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": f"Invalid {param_name} format: '{value}'. "
                "Expected ISO 8601 date (YYYY-MM-DD).",
            },
        ) from exc


def calculate_months_between(start: date, end: date) -> int:
    """Calculate the number of months between two dates.

    Args:
        start: Start date.
        end: End date.

    Returns:
        Number of months between the dates (inclusive of partial months).
    """
    return (end.year - start.year) * 12 + (end.month - start.month)


def validate_date_range(start: date, end: date) -> None:
    """Validate that the date range does not exceed the maximum allowed.

    Args:
        start: Start date.
        end: End date.

    Raises:
        HTTPException: If the date range exceeds 60 months.
    """
    months = calculate_months_between(start, end)
    if months > MAX_DATE_RANGE_MONTHS:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "https://techpulse.dev/errors/limit-exceeded",
                "title": "Limit Exceeded",
                "status": 422,
                "detail": f"Maximum date range is {MAX_DATE_RANGE_MONTHS} months "
                f"(5 years). Requested range spans {months} months.",
            },
        )


TRENDS_CACHE_TTL_SECONDS = 600


@v1_router.get(
    "/trends",
    response_model=ResponseEnvelope[list[TechnologyTrend]],
    summary="Get technology trends",
    description="Returns monthly trend data for specified technologies.",
    responses={
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "type": "https://techpulse.dev/errors/validation-error",
                        "title": "Validation Error",
                        "status": 422,
                        "detail": "tech_ids is required and must not be empty.",
                    }
                }
            },
        }
    },
)
@cached(
    endpoint="trends",
    key_params=["tech_ids_parsed", "start_date", "end_date"],
    ttl=TRENDS_CACHE_TTL_SECONDS,
)
def get_trends(
    tech_ids_parsed: Annotated[list[str], Depends(parse_tech_ids)],
    start_date: Annotated[
        Optional[str],
        Query(
            description="Start date in ISO 8601 format (YYYY-MM-DD). "
            "Defaults to 12 months ago.",
            examples=["2024-01-01"],
        ),
    ] = None,
    end_date: Annotated[
        Optional[str],
        Query(
            description="End date in ISO 8601 format (YYYY-MM-DD). Defaults to today.",
            examples=["2024-12-31"],
        ),
    ] = None,
    cursor: duckdb.DuckDBPyConnection = Depends(get_db_cursor),
) -> ResponseEnvelope[list[TechnologyTrend]]:
    """Retrieve monthly trend data for specified technologies.

    Returns time-series data for the requested technology keys within
    the specified date range. Unknown tech_ids return empty data arrays.
    Dates default to the trailing 12 months if not specified.

    Args:
        tech_ids_parsed: List of technology keys (parsed from query param).
        start_date: Start of date range in ISO 8601 format.
        end_date: End of date range in ISO 8601 format.
        cursor: Database cursor injected via FastAPI dependency.

    Returns:
        ResponseEnvelope containing list of TechnologyTrend objects.

    Raises:
        HTTPException: If validation fails (missing tech_ids, invalid dates).
    """
    parsed_start = parse_date("start_date", start_date)
    parsed_end = parse_date("end_date", end_date)

    request = TrendRequest(
        tech_ids=tech_ids_parsed,
        start_date=parsed_start,
        end_date=parsed_end,
    )

    effective_start, effective_end = request.get_date_range()

    validate_date_range(effective_start, effective_end)

    dao = TrendDAO(cursor)
    trends = dao.get_trends(
        tech_keys=request.tech_ids,
        start_date=effective_start,
        end_date=effective_end,
    )

    return create_envelope(data=trends, total_count=len(trends))
