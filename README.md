Mosaic
======

**Personal work memory and time tracking MCP server**

Mosaic is a Model Context Protocol (MCP) server that helps you track your work, meetings, projects, and tasks with natural language. Built with PostgreSQL 16, SQLAlchemy 2.0 async, and FastMCP.

## Features

- ⏱️ **Work Session Tracking** with automatic half-hour rounding
- 📅 **Meeting Management** with attendee tracking
- 🏢 **Client & Project Organization** with status tracking
- 📝 **Notes** attached to any entity (projects, people, meetings, etc.)
- ⏰ **Reminders** with recurrence and snoozing
- 🔍 **Natural Language Queries** with date ranges, filters, and privacy controls
- 🔐 **Privacy Levels** (Public, Internal, Private) for sensitive data
- 📊 **Timecard Generation** for billing and reporting

## Prerequisites

- **Python 3.14+** (or 3.11+)
- **PostgreSQL 16** (any PostgreSQL instance - local, Docker, cloud-hosted, etc.)
- **[uv](https://github.com/astral-sh/uv)** package manager (for local development)

## Quick Start with uvx

The fastest way to run Mosaic from a git repository:

```bash
# Run directly with uvx (automatically installs and runs)
uvx --from git+https://github.com/jarosser06/mosaic mosaic

# Or from a local clone
git clone https://github.com/jarosser06/mosaic
cd mosaic
uvx --from . mosaic
```

**Before running**, ensure you have:
1. PostgreSQL 16 running and accessible
2. Created a `.env` file with your database connection (see Configuration below)
3. Run database migrations: `uvx --from . alembic upgrade head`

## Local Development Setup

### 1. Clone and Install

```bash
git clone https://github.com/jarosser06/mosaic
cd mosaic
uv sync
```

### 2. Set Up PostgreSQL

You need a PostgreSQL 16 instance. Choose one of these options:

#### Option A: Use Docker (Recommended for Development)

```bash
cd docker
docker-compose up -d postgres
cd ..
```

This starts PostgreSQL 16 on port `5433`.

#### Option B: Use Existing PostgreSQL

Connect to any PostgreSQL 16+ instance (local, RDS, Cloud SQL, etc.).

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL connection details:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://username:password@host:port/database

# Example for Docker setup
DATABASE_URL=postgresql+asyncpg://mosaic:changeme_supersecret_password@localhost:5433/mosaic

# Example for local PostgreSQL
DATABASE_URL=postgresql+asyncpg://myuser:mypass@localhost:5432/mosaic

# Example for cloud PostgreSQL (AWS RDS, etc.)
DATABASE_URL=postgresql+asyncpg://admin:secret@mydb.region.rds.amazonaws.com:5432/mosaic
```

### 4. Run Database Migrations

```bash
uv run alembic upgrade head
```

### 5. Run the Server

```bash
# Using the installed script
uv run mosaic

# Or directly
uv run python -m mosaic.server
```

The server will:
- Initialize the database
- Start the scheduler for reminders
- Register 18 MCP tools
- Wait for MCP protocol communication via stdin

## Connecting to Claude Code

Add Mosaic to your Claude Code MCP configuration:

**macOS/Linux:** `~/.config/claude/claude_desktop_config.json`

### For uvx (from git):

```json
{
  "mcpServers": {
    "mosaic": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jarosser06/mosaic",
        "mosaic"
      ],
      "env": {
        "DATABASE_URL": "postgresql+asyncpg://mosaic:changeme_supersecret_password@localhost:5433/mosaic"
      }
    }
  }
}
```

### For local development:

```json
{
  "mcpServers": {
    "mosaic": {
      "command": "uv",
      "args": ["run", "mosaic"],
      "cwd": "/absolute/path/to/mosaic"
    }
  }
}
```

Then restart Claude Code.

## Desktop Notifications Setup

Mosaic uses native desktop notifications for reminders. Setup requirements vary by platform:

### macOS 10.14+ (CRITICAL - Two Steps Required)

macOS requires **BOTH**:
1. A **signed Python executable** (Homebrew Python is NOT signed by default)
2. **Notification permissions** granted to Python in System Settings

#### Test if notifications work:

```bash
uv run python scripts/test_notifications.py
```

Common issues:
- ✅ Script says "Success" but no notification appears
- ✅ Error: "Notifications are not allowed for this application"

**This means notification permissions need to be granted!**

#### Step 1: Sign Homebrew Python

```bash
# Ad-hoc signature (sufficient for local use)
codesign -s - $(which python3)

# Or sign with your Apple Developer certificate
codesign -s "Your Name" $(which python3)
```

#### Step 2: Grant Notification Permissions

After signing, grant notification permissions:

1. Run the test script: `uv run python scripts/test_notifications.py`
2. If you see a permission prompt, click "Allow"
3. If NO prompt appears:
   - Open **System Settings** → **Notifications**
   - Find **Mosaic** in the list
   - Enable **"Allow Notifications"**
   - Set style to **"Alerts"** (not just "Banners")

**Note**: You may need to restart your terminal after signing and granting permissions.

#### Alternative: Use python.org Python

Install Python from [python.org](https://www.python.org/downloads/) instead of Homebrew. The official installer provides a properly signed Python framework.

```bash
# After installing from python.org
which python3  # Should show /Library/Frameworks/Python.framework/...
```

**Still need to grant notification permissions** (see Step 2 above).

#### Option 3: Bundle with PyInstaller

If you freeze/bundle Mosaic with PyInstaller, sign the resulting app bundle:

```bash
codesign -s - path/to/mosaic.app
```

### Linux

No signing required. Notifications work out of the box using D-Bus.

### Windows

No signing required. Uses native Windows Toast notifications.

### Verify Notifications Work

After setup, test notifications:

```bash
# Test script checks signing and sends test notification
uv run python scripts/test_notifications.py
```

You should see a notification that says "If you see this, notifications are working! 🎉"

## Available MCP Tools (20)

### Logging Tools (8)

| Tool | Description |
|------|-------------|
| `log_work_session` | Track work time with automatic half-hour rounding |
| `log_meeting` | Record meetings with attendees and optional project association |
| `add_person` | Add contacts with company, title, notes, tags |
| `add_client` | Add clients (companies or individuals) with status tracking |
| `add_project` | Create projects linked to clients and employers |
| `add_employer` | Track your employment history |
| `add_note` | Add notes to any entity or create standalone notes |
| `add_reminder` | Create one-time or recurring reminders |

### Query Tools (1)

| Tool | Description |
|------|-------------|
| `query` | Natural language queries supporting date ranges, entity filters, privacy filtering, text search, tags, status, and complex combinations |

### Update Tools (8)

| Tool | Description |
|------|-------------|
| `update_work_session` | Modify time, description, tags, privacy |
| `update_meeting` | Update title, description, attendees, project |
| `update_person` | Update contact details, company, title |
| `update_client` | Change name, status, contact person |
| `update_project` | Modify description, status, tags |
| `update_note` | Edit content, privacy, tags |
| `complete_reminder` | Mark reminder complete (creates next occurrence if recurring) |
| `snooze_reminder` | Postpone reminder to a future time |

### Notification Tools (1)

| Tool | Description |
|------|-------------|
| `trigger_notification` | Send desktop notifications (cross-platform: macOS, Windows, Linux) |

## Usage Examples

### Track Work Time

```
"Log 2.5 hours of work on the API project"
"I worked on the frontend from 9am to 11:30am yesterday"
```

Work sessions are automatically rounded to half-hour increments per the business rule.

### Record Meetings

```
"Log a meeting with John Smith about the Q1 roadmap from 2pm to 3pm"
"Add a 30-minute standup meeting with the team"
```

### Query Your Work

```
"Show me all work sessions from last week"
"What meetings did I have with Acme Corp this month?"
"Find all notes tagged 'urgent'"
"Show public work sessions for timecard generation"
```

### Manage Projects

```
"Create a project called 'Website Redesign' for Acme Corp"
"Add a note to the API project: 'Need to implement rate limiting'"
"Set the website project status to active"
```

## Development

### Project Structure

```
mosaic/
├── src/mosaic/
│   ├── server.py              # MCP server entry point
│   ├── config.py              # Pydantic settings
│   ├── models/                # SQLAlchemy models (11 entities)
│   ├── repositories/          # Data access layer
│   ├── services/              # Business logic
│   ├── tools/                 # MCP tool implementations (18 tools)
│   └── schemas/               # Pydantic validation schemas
├── tests/
│   ├── unit/                  # Model, service, repository tests
│   └── integration/           # End-to-end MCP tool tests
├── alembic/                   # Database migrations
├── docker/                    # Optional Docker setup
└── pyproject.toml             # Dependencies and config
```

### Running Tests

```bash
# Run all tests with coverage (requires 90%+)
uv run pytest

# Run specific test file
uv run pytest tests/integration/test_query_tool.py
```

**Current Coverage:** 93.13% (exceeds 90% requirement)

### Code Quality

This project enforces strict code quality standards:

```bash
# Format code
uv run black src/ tests/

# Sort imports
uv run isort src/ tests/

# Linting
uv run flake8 src/ tests/

# Install pre-commit hooks (runs all checks on commit)
uv run pre-commit install

# Run all checks manually
uv run pre-commit run --all-files
```

**All four linters must pass:**
- ✅ **black** - Code formatting
- ✅ **isort** - Import sorting
- ✅ **flake8** - Linting
- ✅⚠️**mypy** - Type checking 

### Database Migrations

```bash
# Create a new migration after model changes
uv run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history

# Check current version
uv run alembic current
```

**Important:** Run `black` on generated migrations:
```bash
uv run black alembic/versions/xxx_your_migration.py
```

## Key Business Rules

### Half-Hour Time Rounding

Work sessions are automatically rounded to half-hour increments:

| Actual Duration | Rounded Duration |
|----------------|------------------|
| 0:01 - 0:30 | 0.5 hours |
| 0:31 - 1:00 | 1.0 hours |
| 1:01 - 1:30 | 1.5 hours |
| 1:31 - 2:00 | 2.0 hours |

**Examples:**
- 15 minutes → 0.5 hours
- 31 minutes → 1.0 hours
- 2:15 → 2.5 hours
- 2:40 → 3.0 hours

### Privacy Levels

Three privacy levels control data visibility:

- **PUBLIC** - Shareable externally (e.g., for client timecards)
- **INTERNAL** - Internal use only (e.g., team reporting)
- **PRIVATE** - Sensitive data (filtered from all exports)

**Default:** PRIVATE (for safety)

Applied to: work sessions, meetings, notes

### Reminder Recurrence

Reminders support daily, weekly, and monthly recurrence:

- **Daily** - Same time each day
- **Weekly** - Same day/time each week
- **Monthly** - Same date each month

When completed, recurring reminders automatically create the next occurrence.

## Technology Stack

- **FastMCP** - MCP server framework with stdio transport
- **SQLAlchemy 2.0** - Async ORM with asyncpg driver
- **PostgreSQL 16** - Primary database
- **Pydantic 2.x** - Schema validation and settings
- **APScheduler 4.x** - Async scheduler for reminders
- **Alembic** - Database migrations
- **pytest** - Testing framework with 93%+ coverage

## Architecture Patterns

- **Repository Pattern** - Clean data access abstraction
- **Service Layer** - Business logic separation
- **Async/Await** - Full async stack with SQLAlchemy 2.0
- **Discriminated Unions** - Type-safe polymorphic query results
- **Privacy Filtering** - Consistent privacy enforcement across all queries

## Troubleshooting

### Database Connection Errors

**Error:** `DATABASE_URL environment variable is not set`

**Solution:** Ensure you have a `.env` file with `DATABASE_URL` configured, or set it as an environment variable.

### Port Already in Use

The provided `docker-compose.yml` uses port `5433` by default to avoid conflicts with local PostgreSQL installations on port `5432`.

To use a different port:
1. Edit `docker/docker-compose.yml` and change `"5433:5432"` to your desired port
2. Update `DATABASE_URL` in `.env` to match

### Migration Errors

**Error:** `Target database is not up to date`

**Solution:**
```bash
uv run alembic upgrade head
```

### Fresh Database Start

To completely reset your database:

**If using Docker:**
```bash
cd docker
docker-compose down -v  # Removes volumes
docker-compose up -d postgres
cd ..
uv run alembic upgrade head
```

**If using external PostgreSQL:**
```bash
# Drop and recreate your database using your PostgreSQL client
# Then run migrations
uv run alembic upgrade head
```

## Environment Variables

Required variables in `.env`:

```bash
# Database connection (REQUIRED)
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db

# APScheduler job store (optional, defaults to same as DATABASE_URL)
APSCHEDULER_JOB_STORE_URL=postgresql+asyncpg://user:pass@host:port/db

# Application settings (optional)
LOG_LEVEL=INFO
ENVIRONMENT=development

# Notification settings (optional, requires notification bridge)
NOTIFICATION_ENABLED=true
NOTIFICATION_SOUND=default
NOTIFICATION_BRIDGE_URL=http://host.docker.internal:8765
```

## Docker Deployment (Optional)

### Development (PostgreSQL only)

```bash
cd docker
docker-compose up -d postgres
```

### Production (Full stack)

```bash
# Build image
docker build -f docker/Dockerfile -t mosaic:latest .

# Run with docker-compose
cd docker
docker-compose up -d
```

Health checks are configured for PostgreSQL to ensure availability.

## Contributing

For detailed development guidelines and multi-agent system documentation, see [CLAUDE.md](CLAUDE.md).

### Development Standards

- ✅ **90%+ test coverage** (enforced by pytest)
- ✅ **All linters must pass** (black, isort, flake8)
- ✅ **Type hints required** (mypy strict mode)
- ✅ **Async/await patterns** (SQLAlchemy 2.0 style)

## License

MIT
