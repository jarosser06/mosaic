---
name: alembic-migrate
description: Generate and manage database migrations with Alembic. Use when database schema changes.
allowed-tools: Bash, Read
user-invocable: true
---

# Alembic Migration Skill

Generate and manage database migrations with Alembic.

## Usage

Generate new migration:
```bash
uv run alembic revision --autogenerate -m "Description of change"
```

Apply migrations:
```bash
uv run alembic upgrade head
```

Rollback one migration:
```bash
uv run alembic downgrade -1
```

View migration history:
```bash
uv run alembic history
```

Check current version:
```bash
uv run alembic current
```

## Important Steps

**After generating a migration:**
1. Review the generated migration file
2. Run black on it: `uv run black alembic/versions/xxx_migration.py`
3. Test the migration: `uv run alembic upgrade head`
4. Test rollback: `uv run alembic downgrade -1`

## Configuration

Alembic is configured for:
- Async SQLAlchemy engine
- PostgreSQL 16
- Auto-generates from models in src/mosaic/models/

## When to Use

- After adding/modifying SQLAlchemy models
- When adding indexes or constraints
- When renaming columns/tables
- Before deploying database changes
