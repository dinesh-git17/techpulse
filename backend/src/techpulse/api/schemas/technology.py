"""Technology schema models for API responses.

This module defines the Pydantic models for technology entities
returned by the /technologies endpoint.
"""

from pydantic import BaseModel, Field


class Technology(BaseModel):
    """Represents a technology entity in the taxonomy.

    This model is used in the /technologies endpoint response to provide
    the complete list of available technologies for filtering.

    Attributes:
        key: Unique identifier for the technology (e.g., "python", "react").
        name: Human-readable display name (e.g., "Python", "React").
        category: Technology classification (e.g., "Language", "Framework").
    """

    key: str = Field(
        description="Unique identifier for the technology.",
        json_schema_extra={"example": "python"},
    )
    name: str = Field(
        description="Human-readable display name.",
        json_schema_extra={"example": "Python"},
    )
    category: str = Field(
        description="Technology classification.",
        json_schema_extra={"example": "Language"},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "key": "python",
                "name": "Python",
                "category": "Language",
            }
        }
    }
