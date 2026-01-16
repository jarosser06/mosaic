---
name: linting
description: Run all linters (black, isort, mypy, flake8) to ensure code quality. Use before committing or when validating code standards.
allowed-tools: Bash, Read
user-invocable: true
---

# Linting Skill

Run all code quality tools: black, isort, mypy (strict), and flake8.

## Usage

Run all linters:
```bash
uv run black --check src/ tests/
uv run isort --check-only src/ tests/
uv run mypy src/
uv run flake8 src/ tests/
```

Auto-fix formatting:
```bash
uv run black src/ tests/
uv run isort src/ tests/
```

## Linters

**black** - Code formatting (line length: 100, Python 3.14)
**isort** - Import sorting (black profile)
**mypy** - Type checking (strict mode - all functions need type hints)
**flake8** - Style and quality linting

## Common Fixes

**mypy errors** - Add type hints:
```python
# Bad
def get_user(session, user_id):
    ...

# Good
async def get_user(session: AsyncSession, user_id: int) -> User:
    ...
```

**flake8 F401** - Remove unused imports
**flake8 E501** - Line too long (use black to auto-fix)

## When to Use

- Before committing code
- After writing new functions
- When CI/CD checks fail
- Before requesting code review
