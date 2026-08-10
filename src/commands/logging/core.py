import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from utils.database import DATABASE_NAME
from utils.webhook_manager import WebhookManager
from utils.embeds import create_success_embed, create_error_embed, create_info_embed
from config import MAIN_GUILD_ID
from .config import LOG_CHANNEL_MAP
from .formatter import LogFormatter

from .events.members import MemberLogMixin
from .events.channels import ChannelLogMixin
from .events.roles import RoleLogMixin
from .events.moderation import ModerationLogMixin
from .events.voice import VoiceLogMixin

logger = logging.getLogger("codeverse.logging")

# Column order used for the guild_log_channels row (shared by the manual
# log-channel setup commands and the channel resolution fallback).
LOG_COLUMNS = [
    "message_log_channel_id", "member_log_channel_id", "server_log_channel_id",
    "ticket_log_channel_id", "mod_log_channel_id", "other_log_channel_id",
]

class LoggingCog(MemberLogMixin, ChannelLogMixin, RoleLogMixin, ModerationLogMixin, VoiceLogMixin, commands.Cog):
    """Centralized logging system for all bot events"""
    
    def __init__(self, bot):
        self.bot = bot
        self.webhook_manager = WebhookManager(bot)
        self.log_queue = asyncio.Queue()
        self.formatter = LogFormatter(bot)
        self.is_ready = False
        # Registry of command-initiated moderation actions so the event
        # listeners can attribute logs to the real command invoker instead of
        # the bot (see ModerationLogMixin.register_command_action).
        self._pending_mod_actions: dict = {}
        
        # Start log processing task
        self.log_task = asyncio.create_task(self.process_logs())
        
        # Create database tables if needed
        self.setup_database()
        
    def setup_database(self):
        """Create database tables for logging if they don't exist"""
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            
            # Create logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    event_type TEXT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    moderator_id INTEGER,
                    channel_id INTEGER,
                    details TEXT,
                    sent_to_discord BOOLEAN DEFAULT 0
                )
            ''')
            # Table used by the /setlogchannels command so log destinations can
            # be configured manually per guild. Columns mirror the legacy
            # guild_log_channels layout read by _get_legacy_log_channel.
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS guild_log_channels (
                    guild_id INTEGER PRIMARY KEY,
                    message_log_channel_id INTEGER,
                    member_log_channel_id INTEGER,
                    server_log_channel_id INTEGER,
                    ticket_log_channel_id INTEGER,
                    mod_log_channel_id INTEGER,
                    other_log_channel_id INTEGER
                )
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error setting up logging database: {e}")
    
    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        if self.log_task:
            self.log_task.cancel()
    
    async def get_log_channel_id(self, guild_id: int, event_type: str) -> Optional[int]:
        """Resolve channel ID for event.

        Priority 1: per-guild channels configured manually via the
        /setlogchannels command (stored in guild_log_channels).
        Priority 2: hardcoded LOG_CHANNEL_MAP for the main server.
        """
        # Manual per-guild configuration wins so admins can override defaults.
        db_channel = await self._get_legacy_log_channel(guild_id, event_type)
        if db_channel:
            return db_channel

        # Fallback: default map for the main server (MAIN_GUILD_ID from .env)
        if guild_id == MAIN_GUILD_ID and event_type in LOG_CHANNEL_MAP:
            return LOG_CHANNEL_MAP[event_type]

        return None

    async def _get_legacy_log_channel(self, guild_id: int, event_type: str):
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                f'''SELECT {', '.join(LOG_COLUMNS)}
                FROM guild_log_channels WHERE guild_id = ?''',
                (guild_id,),
            )
            result = cursor.fetchone()
            conn.close()
            if not result: return None
            
            message_ch, member_ch, server_ch, ticket_ch, mod_ch, other_ch = result
            
            # Legacy simple mapping
            if event_type.startswith("MEMBER_") or event_type in ("ROLE_ADD", "ROLE_REMOVE", "NICKNAME_UPDATE", "USER_UPDATE"):
                return member_ch
            elif event_type.startswith("TICKET_"):
                return ticket_ch
            elif event_type.startswith(("BAN", "UNBAN", "KICK", "WARN", "TIMEOUT", "MUTE", "UNMUTE")):
                return mod_ch
            elif event_type in ("CHANNEL_CREATE", "CHANNEL_DELETE", "CHANNEL_UPDATE", "ROLE_CREATE", "ROLE_DELETE", "ROLE_UPDATE"):
                return server_ch
                
            return other_ch
        except: return None

    async def log_event(self, event_type: str, user_id: Optional[int] = None, 
                        guild_id: Optional[int] = None, moderator_id: Optional[int] = None, 
                        channel_id: Optional[int] = None, details: Optional[str] = None, 
                        **extra_data):
        """Main method to log an event"""
        timestamp = datetime.now(timezone.utc)
        
        # Store in database
        log_id = await self._store_log_in_db(
            timestamp, event_type, user_id, guild_id, moderator_id, channel_id, details
        )
        
        # Prepare log item for queue
        log_item = {
            "log_id": log_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "user_id": user_id,
            "guild_id": guild_id, 
            "moderator_id": moderator_id,
            "channel_id": channel_id,
            "details": details,
            **extra_data
        }
        
        await self.log_queue.put(log_item)
    
    async def _store_log_in_db(self, timestamp, event_type, user_id, guild_id, moderator_id, channel_id, details):
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO bot_logs 
                (timestamp, event_type, guild_id, user_id, moderator_id, channel_id, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp.isoformat(), event_type, guild_id, user_id, moderator_id, channel_id, str(details)
            ))
            log_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return log_id
        except Exception as e:
            logger.error(f"Error storing log in database: {e}")
            return None

    async def process_logs(self):
        await self.bot.wait_until_ready()
        self.is_ready = True
        while True:
            log_item = await self.log_queue.get()
            try:
                await self._process_log_item(log_item)
            except Exception as e:
                logger.error(f"Error processing log item: {e}")
            finally:
                self.log_queue.task_done()
            await asyncio.sleep(0.1)
    
    async def _process_log_item(self, log_item):
        guild_id = log_item.get("guild_id")
        event_type = log_item.get("event_type")
        
        if not guild_id: return

        channel_id = await self.get_log_channel_id(guild_id, event_type)
        if not channel_id: return
        
        channel = self.bot.get_channel(channel_id)
        if not channel: 
            # Try to fetch if not in cache
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except:
                logger.warning(f"Could not find log channel {channel_id} for guild {guild_id}")
                return

        # Ensure we have a text channel for webhooks
        if not isinstance(channel, discord.TextChannel):
            # For now only supporting TextChannels for logging
            return

        # Handle Tickets (Webhook Content)
        if event_type.startswith("TICKET_"):
             message = await self.formatter.create_log_message(log_item)
             webhook = await self.webhook_manager.get_webhook(channel)
             if webhook:
                 username = self.bot.user.display_name if self.bot.user else "Bot"
                 avatar_url = self.bot.user.display_avatar.url if self.bot.user else None
                 
                 await webhook.send(
                     content=message,
                     username=username,
                     avatar_url=avatar_url
                 )
             return

        # Normal Embed logs
        embed = await self.formatter.create_log_embed(log_item)
        if embed:
            success = await self.webhook_manager.send(channel, embed)
            
            if success and log_item.get("log_id"):
                try:
                    conn = sqlite3.connect(DATABASE_NAME)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE bot_logs SET sent_to_discord = 1 WHERE id = ?", (log_item["log_id"],))
                    conn.commit()
                    conn.close()
                except: pass

    # Public API for other cogs
    async def log_mod_action(self, action_type: str, user_id: int, guild_id: int, 
                             moderator_id: int, reason: Optional[str] = None, **extra_data):
        """Public API for other cogs to log moderation actions"""
        await self.log_event(
            event_type=action_type,
            user_id=user_id,
            guild_id=guild_id,
            moderator_id=moderator_id,
            details=reason,
            **extra_data
        )
    
    async def log_warning(self, user_id: int, guild_id: int, moderator_id: int, 
                          reason: str, case_id: Optional[int] = None):
        """Log warning actions"""
        await self.log_event(
            event_type="WARN",
            user_id=user_id,
            guild_id=guild_id,
            moderator_id=moderator_id,
            details=reason,
            case_id=case_id
        )

    # ------------------------------------------------------------------
    # Manual log channel setup (/setlogchannels)
    # ------------------------------------------------------------------
    # Maps the user-facing log type to its column in guild_log_channels
    # and the event categories it covers (used only for display hints).
    LOG_TYPES: Dict[str, Dict[str, Any]] = {
        "member": {"column": "member_log_channel_id", "events": "Joins, leaves, nickname & role changes"},
        "mod": {"column": "mod_log_channel_id", "events": "Bans, kicks, warns, timeouts, mutes"},
        "server": {"column": "server_log_channel_id", "events": "Channel & role create/delete/update"},
        "ticket": {"column": "ticket_log_channel_id", "events": "Ticket create/close/transcript"},
        "other": {"column": "other_log_channel_id", "events": "Everything not covered above"},
    }

    async def _get_guild_log_config(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Return the manual log channel config row for a guild, if any."""
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                f'''SELECT {', '.join(LOG_COLUMNS)}
                   FROM guild_log_channels WHERE guild_id = ?''',
                (guild_id,),
            )
            row = cursor.fetchone()
            conn.close()
            if not row:
                return None
            return dict(zip(LOG_COLUMNS, row))
        except Exception as e:
            logger.error(f"Error reading log channel config: {e}")
            return None

    def _channel_label(self, channel_id: Optional[int]) -> str:
        """Render a channel id as a mention, or 'Not set'."""
        if not channel_id:
            return "Not set"
        channel = self.bot.get_channel(channel_id)
        if channel:
            return channel.mention
        return f"`{channel_id}` (missing)"

    @commands.hybrid_command(name="setlogchannels", aliases=["setlog"])
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        log_type="Which log category to configure (member/mod/server/ticket/other)",
        channel="The channel to send these logs to (leave empty to view current setup)",
    )
    async def setlogchannels(
        self,
        ctx: commands.Context,
        log_type: str,
        channel: Optional[discord.TextChannel] = None,
    ):
        """Set up or view the manual log channel configuration for this server."""
        if not ctx.guild:
            await ctx.send(embed=create_error_embed("Error", "This command can only be used in servers."), ephemeral=True)
            return

        log_type = log_type.lower().strip()

        # Show current setup: ?setlogchannels show / list
        if log_type in ("show", "list", "status"):
            config = await self._get_guild_log_config(ctx.guild.id)
            lines = []
            for key, meta in self.LOG_TYPES.items():
                cid = config.get(meta["column"]) if config else None
                lines.append(f"**{key.capitalize()} logs:** {self._channel_label(cid)}")
            await ctx.send(
                embed=create_info_embed(
                    "Log Channel Setup",
                    "\n".join(lines) + "\n\nUse `/setlogchannels <type> #channel` to change a category.",
                ),
                ephemeral=True,
            )
            return

        meta = self.LOG_TYPES.get(log_type)
        if not meta:
            await ctx.send(
                embed=create_error_embed(
                    "Invalid Log Type",
                    f"Unknown type `{log_type}`. Valid types: {', '.join('`' + k + '`' for k in self.LOG_TYPES)}.\n"
                    "Use `show` to view the current setup.",
                ),
                ephemeral=True,
            )
            return

        if channel is None:
            config = await self._get_guild_log_config(ctx.guild.id)
            cid = config.get(meta["column"]) if config else None
            await ctx.send(
                embed=create_info_embed(
                    f"{log_type.capitalize()} Log Channel",
                    f"Current channel: {self._channel_label(cid)}\n\n"
                    f"Events covered: {meta['events']}",
                ),
                ephemeral=True,
            )
            return

        # Permission test before saving
        try:
            test_msg = await channel.send(embed=discord.Embed(title="Test", description="Log channel enabled."))
            await test_msg.delete()
        except discord.Forbidden:
            await ctx.send(
                embed=create_error_embed("Permission Error", f"I cannot send messages in {channel.mention}"),
                ephemeral=True,
            )
            return
        except Exception as e:
            await ctx.send(embed=create_error_embed("Setup Error", str(e)), ephemeral=True)
            return

        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            # Read current row if present so we only overwrite the chosen column.
            cursor.execute(
                f'''SELECT {', '.join(LOG_COLUMNS)}
                   FROM guild_log_channels WHERE guild_id = ?''',
                (ctx.guild.id,),
            )
            row = cursor.fetchone()
            current = list(row) if row else [None] * len(LOG_COLUMNS)

            col_index = LOG_COLUMNS.index(meta["column"])
            current[col_index] = channel.id

            cursor.execute(
                '''INSERT OR REPLACE INTO guild_log_channels
                   (guild_id, message_log_channel_id, member_log_channel_id, server_log_channel_id,
                    ticket_log_channel_id, mod_log_channel_id, other_log_channel_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (ctx.guild.id, *current),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            await ctx.send(embed=create_error_embed("Database Error", str(e)), ephemeral=True)
            return

        await ctx.send(
            embed=create_success_embed(
                "Log Channel Set",
                f"**{log_type.capitalize()} logs** will now be sent to {channel.mention}.\n"
                f"Events covered: {meta['events']}",
            ),
            ephemeral=True,
        )

    @commands.hybrid_command(name="setlogchannels-disable", aliases=["setlog-disable"])
    @commands.has_permissions(administrator=True)
    @app_commands.describe(log_type="Which log category to disable (member/mod/server/ticket/other)")
    async def setlogchannels_disable(self, ctx: commands.Context, log_type: str):
        """Clear the manual log channel for a category (falls back to defaults)."""
        if not ctx.guild:
            await ctx.send(embed=create_error_embed("Error", "This command can only be used in servers."), ephemeral=True)
            return

        log_type = log_type.lower().strip()
        meta = self.LOG_TYPES.get(log_type)
        if not meta:
            await ctx.send(
                embed=create_error_embed(
                    "Invalid Log Type",
                    f"Unknown type `{log_type}`. Valid types: {', '.join('`' + k + '`' for k in self.LOG_TYPES)}.",
                ),
                ephemeral=True,
            )
            return

        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                f'''SELECT {', '.join(LOG_COLUMNS)}
                   FROM guild_log_channels WHERE guild_id = ?''',
                (ctx.guild.id,),
            )
            row = cursor.fetchone()
            if not row or row[LOG_COLUMNS.index(meta["column"])] is None:
                conn.close()
                await ctx.send(
                    embed=create_info_embed(
                        "Log Channel", f"No manual **{log_type} log** channel was set."
                    ),
                    ephemeral=True,
                )
                return

            current = list(row)
            col_index = LOG_COLUMNS.index(meta["column"])
            current[col_index] = None
            cursor.execute(
                '''INSERT OR REPLACE INTO guild_log_channels
                   (guild_id, message_log_channel_id, member_log_channel_id, server_log_channel_id,
                    ticket_log_channel_id, mod_log_channel_id, other_log_channel_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (ctx.guild.id, *current),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            await ctx.send(embed=create_error_embed("Database Error", str(e)), ephemeral=True)
            return

        await ctx.send(
            embed=create_success_embed(
                "Log Channel Cleared",
                f"**{log_type.capitalize()} logs** will now fall back to the default configuration.",
            ),
            ephemeral=True,
        )
