from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from .models import Warn
from .repositories import WarnRepository

from ...public import logging_api

LOG_FIELD_USER_ID_NAME = "User ID"
LOG_FIELD_USER_MENTION_NAME = "User Mention"
LOG_FIELD_MODERATOR_ID_NAME = "Moderator ID"
LOG_FIELD_MODERATOR_MENTION_NAME = "Moderator Mention"
LOG_FIELD_REASON_NAME = "Reason"


def get_log_action(
    title: str, description: str, user_id: int, moderator_id: int, reason: str
) -> logging_api.LogAction:
    return logging_api.LogAction(
        title,
        description,
        fields=[
            logging_api.LogField(LOG_FIELD_USER_ID_NAME, str(user_id), inline=True),
            logging_api.LogField(
                LOG_FIELD_USER_MENTION_NAME, f"<@{user_id}>", inline=False
            ),
            logging_api.LogField(
                LOG_FIELD_MODERATOR_ID_NAME, str(moderator_id), inline=True
            ),
            logging_api.LogField(
                LOG_FIELD_MODERATOR_MENTION_NAME, f"<@{moderator_id}>", inline=True
            ),
            logging_api.LogField(LOG_FIELD_REASON_NAME, reason, inline=False),
        ],
    )


class WarnService:
    def __init__(
        self, session: AsyncSession, repository: type[WarnRepository] = WarnRepository
    ) -> None:
        self.repo = repository(session)

    async def issue_warning(
        self, user_id: int, guild_id: int, moderator_id: int, reason: str
    ) -> Warn:
        warn = Warn(
            user_id=user_id, guild_id=guild_id, moderator_id=moderator_id, reason=reason
        )
        await logging_api.log(
            get_log_action(
                "Member Warning Issued",
                "A member has been warned.",
                user_id,
                moderator_id,
                reason,
            )
        )
        return await self.repo.save(warn)

    async def recall_warning(
        self, case_id: int, guild_id: int, moderator_id: int, reason: str
    ) -> Warn:
        warn = await self.get_warning(case_id, guild_id)
        warn.revoked = True
        warn.revoke_reason = reason
        warn.revoke_moderator_id = moderator_id
        warn.revoked_at = datetime.now(tz=timezone.utc)
        await logging_api.log(
            get_log_action(
                "Member Warning Revoked",
                "A member's warning has been revoked.",
                warn.user_id,
                moderator_id,
                reason,
            )
        )
        return await self.repo.save(warn)

    async def get_warnings_for_user(self, user_id: int, guild_id: int) -> list[Warn]:
        return await self.repo.find_by_user_id_and_guild_id(user_id, guild_id)

    async def clear_warnings_for_user(
        self, user_id: int, guild_id: int, moderator_id: int, reason: str
    ) -> list[Warn]:
        warnings = await self.repo.find_by_user_id_and_guild_id(user_id, guild_id)
        for i, warning in enumerate(warnings):
            warnings[i] = await self.recall_warning(
                warning.id, guild_id, moderator_id, reason
            )
        await logging_api.log(
            get_log_action(
                "Member Warnings Cleared",
                "A member's warnings have been cleared.",
                user_id,
                moderator_id,
                reason,
            )
        )
        return warnings

    async def get_warning(self, case_id: int, guild_id: int) -> Warn:
        warn = await self.repo.get(case_id)
        if warn is None:
            raise ValueError(f"Warning #{case_id} does not exist.")
        if guild_id != warn.guild_id:
            raise ValueError(
                f"Warning #{case_id} does not belong to the specified guild."
            )
        return warn
