import discord  # type: ignore[import-not-found]
from discord import app_commands  # type: ignore[import-not-found]
from discord.ext import commands  # type: ignore[import-not-found]
from collections import defaultdict, deque
import time
import logging

from config import (
    SPAM_THRESHOLD, SPAM_TIME_WINDOW, DUPLICATE_THRESHOLD,
    MENTION_THRESHOLD, CAPS_THRESHOLD,
    JOIN_THRESHOLD, JOIN_TIME_WINDOW, NEW_ACCOUNT_THRESHOLD,
    MASS_DELETE_THRESHOLD, NUKE_TIME_WINDOW,
    MODERATION_ROLE_ID, STAFF_ALERT_CHANNEL,
)
from utils.embeds import create_error_embed

logger = logging.getLogger("codeverse.protection")

class Protection(commands.Cog):
    """Anti-spam, anti-raid, and anti-nuke protection systems"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Anti-spam tracking
        self.user_messages = defaultdict(deque)
        self.user_duplicates = defaultdict(lambda: defaultdict(int))
        
        # Anti-raid tracking - auto-cleanup with maxlen
        self.recent_joins = deque(maxlen=JOIN_THRESHOLD * 2)
        
        # Anti-nuke tracking with dual time windows
        # Short window: 1 minute, max 5 bans/kicks
        self.recent_bans_1min = deque(maxlen=10)      # Track up to 10 bans in 1 min window
        self.recent_kicks_1min = deque(maxlen=10)     # Track up to 10 kicks in 1 min window
        
        # Long window: 20 minutes, max 12 bans/kicks
        self.recent_bans_20min = deque(maxlen=20)     # Track up to 20 bans in 20 min window
        self.recent_kicks_20min = deque(maxlen=20)    # Track up to 20 kicks in 20 min window
        
        # Legacy tracking for deletion
        self.recent_deletes = defaultdict(lambda: deque(maxlen=MASS_DELETE_THRESHOLD * 2))
        
        # Blocked users (rate limit cooldown)
        self.blocked_actors = {}  # {user_id: timestamp} - cooldown on blocking actions
        
        # Configuration constants
        self.ANTINUKE_1MIN_WINDOW = 60          # 1 minute
        self.ANTINUKE_1MIN_LIMIT = 5            # max 5 bans/kicks per minute
        self.ANTINUKE_20MIN_WINDOW = 1200       # 20 minutes
        self.ANTINUKE_20MIN_LIMIT = 12          # max 12 bans/kicks per 20 minutes
        self.BLOCK_COOLDOWN = 300               # Block actions for 5 minutes

    def record_action(self, actor_id: int, action_type: str):
        """Record an action for rate limiting"""
        now = time.time()
        if action_type == "ban":
            self.recent_bans_1min.append((now, actor_id))
            self.recent_bans_20min.append((now, actor_id))
        elif action_type == "kick":
            self.recent_kicks_1min.append((now, actor_id))
            self.recent_kicks_20min.append((now, actor_id))

    def check_rate_limit(self, actor_id: int, action_type: str) -> bool:
        """Check if an actor is rate limited for a specific action"""
        now = time.time()
        
        # Check if actor is blocked
        if actor_id in self.blocked_actors:
            if now - self.blocked_actors[actor_id] < self.BLOCK_COOLDOWN:
                return False
            else:
                 del self.blocked_actors[actor_id]

        if action_type == "ban":
            # Clean old entries
            while self.recent_bans_1min and now - self.recent_bans_1min[0][0] > self.ANTINUKE_1MIN_WINDOW:
                self.recent_bans_1min.popleft()
            while self.recent_bans_20min and now - self.recent_bans_20min[0][0] > self.ANTINUKE_20MIN_WINDOW:
                self.recent_bans_20min.popleft()
                
            bans_1min = sum(1 for t, aid in self.recent_bans_1min if aid == actor_id)
            bans_20min = sum(1 for t, aid in self.recent_bans_20min if aid == actor_id)
            
            # Pre-emptive check: if one more action would exceed limit
            if bans_1min >= self.ANTINUKE_1MIN_LIMIT or bans_20min >= self.ANTINUKE_20MIN_LIMIT:
                 # Add to blocked actors
                 self.blocked_actors[actor_id] = now
                 return False

        elif action_type == "kick":
             # Clean old entries
            while self.recent_kicks_1min and now - self.recent_kicks_1min[0][0] > self.ANTINUKE_1MIN_WINDOW:
                self.recent_kicks_1min.popleft()
            while self.recent_kicks_20min and now - self.recent_kicks_20min[0][0] > self.ANTINUKE_20MIN_WINDOW:
                self.recent_kicks_20min.popleft()
                
            kicks_1min = sum(1 for t, aid in self.recent_kicks_1min if aid == actor_id)
            kicks_20min = sum(1 for t, aid in self.recent_kicks_20min if aid == actor_id)
            
            if kicks_1min >= self.ANTINUKE_1MIN_LIMIT or kicks_20min >= self.ANTINUKE_20MIN_LIMIT:
                 self.blocked_actors[actor_id] = now
                 return False

        return True

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Handle anti-raid checks"""
        now = time.time()
        self.recent_joins.append(now)
        
        # Auto cleanup old joins outside the time window
        while self.recent_joins and now - self.recent_joins[0] > JOIN_TIME_WINDOW:
            self.recent_joins.popleft()
        
        # Check for join flood
        if len(self.recent_joins) > JOIN_THRESHOLD:
            try:
                embed = discord.Embed(
                    title="Raid Detection Alert",
                    description=f"Potential raid detected: {len(self.recent_joins)} joins in {JOIN_TIME_WINDOW} seconds",
                    color=0xff0000
                )
                embed.add_field(name="Recommended Action", value="Consider enabling verification requirements", inline=False)
                
                # Find staff channel
                staff_role = member.guild.get_role(MODERATION_ROLE_ID)
                if staff_role:
                    for channel in member.guild.text_channels:
                        if STAFF_ALERT_CHANNEL in channel.name.lower() or 'mod' in channel.name.lower():
                            await channel.send(embed=embed)
                            break
            except:
                pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Handle anti-nuke ban detection with dual-window rate limiting"""
        now = time.time()
        
        # Get the ban entry to find who banned the user
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
                if entry.target and entry.target.id == user.id:
                    actor_id = entry.user.id if entry.user else None
                    break
            else:
                actor_id = None
        except:
            actor_id = None
        
        if not actor_id:
            return
        
        # Track bans in both time windows
        self.recent_bans_1min.append((now, actor_id))
        self.recent_bans_20min.append((now, actor_id))
        
        # Clean old entries outside time windows
        while self.recent_bans_1min and now - self.recent_bans_1min[0][0] > self.ANTINUKE_1MIN_WINDOW:
            self.recent_bans_1min.popleft()
        
        while self.recent_bans_20min and now - self.recent_bans_20min[0][0] > self.ANTINUKE_20MIN_WINDOW:
            self.recent_bans_20min.popleft()
        
        # Count bans by this actor in each window
        bans_1min = sum(1 for t, aid in self.recent_bans_1min if aid == actor_id and now - t < self.ANTINUKE_1MIN_WINDOW)
        bans_20min = sum(1 for t, aid in self.recent_bans_20min if aid == actor_id and now - t < self.ANTINUKE_20MIN_WINDOW)
        
        # Check if actor is already blocked
        if actor_id in self.blocked_actors:
            if now - self.blocked_actors[actor_id] < self.BLOCK_COOLDOWN:
                # Still blocked - attempt to undo the ban
                try:
                    await guild.unban(user, reason="Anti-nuke: Rate limit exceeded (user already blocked)")
                    logger.info("Auto-undid ban for %s by blocked actor %s", user, actor_id)
                except:
                    pass
                return
            else:
                # Cooldown expired, remove from blocked list
                del self.blocked_actors[actor_id]
        
        # Check thresholds and trigger protection if exceeded
        triggered = False
        reason = ""
        
        if bans_1min > self.ANTINUKE_1MIN_LIMIT:
            triggered = True
            reason = f"Exceeded {self.ANTINUKE_1MIN_LIMIT} bans in 1 minute ({bans_1min} detected)"
        elif bans_20min > self.ANTINUKE_20MIN_LIMIT:
            triggered = True
            reason = f"Exceeded {self.ANTINUKE_20MIN_LIMIT} bans in 20 minutes ({bans_20min} detected)"
        
        if triggered:
            # Block the actor
            self.blocked_actors[actor_id] = now
            
            try:
                actor = guild.get_member(actor_id) or await self.bot.fetch_user(actor_id)
                
                # Undo the ban
                try:
                    await guild.unban(user, reason="Anti-nuke: Rate limit protection triggered")
                except:
                    pass
                
                # Alert staff
                embed = discord.Embed(
                    title="🛡️ Anti-Nuke: Ban Rate Limit Triggered",
                    description=f"**{actor}** exceeded the ban rate limit and has been blocked from taking moderation actions.",
                    color=0xff0000
                )
                embed.add_field(name="⚠️ Reason", value=reason, inline=False)
                embed.add_field(name="👤 Target", value=f"{user} ({user.id})", inline=True)
                embed.add_field(name="🔒 Blocked Until", value=f"<t:{int(now + self.BLOCK_COOLDOWN)}:R>", inline=True)
                embed.add_field(name="📋 Action Taken", value="Ban reversed and actor blocked", inline=False)
                embed.set_footer(text="Anti-Nuke Protection System")
                
                # Find staff channel
                staff_role = guild.get_role(MODERATION_ROLE_ID)
                if staff_role:
                    for channel in guild.text_channels:
                        if STAFF_ALERT_CHANNEL in channel.name.lower() or 'mod' in channel.name.lower():
                            await channel.send(embed=embed)
                            break
                
                logger.warning("Anti-nuke ban protection triggered for actor %s: %s", actor_id, reason)
            except Exception as e:
                logger.error("Error in ban protection: %s", e)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Handle anti-nuke kick detection with dual-window rate limiting"""
        if not hasattr(member, 'guild'):
            return
        
        now = time.time()
        
        # Get the kick entry to find who kicked the member
        try:
            async for entry in member.guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
                if entry.target and entry.target.id == member.id:
                    actor_id = entry.user.id if entry.user else None
                    break
            else:
                actor_id = None
        except:
            actor_id = None
        
        if not actor_id:
            return
        
        # Track kicks in both time windows
        self.recent_kicks_1min.append((now, actor_id))
        self.recent_kicks_20min.append((now, actor_id))
        
        # Clean old entries outside time windows
        while self.recent_kicks_1min and now - self.recent_kicks_1min[0][0] > self.ANTINUKE_1MIN_WINDOW:
            self.recent_kicks_1min.popleft()
        
        while self.recent_kicks_20min and now - self.recent_kicks_20min[0][0] > self.ANTINUKE_20MIN_WINDOW:
            self.recent_kicks_20min.popleft()
        
        # Count kicks by this actor in each window
        kicks_1min = sum(1 for t, aid in self.recent_kicks_1min if aid == actor_id and now - t < self.ANTINUKE_1MIN_WINDOW)
        kicks_20min = sum(1 for t, aid in self.recent_kicks_20min if aid == actor_id and now - t < self.ANTINUKE_20MIN_WINDOW)
        
        # Check if actor is already blocked
        if actor_id in self.blocked_actors:
            if now - self.blocked_actors[actor_id] < self.BLOCK_COOLDOWN:
                # Still blocked - log but cannot undo kick (no direct unban API for kicks)
                logger.info("Kick blocked for %s by blocked actor %s", member, actor_id)
                return
            else:
                # Cooldown expired, remove from blocked list
                del self.blocked_actors[actor_id]
        
        # Check thresholds and trigger protection if exceeded
        triggered = False
        reason = ""
        
        if kicks_1min > self.ANTINUKE_1MIN_LIMIT:
            triggered = True
            reason = f"Exceeded {self.ANTINUKE_1MIN_LIMIT} kicks in 1 minute ({kicks_1min} detected)"
        elif kicks_20min > self.ANTINUKE_20MIN_LIMIT:
            triggered = True
            reason = f"Exceeded {self.ANTINUKE_20MIN_LIMIT} kicks in 20 minutes ({kicks_20min} detected)"
        
        if triggered:
            # Block the actor
            self.blocked_actors[actor_id] = now
            
            try:
                actor = member.guild.get_member(actor_id) or await self.bot.fetch_user(actor_id)
                
                # Alert staff (cannot undo kick, but can log and block)
                embed = discord.Embed(
                    title="🛡️ Anti-Nuke: Kick Rate Limit Triggered",
                    description=f"**{actor}** exceeded the kick rate limit and has been blocked from taking moderation actions.",
                    color=0xff0000
                )
                embed.add_field(name="⚠️ Reason", value=reason, inline=False)
                embed.add_field(name="👤 Target", value=f"{member} ({member.id})", inline=True)
                embed.add_field(name="🔒 Blocked Until", value=f"<t:{int(now + self.BLOCK_COOLDOWN)}:R>", inline=True)
                embed.add_field(name="📋 Action Taken", value="Actor blocked from moderation actions", inline=False)
                embed.set_footer(text="Anti-Nuke Protection System")
                
                # Find staff channel
                staff_role = member.guild.get_role(MODERATION_ROLE_ID)
                if staff_role:
                    for channel in member.guild.text_channels:
                        if STAFF_ALERT_CHANNEL in channel.name.lower() or 'mod' in channel.name.lower():
                            await channel.send(embed=embed)
                            break
                
                logger.warning("Anti-nuke kick protection triggered for actor %s: %s", actor_id, reason)
            except Exception as e:
                logger.error("Error in kick protection: %s", e)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        """Handle mass delete detection"""
        if not messages:
            return
            
        guild = messages[0].guild
        now = time.time()
        self.recent_deletes[guild.id].append(now)
        
        # Count recent deletes
        recent_count = sum(1 for t in self.recent_deletes[guild.id] if now - t < NUKE_TIME_WINDOW)
        
        if recent_count > MASS_DELETE_THRESHOLD:
            try:
                embed = discord.Embed(
                    title="Mass Delete Alert",
                    description=f"Mass delete detected: {len(messages)} messages deleted",
                    color=0xff0000
                )
                embed.add_field(name="Channel", value=messages[0].channel.mention, inline=True)
                embed.add_field(name="Recommended Action", value="Check audit logs for suspicious activity", inline=False)
                
                # Find staff channel
                staff_role = guild.get_role(MODERATION_ROLE_ID)
                if staff_role:
                    for channel in guild.text_channels:
                        if STAFF_ALERT_CHANNEL in channel.name.lower() or 'mod' in channel.name.lower():
                            await channel.send(embed=embed)
                            break
            except:
                pass

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def antispam(self, ctx, action: str = "status"):
        """Configure anti-spam settings"""
        if action.lower() == "status":
            embed = discord.Embed(title="Anti-Spam Status", color=0x0000ff)
            embed.add_field(name="Message Threshold", value=f"{SPAM_THRESHOLD} messages", inline=True)
            embed.add_field(name="Time Window", value=f"{SPAM_TIME_WINDOW} seconds", inline=True)
            embed.add_field(name="Duplicate Threshold", value=f"{DUPLICATE_THRESHOLD} duplicates", inline=True)
            embed.add_field(name="Mention Threshold", value=f"{MENTION_THRESHOLD} mentions", inline=True)
            embed.add_field(name="Caps Threshold", value=f"{int(CAPS_THRESHOLD * 100)}%", inline=True)
            
            # Show current tracking stats
            active_users = len(self.user_messages)
            embed.add_field(name="Active Tracking", value=f"{active_users} users", inline=True)
            
            await ctx.send(embed=embed)
        else:
            embed = create_error_embed("Invalid Action", "Use `!antispam status` to view current settings.")
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def antiraid(self, ctx, action: str = "status"):
        """Configure anti-raid settings"""
        if action.lower() == "status":
            embed = discord.Embed(title="Anti-Raid Status", color=0x0000ff)
            embed.add_field(name="Join Threshold", value=f"{JOIN_THRESHOLD} joins", inline=True)
            embed.add_field(name="Time Window", value=f"{JOIN_TIME_WINDOW} seconds", inline=True)
            embed.add_field(name="New Account Threshold", value=f"{NEW_ACCOUNT_THRESHOLD} days", inline=True)
            
            # Show current tracking stats
            recent_joins_count = len(self.recent_joins)
            embed.add_field(name="Recent Joins", value=f"{recent_joins_count} in window", inline=True)
            
            await ctx.send(embed=embed)
        else:
            embed = create_error_embed("Invalid Action", "Use `!antiraid status` to view current settings.")
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def antinuke(self, ctx, action: str = "status"):
        """Configure anti-nuke settings with dual-window rate limiting"""
        if action.lower() == "status":
            embed = discord.Embed(title="🛡️ Anti-Nuke Status (Enhanced Rate Limiting)", color=0x0000ff)
            
            # Short window (1 minute)
            embed.add_field(
                name="⚡ 1-Minute Limit",
                value=f"**Maximum:** {self.ANTINUKE_1MIN_LIMIT} bans/kicks per minute",
                inline=False
            )
            
            # Long window (20 minutes)
            embed.add_field(
                name="🔔 20-Minute Limit",
                value=f"**Maximum:** {self.ANTINUKE_20MIN_LIMIT} bans/kicks per 20 minutes",
                inline=False
            )
            
            # Block cooldown
            embed.add_field(
                name="🔒 Block Cooldown",
                value=f"Violators blocked for **{self.BLOCK_COOLDOWN // 60} minutes**",
                inline=False
            )
            
            # Current tracking stats
            now = time.time()
            bans_1min = sum(1 for t, _ in self.recent_bans_1min if now - t < self.ANTINUKE_1MIN_WINDOW)
            bans_20min = sum(1 for t, _ in self.recent_bans_20min if now - t < self.ANTINUKE_20MIN_WINDOW)
            kicks_1min = sum(1 for t, _ in self.recent_kicks_1min if now - t < self.ANTINUKE_1MIN_WINDOW)
            kicks_20min = sum(1 for t, _ in self.recent_kicks_20min if now - t < self.ANTINUKE_20MIN_WINDOW)
            
            embed.add_field(
                name="📊 Recent Activity",
                value=f"**Bans:** {bans_1min} (1m) / {bans_20min} (20m)\n**Kicks:** {kicks_1min} (1m) / {kicks_20min} (20m)",
                inline=False
            )
            
            blocked_count = sum(1 for exp in self.blocked_actors.values() if exp > now)
            embed.add_field(
                name="🚫 Currently Blocked",
                value=f"**{blocked_count}** user(s) blocked from moderation",
                inline=False
            )
            
            embed.set_footer(text="⚠️ Actions exceeding limits will be reversed and actor blocked")
            await ctx.send(embed=embed)
        else:
            embed = create_error_embed("Invalid Action", "Use `!antinuke status` to view current settings and activity.")
            await ctx.send(embed=embed)

    @app_commands.command(name="getuserid", description="Get the user ID of a selected member")
    @app_commands.describe(user="The member to get the ID of")
    async def getuserid_slash(self, interaction: discord.Interaction, user: discord.Member):
        """Slash command: /getuserid user: <member>"""
        try:
            await interaction.response.send_message(f"{user} — ID: {user.id}", ephemeral=True)
        except Exception:
            # Fallback for already-responded interactions
            try:
                await interaction.followup.send(f"{user} — ID: {user.id}", ephemeral=True)
            except:
                pass

    @commands.command(name="getuserid")
    async def getuserid(self, ctx, user: discord.Member):
        """Fallback text command to get user id: ?getuserid @member"""
        await ctx.send(f"{user} — ID: {user.id}")

async def setup(bot):
    await bot.add_cog(Protection(bot))