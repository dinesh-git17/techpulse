"""Pydantic data models for Hacker News API responses.

This module defines the strict schema contracts for all data returned by the
HackerNewsClient. These models enforce type safety and validation at the
boundary between the external API and internal business logic.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class HNItemType(str, Enum):
    """Enumeration of Hacker News item types.

    The HN API returns items of different types, each with slightly different
    field availability. This enum provides type-safe handling of item categories.
    """

    STORY = "story"
    COMMENT = "comment"
    JOB = "job"
    POLL = "poll"
    POLLOPT = "pollopt"


class HNItem(BaseModel):
    """Validated representation of a Hacker News item.

    This model covers all item types (story, comment, job, poll, pollopt) with
    optional fields for type-specific attributes. The API returns Unix timestamps
    which are converted to UTC datetime objects.

    Attributes:
        id: Unique integer identifier for the item.
        type: The category of item (story, comment, job, poll, pollopt).
        by: Username of the item author. None for deleted items.
        time: UTC datetime when the item was created.
        title: Title text for stories, jobs, and polls.
        text: Body content for comments, self-posts, and polls.
        url: External URL for link stories and jobs.
        kids: List of child comment IDs.
        parent: Parent item ID for comments.
        score: Point score for stories and polls.
        descendants: Total comment count for stories.
        poll: Associated poll ID for poll options.
        parts: List of poll option IDs for polls.
        deleted: True if the item has been deleted.
        dead: True if the item has been flagged/killed.
    """

    id: int = Field(description="Unique integer identifier for the item")
    type: HNItemType = Field(
        description="Item category (story, comment, job, poll, pollopt)"
    )
    by: Optional[str] = Field(
        default=None, description="Username of the author. None for deleted items."
    )
    time: datetime = Field(description="UTC datetime when the item was created")
    title: Optional[str] = Field(
        default=None, description="Title text for stories, jobs, and polls"
    )
    text: Optional[str] = Field(
        default=None, description="Body content for comments, self-posts, and polls"
    )
    url: Optional[str] = Field(
        default=None, description="External URL for link stories and jobs"
    )
    kids: list[int] = Field(
        default_factory=list, description="List of child comment IDs"
    )
    parent: Optional[int] = Field(
        default=None, description="Parent item ID for comments"
    )
    score: Optional[int] = Field(
        default=None, description="Point score for stories and polls"
    )
    descendants: Optional[int] = Field(
        default=None, description="Total comment count for stories"
    )
    poll: Optional[int] = Field(
        default=None, description="Associated poll ID for poll options"
    )
    parts: list[int] = Field(
        default_factory=list, description="List of poll option IDs for polls"
    )
    deleted: bool = Field(
        default=False, description="True if the item has been deleted"
    )
    dead: bool = Field(
        default=False, description="True if the item has been flagged/killed"
    )

    @field_validator("time", mode="before")
    @classmethod
    def convert_unix_timestamp(cls, value: int | datetime) -> datetime:
        """Convert Unix timestamp to UTC datetime.

        Args:
            value: Unix timestamp integer or pre-converted datetime.

        Returns:
            datetime: UTC-aware datetime object.
        """
        if isinstance(value, datetime):
            return value
        return datetime.fromtimestamp(value, tz=timezone.utc)


class HNUser(BaseModel):
    """Validated representation of a Hacker News user profile.

    Attributes:
        id: The unique username.
        created: UTC datetime when the account was created.
        karma: User's karma score.
        about: User biography (may contain HTML).
        submitted: List of item IDs submitted by this user.
    """

    id: str = Field(description="The unique username")
    created: datetime = Field(description="UTC datetime when the account was created")
    karma: int = Field(description="User's karma score")
    about: Optional[str] = Field(
        default=None, description="User biography (may contain HTML)"
    )
    submitted: list[int] = Field(
        default_factory=list, description="List of item IDs submitted by this user"
    )

    @field_validator("created", mode="before")
    @classmethod
    def convert_unix_timestamp(cls, value: int | datetime) -> datetime:
        """Convert Unix timestamp to UTC datetime.

        Args:
            value: Unix timestamp integer or pre-converted datetime.

        Returns:
            datetime: UTC-aware datetime object.
        """
        if isinstance(value, datetime):
            return value
        return datetime.fromtimestamp(value, tz=timezone.utc)
