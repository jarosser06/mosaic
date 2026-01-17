"""Summary generator service for natural language query summaries."""

from collections import defaultdict
from typing import cast

from ..models.base import PrivacyLevel
from ..schemas.query import QueryResultEntity, WorkSessionResult


class SummaryGenerator:
    """
    Generate natural language summaries from query results.

    Creates human-readable summaries that respect privacy levels
    and provide meaningful insights about the data returned.
    """

    def generate(
        self,
        results: list[QueryResultEntity],
        include_private: bool = True,
    ) -> str:
        """
        Generate natural language summary from query results.

        Creates a human-readable summary of results, respecting privacy
        levels. For single-user system, privacy filtering is optional.

        Args:
            results: List of query result entities (discriminated union)
            include_private: Include private entities in summary (default: True)

        Returns:
            str: Natural language summary

        Examples:
            >>> generator = SummaryGenerator()
            >>> summary = generator.generate([ws1, ws2, m1], include_private=True)
            >>> summary
            'Found 2 work sessions (16.5 hours) and 1 meeting.'
        """
        if not results:
            return "No results found."

        # Filter by privacy if needed
        filtered_results = results
        if not include_private:
            filtered_results = [
                r
                for r in results
                if not hasattr(r, "privacy_level") or r.privacy_level != PrivacyLevel.PRIVATE
            ]

        if not filtered_results:
            return "No results found (all results are private)."

        # Group results by entity type
        grouped = self._group_by_entity_type(filtered_results)

        # Build summary parts
        summary_parts = []

        # Work sessions summary (with total hours)
        if grouped["work_sessions"]:
            ws_summary = self._summarize_work_sessions(
                cast(list[WorkSessionResult], grouped["work_sessions"])
            )
            summary_parts.append(ws_summary)

        # Meetings summary
        if grouped["meetings"]:
            count = len(grouped["meetings"])
            plural = "meeting" if count == 1 else "meetings"
            summary_parts.append(f"{count} {plural}")

        # Projects summary
        if grouped["projects"]:
            count = len(grouped["projects"])
            plural = "project" if count == 1 else "projects"
            summary_parts.append(f"{count} {plural}")

        # People summary
        if grouped["people"]:
            count = len(grouped["people"])
            plural = "person" if count == 1 else "people"
            summary_parts.append(f"{count} {plural}")

        # Clients summary
        if grouped["clients"]:
            count = len(grouped["clients"])
            plural = "client" if count == 1 else "clients"
            summary_parts.append(f"{count} {plural}")

        # Employers summary
        if grouped["employers"]:
            count = len(grouped["employers"])
            plural = "employer" if count == 1 else "employers"
            summary_parts.append(f"{count} {plural}")

        # Notes summary
        if grouped["notes"]:
            count = len(grouped["notes"])
            plural = "note" if count == 1 else "notes"
            summary_parts.append(f"{count} {plural}")

        # Reminders summary
        if grouped["reminders"]:
            count = len(grouped["reminders"])
            plural = "reminder" if count == 1 else "reminders"
            summary_parts.append(f"{count} {plural}")

        # Users summary
        if grouped["users"]:
            count = len(grouped["users"])
            plural = "user" if count == 1 else "users"
            summary_parts.append(f"{count} {plural}")

        # Employment histories summary
        if grouped["employment_histories"]:
            count = len(grouped["employment_histories"])
            plural = "employment history" if count == 1 else "employment histories"
            summary_parts.append(f"{count} {plural}")

        # Combine parts
        if len(summary_parts) == 1:
            return f"Found {summary_parts[0]}."
        elif len(summary_parts) == 2:
            return f"Found {summary_parts[0]} and {summary_parts[1]}."
        else:
            last_part = summary_parts.pop()
            return f"Found {', '.join(summary_parts)}, and {last_part}."

    def _group_by_entity_type(
        self, results: list[QueryResultEntity]
    ) -> dict[str, list[QueryResultEntity]]:
        """
        Group results by entity type.

        Args:
            results: List of query result entities

        Returns:
            dict[str, list]: Results grouped by entity type (plural keys)
        """
        # Map singular entity_type values to plural keys
        type_mapping = {
            "work_session": "work_sessions",
            "meeting": "meetings",
            "project": "projects",
            "person": "people",
            "client": "clients",
            "employer": "employers",
            "note": "notes",
            "reminder": "reminders",
            "user": "users",
            "employment_history": "employment_histories",
        }

        grouped: dict[str, list[QueryResultEntity]] = defaultdict(list)

        for result in results:
            entity_type = result.entity_type
            # Convert singular to plural key
            plural_key = type_mapping.get(entity_type, f"{entity_type}s")
            grouped[plural_key].append(result)

        return grouped

    def _summarize_work_sessions(self, work_sessions: list[WorkSessionResult]) -> str:
        """
        Summarize work sessions with total hours.

        Args:
            work_sessions: List of WorkSessionResult instances

        Returns:
            str: Summary string with count and total hours
        """
        count = len(work_sessions)
        plural = "work session" if count == 1 else "work sessions"

        # Calculate total hours (sum of Decimals is always Decimal)
        total_hours = sum(ws.duration_hours for ws in work_sessions)

        # Format total hours
        hours_str = f"{total_hours:.1f}"

        return f"{count} {plural} ({hours_str} hours)"
