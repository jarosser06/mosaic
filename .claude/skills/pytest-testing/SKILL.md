---
name: pytest-testing
description: Run pytest with coverage reporting and analysis. Use when executing tests, validating coverage, or analyzing test failures.
allowed-tools: Bash, Read
user-invocable: true
---

# Pytest Testing Skill

Execute pytest with comprehensive coverage reporting and failure analysis.

## Usage

Run tests with coverage:
```bash
uv run pytest
```

Run specific test file:
```bash
uv run pytest tests/unit/test_work_session.py
```

Run with verbose output:
```bash
uv run pytest -v --cov=src/mosaic --cov-report=term-missing
```

Generate HTML coverage report:
```bash
uv run pytest --cov-report=html
```

## Coverage Requirements

This project enforces **90%+ coverage**. Tests will fail if coverage drops below 90%.

## Commands

- `uv run pytest` - Run all tests with coverage
- `uv run pytest -v` - Verbose output
- `uv run pytest -k "pattern"` - Run tests matching pattern
- `uv run pytest --lf` - Run only last failed tests
- `uv run pytest -x` - Stop on first failure
- `uv run pytest --cov-report=html` - Generate HTML report

## Analyzing Failures

When tests fail:
1. Read the failure output carefully
2. Identify the failing assertion
3. Use Read tool to examine test file
4. Use Serena to examine implementation code
5. Determine if it's a code issue or test issue

## Coverage Analysis

When coverage is below 90%:
1. Generate HTML report: `uv run pytest --cov-report=html`
2. Open htmlcov/index.html
3. Identify uncovered lines (shown in red)
4. Determine which functions need tests
5. Report missing test scenarios
