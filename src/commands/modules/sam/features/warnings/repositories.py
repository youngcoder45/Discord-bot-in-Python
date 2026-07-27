from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore[import-not-found]

from ...internal.abstract.abstract_repository import AbstractRepository
from .models import Warn


class WarnRepository(AbstractRepository[Warn]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Warn)

    async def find_by_user_id_and_guild_id(
        self, user_id: int, guild_id: int
    ) -> list[Warn]:
        """
        Finds all warnings associated with a given user ID. (victim)

        Args:
            user_id: The ID of the user to find warnings for.

        Returns:
            A list of Warnings given to a user ID.
        """
        from sqlmodel import select  # type: ignore[import-not-found]
        statement = select(Warn).where(Warn.guild_id == guild_id, Warn.user_id == user_id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())
