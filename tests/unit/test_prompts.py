"""Unit tests for MCP prompt helper functions.

Tests prompt generation helpers that create dynamic, database-driven
guidance for Claude based on current system state.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.client import Client
from src.mosaic.models.employer import Employer
from src.mosaic.models.person import Person
from src.mosaic.models.project import Project, ProjectStatus
from src.mosaic.models.reminder import Reminder
from src.mosaic.prompts import (
    generate_add_person_prompt,
    generate_find_gaps_prompt,
    generate_generate_timecard_prompt,
    generate_log_meeting_prompt,
    generate_log_work_prompt,
    generate_reminder_review_prompt,
    generate_search_context_prompt,
    generate_weekly_review_prompt,
)


class TestLogWorkPrompt:
    """Test log-work prompt helper (zero args, shows active projects)."""

    @pytest.mark.asyncio
    async def test_log_work_prompt_with_active_projects(
        self, test_session: AsyncSession, employer: Employer, client: Client
    ):
        """Log work prompt should list active projects."""
        # Create active projects
        project1 = Project(
            name="Auth Module",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        project2 = Project(
            name="Dashboard",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        test_session.add_all([project1, project2])
        await test_session.commit()

        prompt = await generate_log_work_prompt(test_session)

        assert "Auth Module" in prompt
        assert "Dashboard" in prompt
        assert "active" in prompt.lower()

    @pytest.mark.asyncio
    async def test_log_work_prompt_excludes_completed_projects(
        self, test_session: AsyncSession, employer: Employer, client: Client
    ):
        """Log work prompt should not list completed projects."""
        active = Project(
            name="Active Project",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        completed = Project(
            name="Completed Project",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.COMPLETED,
        )
        test_session.add_all([active, completed])
        await test_session.commit()

        prompt = await generate_log_work_prompt(test_session)

        assert "Active Project" in prompt
        assert "Completed Project" not in prompt

    @pytest.mark.asyncio
    async def test_log_work_prompt_with_no_projects(self, test_session: AsyncSession):
        """Log work prompt should handle no active projects gracefully."""
        prompt = await generate_log_work_prompt(test_session)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "no active projects" in prompt.lower() or "create a project" in prompt.lower()

    @pytest.mark.asyncio
    async def test_log_work_prompt_groups_by_employer(
        self, test_session: AsyncSession, employer: Employer, client: Client
    ):
        """Log work prompt should group projects by employer."""
        # Create second employer
        employer2 = Employer(name="Personal", is_current=False)
        test_session.add(employer2)
        await test_session.commit()

        # Projects for different employers
        proj1 = Project(
            name="Work Project",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        proj2 = Project(
            name="Personal Project",
            on_behalf_of_id=employer2.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        test_session.add_all([proj1, proj2])
        await test_session.commit()

        prompt = await generate_log_work_prompt(test_session)

        assert employer.name in prompt
        assert employer2.name in prompt


class TestLogMeetingPrompt:
    """Test log-meeting prompt helper (zero args, shows people/projects)."""

    @pytest.mark.asyncio
    async def test_log_meeting_prompt_lists_people(
        self, test_session: AsyncSession, person: Person
    ):
        """Log meeting prompt should list known people."""
        person2 = Person(full_name="Jane Smith", email="jane@example.com")
        test_session.add(person2)
        await test_session.commit()

        prompt = await generate_log_meeting_prompt(test_session)

        assert person.full_name in prompt
        assert "Jane Smith" in prompt

    @pytest.mark.asyncio
    async def test_log_meeting_prompt_lists_active_projects(
        self, test_session: AsyncSession, project: Project
    ):
        """Log meeting prompt should list active projects for association."""
        prompt = await generate_log_meeting_prompt(test_session)

        assert project.name in prompt

    @pytest.mark.asyncio
    async def test_log_meeting_prompt_with_no_people(self, test_session: AsyncSession):
        """Log meeting prompt should handle no people gracefully."""
        prompt = await generate_log_meeting_prompt(test_session)

        assert isinstance(prompt, str)
        assert "people" in prompt.lower() or "person" in prompt.lower()

    @pytest.mark.asyncio
    async def test_log_meeting_prompt_includes_stakeholders(self, test_session: AsyncSession):
        """Log meeting prompt should highlight stakeholders."""
        stakeholder = Person(
            full_name="Sarah Johnson",
            email="sarah@client.com",
            is_stakeholder=True,
        )
        test_session.add(stakeholder)
        await test_session.commit()

        prompt = await generate_log_meeting_prompt(test_session)

        assert "Sarah Johnson" in prompt
        assert "stakeholder" in prompt.lower()


class TestAddPersonPrompt:
    """Test add-person prompt helper (zero args, shows existing people)."""

    @pytest.mark.asyncio
    async def test_add_person_prompt_lists_existing_people(
        self, test_session: AsyncSession, person: Person
    ):
        """Add person prompt should list existing people to avoid duplicates."""
        prompt = await generate_add_person_prompt(test_session)

        assert person.full_name in prompt
        assert person.email in prompt

    @pytest.mark.asyncio
    async def test_add_person_prompt_with_no_people(self, test_session: AsyncSession):
        """Add person prompt should handle empty database."""
        prompt = await generate_add_person_prompt(test_session)

        assert isinstance(prompt, str)
        assert "first person" in prompt.lower() or "no existing" in prompt.lower()

    @pytest.mark.asyncio
    async def test_add_person_prompt_shows_duplicate_warning(
        self, test_session: AsyncSession, person: Person
    ):
        """Add person prompt should warn about potential duplicates."""
        prompt = await generate_add_person_prompt(test_session)

        assert "duplicate" in prompt.lower() or "already exists" in prompt.lower()


class TestGenerateTimecardPrompt:
    """Test generate-timecard prompt helper (args: employer optional, date_range optional)."""

    @pytest.mark.asyncio
    async def test_timecard_prompt_without_args(self, test_session: AsyncSession):
        """Timecard prompt with no args should show employer options."""
        employer1 = Employer(name="Test Corp", is_current=True)
        employer2 = Employer(name="Personal", is_current=False)
        test_session.add_all([employer1, employer2])
        await test_session.commit()

        prompt = await generate_generate_timecard_prompt(test_session)

        assert "Test Corp" in prompt
        assert "Personal" in prompt
        assert "employer" in prompt.lower()

    @pytest.mark.asyncio
    async def test_timecard_prompt_with_employer_arg(
        self, test_session: AsyncSession, employer: Employer
    ):
        """Timecard prompt with employer should show date range guidance."""
        prompt = await generate_generate_timecard_prompt(test_session, employer_name=employer.name)

        assert employer.name in prompt
        assert "date" in prompt.lower() or "range" in prompt.lower()

    @pytest.mark.asyncio
    async def test_timecard_prompt_with_all_args(
        self, test_session: AsyncSession, employer: Employer
    ):
        """Timecard prompt with all args should show preview."""
        start_date = date(2024, 1, 15)
        end_date = date(2024, 1, 19)

        prompt = await generate_generate_timecard_prompt(
            test_session,
            employer_name=employer.name,
            start_date=start_date,
            end_date=end_date,
        )

        assert employer.name in prompt
        assert "2024-01-15" in prompt or "Jan" in prompt
        assert "generate" in prompt.lower()

    @pytest.mark.asyncio
    async def test_timecard_prompt_with_no_work_sessions(
        self, test_session: AsyncSession, employer: Employer
    ):
        """Timecard prompt should warn if no work sessions exist."""
        prompt = await generate_generate_timecard_prompt(
            test_session,
            employer_name=employer.name,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        assert "no work sessions" in prompt.lower() or "no hours" in prompt.lower()


class TestWeeklyReviewPrompt:
    """Test weekly-review prompt helper (args: week optional)."""

    @pytest.mark.asyncio
    async def test_weekly_review_prompt_current_week(self, test_session: AsyncSession):
        """Weekly review for current week should summarize activity."""
        prompt = await generate_weekly_review_prompt(test_session)

        assert "week" in prompt.lower()
        assert "review" in prompt.lower()

    @pytest.mark.asyncio
    async def test_weekly_review_prompt_specific_week(self, test_session: AsyncSession):
        """Weekly review for specific week should show date range."""
        week_start = date(2024, 1, 15)

        prompt = await generate_weekly_review_prompt(test_session, week_start=week_start)

        assert "2024-01-15" in prompt or "Jan" in prompt
        assert "week" in prompt.lower()

    @pytest.mark.asyncio
    async def test_weekly_review_prompt_includes_metrics(
        self, test_session: AsyncSession, project: Project
    ):
        """Weekly review prompt should include key metrics."""
        # Create work session for the week
        from src.mosaic.models.work_session import WorkSession

        session = WorkSession(
            date=date.today(),
            project_id=project.id,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            duration_hours=Decimal("8.0"),
            summary="Test work",
        )
        test_session.add(session)
        await test_session.commit()

        prompt = await generate_weekly_review_prompt(test_session)

        assert "hours" in prompt.lower() or "duration" in prompt.lower()


class TestFindGapsPrompt:
    """Test find-gaps prompt helper (args: date_range optional)."""

    @pytest.mark.asyncio
    async def test_find_gaps_prompt_current_week(self, test_session: AsyncSession):
        """Find gaps for current week should analyze work coverage."""
        prompt = await generate_find_gaps_prompt(test_session)

        assert "gap" in prompt.lower()
        assert "missing" in prompt.lower() or "unlogged" in prompt.lower()

    @pytest.mark.asyncio
    async def test_find_gaps_prompt_with_date_range(self, test_session: AsyncSession):
        """Find gaps with date range should show specific period."""
        start = date(2024, 1, 15)
        end = date(2024, 1, 19)

        prompt = await generate_find_gaps_prompt(test_session, start_date=start, end_date=end)

        assert "2024-01-15" in prompt or "Jan" in prompt
        assert "gap" in prompt.lower()

    @pytest.mark.asyncio
    async def test_find_gaps_prompt_identifies_workdays_without_logs(
        self, test_session: AsyncSession
    ):
        """Find gaps should identify workdays with no logged time."""
        # Empty week should show gaps
        prompt = await generate_find_gaps_prompt(test_session)

        assert "day" in prompt.lower()


class TestSearchContextPrompt:
    """Test search-context prompt helper (args: query REQUIRED)."""

    @pytest.mark.asyncio
    async def test_search_context_prompt_with_query(self, test_session: AsyncSession):
        """Search context with query should provide search guidance."""
        query = "Sarah discussions about auth"

        prompt = await generate_search_context_prompt(test_session, query=query)

        assert query in prompt
        assert "search" in prompt.lower()

    @pytest.mark.asyncio
    async def test_search_context_prompt_suggests_filters(self, test_session: AsyncSession):
        """Search context should suggest relevant filters."""
        query = "project meetings"

        prompt = await generate_search_context_prompt(test_session, query=query)

        assert "filter" in prompt.lower() or "refine" in prompt.lower()

    @pytest.mark.asyncio
    async def test_search_context_prompt_without_query_raises_error(
        self, test_session: AsyncSession
    ):
        """Search context without query should raise error."""
        with pytest.raises(ValueError, match="query is required"):
            await generate_search_context_prompt(test_session)


class TestReminderReviewPrompt:
    """Test reminder-review prompt helper (zero args, shows pending reminders)."""

    @pytest.mark.asyncio
    async def test_reminder_review_prompt_lists_pending_reminders(self, test_session: AsyncSession):
        """Reminder review should list pending reminders."""
        reminder1 = Reminder(
            reminder_time=datetime.now(timezone.utc),
            message="Follow up with Sarah",
            is_completed=False,
        )
        reminder2 = Reminder(
            reminder_time=datetime.now(timezone.utc),
            message="Review spec",
            is_completed=False,
        )
        test_session.add_all([reminder1, reminder2])
        await test_session.commit()

        prompt = await generate_reminder_review_prompt(test_session)

        assert "Follow up with Sarah" in prompt
        assert "Review spec" in prompt

    @pytest.mark.asyncio
    async def test_reminder_review_prompt_excludes_completed(self, test_session: AsyncSession):
        """Reminder review should exclude completed reminders."""
        pending = Reminder(
            reminder_time=datetime.now(timezone.utc),
            message="Pending task",
            is_completed=False,
        )
        completed = Reminder(
            reminder_time=datetime.now(timezone.utc),
            message="Completed task",
            is_completed=True,
        )
        test_session.add_all([pending, completed])
        await test_session.commit()

        prompt = await generate_reminder_review_prompt(test_session)

        assert "Pending task" in prompt
        assert "Completed task" not in prompt

    @pytest.mark.asyncio
    async def test_reminder_review_prompt_with_no_reminders(self, test_session: AsyncSession):
        """Reminder review with no reminders should indicate empty state."""
        prompt = await generate_reminder_review_prompt(test_session)

        assert "no pending reminders" in prompt.lower() or "no reminders" in prompt.lower()

    @pytest.mark.asyncio
    async def test_reminder_review_prompt_sorts_by_due_time(self, test_session: AsyncSession):
        """Reminder review should sort reminders by due time."""
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        later = Reminder(
            reminder_time=now + timedelta(hours=2),
            message="Later reminder",
            is_completed=False,
        )
        sooner = Reminder(
            reminder_time=now + timedelta(hours=1),
            message="Sooner reminder",
            is_completed=False,
        )
        test_session.add_all([later, sooner])
        await test_session.commit()

        prompt = await generate_reminder_review_prompt(test_session)

        # Sooner should appear before later in prompt
        sooner_pos = prompt.index("Sooner reminder")
        later_pos = prompt.index("Later reminder")
        assert sooner_pos < later_pos


class TestPromptErrorHandling:
    """Test error handling for prompt generation."""

    @pytest.mark.asyncio
    async def test_all_prompt_generators_exist(self, test_session: AsyncSession):
        """All required prompt generators should be defined."""
        # This test ensures all required functions exist
        assert callable(generate_log_work_prompt)
        assert callable(generate_log_meeting_prompt)
        assert callable(generate_add_person_prompt)
        assert callable(generate_generate_timecard_prompt)
        assert callable(generate_weekly_review_prompt)
        assert callable(generate_find_gaps_prompt)
        assert callable(generate_search_context_prompt)
        assert callable(generate_reminder_review_prompt)

    @pytest.mark.asyncio
    async def test_all_prompts_return_non_empty_strings(self, test_session: AsyncSession):
        """All prompt generators should return non-empty content."""
        generators = [
            (generate_log_work_prompt, {}),
            (generate_log_meeting_prompt, {}),
            (generate_add_person_prompt, {}),
            (generate_generate_timecard_prompt, {}),
            (generate_weekly_review_prompt, {}),
            (generate_find_gaps_prompt, {}),
            (generate_search_context_prompt, {"query": "test"}),
            (generate_reminder_review_prompt, {}),
        ]

        for gen, kwargs in generators:
            content = await gen(test_session, **kwargs)
            assert isinstance(content, str)
            assert len(content) > 0
            assert len(content) > 20  # Meaningful content
