# Project Structure

```
mosaic/
├── src/mosaic/                   # Main application code
│   ├── server.py                 # MCP server entry point (FastMCP)
│   ├── config.py                 # Pydantic settings with .env loading
│   ├── models/                   # SQLAlchemy models (11 entities)
│   │   ├── user.py
│   │   ├── employer.py
│   │   ├── client.py
│   │   ├── project.py
│   │   ├── person.py
│   │   ├── employment_history.py
│   │   ├── work_session.py
│   │   ├── meeting.py
│   │   ├── meeting_attendee.py
│   │   ├── note.py
│   │   └── reminder.py
│   ├── repositories/             # Data access layer (Repository pattern)
│   │   ├── base.py              # BaseRepository with common CRUD
│   │   ├── user_repository.py
│   │   ├── employer_repository.py
│   │   ├── client_repository.py
│   │   ├── project_repository.py
│   │   ├── person_repository.py
│   │   ├── employment_history_repository.py
│   │   ├── work_session_repository.py
│   │   ├── meeting_repository.py
│   │   ├── note_repository.py
│   │   └── reminder_repository.py
│   ├── services/                 # Business logic layer
│   │   ├── database.py          # Async session management
│   │   ├── time_utils.py        # Half-hour rounding logic
│   │   ├── scheduler.py         # APScheduler integration
│   │   └── notifications.py     # macOS desktop notifications
│   ├── schemas/                  # Pydantic validation schemas
│   │   └── (various schemas for tools)
│   ├── tools/                    # MCP tool implementations (19 tools)
│   │   ├── work_session.py
│   │   ├── meeting.py
│   │   ├── person.py
│   │   ├── client.py
│   │   ├── project.py
│   │   ├── note.py
│   │   ├── reminder.py
│   │   └── (others)
│   ├── resources/                # MCP resources (TO BE CREATED)
│   │   ├── resources.py
│   │   └── content/
│   │       └── (markdown files)
│   └── prompts/                  # MCP prompts (TO BE CREATED)
│       └── prompts.py
├── tests/
│   ├── conftest.py              # Pytest fixtures (async session, entities)
│   ├── unit/                    # Unit tests for models, utils, repos
│   └── integration/             # End-to-end tool flow tests
├── alembic/                     # Database migrations
│   ├── versions/                # Migration files
│   └── env.py                   # Alembic async configuration
├── docker/
│   ├── Dockerfile               # Multi-stage production build
│   └── docker-compose.yml       # PostgreSQL + MCP server
├── .claude/
│   └── skills/                  # Custom Claude Code skills
│       ├── pytest-testing/
│       ├── linting/
│       ├── alembic-migrate/
│       ├── architecture-review/
│       ├── async-patterns/
│       ├── mcp-api-design/
│       └── prompt-writing/
├── scripts/                     # Utility scripts
├── pyproject.toml               # Dependencies, linting, testing config
├── .pre-commit-config.yaml      # Pre-commit hooks configuration
├── alembic.ini                  # Alembic configuration
├── .env                         # Environment variables (not in git)
├── .env.example                 # Environment template
├── .env.test                    # Test environment config
├── README.md                    # Project documentation
├── CLAUDE.md                    # Claude Code integration guide
└── work-memory-system-spec.md   # Functional specification
```

## Key Directories

**src/mosaic/**: All application code
- `models/`: SQLAlchemy ORM models with relationships
- `repositories/`: Data access with BaseRepository pattern
- `services/`: Business logic (time rounding, scheduling)
- `tools/`: MCP tool implementations
- `schemas/`: Pydantic request/response validation
- `resources/`: Static documentation (MCP resources)
- `prompts/`: Dynamic guidance (MCP prompts)

**tests/**: All test code (90%+ coverage required)
- `unit/`: Isolated component tests
- `integration/`: End-to-end workflow tests
- `conftest.py`: Shared fixtures

**alembic/**: Database schema version control
- `versions/`: Auto-generated migration files

**docker/**: Containerization
- PostgreSQL 16 service
- MCP server deployment

**.claude/skills/**: Specialized agent capabilities
- Called via Skill tool from agents
