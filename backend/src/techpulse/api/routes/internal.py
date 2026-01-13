"""Internal API routes for operational tasks.

This module provides internal endpoints for cache management and other
operational tasks. These endpoints are protected by API key authentication
and are intended for use by internal systems like the Dagster pipeline.
"""

from typing import Annotated, Optional

import structlog
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from techpulse.api.cache.keys import CacheKeyBuilder
from techpulse.api.cache.service import get_cache_service
from techpulse.api.core.config import get_settings

logger = structlog.get_logger(__name__)

internal_router = APIRouter(prefix="/internal", tags=["internal"])


class CachePurgeRequest(BaseModel):
    """Request body for cache purge endpoint.

    Attributes:
        pattern: Optional glob pattern for targeted purge (e.g., 'trends').
            If not provided, purges all cached keys.
    """

    pattern: Optional[str] = Field(
        default=None,
        description="Endpoint name for targeted purge (e.g., 'trends'). "
        "If not provided, purges all cached keys.",
    )


class CachePurgeResponse(BaseModel):
    """Response body for cache purge endpoint.

    Attributes:
        purged_count: Number of cache keys that were purged.
        pattern: The pattern that was used for purging.
    """

    purged_count: int = Field(
        ge=0,
        description="Number of cache keys that were purged.",
    )
    pattern: str = Field(
        description="The glob pattern that was used for purging.",
    )


def validate_api_key(api_key: Optional[str]) -> None:
    """Validate the provided API key against the configured purge key.

    Args:
        api_key: The API key from the request header.

    Raises:
        HTTPException: If the API key is missing, invalid, or purge key
            is not configured.
    """
    settings = get_settings()
    configured_key = settings.cache_purge_api_key

    if configured_key is None:
        logger.warning(
            "cache_purge_rejected",
            reason="purge_api_key_not_configured",
        )
        raise HTTPException(
            status_code=401,
            detail={
                "type": "https://techpulse.dev/errors/unauthorized",
                "title": "Unauthorized",
                "status": 401,
                "detail": "Cache purge API key is not configured.",
            },
        )

    if api_key is None:
        logger.warning(
            "cache_purge_rejected",
            reason="missing_api_key",
        )
        raise HTTPException(
            status_code=401,
            detail={
                "type": "https://techpulse.dev/errors/unauthorized",
                "title": "Unauthorized",
                "status": 401,
                "detail": "X-API-Key header is required.",
            },
        )

    if api_key != configured_key:
        logger.warning(
            "cache_purge_rejected",
            reason="invalid_api_key",
        )
        raise HTTPException(
            status_code=401,
            detail={
                "type": "https://techpulse.dev/errors/unauthorized",
                "title": "Unauthorized",
                "status": 401,
                "detail": "Invalid API key.",
            },
        )


@internal_router.post(
    "/cache/purge",
    response_model=CachePurgeResponse,
    summary="Purge cache entries",
    description="Purge cached data entries. Requires X-API-Key authentication. "
    "Called by Dagster pipeline after successful data ingestion.",
    responses={
        401: {
            "description": "Unauthorized - Invalid or missing API key",
            "content": {
                "application/json": {
                    "example": {
                        "type": "https://techpulse.dev/errors/unauthorized",
                        "title": "Unauthorized",
                        "status": 401,
                        "detail": "Invalid API key.",
                    }
                }
            },
        }
    },
)
def purge_cache(
    request: Optional[CachePurgeRequest] = None,
    x_api_key: Annotated[
        Optional[str],
        Header(description="API key for authentication."),
    ] = None,
) -> CachePurgeResponse:
    """Purge cache entries matching the specified pattern.

    Validates the API key and purges cache entries. If a pattern is provided,
    only entries matching that endpoint pattern are purged. Otherwise, all
    cache entries are purged.

    Args:
        request: Optional request body with pattern for targeted purge.
        x_api_key: API key for authentication from X-API-Key header.

    Returns:
        CachePurgeResponse containing the number of purged entries and pattern.

    Raises:
        HTTPException: If authentication fails (401).
    """
    validate_api_key(x_api_key)

    cache_service = get_cache_service()
    key_builder = CacheKeyBuilder()

    endpoint_pattern = request.pattern if request else None
    if endpoint_pattern:
        glob_pattern = key_builder.pattern(endpoint_pattern)
    else:
        glob_pattern = key_builder.all_pattern()

    if cache_service is None or not cache_service.is_connected():
        logger.warning(
            "cache_purge_skipped",
            pattern=glob_pattern,
            reason="cache_not_connected",
        )
        return CachePurgeResponse(purged_count=0, pattern=glob_pattern)

    purged_count = cache_service.delete_pattern(glob_pattern)

    logger.info(
        "cache_purge_completed",
        pattern=glob_pattern,
        purged_count=purged_count,
    )

    return CachePurgeResponse(purged_count=purged_count, pattern=glob_pattern)
