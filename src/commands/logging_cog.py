"""
Centralized logging system for CodeVerse Bot.
Handles all logging events and sends them to the appropriate channels.
"""

import discord
from discord.ext import commands
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, Union, Dict, Any, List, Tuple
import asyncio
import sys
import logging
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.database import DATABASE_NAME
import logging

logger = logging.getLogger("codeverse.logging")

class LoggingCog(commands.Cog):
    """Centralized logging system for all bot events"""
    
    def __init__(self, bot):
        self.bot = bot
        self.log_queue = asyncio.Queue()
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
            
            # Check if guild_log_channels exists and migrate if needed
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='guild_log_channels'")
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                # Check if old schema (only 3 columns)
                cursor.execute("PRAGMA table_info(guild_log_channels)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # If old schema detected, migrate
                if 'message_log_channel_id' not in columns:
                    logger.info("Migrating guild_log_channels table to new schema...")
                    
                    # Backup old data
                    cursor.execute("SELECT * FROM guild_log_channels")
                    old_data = cursor.fetchall()
                    
                    # Drop old table
                    cursor.execute("DROP TABLE guild_log_channels")
                    
                    # Create new table with 6 channels
                    cursor.execute('''
                        CREATE TABLE guild_log_channels (
                            guild_id INTEGER PRIMARY KEY,
                            message_log_channel_id INTEGER,
                            member_log_channel_id INTEGER,
                            server_log_channel_id INTEGER,
                            ticket_log_channel_id INTEGER,
                            mod_log_channel_id INTEGER,
                            other_log_channel_id INTEGER,
                            set_by INTEGER,
                            set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    # Migrate old data (member_log -> member_log, mod_log -> mod_log, ticket_log -> ticket_log)
                    for row in old_data:
                        guild_id = row[0]
                        old_member = row[1] if len(row) > 1 else None
                        old_mod = row[2] if len(row) > 2 else None
                        old_ticket = row[3] if len(row) > 3 else None
                        old_set_by = row[4] if len(row) > 4 else 0
                        
                        cursor.execute('''
                            INSERT INTO guild_log_channels 
                            (guild_id, message_log_channel_id, member_log_channel_id, server_log_channel_id,
                             ticket_log_channel_id, mod_log_channel_id, other_log_channel_id, set_by)
                            VALUES (?, NULL, ?, NULL, ?, ?, NULL, ?)
                        ''', (guild_id, old_member, old_ticket, old_mod, old_set_by))
                    
                    logger.info("Migration completed successfully!")
            else:
                # Create new table with 6 channels
                cursor.execute('''
                    CREATE TABLE guild_log_channels (
                        guild_id INTEGER PRIMARY KEY,
                        message_log_channel_id INTEGER,
                        member_log_channel_id INTEGER,
                        server_log_channel_id INTEGER,
                        ticket_log_channel_id INTEGER,
                        mod_log_channel_id INTEGER,
                        other_log_channel_id INTEGER,
                        set_by INTEGER,
                        set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            
            # Auto-configure channels for The CodeVerse Hub (guild ID: 1263067254153805905)
            cursor.execute('''
                INSERT OR REPLACE INTO guild_log_channels 
                (guild_id, message_log_channel_id, member_log_channel_id, server_log_channel_id, 
                 ticket_log_channel_id, mod_log_channel_id, other_log_channel_id, set_by)
                VALUES (1263067254153805905, 1411766480302772435, 1263434413581008956, 1411766078920458333,
                        1438487366305190018, 1444013659134361703, 1454024682700537968, 0)
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error setting up logging database: {e}")
    
    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        if self.log_task:
            self.log_task.cancel()
    
    async def process_logs(self):
        """Background task to process log queue and send to appropriate channels"""
        try:
            # Wait for bot to be ready before processing logs
            await self.bot.wait_until_ready()
            self.is_ready = True
            
            while True:
                # Get log item from queue
                log_item = await self.log_queue.get()
                try:
                    await self._process_log_item(log_item)
                except Exception as e:
                    logger.error(f"Error processing log item: {e}")
                finally:
                    self.log_queue.task_done()
                    
                # Small delay to prevent API rate limits
                await asyncio.sleep(0.5)
        
        except asyncio.CancelledError:
            logger.info("Log processing task cancelled")
        except Exception as e:
            logger.error(f"Log processing task encountered an error: {e}")
    
    async def _process_log_item(self, log_item):
        """Process a single log item from the queue"""
        event_type = log_item.get("event_type")
        user_id = log_item.get("user_id")
        guild_id = log_item.get("guild_id")
        details = log_item.get("details", "")
        channel_id = log_item.get("channel_id")
        moderator_id = log_item.get("moderator_id")
        log_id = log_item.get("log_id")
        
        # Skip if no guild_id
        if not guild_id:
            return
        
        # Get guild-specific log channels
        log_channel = await self._get_log_channel_for_event(guild_id, event_type)
        
        if not log_channel:
            return  # No channel to send to
        
        # Create and send appropriate embed based on event type
        embed = await self._create_log_embed(log_item)
        if embed:
            try:
                await log_channel.send(embed=embed)
                
                # Update database to mark log as sent
                if log_id:
                    conn = sqlite3.connect(DATABASE_NAME)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE bot_logs SET sent_to_discord = 1 WHERE id = ?", (log_id,))
                    conn.commit()
                    conn.close()
            except Exception as e:
                logger.error(f"Error sending log to channel: {e}")
    
    async def _get_log_channel_for_event(self, guild_id: int, event_type: str):
        """Get the appropriate log channel for a guild and event type"""
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT message_log_channel_id, member_log_channel_id, server_log_channel_id,
                       ticket_log_channel_id, mod_log_channel_id, other_log_channel_id
                FROM guild_log_channels 
                WHERE guild_id = ?
            ''', (guild_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return None  # No log channels configured for this guild
            
            message_ch, member_ch, server_ch, ticket_ch, mod_ch, other_ch = result
            
            # Route events to appropriate channels
            # Member logs (joins, leaves, roles, nicknames)
            if event_type in ("MEMBER_JOIN", "MEMBER_LEAVE", "MEMBER_JOIN_BOT", "ROLE_ADD", 
                               "ROLE_REMOVE", "NICKNAME_UPDATE"):
                return self.bot.get_channel(member_ch) if member_ch else None
            
            # Server logs (channels, roles, server settings, emojis)
            elif event_type in ("CHANNEL_CREATE", "CHANNEL_DELETE", "CHANNEL_UPDATE",
                               "ROLE_CREATE", "ROLE_DELETE", "ROLE_UPDATE",
                               "GUILD_UPDATE", "EMOJI_UPDATE"):
                return self.bot.get_channel(server_ch) if server_ch else None
            
            # Ticket logs
            elif event_type.startswith("TICKET_"):
                return self.bot.get_channel(ticket_ch) if ticket_ch else None
            
            # Moderation logs (bans, kicks, timeouts, warnings, appeals, points)
            elif event_type.startswith(("BAN", "UNBAN", "KICK", "WARN", "TIMEOUT", 
                                       "MUTE", "UNMUTE", "POINT_", "APPEAL_")):
                return self.bot.get_channel(mod_ch) if mod_ch else None
            
            # Voice and other logs
            elif event_type.startswith("VOICE_") or event_type.startswith("STAFF_"):
                return self.bot.get_channel(other_ch) if other_ch else None
            
            # Default to other logs channel
            return self.bot.get_channel(other_ch) if other_ch else None
            
        except Exception as e:
            logger.error(f"Error getting log channel for guild {guild_id}: {e}")
            return None
    
    async def _create_log_embed(self, log_item):
        """Create an appropriate embed for the log item"""
        event_type = log_item.get("event_type", "UNKNOWN")
        user_id = log_item.get("user_id")
        guild_id = log_item.get("guild_id")
        details = log_item.get("details", "")
        moderator_id = log_item.get("moderator_id")
        timestamp = log_item.get("timestamp", datetime.now(timezone.utc))
        
        # Resolve user and moderator objects
        user = None
        moderator = None
        
        if user_id:
            try:
                user = await self.bot.fetch_user(user_id)
            except:
                user = f"Unknown User ({user_id})"
        
        if moderator_id:
            try:
                moderator = await self.bot.fetch_user(moderator_id)
            except:
                moderator = f"Unknown Moderator ({moderator_id})"
        
        # Base embed with timestamp
        embed = discord.Embed(timestamp=timestamp)
        
        # Configure embed based on event type
        if event_type.startswith("MEMBER_JOIN"):
            embed.title = "Member Joined"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} joined the server"
            embed.color = discord.Color(0x2B2D31)
            
            # Add account creation date if available
            if isinstance(user, discord.User):
                account_age = (datetime.now(timezone.utc) - user.created_at).days
                embed.add_field(name="Account Age", value=f"{account_age} days", inline=True)
                embed.add_field(name="Created On", value=f"<t:{int(user.created_at.timestamp())}:F>", inline=True)
                
                # Set thumbnail if available
                if user.avatar:
                    embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("MEMBER_LEAVE"):
            embed.title = "Member Left"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} left the server"
            embed.color = discord.Color(0x2B2D31)
            
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("BAN"):
            embed.title = "Member Banned"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was banned"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
                
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("UNBAN"):
            embed.title = "Member Unbanned"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was unbanned"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
            
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("KICK"):
            embed.title = "Member Kicked"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was kicked"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
                
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("TIMEOUT") or event_type.startswith("MUTE"):
            embed.title = "Member Timed Out"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was timed out"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if "duration" in log_item:
                duration = log_item.get("duration", "Unknown")
                embed.add_field(name="Duration", value=duration, inline=True)
                
            if "expires" in log_item:
                expires = log_item.get("expires")
                if expires:
                    embed.add_field(name="Expires", value=f"<t:{int(expires.timestamp())}:R>", inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
                
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("UNMUTE"):
            embed.title = "Timeout Removed"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was unmuted"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
                
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("WARN"):
            embed.title = "Warning Issued"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was warned"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if "case_id" in log_item:
                case_id = log_item.get("case_id")
                embed.add_field(name="Case ID", value=f"#{case_id}", inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
                
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("APPEAL_"):
            if "SUBMITTED" in event_type:
                embed.title = "Appeal Submitted"
                embed.color = discord.Color(0x2B2D31)
            elif "APPROVED" in event_type:
                embed.title = "Appeal Approved"
                embed.color = discord.Color(0x2B2D31)
            elif "DENIED" in event_type:
                embed.title = "Appeal Denied"
                embed.color = discord.Color(0x2B2D31)
            else:
                embed.title = "Appeal Updated"
                embed.color = discord.Color(0x2B2D31)
            
            embed.description = f"Appeal from {user.mention if isinstance(user, discord.User) else user}"
            
            if "appeal_id" in log_item:
                appeal_id = log_item.get("appeal_id")
                embed.add_field(name="Appeal ID", value=f"#{appeal_id}", inline=True)
            
            if moderator and "SUBMITTED" not in event_type:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details[:1024], inline=False)
                
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("ROLE_"):
            embed.title = "Role Updated"
            embed.description = f"Role change for {user.mention if isinstance(user, discord.User) else user}"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Updated By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
                
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("POINT_"):
            embed.title = "Staff Points Updated"
            embed.description = f"Point update for {user.mention if isinstance(user, discord.User) else user}"
            embed.color = discord.Color(0x2B2D31)
            
            if "points" in log_item:
                points = log_item.get("points")
                embed.add_field(name="Points", value=f"{points:+d}", inline=True)
            
            if "total" in log_item:
                total = log_item.get("total")
                embed.add_field(name="Total", value=f"{total}", inline=True)
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
                
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("NICKNAME_"):
            embed.title = "Nickname Changed"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} changed nickname"
            embed.color = discord.Color(0x2B2D31)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
                
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        



        elif event_type.startswith("VOICE_MUTE"):
            embed.title = "Voice Server Muted"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was server muted"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Muted By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type.startswith("VOICE_UNMUTE"):
            embed.title = "Voice Server Unmuted"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was server unmuted"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Unmuted By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type.startswith("VOICE_DEAFEN"):
            embed.title = "Voice Server Deafened"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was server deafened"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Deafened By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type.startswith("VOICE_UNDEAFEN"):
            embed.title = "Voice Server Undeafened"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was server undeafened"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Undeafened By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type.startswith("VOICE_DISCONNECT"):
            embed.title = "Voice Disconnected"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was disconnected from voice"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Disconnected By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            embed.color = discord.Color(0x2B2D31)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type.startswith("VOICE_UNDEAFEN"):
            embed.title = "Voice Undeafened"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was undeafened"
            embed.color = discord.Color(0x2B2D31)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type.startswith("CHANNEL_CREATE"):
            embed.title = "Channel Created"
            embed.description = "A new channel was created"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Created By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type.startswith("CHANNEL_DELETE"):
            embed.title = "Channel Deleted"
            embed.description = "A channel was deleted"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Deleted By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type.startswith("CHANNEL_UPDATE"):
            embed.title = "Channel Updated"
            embed.description = "A channel was modified"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Updated By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Changes", value=details, inline=False)
        
        elif event_type == "ROLE_CREATE":
            embed.title = "Role Created"
            embed.description = "A new role was created"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Created By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type == "ROLE_DELETE":
            embed.title = "Role Deleted"
            embed.description = "A role was deleted"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Deleted By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type == "ROLE_UPDATE":
            embed.title = "Role Updated"
            embed.description = "A role was modified"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Updated By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Changes", value=details, inline=False)
        
        elif event_type.startswith("EMOJI_"):
            embed.title = "Emojis Updated"
            embed.description = "Server emojis were modified"
            embed.color = discord.Color(0x2B2D31)
            
            if details:
                embed.add_field(name="Changes", value=details, inline=False)
        
        elif event_type.startswith("GUILD_"):
            embed.title = "Server Updated"
            embed.description = "Server settings were modified"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Updated By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Changes", value=details, inline=False)
        
        else:
            # Default for other log types
            embed.title = f"{event_type.replace('_', ' ').title()}"
            embed.description = details if details else "No details provided"
            embed.color = discord.Color(0x2B2D31)
            
            if user:
                embed.add_field(name="User", value=f"{user.mention if isinstance(user, discord.User) else user}", inline=True)
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
        
        # Add footer with log ID if available
        if "log_id" in log_item:
            log_id = log_item.get("log_id")
            embed.set_footer(text=f"Log ID: {log_id}")
        else:
            embed.set_footer(text=f"Event: {event_type}")
        
        return embed
    
    async def log_event(self, event_type: str, user_id: Optional[int] = None, 
                        guild_id: Optional[int] = None, moderator_id: Optional[int] = None, 
                        channel_id: Optional[int] = None, details: Optional[str] = None, 
                        **extra_data):
        """Main method to log an event to both database and Discord"""
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
            **extra_data  # Include any additional data
        }
        
        # Add to processing queue
        await self.log_queue.put(log_item)
    
    async def _store_log_in_db(self, timestamp, event_type, user_id, guild_id, moderator_id, channel_id, details):
        """Store log in database and return log ID"""
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bot_logs 
                (timestamp, event_type, guild_id, user_id, moderator_id, channel_id, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp.isoformat(), event_type, guild_id, user_id, moderator_id, channel_id, details
            ))
            
            log_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return log_id
        except Exception as e:
            logger.error(f"Error storing log in database: {e}")
            return None
    
    # ------------ Event Listeners ------------
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Log member join events"""
        if member.bot:
            event_type = "MEMBER_JOIN_BOT"
        else:
            event_type = "MEMBER_JOIN"
            
        await self.log_event(
            event_type=event_type,
            user_id=member.id,
            guild_id=member.guild.id,
            details=f"Username: {member}"
        )
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Log member leave events"""
        if member.bot:
            event_type = "MEMBER_LEAVE_BOT" 
        else:
            event_type = "MEMBER_LEAVE"
            
        await self.log_event(
            event_type=event_type,
            user_id=member.id,
            guild_id=member.guild.id,
            details=f"Username: {member}"
        )
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Log member ban events"""
        # Wait a moment for audit log to be available
        await asyncio.sleep(1)
        
        reason = "No reason provided"
        moderator_id = None
        
        # Try to get ban reason and moderator from audit log
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=5):
                if entry.target and entry.target.id == user.id:
                    if entry.reason:
                        reason = entry.reason
                    if entry.user:
                        moderator_id = entry.user.id
                    break
        except:
            pass
        
        await self.log_event(
            event_type="BAN",
            user_id=user.id,
            guild_id=guild.id,
            moderator_id=moderator_id,
            details=reason
        )
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Log member unban events"""
        # Wait a moment for audit log to be available
        await asyncio.sleep(1)
        
        reason = "No reason provided"
        moderator_id = None
        
        # Try to get unban reason and moderator from audit log
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.unban, limit=5):
                if entry.target and entry.target.id == user.id:
                    if entry.reason:
                        reason = entry.reason
                    if entry.user:
                        moderator_id = entry.user.id
                    break
        except:
            pass
        
        await self.log_event(
            event_type="UNBAN",
            user_id=user.id,
            guild_id=guild.id,
            moderator_id=moderator_id,
            details=reason
        )
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Log member update events, focusing on roles and timeouts"""
        # Skip if bot
        if after.bot:
            return
            
        # Check for role changes
        if before.roles != after.roles:
            # Calculate role differences
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            
            role_changes = []
            if added_roles:
                role_changes.append(f"**Added:** {', '.join(role.mention for role in added_roles)}")
            if removed_roles:
                role_changes.append(f"**Removed:** {', '.join(role.mention for role in removed_roles)}")
                
            if role_changes:
                # Try to get moderator from audit log
                moderator_id = None
                try:
                    await asyncio.sleep(0.5)
                    async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=10):
                        if entry.target and entry.target.id == after.id:
                            if entry.user:
                                moderator_id = entry.user.id
                            break
                except Exception as e:
                    logger.error(f"Error fetching audit log for role update: {e}")
                
                # Log the role change
                await self.log_event(
                    event_type="ROLE_UPDATE",
                    user_id=after.id,
                    guild_id=after.guild.id,
                    moderator_id=moderator_id,
                    details="\n".join(role_changes)
                )
        
        # Check for nickname changes
        if before.nick != after.nick:
            moderator_id = None
            try:
                await asyncio.sleep(0.5)
                async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=10):
                    if entry.target and entry.target.id == after.id:
                        if entry.user:
                            moderator_id = entry.user.id
                        break
            except Exception as e:
                logger.error(f"Error fetching audit log for nickname update: {e}")
            
            old_nick = before.nick or before.name
            new_nick = after.nick or after.name
            
            await self.log_event(
                event_type="NICKNAME_UPDATE",
                user_id=after.id,
                guild_id=after.guild.id,
                moderator_id=moderator_id,
                details=f"**Before:** {old_nick}\n**After:** {new_nick}"
            )
        
        # Check for timeout changes
        before_timeout = getattr(before, 'timed_out_until', None)
        after_timeout = getattr(after, 'timed_out_until', None)
        
        # Timeout applied
        if (before_timeout is None or before_timeout <= datetime.now(timezone.utc)) and after_timeout and after_timeout > datetime.now(timezone.utc):
            # Try to get timeout reason and moderator from audit log
            reason = "No reason provided"
            moderator_id = None
            try:
                await asyncio.sleep(1)
                async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=5):
                    if entry.target and entry.target.id == after.id:
                        if entry.reason:
                            reason = entry.reason
                        if entry.user:
                            moderator_id = entry.user.id
                        break
            except:
                pass
            
            # Calculate duration
            duration = "Unknown"
            if after_timeout:
                delta = after_timeout - datetime.now(timezone.utc)
                hours, remainder = divmod(delta.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                
                if hours >= 24:
                    days, hours = divmod(hours, 24)
                    duration = f"{int(days)}d {int(hours)}h {int(minutes)}m"
                elif hours >= 1:
                    duration = f"{int(hours)}h {int(minutes)}m"
                else:
                    duration = f"{int(minutes)}m {int(seconds)}s"
            
            await self.log_event(
                event_type="TIMEOUT_APPLIED",
                user_id=after.id,
                guild_id=after.guild.id,
                moderator_id=moderator_id,
                details=reason,
                duration=duration,
                expires=after_timeout
            )
        
        # Timeout removed early
        elif before_timeout and before_timeout > datetime.now(timezone.utc) and (after_timeout is None or after_timeout <= datetime.now(timezone.utc)):
            # Try to get timeout removal reason and moderator from audit log
            reason = "No reason provided"
            moderator_id = None
            try:
                await asyncio.sleep(1)
                async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=5):
                    if entry.target and entry.target.id == after.id:
                        if entry.reason:
                            reason = entry.reason
                        if entry.user:
                            moderator_id = entry.user.id
                        break
            except:
                pass
            
            await self.log_event(
                event_type="TIMEOUT_REMOVED",
                user_id=after.id,
                guild_id=after.guild.id,
                moderator_id=moderator_id,
                details=reason
            )
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Log voice state changes - only moderator actions"""
        if not member.guild:
            return
        
        # Only log server mute (not self-mute) - check if it was done by a moderator
        if before.mute != after.mute and not before.self_mute and not after.self_mute:
            moderator_id = None
            try:
                await asyncio.sleep(0.5)
                async for entry in member.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=10):
                    if entry.target and entry.target.id == member.id:
                        if entry.user and entry.user.id != member.id:
                            moderator_id = entry.user.id
                            break
            except Exception as e:
                logger.error(f"Error fetching audit logs for voice mute: {e}")
            
            # Only log if moderator was found (not self-action)
            if moderator_id:
                if after.mute and not before.mute:
                    # Server muted by moderator
                    await self.log_event(
                        event_type="VOICE_MUTE",
                        user_id=member.id,
                        guild_id=member.guild.id,
                        moderator_id=moderator_id,
                        details=f"Server muted in {after.channel.mention if after.channel else 'voice'}"
                    )
                elif not after.mute and before.mute:
                    # Server unmuted by moderator
                    await self.log_event(
                        event_type="VOICE_UNMUTE",
                        user_id=member.id,
                        guild_id=member.guild.id,
                        moderator_id=moderator_id,
                        details=f"Server unmuted in {after.channel.mention if after.channel else 'voice'}"
                    )
        
        # Only log server deafen (not self-deafen) - check if it was done by a moderator
        if before.deaf != after.deaf and not before.self_deaf and not after.self_deaf:
            moderator_id = None
            try:
                await asyncio.sleep(0.5)
                async for entry in member.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=10):
                    if entry.target and entry.target.id == member.id:
                        if entry.user and entry.user.id != member.id:
                            moderator_id = entry.user.id
                            break
            except Exception as e:
                logger.error(f"Error fetching audit logs for voice deafen: {e}")
            
            # Only log if moderator was found (not self-action)
            if moderator_id:
                if after.deaf and not before.deaf:
                    # Server deafened by moderator
                    await self.log_event(
                        event_type="VOICE_DEAFEN",
                        user_id=member.id,
                        guild_id=member.guild.id,
                        moderator_id=moderator_id,
                        details=f"Server deafened in {after.channel.mention if after.channel else 'voice'}"
                    )
                elif not after.deaf and before.deaf:
                    # Server undeafened by moderator
                    await self.log_event(
                        event_type="VOICE_UNDEAFEN",
                        user_id=member.id,
                        guild_id=member.guild.id,
                        moderator_id=moderator_id,
                        details=f"Server undeafened in {after.channel.mention if after.channel else 'voice'}"
                    )
        
        # Log voice disconnects by moderators (when user is kicked from voice)
        if before.channel is not None and after.channel is None:
            moderator_id = None
            try:
                await asyncio.sleep(0.5)
                async for entry in member.guild.audit_logs(action=discord.AuditLogAction.member_disconnect, limit=10):
                    if entry.target and entry.target.id == member.id:
                        if entry.user and entry.user.id != member.id:
                            moderator_id = entry.user.id
                            break
            except Exception as e:
                logger.error(f"Error fetching audit logs for voice disconnect: {e}")
            
            # Only log if moderator was found (means they were kicked, not left voluntarily)
            if moderator_id:
                await self.log_event(
                    event_type="VOICE_DISCONNECT",
                    user_id=member.id,
                    guild_id=member.guild.id,
                    moderator_id=moderator_id,
                    details=f"Disconnected from {before.channel.mention}"
                )
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Log channel creations"""
        # Try to get who created it
        moderator_id = None
        try:
            await asyncio.sleep(0.5)
            async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_create, limit=5):
                if entry.target and entry.target.id == channel.id:
                    moderator_id = entry.user.id
                    break
        except Exception as e:
            logger.error(f"Error fetching audit logs for channel create: {e}")
        
        channel_type = str(channel.type).replace('_', ' ').title()
        await self.log_event(
            event_type="CHANNEL_CREATE",
            guild_id=channel.guild.id,
            moderator_id=moderator_id,
            details=f"Channel: {channel.mention}\n"
                   f"Type: {channel_type}\n"
                   f"Category: {channel.category.name if channel.category else 'None'}"
        )
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Log channel deletions"""
        # Try to get who deleted it
        moderator_id = None
        try:
            await asyncio.sleep(0.5)
            async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=5):
                if entry.target and hasattr(entry.target, 'name') and entry.target.name == channel.name:
                    moderator_id = entry.user.id
                    break
        except Exception as e:
            logger.error(f"Error fetching audit logs for channel delete: {e}")
        
        channel_type = str(channel.type).replace('_', ' ').title()
        await self.log_event(
            event_type="CHANNEL_DELETE",
            guild_id=channel.guild.id,
            moderator_id=moderator_id,
            details=f"Channel Name: #{channel.name}\n"
                   f"Type: {channel_type}\n"
                   f"Category: {channel.category.name if channel.category else 'None'}"
        )
    
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """Log channel updates"""
        if before.name == after.name and before.topic == getattr(before, 'topic', None) == getattr(after, 'topic', None):
            return  # No significant changes
        
        changes = []
        if before.name != after.name:
            changes.append(f"Name: `{before.name}` → `{after.name}`")
        
        if hasattr(before, 'topic') and hasattr(after, 'topic'):
            if before.topic != after.topic:
                before_topic = before.topic or "(none)"
                after_topic = after.topic or "(none)"
                changes.append(f"Topic: `{before_topic[:100]}` → `{after_topic[:100]}`")
        
        if not changes:
            return
        
        # Try to get who updated it
        moderator_id = None
        try:
            await asyncio.sleep(0.5)
            async for entry in after.guild.audit_logs(action=discord.AuditLogAction.channel_update, limit=5):
                if entry.target and entry.target.id == after.id:
                    moderator_id = entry.user.id
                    break
        except Exception as e:
            logger.error(f"Error fetching audit logs for channel update: {e}")
        
        await self.log_event(
            event_type="CHANNEL_UPDATE",
            guild_id=after.guild.id,
            moderator_id=moderator_id,
            details=f"Channel: {after.mention}\n" + "\n".join(changes)
        )
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """Log role creations"""
        # Try to get who created it
        moderator_id = None
        try:
            await asyncio.sleep(0.5)
            async for entry in role.guild.audit_logs(action=discord.AuditLogAction.role_create, limit=5):
                if entry.target and entry.target.id == role.id:
                    moderator_id = entry.user.id
                    break
        except Exception as e:
            logger.error(f"Error fetching audit logs for role create: {e}")
        
        await self.log_event(
            event_type="ROLE_CREATE",
            guild_id=role.guild.id,
            moderator_id=moderator_id,
            details=f"Role: {role.mention}\n"
                   f"Color: {str(role.color)}\n"
                   f"Hoisted: {role.hoist}\n"
                   f"Mentionable: {role.mentionable}"
        )
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Log role deletions"""
        # Try to get who deleted it
        moderator_id = None
        try:
            await asyncio.sleep(0.5)
            async for entry in role.guild.audit_logs(action=discord.AuditLogAction.role_delete, limit=5):
                if entry.target and entry.target.name == role.name:
                    moderator_id = entry.user.id
                    break
        except Exception as e:
            logger.error(f"Error fetching audit logs for role delete: {e}")
        
        await self.log_event(
            event_type="ROLE_DELETE",
            guild_id=role.guild.id,
            moderator_id=moderator_id,
            details=f"Role Name: {role.name}\n"
                   f"Color: {str(role.color)}"
        )
    
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        """Log role updates"""
        changes = []
        
        if before.name != after.name:
            changes.append(f"Name: `{before.name}` → `{after.name}`")
        if before.color != after.color:
            changes.append(f"Color: {before.color} → {after.color}")
        if before.hoist != after.hoist:
            changes.append(f"Hoisted: {before.hoist} → {after.hoist}")
        if before.mentionable != after.mentionable:
            changes.append(f"Mentionable: {before.mentionable} → {after.mentionable}")
        if before.permissions != after.permissions:
            changes.append("Permissions: Modified")
        
        if not changes:
            return
        
        # Try to get who updated it
        moderator_id = None
        try:
            await asyncio.sleep(0.5)
            async for entry in after.guild.audit_logs(action=discord.AuditLogAction.role_update, limit=5):
                if entry.target and entry.target.id == after.id:
                    moderator_id = entry.user.id
                    break
        except Exception as e:
            logger.error(f"Error fetching audit logs for role update: {e}")
        
        await self.log_event(
            event_type="ROLE_UPDATE",
            guild_id=after.guild.id,
            moderator_id=moderator_id,
            details=f"Role: {after.mention}\n" + "\n".join(changes)
        )
    
    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        """Log emoji changes"""
        added = set(after) - set(before)
        removed = set(before) - set(after)
        
        if not added and not removed:
            return
        
        details = []
        if added:
            details.append(f"**Added:** {', '.join(str(e) for e in added)}")
        if removed:
            details.append(f"**Removed:** {', '.join(e.name for e in removed)}")
        
        await self.log_event(
            event_type="EMOJI_UPDATE",
            guild_id=guild.id,
            details="\n".join(details)
        )
    
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        """Log server updates"""
        changes = []
        
        if before.name != after.name:
            changes.append(f"Name: `{before.name}` → `{after.name}`")
        if before.icon != after.icon:
            changes.append("Icon: Changed")
        if before.banner != after.banner:
            changes.append("Banner: Changed")
        if before.description != after.description:
            changes.append("Description: Changed")
        if before.verification_level != after.verification_level:
            changes.append(f"Verification Level: {before.verification_level} → {after.verification_level}")
        
        if not changes:
            return
        
        # Try to get who updated it
        moderator_id = None
        try:
            await asyncio.sleep(0.5)
            async for entry in after.audit_logs(action=discord.AuditLogAction.guild_update, limit=5):
                moderator_id = entry.user.id
                break
        except Exception as e:
            logger.error(f"Error fetching audit logs for guild update: {e}")
        
        await self.log_event(
            event_type="GUILD_UPDATE",
            guild_id=after.id,
            moderator_id=moderator_id,
            details="\n".join(changes)
        )
    
    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry):
        """Log specific audit log entries that might not trigger other events"""
        # Skip certain audit log actions that are handled by specific events
        skip_actions = {
            discord.AuditLogAction.ban,
            discord.AuditLogAction.unban,
            discord.AuditLogAction.member_role_update,
        }
        
        if entry.action in skip_actions:
            return
        
        # Handle kicks
        if entry.action == discord.AuditLogAction.kick:
            if entry.target and isinstance(entry.target, (discord.User, discord.Member)):
                await self.log_event(
                    event_type="KICK",
                    user_id=entry.target.id,
                    guild_id=entry.guild.id,
                    moderator_id=entry.user.id if entry.user else None,
                    details=entry.reason or "No reason provided"
                )
    
    # ------------ Public API for other cogs ------------
    
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
    
    async def log_points(self, user_id: int, guild_id: int, moderator_id: int, 
                         points: int, total: int, reason: Optional[str] = None):
        """Log point changes"""
        await self.log_event(
            event_type="POINT_CHANGE",
            user_id=user_id,
            guild_id=guild_id,
            moderator_id=moderator_id,
            details=reason,
            points=points,
            total=total
        )
    
    async def log_appeal(self, appeal_type: str, user_id: int, guild_id: int, 
                         moderator_id: Optional[int] = None, appeal_id: Optional[int] = None, 
                         details: Optional[str] = None):
        """Log appeal actions"""
        event_type = f"APPEAL_{appeal_type.upper()}"
        await self.log_event(
            event_type=event_type,
            user_id=user_id,
            guild_id=guild_id,
            moderator_id=moderator_id,
            details=details,
            appeal_id=appeal_id
        )
    
    @commands.command(name="setlogchannels")
    @commands.has_permissions(administrator=True)
    async def set_log_channels(self, ctx, 
                              message_channel: Optional[discord.TextChannel] = None,
                              member_channel: Optional[discord.TextChannel] = None,
                              server_channel: Optional[discord.TextChannel] = None,
                              ticket_channel: Optional[discord.TextChannel] = None,
                              mod_channel: Optional[discord.TextChannel] = None,
                              other_channel: Optional[discord.TextChannel] = None):
        """Set log channels for this server (6 channel types)
        
        Usage: !setlogchannels #message-logs #member-logs #server-logs #ticket-logs #mod-logs #other-logs
        You can set individual channels or all at once.
        
        Channel Types:
        1. Message Logs - Message edits/deletes/purges
        2. Member Logs - Joins/leaves/roles/nicknames
        3. Server Logs - Channels/roles/server settings
        4. Ticket Logs - Ticket system events
        5. Mod Logs - Bans/kicks/warnings/timeouts
        6. Other Logs - Voice activity/staff shifts
        """
        if not ctx.guild:
            await ctx.send("This command can only be used in a server!")
            return
        
        if not any([message_channel, member_channel, server_channel, ticket_channel, mod_channel, other_channel]):
            # Show current configuration
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT message_log_channel_id, member_log_channel_id, server_log_channel_id,
                       ticket_log_channel_id, mod_log_channel_id, other_log_channel_id
                FROM guild_log_channels 
                WHERE guild_id = ?
            ''', (ctx.guild.id,))
            
            result = cursor.fetchone()
            conn.close()
            
            embed = discord.Embed(
                title="📋 Current Log Channel Configuration",
                color=0x2B2D31
            )
            
            if result:
                msg_ch, mem_ch, srv_ch, tkt_ch, mod_ch, oth_ch = result
                embed.add_field(
                    name="1️⃣ Message Logs",
                    value=f"<#{msg_ch}>" if msg_ch else "Not set",
                    inline=True
                )
                embed.add_field(
                    name="2️⃣ Member Logs",
                    value=f"<#{mem_ch}>" if mem_ch else "Not set",
                    inline=True
                )
                embed.add_field(
                    name="3️⃣ Server Logs",
                    value=f"<#{srv_ch}>" if srv_ch else "Not set",
                    inline=True
                )
                embed.add_field(
                    name="4️⃣ Ticket Logs",
                    value=f"<#{tkt_ch}>" if tkt_ch else "Not set",
                    inline=True
                )
                embed.add_field(
                    name="5️⃣ Moderation Logs",
                    value=f"<#{mod_ch}>" if mod_ch else "Not set",
                    inline=True
                )
                embed.add_field(
                    name="6️⃣ Other Logs",
                    value=f"<#{oth_ch}>" if oth_ch else "Not set",
                    inline=True
                )
            else:
                embed.description = "No log channels configured for this server."
            
            embed.set_footer(text="Use !setlogchannels to configure (6 channels)")
            await ctx.send(embed=embed)
            return
        
        # Update configuration
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Get current config
        cursor.execute('''
            SELECT message_log_channel_id, member_log_channel_id, server_log_channel_id,
                   ticket_log_channel_id, mod_log_channel_id, other_log_channel_id
            FROM guild_log_channels 
            WHERE guild_id = ?
        ''', (ctx.guild.id,))
        
        result = cursor.fetchone()
        
        if result:
            # Update existing config
            curr_msg, curr_mem, curr_srv, curr_tkt, curr_mod, curr_oth = result
            new_msg = message_channel.id if message_channel else curr_msg
            new_mem = member_channel.id if member_channel else curr_mem
            new_srv = server_channel.id if server_channel else curr_srv
            new_tkt = ticket_channel.id if ticket_channel else curr_tkt
            new_mod = mod_channel.id if mod_channel else curr_mod
            new_oth = other_channel.id if other_channel else curr_oth
            
            cursor.execute('''
                UPDATE guild_log_channels 
                SET message_log_channel_id = ?, member_log_channel_id = ?, server_log_channel_id = ?,
                    ticket_log_channel_id = ?, mod_log_channel_id = ?, other_log_channel_id = ?,
                    set_by = ?, set_at = CURRENT_TIMESTAMP
                WHERE guild_id = ?
            ''', (new_msg, new_mem, new_srv, new_tkt, new_mod, new_oth, ctx.author.id, ctx.guild.id))
        else:
            # Insert new config
            cursor.execute('''
                INSERT INTO guild_log_channels 
                (guild_id, message_log_channel_id, member_log_channel_id, server_log_channel_id,
                 ticket_log_channel_id, mod_log_channel_id, other_log_channel_id, set_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ctx.guild.id, 
                  message_channel.id if message_channel else None,
                  member_channel.id if member_channel else None,
                  server_channel.id if server_channel else None,
                  ticket_channel.id if ticket_channel else None,
                  mod_channel.id if mod_channel else None,
                  other_channel.id if other_channel else None,
                  ctx.author.id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="✅ Log Channels Updated",
            description="Server log channels have been configured successfully.",
            color=0x00ff00
        )
        
        if message_channel:
            embed.add_field(name="Message Logs", value=message_channel.mention, inline=True)
        if member_channel:
            embed.add_field(name="Member Logs", value=member_channel.mention, inline=True)
        if server_channel:
            embed.add_field(name="Server Logs", value=server_channel.mention, inline=True)
        if ticket_channel:
            embed.add_field(name="Ticket Logs", value=ticket_channel.mention, inline=True)
        if mod_channel:
            embed.add_field(name="Moderation Logs", value=mod_channel.mention, inline=True)
        if other_channel:
            embed.add_field(name="Other Logs", value=other_channel.mention, inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Add the cog to the bot"""
    await bot.add_cog(LoggingCog(bot))