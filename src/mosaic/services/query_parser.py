"""Query parsing service for natural language queries."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from ..models.base import ClientStatus, EntityType, PrivacyLevel, ProjectStatus


@dataclass
class ParsedQuery:
    """
    Parsed natural language query with extracted filters.

    Contains all filters extracted from user query to be passed
    to QueryService.flexible_query().
    """

    entity_types: list[EntityType] | None = None
    start_date: date | None = None
    end_date: date | None = None
    privacy_levels: list[PrivacyLevel] | None = None
    include_private: bool = True
    search_text: str | None = None
    project_id: int | None = None
    person_id: int | None = None
    client_id: int | None = None
    employer_id: int | None = None
    limit: int | None = None
    project_status: str | None = None
    client_status: str | None = None


class QueryParser:
    """
    Pattern-based natural language query parser.

    Extracts entity types, filters, and date ranges from natural language
    queries WITHOUT using LLMs. Uses regex patterns for common query forms.
    """

    # Entity type patterns
    ENTITY_PATTERNS = {
        EntityType.WORK_SESSION: [
            r"\b(work\s+sessions?|time\s+entries|hours?)\b",
            r"\bworked\b",
        ],
        EntityType.MEETING: [r"\b(meetings?|calls?)\b"],
        EntityType.PROJECT: [r"\b(projects?)\b"],
        EntityType.PERSON: [r"\b(people|persons?|contacts?)\b"],
        EntityType.CLIENT: [r"\b(clients?)\b"],
        EntityType.EMPLOYER: [r"\b(employers?)\b"],
        EntityType.NOTE: [r"\b(notes?)\b"],
        EntityType.REMINDER: [r"\b(reminders?|todos?)\b"],
    }

    # Date range patterns - use regex for flexible matching
    DATE_PATTERNS: dict[str, "Callable[[], tuple[date, date]]"] = {
        r"\btoday\b": lambda: (date.today(), date.today()),
        r"\byesterday\b": lambda: (
            date.today() - timedelta(days=1),
            date.today() - timedelta(days=1),
        ),
        r"\bthis\s+week\b": lambda: (
            date.today() - timedelta(days=date.today().weekday()),
            date.today(),
        ),
        r"\blast\s+week\b": lambda: (
            date.today() - timedelta(days=date.today().weekday() + 7),
            date.today() - timedelta(days=date.today().weekday() + 1),
        ),
        r"\bthis\s+month\b": lambda: (date.today().replace(day=1), date.today()),
        r"\blast\s+month\b": lambda: _last_month_range(),
        r"\bthis\s+year\b": lambda: (date.today().replace(month=1, day=1), date.today()),
    }

    # Month name patterns - dynamically matches month names
    MONTH_NAMES = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    # Privacy level patterns
    PRIVACY_PATTERNS = {
        PrivacyLevel.PUBLIC: [r"\bpublic\b"],
        PrivacyLevel.INTERNAL: [r"\binternal\b"],
        PrivacyLevel.PRIVATE: [r"\bprivate\b"],
    }

    # Project status patterns
    PROJECT_STATUS_PATTERNS = {
        ProjectStatus.ACTIVE: [r"\bactive\b"],
        ProjectStatus.PAUSED: [r"\bpaused\b"],
        ProjectStatus.COMPLETED: [r"\bcompleted\b"],
    }

    # Client status patterns
    CLIENT_STATUS_PATTERNS = {
        ClientStatus.ACTIVE: [r"\bactive\b"],
        ClientStatus.PAST: [r"\bpast\b"],
    }

    def parse(self, query_text: str) -> ParsedQuery:
        """
        Parse natural language query into structured filters.

        Uses pattern matching to extract:
        - Entity types (work sessions, meetings, projects, etc.)
        - Date ranges (last week, this month, etc.)
        - Privacy levels (public, internal, private)
        - Status filters (active, paused, completed)
        - Text search terms (remaining words after pattern extraction)

        Args:
            query_text: Natural language query string

        Returns:
            ParsedQuery: Structured filters for QueryService

        Examples:
            >>> parser = QueryParser()
            >>> parsed = parser.parse("Show me work sessions from last week")
            >>> parsed.entity_types
            [EntityType.WORK_SESSION]
            >>> parsed.start_date
            datetime.date(2026, 1, 6)
        """
        query_lower = query_text.lower()

        # Extract entity types
        entity_types = self._extract_entity_types(query_lower)

        # Extract date range
        start_date, end_date = self._extract_date_range(query_lower)

        # Extract privacy levels
        privacy_levels = self._extract_privacy_levels(query_lower)

        # Extract status filters
        project_status = self._extract_project_status(query_lower)
        client_status = self._extract_client_status(query_lower)

        # Extract search text (words not part of patterns)
        search_text = self._extract_search_text(query_text)

        # Build ParsedQuery
        return ParsedQuery(
            entity_types=entity_types if entity_types else None,
            start_date=start_date,
            end_date=end_date,
            privacy_levels=privacy_levels if privacy_levels else None,
            include_private=True,  # Single-user system, show all by default
            search_text=search_text if search_text else None,
            project_status=project_status,
            client_status=client_status,
            limit=None,  # No limit by default
        )

    def _extract_entity_types(self, query_lower: str) -> list[EntityType]:
        """
        Extract entity types from query text.

        Args:
            query_lower: Lowercase query text

        Returns:
            list[EntityType]: Matched entity types (empty if none found)
        """
        entity_types = []
        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    entity_types.append(entity_type)
                    break  # Only add each entity type once

        return entity_types

    def _extract_date_range(self, query_lower: str) -> tuple[date | None, date | None]:
        """
        Extract date range from query text.

        Args:
            query_lower: Lowercase query text

        Returns:
            tuple[date | None, date | None]: (start_date, end_date)
        """
        import re

        # Check date patterns (regex)
        for pattern_regex, range_func in self.DATE_PATTERNS.items():
            if re.search(pattern_regex, query_lower):
                return range_func()

        # Check month names
        for month_name, month_num in self.MONTH_NAMES.items():
            if month_name in query_lower:
                # Extract month range for current year
                year = date.today().year
                # First day of month
                start = date(year, month_num, 1)
                # Last day of month
                if month_num == 12:
                    end = date(year, 12, 31)
                else:
                    end = date(year, month_num + 1, 1) - timedelta(days=1)
                return (start, end)

        return (None, None)

    def _extract_privacy_levels(self, query_lower: str) -> list[PrivacyLevel]:
        """
        Extract privacy levels from query text.

        Args:
            query_lower: Lowercase query text

        Returns:
            list[PrivacyLevel]: Matched privacy levels (empty if none found)
        """
        privacy_levels = []
        for privacy_level, patterns in self.PRIVACY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    privacy_levels.append(privacy_level)
                    break

        return privacy_levels

    def _extract_project_status(self, query_lower: str) -> str | None:
        """
        Extract project status from query text.

        Args:
            query_lower: Lowercase query text

        Returns:
            str | None: Matched project status value or None
        """
        for status, patterns in self.PROJECT_STATUS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return status.value

        return None

    def _extract_client_status(self, query_lower: str) -> str | None:
        """
        Extract client status from query text.

        Args:
            query_lower: Lowercase query text

        Returns:
            str | None: Matched client status value or None
        """
        for status, patterns in self.CLIENT_STATUS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return status.value

        return None

    def _extract_search_text(self, query_text: str) -> str | None:
        """
        Extract search text from query.

        Removes common query prefixes and date/entity patterns
        to get the core search terms.

        Args:
            query_text: Original query text

        Returns:
            str | None: Search text or None if empty
        """
        # Remove common query prefixes
        text = re.sub(
            r"^(show\s+me|find|search|get|list|what|how\s+many)\s+",
            "",
            query_text,
            flags=re.IGNORECASE,
        )

        # Remove date patterns (regex)
        for pattern_text in self.DATE_PATTERNS.keys():
            text = re.sub(pattern_text, "", text, flags=re.IGNORECASE)

        # Remove month names
        for month_name in self.MONTH_NAMES.keys():
            text = re.sub(rf"\b{month_name}\b", "", text, flags=re.IGNORECASE)

        # Remove entity type patterns
        for patterns in self.ENTITY_PATTERNS.values():
            for pattern in patterns:
                text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Remove privacy patterns
        for patterns in self.PRIVACY_PATTERNS.values():
            for pattern in patterns:
                text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Remove project status patterns
        for patterns in self.PROJECT_STATUS_PATTERNS.values():
            for pattern in patterns:
                text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Remove client status patterns
        for patterns in self.CLIENT_STATUS_PATTERNS.values():
            for pattern in patterns:
                text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Remove filler words and prepositions
        # Also includes common entity-related words that appear in natural queries
        # (work, meet, note, remind, track, log, record)
        filler_words = (
            r"\b(did|do|does|is|are|was|were|have|has|had|in|on|at|for|"
            r"from|to|the|a|an|i|my|me|work|worked|meet|met|note|noted|"
            r"remind|reminded|track|tracked|log|logged|record|recorded)\b"
        )
        text = re.sub(filler_words, "", text, flags=re.IGNORECASE)

        # Remove punctuation
        text = re.sub(r"[?!,.]", "", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Return None if empty
        return text if text else None


def _last_month_range() -> tuple[date, date]:
    """
    Calculate last month's date range.

    Returns:
        tuple[date, date]: (first_day, last_day) of last month
    """
    today = date.today()
    # First day of current month
    first_of_this_month = today.replace(day=1)
    # Last day of last month
    last_of_last_month = first_of_this_month - timedelta(days=1)
    # First day of last month
    first_of_last_month = last_of_last_month.replace(day=1)

    return (first_of_last_month, last_of_last_month)
