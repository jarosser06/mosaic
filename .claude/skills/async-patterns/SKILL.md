---
name: async-patterns
description: Python async/await best practices with SQLAlchemy 2.0. Use when implementing async code, database operations, or reviewing async patterns.
allowed-tools: Read, Grep
user-invocable: true
---

# Async Patterns Skill

Best practices for Python async/await with SQLAlchemy 2.0 and asyncpg.

## Core Principles

### 1. Use AsyncEngine and AsyncSession

**Good:**
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    echo=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,  # Important for async
    class_=AsyncSession
)
```

**Bad:**
```python
# Don't use sync engine with async code
engine = create_engine("postgresql://...")
```

### 2. SQLAlchemy 2.0 Query Style

**Good:**
```python
from sqlalchemy import select

async def get_user(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

**Bad:**
```python
# Don't use legacy query() style
user = session.query(User).filter(User.id == user_id).first()
```

### 3. Context Manager for Sessions

**Good:**
```python
async def create_work_session(data: dict) -> WorkSession:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            ws = WorkSession(**data)
            session.add(ws)
            await session.flush()
            return ws
```

**Bad:**
```python
# Don't forget to close sessions
session = AsyncSessionLocal()
ws = WorkSession(**data)
session.add(ws)
await session.commit()
# Missing session.close()
```

### 4. FastAPI/MCP Dependency Injection

**Good:**
```python
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# In tool implementation
async def log_work_session(session: AsyncSession = Depends(get_session)):
    # Use session
    pass
```

### 5. Avoid Concurrent Queries in Same Session

**Good:**
```python
# Use separate sessions for concurrent operations
async with AsyncSessionLocal() as session1:
    task1 = get_user(session1, 1)

async with AsyncSessionLocal() as session2:
    task2 = get_project(session2, 1)

user, project = await asyncio.gather(task1, task2)
```

**Bad:**
```python
# Don't run concurrent queries in same session
async with AsyncSessionLocal() as session:
    results = await asyncio.gather(
        get_user(session, 1),      # Shares session
        get_project(session, 1)    # Shares session - ERROR
    )
```

## Common Patterns

### Repository Base Class

```python
from typing import Generic, TypeVar, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> T | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def commit(self) -> None:
        await self.session.commit()
```

### Service with Transaction Management

```python
class WorkSessionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = WorkSessionRepository(session)

    async def create_from_meeting(
        self,
        meeting: Meeting
    ) -> WorkSession:
        async with self.session.begin():
            # Both operations in same transaction
            work_session = await self.repo.create(
                project_id=meeting.project_id,
                start_time=meeting.start_time,
                end_time=meeting.end_time
            )
            meeting.work_session_id = work_session.id
            await self.session.flush()
            return work_session
```

### Handling Relationships

```python
from sqlalchemy.orm import selectinload

async def get_project_with_sessions(
    session: AsyncSession,
    project_id: int
) -> Project | None:
    result = await session.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.work_sessions))  # Eager load
    )
    return result.scalar_one_or_none()
```

## Common Mistakes

### ❌ Forgetting await

```python
# Bad
result = session.execute(select(User))  # Missing await

# Good
result = await session.execute(select(User))
```

### ❌ Using sync methods

```python
# Bad
session.commit()  # Sync method

# Good
await session.commit()
```

### ❌ Not using context managers

```python
# Bad
session = AsyncSessionLocal()
# ... do work ...
await session.close()  # Easy to forget

# Good
async with AsyncSessionLocal() as session:
    # ... do work ...
    # Automatically closed
```

### ❌ Accessing lazy-loaded relationships

```python
# Bad - triggers synchronous lazy load
user = await get_user(session, 1)
projects = user.projects  # ERROR: lazy load in async

# Good - eager load
result = await session.execute(
    select(User)
    .where(User.id == 1)
    .options(selectinload(User.projects))
)
user = result.scalar_one()
projects = user.projects  # OK: already loaded
```

## Type Hints for Async

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine

# Async generator
async def get_sessions() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# Async function returning optional
async def get_user(session: AsyncSession, id: int) -> User | None:
    ...

# Async function returning list
async def list_projects(session: AsyncSession) -> list[Project]:
    ...
```

## Testing Async Code

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_create_user(async_session: AsyncSession):
    user = await create_user(async_session, email="test@test.com")
    assert user.email == "test@test.com"
```

## When to Use

- Implementing repository methods
- Creating service layer methods
- Writing MCP tool implementations
- Reviewing async database code
- Debugging async issues

## Resources

Based on research from:
- [Asynchronous I/O - SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Setting up FastAPI with Async SQLAlchemy 2.0](https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308)
- [Building High-Performance Async APIs](https://leapcell.io/blog/building-high-performance-async-apis-with-fastapi-sqlalchemy-2-0-and-asyncpg)
- [Async SQLAlchemy Journey: From Confusion to Clarity](https://shanechang.com/p/async-sqlalchemy-journey/)
