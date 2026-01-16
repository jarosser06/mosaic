# Multi-Agent Development System

## Overview
Mosaic uses a multi-agent development system where specialized agents are spawned via the Task tool and leverage granular skills for specific capabilities.

## Key Concepts
- **Agents**: Spawned using Task tool (can run in parallel)
- **Skills**: Invoked by agents using Skill tool
- **Serena MCP**: Required for all codebase operations
- **Context7 MCP**: Required for all documentation lookup
- **Parallelization**: Main assistant can spawn multiple agents in parallel

## Coordination Model
Agents cannot spawn other agents. Instead:
1. Project Architect analyzes and returns detailed instructions
2. Main assistant spawns appropriate agents based on those instructions
3. Agents report results back to main assistant
4. Main assistant coordinates next phase

## Agent Roles

### Project Architect (Entry Point)
- **ALWAYS starts ALL work** - never skip this step
- Top-level coordinator
- Analyzes spec requirements
- Defines data models, APIs, schemas
- Returns detailed next-step instructions for main assistant

### Python QA
- Designs comprehensive test suites
- Targets 90%+ coverage
- Uses `pytest-testing` skill
- Creates tests BEFORE implementation (TDD)

### Application Architect
- Designs code components
- Ensures DRY principles
- Applies SOLID principles
- Uses `architecture-review` skill
- Returns implementation specifications

### Python Developer
- Implements code from specifications
- Uses `async-patterns` skill
- Uses `mcp-api-design` skill for MCP tools
- MUST use Serena MCP for all code modifications
- MUST use Context7 MCP for documentation

### Project QA
- Executes tests with `pytest-testing` skill
- Runs linters with `linting` skill
- Validates 90%+ coverage
- Determines CODE ISSUE vs TEST ISSUE

## Available Skills

1. **pytest-testing**: Run pytest with coverage and analysis
2. **linting**: Run all 4 linters (black, isort, mypy, flake8)
3. **alembic-migrate**: Generate/manage database migrations
4. **architecture-review**: Review for SOLID/DRY principles
5. **async-patterns**: Python async/await with SQLAlchemy 2.0
6. **mcp-api-design**: Design MCP tools following best practices
7. **prompt-writing**: Write effective prompts for Claude 4.x

## Workflow Example

1. **User request** → Main assistant spawns Project Architect
2. **Project Architect** → Analyzes, returns instructions
3. **Main assistant** → Spawns Python QA + App Architect (PARALLEL)
4. **Python QA + App Architect** → Design tests + architecture
5. **Main assistant** → Spawns Python Developer(s) (PARALLEL)
6. **Python Developer(s)** → Implement code
7. **Main assistant** → Spawns Project QA
8. **Project QA** → Validates (tests + linters)
9. **Main assistant** → Reports to user

## Critical Rules
- Always start with Project Architect
- Agents report to main assistant, not other agents
- Main assistant coordinates all spawning
- Agents cannot spawn other agents
- Use Serena MCP for all codebase operations
- Use Context7 MCP for all documentation lookup
