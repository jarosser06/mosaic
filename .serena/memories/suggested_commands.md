# Suggested Commands

## Development Setup
```bash
# Install dependencies
uv sync

# Create .env from template
cp .env.example .env

# Start PostgreSQL (Docker)
cd docker && docker-compose up -d postgres && cd ..

# Run migrations
uv run alembic upgrade head

# Install pre-commit hooks
uv run pre-commit install
```

## Running the Server
```bash
# Run MCP server (development)
uv run python -m src.mosaic.server

# The server connects to PostgreSQL and registers all tools, resources, prompts
```

## Testing
```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_work_session.py

# Run with verbose output
uv run pytest -v

# Run tests matching a pattern
uv run pytest -k "rounding"

# Generate HTML coverage report
uv run pytest --cov-report=html
# Open htmlcov/index.html to view

# Run only failed tests from last run
uv run pytest --lf

# Run tests in parallel (faster)
uv run pytest -n auto
```

## Linting and Formatting
```bash
# Format code with black
uv run black src/ tests/

# Sort imports with isort
uv run isort src/ tests/

# Type check with mypy (strict mode)
uv run mypy src/

# Lint with flake8
uv run flake8 src/ tests/

# Run all linters (check only)
uv run black --check src/ tests/
uv run isort --check-only src/ tests/
uv run mypy src/
uv run flake8 src/ tests/
```

## Database Migrations
```bash
# Generate migration after model changes
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history

# Check current version
uv run alembic current

# Format migration file
uv run black alembic/versions/xxx_migration.py
```

## Docker Commands
```bash
# Start PostgreSQL only
cd docker && docker-compose up -d postgres

# Start everything (PostgreSQL + MCP server)
cd docker && docker-compose up -d

# View logs
docker-compose logs -f mosaic

# Stop all services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# Access PostgreSQL CLI
docker exec -it mosaic-postgres psql -U mosaic -d mosaic
```

## macOS-Specific (Darwin System)
```bash
# Standard unix commands work on macOS
ls, cd, grep, find, git

# Package management via uv (not pip)
uv run <command>
uvx <tool>
```
