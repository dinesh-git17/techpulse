"""Technology lookup endpoint.

This module provides the GET /technologies endpoint for retrieving
the complete technology taxonomy for frontend filtering.
"""

import duckdb
from fastapi import Depends

from techpulse.api.dao.technology import TechnologyDAO
from techpulse.api.db.manager import get_db_cursor
from techpulse.api.main import v1_router
from techpulse.api.schemas.envelope import ResponseEnvelope, create_envelope
from techpulse.api.schemas.technology import Technology


@v1_router.get(
    "/technologies",
    response_model=ResponseEnvelope[list[Technology]],
    summary="List all technologies",
    description="Returns the complete technology taxonomy for filtering.",
)
def list_technologies(
    cursor: duckdb.DuckDBPyConnection = Depends(get_db_cursor),
) -> ResponseEnvelope[list[Technology]]:
    """Retrieve all available technologies.

    Returns the complete list of technologies available for trend analysis,
    sorted alphabetically by name. This endpoint is used to populate
    filter dropdowns in the frontend.

    Args:
        cursor: Database cursor injected via FastAPI dependency.

    Returns:
        ResponseEnvelope containing a list of Technology objects with
        total_count metadata.
    """
    dao = TechnologyDAO(cursor)
    technologies = dao.list_all()
    return create_envelope(data=technologies, total_count=len(technologies))
