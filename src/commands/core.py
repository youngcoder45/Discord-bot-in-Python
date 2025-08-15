import discord
import os
from discord.ext import commands
from datetime import datetime, timezone

class Core(commands.Cog):
    """Core hybrid commands: ping, info."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = getattr(bot, 'start_time', datetime.now(timezone.utc))

    @commands.hybrid_command(name="ping", description="Check if the bot is responsive")
    async def ping(self, ctx: commands.Context):
        """Latency check (works as /ping and ?ping)."""
        # Interaction vs prefix handling
        if getattr(ctx, 'interaction', None) and not ctx.interaction.response.is_done():
            await ctx.interaction.response.defer(ephemeral=True)
        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(title="🏓 Pong", color=discord.Color.green())
        embed.add_field(name="WebSocket Latency", value=f"{latency_ms} ms")
        send = getattr(ctx, 'interaction', None)
        if send:  # slash path
            await ctx.interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name="info", description="Get bot information")
    async def info(self, ctx: commands.Context):
        if getattr(ctx, 'interaction', None) and not ctx.interaction.response.is_done():
            await ctx.interaction.response.defer(ephemeral=True)
        uptime = datetime.now(timezone.utc) - self.start_time
        embed = discord.Embed(title="CodeVerse Bot", color=discord.Color.blue())
        embed.add_field(name="Uptime", value=str(uptime).split('.')[0], inline=False)
        embed.add_field(name="Prefix", value=str(self.bot.command_prefix), inline=True)
        instance_id = os.getenv('INSTANCE_ID', 'unknown')
        embed.add_field(name="Instance", value=instance_id, inline=True)
        embed.set_footer(text=f"Hybrid commands • Instance: {instance_id}")
        if getattr(ctx, 'interaction', None):
            await ctx.interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await ctx.reply(embed=embed)

    @commands.command(name="help", help="Show this help message")
    async def help_cmd(self, ctx: commands.Context):
        """Custom help command listing prefix & hybrid commands.

        Only invoked via prefix (?help). Lists:
          • Hybrid commands (work as slash and prefix)
          • Prefix-only commands
        Hidden commands are excluded.
        """
        embed = discord.Embed(title="📖 Help", color=discord.Color.teal())
        embed.description = "Available commands. Slash equivalents exist for hybrid commands (use / in Discord)."

        hybrids = []
        prefix_only = []
        for cmd in sorted(self.bot.commands, key=lambda c: c.name):
            if cmd.hidden:
                continue
            # Skip this help if will be added later; we'll format manually
            if cmd.name == 'help':
                continue
            is_hybrid = isinstance(cmd, commands.HybridCommand)
            entry = f"`{self.bot.command_prefix}{cmd.name}` - {cmd.help or cmd.description or 'No description'}"
            if is_hybrid:
                hybrids.append(entry + " (hybrid)")
            else:
                prefix_only.append(entry)

        if hybrids:
            embed.add_field(name="Hybrid", value="\n".join(hybrids), inline=False)
        if prefix_only:
            embed.add_field(name="Prefix Only", value="\n".join(prefix_only), inline=False)

        # Add the help command itself at bottom
        embed.add_field(name="Meta", value=f"`{self.bot.command_prefix}help` - Show this message", inline=False)
        embed.set_footer(text="CodeVerse Bot • Help")
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
