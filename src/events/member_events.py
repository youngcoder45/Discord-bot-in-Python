import discord
from discord.ext import commands
from utils.json_store import add_or_update_user

class MemberEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle member join: track user."""
        await add_or_update_user(member.id, str(member))
        # Logging now handled by centralized logging system

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Handle member leaving the guild (logging only)."""
        # Logging now handled by centralized logging system
        pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Handle member updates (role changes, nickname changes, etc.)"""
        # Nothing to do here - role changes now handled by the centralized logging system
        # This method is kept for future compatibility
        pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Handle member ban events"""
        # Logging now handled by centralized logging system
        pass

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Handle member unban events"""
        # Logging now handled by centralized logging system
        pass

async def setup(bot):
    await bot.add_cog(MemberEvents(bot))