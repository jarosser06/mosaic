"""Common schemas, validators, and utilities shared across all schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from mosaic.models.base import (
    ClientStatus,
    ClientType,
    EntityType,
    PrivacyLevel,
    ProjectStatus,
    WeekBoundary,
)


class BaseSchema(BaseModel):
    """Base schema with common configuration for all schemas."""

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=False,
        str_strip_whitespace=True,
    )


class TimezoneAwareDatetimeMixin:
    """Mixin to validate timezone-aware datetime fields."""

    @field_validator("*", mode="after")
    @classmethod
    def validate_timezone_aware(cls, v: Any) -> Any:
        """Ensure all datetime fields are timezone-aware."""
        if isinstance(v, datetime) and v.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware")
        return v


class TimeRangeMixin:
    """Mixin to validate time ranges (end_time > start_time)."""

    @model_validator(mode="after")
    def validate_time_range(self) -> "TimeRangeMixin":
        """Ensure end_time is after start_time."""
        if hasattr(self, "start_time") and hasattr(self, "end_time"):
            if (
                self.start_time is not None
                and self.end_time is not None
                and self.end_time <= self.start_time
            ):
                raise ValueError("end_time must be after start_time")
        return self


class DateRangeMixin:
    """Mixin to validate date ranges (end_date >= start_date)."""

    @model_validator(mode="after")
    def validate_date_range(self) -> "DateRangeMixin":
        """Ensure end_date is on or after start_date."""
        if hasattr(self, "start_date") and hasattr(self, "end_date"):
            if (
                self.start_date is not None
                and self.end_date is not None
                and self.end_date < self.start_date
            ):
                raise ValueError("end_date must be on or after start_date")
        return self


# Re-export enums for convenience
__all__ = [
    "BaseSchema",
    "TimezoneAwareDatetimeMixin",
    "TimeRangeMixin",
    "DateRangeMixin",
    "PrivacyLevel",
    "WeekBoundary",
    "EntityType",
    "ProjectStatus",
    "ClientStatus",
    "ClientType",
]
