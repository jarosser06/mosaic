"""Integration tests for MCP resource access.

Tests end-to-end resource retrieval through real MCP server,
including URI resolution and content delivery.
"""

import pytest


class TestResourceRegistration:
    """Test that all resources are registered with MCP server."""

    @pytest.mark.asyncio
    async def test_mcp_server_has_resources(self, mcp_server):
        """MCP server should have resources registered."""
        # FastMCP should have resources attribute
        assert hasattr(mcp_server, "list_resources")

    @pytest.mark.asyncio
    async def test_list_all_resources(self, mcp_server):
        """Should be able to list all available resources."""
        resources = await mcp_server.list_resources()

        assert isinstance(resources, list)
        assert len(resources) >= 5  # At least 5 resources defined

    @pytest.mark.asyncio
    async def test_all_required_resources_registered(self, mcp_server):
        """All 5 required resources should be registered."""
        resources = await mcp_server.list_resources()
        resource_uris = [r.uri for r in resources]

        required_resources = [
            "mosaic://docs/schema",
            "mosaic://docs/time-tracking-rules",
            "mosaic://docs/privacy-rules",
            "mosaic://docs/query-patterns",
            "mosaic://docs/workflow-patterns",
        ]

        for required in required_resources:
            assert required in resource_uris, f"Required resource {required} not registered"


class TestSchemaResource:
    """Test mosaic://docs/schema resource access."""

    @pytest.mark.asyncio
    async def test_read_schema_resource(self, mcp_server):
        """Should be able to read schema resource."""
        content = await mcp_server.read_resource("mosaic://docs/schema")

        assert isinstance(content, str)
        assert len(content) > 100
        assert "#" in content  # Markdown headers

    @pytest.mark.asyncio
    async def test_schema_resource_includes_entities(self, mcp_server):
        """Schema resource should document all entities."""
        content = await mcp_server.read_resource("mosaic://docs/schema")

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
            assert entity in content

    @pytest.mark.asyncio
    async def test_schema_resource_is_static(self, mcp_server):
        """Schema resource should return same content each time."""
        content1 = await mcp_server.read_resource("mosaic://docs/schema")
        content2 = await mcp_server.read_resource("mosaic://docs/schema")

        assert content1 == content2


class TestRulesTimeTrackingResource:
    """Test mosaic://docs/time-tracking-rules resource access."""

    @pytest.mark.asyncio
    async def test_read_time_tracking_rules(self, mcp_server):
        """Should be able to read time tracking rules."""
        content = await mcp_server.read_resource("mosaic://docs/time-tracking-rules")

        assert isinstance(content, str)
        assert len(content) > 50

    @pytest.mark.asyncio
    async def test_time_tracking_rules_include_half_hour_rounding(self, mcp_server):
        """Time tracking rules must document half-hour rounding."""
        content = await mcp_server.read_resource("mosaic://docs/time-tracking-rules")

        assert "0.5" in content or "half hour" in content.lower()
        assert "rounding" in content.lower() or "round" in content.lower()

    @pytest.mark.asyncio
    async def test_time_tracking_rules_include_examples(self, mcp_server):
        """Time tracking rules should include examples."""
        content = await mcp_server.read_resource("mosaic://docs/time-tracking-rules")

        # Examples from spec
        assert "2:15" in content or "2.5" in content
        assert "2:40" in content or "3.0" in content

    @pytest.mark.asyncio
    async def test_time_tracking_rules_are_static(self, mcp_server):
        """Time tracking rules should return same content each time."""
        content1 = await mcp_server.read_resource("mosaic://docs/time-tracking-rules")
        content2 = await mcp_server.read_resource("mosaic://docs/time-tracking-rules")

        assert content1 == content2


class TestRulesPrivacyResource:
    """Test mosaic://docs/privacy-rules resource access."""

    @pytest.mark.asyncio
    async def test_read_privacy_rules(self, mcp_server):
        """Should be able to read privacy rules."""
        content = await mcp_server.read_resource("mosaic://docs/privacy-rules")

        assert isinstance(content, str)
        assert len(content) > 50

    @pytest.mark.asyncio
    async def test_privacy_rules_document_three_levels(self, mcp_server):
        """Privacy rules should document all three levels."""
        content = await mcp_server.read_resource("mosaic://docs/privacy-rules")

        assert "public" in content.lower()
        assert "internal" in content.lower()
        assert "private" in content.lower()

    @pytest.mark.asyncio
    async def test_privacy_rules_document_default_behavior(self, mcp_server):
        """Privacy rules should explain default privacy level."""
        content = await mcp_server.read_resource("mosaic://docs/privacy-rules")

        assert "default" in content.lower()
        assert "private" in content.lower()

    @pytest.mark.asyncio
    async def test_privacy_rules_are_static(self, mcp_server):
        """Privacy rules should return same content each time."""
        content1 = await mcp_server.read_resource("mosaic://docs/privacy-rules")
        content2 = await mcp_server.read_resource("mosaic://docs/privacy-rules")

        assert content1 == content2


class TestPatternsQueriesResource:
    """Test mosaic://docs/query-patterns resource access."""

    @pytest.mark.asyncio
    async def test_read_queries_patterns(self, mcp_server):
        """Should be able to read query patterns."""
        content = await mcp_server.read_resource("mosaic://docs/query-patterns")

        assert isinstance(content, str)
        assert len(content) > 100

    @pytest.mark.asyncio
    async def test_queries_patterns_include_examples(self, mcp_server):
        """Query patterns should include example queries."""
        content = await mcp_server.read_resource("mosaic://docs/query-patterns")

        assert "query" in content.lower()
        # Should have various query examples
        assert "?" in content or "example" in content.lower()

    @pytest.mark.asyncio
    async def test_queries_patterns_include_filters(self, mcp_server):
        """Query patterns should document filter types."""
        content = await mcp_server.read_resource("mosaic://docs/query-patterns")

        # Filter categories
        filter_keywords = ["time", "date", "project", "person", "privacy"]
        assert any(keyword in content.lower() for keyword in filter_keywords)

    @pytest.mark.asyncio
    async def test_queries_patterns_are_static(self, mcp_server):
        """Query patterns should return same content each time."""
        content1 = await mcp_server.read_resource("mosaic://docs/query-patterns")
        content2 = await mcp_server.read_resource("mosaic://docs/query-patterns")

        assert content1 == content2


class TestPatternsWorkflowsResource:
    """Test mosaic://docs/workflow-patterns resource access."""

    @pytest.mark.asyncio
    async def test_read_workflows_patterns(self, mcp_server):
        """Should be able to read workflow patterns."""
        content = await mcp_server.read_resource("mosaic://docs/workflow-patterns")

        assert isinstance(content, str)
        assert len(content) > 100

    @pytest.mark.asyncio
    async def test_workflows_patterns_include_common_flows(self, mcp_server):
        """Workflow patterns should document common workflows."""
        content = await mcp_server.read_resource("mosaic://docs/workflow-patterns")

        # Common workflows from spec
        workflow_keywords = ["log", "work", "meeting", "timecard", "reminder"]
        matching = [kw for kw in workflow_keywords if kw in content.lower()]
        assert len(matching) >= 3, f"Expected at least 3 workflows, found: {matching}"

    @pytest.mark.asyncio
    async def test_workflows_patterns_have_steps(self, mcp_server):
        """Workflow patterns should have step-by-step instructions."""
        content = await mcp_server.read_resource("mosaic://docs/workflow-patterns")

        # Should have numbered or bulleted steps
        step_indicators = ["1.", "2.", "-", "*"]
        assert any(indicator in content for indicator in step_indicators)

    @pytest.mark.asyncio
    async def test_workflows_patterns_are_static(self, mcp_server):
        """Workflow patterns should return same content each time."""
        content1 = await mcp_server.read_resource("mosaic://docs/workflow-patterns")
        content2 = await mcp_server.read_resource("mosaic://docs/workflow-patterns")

        assert content1 == content2


class TestResourceErrorHandling:
    """Test error handling for resource access."""

    @pytest.mark.asyncio
    async def test_read_nonexistent_resource_raises_error(self, mcp_server):
        """Reading non-existent resource should raise error."""
        with pytest.raises(Exception):  # MCP raises some exception type
            await mcp_server.read_resource("mosaic://nonexistent")

    @pytest.mark.asyncio
    async def test_read_invalid_uri_raises_error(self, mcp_server):
        """Reading invalid URI should raise error."""
        with pytest.raises(Exception):
            await mcp_server.read_resource("invalid-uri")

    @pytest.mark.asyncio
    async def test_read_empty_uri_raises_error(self, mcp_server):
        """Reading empty URI should raise error."""
        with pytest.raises(Exception):
            await mcp_server.read_resource("")


class TestResourceMetadata:
    """Test resource metadata and descriptions."""

    @pytest.mark.asyncio
    async def test_resources_have_names(self, mcp_server):
        """All resources should have names."""
        resources = await mcp_server.list_resources()

        for resource in resources:
            assert hasattr(resource, "name")
            assert isinstance(resource.name, str)
            assert len(resource.name) > 0

    @pytest.mark.asyncio
    async def test_resources_have_uris(self, mcp_server):
        """All resources should have URIs."""
        resources = await mcp_server.list_resources()

        for resource in resources:
            assert hasattr(resource, "uri")
            assert isinstance(resource.uri, str)
            assert resource.uri.startswith("mosaic://")

    @pytest.mark.asyncio
    async def test_resources_have_descriptions(self, mcp_server):
        """All resources should have descriptions for MCP client."""
        resources = await mcp_server.list_resources()

        for resource in resources:
            assert hasattr(resource, "description")
            assert isinstance(resource.description, str)
            assert len(resource.description) > 10  # Meaningful description

    @pytest.mark.asyncio
    async def test_resources_have_mime_types(self, mcp_server):
        """All resources should specify mime types."""
        resources = await mcp_server.list_resources()

        for resource in resources:
            assert hasattr(resource, "mime_type")
            # All our resources are markdown
            assert resource.mime_type == "text/markdown"


class TestResourcePerformance:
    """Test resource access performance."""

    @pytest.mark.asyncio
    async def test_resource_access_is_fast(self, mcp_server):
        """Resource access should be fast (static content)."""
        import time

        start = time.time()
        await mcp_server.read_resource("mosaic://docs/schema")
        elapsed = time.time() - start

        # Static content should be near-instant
        assert elapsed < 0.1, f"Resource access took {elapsed}s (expected < 0.1s)"

    @pytest.mark.asyncio
    async def test_multiple_resource_reads_are_fast(self, mcp_server):
        """Multiple resource reads should be fast."""
        import time

        start = time.time()
        for _ in range(10):
            await mcp_server.read_resource("mosaic://docs/schema")
        elapsed = time.time() - start

        # 10 reads should still be very fast
        assert elapsed < 0.5, f"10 resource reads took {elapsed}s (expected < 0.5s)"

    @pytest.mark.asyncio
    async def test_all_resources_load_quickly(self, mcp_server):
        """All resources should load quickly."""
        import time

        resources = await mcp_server.list_resources()

        for resource in resources:
            start = time.time()
            await mcp_server.read_resource(resource.uri)
            elapsed = time.time() - start

            assert elapsed < 0.1, f"{resource.uri} took {elapsed}s (expected < 0.1s)"
