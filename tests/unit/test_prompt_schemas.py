"""Unit tests for prompt argument schema validation.

Tests Pydantic schemas that validate prompt arguments for
MCP prompts that accept parameters.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from src.mosaic.schemas.prompts import (
    FindGapsArgs,
    GenerateTimecardArgs,
    SearchContextArgs,
    WeeklyReviewArgs,
)


class TestGenerateTimecardArgs:
    """Test generate-timecard prompt argument validation."""

    def test_generate_timecard_args_all_fields(self):
        """All fields should validate correctly."""
        args = GenerateTimecardArgs(
            employer_name="Test Corp",
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )

        assert args.employer_name == "Test Corp"
        assert args.start_date == date(2024, 1, 15)
        assert args.end_date == date(2024, 1, 19)

    def test_generate_timecard_args_optional_fields(self):
        """All fields should be optional."""
        args = GenerateTimecardArgs()

        assert args.employer_name is None
        assert args.start_date is None
        assert args.end_date is None

    def test_generate_timecard_args_partial_fields(self):
        """Partial field sets should be valid."""
        # Just employer
        args1 = GenerateTimecardArgs(employer_name="Test Corp")
        assert args1.employer_name == "Test Corp"
        assert args1.start_date is None

        # Just dates
        args2 = GenerateTimecardArgs(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        assert args2.employer_name is None
        assert args2.start_date == date(2024, 1, 15)

    def test_generate_timecard_args_end_before_start_raises_error(self):
        """End date before start date should raise validation error."""
        with pytest.raises(ValidationError, match="end_date must be after start_date"):
            GenerateTimecardArgs(
                start_date=date(2024, 1, 19),
                end_date=date(2024, 1, 15),
            )

    def test_generate_timecard_args_same_dates_allowed(self):
        """Same start and end date should be allowed (single day)."""
        args = GenerateTimecardArgs(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
        )

        assert args.start_date == args.end_date

    def test_generate_timecard_args_invalid_employer_name(self):
        """Empty employer name should raise validation error."""
        with pytest.raises(ValidationError):
            GenerateTimecardArgs(employer_name="")

    def test_generate_timecard_args_whitespace_employer_name(self):
        """Whitespace-only employer name should raise validation error."""
        with pytest.raises(ValidationError):
            GenerateTimecardArgs(employer_name="   ")

    def test_generate_timecard_args_string_dates_converted(self):
        """String dates should be converted to date objects."""
        args = GenerateTimecardArgs(
            start_date="2024-01-15",
            end_date="2024-01-19",
        )

        assert isinstance(args.start_date, date)
        assert args.start_date == date(2024, 1, 15)

    def test_generate_timecard_args_invalid_date_format(self):
        """Invalid date format should raise validation error."""
        with pytest.raises(ValidationError):
            GenerateTimecardArgs(start_date="not-a-date")


class TestWeeklyReviewArgs:
    """Test weekly-review prompt argument validation."""

    def test_weekly_review_args_with_week_start(self):
        """Week start should validate correctly."""
        args = WeeklyReviewArgs(week_start=date(2024, 1, 15))

        assert args.week_start == date(2024, 1, 15)

    def test_weekly_review_args_optional_week_start(self):
        """Week start should be optional (defaults to current week)."""
        args = WeeklyReviewArgs()

        assert args.week_start is None

    def test_weekly_review_args_string_date_converted(self):
        """String date should be converted to date object."""
        args = WeeklyReviewArgs(week_start="2024-01-15")

        assert isinstance(args.week_start, date)
        assert args.week_start == date(2024, 1, 15)

    def test_weekly_review_args_invalid_date_format(self):
        """Invalid date format should raise validation error."""
        with pytest.raises(ValidationError):
            WeeklyReviewArgs(week_start="invalid-date")

    def test_weekly_review_args_future_week_allowed(self):
        """Future week start should be allowed."""
        future = date(2025, 12, 31)
        args = WeeklyReviewArgs(week_start=future)

        assert args.week_start == future

    def test_weekly_review_args_past_week_allowed(self):
        """Past week start should be allowed."""
        past = date(2020, 1, 1)
        args = WeeklyReviewArgs(week_start=past)

        assert args.week_start == past


class TestFindGapsArgs:
    """Test find-gaps prompt argument validation."""

    def test_find_gaps_args_with_date_range(self):
        """Date range should validate correctly."""
        args = FindGapsArgs(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )

        assert args.start_date == date(2024, 1, 15)
        assert args.end_date == date(2024, 1, 19)

    def test_find_gaps_args_optional_fields(self):
        """Both fields should be optional (defaults to current week)."""
        args = FindGapsArgs()

        assert args.start_date is None
        assert args.end_date is None

    def test_find_gaps_args_partial_date_range_raises_error(self):
        """Providing only start or only end should raise validation error."""
        with pytest.raises(ValidationError, match="both start_date and end_date required"):
            FindGapsArgs(start_date=date(2024, 1, 15))

        with pytest.raises(ValidationError, match="both start_date and end_date required"):
            FindGapsArgs(end_date=date(2024, 1, 19))

    def test_find_gaps_args_end_before_start_raises_error(self):
        """End date before start date should raise validation error."""
        with pytest.raises(ValidationError, match="end_date must be after start_date"):
            FindGapsArgs(
                start_date=date(2024, 1, 19),
                end_date=date(2024, 1, 15),
            )

    def test_find_gaps_args_same_dates_allowed(self):
        """Same start and end date should be allowed (single day)."""
        args = FindGapsArgs(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
        )

        assert args.start_date == args.end_date

    def test_find_gaps_args_string_dates_converted(self):
        """String dates should be converted to date objects."""
        args = FindGapsArgs(
            start_date="2024-01-15",
            end_date="2024-01-19",
        )

        assert isinstance(args.start_date, date)
        assert isinstance(args.end_date, date)

    def test_find_gaps_args_large_date_range_allowed(self):
        """Large date range (e.g., full year) should be allowed."""
        args = FindGapsArgs(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        assert args.start_date == date(2024, 1, 1)
        assert args.end_date == date(2024, 12, 31)


class TestSearchContextArgs:
    """Test search-context prompt argument validation."""

    def test_search_context_args_with_query(self):
        """Query should validate correctly."""
        args = SearchContextArgs(query="Sarah discussions about auth")

        assert args.query == "Sarah discussions about auth"

    def test_search_context_args_query_required(self):
        """Query should be required."""
        with pytest.raises(ValidationError, match="query"):
            SearchContextArgs()

    def test_search_context_args_empty_query_raises_error(self):
        """Empty query should raise validation error."""
        with pytest.raises(ValidationError):
            SearchContextArgs(query="")

    def test_search_context_args_whitespace_query_raises_error(self):
        """Whitespace-only query should raise validation error."""
        with pytest.raises(ValidationError):
            SearchContextArgs(query="   ")

    def test_search_context_args_long_query_allowed(self):
        """Long query strings should be allowed."""
        long_query = "Find all meetings with Sarah about the authentication " * 10
        args = SearchContextArgs(query=long_query)

        assert args.query == long_query

    def test_search_context_args_special_characters_allowed(self):
        """Special characters in query should be allowed."""
        args = SearchContextArgs(query="auth@2024 #bug-fix (urgent)")

        assert args.query == "auth@2024 #bug-fix (urgent)"

    def test_search_context_args_unicode_query_allowed(self):
        """Unicode characters in query should be allowed."""
        args = SearchContextArgs(query="Discussion with François about café")

        assert args.query == "Discussion with François about café"


class TestPromptSchemaDefaults:
    """Test default values and field descriptions for prompt schemas."""

    def test_generate_timecard_args_has_field_descriptions(self):
        """Schema should have Field descriptions for MCP client."""
        schema = GenerateTimecardArgs.model_json_schema()

        assert "properties" in schema
        assert "employer_name" in schema["properties"]
        assert "description" in schema["properties"]["employer_name"]

    def test_weekly_review_args_has_field_descriptions(self):
        """Schema should have Field descriptions for MCP client."""
        schema = WeeklyReviewArgs.model_json_schema()

        assert "properties" in schema
        assert "week_start" in schema["properties"]
        assert "description" in schema["properties"]["week_start"]

    def test_find_gaps_args_has_field_descriptions(self):
        """Schema should have Field descriptions for MCP client."""
        schema = FindGapsArgs.model_json_schema()

        assert "properties" in schema
        assert "start_date" in schema["properties"]
        assert "description" in schema["properties"]["start_date"]

    def test_search_context_args_has_field_descriptions(self):
        """Schema should have Field descriptions for MCP client."""
        schema = SearchContextArgs.model_json_schema()

        assert "properties" in schema
        assert "query" in schema["properties"]
        assert "description" in schema["properties"]["query"]

    def test_all_schemas_export_valid_json_schema(self):
        """All schemas should export valid JSON schema for MCP."""
        schemas = [
            GenerateTimecardArgs,
            WeeklyReviewArgs,
            FindGapsArgs,
            SearchContextArgs,
        ]

        for schema_cls in schemas:
            schema = schema_cls.model_json_schema()
            assert "type" in schema
            assert schema["type"] == "object"
            assert "properties" in schema


class TestPromptSchemaErrorMessages:
    """Test that validation errors have helpful messages."""

    def test_generate_timecard_date_validation_message(self):
        """Date validation should have clear error message."""
        try:
            GenerateTimecardArgs(
                start_date=date(2024, 1, 19),
                end_date=date(2024, 1, 15),
            )
            pytest.fail("Should have raised ValidationError")
        except ValidationError as e:
            error_dict = e.errors()[0]
            assert "end_date must be after start_date" in str(error_dict)

    def test_find_gaps_partial_range_message(self):
        """Partial date range should have clear error message."""
        try:
            FindGapsArgs(start_date=date(2024, 1, 15))
            pytest.fail("Should have raised ValidationError")
        except ValidationError as e:
            error_dict = e.errors()[0]
            assert "both start_date and end_date required" in str(error_dict)

    def test_search_context_empty_query_message(self):
        """Empty query should have clear error message."""
        try:
            SearchContextArgs(query="")
            pytest.fail("Should have raised ValidationError")
        except ValidationError as e:
            error_dict = e.errors()[0]
            assert "query" in str(error_dict).lower()

    def test_all_schemas_provide_field_level_errors(self):
        """Validation errors should point to specific fields."""
        schemas_with_errors = [
            (
                GenerateTimecardArgs,
                {"start_date": date(2024, 1, 19), "end_date": date(2024, 1, 15)},
                ["start_date", "end_date"],
            ),
            (
                FindGapsArgs,
                {"start_date": date(2024, 1, 15)},
                ["start_date", "end_date"],
            ),
            (SearchContextArgs, {"query": ""}, ["query"]),
        ]

        for schema_cls, invalid_data, expected_fields in schemas_with_errors:
            try:
                schema_cls(**invalid_data)
                pytest.fail(f"Should have raised ValidationError for {schema_cls.__name__}")
            except ValidationError as e:
                error_fields = [err["loc"][0] for err in e.errors()]
                assert any(
                    field in error_fields for field in expected_fields
                ), f"Expected error in {expected_fields}, got {error_fields}"
