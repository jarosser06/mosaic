# Task Completion Checklist

When a coding task is completed, **ALL of these must pass**:

## 1. Linting (MANDATORY)
Run all four linters - all must pass:

```bash
uv run black src/ tests/
uv run isort src/ tests/
uv run mypy src/
uv run flake8 src/ tests/
```

**Failure = Task incomplete**

## 2. Testing (MANDATORY)
Run tests with 90%+ coverage:

```bash
uv run pytest
```

**Requirements:**
- All tests pass
- Coverage ≥ 90%
- No test failures or errors

**Failure = Task incomplete**

## 3. Pre-commit Hooks (Optional but Recommended)
Hooks run automatically on commit if installed:

```bash
uv run pre-commit install  # Once
git commit  # Runs hooks automatically
```

## 4. Database Migrations (If Models Changed)
If SQLAlchemy models were modified:

```bash
# Generate migration
uv run alembic revision --autogenerate -m "Description"

# Format the migration
uv run black alembic/versions/xxx_migration.py

# Apply migration
uv run alembic upgrade head
```

## 5. Documentation (If Public API Changed)
Update relevant docs if:
- New MCP tools added
- New resources/prompts added
- Public API changed
- Configuration changed

## Multi-Agent Validation
When using the multi-agent system:
1. Project QA agent runs `pytest-testing` skill
2. Project QA agent runs `linting` skill
3. Project QA reports PASS or FAIL
4. If FAIL: Fix issues and re-validate

## Summary
✅ All linters pass (black, isort, mypy, flake8)
✅ All tests pass with ≥90% coverage
✅ Database migrations applied (if needed)
✅ Documentation updated (if needed)
✅ Pre-commit hooks pass (if installed)
