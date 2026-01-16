# Code Style and Conventions

## Python Style
- **Line length**: 100 characters (black, isort)
- **Target version**: Python 3.14
- **Import sorting**: isort with black profile
- **Type hints**: REQUIRED on all functions (mypy strict mode)
- **Async/await**: All database operations use async patterns
- **Docstrings**: Clear, concise documentation for public APIs

## Type Annotations
```python
# Required for all functions
async def get_user(session: AsyncSession, user_id: int) -> User:
    ...

# Return types must be explicit
def calculate_hours(duration: timedelta) -> float:
    ...
```

## Naming Conventions
- **Classes**: PascalCase (WorkSession, ProjectRepository)
- **Functions/methods**: snake_case (round_to_half_hour, list_projects)
- **Constants**: UPPER_SNAKE_CASE (DEFAULT_PRIVACY_LEVEL)
- **Private methods**: _leading_underscore (_load_markdown)

## Architecture Patterns
- **Repository Pattern**: Data access layer (BaseRepository)
- **Service Layer**: Business logic (time_utils, scheduler)
- **SOLID Principles**: Single responsibility, dependency inversion
- **DRY**: Don't repeat yourself - extract common patterns

## SQLAlchemy 2.0 Patterns
- Use `AsyncSession` and `async_sessionmaker`
- Modern query style with `select()`
- Context managers for session management
- Avoid concurrent queries in same session
- Eager loading with `selectinload()`

## MCP Tool Design
- Clear, verb-based tool names (log_work_session, create_reminder)
- Rich Pydantic schemas with Field descriptions
- Structured return values
- Explicit user consent for dangerous operations
- JSON-RPC 2.0 transport via FastMCP

## Testing Conventions
- **TDD**: Write tests BEFORE implementation
- **Coverage**: 90%+ required
- **Structure**: unit/ and integration/ directories
- **Fixtures**: Reusable in conftest.py
- **Naming**: test_*.py files, test_* functions
