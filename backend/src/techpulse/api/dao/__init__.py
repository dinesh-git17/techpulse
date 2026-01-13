"""Data Access Object layer for database operations."""

from techpulse.api.dao.base import BaseDAO
from techpulse.api.dao.technology import TechnologyDAO
from techpulse.api.dao.trend import TrendDAO

__all__ = ["BaseDAO", "TechnologyDAO", "TrendDAO"]
