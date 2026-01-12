import discord
from discord.ext import commands
import asyncio
import logging
import sqlite3
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path

# Add parent directory to path to import config/utils if not in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from utils.database import DATABASE_NAME
from utils.webhook_manager import WebhookManager
from .config import LOG_CHANNEL_MAP
from .formatter import LogFormatter

from .events.members import MemberLogMixin
from .events.channels import ChannelLogMixin
from .events.roles import RoleLogMixin
from .events.moderation import ModerationLogMixin
from .events.voice import VoiceLogMixin

logger = logging.getLogger("codeverse.logging")

class LoggingCog(MemberLogMixin, ChannelLogMixin, RoleLogMixin, ModerationLogMixin, VoiceLogMixin, commands.Cog):
    """Centralized logging system for all bot events"""
    
    def __init__(self, bot):
        self.bot = bot
        self.webhook_manager = WebhookManager(bot)
        self.log_queue = asyncio.Queue()
        self.formatter = LogFormatter(bot)
        self.is_ready = False
        
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
            # Note: We are not removing the old guild_log_channels table logic 
            # as it might be used by other parts or legacy code, 
            # but for this Guild, we use the Config Map.
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error setting up logging database: {e}")
    
    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        if self.log_task:
            self.log_task.cancel()
    
    async def get_log_channel_id(self, guild_id: int, event_type: str) -> Optional[int]:
        """Resolve channel ID for event"""
        # Priority 1: Hardcoded map for The CodeVerse Hub (or main server)
        # We assume this bot runs for this server primarily or the user wants this config globally.
        # If we wanted to check guild_id, we would do:
        # if guild_id == 1263067254153805905: ...
        
        # Check specific event type
        if event_type in LOG_CHANNEL_MAP:
             return LOG_CHANNEL_MAP[event_type]
        
        # Check prefix mappings if not found exact ? 
        # (e.g. TICKET_Something -> TICKET_CREATE?) 
        # No, explicit map is better.
        
        # Fallback to DB (Legacy support)
        return await self._get_legacy_log_channel(guild_id, event_type)

    async def _get_legacy_log_channel(self, guild_id: int, event_type: str):
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT message_log_channel_id, member_log_channel_id, server_log_channel_id,
                       ticket_log_channel_id, mod_log_channel_id, other_log_channel_id
                FROM guild_log_channels WHERE guild_id = ?
            ''', (guild_id,))
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
