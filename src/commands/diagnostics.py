import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from pathlib import Path

class Diagnostics(commands.Cog):
    """Bot diagnostics and health monitoring."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="diag", help="Show comprehensive bot diagnostics")
    async def diag(self, ctx: commands.Context):
        """Show bot diagnostics and health status."""
        uptime = datetime.now(timezone.utc) - getattr(self.bot, 'start_time', datetime.now(timezone.utc))
        
        embed = discord.Embed(
            title="Bot Diagnostics",
            description="Current system status and health metrics",
            color=0x3498DB,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Basic Info
        embed.add_field(
            name="Instance Information",
            value=f"**ID:** {os.getenv('INSTANCE_ID', 'production')}\n**Uptime:** {str(uptime).split('.')[0]}",
            inline=True
        )
        
        # Performance
        embed.add_field(
            name="Performance Metrics",
            value=f"**Latency:** {round(self.bot.latency*1000)}ms\n**Guilds:** {len(self.bot.guilds)}",
            inline=True
        )
        
        # Database Status
        db_files = []
        data_dir = Path("data")
        if data_dir.exists():
            for db_file in data_dir.glob("*.db"):
                db_files.append(db_file.name)
        
        embed.add_field(
            name="Database Status",
            value=f"**Active DBs:** {len(db_files)}\n**Files:** {', '.join(db_files) if db_files else 'None'}",
            inline=False
        )
        
        # Environment Check
        required_vars = ['DISCORD_TOKEN', 'GUILD_ID']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        embed.add_field(
            name="Environment Status",
            value=f"**Config:** {'Complete' if not missing_vars else 'Missing variables'}\n**Platform:** {os.getenv('HOSTING_PLATFORM', 'Unknown')}",
            inline=True
        )
        
        embed.set_footer(text=f"Bot Version: Production | Instance: {os.getenv('INSTANCE_ID', 'prod')}")
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot: commands.Bot):
    await bot.add_cog(Diagnostics(bot))
