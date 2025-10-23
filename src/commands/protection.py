import discord
from discord.ext import commands
from collections import defaultdict, deque
import time
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import *

from utils.database import add_points
from utils.embeds import create_error_embed

class Protection(commands.Cog):
    """Anti-spam, anti-raid, and anti-nuke protection systems"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Anti-spam tracking
        self.user_messages = defaultdict(deque)
        self.user_duplicates = defaultdict(lambda: defaultdict(int))
        
        # Anti-raid tracking - auto-cleanup with maxlen
        self.recent_joins = deque(maxlen=JOIN_THRESHOLD * 2)
        
        # Anti-nuke tracking - auto-cleanup with maxlen
        self.recent_bans = deque(maxlen=MASS_BAN_THRESHOLD * 2)
        self.recent_kicks = deque(maxlen=MASS_KICK_THRESHOLD * 2)
        self.recent_deletes = defaultdict(lambda: deque(maxlen=MASS_DELETE_THRESHOLD * 2))

    # @commands.Cog.listener()
    # async def on_message(self, message):
    #     """Handle anti-spam checks - DISABLED BY USER REQUEST"""
    #     # Anti-spam completely removed - user got false flagged for typing "oh" twice
    #     pass

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
                    color=0xe74c3c
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
        
        # Check for new accounts
        account_age = (datetime.now(member.created_at.tzinfo) - member.created_at).days
        if account_age < NEW_ACCOUNT_THRESHOLD:
            try:
                embed = discord.Embed(
                    title="Welcome",
                    description=f"Welcome to **{member.guild.name}**! Your account is {account_age} days old. Please familiarize yourself with our community guidelines.",
                    color=0x3498db
                )
                embed.set_footer(text="New Account Detection")
                await member.send(embed=embed)
            except:
                pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Handle anti-nuke ban detection"""
        now = time.time()
        self.recent_bans.append(now)
        
        # Auto cleanup old bans outside the time window
        while self.recent_bans and now - self.recent_bans[0] > NUKE_TIME_WINDOW:
            self.recent_bans.popleft()
        
        if len(self.recent_bans) > MASS_BAN_THRESHOLD:
            try:
                embed = discord.Embed(
                    title="Mass Ban Alert",
                    description=f"Mass ban detected: {len(self.recent_bans)} bans in {NUKE_TIME_WINDOW//60} minutes",
                    color=0xe74c3c
                )
                embed.add_field(name="Recommended Action", value="Check audit logs and consider revoking bot permissions", inline=False)
                
                # Find staff channel
                staff_role = guild.get_role(MODERATION_ROLE_ID)
                if staff_role:
                    for channel in guild.text_channels:
                        if STAFF_ALERT_CHANNEL in channel.name.lower() or 'mod' in channel.name.lower():
                            await channel.send(embed=embed)
                            break
            except:
                pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Handle anti-nuke kick detection"""
        if not hasattr(member, 'guild'):
            return
        
        now = time.time()
        self.recent_kicks.append(now)
        
        # Auto cleanup old kicks outside the time window
        while self.recent_kicks and now - self.recent_kicks[0] > NUKE_TIME_WINDOW:
            self.recent_kicks.popleft()
        
        if len(self.recent_kicks) > MASS_KICK_THRESHOLD:
            try:
                embed = discord.Embed(
                    title="Mass Kick Alert",
                    description=f"Mass kick detected: {len(self.recent_kicks)} kicks in {NUKE_TIME_WINDOW//60} minutes",
                    color=0xe74c3c
                )
                embed.add_field(name="Recommended Action", value="Check audit logs and consider revoking bot permissions", inline=False)
                
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
                    color=0xe74c3c
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
            embed = discord.Embed(title="Anti-Spam Status", color=0x3498db)
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
            embed = discord.Embed(title="Anti-Raid Status", color=0x3498db)
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
        """Configure anti-nuke settings"""
        if action.lower() == "status":
            embed = discord.Embed(title="Anti-Nuke Status", color=0x3498db)
            embed.add_field(name="Mass Ban Threshold", value=f"{MASS_BAN_THRESHOLD} bans", inline=True)
            embed.add_field(name="Mass Kick Threshold", value=f"{MASS_KICK_THRESHOLD} kicks", inline=True)
            embed.add_field(name="Mass Delete Threshold", value=f"{MASS_DELETE_THRESHOLD} deletes", inline=True)
            embed.add_field(name="Time Window", value=f"{NUKE_TIME_WINDOW//60} minutes", inline=True)
            
            # Show current tracking stats
            recent_bans_count = len(self.recent_bans)
            recent_kicks_count = len(self.recent_kicks)
            embed.add_field(name="Recent Bans", value=f"{recent_bans_count} in window", inline=True)
            embed.add_field(name="Recent Kicks", value=f"{recent_kicks_count} in window", inline=True)
            
            await ctx.send(embed=embed)
        else:
            embed = create_error_embed("Invalid Action", "Use `!antinuke status` to view current settings.")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Protection(bot))