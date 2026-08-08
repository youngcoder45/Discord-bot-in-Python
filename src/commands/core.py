import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from typing import Optional
from utils.json_store import get_guild_prefix, set_guild_prefix
from commands.help_menu import send_help_menu

DEFAULT_PREFIX = '?'

REPORT_CHANNEL_ID = 1418492683277570109

class Core(commands.Cog):
    """Core hybrid commands: ping, info, help menu."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = getattr(bot, 'start_time', datetime.now(timezone.utc))
        
        # Register Context Menu
        self.ctx_menu = app_commands.ContextMenu(
            name='Report Message',
            callback=self.report_message_ctx,
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    @commands.command(name="sync", hidden=True)
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        """Syncs the command tree."""
        msg = await ctx.reply("Syncing...", mention_author=False)
        try:
            synced = await self.bot.tree.sync()
            await msg.edit(content=f"Synced {len(synced)} commands globally.")
        except Exception as e:
            await msg.edit(content=f"Sync failed: {e}")

    @commands.command(name="load", hidden=True)
    @commands.is_owner()
    async def load_cog(self, ctx: commands.Context, cog_name: str):
        """Load or reload a specific cog."""
        msg = await ctx.reply(f"Reloading cog `{cog_name}`...", mention_author=False)
        
        # Map common names to actual cog paths
        cog_mapping = {
            "core": "commands.core",
            "help": "commands.core",
            "mod": "commands.modcog",
            "modcog": "commands.modcog",
            "moderation": "commands.modcog",
            "advanced_mod": "commands.advanced_moderation",
            "advanced_moderation": "commands.advanced_moderation",
            "tickets": "commands.tickets",
            "utility": "commands.utility",
            "embeds": "commands.utility",
            "thread": "commands.thread",
            "threads": "commands.thread",
            "appeals": "commands.appeals",
            "logging": "commands.logging",
            "logging_cog": "commands.logging",
            "diagnostics": "commands.diagnostics",
            "spam": "commands.spam_catch",
            "spam_catch": "commands.spam_catch",
            "roles": "commands.roles",
            "reaction_roles": "commands.reaction_roles",
            "sticky": "commands.sticky_message",
            "sticky_message": "commands.sticky_message",
            "rules": "commands.rules",
        }
        
        # Get the actual cog path
        cog_path = cog_mapping.get(cog_name.lower(), f"commands.{cog_name}")
        
        try:
            # Try to reload if already loaded
            try:
                await self.bot.reload_extension(cog_path)
                await msg.edit(content=f"Successfully reloaded cog `{cog_name}` ({cog_path})")
            except commands.ExtensionNotLoaded:
                # If not loaded, try to load it
                await self.bot.load_extension(cog_path)
                await msg.edit(content=f"Successfully loaded cog `{cog_name}` ({cog_path})")
        except commands.ExtensionNotFound:
            await msg.edit(content=f"Cog `{cog_name}` not found. Path tried: {cog_path}")
        except commands.ExtensionFailed as e:
            await msg.edit(content=f"Failed to load `{cog_name}`: {str(e)}")
        except Exception as e:
            await msg.edit(content=f"Error loading `{cog_name}`: {str(e)}")

    @commands.hybrid_command(name="prefix", help="View or change the bot prefix")
    @app_commands.describe(new_prefix="New prefix to use in this server")
    async def prefix(self, ctx: commands.Context, new_prefix: Optional[str] = None):
        """View or change the bot's command prefix for this guild."""
        if ctx.guild is None:
            await ctx.reply(f"Current prefix: `{DEFAULT_PREFIX}` (prefix changes are only supported in servers).", mention_author=False)
            return

        current = await get_guild_prefix(ctx.guild.id) or DEFAULT_PREFIX

        if new_prefix is None:
            await ctx.reply(
                f"Current prefix for **{ctx.guild.name}**: `{current}`\n"
                f"To change it: `/prefix <new_prefix>`",
                mention_author=False,
            )
            return

        # Permission gate only when changing
        if not getattr(ctx.author, 'guild_permissions', None) or not ctx.author.guild_permissions.manage_guild:
            await ctx.reply("You need the **Manage Server** permission to change the prefix.", mention_author=False)
            return

        new_prefix = new_prefix.strip()
        if not (1 <= len(new_prefix) <= 5) or any(ch.isspace() for ch in new_prefix):
            await ctx.reply("Prefix must be 1–5 characters and contain no spaces.", mention_author=False)
            return

        await set_guild_prefix(ctx.guild.id, new_prefix)
        await ctx.reply(f"Prefix updated for **{ctx.guild.name}**: `{current}` → `{new_prefix}`", mention_author=False)

    @commands.hybrid_command(name="ping", help="Check if the bot is responsive")
    async def ping(self, ctx: commands.Context):
        """Latency check."""
        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="Connection Status", 
            description=f"WebSocket Latency: {latency_ms}ms",
            color=0x00ff00
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="get-user-id",
        aliases=["getuserid"],
        help="Get the Discord ID of a user",
    )
    @app_commands.describe(user="The user to get the ID of (defaults to you)")
    async def get_user_id(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Return the numeric Discord ID of a user in an ephemeral message."""
        target = user or ctx.author
        await ctx.reply(f"user id is `{target.id}`", ephemeral=True)

    async def _send_report(self, reporter, message, interaction_or_ctx):
        """Helper to send report embed"""
        report_channel = self.bot.get_channel(REPORT_CHANNEL_ID)
        if not report_channel:
            try:
                report_channel = await self.bot.fetch_channel(REPORT_CHANNEL_ID)
            except (discord.Forbidden, discord.NotFound):
                msg = "Report channel not found. Please contact an admin."
                if isinstance(interaction_or_ctx, commands.Context):
                    await interaction_or_ctx.reply(msg, ephemeral=True)
                else:
                    await interaction_or_ctx.response.send_message(msg, ephemeral=True)
                return
            except Exception:
                msg = "Could not access report channel. Please try again later."
                if isinstance(interaction_or_ctx, commands.Context):
                    await interaction_or_ctx.reply(msg, ephemeral=True)
                else:
                    await interaction_or_ctx.response.send_message(msg, ephemeral=True)
                return

        if not isinstance(report_channel, discord.TextChannel):
             # Fallback or error if channel is not a text channel
             return

        embed = discord.Embed(title=" User Report", color=discord.Color.red(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Reporter", value=f"{reporter.mention} ({reporter.id})", inline=False)
        embed.add_field(name="Reported User", value=f"{message.author.mention} ({message.author.id})", inline=False)
        embed.add_field(name="Channel", value=f"{message.channel.mention}", inline=True)
        embed.add_field(name="Message Link", value=f"[Jump to Message]({message.jump_url})", inline=True)
        embed.add_field(name="Content", value=message.content[:1024] or "[No Content/Attachment]", inline=False)
        
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        await report_channel.send(embed=embed)
        
        success_msg = " Report sent to moderators."
        if isinstance(interaction_or_ctx, commands.Context):
            await interaction_or_ctx.reply(success_msg, ephemeral=True)
        else:
            await interaction_or_ctx.response.send_message(success_msg, ephemeral=True)

    @commands.hybrid_command(name="report", help="Report a message to the moderators")
    @app_commands.describe(message_reference="The Message ID or Link of the message to report")
    async def report(self, ctx: commands.Context, message_reference: str):
        """Report a message to the moderators."""
        message = None
        
        # Try parsing as link
        if "discord.com/channels/" in message_reference:
            try:
                parts = message_reference.split("/")
                channel_id = int(parts[-2])
                message_id = int(parts[-1])
                channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
                if isinstance(channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel, discord.StageChannel)):
                    message = await channel.fetch_message(message_id)
            except (discord.NotFound, discord.Forbidden, ValueError, IndexError):
                pass
        
        # Try parsing as ID in current channel
        if not message and message_reference.isdigit():
            try:
                message = await ctx.channel.fetch_message(int(message_reference))
            except (discord.NotFound, discord.Forbidden):
                pass
                
        if not message:
            await ctx.reply(" Could not find the message. Please provide a valid Message Link or ID from this channel.", ephemeral=True)
            return
            
        await self._send_report(ctx.author, message, ctx)

    async def report_message_ctx(self, interaction: discord.Interaction, message: discord.Message):
        await self._send_report(interaction.user, message, interaction)

    @commands.hybrid_command(name="help", aliases=["bothelp"], help="Open the interactive dropdown help center")
    @app_commands.describe(command="Optional command name to get detailed help about")
    async def help(self, ctx: commands.Context, command: str | None = None):
        """Interactive categorized help with a dropdown menu."""
        await send_help_menu(ctx, command)


    

async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
