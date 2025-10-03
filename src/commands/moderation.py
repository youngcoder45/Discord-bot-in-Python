import discord
from discord.ext import commands


class Moderation(commands.Cog):
    """Basic moderation commands (purge, kick, ban, unban)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------- Helpers --------
    async def _safe_reply(self, ctx: commands.Context, content: str | None = None, *, embed: discord.Embed | None = None):
        """Unified reply for hybrid commands without using ephemeral on regular ctx.send."""
        try:
            if ctx.interaction:
                if not ctx.interaction.response.is_done():
                    if embed is not None:
                        return await ctx.interaction.response.send_message(content=content or "", embed=embed, ephemeral=True)
                    return await ctx.interaction.response.send_message(content=content or "", ephemeral=True)
                else:
                    if embed is not None:
                        return await ctx.interaction.followup.send(content=content or "", embed=embed, ephemeral=True)
                    return await ctx.interaction.followup.send(content=content or "", ephemeral=True)
            if embed is not None:
                return await ctx.send(content=content or "", embed=embed)
            return await ctx.send(content=content or "")
        except Exception as e:  # Broad catch to avoid cascading errors
            print(f"[Moderation:_safe_reply] Failed to send response: {e}")

    # -------- Commands --------
    @commands.hybrid_command(name="purge", description="Delete a number of messages from the current channel.")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int):
        """Delete messages (prefix: ?purge, slash: /purge)."""
        if amount < 1 or amount > 100:
            return await self._safe_reply(ctx, "❌ Please provide a number between 1 and 100.")
        if not isinstance(ctx.channel, discord.TextChannel):
            return await self._safe_reply(ctx, "❌ This command must be used in a server text channel.")
        if ctx.interaction and not ctx.interaction.response.is_done():
            try:
                await ctx.interaction.response.defer(ephemeral=True)
            except Exception:
                pass
        try:
            deleted = await ctx.channel.purge(limit=amount + (0 if ctx.interaction else 1))
            count = len(deleted)
            await self._safe_reply(ctx, f"🧹 Deleted {count} messages.")
        except discord.Forbidden:
            await self._safe_reply(ctx, "❌ I lack permission to manage messages here.")
        except Exception as e:
            await self._safe_reply(ctx, f"❌ Failed to purge messages: {e}")

    @commands.hybrid_command(name="kick", description="Kick a member from the server.")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if ctx.guild is None:
            return await self._safe_reply(ctx, "❌ This command can only be used in a server.")
        if member == ctx.author:
            return await self._safe_reply(ctx, "❌ You cannot kick yourself!")
        if isinstance(member, discord.Member) and isinstance(ctx.author, discord.Member) and ctx.guild is not None:
            if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                return await self._safe_reply(ctx, "❌ Target has an equal or higher role.")
        try:
            await member.kick(reason=reason)
            await self._safe_reply(ctx, f"👢 Kicked {member.mention} | Reason: {reason}")
        except discord.Forbidden:
            await self._safe_reply(ctx, "❌ I don't have permission to kick that member.")
        except Exception as e:
            await self._safe_reply(ctx, f"❌ Error: {e}")

    @commands.hybrid_command(name="ban", description="Ban a member from the server.")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if ctx.guild is None:
            return await self._safe_reply(ctx, "❌ This command can only be used in a server.")
        if member == ctx.author:
            return await self._safe_reply(ctx, "❌ You cannot ban yourself!")
        if isinstance(member, discord.Member) and isinstance(ctx.author, discord.Member) and ctx.guild is not None:
            if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                return await self._safe_reply(ctx, "❌ Target has an equal or higher role.")
        try:
            await member.ban(reason=reason)
            await self._safe_reply(ctx, f"🔨 Banned {member.mention} | Reason: {reason}")
        except discord.Forbidden:
            await self._safe_reply(ctx, "❌ I don't have permission to ban that member.")
        except Exception as e:
            await self._safe_reply(ctx, f"❌ Error: {e}")

    @commands.hybrid_command(name="unban", description="Unban a previously banned user (use their ID).")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user_id: int):
        if ctx.guild is None:
            return await self._safe_reply(ctx, "❌ This command can only be used in a server.")
        try:
            user = await self.bot.fetch_user(user_id)
        except discord.NotFound:
            return await self._safe_reply(ctx, "❌ User not found.")

        try:
            # discord.py 2.x: guild.fetch_ban for a single user
            await ctx.guild.fetch_ban(user)
        except discord.NotFound:
            return await self._safe_reply(ctx, "❌ That user is not banned.")

        try:
            await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author}")
            await self._safe_reply(ctx, f"✅ Unbanned {user.mention}")
        except discord.Forbidden:
            await self._safe_reply(ctx, "❌ I don't have permission to unban that user.")
        except Exception as e:
            await self._safe_reply(ctx, f"❌ Error: {e}")

    # -------- Shared Error Handler --------
    @purge.error
    @kick.error
    @ban.error
    @unban.error
    async def _command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await self._safe_reply(ctx, "❌ You lack permission for that command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await self._safe_reply(ctx, "⚠️ I am missing required permissions.")
        elif isinstance(error, commands.BadArgument):
            await self._safe_reply(ctx, "⚠️ Invalid argument provided.")
        elif isinstance(error, commands.CommandInvokeError) and "Unknown interaction" in str(error):
            print(f"[Moderation] Interaction expired for {ctx.command}: {error}")
        else:
            await self._safe_reply(ctx, f"⚠️ An error occurred: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))