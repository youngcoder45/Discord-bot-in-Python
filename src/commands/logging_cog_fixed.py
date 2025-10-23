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

# Channel IDs for different log types
MEMBER_LOGS_CHANNEL = 1263434413581008956  # member updates (join/leave/role update)
MOD_LOGS_CHANNEL = 1399746928585085068     # moderation logs (ban/kick/warn/timeout)

class LoggingCog(commands.Cog):
    """Centralized logging system for all bot events"""
    
    def __init__(self, bot):
        self.bot = bot
        self.log_queue = asyncio.Queue()
        self.is_ready = False
        self.member_log_channel = None
        self.mod_log_channel = None
        
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
            
            # Get log channels
            self.member_log_channel = self.bot.get_channel(MEMBER_LOGS_CHANNEL)
            self.mod_log_channel = self.bot.get_channel(MOD_LOGS_CHANNEL)
            
            if not self.member_log_channel:
                logger.warning(f"Member log channel {MEMBER_LOGS_CHANNEL} not found")
            
            if not self.mod_log_channel:
                logger.warning(f"Moderation log channel {MOD_LOGS_CHANNEL} not found")
            
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
        
        # Determine which channel to send to
        is_mod_log = event_type.startswith(("BAN", "KICK", "WARN", "TIMEOUT", "MUTE", "UNMUTE", 
                                           "UNBAN", "MOD_", "POINT_", "APPEAL_"))
        
        log_channel = self.mod_log_channel if is_mod_log else self.member_log_channel
        
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
            embed.title = "📥 Member Joined"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} joined the server"
            embed.color = discord.Color.green()
            
            # Add account creation date if available
            if isinstance(user, discord.User):
                account_age = (datetime.now(timezone.utc) - user.created_at).days
                embed.add_field(name="Account Age", value=f"{account_age} days", inline=True)
                embed.add_field(name="Created On", value=f"<t:{int(user.created_at.timestamp())}:F>", inline=True)
                
                # Set thumbnail if available
                if user.avatar:
                    embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("MEMBER_LEAVE"):
            embed.title = "📤 Member Left"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} left the server"
            embed.color = discord.Color.gold()
            
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("BAN"):
            embed.title = "🔨 Member Banned"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was banned"
            embed.color = discord.Color.red()
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
                
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("UNBAN"):
            embed.title = "🔓 Member Unbanned"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was unbanned"
            embed.color = discord.Color.green()
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
            
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("KICK"):
            embed.title = "👢 Member Kicked"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was kicked"
            embed.color = discord.Color.orange()
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
                
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("TIMEOUT") or event_type.startswith("MUTE"):
            embed.title = "🔇 Member Timed Out"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was timed out"
            embed.color = discord.Color.dark_orange()
            
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
        
        elif event_type.startswith("WARN"):
            embed.title = "⚠️ Member Warned"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was warned"
            embed.color = discord.Color.yellow()
            
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
                embed.title = "📩 Appeal Submitted"
                embed.color = discord.Color.blue()
            elif "APPROVED" in event_type:
                embed.title = "✅ Appeal Approved"
                embed.color = discord.Color.green()
            elif "DENIED" in event_type:
                embed.title = "❌ Appeal Denied"
                embed.color = discord.Color.red()
            else:
                embed.title = "📝 Appeal Updated"
                embed.color = discord.Color.purple()
            
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
            embed.title = "👤 Role Updated"
            embed.description = f"Role change for {user.mention if isinstance(user, discord.User) else user}"
            embed.color = discord.Color.blue()
            
            if moderator:
                embed.add_field(name="Updated By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
                
            # Set thumbnail if available
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("POINT_"):
            embed.title = "🔢 Moderation Points"
            embed.description = f"Point update for {user.mention if isinstance(user, discord.User) else user}"
            embed.color = discord.Color.dark_purple()
            
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
        
        else:
            # Default for other log types
            embed.title = f"📝 {event_type.replace('_', ' ').title()}"
            embed.description = details if details else "No details provided"
            embed.color = discord.Color.light_grey()
            
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
                role_changes.append(f"Added: {', '.join(role.name for role in added_roles)}")
            if removed_roles:
                role_changes.append(f"Removed: {', '.join(role.name for role in removed_roles)}")
                
            if role_changes:
                # Try to get moderator from audit log
                moderator_id = None
                try:
                    await asyncio.sleep(1)
                    async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=5):
                        if entry.target and entry.target.id == after.id:
                            if entry.user:
                                moderator_id = entry.user.id
                            break
                except:
                    pass
                
                await self.log_event(
                    event_type="ROLE_UPDATE",
                    user_id=after.id,
                    guild_id=after.guild.id,
                    moderator_id=moderator_id,
                    details="\n".join(role_changes)
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

async def setup(bot):
    """Add the cog to the bot"""
    await bot.add_cog(LoggingCog(bot))