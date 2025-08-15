import os
import discord
from discord.ext import commands
from datetime import datetime, timezone
from utils.json_store import health_snapshot

class Diagnostics(commands.Cog):
    """Operational diagnostics (prefix)."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="diag", help="Show bot diagnostics")
    async def diag(self, ctx: commands.Context):
        uptime = datetime.now(timezone.utc) - getattr(self.bot, 'start_time', datetime.now(timezone.utc))
        snap = await health_snapshot()
        embed = discord.Embed(title="🔍 Bot Diagnostics", color=discord.Color.blue())
        embed.add_field(name="Instance ID", value=os.getenv('INSTANCE_ID', 'unknown'), inline=False)
        embed.add_field(name="Uptime", value=str(uptime).split('.')[0], inline=True)
        embed.add_field(name="Users Tracked", value=str(snap.get('users', 0)), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency*1000)} ms", inline=True)
        embed.set_footer(text="Diagnostics • Use responsibly")
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot: commands.Bot):
    await bot.add_cog(Diagnostics(bot))
