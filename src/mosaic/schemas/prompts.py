"""Pydantic schemas for MCP prompt argument validation.

These schemas validate arguments passed to MCP prompts that accept parameters.
"""

from datetime import date
from typing import Optional

from pydantic import Field, field_validator, model_validator

from mosaic.schemas.common import BaseSchema


class GenerateTimecardArgs(BaseSchema):
    """Arguments for generate-timecard prompt.

    Generates a timecard for a specific employer and date range.
    All fields are optional - defaults to current employer and week.
    """

    employer_name: Optional[str] = Field(
        default=None,
        description="Name of employer to generate timecard for (defaults to current employer)",
        min_length=1,
    )
    start_date: Optional[date] = Field(
        default=None,
        description="Start date of timecard period (defaults to start of current week)",
    )
    end_date: Optional[date] = Field(
        default=None,
        description="End date of timecard period (defaults to end of current week)",
    )

    @field_validator("employer_name")
    @classmethod
    def validate_employer_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate employer name is not empty or whitespace-only."""
        if v is not None and not v.strip():
            raise ValueError("employer_name cannot be empty or whitespace")
        return v

    @model_validator(mode="after")
    def validate_date_range(self) -> "GenerateTimecardArgs":
        """Ensure end_date is after start_date."""
        if self.start_date is not None and self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError("end_date must be after start_date")
        return self


class WeeklyReviewArgs(BaseSchema):
    """Arguments for weekly-review prompt.

    Generates a weekly summary of work activities, meetings, and hours.
    """

    week_start: Optional[date] = Field(
        default=None,
        description="Start date of week to review (defaults to current week)",
    )


class FindGapsArgs(BaseSchema):
    """Arguments for find-gaps prompt.

    Identifies gaps in logged work time for a date range.
    Both dates must be provided together or neither.
    """

    start_date: Optional[date] = Field(
        default=None,
        description="Start date for gap analysis (defaults to current week start)",
    )
    end_date: Optional[date] = Field(
        default=None,
        description="End date for gap analysis (defaults to current week end)",
    )

    @model_validator(mode="after")
    def validate_date_range(self) -> "FindGapsArgs":
        """Ensure both dates provided together and end_date is after start_date."""
        # Both or neither
        if (self.start_date is None) != (self.end_date is None):
            raise ValueError("both start_date and end_date required if either is provided")

        # Validate range if both provided
        if self.start_date is not None and self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError("end_date must be after start_date")

        return self


class SearchContextArgs(BaseSchema):
    """Arguments for search-context prompt.

    Searches for relevant context based on a natural language query.
    """

    query: str = Field(
        description="Natural language search query for finding relevant context",
        min_length=1,
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query is not empty or whitespace-only."""
        if not v.strip():
            raise ValueError("query cannot be empty or whitespace")
        return v


__all__ = [
    "GenerateTimecardArgs",
    "WeeklyReviewArgs",
    "FindGapsArgs",
    "SearchContextArgs",
]
