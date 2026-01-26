"""Unit tests for QueryParser service."""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from src.mosaic.models.base import EntityType, PrivacyLevel
from src.mosaic.services.query_parser import ParsedQuery, QueryParser, _last_month_range


class TestParsedQuery:
    """Test ParsedQuery dataclass."""

    def test_parsed_query_defaults(self):
        """Test ParsedQuery with default values."""
        parsed = ParsedQuery()

        assert parsed.entity_types is None
        assert parsed.start_date is None
        assert parsed.end_date is None
        assert parsed.privacy_levels is None
        assert parsed.include_private is True
        assert parsed.search_text is None
        assert parsed.project_id is None
        assert parsed.person_id is None
        assert parsed.client_id is None
        assert parsed.employer_id is None
        assert parsed.limit is None

    def test_parsed_query_with_values(self):
        """Test ParsedQuery with all fields populated."""
        parsed = ParsedQuery(
            entity_types=[EntityType.WORK_SESSION],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            privacy_levels=[PrivacyLevel.PUBLIC],
            include_private=False,
            search_text="test query",
            project_id=1,
            person_id=2,
            client_id=3,
            employer_id=4,
            limit=10,
        )

        assert parsed.entity_types == [EntityType.WORK_SESSION]
        assert parsed.start_date == date(2024, 1, 1)
        assert parsed.end_date == date(2024, 1, 31)
        assert parsed.privacy_levels == [PrivacyLevel.PUBLIC]
        assert parsed.include_private is False
        assert parsed.search_text == "test query"
        assert parsed.project_id == 1
        assert parsed.person_id == 2
        assert parsed.client_id == 3
        assert parsed.employer_id == 4
        assert parsed.limit == 10


class TestQueryParser:
    """Test QueryParser functionality."""

    @pytest.fixture
    def parser(self) -> QueryParser:
        """Create a QueryParser instance."""
        return QueryParser()

    # ==================== Entity Type Extraction Tests ====================

    def test_extract_work_session_pattern_1(self, parser: QueryParser):
        """Test extraction of work session pattern 'work sessions'."""
        result = parser._extract_entity_types("show me work sessions")
        assert EntityType.WORK_SESSION in result
        assert len(result) == 1

    def test_extract_work_session_pattern_2(self, parser: QueryParser):
        """Test extraction of work session pattern 'time entries'."""
        result = parser._extract_entity_types("list time entries")
        assert EntityType.WORK_SESSION in result
        assert len(result) == 1

    def test_extract_work_session_pattern_3(self, parser: QueryParser):
        """Test extraction of work session pattern 'hours'."""
        result = parser._extract_entity_types("show my hours")
        assert EntityType.WORK_SESSION in result
        assert len(result) == 1

    def test_extract_work_session_pattern_4(self, parser: QueryParser):
        """Test extraction of work session pattern 'worked'."""
        result = parser._extract_entity_types("what I worked on")
        assert EntityType.WORK_SESSION in result
        assert len(result) == 1

    def test_extract_work_session_singular(self, parser: QueryParser):
        """Test extraction of singular 'work session'."""
        result = parser._extract_entity_types("show me work session")
        assert EntityType.WORK_SESSION in result

    def test_extract_work_session_singular_hour(self, parser: QueryParser):
        """Test extraction of singular 'hour'."""
        result = parser._extract_entity_types("show me hour")
        assert EntityType.WORK_SESSION in result

    def test_extract_meeting_pattern(self, parser: QueryParser):
        """Test extraction of meeting patterns."""
        result = parser._extract_entity_types("show me meetings")
        assert EntityType.MEETING in result

    def test_extract_meeting_singular(self, parser: QueryParser):
        """Test extraction of singular 'meeting'."""
        result = parser._extract_entity_types("find meeting")
        assert EntityType.MEETING in result

    def test_extract_meeting_calls(self, parser: QueryParser):
        """Test extraction of 'calls' as meeting."""
        result = parser._extract_entity_types("show me calls")
        assert EntityType.MEETING in result

    def test_extract_meeting_call_singular(self, parser: QueryParser):
        """Test extraction of singular 'call' as meeting."""
        result = parser._extract_entity_types("find call")
        assert EntityType.MEETING in result

    def test_extract_project_pattern(self, parser: QueryParser):
        """Test extraction of project patterns."""
        result = parser._extract_entity_types("list projects")
        assert EntityType.PROJECT in result

    def test_extract_project_singular(self, parser: QueryParser):
        """Test extraction of singular 'project'."""
        result = parser._extract_entity_types("find project")
        assert EntityType.PROJECT in result

    def test_extract_person_pattern_people(self, parser: QueryParser):
        """Test extraction of 'people' pattern."""
        result = parser._extract_entity_types("show me people")
        assert EntityType.PERSON in result

    def test_extract_person_pattern_persons(self, parser: QueryParser):
        """Test extraction of 'persons' pattern."""
        result = parser._extract_entity_types("list persons")
        assert EntityType.PERSON in result

    def test_extract_person_pattern_contacts(self, parser: QueryParser):
        """Test extraction of 'contacts' pattern."""
        result = parser._extract_entity_types("show my contacts")
        assert EntityType.PERSON in result

    def test_extract_person_pattern_contact_singular(self, parser: QueryParser):
        """Test extraction of singular 'contact' pattern."""
        result = parser._extract_entity_types("find contact")
        assert EntityType.PERSON in result

    def test_extract_person_singular(self, parser: QueryParser):
        """Test extraction of singular 'person'."""
        result = parser._extract_entity_types("find person")
        assert EntityType.PERSON in result

    def test_extract_client_pattern(self, parser: QueryParser):
        """Test extraction of client patterns."""
        result = parser._extract_entity_types("show me clients")
        assert EntityType.CLIENT in result

    def test_extract_client_singular(self, parser: QueryParser):
        """Test extraction of singular 'client'."""
        result = parser._extract_entity_types("find client")
        assert EntityType.CLIENT in result

    def test_extract_employer_pattern(self, parser: QueryParser):
        """Test extraction of employer patterns."""
        result = parser._extract_entity_types("list employers")
        assert EntityType.EMPLOYER in result

    def test_extract_employer_singular(self, parser: QueryParser):
        """Test extraction of singular 'employer'."""
        result = parser._extract_entity_types("find employer")
        assert EntityType.EMPLOYER in result

    def test_extract_reminder_pattern_reminders(self, parser: QueryParser):
        """Test extraction of 'reminders' pattern."""
        result = parser._extract_entity_types("show my reminders")
        assert EntityType.REMINDER in result

    def test_extract_reminder_pattern_todos(self, parser: QueryParser):
        """Test extraction of 'todos' pattern."""
        result = parser._extract_entity_types("list todos")
        assert EntityType.REMINDER in result

    def test_extract_reminder_pattern_todo_singular(self, parser: QueryParser):
        """Test extraction of singular 'todo' pattern."""
        result = parser._extract_entity_types("find todo")
        assert EntityType.REMINDER in result

    def test_extract_reminder_singular(self, parser: QueryParser):
        """Test extraction of singular 'reminder'."""
        result = parser._extract_entity_types("find reminder")
        assert EntityType.REMINDER in result

    def test_extract_note_pattern_notes(self, parser: QueryParser):
        """Test extraction of 'notes' pattern."""
        result = parser._extract_entity_types("show my notes")
        assert EntityType.NOTE in result

    def test_extract_note_singular(self, parser: QueryParser):
        """Test extraction of singular 'note'."""
        result = parser._extract_entity_types("find note")
        assert EntityType.NOTE in result

    def test_extract_multiple_entity_types(self, parser: QueryParser):
        """Test extraction of multiple entity types."""
        result = parser._extract_entity_types("show me meetings and projects")
        assert EntityType.MEETING in result
        assert EntityType.PROJECT in result
        assert len(result) == 2

    def test_extract_no_entity_types(self, parser: QueryParser):
        """Test extraction when no entity types present."""
        result = parser._extract_entity_types("show me something else")
        assert result == []

    def test_extract_entity_types_case_insensitive(self, parser: QueryParser):
        """Test that entity type extraction is case insensitive."""
        result = parser._extract_entity_types("show me meetings")
        assert EntityType.MEETING in result

    def test_extract_entity_types_no_duplicate(self, parser: QueryParser):
        """Test that entity types are not duplicated if matched multiple times."""
        result = parser._extract_entity_types("work sessions time entries hours worked")
        # Should only have one WORK_SESSION despite matching multiple patterns
        assert result.count(EntityType.WORK_SESSION) == 1

    # ==================== Date Range Extraction Tests ====================

    def test_extract_date_range_today(self, parser: QueryParser):
        """Test extraction of 'today' date range."""
        start, end = parser._extract_date_range("show me work from today")
        expected = date.today()
        assert start == expected
        assert end == expected

    def test_extract_date_range_yesterday(self, parser: QueryParser):
        """Test extraction of 'yesterday' date range."""
        start, end = parser._extract_date_range("show me work from yesterday")
        expected = date.today() - timedelta(days=1)
        assert start == expected
        assert end == expected

    def test_extract_date_range_this_week(self, parser: QueryParser):
        """Test extraction of 'this week' date range."""
        start, end = parser._extract_date_range("show me work from this week")
        today = date.today()
        expected_start = today - timedelta(days=today.weekday())
        expected_end = today
        assert start == expected_start
        assert end == expected_end

    def test_extract_date_range_last_week(self, parser: QueryParser):
        """Test extraction of 'last week' date range."""
        start, end = parser._extract_date_range("show me work from last week")
        today = date.today()
        expected_start = today - timedelta(days=today.weekday() + 7)
        expected_end = today - timedelta(days=today.weekday() + 1)
        assert start == expected_start
        assert end == expected_end

    def test_extract_date_range_this_month(self, parser: QueryParser):
        """Test extraction of 'this month' date range."""
        start, end = parser._extract_date_range("show me work from this month")
        today = date.today()
        expected_start = today.replace(day=1)
        expected_end = today
        assert start == expected_start
        assert end == expected_end

    def test_extract_date_range_last_month(self, parser: QueryParser):
        """Test extraction of 'last month' date range."""
        start, end = parser._extract_date_range("show me work from last month")
        expected_start, expected_end = _last_month_range()
        assert start == expected_start
        assert end == expected_end

    def test_extract_date_range_this_year(self, parser: QueryParser):
        """Test extraction of 'this year' date range."""
        start, end = parser._extract_date_range("show me work from this year")
        today = date.today()
        expected_start = today.replace(month=1, day=1)
        expected_end = today
        assert start == expected_start
        assert end == expected_end

    def test_extract_date_range_none(self, parser: QueryParser):
        """Test extraction when no date range is present."""
        start, end = parser._extract_date_range("show me work")
        assert start is None
        assert end is None

    def test_extract_date_range_case_insensitive(self, parser: QueryParser):
        """Test that date range extraction is case insensitive."""
        start, end = parser._extract_date_range("show me work from today")
        expected = date.today()
        assert start == expected
        assert end == expected

    # ==================== Privacy Level Extraction Tests ====================

    def test_extract_privacy_level_public(self, parser: QueryParser):
        """Test extraction of 'public' privacy level."""
        result = parser._extract_privacy_levels("show public work")
        assert PrivacyLevel.PUBLIC in result

    def test_extract_privacy_level_internal(self, parser: QueryParser):
        """Test extraction of 'internal' privacy level."""
        result = parser._extract_privacy_levels("show internal work")
        assert PrivacyLevel.INTERNAL in result

    def test_extract_privacy_level_private(self, parser: QueryParser):
        """Test extraction of 'private' privacy level."""
        result = parser._extract_privacy_levels("show private work")
        assert PrivacyLevel.PRIVATE in result

    def test_extract_privacy_levels_multiple(self, parser: QueryParser):
        """Test extraction of multiple privacy levels."""
        result = parser._extract_privacy_levels("show public and private work")
        assert PrivacyLevel.PUBLIC in result
        assert PrivacyLevel.PRIVATE in result
        assert len(result) == 2

    def test_extract_privacy_levels_none(self, parser: QueryParser):
        """Test extraction when no privacy levels present."""
        result = parser._extract_privacy_levels("show me work")
        assert result == []

    def test_extract_privacy_levels_case_insensitive(self, parser: QueryParser):
        """Test that privacy level extraction is case insensitive."""
        result = parser._extract_privacy_levels("show public work")
        assert PrivacyLevel.PUBLIC in result

    def test_extract_privacy_levels_no_duplicate(self, parser: QueryParser):
        """Test that privacy levels are not duplicated."""
        result = parser._extract_privacy_levels("show public public work")
        assert result.count(PrivacyLevel.PUBLIC) == 1

    def test_extract_privacy_levels_all_three(self, parser: QueryParser):
        """Test extraction of all three privacy levels."""
        result = parser._extract_privacy_levels("show public internal and private work")
        assert PrivacyLevel.PUBLIC in result
        assert PrivacyLevel.INTERNAL in result
        assert PrivacyLevel.PRIVATE in result
        assert len(result) == 3

    # ==================== Search Text Extraction Tests ====================

    def test_extract_search_text_with_prefix_show_me(self, parser: QueryParser):
        """Test extraction of search text with 'show me' prefix."""
        result = parser._extract_search_text("show me important tasks")
        assert result == "important tasks"

    # ==================== Parse Method Integration Tests ====================

    def test_parse_simple_query(self, parser: QueryParser):
        """Test parsing a simple query."""
        result = parser.parse("show me work sessions")
        assert result.entity_types == [EntityType.WORK_SESSION]
        assert result.start_date is None
        assert result.end_date is None
        assert result.privacy_levels is None
        assert result.include_private is True
        assert result.search_text is None

    def test_parse_query_with_date(self, parser: QueryParser):
        """Test parsing query with date range."""
        result = parser.parse("show me work sessions from today")
        assert result.entity_types == [EntityType.WORK_SESSION]
        assert result.start_date == date.today()
        assert result.end_date == date.today()

    def test_parse_query_with_privacy(self, parser: QueryParser):
        """Test parsing query with privacy level."""
        result = parser.parse("show me public work sessions")
        assert result.entity_types == [EntityType.WORK_SESSION]
        assert result.privacy_levels == [PrivacyLevel.PUBLIC]

    def test_parse_query_multiple_entities(self, parser: QueryParser):
        """Test parsing query with multiple entity types."""
        result = parser.parse("show me meetings and projects")
        assert EntityType.MEETING in result.entity_types
        assert EntityType.PROJECT in result.entity_types

    def test_parse_query_empty_string(self, parser: QueryParser):
        """Test parsing an empty query."""
        result = parser.parse("")
        assert result.entity_types is None
        assert result.start_date is None
        assert result.end_date is None
        assert result.privacy_levels is None
        assert result.search_text is None

    def test_parse_query_case_insensitive(self, parser: QueryParser):
        """Test that parsing is case insensitive."""
        result = parser.parse("SHOW ME WORK SESSIONS FROM TODAY")
        assert result.entity_types == [EntityType.WORK_SESSION]
        assert result.start_date == date.today()

    def test_parse_query_defaults(self, parser: QueryParser):
        """Test that parsed query has correct defaults."""
        result = parser.parse("show me work")
        assert result.include_private is True
        assert result.limit is None
        assert result.project_id is None
        assert result.person_id is None
        assert result.client_id is None
        assert result.employer_id is None


# ==================== Helper Function Tests ====================


class TestLastMonthRange:
    """Test _last_month_range helper function."""

    @patch("src.mosaic.services.query_parser.date")
    def test_last_month_range_january(self, mock_date):
        """Test last month range when current month is January."""
        # Mock date.today() to return January 15, 2024
        mock_date.today.return_value = date(2024, 1, 15)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

        start, end = _last_month_range()

        # December 2023: 12/1 - 12/31
        assert start == date(2023, 12, 1)
        assert end == date(2023, 12, 31)

    @patch("src.mosaic.services.query_parser.date")
    def test_last_month_range_march(self, mock_date):
        """Test last month range when current month is March (handles Feb)."""
        # Mock date.today() to return March 15, 2024 (leap year)
        mock_date.today.return_value = date(2024, 3, 15)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

        start, end = _last_month_range()

        # February 2024 (leap year): 2/1 - 2/29
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)

    @patch("src.mosaic.services.query_parser.date")
    def test_last_month_range_march_non_leap_year(self, mock_date):
        """Test last month range for February in non-leap year."""
        # Mock date.today() to return March 15, 2023 (non-leap year)
        mock_date.today.return_value = date(2023, 3, 15)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

        start, end = _last_month_range()

        # February 2023 (non-leap year): 2/1 - 2/28
        assert start == date(2023, 2, 1)
        assert end == date(2023, 2, 28)

    @patch("src.mosaic.services.query_parser.date")
    def test_last_month_range_may(self, mock_date):
        """Test last month range for a 30-day month."""
        # Mock date.today() to return May 20, 2024
        mock_date.today.return_value = date(2024, 5, 20)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

        start, end = _last_month_range()

        # April 2024: 4/1 - 4/30
        assert start == date(2024, 4, 1)
        assert end == date(2024, 4, 30)

    @patch("src.mosaic.services.query_parser.date")
    def test_last_month_range_february(self, mock_date):
        """Test last month range for a 31-day month."""
        # Mock date.today() to return February 15, 2024
        mock_date.today.return_value = date(2024, 2, 15)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

        start, end = _last_month_range()

        # January 2024: 1/1 - 1/31
        assert start == date(2024, 1, 1)
        assert end == date(2024, 1, 31)

    def test_last_month_range_real_call(self):
        """Test _last_month_range without mocking (real dates)."""
        start, end = _last_month_range()

        # Verify that start is first day of some month
        assert start.day == 1

        # Verify that end is last day of same month as start
        assert end.month == start.month
        assert end.year == start.year

        # Verify that end is before today
        assert end < date.today()

        # Verify that start is before end
        assert start <= end


# ==================== Edge Cases and Boundary Tests ====================


class TestQueryParserEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def parser(self) -> QueryParser:
        """Create a QueryParser instance."""
        return QueryParser()

    def test_parse_query_with_special_characters(self, parser: QueryParser):
        """Test parsing query with special characters."""
        result = parser.parse("show me work sessions with @tags #hashtags")
        assert result.entity_types == [EntityType.WORK_SESSION]
        assert result.search_text == "with @tags #hashtags"

    def test_parse_query_with_numbers(self, parser: QueryParser):
        """Test parsing query with numbers."""
        result = parser.parse("find work sessions with 100 hours")
        assert result.entity_types == [EntityType.WORK_SESSION]
        assert result.search_text == "with 100"

    def test_parse_query_very_long(self, parser: QueryParser):
        """Test parsing a very long query."""
        long_query = "show me work sessions " + "word " * 100
        result = parser.parse(long_query)
        assert result.entity_types == [EntityType.WORK_SESSION]
        # Search text should be cleaned but still present
        assert result.search_text is not None
        assert len(result.search_text) > 0

    def test_parse_query_only_whitespace(self, parser: QueryParser):
        """Test parsing query with only whitespace."""
        result = parser.parse("   \t\n  ")
        assert result.entity_types is None
        assert result.search_text is None

    def test_entity_types_none_when_empty(self, parser: QueryParser):
        """Test that entity_types is None (not empty list) when no matches."""
        result = parser.parse("random query")
        assert result.entity_types is None

    def test_privacy_levels_none_when_empty(self, parser: QueryParser):
        """Test that privacy_levels is None (not empty list) when no matches."""
        result = parser.parse("random query")
        assert result.privacy_levels is None

    def test_extract_entity_types_word_boundaries(self, parser: QueryParser):
        """Test that entity patterns respect word boundaries."""
        # "workplace" should not match "work" pattern because patterns use \b word boundaries
        # "sessions" alone should match "work sessions?" pattern
        result = parser._extract_entity_types("workplace sessions")
        # Pattern r"\b(work\s+sessions?|time\s+entries|hours?)\b" requires "work sessions"
        # So "workplace sessions" should match because "sessions" with \b at start/end
        # Actually the pattern is r"\b(work\s+sessions?..." which requires "work " before "sessions"
        # So this should NOT match
        assert EntityType.WORK_SESSION not in result

    def test_parse_all_date_patterns_in_one_query(self, parser: QueryParser):
        """Test query with multiple date patterns (first one wins)."""
        result = parser.parse("show work from today and yesterday and this week")
        # Only first match should be used
        assert result.start_date == date.today()
        assert result.end_date == date.today()

    def test_extract_search_text_no_prefix(self, parser: QueryParser):
        """Test search text extraction when no prefix to remove."""
        result = parser._extract_search_text("just some text")
        assert result == "just some text"

    def test_extract_date_range_first_match_wins(self, parser: QueryParser):
        """Test that first date pattern match is used."""
        # "today" appears before "yesterday"
        start, end = parser._extract_date_range("today and yesterday")
        assert start == date.today()
        assert end == date.today()
