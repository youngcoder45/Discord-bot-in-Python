from discord.ext import commands
import logging, discord, os
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageHandler(commands.Cog):
    """Simplified message handler (leveling system removed)."""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot messages or DMs
        if message.author.bot or not message.guild:
            return
        # Allow other cogs / commands to process
        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(MessageHandler(bot))
    # NOTE: Legacy leveling/XP code removed.

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Handle new member joins (no DM, simplified)."""
        joins_channel_id = int(os.getenv('JOINS_LEAVES_CHANNEL_ID', 0))
        if not joins_channel_id:
            return
        channel = self.bot.get_channel(joins_channel_id)
        if not channel:
            return
        embed = discord.Embed(
            title="👋 Welcome!",
            description=f"Welcome {member.mention} to **{member.guild.name}**!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Handle member leaves (simplified)."""
        joins_channel_id = int(os.getenv('JOINS_LEAVES_CHANNEL_ID', 0))
        if not joins_channel_id:
            return
        channel = self.bot.get_channel(joins_channel_id)
        if not channel:
            return
        embed = discord.Embed(
            title="👋 Member Left",
            description=f"{member.display_name} has left the server.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Global command error handler"""
        # Don't handle errors that are already handled by command-specific handlers
        if hasattr(ctx.command, 'on_error'):
            return
        
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You don't have permission to use this command!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
        
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Argument",
                description=f"Missing required argument: `{error.param}`\n"
                           f"Use `?help {ctx.command}` for usage information.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=15)
        
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Invalid Argument", 
                description="Invalid argument provided!\n"
                           f"Use `?help {ctx.command}` for usage information.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=15)
        
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Command on Cooldown",
                description=f"This command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed, delete_after=10)
        
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="❌ Member Not Found",
                description="Could not find the specified member!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
        
        else:
            # Log unexpected errors
            print(f"Unhandled error in command {ctx.command}: {error}")
            
            embed = discord.Embed(
                title="❌ An Error Occurred",
                description="An unexpected error occurred while processing your command.\n"
                           "Please try again later or contact an administrator.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=15)
    
    # AFK and XP systems removed per request.

async def setup(bot):
    await bot.add_cog(MessageHandler(bot))