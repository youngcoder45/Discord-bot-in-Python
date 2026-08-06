"""
Comprehensive moderation commands for server management
Merges functionality from moderation.py, moderation_extended.py, and sam warnings module.
"""

import discord  # type: ignore[import-not-found]
import asyncio
import sqlite3
from discord.ext import commands  # type: ignore[import-not-found]
from discord import app_commands  # type: ignore[import-not-found]
from datetime import datetime, timezone, timedelta
from typing import Optional, Union, Any, cast
from collections.abc import Awaitable, Callable
from utils.embeds import create_success_embed, create_error_embed, create_info_embed
from utils.helpers import log_action, safe_send, register_mod_action, discard_mod_action

# Bot owner ID for restricted commands
BOT_OWNER_ID = 955695820999639120

# SAM Module imports for warnings
try:
    from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore[import-not-found]
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
        self.lockdown_channels = set()  # Store locked down channels
        # SAM warnings are handled via the Warnings cog directly, not this cog

    # -------- Helpers --------

    async def _safe_reply(self, ctx: commands.Context, content: str | None = None, *, embed: discord.Embed | None = None, ephemeral: bool = True):
        """Unified reply for hybrid commands. Delegates to shared safe_send from helpers."""
        return await safe_send(ctx, content=content, embed=embed, ephemeral=ephemeral)

    # -------- Basic Moderation Commands --------
    
    @commands.hybrid_command(name="purge", description="Delete a number of messages from the current channel or thread.")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(self, ctx: commands.Context, amount: int):
        """Delete messages (prefix: ?purge, slash: /purge). Works in channels and threads!"""
        if amount < 1 or amount > 100:
            return await self._safe_reply(ctx, "❌ Please provide a number between 1 and 100.")

        if ctx.channel is None:
            return await self._safe_reply(ctx, "❌ This command must be used in a server channel.")

        # Allow text channels, threads, and voice/stage channel text chats (when supported by the API/library).
        if not isinstance(ctx.channel, discord.abc.Messageable):
            return await self._safe_reply(ctx, "❌ This channel doesn't support messages, so I can't purge here.")
        
        if ctx.interaction and not ctx.interaction.response.is_done():
            try:
                await ctx.interaction.response.defer(ephemeral=True)
            except Exception:
                pass
        try:
            # For prefix commands, include the invoking message in the fetch window.
            limit = amount + (0 if ctx.interaction else 1)

            purge_fn = getattr(ctx.channel, "purge", None)
            if callable(purge_fn):
                deleted = await purge_fn(limit=limit)  # type: ignore[misc]
                count = len(deleted)
            else:
                # Fallback for messageable channels that don't expose `.purge()`.
                # We implement a safe version using history + bulk delete when possible.
                import datetime

                now = discord.utils.utcnow()
                bulk_threshold = now - datetime.timedelta(days=14)

                fetched = [m async for m in ctx.channel.history(limit=limit)]  # type: ignore[attr-defined]
                if not ctx.interaction and getattr(ctx, "message", None) is not None:
                    fetched = [m for m in fetched if m.id != ctx.message.id]

                targets = fetched[:amount]
                bulk_candidates = [m for m in targets if m.created_at > bulk_threshold]
                old_messages = [m for m in targets if m.created_at <= bulk_threshold]

                count = 0

                delete_messages_fn = getattr(ctx.channel, "delete_messages", None)
                if callable(delete_messages_fn) and len(bulk_candidates) > 1:
                    try:
                        delete_messages = cast(Callable[[list[Any]], Awaitable[Any]], delete_messages_fn)
                        await delete_messages(bulk_candidates)
                        count += len(bulk_candidates)
                    except Exception:
                        # Fall back to individual deletes if bulk delete isn't supported.
                        for m in bulk_candidates:
                            try:
                                await m.delete()
                                count += 1
                            except Exception:
                                pass
                else:
                    for m in bulk_candidates:
                        try:
                            await m.delete()
                            count += 1
                        except Exception:
                            pass

                for m in old_messages:
                    try:
                        await m.delete()
                        count += 1
                    except Exception:
                        pass
            
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
    @commands.bot_has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        # PERM CHECK: Native Kick OR Permit
        has_native = ctx.author.guild_permissions.kick_members if isinstance(ctx.author, discord.Member) else False
        permits_cog: Any = self.bot.get_cog("PermitSystem")
        has_permit = False
        if permits_cog and hasattr(permits_cog, 'check_permit') and ctx.guild:
            has_permit = permits_cog.check_permit(ctx.author.id, ctx.guild.id, "kick_members")
        
        if not (has_native or has_permit):
             return await self._safe_reply(ctx, "❌ You do not have permission to kick members (Need native perms or 'kick_members' permit).")

        if ctx.guild is None:
            return await self._safe_reply(ctx, "❌ This command can only be used in a server.")
        if member == ctx.author:
            return await self._safe_reply(ctx, "❌ You cannot kick yourself!")
        if isinstance(member, discord.Member) and isinstance(ctx.author, discord.Member) and ctx.guild is not None:
            if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                return await self._safe_reply(ctx, "❌ Target has an equal or higher role.")
        try:
            # Register the actual invoker so the logging system attributes the
            # kick to the moderator instead of the bot (Discord audit logs show
            # the bot application for API-performed actions).
            register_mod_action(self.bot, ctx.guild.id, member.id, ctx.author.id, reason, "KICK")
            await member.kick(reason=reason)
            await self._safe_reply(ctx, f"👢 Kicked {member.mention} | Reason: {reason}")

        except discord.Forbidden:
            discard_mod_action(self.bot, ctx.guild.id, member.id, "KICK")
            await self._safe_reply(ctx, "❌ I don't have permission to kick that member.")
        except Exception as e:
            discard_mod_action(self.bot, ctx.guild.id, member.id, "KICK")
            await self._safe_reply(ctx, f"❌ Error: {e}")

    @commands.hybrid_command(name="ban", description="Ban a member from the server.")
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        # PERM CHECK: Native Ban OR Permit
        has_native = ctx.author.guild_permissions.ban_members if isinstance(ctx.author, discord.Member) else False
        permits_cog: Any = self.bot.get_cog("PermitSystem")
        has_permit = False
        if permits_cog and hasattr(permits_cog, 'check_permit') and ctx.guild:
            has_permit = permits_cog.check_permit(ctx.author.id, ctx.guild.id, "ban_members")
        
        if not (has_native or has_permit):
             return await self._safe_reply(ctx, "❌ You do not have permission to ban members (Need native perms or 'ban_members' permit).")

        if ctx.guild is None:
            return await self._safe_reply(ctx, "❌ This command can only be used in a server.")
        if member == ctx.author:
            return await self._safe_reply(ctx, "❌ You cannot ban yourself!")
        if isinstance(member, discord.Member) and isinstance(ctx.author, discord.Member) and ctx.guild is not None:
            if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                return await self._safe_reply(ctx, "❌ Target has an equal or higher role.")
        try:
            # Register the actual invoker so the logging system attributes the
            # ban to the moderator instead of the bot (Discord audit logs show
            # the bot application for API-performed bans).
            register_mod_action(self.bot, ctx.guild.id, member.id, ctx.author.id, reason, "BAN")
            await member.ban(reason=reason)
            await self._safe_reply(ctx, f"🔨 Banned {member.mention} | Reason: {reason}")

        except discord.Forbidden:
            discard_mod_action(self.bot, ctx.guild.id, member.id, "BAN")
            await self._safe_reply(ctx, "❌ I don't have permission to ban that member.")
        except Exception as e:
            discard_mod_action(self.bot, ctx.guild.id, member.id, "BAN")
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
            unban_reason = f"Unbanned by {ctx.author}"
            register_mod_action(self.bot, ctx.guild.id, user.id, ctx.author.id, unban_reason, "UNBAN")
            await ctx.guild.unban(user, reason=unban_reason)
            await self._safe_reply(ctx, f"✅ Unbanned {user.mention}")
        except discord.Forbidden:
            discard_mod_action(self.bot, ctx.guild.id, user.id, "UNBAN")
            await self._safe_reply(ctx, "❌ I don't have permission to unban that user.")
        except Exception as e:
            discard_mod_action(self.bot, ctx.guild.id, user.id, "UNBAN")
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
            ban_reason = f"[SOFTBAN] {reason}"
            unban_reason = f"Softban by {ctx.author}"
            register_mod_action(self.bot, ctx.guild.id, user.id, ctx.author.id, ban_reason, "BAN")
            await user.ban(reason=ban_reason, delete_message_days=1)
            register_mod_action(self.bot, ctx.guild.id, user.id, ctx.author.id, unban_reason, "UNBAN")
            await ctx.guild.unban(user, reason=unban_reason)
            
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
            discard_mod_action(self.bot, ctx.guild.id, user.id, "BAN")
            discard_mod_action(self.bot, ctx.guild.id, user.id, "UNBAN")
            await ctx.send("❌ I don't have permission to softban that user.")
        except Exception as e:
            discard_mod_action(self.bot, ctx.guild.id, user.id, "BAN")
            discard_mod_action(self.bot, ctx.guild.id, user.id, "UNBAN")
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
    @app_commands.describe(user="Member to toggle role for", role="The role to toggle")
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def role(self, ctx: commands.Context, user: discord.Member, *, role: discord.Role):
        """Add or remove a role from a user"""
        assert ctx.guild is not None
        
        try:
            if role in user.roles:
                register_mod_action(self.bot, ctx.guild.id, user.id, ctx.author.id, f"Role toggle by {ctx.author}", "ROLE_REMOVE")
                await user.remove_roles(role, reason=f"Role toggle by {ctx.author}")
                
                embed = discord.Embed(
                    title="Role Removed",
                    description=f"Removed {role.mention} from {user.mention}.",
                    color=discord.Color.orange()
                )
            else:
                register_mod_action(self.bot, ctx.guild.id, user.id, ctx.author.id, f"Role toggle by {ctx.author}", "ROLE_ADD")
                await user.add_roles(role, reason=f"Role toggle by {ctx.author}")
                
                embed = discord.Embed(
                    title="Role Added",
                    description=f"Added {role.mention} to {user.mention}.",
                    color=discord.Color.green()
                )
            
            embed.set_footer(text=f"Action by {ctx.author}")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            discard_mod_action(self.bot, ctx.guild.id, user.id, "ROLE_ADD")
            discard_mod_action(self.bot, ctx.guild.id, user.id, "ROLE_REMOVE")
            await ctx.send("❌ I don't have permission to modify that role.")
        except Exception as e:
            discard_mod_action(self.bot, ctx.guild.id, user.id, "ROLE_ADD")
            discard_mod_action(self.bot, ctx.guild.id, user.id, "ROLE_REMOVE")
            await ctx.send(f"❌ Failed to toggle role: {str(e)}")

    @commands.hybrid_command(name="addmod", help="Add the moderator role to a user")
    @app_commands.describe(user="Member to promote to moderator")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def addmod(self, ctx: commands.Context, user: discord.Member):
        """Promote a user to moderator"""
        if ctx.guild is None:
             return await ctx.send("This command can only be used in a server.")

        MOD_ROLE_ID = 1403059755001577543
        role = ctx.guild.get_role(MOD_ROLE_ID)
        
        if not role:
            await ctx.send(f"❌ Moderator role (ID: {MOD_ROLE_ID}) not found in this server.")
            return
            
        if role in user.roles:
            await ctx.send(f"⚠️ {user.mention} is already a moderator.")
            return
            
        try:
            register_mod_action(self.bot, ctx.guild.id, user.id, ctx.author.id, f"Promoted to Moderator by {ctx.author}", "ROLE_ADD")
            await user.add_roles(role, reason=f"Promoted to Moderator by {ctx.author}")
            
            embed = discord.Embed(
                title="Staff Addition",
                description=f"Successfully Made {user.mention} a Staff!",
                color=discord.Color.blue()
            )
            embed.add_field(name="Role Added", value=role.mention)
            embed.set_footer(text=f"Promoted by {ctx.author}")
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            discard_mod_action(self.bot, ctx.guild.id, user.id, "ROLE_ADD")
            await ctx.send("❌ I don't have permission to assign the moderator role.")
        except Exception as e:
            discard_mod_action(self.bot, ctx.guild.id, user.id, "ROLE_ADD")
            await ctx.send(f"❌ Failed to promote user: {str(e)}")

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
            register_mod_action(self.bot, ctx.guild.id, member.id, ctx.author.id, reason, "TIMEOUT_APPLIED")
            await member.timeout(timeout_until, reason=reason)
            
            embed = discord.Embed(
                title="Member Timed Out",
                description=f"{member.mention} has been timed out.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Duration", value=duration, inline=True)
            embed.add_field(name="Until", value=f"<t:{int(timeout_until.timestamp())}:F>", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Timed out by {ctx.author}")
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            discard_mod_action(self.bot, ctx.guild.id, member.id, "TIMEOUT_APPLIED")
            await ctx.send("❌ I don't have permission to timeout that member.")
        except Exception as e:
            discard_mod_action(self.bot, ctx.guild.id, member.id, "TIMEOUT_APPLIED")
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
            register_mod_action(self.bot, ctx.guild.id, member.id, ctx.author.id, reason, "TIMEOUT_REMOVED")
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
            discard_mod_action(self.bot, ctx.guild.id, member.id, "TIMEOUT_REMOVED")
            await ctx.send("❌ I don't have permission to remove timeout from that member.")
        except Exception as e:
            discard_mod_action(self.bot, ctx.guild.id, member.id, "TIMEOUT_REMOVED")
            await ctx.send(f"❌ Failed to remove timeout: {str(e)}")

    @commands.hybrid_command(name="slowmode", help="View or set slowmode delay for the current channel")
    @app_commands.describe(seconds="Slowmode delay in seconds (0 to disable, max 21600)")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def slowmode(self, ctx: commands.Context, seconds: Optional[int] = None):
        """View or set slowmode delay for the current channel"""
        if not isinstance(ctx.channel, (discord.TextChannel, discord.Thread)):
            return await ctx.send("❌ This command can only be used in text channels or threads.")

        if seconds is None:
            current_delay = getattr(ctx.channel, "slowmode_delay", 0) or 0
            embed = discord.Embed(
                title="⏱ Current Slowmode",
                description=(
                    f"Current slowmode in {ctx.channel.mention} is **{current_delay} seconds**.\n\n"
                    f"Use `?slowmode <a value here>` to set slowmode."
                ),
                color=discord.Color.blurple(),
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            return await ctx.send(embed=embed)

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
                    title="Slowmode Enabled",
                    description=f"Slowmode set to **{seconds}** seconds in {ctx.channel.mention}.",
                    color=discord.Color.blue()
                )
            
            embed.set_footer(text=f"Set by {ctx.author}")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to modify this channel.")
        except Exception as e:
            await ctx.send(f"❌ Failed to set slowmode: {str(e)}")

    @commands.hybrid_command(name="lock", help="Lock a channel or thread to prevent members from sending messages")
    @app_commands.describe(channel="Channel/thread to lock (optional, defaults to current)")
    @commands.has_permissions(manage_channels=True, manage_threads=True)
    @commands.bot_has_permissions(manage_channels=True, manage_threads=True)
    @commands.guild_only()
    async def lock(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Lock a channel or thread to prevent members from sending messages"""
        # Handle threads
        if isinstance(ctx.channel, discord.Thread):
            thread = ctx.channel
            try:
                # Lock the thread
                await thread.edit(locked=True)
                
                # Add lock emoji to thread name if not already present
                new_name = thread.name
                if not new_name.startswith("🔒"):
                    new_name = f"🔒 {thread.name}"
                    await thread.edit(name=new_name, reason=f"Thread locked by {ctx.author}")
                
                embed = discord.Embed(
                    title="🔒 Thread Locked",
                    description=f"Thread '{new_name}' has been locked. Members cannot send messages.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Locked by {ctx.author}")
                await ctx.send(embed=embed)
            except discord.Forbidden:
                await ctx.send("❌ I don't have permission to modify this thread.")
            except Exception as e:
                await ctx.send(f"❌ Failed to lock thread: {str(e)}")
            return
        
        # Handle text channels
        assert ctx.guild is not None

        target_channel = channel if isinstance(channel, discord.TextChannel) else (ctx.channel if isinstance(ctx.channel, discord.TextChannel) else None)
        if target_channel is None:
            return await ctx.send("❌ This command can only be used on text channels or threads.")
        
        try:
            overwrites = target_channel.overwrites_for(ctx.guild.default_role)
            overwrites.send_messages = False
            await target_channel.set_permissions(ctx.guild.default_role, overwrite=overwrites, reason=f"Channel locked by {ctx.author}")
            
            self.lockdown_channels.add(target_channel.id)
            
            embed = discord.Embed(
                title="🔒 Channel Locked",
                description=f"{target_channel.mention} has been locked. Members cannot send messages.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Locked by {ctx.author}")
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to modify this channel.")
        except Exception as e:
            await ctx.send(f"❌ Failed to lock channel: {str(e)}")

    @commands.hybrid_command(name="unlock", help="Unlock a previously locked channel or thread")
    @app_commands.describe(channel="Channel/thread to unlock (optional, defaults to current)")
    @commands.has_permissions(manage_channels=True, manage_threads=True)
    @commands.bot_has_permissions(manage_channels=True, manage_threads=True)
    @commands.guild_only()
    async def unlock(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Unlock a channel or thread to allow members to send messages"""
        # Handle threads
        if isinstance(ctx.channel, discord.Thread):
            thread = ctx.channel
            try:
                # Unlock the thread
                await thread.edit(locked=False)
                
                # Remove lock emoji from thread name if present
                new_name = thread.name
                if new_name.startswith("🔒"):
                    new_name = new_name[2:].lstrip()  # Remove emoji and extra space
                    await thread.edit(name=new_name, reason=f"Thread unlocked by {ctx.author}")
                
                embed = discord.Embed(
                    title="🔓 Thread Unlocked",
                    description=f"Thread '{new_name}' has been unlocked. Members can send messages again.",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Unlocked by {ctx.author}")
                await ctx.send(embed=embed)
            except discord.Forbidden:
                await ctx.send("❌ I don't have permission to modify this thread.")
            except Exception as e:
                await ctx.send(f"❌ Failed to unlock thread: {str(e)}")
            return
        
        # Handle text channels
        assert ctx.guild is not None

        target_channel = channel if isinstance(channel, discord.TextChannel) else (ctx.channel if isinstance(ctx.channel, discord.TextChannel) else None)
        if target_channel is None:
            return await ctx.send("❌ This command can only be used on text channels or threads.")
        
        try:
            overwrites = target_channel.overwrites_for(ctx.guild.default_role)
            overwrites.send_messages = None  # Reset to default
            await target_channel.set_permissions(ctx.guild.default_role, overwrite=overwrites, reason=f"Channel unlocked by {ctx.author}")
            
            self.lockdown_channels.discard(target_channel.id)
            
            embed = discord.Embed(
                title="🔓 Channel Unlocked",
                description=f"{target_channel.mention} has been unlocked. Members can send messages again.",
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

    @commands.hybrid_command(name="nuke", help="Clone and delete a channel to clear all messages (OWNER ONLY)")
    @app_commands.describe(channel="Channel to nuke (optional, defaults to current)")
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def nuke(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Nuke a channel by cloning and deleting it (Owner only)"""
        # Check if user is the bot owner
        if ctx.author.id != BOT_OWNER_ID:
            return await ctx.send("❌ This command can only be used by the bot owner.")
        
        # Ensure channel is a TextChannel: prefer provided channel, otherwise use ctx.channel if it's a TextChannel
        channel_to_nuke = channel if isinstance(channel, discord.TextChannel) else (ctx.channel if isinstance(ctx.channel, discord.TextChannel) else None)
        if channel_to_nuke is None:
            return await ctx.send("❌ This command can only be used on text channels.")
        
        try:
            # Create confirmation message
            embed = discord.Embed(
                title="⚠️ Confirm Channel Nuke",
                description=f"Are you sure you want to nuke {channel_to_nuke.mention}?\n\n**This will:**\n• Delete all messages\n• Reset channel position\n• Preserve permissions and settings",
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
                position = channel_to_nuke.position
                new_channel = await channel_to_nuke.clone(reason=f"Channel nuked by {ctx.author}")
                await channel_to_nuke.delete(reason=f"Channel nuked by {ctx.author}")
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

    @commands.hybrid_command(name="massban", help="Ban multiple users by ID (OWNER ONLY)")
    @app_commands.describe(user_ids="User IDs to ban (space-separated)", reason="Reason for the bans")
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def massban(self, ctx: commands.Context, user_ids: str, *, reason: str = "Mass ban"):
        """Ban multiple users by their IDs (Owner only)"""
        # Check if user is the bot owner
        if ctx.author.id != BOT_OWNER_ID:
            return await ctx.send("❌ This command can only be used by the bot owner.")
        
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
                ban_reason = f"[MASSBAN] {reason}"
                register_mod_action(self.bot, ctx.guild.id, user_id, ctx.author.id, ban_reason, "BAN")
                await ctx.guild.ban(user, reason=ban_reason)
                banned.append(f"{user} ({user_id})")
            except Exception as e:
                discard_mod_action(self.bot, ctx.guild.id, user_id, "BAN")
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
            register_mod_action(self.bot, ctx.guild.id, member.id, ctx.author.id, f"Nickname changed by {ctx.author}", "NICKNAME_UPDATE")
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
            discard_mod_action(self.bot, ctx.guild.id, member.id, "NICKNAME_UPDATE")
            await ctx.send("❌ I don't have permission to change that member's nickname.")
        except Exception as e:
            discard_mod_action(self.bot, ctx.guild.id, member.id, "NICKNAME_UPDATE")
            await ctx.send(f"❌ Failed to change nickname: {str(e)}")

    # -------- Server Information Commands --------
    
    @commands.hybrid_command(name="info", aliases=["userinfo"], help="Get detailed information about a user")
    @app_commands.describe(user="User to get information about (defaults to yourself)")
    @commands.guild_only()
    async def userinfo(self, ctx: commands.Context, user: Optional[Union[discord.Member, discord.User]] = None):
        """Get comprehensive user information"""
        target_user = user if user is not None else ctx.author
        assert ctx.guild is not None
        
        embed = discord.Embed(
            title=f"User Information: {target_user}",
            color=target_user.color if isinstance(target_user, discord.Member) and target_user.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        if target_user.avatar:
            embed.set_thumbnail(url=target_user.avatar.url)
        
        # Basic Info
        embed.add_field(name="Username", value=str(target_user), inline=True)
        embed.add_field(name="User ID", value=f"`{target_user.id}`", inline=True)
        embed.add_field(name="Bot", value="Yes" if target_user.bot else "No", inline=True)
        
        # Account Creation
        embed.add_field(
            name="Account Created",
            value=f"<t:{int(target_user.created_at.timestamp())}:F>\n(<t:{int(target_user.created_at.timestamp())}:R>)",
            inline=False
        )
        
        # Member-specific info
        if isinstance(target_user, discord.Member):
            # Join date
            if target_user.joined_at:
                embed.add_field(
                    name="Joined Server",
                    value=f"<t:{int(target_user.joined_at.timestamp())}:F>\n(<t:{int(target_user.joined_at.timestamp())}:R>)",
                    inline=False
                )
            
            # Roles
            if len(target_user.roles) > 1:
                roles = [role.mention for role in reversed(target_user.roles[1:])][:20]
                embed.add_field(
                    name=f"Roles [{len(target_user.roles) - 1}]",
                    value=" ".join(roles) if roles else "None",
                    inline=False
                )
            
            # Status
            status_emoji = {
                discord.Status.online: "Online",
                discord.Status.idle: "Idle",
                discord.Status.dnd: "Do Not Disturb",
                discord.Status.offline: "Offline"
            }
            embed.add_field(name="Status", value=status_emoji.get(target_user.status, "Unknown"), inline=True)
            
            # Highest role
            if target_user.top_role != ctx.guild.default_role:
                embed.add_field(name="⬆Highest Role", value=target_user.top_role.mention, inline=True)
            
            # Boost status
            if target_user.premium_since:
                embed.add_field(
                    name="Boosting Since",
                    value=f"<t:{int(target_user.premium_since.timestamp())}:R>",
                    inline=True
                )
            
            # Timeout status
            if target_user.timed_out_until:
                embed.add_field(
                    name="Timed Out Until",
                    value=f"<t:{int(target_user.timed_out_until.timestamp())}:F>",
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="avatar", help="Get a user's avatar")
    @app_commands.describe(user="User to get avatar from (defaults to yourself)")
    async def avatar(self, ctx: commands.Context, user: Optional[Union[discord.Member, discord.User]] = None):
        """Get a user's avatar in high resolution"""
        target_user = user if user is not None else ctx.author
        
        embed = discord.Embed(
            title=f"{target_user}'s Avatar",
            color=discord.Color.blue()
        )
        
        if target_user.avatar:
            embed.set_image(url=target_user.avatar.url)
            embed.add_field(name="Links", value=f"[PNG]({target_user.avatar.replace(format='png', size=1024).url}) | [JPG]({target_user.avatar.replace(format='jpg', size=1024).url}) | [WEBP]({target_user.avatar.replace(format='webp', size=1024).url})", inline=False)
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
        embed.add_field(name="Name", value=role.name, inline=True)
        embed.add_field(name="ID", value=f"`{role.id}`", inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        
        # Position
        embed.add_field(name="Position", value=f"{role.position}/{len(ctx.guild.roles)}", inline=True)
        
        # Members
        member_count = len(role.members)
        embed.add_field(name="Members", value=str(member_count), inline=True)
        
        # Created
        embed.add_field(
            name="Created",
            value=f"<t:{int(role.created_at.timestamp())}:F>\n(<t:{int(role.created_at.timestamp())}:R>)",
            inline=False
        )
        
        # Properties
        properties = []
        if role.hoist:
            properties.append("Hoisted")
        if role.mentionable:
            properties.append("Mentionable")
        if role.managed:
            properties.append("Managed")
        if role.is_premium_subscriber():
            properties.append("Booster Role")
        
        if properties:
            embed.add_field(name="⚙️ Properties", value="\n".join(properties), inline=False)
        
        # Key permissions
        key_perms = []
        if role.permissions.administrator:
            key_perms.append("Administrator")
        if role.permissions.manage_guild:
            key_perms.append("Manage Server")
        if role.permissions.manage_roles:
            key_perms.append("Manage Roles")
        if role.permissions.manage_channels:
            key_perms.append("Manage Channels")
        if role.permissions.kick_members:
            key_perms.append("Kick Members")
        if role.permissions.ban_members:
            key_perms.append("Ban Members")
        if role.permissions.moderate_members:
            key_perms.append("Timeout Members")
        
        if key_perms:
            embed.add_field(name="Key Permissions", value="\n".join(key_perms), inline=False)
        
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
        if owner is None:
            owner_mention = "Unknown"
            owner_display = "Unknown"
        else:
            owner_mention = owner.mention
            owner_display = str(owner)
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
    # Warnings system moved to SAM module (/warn, /unwarn, /warnings)
    # See: commands.modules.sam.features.warnings.cogs

    # -------- Verification Command --------

    @app_commands.command(name="verify", description="Verify a user by assigning a verification role")
    @app_commands.describe(user="The user to verify")
    async def verify(self, interaction: discord.Interaction, user: discord.User):
        """Verify a user by assigning a verification role."""
        # Check if invoker has the required admin/bypass role
        admin_bypass_role_id = 1403059755001577543
        
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "❌ You do not have permission to use this command.",
                ephemeral=True
            )
            return
        
        if not any(role.id == admin_bypass_role_id for role in interaction.user.roles) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You do not have permission to use this command.",
                ephemeral=True
            )
            return
        
        # Get target member
        if not isinstance(user, discord.Member):
            try:
                target_member = await interaction.guild.fetch_member(user.id)
            except discord.NotFound:
                await interaction.response.send_message(
                    f"❌ User {user.mention} is not a member of this server.",
                    ephemeral=True
                )
                return
        else:
            target_member = user
        
        # Create the verification view
        view = VerificationView(target_member, self.bot)
        
        embed = discord.Embed(
            title="Verification Panel",
            description=f"Select a verification type for {target_member.mention}:",
            color=0x5865F2
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

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


class VerificationView(discord.ui.View):
    """View for verification role selection and confirmation."""
    
    VERIFICATION_ROLES = {
        "stream_verify": {
            "label": "Stream Verify",
            "role_id": 1417578146407911455,
            "value": "stream_verify"
        },
        "voice_verification": {
            "label": "Voice Verification",
            "role_id": 1414651719995883560,
            "value": "voice_verification"
        },
        "embed_verification": {
            "label": "Embed Verification",
            "role_id": 1486406987091677315,
            "value": "embed_verification"
        },
        "join_vc_verification": {
            "label": "Join VC Verification",
            "role_id": 1345308261133455430,
            "value": "join_vc_verification"
        },
    }
    
    def __init__(self, target_member: discord.Member, bot: discord.Client):
        super().__init__(timeout=300)  # 5 minute timeout
        self.target_member = target_member
        self.bot = bot
        self.selected_verification = None
        
    @discord.ui.select(
        placeholder="Select a verification type...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Stream Verify", value="stream_verify"),
            discord.SelectOption(label="Voice Verification", value="voice_verification"),
            discord.SelectOption(label="Embed Verification", value="embed_verification"),
            discord.SelectOption(label="Join VC Verification", value="join_vc_verification"),
        ]
    )
    async def select_verification(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Handle verification type selection."""
        self.selected_verification = select.values[0]
        
        # Update the embed to show selection
        embed = discord.Embed(
            title="Verification Panel",
            description=f"Selected: **{self.VERIFICATION_ROLES[self.selected_verification]['label']}** for {self.target_member.mention}",
            color=0x5865F2
        )
        
        await interaction.response.defer()
        # After deferring, edits must go through edit_original_response
        # (response.edit_message would raise InteractionResponded).
        await interaction.edit_original_response(embed=embed, view=self)
    
    @discord.ui.button(label="Save", style=discord.ButtonStyle.green)
    async def save_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle saving the verification."""
        # Check if a verification type was selected
        if not self.selected_verification:
            await interaction.response.send_message(
                "❌ Please select a verification type before saving.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        role_id = self.VERIFICATION_ROLES[self.selected_verification]["role_id"]
        role = interaction.guild.get_role(role_id)
        
        if not role:
            await interaction.followup.send(
                f"❌ Verification role not found (ID: {role_id})",
                ephemeral=True
            )
            return
        
        # Check if user already has the role
        if role in self.target_member.roles:
            await interaction.followup.send(
                f"ℹ️ {self.target_member.mention} already possesses the **{role.name}** role.",
                ephemeral=True
            )
            return
        
        # Try to assign the role
        try:
            await self.target_member.add_roles(role, reason=f"Verification by {interaction.user}")
            
            # Update embed with confirmation
            embed = discord.Embed(
                title="✅ Verification Complete",
                description=f"Successfully assigned **{role.name}** to {self.target_member.mention}",
                color=0x00FF00
            )
            embed.add_field(name="Verification Type", value=self.VERIFICATION_ROLES[self.selected_verification]["label"], inline=False)
            embed.add_field(name="Verified By", value=interaction.user.mention, inline=False)
            embed.timestamp = datetime.now(timezone.utc)
            
            # Disable all components
            for item in self.children:
                item.disabled = True
            
            # The interaction was deferred above, so edits must use
            # edit_original_response (response.edit_message would raise
            # InteractionResponded after a defer).
            await interaction.edit_original_response(embed=embed, view=self)
            
        except discord.Forbidden:
            await interaction.followup.send(
                f"❌ I cannot assign the **{role.name}** role due to hierarchy restrictions.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ An error occurred while assigning the role: {str(e)}",
                ephemeral=True
            )
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle cancellation."""
        embed = discord.Embed(
            title="Verification Cancelled",
            description="The verification process has been cancelled.",
            color=0xFF0000
        )
        
        # Disable all components
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def on_timeout(self):
        """Handle view timeout."""
        # Disable all components
        for item in self.children:
            item.disabled = True


async def setup(bot: commands.Bot):
    await bot.add_cog(ModCog(bot))
