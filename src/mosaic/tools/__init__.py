"""MCP tools for Mosaic server."""

# Import all tool modules to trigger @mcp.tool() decorators
from . import logging_tools, notification_tools, query_tools, update_tools

__all__ = [
    "logging_tools",
    "query_tools",
    "update_tools",
    "notification_tools",
]
