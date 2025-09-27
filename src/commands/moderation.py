import discord
from discord.ext import commands
from discord import app_commands

class Moderation(commands.Cog):
    """Basic moderation commands: purge, kick, ban, unban."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---- PURGE ----
    @commands.hybrid_command(
        name="purge",
        description="Delete a number of messages from the current channel."
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int):
        """Delete messages (prefix: ?purge, slash: /purge)."""
        if amount < 1:
            return await ctx.send("Please provide a number greater than 0.", ephemeral=True)

        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹 Deleted {len(deleted) - 1} messages.
-# Note:- This message will be deleted in 5 seconds.", delete_after=5)

    # ---- KICK ----
    @commands.hybrid_command(
        name="kick",
        description="Kick a member from the server."
    )
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        await member.kick(reason=reason)
        await ctx.send(f" Kicked {member.mention} | Reason: {reason}")

    # ---- BAN ----
    @commands.hybrid_command(
        name="ban",
        description="Ban a member from the server."
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        await member.ban(reason=reason)
        await ctx.send(f"🔨 Banned {member.mention} | Reason: {reason}")

    # ---- UNBAN ----
    @commands.hybrid_command(
        name="unban",
        description="Unban a user from the server."
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user: discord.User):
        await ctx.guild.unban(user)
        await ctx.send(f"✅ Unbanned {user.mention}")

    # ---- ERROR HANDLING ----
    @purge.error
    @kick.error
    @ban.error
    @unban.error
    async def mod_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don’t have permission to use this command.", ephemeral=True)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("⚠️ I don’t have the required permissions to do that.", ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("⚠️ Invalid argument. Please try again.", ephemeral=True)
        else:
            await ctx.send(f"⚠️ An error occurred: {error}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))