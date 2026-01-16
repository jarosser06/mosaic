"""MCP resource handlers for Mosaic documentation.

Provides read-only access to system documentation via MCP resources.
Each resource returns markdown content from the content/ directory.
"""

import logging
from pathlib import Path

from ..server import mcp

logger = logging.getLogger(__name__)

# Base path for content files
CONTENT_DIR = Path(__file__).parent / "content"


@mcp.resource("mosaic://docs/schema")
def schema_resource() -> str:
    """
    Database schema documentation resource.

    Returns complete schema documentation including all 11 entities,
    relationships, enums, and indexes.

    Returns:
        str: Markdown content describing the full database schema

    Raises:
        FileNotFoundError: If schema.md is missing
    """
    schema_path = CONTENT_DIR / "schema.md"
    try:
        return schema_path.read_text()
    except FileNotFoundError:
        logger.error(f"Schema resource file not found: {schema_path}")
        raise


@mcp.resource("mosaic://docs/time-tracking-rules")
def time_tracking_rules_resource() -> str:
    """
    Time tracking business rules resource.

    Returns documentation of half-hour rounding rules, work session
    tracking, and duration calculation specifications.

    Returns:
        str: Markdown content describing time tracking rules

    Raises:
        FileNotFoundError: If time_tracking_rules.md is missing
    """
    rules_path = CONTENT_DIR / "time_tracking_rules.md"
    try:
        return rules_path.read_text()
    except FileNotFoundError:
        logger.error(f"Time tracking rules resource file not found: {rules_path}")
        raise


@mcp.resource("mosaic://docs/privacy-rules")
def privacy_rules_resource() -> str:
    """
    Privacy model and filtering rules resource.

    Returns documentation of the three-tier privacy system (public,
    internal, private) and how it applies across entities.

    Returns:
        str: Markdown content describing privacy rules

    Raises:
        FileNotFoundError: If privacy_rules.md is missing
    """
    privacy_path = CONTENT_DIR / "privacy_rules.md"
    try:
        return privacy_path.read_text()
    except FileNotFoundError:
        logger.error(f"Privacy rules resource file not found: {privacy_path}")
        raise


@mcp.resource("mosaic://docs/query-patterns")
def query_patterns_resource() -> str:
    """
    Query examples and patterns resource.

    Returns documentation of common query patterns, natural language
    query examples, and expected outputs for various use cases.

    Returns:
        str: Markdown content with query pattern examples

    Raises:
        FileNotFoundError: If query_patterns.md is missing
    """
    patterns_path = CONTENT_DIR / "query_patterns.md"
    try:
        return patterns_path.read_text()
    except FileNotFoundError:
        logger.error(f"Query patterns resource file not found: {patterns_path}")
        raise


@mcp.resource("mosaic://docs/workflow-patterns")
def workflow_patterns_resource() -> str:
    """
    Workflow patterns and best practices resource.

    Returns documentation of common workflows like meeting-to-work-session
    auto-generation, timecard generation, and multi-tool interactions.

    Returns:
        str: Markdown content describing workflow patterns

    Raises:
        FileNotFoundError: If workflow_patterns.md is missing
    """
    workflow_path = CONTENT_DIR / "workflow_patterns.md"
    try:
        return workflow_path.read_text()
    except FileNotFoundError:
        logger.error(f"Workflow patterns resource file not found: {workflow_path}")
        raise
