"""Schemas for timecard generation operations."""

from datetime import date as Date
from decimal import Decimal

from pydantic import Field

from mosaic.schemas.common import BaseSchema, DateRangeMixin


class TimecardInput(BaseSchema, DateRangeMixin):
    """Input schema for generating a timecard."""

    start_date: Date = Field(
        description="Start date of timecard period (inclusive)",
        examples=["2024-01-01", "2024-01-15"],
    )

    end_date: Date = Field(
        description="End date of timecard period (inclusive)",
        examples=["2024-01-31", "2024-01-21"],
    )

    include_private: bool = Field(
        default=True,
        description="Whether to include work sessions with PRIVATE privacy level",
        examples=[True, False],
    )

    project_id: int | None = Field(
        default=None,
        description="Optional project ID to filter timecard entries",
        gt=0,
        examples=[1, 42, None],
    )


class TimecardEntry(BaseSchema):
    """Schema for a single timecard entry (one project on one date)."""

    date: Date = Field(
        description="Date of work performed",
        examples=["2024-01-15"],
    )

    project_id: int = Field(
        description="ID of project worked on",
        examples=[1, 42],
    )

    project_name: str = Field(
        description="Name of project worked on",
        examples=["Website Redesign", "Mobile App"],
    )

    total_hours: Decimal = Field(
        description="Total hours worked on this project on this date (half-hour rounded)",
        examples=[8.0, 4.5, 2.5],
    )

    summary: str | None = Field(
        default=None,
        description="Aggregated summary of work performed (from all sessions on this date/project)",
        examples=[
            "Morning: Feature development; Afternoon: Bug fixes",
            "Implemented user authentication",
        ],
    )


class TimecardOutput(BaseSchema, DateRangeMixin):
    """Output schema for generated timecard."""

    start_date: Date = Field(
        description="Start date of timecard period",
        examples=["2024-01-01"],
    )

    end_date: Date = Field(
        description="End date of timecard period",
        examples=["2024-01-31"],
    )

    entries: list[TimecardEntry] = Field(
        description="List of timecard entries, grouped by date and project",
        examples=[
            [
                {
                    "date": "2024-01-15",
                    "project_id": 1,
                    "project_name": "Website Redesign",
                    "total_hours": 8.0,
                    "summary": "Feature development",
                }
            ]
        ],
    )

    total_hours: Decimal = Field(
        description="Total hours across all entries in this timecard",
        examples=[40.0, 160.0, 8.5],
    )

    project_filter: int | None = Field(
        default=None,
        description="Project ID filter applied (if any)",
    )

    privacy_filter_applied: bool = Field(
        description="Whether private sessions were excluded",
        examples=[True, False],
    )
