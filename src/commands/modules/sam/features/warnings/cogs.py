import discord
from discord.ext import commands
import re
from sqlalchemy.ext.asyncio import AsyncSession

from ...internal import database, logger_config
from .services import WarnService

logger = logger_config.logger.getChild("warnings")

DEFAULT_REASON = "No reason specified."

class Warnings(commands.Cog):
    def __init__(self, bot: commands.Bot, warn_service_class: type[WarnService] | None = None):
        self.bot = bot
        self.warn_service_class = warn_service_class or WarnService

    @commands.hybrid_command(name="warn", description="Warn a user.")
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def warn(self, ctx: commands.Context, user: discord.User, *, reason: str = None):
        """
        Warns a user.
        Slash command: /warn user:@user reason:reason
        Prefix command: ?warn @user ?r reason
        """
        if reason is None:
            reason = DEFAULT_REASON
        else:
            # Handle "?r" prefix specifically requested for prefix commands
            match = re.match(r"^\s*\?r\s+(.+)$", reason, re.DOTALL | re.IGNORECASE)
            if match:
                reason = match.group(1)
        
        async with database.get_session() as session:
            svc = self.warn_service_class(session)
            await svc.issue_warning(user.id, ctx.guild.id, ctx.author.id, reason)
            
            embed = discord.Embed(
                title="Warning Issued",
                description=f":warning: **{user.mention}** has been warned.",
                color=discord.Color.gold()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.set_footer(text=f"User ID: {user.id}")
            
            await ctx.send(embed=embed)

    @commands.hybrid_group(name="warnings", description="Manage warnings.")
    async def warnings_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @warnings_group.command(name="list", description="List warnings for a user.")
    @commands.has_permissions(kick_members=True)
    async def list_warnings(self, ctx: commands.Context, user: discord.User):
        async with database.get_session() as session:
            svc = self.warn_service_class(session)
            warnings_list = await svc.get_warnings_for_user(user.id, ctx.guild.id)
            
            if not warnings_list:
                embed = discord.Embed(description=f"{user.mention} has no warnings.", color=discord.Color.green())
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(title=f"Warnings for {user.name}", color=discord.Color.orange())
            lines = []
            for w in warnings_list:
                lines.append(str(w))
            
            content = "\n".join(lines)
            if len(content) > 4000:
                content = content[:4000] + "..."
            
            embed.description = content
            await ctx.send(embed=embed)

    @warnings_group.command(name="remove", description="Remove a warning by ID.")
    @commands.has_permissions(kick_members=True)
    async def remove_warning(self, ctx: commands.Context, case_id: int, *, reason: str = None):
        if reason is None:
            reason = "Warning removed by moderator."
            
        try:
            async with database.get_session() as session:
                svc = self.warn_service_class(session)
                await svc.recall_warning(case_id, ctx.guild.id, ctx.author.id, reason)
                
                embed = discord.Embed(
                    description=f":white_check_mark: Warning `#{case_id}` removed.",
                    color=discord.Color.green()
                )
                if reason:
                   embed.add_field(name="Reason", value=reason)
                await ctx.send(embed=embed)
        except ValueError:
            await ctx.send(f":x: Warning `#{case_id}` not found or invalid.")
        except Exception as e:
             await ctx.send(f":x: Error removing warning: {e}")

    @warnings_group.command(name="clear", description="Clear all warnings for a user.")
    @commands.has_permissions(administrator=True)
    async def clear_warnings(self, ctx: commands.Context, user: discord.User, *, reason: str = None):
         if reason is None:
            reason = "Cleared all warnings."
            
         async with database.get_session() as session:
            svc = self.warn_service_class(session)
            await svc.clear_warnings_for_user(user.id, ctx.guild.id, ctx.author.id, reason)
            
            embed = discord.Embed(
                description=f":broom: Cleared all warnings for {user.mention}.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    """Set up the warnings cog."""
    await bot.add_cog(Warnings(bot))
