---
name: mcp-api-design
description: Design MCP tools and servers following best practices. Use when designing tool interfaces, implementing MCP servers, or reviewing tool designs.
allowed-tools: Read, Grep
user-invocable: true
---

# MCP API Design Skill

Design MCP tools and servers following Model Context Protocol best practices (2026).

## MCP Core Primitives

### 1. Tools (Model-Controlled)
Functions that the LLM can invoke. Tools should:
- Have clear, descriptive names
- Include comprehensive parameter schemas
- Return structured results
- Handle errors gracefully

### 2. Resources (App-Controlled)
Data that apps expose to Claude. Resources should:
- Have stable URIs
- Support efficient loading
- Provide rich metadata
- Cache when appropriate

### 3. Prompts (User-Controlled)
Templates for common interactions. Prompts should:
- Be reusable across contexts
- Support parameterization
- Have clear documentation
- Follow prompt engineering best practices

## 2026 Best Practice: Code Execution Pattern

**Problem**: Too many tools overwhelm context window.

**Solution**: Present MCP servers as code APIs instead of direct tool calls.

**Benefits:**
- Agents load only needed tools on-demand
- Process data in execution environment
- Reduce context consumption
- Scale better with complex tasks

**Implementation:**
```python
# Instead of registering 100 tools
@server.list_tools()
async def handle_list_tools():
    return [tool1, tool2, ..., tool100]  # Bad: floods context

# Present as code API
@server.tool()
async def search_tools(
    query: str,
    detail_level: Literal["name", "description", "full"] = "description"
) -> list[ToolDefinition]:
    """Search available tools by query, return only what's needed."""
    matching = find_matching_tools(query)

    if detail_level == "name":
        return [{"name": t.name} for t in matching]
    elif detail_level == "description":
        return [{"name": t.name, "description": t.desc} for t in matching]
    else:
        return [full_definition(t) for t in matching]
```

## Tool Design Best Practices

### Clear Naming
**Good:**
- `log_work_session` - Verb + noun, clear action
- `query_projects_by_date_range` - Specific, descriptive

**Bad:**
- `log` - Too vague
- `doWork` - Unclear action
- `getAllTheProjectsInTheDatabase` - Too verbose

### Rich Parameter Schemas

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class LogWorkSessionInput(BaseModel):
    """Schema for logging a work session."""

    project_id: int = Field(
        description="ID of the project this work is for"
    )
    start_time: datetime = Field(
        description="When the work session started (ISO 8601)"
    )
    end_time: datetime = Field(
        description="When the work session ended (ISO 8601)"
    )
    summary: Optional[str] = Field(
        None,
        description="Brief summary of work performed",
        max_length=500
    )
    privacy_level: str = Field(
        "private",
        description="Privacy level: public, internal, or private"
    )

@server.tool()
async def log_work_session(input: LogWorkSessionInput) -> dict:
    """
    Log a work session with automatic half-hour rounding.

    Duration is calculated from start_time to end_time and rounded
    to the nearest half hour following business rules.
    """
    # Implementation
    pass
```

### Structured Return Values

```python
from typing import TypedDict

class WorkSessionResult(TypedDict):
    """Result from logging a work session."""
    id: int
    project_name: str
    rounded_hours: float
    start_time: str
    end_time: str
    summary: str

@server.tool()
async def log_work_session(input: LogWorkSessionInput) -> WorkSessionResult:
    # Returns structured data, not plain strings
    return {
        "id": session.id,
        "project_name": session.project.name,
        "rounded_hours": float(session.duration_hours),
        "start_time": session.start_time.isoformat(),
        "end_time": session.end_time.isoformat(),
        "summary": session.summary
    }
```

## Security Requirements

**Per MCP specification:**

Hosts MUST obtain **explicit user consent** before invoking any tool.

**Implementation checklist:**
- [ ] Build robust consent and authorization flows
- [ ] Provide clear documentation of security implications
- [ ] Implement appropriate access controls
- [ ] Protect sensitive data
- [ ] Follow security best practices
- [ ] Consider privacy implications

**Example consent flow:**
```python
@server.tool()
async def delete_all_work_sessions() -> dict:
    """
    DANGEROUS: Delete all work sessions.

    Security: Requires explicit user confirmation.
    """
    # Host should show consent dialog before calling
    # Tool description warns about dangerous action
    pass
```

## Error Handling

**Good:**
```python
from mcp.server import Server
from mcp.types import McpError

@server.tool()
async def log_work_session(input: LogWorkSessionInput) -> WorkSessionResult:
    try:
        session = await create_work_session(input)
        return format_result(session)
    except ValueError as e:
        raise McpError(
            code="INVALID_PARAMS",
            message=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        raise McpError(
            code="INTERNAL_ERROR",
            message="Failed to create work session"
        )
```

**Bad:**
```python
@server.tool()
async def log_work_session(input: dict):
    # No input validation
    # No error handling
    # No structured response
    session = await create_work_session(input)
    return str(session)  # Returns string instead of structured data
```

## Transport and Protocol

MCP uses JSON-RPC 2.0 over stdio, SSE, or HTTP.

**Key points:**
- Message flow similar to Language Server Protocol (LSP)
- JSON-RPC 2.0 for request/response
- Support for notifications (one-way messages)
- Batching support for efficiency

## Python SDK Pattern

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("mosaic")

@server.list_tools()
async def handle_list_tools():
    return [
        {
            "name": "log_work_session",
            "description": "Log a work session with half-hour rounding",
            "inputSchema": LogWorkSessionInput.schema()
        }
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "log_work_session":
        input = LogWorkSessionInput(**arguments)
        return await log_work_session(input)

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Tool Organization Patterns

### Pattern 1: Feature-Based
```
tools/
├── logging.py      # log_work_session, log_meeting
├── queries.py      # query, aggregate_hours
├── updates.py      # update_work_session, update_project
└── notifications.py  # trigger_notification
```

### Pattern 2: Entity-Based
```
tools/
├── work_sessions.py   # CRUD for work sessions
├── projects.py        # CRUD for projects
├── meetings.py        # CRUD for meetings
└── people.py          # CRUD for people
```

### Pattern 3: Hybrid (Recommended)
```
tools/
├── logging.py         # Cross-entity logging actions
├── queries.py         # Flexible query tool
├── work_sessions.py   # Work session specific ops
└── notifications.py   # Notification system
```

## Testing MCP Tools

```python
import pytest
from mcp.server import Server

@pytest.mark.asyncio
async def test_log_work_session():
    server = Server("test")

    # Test tool registration
    tools = await server.list_tools()
    assert any(t["name"] == "log_work_session" for t in tools)

    # Test tool execution
    result = await server.call_tool(
        "log_work_session",
        {
            "project_id": 1,
            "start_time": "2026-01-15T09:00:00Z",
            "end_time": "2026-01-15T10:15:00Z",
            "summary": "Implemented feature X"
        }
    )

    assert result["rounded_hours"] == 1.5  # 1:15 rounds to 1.5
```

## Checklist for New Tools

- [ ] Clear, verb-based name
- [ ] Comprehensive docstring
- [ ] Pydantic input schema with Field descriptions
- [ ] TypedDict or Pydantic output schema
- [ ] Proper error handling with McpError
- [ ] Security implications documented
- [ ] Unit tests with pytest
- [ ] Integration test with actual server

## When to Use

- Designing new MCP tools
- Reviewing tool implementations
- Refactoring tool organization
- Implementing MCP server
- Adding tool security measures

## Resources

Based on research from:
- [Model Context Protocol Specification (Nov 2025)](https://modelcontextprotocol.io/specification/2025-11-25)
- [Code Execution with MCP - Anthropic Engineering](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [MCP Developer Guide 2026 - Public APIs](https://publicapis.io/blog/mcp-model-context-protocol-guide)
- [Introducing Model Context Protocol - Anthropic](https://www.anthropic.com/news/model-context-protocol)
