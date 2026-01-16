"""Base repository with generic CRUD operations."""

from typing import Generic, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Generic repository providing CRUD operations for any model.

    Args:
        session: SQLAlchemy async session
        model: SQLAlchemy model class

    Example:
        async with get_session() as session:
            repo = BaseRepository(session, User)
            user = await repo.get_by_id(1)
    """

    def __init__(self, session: AsyncSession, model: Type[T]):
        """
        Initialize repository with session and model class.

        Args:
            session: SQLAlchemy async session
            model: SQLAlchemy model class
        """
        self.session = session
        self.model = model

    async def create(self, **kwargs: object) -> T:
        """
        Create a new entity.

        Args:
            **kwargs: Field values for the new entity

        Returns:
            T: Created entity

        Raises:
            ValueError: If required fields are missing
            IntegrityError: If unique constraints are violated
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, id: int) -> Optional[T]:
        """
        Get entity by ID.

        Args:
            id: Primary key value

        Returns:
            Optional[T]: Entity if found, None otherwise
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def update(self, id: int, **kwargs: object) -> Optional[T]:
        """
        Update an existing entity.

        Args:
            id: Primary key value
            **kwargs: Fields to update

        Returns:
            Optional[T]: Updated entity if found, None otherwise

        Raises:
            IntegrityError: If unique constraints are violated
        """
        instance = await self.get_by_id(id)
        if not instance:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        """
        Delete an entity by ID.

        Args:
            id: Primary key value

        Returns:
            bool: True if entity was deleted, False if not found

        Raises:
            IntegrityError: If foreign key constraints prevent deletion
        """
        instance = await self.get_by_id(id)
        if not instance:
            return False

        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def list_all(self) -> list[T]:
        """
        List all entities.

        Returns:
            list[T]: All entities of this type
        """
        result = await self.session.execute(select(self.model))
        return list(result.scalars().all())
