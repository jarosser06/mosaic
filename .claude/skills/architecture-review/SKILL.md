---
name: architecture-review
description: Review code for SOLID principles, DRY violations, design patterns, and clean architecture. Use when designing components or reviewing implementations.
allowed-tools: Read, Grep, Glob
user-invocable: true
---

# Architecture Review Skill

Review code for clean architecture, SOLID principles, DRY violations, and proper design patterns.

## SOLID Principles

### Single Responsibility Principle (SRP)
Each class should have one reason to change. A class should do one thing and do it well.

**Check for violations:**
- Classes with multiple unrelated methods
- Classes that handle both business logic and data access
- God objects that do everything

### Open-Closed Principle (OCP)
Open for extension, closed for modification. Use inheritance and composition.

**Check for violations:**
- Hard-coded conditionals that grow over time
- Missing abstract base classes
- Direct type checking instead of polymorphism

### Liskov Substitution Principle (LSP)
Child classes should be replaceable with parent classes without breaking behavior.

**Check for violations:**
- Subclasses that change expected behavior
- Overridden methods that throw unexpected exceptions
- Subclasses requiring more restrictive preconditions

### Interface Segregation Principle (ISP)
Code shouldn't implement unused behaviors. Create specific interfaces.

**Check for violations:**
- Large interfaces with many methods
- Classes implementing methods they don't use
- Fat interfaces that force unnecessary dependencies

### Dependency Inversion Principle (DIP)
Depend on abstractions, not concretions. Use dependency injection.

**Check for violations:**
- Direct instantiation of concrete classes
- Hard-coded dependencies
- Missing abstract base classes for swappable components

## DRY Principle (Don't Repeat Yourself)

**Every piece of knowledge must have a single representation.**

**Check for violations:**
```bash
# Search for duplicate code patterns
grep -r "pattern" src/
```

**Common duplications:**
- Copy-pasted functions with minor variations
- Repeated validation logic
- Duplicate database queries
- Repeated error handling patterns

**Solutions:**
- Extract to helper functions
- Create base classes
- Use composition
- Apply factory pattern

## Design Patterns for This Project

### Repository Pattern
Abstraction over data storage. Separates domain logic from data access.

**Structure:**
```
models/ → Pure data models
repositories/ → Data access (CRUD)
services/ → Business logic
tools/ → MCP tool implementations
```

**Key points:**
- Repositories handle database operations
- Services orchestrate business logic
- Tools call services, not repositories directly
- All database access goes through repositories

### Service Layer Pattern
Orchestrates business logic and coordinates between repositories.

**Structure:**
```python
class WorkSessionService:
    def __init__(self, repo: WorkSessionRepository):
        self.repo = repo

    async def create_with_rounding(self, data: dict) -> WorkSession:
        # Business logic here
        rounded_hours = round_to_half_hour(minutes)
        return await self.repo.create({**data, "hours": rounded_hours})
```

**Key points:**
- Services contain business rules
- Services coordinate multiple repositories
- Keep services testable (inject repositories)

### Factory Pattern
Create objects without specifying exact class.

**When to use:**
- Creating different types of notifications
- Creating sessions based on configuration
- Building complex objects with many parameters

### Dependency Injection
Pass dependencies instead of creating them internally.

**Good:**
```python
def __init__(self, session: AsyncSession, repo: UserRepository):
    self.session = session
    self.repo = repo
```

**Bad:**
```python
def __init__(self):
    self.session = create_session()  # Hard-coded
    self.repo = UserRepository()     # Hard-coded
```

## Architecture Layers

### Layered Architecture
```
MCP Tools (API Layer)
    ↓
Services (Business Logic)
    ↓
Repositories (Data Access)
    ↓
Models (Data Layer)
```

**Rules:**
- Upper layers can call lower layers
- Lower layers never call upper layers
- Each layer has single responsibility
- Dependencies point downward

## Code Review Checklist

### DRY Check
- [ ] Search for duplicate code patterns
- [ ] Check for repeated business logic
- [ ] Look for copy-pasted functions
- [ ] Identify repeated validation
- [ ] Find duplicate queries

### SOLID Check
- [ ] Each class has single responsibility
- [ ] Using abstract base classes for extension
- [ ] Subclasses don't break parent behavior
- [ ] No fat interfaces with unused methods
- [ ] Dependencies are injected, not instantiated

### Pattern Check
- [ ] Repositories only handle data access
- [ ] Services contain business logic
- [ ] Tools don't directly access repositories
- [ ] Using dependency injection
- [ ] Proper layering maintained

### Python Best Practices
- [ ] Type hints on all functions
- [ ] Async/await for I/O operations
- [ ] Proper error handling with specific exceptions
- [ ] Google-style docstrings
- [ ] No circular imports

## When to Use

- Before implementing new features
- When reviewing pull requests
- After refactoring code
- When duplicate code is suspected
- Before merging to main branch

## Resources

Based on research from:
- [Python Design Patterns for Clean Architecture](https://www.glukhov.org/post/2025/11/python-design-patterns-for-clean-architecture/)
- [Managing Complexity with Architecture Patterns in Python](https://klaviyo.tech/managing-complexity-with-architecture-patterns-in-python-626b895710ca)
- [Repository Pattern - Cosmic Python](https://www.cosmicpython.com/book/chapter_02_repository.html)
- [SOLID Design Principles in Python - Real Python](https://realpython.com/solid-principles-python/)
- [Service Layer + Repository + Specification Patterns](https://craftedstack.com/blog/python/design-patterns-repository-service-layer-specification/)
