"""
Comprehensive moderation commands for server management
Merges functionality from moderation.py, moderation_extended.py, and sam warnings module.
"""

import discord
import asyncio
import json
import os
import re
import sqlite3
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta
from typing import Optional, Union
from utils.helpers import create_success_embed, create_error_embed, create_warning_embed, log_action

# SAM Module imports for warnings
try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from .modules.sam.internal import database, logger_config
    from .modules.sam.features.warnings.services import WarnService
    from .modules.sam.features.warnings.models import Warn
    from .modules.sam.public import logging_api
    
    SAM_AVAILABLE = True
    logger = logger_config.logger.getChild("modcog.warnings")
except ImportError:
    SAM_AVAILABLE = False
    print("Warning: SAM module not available. Warnings functionality limited.")


class ModCog(commands.Cog):
    """Comprehensive moderation commands for server management"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.muted_users = {}  # Store muted users with timestamps
        self.lockdown_channels = set()  # Store locked down channels
        self._db_session = None
        
        # Initialize warnings service if SAM is available
        self.warn_service_class = WarnService if SAM_AVAILABLE else None

    # -------- Database Session Management (for Warnings) --------
    
    async def _get_db_session(self) -> AsyncSession:
        """Get a database session."""
        if not self._db_session and SAM_AVAILABLE:
            self._db_session = await database.get_session().__aenter__()
        return self._db_session

    async def _close_db_session(self) -> None:
        """Close the database session."""
        if self._db_session and SAM_AVAILABLE:
            await self._db_session.__aexit__(None, None, None)
            self._db_session = None

    async def get_warn_service(self) -> Optional[WarnService]:
        """Get an instance of the warning service with an active database session."""
        if not SAM_AVAILABLE or self.warn_service_class is None:
            return None
            
        session = await self._get_db_session()
        return self.warn_service_class(session)

    # -------- Helpers --------

    async def _safe_reply(self, ctx: commands.Context, content: str | None = None, *, embed: discord.Embed | None = None):
        """Unified reply for hybrid commands without using ephemeral on regular ctx.send."""
        try:
            if ctx.interaction:
                if not ctx.interaction.response.is_done():
                    if embed is not None:
                        return await ctx.interaction.response.send_message(content=content or "", embed=embed, ephemeral=True)
                    return await ctx.interaction.response.send_message(content=content or "", ephemeral=True)
                else:
                    if embed is not None:
                        return await ctx.interaction.followup.send(content=content or "", embed=embed, ephemeral=True)
                    return await ctx.interaction.followup.send(content=content or "", ephemeral=True)
            if embed is not None:
                return await ctx.send(content=content or "", embed=embed)
            return await ctx.send(content=content or "")
        except Exception as e:  # Broad catch to avoid cascading errors
            print(f"[ModCog:_safe_reply] Failed to send response: {e}")

    # -------- Basic Moderation Commands --------
    
    @commands.hybrid_command(name="purge", description="Delete a number of messages from the current channel.")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int):
        """Delete messages (prefix: ?purge, slash: /purge)."""
        if amount < 1 or amount > 100:
            return await self._safe_reply(ctx, "❌ Please provide a number between 1 and 100.")
        if not isinstance(ctx.channel, discord.TextChannel):
            return await self._safe_reply(ctx, "❌ This command must be used in a server text channel.")
        if ctx.interaction and not ctx.interaction.response.is_done():
            try:
                await ctx.interaction.response.defer(ephemeral=True)
            except Exception:
                pass
        try:
            deleted = await ctx.channel.purge(limit=amount + (0 if ctx.interaction else 1))
            count = len(deleted)
            
            # For slash commands (interactions), ephemeral already auto-hides
            # For prefix commands, send regular message and delete after 5s
            if ctx.interaction:
                await self._safe_reply(ctx, f"🧹 Deleted {count} messages.\n-# This message will auto-dismiss")
            else:
                msg = await ctx.send(f"🧹 Deleted {count} messages.\n-# Note: This message will be deleted in 5 seconds")
                await msg.delete(delay=5)
        except discord.Forbidden:
            await self._safe_reply(ctx, "❌ I lack permission to manage messages here.")
        except Exception as e:
            await self._safe_reply(ctx, f"❌ Failed to purge messages: {e}")

    @commands.hybrid_command(name="kick", description="Kick a member from the server.")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if ctx.guild is None:
            return await self._safe_reply(ctx, "❌ This command can only be used in a server.")
        if member == ctx.author:
            return await self._safe_reply(ctx, "❌ You cannot kick yourself!")
        if isinstance(member, discord.Member) and isinstance(ctx.author, discord.Member) and ctx.guild is not None:
            if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                return await self._safe_reply(ctx, "❌ Target has an equal or higher role.")
        try:
            await member.kick(reason=reason)
            await self._safe_reply(ctx, f"👢 Kicked {member.mention} | Reason: {reason}")
        except discord.Forbidden:
            await self._safe_reply(ctx, "❌ I don't have permission to kick that member.")
        except Exception as e:
            await self._safe_reply(ctx, f"❌ Error: {e}")

    @commands.hybrid_command(name="ban", description="Ban a member from the server.")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if ctx.guild is None:
            return await self._safe_reply(ctx, "❌ This command can only be used in a server.")
        if member == ctx.author:
            return await self._safe_reply(ctx, "❌ You cannot ban yourself!")
        if isinstance(member, discord.Member) and isinstance(ctx.author, discord.Member) and ctx.guild is not None:
            if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                return await self._safe_reply(ctx, "❌ Target has an equal or higher role.")
        try:
            await member.ban(reason=reason)
            await self._safe_reply(ctx, f"🔨 Banned {member.mention} | Reason: {reason}")
        except discord.Forbidden:
            await self._safe_reply(ctx, "❌ I don't have permission to ban that member.")
        except Exception as e:
            await self._safe_reply(ctx, f"❌ Error: {e}")

    @commands.hybrid_command(name="unban", description="Unban a previously banned user (use their ID).")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user_id: int):
        if ctx.guild is None:
            return await self._safe_reply(ctx, "❌ This command can only be used in a server.")
        try:
            user = await self.bot.fetch_user(user_id)
        except discord.NotFound:
            return await self._safe_reply(ctx, "❌ User not found.")

        try:
            # discord.py 2.x: guild.fetch_ban for a single user
            await ctx.guild.fetch_ban(user)
        except discord.NotFound:
            return await self._safe_reply(ctx, "❌ That user is not banned.")

        try:
            await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author}")
            await self._safe_reply(ctx, f"✅ Unbanned {user.mention}")
        except discord.Forbidden:
            await self._safe_reply(ctx, "❌ I don't have permission to unban that user.")
        except Exception as e:
            await self._safe_reply(ctx, f"❌ Error: {e}")

    # -------- Advanced Moderation Commands --------
    
    @commands.hybrid_command(name="softban", help="Kick a user and delete their messages")
    @app_commands.describe(user="The user to softban", reason="Reason for the softban")
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def softban(self, ctx: commands.Context, user: discord.Member, *, reason: str = "No reason provided"):
        """Ban and immediately unban a user to delete their recent messages"""
        if ctx.guild is None:
            return await ctx.send("❌ This command can only be used in a server.")
        
        if user == ctx.author:
            return await ctx.send("❌ You cannot softban yourself.")
        
        if isinstance(ctx.author, discord.Member) and ctx.guild is not None:
            if user.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                return await ctx.send("❌ You can't softban someone with an equal or higher role.")
        
        try:
            # Ban then immediately unban
            await user.ban(reason=f"[SOFTBAN] {reason}", delete_message_days=1)
            await ctx.guild.unban(user, reason=f"Softban by {ctx.author}")
            
            # Log the action
            embed = discord.Embed(
                title="🪓 Softbanned",
                description=f"{user.mention} has been softbanned (messages deleted, user can rejoin).",
                color=discord.Color.orange()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Softbanned by {ctx.author}")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to softban that user.")
        except Exception as e:
            await ctx.send(f"❌ Failed to softban: {str(e)}")

    @commands.hybrid_command(name="clean", help="Delete bot messages and command invocations")
    @app_commands.describe(count="Number of messages to check (default 100)")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def clean(self, ctx: commands.Context, count: int = 100):
        """Delete bot messages and command invocations from the channel"""
        if count < 1 or count > 1000:
            return await ctx.send("❌ Count must be between 1 and 1000.")
        
        if not isinstance(ctx.channel, discord.TextChannel):
            return await ctx.send("❌ This command can only be used in text channels.")
        
        def is_bot_message(msg):
            return msg.author.bot or msg.content.startswith(('/', '!', '?'))
        
        try:
            deleted = await ctx.channel.purge(limit=count, check=is_bot_message)
            
            embed = discord.Embed(
                title="🧹 Cleaned Messages",
                description=f"Deleted {len(deleted)} bot/command messages from the last {count} messages.",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Cleaned by {ctx.author}")
            
            # Send confirmation and delete it after 5 seconds
            msg = await ctx.send(embed=embed)
            await msg.delete(delay=5)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete messages.")
        except Exception as e:
            await ctx.send(f"❌ Failed to clean messages: {str(e)}")

    @commands.hybrid_command(name="role", help="Toggle a role for a user")
    @app_commands.describe(user="Member to toggle role for", role_name="Name of the role to toggle")
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def role(self, ctx: commands.Context, user: discord.Member, *, role_name: str):
        """Add or remove a role from a user"""
        assert ctx.guild is not None
        role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), ctx.guild.roles)
        
        if not role:
            return await ctx.send(f"❌ Role '{role_name}' not found.")
        
        try:
            if role in user.roles:
                await user.remove_roles(role, reason=f"Role toggle by {ctx.author}")
                
                embed = discord.Embed(
                    title="➖ Role Removed",
                    description=f"Removed {role.mention} from {user.mention}.",
                    color=discord.Color.orange()
                )
            else:
                await user.add_roles(role, reason=f"Role toggle by {ctx.author}")
                
                embed = discord.Embed(
                    title="➕ Role Added",
                    description=f"Added {role.mention} to {user.mention}.",
                    color=discord.Color.green()
                )
            
            embed.set_footer(text=f"Action by {ctx.author}")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to modify that role.")
        except Exception as e:
            await ctx.send(f"❌ Failed to toggle role: {str(e)}")

    @commands.hybrid_command(name="timeout", help="Timeout a member for a specified duration")
    @app_commands.describe(
        member="Member to timeout",
        duration="Duration (e.g., 10m, 2h, 1d)",
        reason="Reason for the timeout"
    )
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @commands.guild_only()
    async def timeout(self, ctx: commands.Context, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
        """Timeout a member for a specified duration"""
        if member == ctx.author:
            return await ctx.send("❌ You cannot timeout yourself!")
        
        if isinstance(ctx.author, discord.Member) and ctx.guild is not None:
            if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                return await ctx.send("❌ Target has an equal or higher role.")
        
        # Parse duration
        time_regex = re.compile(r"(\d+)([smhd])")
        matches = time_regex.findall(duration.lower())
        
        if not matches:
            return await ctx.send("❌ Invalid duration format. Use: 10m, 2h, 1d, etc.")
        
        total_seconds = 0
        for value, unit in matches:
            value = int(value)
            if unit == 's':
                total_seconds += value
            elif unit == 'm':
                total_seconds += value * 60
            elif unit == 'h':
                total_seconds += value * 3600
            elif unit == 'd':
                total_seconds += value * 86400
        
        if total_seconds < 60:
            return await ctx.send("❌ Timeout duration must be at least 1 minute.")
        
        if total_seconds > 2419200:  # 28 days
            return await ctx.send("❌ Timeout duration cannot exceed 28 days.")
        
        try:
            timeout_until = datetime.now(timezone.utc) + timedelta(seconds=total_seconds)
            await member.timeout(timeout_until, reason=reason)
            
            embed = discord.Embed(
                title="⏱️ Member Timed Out",
                description=f"{member.mention} has been timed out.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Duration", value=duration, inline=True)
            embed.add_field(name="Until", value=f"<t:{int(timeout_until.timestamp())}:F>", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Timed out by {ctx.author}")
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to timeout that member.")
        except Exception as e:
            await ctx.send(f"❌ Failed to timeout: {str(e)}")

    @commands.hybrid_command(name="untimeout", help="Remove timeout from a member")
    @app_commands.describe(member="Member to remove timeout from", reason="Reason for removing timeout")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @commands.guild_only()
    async def untimeout(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Remove timeout from a member"""
        if not member.timed_out_until:
            return await ctx.send(f"❌ {member.mention} is not timed out.")
        
        try:
            await member.timeout(None, reason=reason)
            
            embed = discord.Embed(
                title="✅ Timeout Removed",
                description=f"Removed timeout from {member.mention}.",
                color=discord.Color.green()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Removed by {ctx.author}")
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to remove timeout from that member.")
        except Exception as e:
            await ctx.send(f"❌ Failed to remove timeout: {str(e)}")

    @commands.hybrid_command(name="slowmode", help="Set slowmode delay for the current channel")
    @app_commands.describe(seconds="Slowmode delay in seconds (0 to disable, max 21600)")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def slowmode(self, ctx: commands.Context, seconds: int):
        """Set slowmode delay for the current channel"""
        if not isinstance(ctx.channel, discord.TextChannel):
            return await ctx.send("❌ This command can only be used in text channels.")
        
        if seconds < 0 or seconds > 21600:
            return await ctx.send("❌ Slowmode delay must be between 0 and 21600 seconds (6 hours).")
        
        try:
            await ctx.channel.edit(slowmode_delay=seconds, reason=f"Slowmode set by {ctx.author}")
            
            if seconds == 0:
                embed = discord.Embed(
                    title="✅ Slowmode Disabled",
                    description=f"Slowmode has been disabled in {ctx.channel.mention}.",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="⏱️ Slowmode Enabled",
                    description=f"Slowmode set to **{seconds}** seconds in {ctx.channel.mention}.",
                    color=discord.Color.blue()
                )
            
            embed.set_footer(text=f"Set by {ctx.author}")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to modify this channel.")
        except Exception as e:
            await ctx.send(f"❌ Failed to set slowmode: {str(e)}")

    @commands.hybrid_command(name="lock", help="Lock a channel to prevent members from sending messages")
    @app_commands.describe(channel="Channel to lock (optional, defaults to current)")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def lock(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Lock a channel to prevent members from sending messages"""
        channel = channel or ctx.channel
        assert ctx.guild is not None
        
        if not isinstance(channel, discord.TextChannel):
            return await ctx.send("❌ This command can only be used on text channels.")
        
        try:
            overwrites = channel.overwrites_for(ctx.guild.default_role)
            overwrites.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites, reason=f"Channel locked by {ctx.author}")
            
            self.lockdown_channels.add(channel.id)
            
            embed = discord.Embed(
                title="🔒 Channel Locked",
                description=f"{channel.mention} has been locked. Members cannot send messages.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Locked by {ctx.author}")
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to modify this channel.")
        except Exception as e:
            await ctx.send(f"❌ Failed to lock channel: {str(e)}")

    @commands.hybrid_command(name="unlock", help="Unlock a previously locked channel")
    @app_commands.describe(channel="Channel to unlock (optional, defaults to current)")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def unlock(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Unlock a channel to allow members to send messages"""
        channel = channel or ctx.channel
        assert ctx.guild is not None
        
        if not isinstance(channel, discord.TextChannel):
            return await ctx.send("❌ This command can only be used on text channels.")
        
        try:
            overwrites = channel.overwrites_for(ctx.guild.default_role)
            overwrites.send_messages = None  # Reset to default
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites, reason=f"Channel unlocked by {ctx.author}")
            
            self.lockdown_channels.discard(channel.id)
            
            embed = discord.Embed(
                title="🔓 Channel Unlocked",
                description=f"{channel.mention} has been unlocked. Members can send messages again.",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Unlocked by {ctx.author}")
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to modify this channel.")
        except Exception as e:
            await ctx.send(f"❌ Failed to unlock channel: {str(e)}")

    @commands.hybrid_command(name="lockdown", help="Lock all channels in the server")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def lockdown(self, ctx: commands.Context):
        """Lock all channels in the server"""
        assert ctx.guild is not None
        
        await ctx.send("🔒 Initiating server lockdown...")
        
        locked_count = 0
        failed_count = 0
        
        for channel in ctx.guild.text_channels:
            try:
                overwrites = channel.overwrites_for(ctx.guild.default_role)
                overwrites.send_messages = False
                await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites, reason=f"Server lockdown by {ctx.author}")
                self.lockdown_channels.add(channel.id)
                locked_count += 1
            except:
                failed_count += 1
        
        embed = discord.Embed(
            title="🔒 Server Lockdown Complete",
            description=f"Successfully locked **{locked_count}** channels.",
            color=discord.Color.red()
        )
        
        if failed_count > 0:
            embed.add_field(name="⚠️ Failed", value=f"{failed_count} channels could not be locked.", inline=False)
        
        embed.set_footer(text=f"Lockdown initiated by {ctx.author}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="unlockdown", help="Unlock all previously locked channels")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def unlockdown(self, ctx: commands.Context):
        """Unlock all previously locked channels"""
        assert ctx.guild is not None
        
        if not self.lockdown_channels:
            return await ctx.send("❌ No channels are currently locked down.")
        
        await ctx.send("🔓 Removing server lockdown...")
        
        unlocked_count = 0
        failed_count = 0
        
        for channel_id in list(self.lockdown_channels):
            channel = ctx.guild.get_channel(channel_id)
            if channel and isinstance(channel, discord.TextChannel):
                try:
                    overwrites = channel.overwrites_for(ctx.guild.default_role)
                    overwrites.send_messages = None
                    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites, reason=f"Lockdown removed by {ctx.author}")
                    self.lockdown_channels.discard(channel_id)
                    unlocked_count += 1
                except:
                    failed_count += 1
        
        embed = discord.Embed(
            title="🔓 Server Lockdown Removed",
            description=f"Successfully unlocked **{unlocked_count}** channels.",
            color=discord.Color.green()
        )
        
        if failed_count > 0:
            embed.add_field(name="⚠️ Failed", value=f"{failed_count} channels could not be unlocked.", inline=False)
        
        embed.set_footer(text=f"Lockdown removed by {ctx.author}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="nuke", help="Clone and delete a channel to clear all messages")
    @app_commands.describe(channel="Channel to nuke (optional, defaults to current)")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def nuke(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Nuke a channel by cloning and deleting it"""
        channel = channel or ctx.channel
        
        if not isinstance(channel, discord.TextChannel):
            return await ctx.send("❌ This command can only be used on text channels.")
        
        try:
            # Create confirmation message
            embed = discord.Embed(
                title="⚠️ Confirm Channel Nuke",
                description=f"Are you sure you want to nuke {channel.mention}?\n\n**This will:**\n• Delete all messages\n• Reset channel position\n• Preserve permissions and settings",
                color=discord.Color.red()
            )
            embed.set_footer(text="React with ✅ to confirm or ❌ to cancel")
            
            confirm_msg = await ctx.send(embed=embed)
            await confirm_msg.add_reaction("✅")
            await confirm_msg.add_reaction("❌")
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
            
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
                
                if str(reaction.emoji) == "❌":
                    await confirm_msg.delete()
                    return await ctx.send("❌ Channel nuke cancelled.")
                
                # Proceed with nuke
                position = channel.position
                new_channel = await channel.clone(reason=f"Channel nuked by {ctx.author}")
                await channel.delete(reason=f"Channel nuked by {ctx.author}")
                await new_channel.edit(position=position)
                
                embed = discord.Embed(
                    title="💥 Channel Nuked",
                    description="This channel has been completely reset!",
                    color=discord.Color.green()
                )
                embed.set_image(url="https://media.giphy.com/media/HhTXt43pk1I1W/giphy.gif")
                embed.set_footer(text=f"Nuked by {ctx.author}")
                
                await new_channel.send(embed=embed)
                
            except asyncio.TimeoutError:
                await confirm_msg.delete()
                await ctx.send("❌ Channel nuke timed out.")
                
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to manage this channel.")
        except Exception as e:
            await ctx.send(f"❌ Failed to nuke channel: {str(e)}")

    @commands.hybrid_command(name="massban", help="Ban multiple users by ID")
    @app_commands.describe(user_ids="User IDs to ban (space-separated)", reason="Reason for the bans")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def massban(self, ctx: commands.Context, user_ids: str, *, reason: str = "Mass ban"):
        """Ban multiple users by their IDs"""
        assert ctx.guild is not None
        
        # Parse user IDs
        ids = [int(id.strip()) for id in user_ids.split() if id.strip().isdigit()]
        
        if not ids:
            return await ctx.send("❌ No valid user IDs provided.")
        
        if len(ids) > 50:
            return await ctx.send("❌ Cannot ban more than 50 users at once.")
        
        await ctx.send(f"⚖️ Processing ban for {len(ids)} user(s)...")
        
        banned = []
        failed = []
        
        for user_id in ids:
            try:
                user = await self.bot.fetch_user(user_id)
                await ctx.guild.ban(user, reason=f"[MASSBAN] {reason}")
                banned.append(f"{user} ({user_id})")
            except Exception as e:
                failed.append(f"{user_id}: {str(e)}")
        
        embed = discord.Embed(
            title="🔨 Mass Ban Complete",
            color=discord.Color.red()
        )
        
        if banned:
            embed.add_field(
                name=f"✅ Banned ({len(banned)})",
                value="\n".join(banned[:10]) + (f"\n...and {len(banned) - 10} more" if len(banned) > 10 else ""),
                inline=False
            )
        
        if failed:
            embed.add_field(
                name=f"❌ Failed ({len(failed)})",
                value="\n".join(failed[:10]) + (f"\n...and {len(failed) - 10} more" if len(failed) > 10 else ""),
                inline=False
            )
        
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Mass ban by {ctx.author}")
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="nickname", help="Change a member's nickname")
    @app_commands.describe(member="Member to change nickname", nickname="New nickname (leave empty to reset)")
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def nickname(self, ctx: commands.Context, member: discord.Member, *, nickname: Optional[str] = None):
        """Change a member's nickname"""
        if isinstance(ctx.author, discord.Member) and ctx.guild is not None:
            if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                return await ctx.send("❌ Target has an equal or higher role.")
        
        old_nick = member.display_name
        
        try:
            await member.edit(nick=nickname, reason=f"Nickname changed by {ctx.author}")
            
            embed = discord.Embed(
                title="✏️ Nickname Changed",
                color=discord.Color.blue()
            )
            embed.add_field(name="Member", value=member.mention, inline=True)
            embed.add_field(name="Old Nickname", value=old_nick, inline=True)
            embed.add_field(name="New Nickname", value=nickname or member.name, inline=True)
            embed.set_footer(text=f"Changed by {ctx.author}")
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to change that member's nickname.")
        except Exception as e:
            await ctx.send(f"❌ Failed to change nickname: {str(e)}")

    # -------- Server Information Commands --------
    
    @commands.hybrid_command(name="userinfo", help="Get detailed information about a user")
    @app_commands.describe(user="User to get information about (defaults to yourself)")
    @commands.guild_only()
    async def userinfo(self, ctx: commands.Context, user: Optional[Union[discord.Member, discord.User]] = None):
        """Get comprehensive user information"""
        user = user or ctx.author
        assert ctx.guild is not None
        
        embed = discord.Embed(
            title=f"User Information: {user}",
            color=user.color if isinstance(user, discord.Member) and user.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        # Basic Info
        embed.add_field(name="👤 Username", value=str(user), inline=True)
        embed.add_field(name="🆔 User ID", value=f"`{user.id}`", inline=True)
        embed.add_field(name="🤖 Bot", value="Yes" if user.bot else "No", inline=True)
        
        # Account Creation
        embed.add_field(
            name="📅 Account Created",
            value=f"<t:{int(user.created_at.timestamp())}:F>\n(<t:{int(user.created_at.timestamp())}:R>)",
            inline=False
        )
        
        # Member-specific info
        if isinstance(user, discord.Member):
            # Join date
            if user.joined_at:
                embed.add_field(
                    name="📥 Joined Server",
                    value=f"<t:{int(user.joined_at.timestamp())}:F>\n(<t:{int(user.joined_at.timestamp())}:R>)",
                    inline=False
                )
            
            # Roles
            if len(user.roles) > 1:
                roles = [role.mention for role in reversed(user.roles[1:])][:20]
                embed.add_field(
                    name=f"🎭 Roles [{len(user.roles) - 1}]",
                    value=" ".join(roles) if roles else "None",
                    inline=False
                )
            
            # Status
            status_emoji = {
                discord.Status.online: "🟢 Online",
                discord.Status.idle: "🟡 Idle",
                discord.Status.dnd: "🔴 Do Not Disturb",
                discord.Status.offline: "⚫ Offline"
            }
            embed.add_field(name="📊 Status", value=status_emoji.get(user.status, "Unknown"), inline=True)
            
            # Highest role
            if user.top_role != ctx.guild.default_role:
                embed.add_field(name="⬆️ Highest Role", value=user.top_role.mention, inline=True)
            
            # Boost status
            if user.premium_since:
                embed.add_field(
                    name="💎 Boosting Since",
                    value=f"<t:{int(user.premium_since.timestamp())}:R>",
                    inline=True
                )
            
            # Timeout status
            if user.timed_out_until:
                embed.add_field(
                    name="⏱️ Timed Out Until",
                    value=f"<t:{int(user.timed_out_until.timestamp())}:F>",
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="avatar", help="Get a user's avatar")
    @app_commands.describe(user="User to get avatar from (defaults to yourself)")
    async def avatar(self, ctx: commands.Context, user: Optional[Union[discord.Member, discord.User]] = None):
        """Get a user's avatar in high resolution"""
        user = user or ctx.author
        
        embed = discord.Embed(
            title=f"{user}'s Avatar",
            color=discord.Color.blue()
        )
        
        if user.avatar:
            embed.set_image(url=user.avatar.url)
            embed.add_field(name="🔗 Links", value=f"[PNG]({user.avatar.replace(format='png', size=1024).url}) | [JPG]({user.avatar.replace(format='jpg', size=1024).url}) | [WEBP]({user.avatar.replace(format='webp', size=1024).url})", inline=False)
        else:
            embed.description = "This user has no custom avatar."
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="roleinfo", help="Get information about a role")
    @app_commands.describe(role="Role to get information about")
    @commands.guild_only()
    async def roleinfo(self, ctx: commands.Context, *, role: discord.Role):
        """Get comprehensive role information"""
        assert ctx.guild is not None
        
        embed = discord.Embed(
            title=f"Role Information: {role.name}",
            color=role.color if role.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        # Basic info
        embed.add_field(name="🎭 Name", value=role.name, inline=True)
        embed.add_field(name="🆔 ID", value=f"`{role.id}`", inline=True)
        embed.add_field(name="🎨 Color", value=str(role.color), inline=True)
        
        # Position
        embed.add_field(name="📊 Position", value=f"{role.position}/{len(ctx.guild.roles)}", inline=True)
        
        # Members
        member_count = len(role.members)
        embed.add_field(name="👥 Members", value=str(member_count), inline=True)
        
        # Created
        embed.add_field(
            name="📅 Created",
            value=f"<t:{int(role.created_at.timestamp())}:F>\n(<t:{int(role.created_at.timestamp())}:R>)",
            inline=False
        )
        
        # Properties
        properties = []
        if role.hoist:
            properties.append("📌 Hoisted")
        if role.mentionable:
            properties.append("💬 Mentionable")
        if role.managed:
            properties.append("🤖 Managed")
        if role.is_premium_subscriber():
            properties.append("💎 Booster Role")
        
        if properties:
            embed.add_field(name="⚙️ Properties", value="\n".join(properties), inline=False)
        
        # Key permissions
        key_perms = []
        if role.permissions.administrator:
            key_perms.append("👑 Administrator")
        if role.permissions.manage_guild:
            key_perms.append("⚙️ Manage Server")
        if role.permissions.manage_roles:
            key_perms.append("🎭 Manage Roles")
        if role.permissions.manage_channels:
            key_perms.append("📝 Manage Channels")
        if role.permissions.kick_members:
            key_perms.append("👢 Kick Members")
        if role.permissions.ban_members:
            key_perms.append("🔨 Ban Members")
        if role.permissions.moderate_members:
            key_perms.append("⏱️ Timeout Members")
        
        if key_perms:
            embed.add_field(name="🔑 Key Permissions", value="\n".join(key_perms), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="serverinfo", help="Get detailed server information")
    @app_commands.describe()
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context):
        """Get comprehensive server information"""
        guild = ctx.guild
        assert guild is not None  # Since we have @commands.guild_only()
        
        # Calculate server stats
        total_members = guild.member_count or len(guild.members)
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        bot_count = sum(1 for member in guild.members if member.bot)
        human_count = len([m for m in guild.members if not m.bot])
        
        # Channel counts
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # Role count
        role_count = len(guild.roles) - 1  # Exclude @everyone
        
        # Boost info
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count
        
        # Server features
        features = []
        if guild.features:
            feature_names = {
                'COMMUNITY': 'Community Server',
                'PARTNERED': 'Discord Partner',
                'VERIFIED': 'Verified',
                'VANITY_URL': 'Custom Invite URL',
                'ANIMATED_ICON': 'Animated Icon',
                'BANNER': 'Server Banner',
                'WELCOME_SCREEN_ENABLED': 'Welcome Screen',
                'MEMBER_VERIFICATION_GATE_ENABLED': 'Membership Screening',
                'PREVIEW_ENABLED': 'Server Preview'
            }
            features = [feature_names.get(f, f.replace('_', ' ').title()) for f in guild.features[:10]]
        
        embed = discord.Embed(
            title=f"{guild.name} Server Information",
            color=discord.Color.blue(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(
            name="Member Stats",
            value=f"**Total:** {total_members:,}\n**Online:** {online_members:,}\n**Humans:** {human_count:,}\n**Bots:** {bot_count:,}",
            inline=True
        )
        
        embed.add_field(
            name="Channels",
            value=f"**Text:** {text_channels}\n**Voice:** {voice_channels}\n**Categories:** {categories}\n**Total:** {text_channels + voice_channels}",
            inline=True
        )
        
        embed.add_field(
            name="Roles & Boosts",
            value=f"**Roles:** {role_count}\n**Boost Level:** {boost_level}/3\n**Boosts:** {boost_count}",
            inline=True
        )
        
        owner = guild.owner or (guild.get_member(guild.owner_id) if guild.owner_id else None)
        owner_mention = owner.mention if isinstance(owner, (discord.Member, discord.User)) else "Unknown"
        owner_display = str(owner) if owner else "Unknown"
        embed.add_field(
            name="👑 Server Owner",
            value=f"{owner_mention}\n{owner_display}",
            inline=True
        )
        
        embed.add_field(
            name="Created",
            value=f"<t:{int(guild.created_at.timestamp())}:F>\n(<t:{int(guild.created_at.timestamp())}:R>)",
            inline=True
        )
        
        embed.add_field(
            name="Server ID",
            value=f"`{guild.id}`",
            inline=True
        )
        
        if features:
            embed.add_field(
                name="Features",
                value="\n".join(f"• {feature}" for feature in features[:5]),
                inline=False
            )
        
        if guild.description:
            embed.add_field(
                name="Description",
                value=guild.description,
                inline=False
            )
        
        await ctx.send(embed=embed)

    # -------- Warnings Commands --------

    @commands.hybrid_group(
        name="warnings",
        usage="warnings ((add <user> [reason]|remove <user> <case_id> [reason])|(list|clear <user>)|view <case_id>)",
        description="Manage user warnings - add, remove, list, or view warning details",
    )
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def warnings(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
            
    @warnings.command("add")
    @commands.guild_only()
    async def warnings_add(
        self, ctx: commands.Context, user: discord.User, *, reason: str | None = None
    ):
        assert ctx.guild is not None
        if reason is None:
            reason = "No reason specified."

        if not SAM_AVAILABLE:
            await ctx.send("⚠️ Warning system unavailable. SAM module not loaded.")
            return
            
        try:
            svc = await self.get_warn_service()
            if svc:
                await svc.issue_warning(user.id, ctx.guild.id, ctx.author.id, reason)
                # TODO: Embed
                await ctx.send(f"⚠️ Warned {user.mention} for `{reason}`")
            else:
                await ctx.send("⚠️ Warning system unavailable.")
        finally:
            await self._close_db_session()

    @warnings.command("remove")
    @commands.guild_only()
    async def warnings_remove(
        self,
        ctx: commands.Context,
        user: discord.User,
        case_id: int,
        *,
        reason: str | None = None,
    ):
        assert ctx.guild is not None
        if reason is None:
            reason = "No reason specified."
            
        if not SAM_AVAILABLE:
            await ctx.send("⚠️ Warning system unavailable. SAM module not loaded.")
            return
            
        try:
            svc = await self.get_warn_service()
            if svc:
                await svc.recall_warning(case_id, ctx.guild.id, ctx.author.id, reason)
                # TODO: Embed
                await ctx.send(
                    f"✅ Removed warning from {user.mention} with reason `{reason}`"
                )
            else:
                await ctx.send("⚠️ Warning system unavailable.")
        except ValueError as e:
            # TODO: Embed
            await ctx.send(f"❌ Cannot remove this warning: {e}")
        finally:
            await self._close_db_session()

    @warnings.command("list")
    @commands.guild_only()
    async def warnings_list(self, ctx: commands.Context, user: discord.User):
        assert ctx.guild is not None
        
        if not SAM_AVAILABLE:
            await ctx.send("⚠️ Warning system unavailable. SAM module not loaded.")
            return
            
        try:
            svc = await self.get_warn_service()
            if svc:
                warnings = await svc.get_warnings_for_user(user.id, ctx.guild.id)
                
                if not warnings:
                    await ctx.send(f"✅ {user.mention} has no warnings.")
                    return
                    
                # TODO: Implement proper pagination and embed
                warning_list = "\n".join(map(str, warnings))
                
                embed = discord.Embed(
                    title=f"⚠️ Warnings for {user}",
                    description=warning_list if warning_list else "No warnings found.",
                    color=discord.Color.orange()
                )
                embed.set_footer(text=f"User ID: {user.id}")
                await ctx.send(embed=embed)
            else:
                await ctx.send("⚠️ Warning system unavailable.")
        finally:
            await self._close_db_session()

    @warnings.command("clear")
    @commands.guild_only()
    async def warnings_clear(
        self, ctx: commands.Context, user: discord.User, *, reason: str | None = None
    ):
        assert ctx.guild is not None
        if reason is None:
            reason = "No reason specified."
            
        if not SAM_AVAILABLE:
            await ctx.send("⚠️ Warning system unavailable. SAM module not loaded.")
            return
            
        try:
            svc = await self.get_warn_service()
            if svc:
                warnings = await svc.get_warnings_for_user(user.id, ctx.guild.id)
                if not warnings:
                    await ctx.send(f"✅ {user.mention} has no warnings to clear.")
                    return
                    
                await svc.clear_warnings_for_user(
                    user.id,
                    ctx.guild.id,
                    ctx.author.id,
                    reason,
                )
                # TODO: Embed
                await ctx.send(f"🧹 Cleared all warnings for {user.mention} with note `{reason}`")
            else:
                await ctx.send("⚠️ Warning system unavailable.")
        finally:
            await self._close_db_session()

    @warnings.command("view")
    @commands.guild_only()
    async def warnings_view(self, ctx: commands.Context, case_id: int):
        assert ctx.guild is not None
        
        if not SAM_AVAILABLE:
            await ctx.send("⚠️ Warning system unavailable. SAM module not loaded.")
            return
            
        try:
            svc = await self.get_warn_service()
            if svc:
                warning = await svc.get_warning(case_id, ctx.guild.id)
                
                # Create a nice embed for the warning
                embed = discord.Embed(
                    title=f"⚠️ Warning #{case_id}",
                    color=discord.Color.orange()
                )
                
                embed.add_field(name="User", value=f"<@{warning.user_id}>", inline=True)
                embed.add_field(name="Moderator", value=f"<@{warning.moderator_id}>", inline=True)
                embed.add_field(name="Date", value=f"<t:{int(warning.created_at.timestamp())}>", inline=True)
                embed.add_field(name="Reason", value=warning.reason, inline=False)
                
                if warning.revoked:
                    embed.add_field(name="Status", value="REVOKED", inline=True)
                    embed.add_field(name="Revoked by", value=f"<@{warning.revoke_moderator_id}>", inline=True)
                    if warning.revoked_at:
                        embed.add_field(name="Revoked on", value=f"<t:{int(warning.revoked_at.timestamp())}>", inline=True)
                    embed.add_field(name="Revoke reason", value=warning.revoke_reason or "No reason provided", inline=False)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("⚠️ Warning system unavailable.")
        except ValueError as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Cannot view this warning: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        finally:
            await self._close_db_session()

    # -------- Shared Error Handler --------
    
    @purge.error
    @kick.error
    @ban.error
    @unban.error
    async def _command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await self._safe_reply(ctx, "❌ You lack permission for that command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await self._safe_reply(ctx, "⚠️ I am missing required permissions.")
        elif isinstance(error, commands.BadArgument):
            await self._safe_reply(ctx, "⚠️ Invalid argument provided.")
        elif isinstance(error, commands.CommandInvokeError) and "Unknown interaction" in str(error):
            print(f"[ModCog] Interaction expired for {ctx.command}: {error}")
        else:
            await self._safe_reply(ctx, f"⚠️ An error occurred: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ModCog(bot))