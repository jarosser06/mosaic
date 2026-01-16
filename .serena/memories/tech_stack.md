# Technology Stack

## Core Technologies
- **Python**: 3.14 (latest)
- **MCP SDK**: >=1.2.0 (FastMCP framework)
- **Database**: PostgreSQL 16 (via Docker)
- **ORM**: SQLAlchemy 2.0 with asyncio support
- **Database Driver**: asyncpg (async PostgreSQL)
- **Migrations**: Alembic 1.13+
- **Validation**: Pydantic 2.6+ with email support
- **Configuration**: pydantic-settings with python-dotenv
- **Scheduler**: APScheduler 4.0.0a5
- **Notifications**: desktop-notifier 5.0+

## Development Tools
- **Package Manager**: uv (fast dependency management)
- **Testing**: pytest 8.0+ with pytest-asyncio, pytest-cov
- **Formatters**: black (line-length=100), isort
- **Type Checking**: mypy (strict mode)
- **Linting**: flake8
- **Pre-commit Hooks**: Automated quality checks
- **Coverage**: 90%+ threshold enforced

## Infrastructure
- **Docker**: PostgreSQL 16 container on port 5433
- **Docker Compose**: Development environment setup
- **Connection**: postgresql+asyncpg://mosaic:changeme@localhost:5433/mosaic

## MCP Tools (Required)
- **Serena MCP**: Semantic codebase interaction (MANDATORY for all code operations)
- **Context7 MCP**: Documentation lookup (MANDATORY for library docs)
