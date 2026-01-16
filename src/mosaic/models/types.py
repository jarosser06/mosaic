"""Custom SQLAlchemy types for cross-database compatibility."""

import json
from typing import Any

from sqlalchemy import String, Text, TypeDecorator
from sqlalchemy.dialects import postgresql


class StringArray(TypeDecorator):
    """
    Cross-database compatible string array type.

    Uses PostgreSQL ARRAY for PostgreSQL, JSON for SQLite/other databases.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        """Load the appropriate type for the database dialect."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.ARRAY(String))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value: list[str] | None, dialect: Any) -> Any:
        """Convert Python list to database format."""
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        else:
            return json.dumps(value)

    def process_result_value(self, value: Any, dialect: Any) -> list[str] | None:
        """Convert database format to Python list."""
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        else:
            return json.loads(value) if isinstance(value, str) else value
