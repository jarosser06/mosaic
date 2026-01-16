# Mosaic - Claude Code Integration Guide

## Overview

Mosaic is a personal work memory and time tracking MCP server built with a **multi-agent development system** that ensures best practices, DRY code, and comprehensive testing.

## Critical Requirements

### 1. Testing Requirements ⚠️

**MANDATORY: 90%+ Unit Test Coverage**

This project enforces a strict 90% code coverage threshold. All code must be thoroughly tested.

```bash
# Run tests with coverage
uv run pytest

# Generate HTML coverage report
uv run pytest --cov-report=html
# Open htmlcov/index.html to view detailed coverage

# Coverage enforcement in pyproject.toml
[tool.pytest.ini_options]
addopts = [
    "--cov=src/mosaic",
    "--cov-report=term-missing",
    "--cov-fail-under=90",  # Build FAILS if coverage < 90%
]
```

**Coverage Strategy**:
- **Unit Tests** (60% of coverage): Individual functions, models, utilities
- **Integration Tests** (30% of coverage): Tool flows, database operations
- **Edge Cases** (10% of coverage): Timezone boundaries, error conditions

### 2. Linting Requirements ⚠️

**All Four Linters Must Pass**

This project uses four linters, all configured in `pyproject.toml` and enforced via pre-commit hooks:

```bash
# black - Code formatting
uv run black --check src/ tests/
uv run black src/ tests/  # Auto-fix

# isort - Import sorting
uv run isort --check-only src/ tests/
uv run isort src/ tests/  # Auto-fix

# mypy - Type checking (STRICT mode)
uv run mypy src/

# flake8 - Linting
uv run flake8 src/ tests/
```

**Pre-commit Hooks**: Install to run linters automatically on commit:
```bash
uv run pre-commit install
```

**Type Hints Required**: All functions must have complete type annotations. mypy runs in strict mode.

### 3. PostgreSQL 16 (Latest Stable)

Mosaic uses PostgreSQL 16 with async support via asyncpg.

```bash
# Start PostgreSQL via Docker
cd docker
docker-compose up -d postgres

# Check PostgreSQL is running
docker-compose ps

# Access PostgreSQL CLI
docker exec -it mosaic-postgres psql -U mosaic -d mosaic
```

**Connection String** (in `.env`):
```
DATABASE_URL=postgresql+asyncpg://mosaic:changeme@localhost:5433/mosaic
```

**Port**: Changed to 5433 to avoid conflicts with local PostgreSQL installations.

### 4. Dependency Management with uv/uvx

This project uses [uv](https://github.com/astral-sh/uv) for fast dependency management:

```bash
# Install dependencies
uv sync

# Run commands with uv
uv run pytest
uv run alembic upgrade head
uv run python -m src.mosaic.server

# Execute tools with uvx
uvx black src/
```

**Dependencies** are defined in `pyproject.toml` under `[project.dependencies]` and `[project.optional-dependencies]`.

## Multi-Agent Development System

Mosaic uses a **multi-agent development system** where specialized agents are spawned via the Task tool and leverage granular skills for specific capabilities.

**Key Concepts:**
- **Agents** = Spawned using Task tool (can run in parallel)
- **Skills** = Invoked by agents using Skill tool
- **Serena MCP** = Required for all codebase operations
- **Context7 MCP** = Required for all documentation lookup

**Parallelization:** Main assistant can spawn multiple agents in parallel by using multiple Task tool calls in a single message.

**Coordination Model:** Agents cannot spawn other agents. Instead:
1. Project Architect analyzes and returns detailed instructions
2. Main assistant spawns appropriate agents based on those instructions
3. Agents report results back to main assistant
4. Main assistant coordinates next phase

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│  Agents (Spawned via Task Tool)                │
│  - Project Architect                            │
│  - Application Architect                        │
│  - Python Developer(s)                          │
│  - Python QA                                    │
│  - Project QA                                   │
└───────────────┬─────────────────────────────────┘
                │ uses
                ▼
┌─────────────────────────────────────────────────┐
│  Skills (Granular Tool Capabilities)            │
│  - pytest-testing                               │
│  - linting                                      │
│  - alembic-migrate                              │
│  - architecture-review                          │
│  - async-patterns                               │
│  - mcp-api-design                               │
│  - prompt-writing                               │
└───────────────┬─────────────────────────────────┘
                │ mandate
                ▼
┌─────────────────────────────────────────────────┐
│  MCP Tools (Required for All Work)             │
│  - Serena MCP (semantic codebase interaction)  │
│  - Context7 MCP (documentation lookup)         │
└─────────────────────────────────────────────────┘
```

### Agent Coordination Flow

**CRITICAL: Project Architect is the Single Entry Point**

ALL work starts with the Project Architect agent. Never skip this step.

```
User Request
    ↓
┌───────────────────────────────────┐
│  Main Assistant                   │
│  - Spawns Project Architect       │
│  - Coordinates all agents         │
└─────────┬─────────────────────────┘
          │
          ├──→ Spawns: Project Architect
          │         │
          │         └──→ Returns: Next-step instructions
          │
          ├──→ Spawns (in parallel): Python QA + App Architect
          │         │
          │         └──→ Both return: Designs/specs
          │
          ├──→ Spawns (in parallel): Python Developer(s)
          │         │
          │         └──→ Return: Implementation complete
          │
          └──→ Spawns: Project QA
                    │
                    └──→ Returns: PASS/FAIL + analysis
```

**Key Principle:** Agents don't spawn other agents. They return instructions, and the main assistant coordinates.

### Agent Roles

**1. Project Architect** (Spawned by main assistant)
- **Single entry point for ALL work**
- Top-level coordinator
- Analyzes spec requirements
- Defines data models, APIs, schemas
- Ensures spec alignment
- **Returns:** Detailed next-step instructions for main assistant to coordinate
- **Reports to:** Main assistant

**2. Python QA** (Spawned by main assistant based on Project Architect's plan)
- Designs comprehensive test suites
- Targets 90%+ coverage
- Uses `pytest-testing` skill
- Creates tests BEFORE implementation (TDD)
- **Receives:** Detailed requirements from Project Architect via main assistant
- **Reports to:** Main assistant

**3. Application Architect** (Spawned by main assistant based on Project Architect's plan)
- Designs code components
- Ensures DRY (Don't Repeat Yourself)
- Applies SOLID principles
- Uses `architecture-review` skill
- **Returns:** Implementation specifications for Python Developers
- **Receives:** Requirements from Project Architect via main assistant
- **Reports to:** Main assistant

**4. Python Developer** (Spawned by main assistant based on App Architect's specs)
- Implements code from specifications
- Uses `async-patterns` skill
- Uses `mcp-api-design` skill for MCP tools
- MUST use Serena MCP for all code modifications
- MUST use Context7 MCP for documentation
- **Receives:** Implementation specs from App Architect via main assistant
- **Reports to:** Main assistant

**5. Project QA** (Spawned by main assistant based on Project Architect's plan)
- Executes tests with `pytest-testing` skill
- Runs linters with `linting` skill
- Validates 90%+ coverage
- Determines CODE ISSUE vs TEST ISSUE
- **Receives:** Validation instructions from Project Architect via main assistant
- **Reports to:** Main assistant

### Available Skills

Skills are granular capabilities that agents invoke:

#### 1. `pytest-testing`
Run pytest with coverage reporting and failure analysis.

**Key commands:**
- `uv run pytest` - Run all tests
- `uv run pytest --cov-report=html` - Generate coverage report
- `uv run pytest -k "pattern"` - Run specific tests

**Enforces:** 90%+ coverage threshold

#### 2. `linting`
Run all four linters: black, isort, mypy (strict), flake8.

**Key commands:**
- `uv run black src/ tests/` - Format code
- `uv run isort src/ tests/` - Sort imports
- `uv run mypy src/` - Type check (strict mode)
- `uv run flake8 src/ tests/` - Lint for quality

**All must pass** before committing.

#### 3. `alembic-migrate`
Generate and manage database migrations with Alembic.

**Key commands:**
- `uv run alembic revision --autogenerate -m "message"`
- `uv run alembic upgrade head`
- `uv run alembic downgrade -1`

**Important:** Run black on generated migrations.

#### 4. `architecture-review`
Review code for SOLID principles, DRY violations, and design patterns.

**Checks:**
- Single Responsibility Principle
- Open-Closed Principle
- Liskov Substitution Principle
- Interface Segregation Principle
- Dependency Inversion Principle
- DRY violations (duplicate code)
- Proper layering (Tools → Services → Repositories → Models)

**Based on research:**
- [Python Design Patterns for Clean Architecture](https://www.glukhov.org/post/2025/11/python-design-patterns-for-clean-architecture/)
- [Repository Pattern - Cosmic Python](https://www.cosmicpython.com/book/chapter_02_repository.html)
- [SOLID Principles - Real Python](https://realpython.com/solid-principles-python/)

#### 5. `async-patterns`
Python async/await best practices with SQLAlchemy 2.0.

**Key patterns:**
- Use `AsyncSession` and `async_sessionmaker`
- SQLAlchemy 2.0 query style with `select()`
- Context managers for session management
- Avoid concurrent queries in same session
- Proper eager loading with `selectinload()`

**Based on research:**
- [SQLAlchemy 2.0 Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Async SQLAlchemy Journey](https://shanechang.com/p/async-sqlalchemy-journey/)
- [Building High-Performance Async APIs](https://leapcell.io/blog/building-high-performance-async-apis-with-fastapi-sqlalchemy-2-0-and-asyncpg)

#### 6. `mcp-api-design`
Design MCP tools and servers following best practices.

**2026 Best Practice:** Code execution pattern - present MCP servers as code APIs instead of flooding context with all tools.

**Key principles:**
- Clear, verb-based tool names
- Rich Pydantic schemas with Field descriptions
- Structured return values
- Explicit user consent for dangerous operations
- JSON-RPC 2.0 transport

**Based on research:**
- [MCP Specification (Nov 2025)](https://modelcontextprotocol.io/specification/2025-11-25)
- [Code Execution with MCP - Anthropic](https://www.anthropic.com/engineering/code-execution-with-mcp)

#### 7. `prompt-writing`
Write effective prompts for Claude 4.x models.

**Core principles:**
- Be specific and explicit
- Provide context and motivation
- Use examples carefully (Claude pays close attention)
- Structured prompts work best (role, goals, constraints, process)
- Use thinking capabilities for complex reasoning
- Think step by step

**Based on research:**
- [Claude 4 Best Practices - Anthropic](https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)

### Mandatory MCP Tools

All agents MUST use these MCP servers:

#### Serena MCP (Semantic Codebase Interaction)

**Required for all codebase operations:**
- `mcp__serena__list_dir` - Explore project structure
- `mcp__serena__get_symbols_overview` - Understand file contents
- `mcp__serena__find_symbol` - Locate classes, functions
- `mcp__serena__find_referencing_symbols` - Find usage patterns
- `mcp__serena__search_for_pattern` - Find code patterns
- `mcp__serena__replace_symbol_body` - Implement changes
- `mcp__serena__insert_after_symbol` - Add new code

**Why mandatory:** Token-efficient semantic understanding vs reading entire files.

#### Context7 MCP (Documentation Lookup)

**Required for all documentation needs:**
```python
# Example: Looking up SQLAlchemy async patterns
mcp__context7__resolve-library-id("SQLAlchemy", query="async session patterns")
mcp__context7__query-docs(libraryId="/sqlalchemy/sqlalchemy", query="async session commit")
```

**Libraries to query:**
- SQLAlchemy 2.0 (async patterns)
- pytest, pytest-asyncio
- Pydantic 2.x
- Anthropic MCP SDK
- asyncpg, APScheduler

**Why mandatory:** Up-to-date, authoritative documentation from official sources.

### How to Use the Multi-Agent System

**ALWAYS start with Project Architect. Never skip this step.**

```bash
# In Claude Code, describe what you need:
# Example:

"Implement work session tracking with half-hour rounding as specified
in work-memory-system-spec.md. Ensure 90%+ test coverage and follow
all project standards."
```

The main assistant will then:
1. Spawn the Project Architect agent
2. Project Architect analyzes and returns next-step instructions
3. Main assistant spawns appropriate agents based on instructions
4. Agents report results back to main assistant
5. Main assistant coordinates next phase
6. Repeat until complete

**DO NOT:**
- Spawn agents directly yourself
- Skip the Project Architect analysis phase
- Try to coordinate agents manually

**DO:**
- Describe what you need and let main assistant coordinate
- Trust the multi-agent workflow
- Review outputs at each phase if desired

### Complete Workflow Example

**User Request:** "Implement work session tracking with half-hour rounding"

**Step 1: Main assistant spawns Project Architect**
Main assistant spawns the Project Architect to analyze and plan.

**Step 2: Project Architect analyzes and returns instructions**
- Uses Serena to explore existing models, repositories, services
- Analyzes spec requirements
- Defines WorkSession model, repository interface, service methods
- Makes architectural decisions
- **Returns instructions:** "Next phase: Test design + Code design (parallel)"

**Step 3: Main assistant spawns Python QA and App Architect IN PARALLEL**
Based on Project Architect's instructions, main assistant spawns both agents in one message with two Task calls.

**Step 4: Python QA designs tests**
- Uses `Skill(skill="pytest-testing")` to understand testing patterns
- Uses Serena to find existing test patterns
- Creates test_work_session.py with comprehensive tests
- **Reports to main assistant:** Test files created, 90%+ coverage expected

**Step 5: App Architect designs architecture**
- Uses `Skill(skill="architecture-review")` to check SOLID/DRY
- Uses Serena to find BaseRepository pattern
- Uses `Skill(skill="async-patterns")` for SQLAlchemy guidance
- Uses Context7 to research SQLAlchemy 2.0 async patterns
- Designs WorkSessionRepository
- **Returns implementation specs** to main assistant

**Step 6: Main assistant spawns Python Developer(s)**
Based on App Architect's specs, main assistant spawns developers (can be multiple in parallel for different components).

**Step 7: Python Developer implements**
- Uses `Skill(skill="async-patterns")` for guidance
- Uses Serena MCP tools to modify code:
  - `mcp__serena__replace_symbol_body` for implementing methods
  - `mcp__serena__insert_after_symbol` for adding new classes
- Uses Context7 MCP for SQLAlchemy documentation
- **Reports to main assistant:** Implementation complete

**Step 8: Main assistant spawns Project QA**
Based on completion of implementation, main assistant spawns Project QA for validation.

**Step 9: Project QA validates**
- Runs `Skill(skill="pytest-testing")` - executes pytest with coverage
- Runs `Skill(skill="linting")` - runs all 4 linters
- Analyzes results
- **Reports to main assistant:** PASS (92% coverage, all linters pass)

**Step 10: Main assistant reports to user**
```markdown
## Work Completed
- Implemented WorkSession model with half-hour rounding
- Created WorkSessionRepository with CRUD operations
- Implemented 15 test cases covering all edge cases

## Test Coverage
- Overall: 92.3%
- All tests passing: YES

## Linting Status
- black: PASS
- isort: PASS
- mypy: PASS
- flake8: PASS

## Files Created/Modified
- src/mosaic/models/work_session.py
- src/mosaic/repositories/work_session_repository.py
- src/mosaic/services/time_utils.py
- tests/unit/test_work_session.py
- tests/integration/test_work_session_repository.py
```

**Key Differences from Old Model:**
- Agents don't spawn other agents
- Project Architect returns instructions, doesn't delegate directly
- Main assistant coordinates all agent spawning
- Each agent reports back to main assistant, not to other agents
- Main assistant decides next phase based on agent outputs

## Database Migrations

Mosaic uses Alembic for database migrations with async support.

```bash
# Generate a migration after model changes
uv run alembic revision --autogenerate -m "Add new field to User"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history

# Check current version
uv run alembic current
```

**Important**: After generating a migration, run black on it:
```bash
uv run black alembic/versions/your_migration.py
```

## Docker Deployment

### Development Setup

```bash
cd docker

# Start PostgreSQL only
docker-compose up -d postgres

# Start everything (PostgreSQL + MCP server)
docker-compose up -d

# View logs
docker-compose logs -f mosaic

# Stop all services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v
```

### Production Build

```bash
# Build the Docker image
docker build -f docker/Dockerfile -t mosaic:latest .

# Run with docker-compose
cd docker
docker-compose up -d
```

### Health Checks

PostgreSQL has a health check configured:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U mosaic"]
  interval: 10s
  timeout: 5s
  retries: 5
```

## Development Workflow

### 1. Local Development Setup

```bash
# Clone the repository
git clone <repo-url>
cd mosaic

# Install dependencies
uv sync

# Create .env file from template
cp .env.example .env
# Edit .env with your configuration

# Start PostgreSQL
cd docker
docker-compose up -d postgres
cd ..

# Run migrations
uv run alembic upgrade head

# Install pre-commit hooks
uv run pre-commit install
```

### 2. Making Changes

```bash
# Use the multi-agent system
/project-architect "Implement new feature X"

# Or work directly
# 1. Write tests first (TDD approach)
# 2. Implement code
# 3. Run linters
# 4. Run tests
```

### 3. Before Committing

```bash
# Run all linters
uv run black src/ tests/
uv run isort src/ tests/
uv run mypy src/
uv run flake8 src/ tests/

# Run tests with coverage
uv run pytest

# Verify coverage meets 90%
# Check htmlcov/index.html for detailed report
```

### 4. Pre-commit Hooks

Pre-commit hooks will automatically run on `git commit`:
- black (formatting)
- isort (import sorting)
- flake8 (linting)
- mypy (type checking)
- trailing-whitespace, end-of-file-fixer

If any check fails, the commit is blocked. Fix issues and retry.

## Running the MCP Server

### Local Development

```bash
# Run the MCP server directly
uv run python -m src.mosaic.server

# The server will:
# - Connect to PostgreSQL on localhost:5433
# - Register 16 MCP tools
# - Wait for stdin (MCP protocol)
```

### Docker Deployment

```bash
cd docker
docker-compose up -d mosaic

# Check logs
docker-compose logs -f mosaic
```

### Connecting to Claude Code

Add to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "mosaic": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.mosaic.server"],
      "cwd": "/path/to/mosaic"
    }
  }
}
```

## Key Business Logic

### Half-Hour Time Rounding

Critical business rule from spec (src/mosaic/services/time_utils.py):

```python
# 0:01 to 0:30 minutes → 0.5 hours
# 0:31 to 1:00 minutes → 1.0 hours

# Examples:
# 15 minutes → 0.5 hours
# 31 minutes → 1.0 hours
# 2:15 → 2.5 hours
# 2:40 → 3.0 hours
```

**Testing**: Must have parametrized tests covering all boundary conditions.

### Privacy Model

- Default: PRIVATE (for safety)
- Applied to: work sessions, meetings, notes
- Filtered during: timecard generation, external summaries
- Full access: user queries (single-user system)

### Meeting-to-Work-Session Auto-Generation

When a meeting has a project association:
- Automatically create work session with meeting duration
- Inherit `on_behalf_of` from project
- Atomic transaction (both or neither)

## Project Structure

```
mosaic/
├── src/mosaic/
│   ├── server.py              # MCP server entry point
│   ├── config.py              # Pydantic settings
│   ├── models/                # SQLAlchemy models (11 entities)
│   ├── repositories/          # Data access layer
│   ├── services/              # Business logic
│   │   ├── database.py        # Async session management
│   │   ├── time_utils.py      # Half-hour rounding
│   │   ├── scheduler.py       # APScheduler
│   │   └── notifications.py   # macOS notifications
│   ├── tools/                 # MCP tool implementations (16 tools)
│   └── schemas/               # Pydantic validation
├── tests/
│   ├── conftest.py            # Pytest fixtures
│   ├── unit/                  # Model, utils, repository tests
│   └── integration/           # End-to-end tool flows
├── alembic/                   # Database migrations
├── docker/
│   ├── Dockerfile             # Multi-stage build
│   └── docker-compose.yml     # PostgreSQL + MCP server
├── .claude/
│   └── skills/                # Custom Claude Code skills
│       ├── project-architect/
│       ├── app-architect/
│       ├── python-dev/
│       ├── python-qa/
│       └── project-qa/
├── pyproject.toml             # Dependencies, linting, testing config
├── .pre-commit-config.yaml    # Pre-commit hooks
├── .env                       # Environment variables
└── CLAUDE.md                  # This file
```

## Troubleshooting

### Port 5432 Already in Use

PostgreSQL default port (5432) may be in use by local installation.

**Solution**: Mosaic uses port 5433 instead.

```bash
# In docker-compose.yml
ports:
  - "5433:5432"

# In .env
DATABASE_URL=postgresql+asyncpg://mosaic:changeme@localhost:5433/mosaic
```

### Database Already Exists Error

If PostgreSQL container exits with "directory not empty" error:

```bash
# Remove volumes and restart
cd docker
docker-compose down -v
docker-compose up -d postgres
```

### Alembic Migration Fails Black Check

After generating a migration, manually run black:

```bash
uv run alembic revision --autogenerate -m "My migration"
uv run black alembic/versions/xxx_my_migration.py
```

### Coverage Below 90%

```bash
# Generate HTML report to see missing coverage
uv run pytest --cov-report=html

# Open htmlcov/index.html
# Red lines show uncovered code

# Write additional tests for uncovered areas
```

### mypy Strict Mode Errors

All functions must have type hints. Common fixes:

```python
# Bad
def my_function(x):
    return x + 1

# Good
def my_function(x: int) -> int:
    return x + 1

# Bad
async def get_user(session, user_id):
    ...

# Good
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user(session: AsyncSession, user_id: int) -> User:
    ...
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://mosaic:changeme@localhost:5433/mosaic
POSTGRES_USER=mosaic
POSTGRES_PASSWORD=changeme
POSTGRES_DB=mosaic

# Optional: Scheduler
SCHEDULER_TIMEZONE=UTC

# Optional: Notifications
NOTIFICATION_BRIDGE_URL=http://host.docker.internal:8765
```

## Testing Commands

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_work_session.py

# Run with verbose output
uv run pytest -v

# Run tests matching a pattern
uv run pytest -k "rounding"

# Run only failed tests from last run
uv run pytest --lf

# Generate coverage report
uv run pytest --cov=src/mosaic --cov-report=term-missing --cov-report=html

# Run tests in parallel (faster)
uv run pytest -n auto
```

## Summary

**Critical Requirements**:
1. ⚠️ **90%+ test coverage** (enforced by pytest)
2. ⚠️ **All four linters must pass** (black, isort, mypy strict, flake8)
3. ⚠️ **PostgreSQL 16** (via Docker)
4. ⚠️ **uv for dependency management**

**Multi-Agent System**:
- **Agents** (spawned via Task tool): Project Architect, App Architect, Python Developer, Python QA, Project QA
- **Skills** (invoked via Skill tool): pytest-testing, linting, alembic-migrate, architecture-review, async-patterns, mcp-api-design, prompt-writing
- **Parallelization**: Multiple sub-agents can run in parallel (multiple Task calls in one message)

**Key Tools**:
- **Serena MCP**: Semantic codebase interaction (MUST USE)
- **Context7 MCP**: Documentation lookup (MUST USE)
- **Pre-commit hooks**: Automatic linting on commit
- **Docker**: PostgreSQL 16 + MCP server deployment

**Development Workflow**:
1. Spawn Project Architect agent via Task tool
2. Project Architect delegates to Python QA (tests) and App Architect (code) in parallel
3. App Architect delegates to Python Developer(s)
4. Project Architect spawns Project QA to validate
5. All tests pass with 90%+ coverage
6. All linters pass (black, isort, mypy, flake8)
7. Pre-commit hooks enforce quality on commit

For questions or issues, see the troubleshooting section above.
