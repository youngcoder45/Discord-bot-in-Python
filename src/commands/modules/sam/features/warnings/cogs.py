import discord
from discord.ext import commands
from sqlalchemy.ext.asyncio import AsyncSession

from ...internal import database, logger_config
from .services import WarnService

logger = logger_config.logger.getChild("warnings")


DEFAULT_REASON_WHEN_MISSING = "No reason specified."


class Warnings(commands.Cog):
    def __init__(
        self, bot: commands.Bot, warn_service_class: type[WarnService] | None = None
    ):
        self.bot = bot
        self.warn_service_class = warn_service_class or WarnService
        self._db_session = None

    async def _get_db_session(self) -> AsyncSession:
        """Get a database session."""
        if not self._db_session:
            self._db_session = await database.get_session().__aenter__()
        return self._db_session

    async def _close_db_session(self) -> None:
        """Close the database session."""
        if self._db_session:
            await self._db_session.__aexit__(None, None, None)
            self._db_session = None

    async def get_service(self) -> WarnService:
        """Get an instance of the warning service with an active database session."""
        session = await self._get_db_session()
        return self.warn_service_class(session)

    @commands.hybrid_group(
        name="warnings",
        usage="warnings ((add <user> [reason]|remove <user> <case_id> [reason])|(list|clear <user>)|view <case_id>)",
        description="Manage user warnings - add, remove, list, or view warning details",
    )
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def root(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @root.command("add")
    @commands.guild_only()
    async def _add(
        self, ctx: commands.Context, user: discord.User, *, reason: str | None = None
    ):
        assert ctx.guild is not None
        if reason is None:
            reason = DEFAULT_REASON_WHEN_MISSING

        svc = await self.get_service()
        await svc.issue_warning(user.id, ctx.guild.id, ctx.author.id, reason)
        # TODO: Embed
        await ctx.send(f"Warned {user.mention} for `{reason}`")
        await self._close_db_session()

    @root.command("remove")
    @commands.guild_only()
    async def _remove(
        self,
        ctx: commands.Context,
        user: discord.User,
        case_id: int,
        *,
        reason: str | None = None,
    ):
        assert ctx.guild is not None
        if reason is None:
            reason = DEFAULT_REASON_WHEN_MISSING
        try:
            svc = await self.get_service()
            await svc.recall_warning(case_id, ctx.guild.id, ctx.author.id, reason)
            # TODO: Embed
            await ctx.send(
                f"Removed warning from {user.mention} with reason `{reason}`"
            )
        except ValueError as e:
            # TODO: Embed
            await ctx.send(f"Cannot remove this warning: {e}")
        finally:
            await self._close_db_session()

    @root.command("list")
    @commands.guild_only()
    async def _list(self, ctx: commands.Context, user: discord.User):
        assert ctx.guild is not None
        try:
            svc = await self.get_service()
            warnings = await svc.get_warnings_for_user(user.id, ctx.guild.id)
            # TODO: Embed, pagination
            await ctx.send("\n".join(map(str, warnings)))
        finally:
            await self._close_db_session()

    @root.command("clear")
    @commands.guild_only()
    async def _clear(
        self, ctx: commands.Context, user: discord.User, *, reason: str | None = None
    ):
        assert ctx.guild is not None
        try:
            svc = await self.get_service()
            await svc.clear_warnings_for_user(
                user.id,
                ctx.guild.id,
                ctx.author.id,
                reason or DEFAULT_REASON_WHEN_MISSING,
            )
            # TODO: Embed
            await ctx.send(f"Cleared warnings for {user.mention} with note `{reason}`")
        finally:
            await self._close_db_session()

    @root.command("view")
    @commands.guild_only()
    async def _view(self, ctx: commands.Context, case_id: int):
        assert ctx.guild is not None
        try:
            svc = await self.get_service()
            warning = await svc.get_warning(case_id, ctx.guild.id)
            # TODO: Embed
            await ctx.send(str(warning))
        except ValueError as e:
            # TODO: Embed
            await ctx.send(f"Cannot view this warning: {e}")
        finally:
            await self._close_db_session()


async def setup(bot: commands.Bot) -> None:
    """Set up the warnings cog."""
    await bot.add_cog(Warnings(bot))
