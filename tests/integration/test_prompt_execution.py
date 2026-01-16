"""Integration tests for MCP prompt execution.

Tests end-to-end prompt retrieval through real MCP server,
including argument validation and dynamic content generation.
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
from src.mosaic.models.work_session import WorkSession


class TestPromptRegistration:
    """Test that all prompts are registered with MCP server."""

    @pytest.mark.asyncio
    async def test_mcp_server_has_prompts(self, mcp_server):
        """MCP server should have prompts registered."""
        assert hasattr(mcp_server, "list_prompts")

    @pytest.mark.asyncio
    async def test_list_all_prompts(self, mcp_server):
        """Should be able to list all available prompts."""
        prompts = await mcp_server.list_prompts()

        assert isinstance(prompts, list)
        assert len(prompts) >= 8  # At least 8 prompts defined

    @pytest.mark.asyncio
    async def test_all_required_prompts_registered(self, mcp_server):
        """All 8 required prompts should be registered."""
        prompts = await mcp_server.list_prompts()
        prompt_names = [p.name for p in prompts]

        required_prompts = [
            "log-work",
            "log-meeting",
            "add-person",
            "generate-timecard",
            "weekly-review",
            "find-gaps",
            "search-context",
            "reminder-review",
        ]

        for required in required_prompts:
            assert required in prompt_names, f"Required prompt {required} not registered"


class TestLogWorkPrompt:
    """Test log-work prompt execution (zero args, shows active projects)."""

    @pytest.mark.asyncio
    async def test_log_work_prompt_with_active_projects(
        self,
        mcp_server,
        test_session: AsyncSession,
        employer: Employer,
        client: Client,
    ):
        """Log work prompt should show active projects."""
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

        # Get prompt
        prompt_response = await mcp_server.get_prompt("log-work")

        assert "Auth Module" in prompt_response.messages[0].content.text
        assert "Dashboard" in prompt_response.messages[0].content.text

    @pytest.mark.asyncio
    async def test_log_work_prompt_excludes_completed(
        self,
        mcp_server,
        test_session: AsyncSession,
        employer: Employer,
        client: Client,
    ):
        """Log work prompt should not show completed projects."""
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

        prompt_response = await mcp_server.get_prompt("log-work")

        content = prompt_response.messages[0].content.text
        assert "Active Project" in content
        assert "Completed Project" not in content

    @pytest.mark.asyncio
    async def test_log_work_prompt_with_no_projects(self, mcp_server, test_session: AsyncSession):
        """Log work prompt should handle no projects gracefully."""
        prompt_response = await mcp_server.get_prompt("log-work")

        content = prompt_response.messages[0].content.text
        assert "no active projects" in content.lower() or "create" in content.lower()


class TestLogMeetingPrompt:
    """Test log-meeting prompt execution (zero args, shows people/projects)."""

    @pytest.mark.asyncio
    async def test_log_meeting_prompt_lists_people(
        self,
        mcp_server,
        test_session: AsyncSession,
        person: Person,
    ):
        """Log meeting prompt should list known people."""
        person2 = Person(full_name="Jane Smith", email="jane@example.com")
        test_session.add(person2)
        await test_session.commit()

        prompt_response = await mcp_server.get_prompt("log-meeting")

        content = prompt_response.messages[0].content.text
        assert person.full_name in content
        assert "Jane Smith" in content

    @pytest.mark.asyncio
    async def test_log_meeting_prompt_lists_projects(
        self, mcp_server, test_session: AsyncSession, project: Project
    ):
        """Log meeting prompt should list active projects."""
        prompt_response = await mcp_server.get_prompt("log-meeting")

        content = prompt_response.messages[0].content.text
        assert project.name in content

    @pytest.mark.asyncio
    async def test_log_meeting_prompt_highlights_stakeholders(
        self, mcp_server, test_session: AsyncSession
    ):
        """Log meeting prompt should highlight stakeholders."""
        stakeholder = Person(
            full_name="Sarah Johnson",
            email="sarah@client.com",
            is_stakeholder=True,
        )
        test_session.add(stakeholder)
        await test_session.commit()

        prompt_response = await mcp_server.get_prompt("log-meeting")

        content = prompt_response.messages[0].content.text
        assert "Sarah Johnson" in content
        assert "stakeholder" in content.lower()


class TestAddPersonPrompt:
    """Test add-person prompt execution (zero args, shows existing people)."""

    @pytest.mark.asyncio
    async def test_add_person_prompt_lists_existing(
        self, mcp_server, test_session: AsyncSession, person: Person
    ):
        """Add person prompt should list existing people."""
        prompt_response = await mcp_server.get_prompt("add-person")

        content = prompt_response.messages[0].content.text
        assert person.full_name in content
        assert person.email in content

    @pytest.mark.asyncio
    async def test_add_person_prompt_with_no_people(self, mcp_server, test_session: AsyncSession):
        """Add person prompt should handle empty database."""
        prompt_response = await mcp_server.get_prompt("add-person")

        content = prompt_response.messages[0].content.text
        assert "first person" in content.lower() or "no existing" in content.lower()

    @pytest.mark.asyncio
    async def test_add_person_prompt_warns_duplicates(
        self, mcp_server, test_session: AsyncSession, person: Person
    ):
        """Add person prompt should warn about duplicates."""
        prompt_response = await mcp_server.get_prompt("add-person")

        content = prompt_response.messages[0].content.text
        assert "duplicate" in content.lower() or "already" in content.lower()


class TestGenerateTimecardPrompt:
    """Test generate-timecard prompt execution (args: employer, date_range optional)."""

    @pytest.mark.asyncio
    async def test_generate_timecard_prompt_no_args(
        self, mcp_server, test_session: AsyncSession, employer: Employer
    ):
        """Timecard prompt with no args should show employers."""
        employer2 = Employer(name="Personal", is_current=False)
        test_session.add(employer2)
        await test_session.commit()

        prompt_response = await mcp_server.get_prompt("generate-timecard")

        content = prompt_response.messages[0].content.text
        assert employer.name in content
        assert "Personal" in content

    @pytest.mark.asyncio
    async def test_generate_timecard_prompt_with_employer(
        self, mcp_server, test_session: AsyncSession, employer: Employer
    ):
        """Timecard prompt with employer should show date guidance."""
        prompt_response = await mcp_server.get_prompt(
            "generate-timecard", arguments={"employer_name": employer.name}
        )

        content = prompt_response.messages[0].content.text
        assert employer.name in content
        assert "date" in content.lower() or "range" in content.lower()

    @pytest.mark.asyncio
    async def test_generate_timecard_prompt_with_all_args(
        self, mcp_server, test_session: AsyncSession, employer: Employer
    ):
        """Timecard prompt with all args should show preview."""
        prompt_response = await mcp_server.get_prompt(
            "generate-timecard",
            arguments={
                "employer_name": employer.name,
                "start_date": "2024-01-15",
                "end_date": "2024-01-19",
            },
        )

        content = prompt_response.messages[0].content.text
        assert employer.name in content
        assert "2024-01-15" in content or "Jan" in content

    @pytest.mark.asyncio
    async def test_generate_timecard_prompt_invalid_args_raises_error(
        self, mcp_server, test_session: AsyncSession
    ):
        """Timecard prompt with invalid args should raise error."""
        with pytest.raises(Exception):  # Validation error
            await mcp_server.get_prompt(
                "generate-timecard",
                arguments={
                    "start_date": "2024-01-19",
                    "end_date": "2024-01-15",  # end before start
                },
            )


class TestWeeklyReviewPrompt:
    """Test weekly-review prompt execution (args: week optional)."""

    @pytest.mark.asyncio
    async def test_weekly_review_prompt_current_week(self, mcp_server, test_session: AsyncSession):
        """Weekly review for current week should summarize."""
        prompt_response = await mcp_server.get_prompt("weekly-review")

        content = prompt_response.messages[0].content.text
        assert "week" in content.lower()
        assert "review" in content.lower()

    @pytest.mark.asyncio
    async def test_weekly_review_prompt_specific_week(self, mcp_server, test_session: AsyncSession):
        """Weekly review for specific week should show date range."""
        prompt_response = await mcp_server.get_prompt(
            "weekly-review", arguments={"week_start": "2024-01-15"}
        )

        content = prompt_response.messages[0].content.text
        assert "2024-01-15" in content or "Jan" in content

    @pytest.mark.asyncio
    async def test_weekly_review_prompt_with_work_sessions(
        self,
        mcp_server,
        test_session: AsyncSession,
        project: Project,
    ):
        """Weekly review should include work session metrics."""
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

        prompt_response = await mcp_server.get_prompt("weekly-review")

        content = prompt_response.messages[0].content.text
        assert "hours" in content.lower() or "8" in content


class TestFindGapsPrompt:
    """Test find-gaps prompt execution (args: date_range optional)."""

    @pytest.mark.asyncio
    async def test_find_gaps_prompt_current_week(self, mcp_server, test_session: AsyncSession):
        """Find gaps for current week should analyze coverage."""
        prompt_response = await mcp_server.get_prompt("find-gaps")

        content = prompt_response.messages[0].content.text
        assert "gap" in content.lower()
        assert "missing" in content.lower() or "unlogged" in content.lower()

    @pytest.mark.asyncio
    async def test_find_gaps_prompt_with_date_range(self, mcp_server, test_session: AsyncSession):
        """Find gaps with date range should show specific period."""
        prompt_response = await mcp_server.get_prompt(
            "find-gaps",
            arguments={"start_date": "2024-01-15", "end_date": "2024-01-19"},
        )

        content = prompt_response.messages[0].content.text
        assert "2024-01-15" in content or "Jan" in content
        assert "gap" in content.lower()

    @pytest.mark.asyncio
    async def test_find_gaps_prompt_partial_range_raises_error(
        self, mcp_server, test_session: AsyncSession
    ):
        """Find gaps with partial range should raise error."""
        with pytest.raises(Exception):  # Validation error
            await mcp_server.get_prompt("find-gaps", arguments={"start_date": "2024-01-15"})


class TestSearchContextPrompt:
    """Test search-context prompt execution (args: query REQUIRED)."""

    @pytest.mark.asyncio
    async def test_search_context_prompt_with_query(self, mcp_server, test_session: AsyncSession):
        """Search context with query should provide guidance."""
        prompt_response = await mcp_server.get_prompt(
            "search-context", arguments={"query": "Sarah discussions about auth"}
        )

        content = prompt_response.messages[0].content.text
        assert "Sarah discussions about auth" in content
        assert "search" in content.lower()

    @pytest.mark.asyncio
    async def test_search_context_prompt_without_query_raises_error(
        self, mcp_server, test_session: AsyncSession
    ):
        """Search context without query should raise error."""
        with pytest.raises(Exception):  # Validation error (required field)
            await mcp_server.get_prompt("search-context")

    @pytest.mark.asyncio
    async def test_search_context_prompt_suggests_filters(
        self, mcp_server, test_session: AsyncSession
    ):
        """Search context should suggest relevant filters."""
        prompt_response = await mcp_server.get_prompt(
            "search-context", arguments={"query": "project meetings"}
        )

        content = prompt_response.messages[0].content.text
        assert "filter" in content.lower() or "refine" in content.lower()


class TestReminderReviewPrompt:
    """Test reminder-review prompt execution (zero args, shows pending reminders)."""

    @pytest.mark.asyncio
    async def test_reminder_review_prompt_lists_pending(
        self, mcp_server, test_session: AsyncSession
    ):
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

        prompt_response = await mcp_server.get_prompt("reminder-review")

        content = prompt_response.messages[0].content.text
        assert "Follow up with Sarah" in content
        assert "Review spec" in content

    @pytest.mark.asyncio
    async def test_reminder_review_prompt_excludes_completed(
        self, mcp_server, test_session: AsyncSession
    ):
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

        prompt_response = await mcp_server.get_prompt("reminder-review")

        content = prompt_response.messages[0].content.text
        assert "Pending task" in content
        assert "Completed task" not in content

    @pytest.mark.asyncio
    async def test_reminder_review_prompt_with_no_reminders(
        self, mcp_server, test_session: AsyncSession
    ):
        """Reminder review with no reminders should indicate empty state."""
        prompt_response = await mcp_server.get_prompt("reminder-review")

        content = prompt_response.messages[0].content.text
        assert "no pending" in content.lower() or "no reminders" in content.lower()

    @pytest.mark.asyncio
    async def test_reminder_review_prompt_sorts_by_time(
        self, mcp_server, test_session: AsyncSession
    ):
        """Reminder review should sort by due time."""
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

        prompt_response = await mcp_server.get_prompt("reminder-review")

        content = prompt_response.messages[0].content.text
        sooner_pos = content.index("Sooner reminder")
        later_pos = content.index("Later reminder")
        assert sooner_pos < later_pos


class TestPromptMetadata:
    """Test prompt metadata and descriptions."""

    @pytest.mark.asyncio
    async def test_prompts_have_names(self, mcp_server):
        """All prompts should have names."""
        prompts = await mcp_server.list_prompts()

        for prompt in prompts:
            assert hasattr(prompt, "name")
            assert isinstance(prompt.name, str)
            assert len(prompt.name) > 0

    @pytest.mark.asyncio
    async def test_prompts_have_descriptions(self, mcp_server):
        """All prompts should have descriptions."""
        prompts = await mcp_server.list_prompts()

        for prompt in prompts:
            assert hasattr(prompt, "description")
            assert isinstance(prompt.description, str)
            assert len(prompt.description) > 10  # Meaningful description

    @pytest.mark.asyncio
    async def test_prompts_have_argument_schemas(self, mcp_server):
        """Prompts with arguments should have schemas."""
        prompts = await mcp_server.list_prompts()

        # Prompts that accept arguments
        prompts_with_args = [
            "generate-timecard",
            "weekly-review",
            "find-gaps",
            "search-context",
        ]

        for prompt in prompts:
            if prompt.name in prompts_with_args:
                assert hasattr(prompt, "arguments")
                assert isinstance(prompt.arguments, list) or isinstance(prompt.arguments, dict)


class TestPromptPerformance:
    """Test prompt generation performance."""

    @pytest.mark.asyncio
    async def test_prompt_generation_is_fast(self, mcp_server, test_session: AsyncSession):
        """Prompt generation should be reasonably fast."""
        import time

        start = time.time()
        await mcp_server.get_prompt("log-work")
        elapsed = time.time() - start

        # Database-driven but should still be fast
        assert elapsed < 1.0, f"Prompt generation took {elapsed}s (expected < 1s)"

    @pytest.mark.asyncio
    async def test_all_prompts_load_quickly(self, mcp_server, test_session: AsyncSession):
        """All prompts should load reasonably quickly."""
        import time

        prompts = await mcp_server.list_prompts()

        for prompt in prompts:
            start = time.time()
            try:
                # Some prompts require args
                if prompt.name == "search-context":
                    await mcp_server.get_prompt(prompt.name, arguments={"query": "test"})
                elif prompt.name == "find-gaps":
                    await mcp_server.get_prompt(
                        prompt.name,
                        arguments={
                            "start_date": "2024-01-15",
                            "end_date": "2024-01-19",
                        },
                    )
                else:
                    await mcp_server.get_prompt(prompt.name)
            except Exception:
                # Skip prompts that need specific args we didn't provide
                continue

            elapsed = time.time() - start
            assert elapsed < 1.0, f"{prompt.name} took {elapsed}s (expected < 1s)"
