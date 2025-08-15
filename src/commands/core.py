import discord
import os
from discord.ext import commands
from datetime import datetime, timezone

class Core(commands.Cog):
    """Core prefix commands: ping, info, help."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = getattr(bot, 'start_time', datetime.now(timezone.utc))

    @commands.command(name="ping", help="Check if the bot is responsive")
    async def ping(self, ctx: commands.Context):
        """Latency check."""
        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(title="🏓 Pong", color=discord.Color.green())
        embed.add_field(name="WebSocket Latency", value=f"{latency_ms} ms")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="info", help="Get bot information")
    async def info(self, ctx: commands.Context):
        uptime = datetime.now(timezone.utc) - self.start_time
        embed = discord.Embed(title="CodeVerse Bot", color=discord.Color.blue())
        embed.add_field(name="Uptime", value=str(uptime).split('.')[0], inline=False)
        embed.add_field(name="Prefix", value=str(self.bot.command_prefix), inline=True)
        instance_id = os.getenv('INSTANCE_ID', 'unknown')
        embed.add_field(name="Instance", value=instance_id, inline=True)
        embed.set_footer(text=f"Prefix commands • Instance: {instance_id}")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="help", help="Show this help message")
    async def help_cmd(self, ctx: commands.Context):
        """Custom help command listing prefix commands."""
        embed = discord.Embed(title="📖 Help", color=discord.Color.teal())
        embed.description = "Available prefix commands. Use the prefix again to run them."

        entries = []
        for cmd in sorted(self.bot.commands, key=lambda c: c.name):
            if cmd.hidden or cmd.name == 'help':
                continue
            entries.append(f"`{self.bot.command_prefix}{cmd.name}` - {cmd.help or 'No description'}")

        if entries:
            embed.add_field(name="Commands", value="\n".join(entries), inline=False)
        embed.add_field(name="Meta", value=f"`{self.bot.command_prefix}help` - Show this message", inline=False)
        embed.set_footer(text="CodeVerse Bot • Help")
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
