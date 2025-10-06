from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Warn(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field()
    guild_id: int = Field(index=True)
    moderator_id: int = Field()
    reason: str = Field(max_length=512)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked: bool = Field(default=False)
    revoke_reason: str | None = Field(default=None, max_length=512)
    revoke_moderator_id: int | None = Field(default=None)
    revoked_at: datetime | None = Field(default=None)
    
    def __str__(self) -> str:
        if not self.revoked:
            return f"#{self.id}: `{self.reason}` issued by <@{self.moderator_id}> @ <t:{round(self.created_at.timestamp())}>"
        else:
            if self.revoked_at is None:
                revoked_timestamp = "Unknown"
            else:
                revoked_timestamp = f"<t:{round(self.revoked_at.timestamp())}>"
            return f"#{self.id}: `{self.revoke_reason}` revoked by <@{self.revoke_moderator_id}> @ " + revoked_timestamp + " [**REVOKED**]"
