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

    async def get_leaderboard(self, guild_id: int, limit: int = 10) -> list[tuple[int, int]]:
        """Return the top users by active (non-revoked) warning count.

        Args:
            guild_id: The guild to build the leaderboard for.
            limit: Maximum number of entries to return.

        Returns:
            A list of ``(user_id, active_warning_count)`` tuples ordered from
            most to fewest warnings.
        """
        from sqlmodel import func, select  # type: ignore[import-not-found]
        statement = (
            select(Warn.user_id, func.count(Warn.id))
            .where(Warn.guild_id == guild_id, Warn.revoked.is_(False))
            .group_by(Warn.user_id)
            .order_by(func.count(Warn.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return [(user_id, count) for user_id, count in result.all()]
