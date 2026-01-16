"""Unit tests for MCP resource markdown content validation.

Tests that resource handlers correctly read and serve markdown documentation
from static files in the content/ directory.
"""

from src.mosaic.resources.resource_handlers import (
    CONTENT_DIR,
    privacy_rules_resource,
    query_patterns_resource,
    schema_resource,
    time_tracking_rules_resource,
    workflow_patterns_resource,
)


class TestSchemaResource:
    """Test mosaic://docs/schema resource content validation."""

    def test_schema_resource_returns_markdown(self):
        """Schema content should return valid markdown."""
        content = schema_resource()

        assert isinstance(content, str)
        assert len(content) > 100
        assert "# " in content  # Has markdown headers

    def test_schema_includes_all_entities(self):
        """Schema should document all 11 core entities."""
        content = schema_resource()

        # All core entities from spec
        required_entities = [
            "User",
            "Employer",
            "Client",
            "Person",
            "Project",
            "WorkSession",
            "Meeting",
            "Reminder",
            "Note",
        ]

        for entity in required_entities:
            assert entity in content, f"Schema missing {entity} entity"

    def test_schema_includes_privacy_levels(self):
        """Schema should document privacy levels."""
        content = schema_resource()

        assert "privacy" in content.lower()
        assert "public" in content.lower() or "private" in content.lower()

    def test_schema_includes_relationships(self):
        """Schema should document entity relationships."""
        content = schema_resource()

        # Key relationships
        assert "project" in content.lower()
        assert "employer" in content.lower() or "on_behalf_of" in content.lower()
        assert "client" in content.lower()

    def test_schema_content_is_stable(self):
        """Schema content should be deterministic."""
        content1 = schema_resource()
        content2 = schema_resource()

        assert content1 == content2

    def test_schema_markdown_file_exists(self):
        """Schema markdown file should exist in content directory."""
        schema_path = CONTENT_DIR / "schema.md"
        assert schema_path.exists()
        assert schema_path.is_file()


class TestRulesTimeTrackingResource:
    """Test mosaic://docs/time-tracking-rules resource content validation."""

    def test_time_tracking_rules_returns_markdown(self):
        """Time tracking rules should return valid markdown."""
        content = time_tracking_rules_resource()

        assert isinstance(content, str)
        assert len(content) > 50
        assert "#" in content  # Has markdown headers

    def test_time_tracking_includes_half_hour_rounding(self):
        """Time tracking rules must include half-hour rounding spec."""
        content = time_tracking_rules_resource()

        # Critical business rule
        assert "0.5" in content or "half hour" in content.lower()
        assert "rounding" in content.lower() or "round" in content.lower()

    def test_time_tracking_includes_examples(self):
        """Time tracking rules should include practical examples."""
        content = time_tracking_rules_resource()

        # Should have examples of rounding behavior
        assert "2:15" in content or "2.5" in content
        assert "example" in content.lower() or ":" in content

    def test_time_tracking_mentions_work_sessions(self):
        """Time tracking rules should reference work sessions."""
        content = time_tracking_rules_resource()

        assert "work session" in content.lower() or "worksession" in content.lower()

    def test_time_tracking_content_is_stable(self):
        """Time tracking rules should be deterministic."""
        content1 = time_tracking_rules_resource()
        content2 = time_tracking_rules_resource()

        assert content1 == content2

    def test_time_tracking_markdown_file_exists(self):
        """Time tracking rules markdown file should exist."""
        rules_path = CONTENT_DIR / "time_tracking_rules.md"
        assert rules_path.exists()
        assert rules_path.is_file()


class TestRulesPrivacyResource:
    """Test mosaic://docs/privacy-rules resource content validation."""

    def test_privacy_rules_returns_markdown(self):
        """Privacy rules should return valid markdown."""
        content = privacy_rules_resource()

        assert isinstance(content, str)
        assert len(content) > 50
        assert "#" in content

    def test_privacy_includes_three_levels(self):
        """Privacy rules should document all three privacy levels."""
        content = privacy_rules_resource()

        # All three levels from spec
        assert "public" in content.lower()
        assert "internal" in content.lower()
        assert "private" in content.lower()

    def test_privacy_includes_default_behavior(self):
        """Privacy rules should document default privacy level."""
        content = privacy_rules_resource()

        assert "default" in content.lower()
        assert "private" in content.lower()  # Default is PRIVATE

    def test_privacy_includes_filtering_rules(self):
        """Privacy rules should explain when filtering applies."""
        content = privacy_rules_resource()

        assert "timecard" in content.lower() or "external" in content.lower()
        assert "filter" in content.lower() or "exclude" in content.lower()

    def test_privacy_content_is_stable(self):
        """Privacy rules should be deterministic."""
        content1 = privacy_rules_resource()
        content2 = privacy_rules_resource()

        assert content1 == content2

    def test_privacy_markdown_file_exists(self):
        """Privacy rules markdown file should exist."""
        privacy_path = CONTENT_DIR / "privacy_rules.md"
        assert privacy_path.exists()
        assert privacy_path.is_file()


class TestPatternsQueriesResource:
    """Test mosaic://docs/query-patterns resource content validation."""

    def test_queries_patterns_returns_markdown(self):
        """Query patterns should return valid markdown."""
        content = query_patterns_resource()

        assert isinstance(content, str)
        assert len(content) > 100
        assert "#" in content

    def test_queries_includes_example_queries(self):
        """Query patterns should include example queries."""
        content = query_patterns_resource()

        # Should have various query examples
        assert "query" in content.lower()
        assert "?" in content or "example" in content.lower()

    def test_queries_includes_time_ranges(self):
        """Query patterns should include time range examples."""
        content = query_patterns_resource()

        # Time-based query patterns
        time_keywords = ["today", "week", "month", "date", "time"]
        assert any(keyword in content.lower() for keyword in time_keywords)

    def test_queries_includes_entity_filters(self):
        """Query patterns should include entity filter examples."""
        content = query_patterns_resource()

        # Entity-based filters
        entity_keywords = ["project", "person", "client", "employer"]
        assert any(keyword in content.lower() for keyword in entity_keywords)

    def test_queries_includes_aggregation_patterns(self):
        """Query patterns should include aggregation examples."""
        content = query_patterns_resource()

        # Aggregation patterns
        agg_keywords = ["sum", "total", "group", "aggregate"]
        assert any(keyword in content.lower() for keyword in agg_keywords)

    def test_queries_content_is_stable(self):
        """Query patterns should be deterministic."""
        content1 = query_patterns_resource()
        content2 = query_patterns_resource()

        assert content1 == content2

    def test_queries_markdown_file_exists(self):
        """Query patterns markdown file should exist."""
        patterns_path = CONTENT_DIR / "query_patterns.md"
        assert patterns_path.exists()
        assert patterns_path.is_file()


class TestPatternsWorkflowsResource:
    """Test mosaic://docs/workflow-patterns resource content validation."""

    def test_workflows_patterns_returns_markdown(self):
        """Workflow patterns should return valid markdown."""
        content = workflow_patterns_resource()

        assert isinstance(content, str)
        assert len(content) > 100
        assert "#" in content

    def test_workflows_includes_logging_workflow(self):
        """Workflow patterns should include work logging flow."""
        content = workflow_patterns_resource()

        assert "log" in content.lower()
        assert "work" in content.lower() or "session" in content.lower()

    def test_workflows_includes_meeting_workflow(self):
        """Workflow patterns should include meeting logging flow."""
        content = workflow_patterns_resource()

        assert "meeting" in content.lower()

    def test_workflows_includes_timecard_workflow(self):
        """Workflow patterns should include timecard generation flow."""
        content = workflow_patterns_resource()

        assert "timecard" in content.lower() or "generate" in content.lower()

    def test_workflows_includes_reminder_workflow(self):
        """Workflow patterns should include reminder management flow."""
        content = workflow_patterns_resource()

        assert "reminder" in content.lower()

    def test_workflows_includes_steps(self):
        """Workflow patterns should have step-by-step instructions."""
        content = workflow_patterns_resource()

        # Should have numbered or bulleted steps
        step_indicators = ["1.", "2.", "-", "*", "step"]
        assert any(indicator in content.lower() for indicator in step_indicators)

    def test_workflows_content_is_stable(self):
        """Workflow patterns should be deterministic."""
        content1 = workflow_patterns_resource()
        content2 = workflow_patterns_resource()

        assert content1 == content2

    def test_workflows_markdown_file_exists(self):
        """Workflow patterns markdown file should exist."""
        workflow_path = CONTENT_DIR / "workflow_patterns.md"
        assert workflow_path.exists()
        assert workflow_path.is_file()


class TestResourceErrorHandling:
    """Test error handling for resource content loading."""

    def test_all_resource_functions_exist(self):
        """All required resource functions should be defined."""
        # This test ensures all required functions exist
        assert callable(schema_resource)
        assert callable(time_tracking_rules_resource)
        assert callable(privacy_rules_resource)
        assert callable(query_patterns_resource)
        assert callable(workflow_patterns_resource)

    def test_all_resources_return_non_empty_strings(self):
        """All resource functions should return non-empty content."""
        resources = [
            schema_resource,
            time_tracking_rules_resource,
            privacy_rules_resource,
            query_patterns_resource,
            workflow_patterns_resource,
        ]

        for resource_func in resources:
            content = resource_func()
            assert isinstance(content, str)
            assert len(content) > 0
            assert len(content) > 50  # Meaningful content

    def test_all_resources_are_valid_markdown(self):
        """All resource content should be valid markdown."""
        resources = [
            schema_resource,
            time_tracking_rules_resource,
            privacy_rules_resource,
            query_patterns_resource,
            workflow_patterns_resource,
        ]

        for resource_func in resources:
            content = resource_func()
            # Basic markdown validation
            assert "#" in content or "##" in content  # Has headers
            assert len(content.split("\n")) > 3  # Multiple lines

    def test_all_markdown_files_exist(self):
        """All markdown content files should exist in content directory."""
        required_files = [
            "schema.md",
            "time_tracking_rules.md",
            "privacy_rules.md",
            "query_patterns.md",
            "workflow_patterns.md",
        ]

        for filename in required_files:
            filepath = CONTENT_DIR / filename
            assert filepath.exists(), f"Missing content file: {filename}"
            assert filepath.is_file()

    def test_content_directory_exists(self):
        """Content directory should exist and be a directory."""
        assert CONTENT_DIR.exists()
        assert CONTENT_DIR.is_dir()
        assert (CONTENT_DIR / "schema.md").parent == CONTENT_DIR
