from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ...internal.abstract.abstract_repository import AbstractRepository
from .models import Warn


class WarnRepository(AbstractRepository[Warn]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Warn)

    async def find_by_guild_id(self, guild_id: int) -> list[Warn]:
        from sqlmodel import select
        statement = select(Warn).where(Warn.guild_id == guild_id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

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
        from sqlmodel import select
        statement = select(Warn).where(Warn.guild_id == guild_id, Warn.user_id == user_id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def find_by_staff_id_and_guild_id(
        self, staff_id: int, guild_id: int
    ) -> list[Warn]:
        """
        Finds all warnings given by a given staff ID. (moderator)

        Args:
            staff_id: The ID of the staff member to find warnings given by.

        Returns:
            A list of Warnings given by a staff ID.
        """
        from sqlmodel import select
        statement = select(Warn).where(Warn.guild_id == guild_id, Warn.moderator_id == staff_id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def find_by_guild_id_and_after(
        self, guild_id: int, date: datetime
    ) -> list[Warn]:
        """
        Finds all warnings created after a given date.

        Args:
            date: The date to find warnings after.

        Returns:
            A list of Warnings created after the given date.
        """
        from sqlmodel import select
        statement = select(Warn).where(Warn.guild_id == guild_id, Warn.created_at > date)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def find_by_guild_id_and_before(
        self, guild_id: int, date: datetime
    ) -> list[Warn]:
        """
        Finds all warnings created before a given date.

        Args:
            date: The date to find warnings before.

        Returns:
            A list of Warnings created before the given date.
        """
        return (
            (
                await self.session.execute(
                    self.model.select()
                    .where(self.model.guild_id == guild_id)
                    .where(self.model.created_at < date)
                )
            )
            .scalars()
            .all()
        )  # type: ignore

    async def find_by_guild_id_and_between(
        self, guild_id: int, start: datetime, end: datetime
    ) -> list[Warn]:
        """
        Finds all warnings created between two given dates.

        Args:
            start: The starting date to find warnings between.
            end: The ending date to find warnings between.

        Returns:
            A list of Warnings created between the given dates.
        """
        return (
            (
                await self.session.execute(
                    self.model.select()
                    .where(self.model.guild_id == guild_id)
                    .where(self.model.created_at >= start)
                    .where(self.model.created_at <= end)
                )
            )
            .scalars()
            .all()
        )  # type: ignore
