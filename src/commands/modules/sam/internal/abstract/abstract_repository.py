from abc import ABC
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

T = TypeVar("T", bound=SQLModel)


class AbstractRepository[T](ABC):
    model: type
    session: AsyncSession

    def __init__(self, session: AsyncSession, model_class: type) -> None:
        super().__init__()
        self.session = session
        self.model = model_class

    async def get(self, id: int) -> T | None:
        """
        Retrieves an instance of `T` from the database by its id.

        Args:
            id: int, the id of the instance to retrieve.

        Returns:
            T | None, the retrieved instance of `T` or None if no matching instance is found.
        """
        return await self.session.get(self.model, id)

    async def save(self, model: T) -> T:
        """
        Saves an instance of `T` to the database.

        Args:
            model: T, the instance of `T` to save.

        Returns:
            T, the saved instance of `T`.
        """
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model

    async def delete(self, model: T) -> None:
        """
        Deletes an instance of `T` from the database.

        Args:
            model: T, the instance of `T` to delete.

        Returns:
            None
        """
        await self.session.delete(model)
        await self.session.commit()
