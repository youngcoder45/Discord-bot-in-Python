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

    # -------- Server Information Commands --------
    
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