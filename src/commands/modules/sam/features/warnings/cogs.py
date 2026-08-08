import re
from typing import Optional

import discord  # type: ignore[import-not-found]
from discord.ext import commands  # type: ignore[import-not-found]
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore[import-not-found]

from ...internal import database, logger_config
from .services import WarnService

logger = logger_config.logger.getChild("warnings")

DEFAULT_REASON = "No reason specified."


class Warnings(commands.Cog):
    def __init__(
        self, bot: commands.Bot, warn_service_class: type[WarnService] | None = None
    ):
        self.bot = bot
        self.warn_service_class = warn_service_class or WarnService

    async def _send_dm(self, user_id: int, embed: discord.Embed) -> tuple[bool, str]:
        """
        Safely send a DM to a user with proper error handling.
        Returns: (success: bool, status: str)
        """
        try:
            # Try to fetch user from cache first, then from API
            user = self.bot.get_user(user_id)
            if user is None:
                user = await self.bot.fetch_user(user_id)

            if user is None:
                return False, "User not found"

            await user.send(embed=embed)
            return True, "✅ DM sent successfully"

        except discord.Forbidden:
            return False, "⚠️ User has DMs disabled or blocked the bot"
        except discord.NotFound:
            return False, "❌ User not found"
        except Exception as e:
            logger.error(f"Failed to send DM to user {user_id}: {str(e)}")
            return False, f"⚠️ Failed to send DM: {type(e).__name__}"

    @commands.hybrid_command(name="warn", description="Issue a warning to a user.")
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def warn(
        self, ctx: commands.Context, user: discord.User, *, reason: Optional[str] = None
    ):
        """
        Issue a warning to a user.
        Slash command: /warn user:@user reason:reason
        Prefix command: ?warn @user reason
        """
        if reason is None:
            reason = DEFAULT_REASON

        try:
            async with database.get_session() as session:
                svc = self.warn_service_class(session)
                warn_obj = await svc.issue_warning(
                    user.id, ctx.guild.id, ctx.author.id, reason
                )

                # Send DM to the warned user
                dm_embed = discord.Embed(
                    title="⚠️ You Have Been Warned",
                    description=f"You have received a warning in **{ctx.guild.name}**.",
                    color=discord.Color.gold(),
                )
                dm_embed.add_field(name="Case ID", value=f"#{warn_obj.id}", inline=True)
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=True)
                dm_embed.set_footer(
                    text="Please review the rules and avoid further violations."
                )

                dm_sent, dm_status = await self._send_dm(user.id, dm_embed)

                # Send confirmation to moderator
                embed = discord.Embed(
                    title="⚠️ Warning Issued",
                    description=f"{user.mention} has been warned.",
                    color=discord.Color.gold(),
                )
                embed.add_field(name="Case ID", value=f"#{warn_obj.id}", inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                embed.add_field(name="DM Status", value=dm_status, inline=True)
                embed.set_footer(text=f"User ID: {user.id}")

                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to issue warning: {str(e)}",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="unwarn", description="Remove a warning by ID.")
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def unwarn(
        self, ctx: commands.Context, case_id: int, *, reason: Optional[str] = None
    ):
        """
        Remove a warning by ID.
        Slash command: /unwarn case_id:123 reason:reason
        Prefix command: ?unwarn 123 reason
        """
        if reason is None:
            reason = "Warning removed by moderator."

        try:
            async with database.get_session() as session:
                svc = self.warn_service_class(session)
                warn_obj = await svc.recall_warning(
                    case_id, ctx.guild.id, ctx.author.id, reason
                )

                # Send DM to the user
                dm_embed = discord.Embed(
                    title="✅ Warning Removed",
                    description=f"A warning has been removed from your record in **{ctx.guild.name}**.",
                    color=discord.Color.green(),
                )
                dm_embed.add_field(name="Case ID", value=f"#{warn_obj.id}", inline=True)
                dm_embed.add_field(name="Removal Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=True)
                dm_embed.set_footer(text="Keep up the good behavior!")

                dm_sent, dm_status = await self._send_dm(warn_obj.user_id, dm_embed)

                embed = discord.Embed(
                    title="✅ Warning Removed",
                    description=f"Warning `#{case_id}` has been removed.",
                    color=discord.Color.green(),
                )
                embed.add_field(
                    name="Affected User", value=f"<@{warn_obj.user_id}>", inline=True
                )
                embed.add_field(name="Removal Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                embed.add_field(name="DM Status", value=dm_status, inline=True)

                await ctx.send(embed=embed)
        except ValueError as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Warning `#{case_id}` not found or invalid.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to remove warning: {str(e)}",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @commands.hybrid_group(name="warnings", description="Manage warnings.")
    @commands.guild_only()
    async def warnings_group(self, ctx: commands.Context):
        """Warnings leaderboard; use the subcommands for detailed views.

        Prefix:
          ?warnings          -> server warnings leaderboard
          ?warnings view @user -> that user's warning history
        Slash:
          /warnings leaderboard -> server warnings leaderboard
          /warnings view user:@user -> that user's warning history
        """
        if ctx.invoked_subcommand is not None:
            return
        await self._display_leaderboard(ctx)

    @warnings_group.command(
        name="leaderboard", description="Show the warnings leaderboard for this server."
    )
    async def leaderboard(self, ctx: commands.Context):
        """Show the top warned users in this server."""
        await self._display_leaderboard(ctx)

    async def _display_leaderboard(self, ctx: commands.Context) -> None:
        """Render the server warnings leaderboard embed."""
        try:
            async with database.get_session() as session:
                svc = self.warn_service_class(session)
                entries = await svc.get_leaderboard(ctx.guild.id, 10)

                if not entries:
                    embed = discord.Embed(
                        title="Warnings Leaderboard",
                        description="No warnings have been issued yet in this server.",
                        color=discord.Color.gold(),
                    )
                    await ctx.send(embed=embed)
                    return

                lines = []
                for i, (user_id, count) in enumerate(entries, start=1):
                    lines.append(
                        f"**{i}.** <@{user_id}> — **{count}** warning{'s' if count != 1 else ''}"
                    )

                embed = discord.Embed(
                    title="Warnings Leaderboard",
                    description="\n".join(lines),
                    color=discord.Color.gold(),
                )
                embed.set_footer(text="Top 10 • Revoked warnings are excluded")
                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to load the warnings leaderboard: {str(e)}",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @warnings_group.command(name="view", description="View warnings for a user.")
    @commands.has_permissions(kick_members=True)
    async def view_warnings(self, ctx: commands.Context, user: discord.User):
        """View all warnings for a specific user."""
        await self._display_user_warnings(ctx, user)

    async def _display_user_warnings(
        self, ctx: commands.Context, user: discord.User
    ) -> None:
        """Render a user's warning history (total, moderator, date, reason)."""
        try:
            async with database.get_session() as session:
                svc = self.warn_service_class(session)
                warnings_list = await svc.get_warnings_for_user(user.id, ctx.guild.id)

                if not warnings_list:
                    embed = discord.Embed(
                        description=f"✅ {user.mention} has no warnings.",
                        color=discord.Color.green(),
                    )
                    await ctx.send(embed=embed)
                    return

                active_warnings = [w for w in warnings_list if not w.revoked]
                revoked_warnings = [w for w in warnings_list if w.revoked]

                embed = discord.Embed(
                    title=f"Warnings for {user.name}",
                    color=discord.Color.orange()
                    if active_warnings
                    else discord.Color.green(),
                )
                embed.add_field(
                    name="Total Warnings",
                    value=f"**{len(active_warnings)}** active • **{len(revoked_warnings)}** revoked",
                    inline=False,
                )

                if active_warnings:
                    active_content = "\n".join([str(w) for w in active_warnings])
                    if len(active_content) > 1024:
                        active_content = active_content[:1024] + "..."
                    embed.add_field(
                        name=f"Active Warnings ({len(active_warnings)})",
                        value=active_content,
                        inline=False,
                    )

                if revoked_warnings:
                    revoked_content = "\n".join([str(w) for w in revoked_warnings])
                    if len(revoked_content) > 1024:
                        revoked_content = revoked_content[:1024] + "..."
                    embed.add_field(
                        name=f"Revoked Warnings ({len(revoked_warnings)})",
                        value=revoked_content,
                        inline=False,
                    )

                embed.set_footer(
                    text=f"Total: {len(active_warnings)} active, {len(revoked_warnings)} revoked"
                )
                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to retrieve warnings: {str(e)}",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @warnings_group.command(
        name="modify", description="Modify a warning (remove/revoke it)."
    )
    @commands.has_permissions(kick_members=True)
    async def modify_warning(
        self, ctx: commands.Context, case_id: int, *, reason: Optional[str] = None
    ):
        """Modify a warning by revoking it."""
        if reason is None:
            reason = "Warning revoked by moderator."

        try:
            async with database.get_session() as session:
                svc = self.warn_service_class(session)
                warn_obj = await svc.recall_warning(
                    case_id, ctx.guild.id, ctx.author.id, reason
                )

                # Send DM to the user
                dm_embed = discord.Embed(
                    title="✅ Warning Revoked",
                    description=f"A warning has been revoked from your record in **{ctx.guild.name}**.",
                    color=discord.Color.green(),
                )
                dm_embed.add_field(name="Case ID", value=f"#{warn_obj.id}", inline=True)
                dm_embed.add_field(name="Revoke Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=True)
                dm_embed.set_footer(text="Thank you for your cooperation!")

                dm_sent, dm_status = await self._send_dm(warn_obj.user_id, dm_embed)

                embed = discord.Embed(
                    title="✅ Warning Revoked",
                    description=f"Warning `#{case_id}` has been revoked.",
                    color=discord.Color.green(),
                )
                embed.add_field(
                    name="Affected User", value=f"<@{warn_obj.user_id}>", inline=True
                )
                embed.add_field(name="Revoke Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                embed.add_field(name="DM Status", value=dm_status, inline=True)

                await ctx.send(embed=embed)
        except ValueError:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Warning `#{case_id}` not found or invalid.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to modify warning: {str(e)}",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @warnings_group.command(name="clear", description="Clear all warnings for a user.")
    @commands.has_permissions(administrator=True)
    async def clear_warnings(
        self, ctx: commands.Context, user: discord.User, *, reason: Optional[str] = None
    ):
        """Clear all warnings for a user (admin only)."""
        if reason is None:
            reason = "All warnings cleared."

        try:
            async with database.get_session() as session:
                svc = self.warn_service_class(session)
                await svc.clear_warnings_for_user(
                    user.id, ctx.guild.id, ctx.author.id, reason
                )

                # Send DM to the user
                dm_embed = discord.Embed(
                    title="🧹 All Warnings Cleared",
                    description=f"All your warnings have been cleared in **{ctx.guild.name}**.",
                    color=discord.Color.green(),
                )
                dm_embed.add_field(name="Clear Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=True)
                dm_embed.set_footer(
                    text="Your record has been reset. Keep up the good work!"
                )

                dm_sent, dm_status = await self._send_dm(user.id, dm_embed)

                embed = discord.Embed(
                    title="🧹 Warnings Cleared",
                    description=f"All warnings for {user.mention} have been cleared.",
                    color=discord.Color.green(),
                )
                embed.add_field(name="Clear Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                embed.add_field(name="DM Status", value=dm_status, inline=True)

                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to clear warnings: {str(e)}",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Set up the warnings cog."""
    await bot.add_cog(Warnings(bot))
