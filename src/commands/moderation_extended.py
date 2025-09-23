"""
Comprehensive moderation commands for advanced server management
Designed to compete with YagPDB and other advanced moderation bots
"""

import discord
import asyncio
import json
import os
import re
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta
from ..utils.helpers import create_success_embed, create_error_embed, create_warning_embed, log_action
from typing import Optional, Union

class ModerationExtended(commands.Cog):
    """Comprehensive moderation commands for advanced server management"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.muted_users = {}  # Store muted users with timestamps
        self.lockdown_channels = set()  # Store locked down channels

    # ==================== SERVER INFORMATION COMMANDS ====================
    
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
            title=f"📊 {guild.name} Server Information",
            color=discord.Color.blue(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(
            name="📈 Member Stats",
            value=f"**Total:** {total_members:,}\n**Online:** {online_members:,}\n**Humans:** {human_count:,}\n**Bots:** {bot_count:,}",
            inline=True
        )
        
        embed.add_field(
            name="💬 Channels",
            value=f"**Text:** {text_channels}\n**Voice:** {voice_channels}\n**Categories:** {categories}\n**Total:** {text_channels + voice_channels}",
            inline=True
        )
        
        embed.add_field(
            name="🎭 Roles & Boosts",
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
            name="📅 Created",
            value=f"<t:{int(guild.created_at.timestamp())}:F>\n(<t:{int(guild.created_at.timestamp())}:R>)",
            inline=True
        )
        
        embed.add_field(
            name="🆔 Server ID",
            value=f"`{guild.id}`",
            inline=True
        )
        
        if features:
            embed.add_field(
                name="✨ Features",
                value="\n".join(f"• {feature}" for feature in features[:5]),
                inline=False
            )
        
        if guild.description:
            embed.add_field(
                name="📝 Description",
                value=guild.description,
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="userinfo", help="Get detailed user information")
    @app_commands.describe(user="The user to get information about")
    @commands.guild_only()
    async def userinfo(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        """Get comprehensive user information"""
        assert ctx.guild is not None  # Since we have @commands.guild_only()
        
        if user is None:
            user = ctx.author  # type: ignore
        
        assert user is not None  # Should always be true in guild context
        
        # User status and activity
        status_emoji = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡",
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫"
        }
        
        # Calculate join position
        sorted_members = sorted(ctx.guild.members, key=lambda m: m.joined_at or datetime.min.replace(tzinfo=timezone.utc))
        join_position = sorted_members.index(user) + 1
        
        embed = discord.Embed(
            title=f"👤 {user.display_name}",
            color=user.color if user.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Basic info
        embed.add_field(
            name="📊 Basic Info",
            value=f"**Username:** {user}\n**Nickname:** {user.nick or 'None'}\n**ID:** `{user.id}`\n**Bot:** {'Yes' if user.bot else 'No'}",
            inline=True
        )
        
        # Status and activity
        status_text = f"{status_emoji.get(user.status, '❓')} {str(user.status).title()}"
        if user.activity:
            if user.activity.type == discord.ActivityType.playing:
                status_text += f"\n🎮 Playing **{user.activity.name}**"
            elif user.activity.type == discord.ActivityType.listening:
                status_text += f"\n🎵 Listening to **{user.activity.name}**"
            elif user.activity.type == discord.ActivityType.watching:
                status_text += f"\n📺 Watching **{user.activity.name}**"
            elif user.activity.type == discord.ActivityType.custom:
                status_text += f"\n💭 {user.activity.name or 'Custom Status'}"
        
        embed.add_field(
            name="💡 Status",
            value=status_text,
            inline=True
        )
        
        # Roles (top 10)
        roles = [role.mention for role in user.roles[1:]]  # Exclude @everyone
        if roles:
            roles_text = ", ".join(roles[:10])
            if len(roles) > 10:
                roles_text += f" (+{len(roles) - 10} more)"
        else:
            roles_text = "No roles"
        
        embed.add_field(
            name=f"🎭 Roles ({len(roles)})",
            value=roles_text,
            inline=False
        )
        
        # Dates
        embed.add_field(
            name="📅 Account Created",
            value=f"<t:{int(user.created_at.timestamp())}:F>\n(<t:{int(user.created_at.timestamp())}:R>)",
            inline=True
        )
        
        if user.joined_at:
            embed.add_field(
                name="📥 Joined Server",
                value=f"<t:{int(user.joined_at.timestamp())}:F>\n(<t:{int(user.joined_at.timestamp())}:R>)\n**Position:** #{join_position:,}",
                inline=True
            )
        
        # Permissions (if user has significant perms)
        key_perms = []
        if user.guild_permissions.administrator:
            key_perms.append("Administrator")
        else:
            perm_checks = [
                ("Manage Server", user.guild_permissions.manage_guild),
                ("Manage Channels", user.guild_permissions.manage_channels),
                ("Manage Roles", user.guild_permissions.manage_roles),
                ("Manage Messages", user.guild_permissions.manage_messages),
                ("Kick Members", user.guild_permissions.kick_members),
                ("Ban Members", user.guild_permissions.ban_members),
                ("Moderate Members", user.guild_permissions.moderate_members)
            ]
            key_perms = [name for name, has_perm in perm_checks if has_perm]
        
        if key_perms:
            embed.add_field(
                name="🔐 Key Permissions",
                value="\n".join(f"• {perm}" for perm in key_perms[:7]),
                inline=True
            )
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="roleinfo", help="Get information about a specific role")
    @app_commands.describe(role="The role to get information about")
    @commands.guild_only()
    async def roleinfo(self, ctx: commands.Context, *, role: discord.Role):
        """Get detailed role information"""
        # Count members with this role
        member_count = len(role.members)
        
        # Get role permissions
        perms = role.permissions
        key_perms = []
        if perms.administrator:
            key_perms.append("Administrator")
        else:
            perm_checks = [
                ("Manage Server", perms.manage_guild),
                ("Manage Channels", perms.manage_channels),
                ("Manage Roles", perms.manage_roles),
                ("Manage Messages", perms.manage_messages),
                ("Kick Members", perms.kick_members),
                ("Ban Members", perms.ban_members),
                ("Moderate Members", perms.moderate_members),
                ("Mention Everyone", perms.mention_everyone),
                ("Send TTS Messages", perms.send_tts_messages),
                ("Use External Emojis", perms.use_external_emojis)
            ]
            key_perms = [name for name, has_perm in perm_checks if has_perm]
        
        embed = discord.Embed(
            title=f"🎭 Role Information",
            color=role.color if role.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        embed.add_field(
            name="📊 Basic Info",
            value=f"**Name:** {role.name}\n**ID:** `{role.id}`\n**Color:** {str(role.color).upper()}\n**Position:** {role.position}",
            inline=True
        )
        
        embed.add_field(
            name="👥 Members",
            value=f"**Count:** {member_count:,}\n**Mentionable:** {'Yes' if role.mentionable else 'No'}\n**Hoisted:** {'Yes' if role.hoist else 'No'}",
            inline=True
        )
        
        embed.add_field(
            name="📅 Created",
            value=f"<t:{int(role.created_at.timestamp())}:F>\n(<t:{int(role.created_at.timestamp())}:R>)",
            inline=True
        )
        
        if key_perms:
            embed.add_field(
                name="🔐 Key Permissions",
                value="\n".join(f"• {perm}" for perm in key_perms[:10]),
                inline=False
            )
        
        # Show some members with this role (max 10)
        if member_count > 0:
            member_list = [m.mention for m in role.members[:10]]
            members_text = ", ".join(member_list)
            if member_count > 10:
                members_text += f" (+{member_count - 10} more)"
            
            embed.add_field(
                name="👤 Members (Sample)",
                value=members_text,
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="channelinfo", help="Get information about a channel")
    @app_commands.describe(channel="The channel to get information about")
    @commands.guild_only()
    async def channelinfo(self, ctx: commands.Context, channel: Optional[Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel]] = None):
        """Get detailed channel information"""
        assert ctx.guild is not None
        if channel is None:
            if isinstance(ctx.channel, (discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel)):
                channel = ctx.channel
            elif isinstance(ctx.channel, discord.Thread) and isinstance(ctx.channel.parent, (discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel)):
                channel = ctx.channel.parent
            else:
                await ctx.send(embed=create_error_embed("Unsupported Channel", "This command must be used in a guild text/voice/category channel or a thread within one."), ephemeral=True)
                return
        
        embed = discord.Embed(
            title=f"📺 Channel Information",
            color=discord.Color.blue(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        # Basic info for all channel types
        embed.add_field(
            name="📊 Basic Info",
            value=f"**Name:** {channel.name}\n**ID:** `{channel.id}`\n**Type:** {str(channel.type).title()}\n**Position:** {channel.position}",
            inline=True
        )
        
        embed.add_field(
            name="📅 Created",
            value=f"<t:{int(channel.created_at.timestamp())}:F>\n(<t:{int(channel.created_at.timestamp())}:R>)",
            inline=True
        )
        
        if hasattr(channel, 'category') and channel.category:
            embed.add_field(
                name="📁 Category",
                value=channel.category.name,
                inline=True
            )
        
        # Text channel specific info
        if isinstance(channel, discord.TextChannel):
            embed.add_field(
                name="💬 Text Channel Info",
                value=f"**Topic:** {channel.topic or 'None'}\n**Slowmode:** {channel.slowmode_delay}s\n**NSFW:** {'Yes' if channel.nsfw else 'No'}",
                inline=False
            )
        
        # Voice channel specific info
        elif isinstance(channel, discord.VoiceChannel):
            embed.add_field(
                name="🔊 Voice Channel Info",
                value=f"**Bitrate:** {channel.bitrate // 1000}kbps\n**User Limit:** {channel.user_limit or 'Unlimited'}\n**Connected:** {len(channel.members)}",
                inline=False
            )
            
            if channel.members:
                members = [m.display_name for m in channel.members[:10]]
                members_text = ", ".join(members)
                if len(channel.members) > 10:
                    members_text += f" (+{len(channel.members) - 10} more)"
                
                embed.add_field(
                    name="👥 Connected Users",
                    value=members_text,
                    inline=False
                )
        
        # Category specific info
        elif isinstance(channel, discord.CategoryChannel):
            text_count = len([c for c in channel.channels if isinstance(c, discord.TextChannel)])
            voice_count = len([c for c in channel.channels if isinstance(c, discord.VoiceChannel)])
            
            embed.add_field(
                name="📁 Category Info",
                value=f"**Text Channels:** {text_count}\n**Voice Channels:** {voice_count}\n**Total:** {len(channel.channels)}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    # ==================== ADVANCED MODERATION COMMANDS ====================
    
    @commands.hybrid_command(name="lockdown", help="Lock down a channel (prevent non-mods from speaking)")
    @app_commands.describe(
        channel="Channel to lock down (current channel if not specified)",
        reason="Reason for the lockdown"
    )
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def lockdown(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None, *, reason: str = "No reason provided"):
        """Lock down a channel to prevent normal users from speaking"""
        assert ctx.guild is not None
        if channel is None:
            if isinstance(ctx.channel, discord.TextChannel):
                channel = ctx.channel
            elif isinstance(ctx.channel, discord.Thread) and isinstance(ctx.channel.parent, discord.TextChannel):
                channel = ctx.channel.parent
            else:
                await ctx.send(embed=create_error_embed("Unsupported Channel", "Please specify a text channel or run this in a text channel/thread."), ephemeral=True)
                return
        
        # Store original permissions for @everyone
        everyone = ctx.guild.default_role
        overwrites = channel.overwrites_for(everyone)
        
        if overwrites.send_messages is False:
            await ctx.send(embed=create_warning_embed("Already Locked", f"{channel.mention} is already locked down."), ephemeral=True)
            return
        
        try:
            overwrites.send_messages = False
            await channel.set_permissions(everyone, overwrite=overwrites, reason=f"Lockdown by {ctx.author}: {reason}")
            
            self.lockdown_channels.add(channel.id)
            
            embed = create_success_embed(
                "🔒 Channel Locked Down",
                f"{channel.mention} has been locked down.\n**Reason:** {reason}"
            )
            embed.set_footer(text=f"Locked by {ctx.author}")
            
            await ctx.send(embed=embed)
            await log_action("LOCKDOWN", ctx.author.id, f"Channel: {channel.name} | Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Error", "I don't have permission to modify channel permissions."), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=create_error_embed("Error", f"Failed to lock down channel: {str(e)}"), ephemeral=True)

    @commands.hybrid_command(name="unlock", help="Unlock a previously locked channel")
    @app_commands.describe(
        channel="Channel to unlock (current channel if not specified)",
        reason="Reason for unlocking"
    )
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def unlock(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None, *, reason: str = "No reason provided"):
        """Unlock a previously locked channel"""
        assert ctx.guild is not None
        if channel is None:
            if isinstance(ctx.channel, discord.TextChannel):
                channel = ctx.channel
            elif isinstance(ctx.channel, discord.Thread) and isinstance(ctx.channel.parent, discord.TextChannel):
                channel = ctx.channel.parent
            else:
                await ctx.send(embed=create_error_embed("Unsupported Channel", "Please specify a text channel or run this in a text channel/thread."), ephemeral=True)
                return
        
        everyone = ctx.guild.default_role
        overwrites = channel.overwrites_for(everyone)
        
        if overwrites.send_messages is not False:
            await ctx.send(embed=create_warning_embed("Not Locked", f"{channel.mention} is not currently locked down."), ephemeral=True)
            return
        
        try:
            overwrites.send_messages = None  # Reset to default
            await channel.set_permissions(everyone, overwrite=overwrites, reason=f"Unlock by {ctx.author}: {reason}")
            
            self.lockdown_channels.discard(channel.id)
            
            embed = create_success_embed(
                "🔓 Channel Unlocked",
                f"{channel.mention} has been unlocked.\n**Reason:** {reason}"
            )
            embed.set_footer(text=f"Unlocked by {ctx.author}")
            
            await ctx.send(embed=embed)
            await log_action("UNLOCK", ctx.author.id, f"Channel: {channel.name} | Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Error", "I don't have permission to modify channel permissions."), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=create_error_embed("Error", f"Failed to unlock channel: {str(e)}"), ephemeral=True)

    @commands.hybrid_command(name="nuke", help="Delete and recreate a channel (clears all messages)")
    @app_commands.describe(
        channel="Channel to nuke (current channel if not specified)",
        reason="Reason for nuking the channel"
    )
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def nuke(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None, *, reason: str = "No reason provided"):
        """Delete and recreate a channel (nuclear option)"""
        assert ctx.guild is not None
        if channel is None:
            if isinstance(ctx.channel, discord.TextChannel):
                channel = ctx.channel
            elif isinstance(ctx.channel, discord.Thread) and isinstance(ctx.channel.parent, discord.TextChannel):
                channel = ctx.channel.parent
            else:
                await ctx.send(embed=create_error_embed("Unsupported Channel", "Please specify a text channel or run this in a text channel/thread."), ephemeral=True)
                return
        
        # Store channel information
        channel_name = channel.name
        channel_topic = channel.topic
        channel_category = channel.category
        channel_position = channel.position
        channel_overwrites = channel.overwrites
        channel_slowmode = channel.slowmode_delay
        channel_nsfw = channel.nsfw
        
        try:
            # Create confirmation embed
            embed = discord.Embed(
                title="Nuclear Option Confirmation",
                description=f"This will **permanently delete** all messages in {channel.mention} and recreate it.\n\n**This action cannot be undone!**",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text="React with ✓ to confirm or ✗ to cancel (30s timeout)")
            
            msg = await ctx.send(embed=embed)
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                if str(reaction.emoji) == "❌":
                    await msg.edit(embed=create_warning_embed("Cancelled", "Channel nuke cancelled."))
                    return
                
                # Proceed with nuke
                new_channel = await channel.clone(reason=f"Nuked by {ctx.author}: {reason}")
                await channel.delete(reason=f"Nuked by {ctx.author}: {reason}")
                
                # Restore properties
                edit_kwargs = {
                    "position": channel_position,
                    "slowmode_delay": channel_slowmode,
                    "nsfw": channel_nsfw,
                }
                if channel_topic is not None:
                    edit_kwargs["topic"] = channel_topic
                await new_channel.edit(**edit_kwargs)
                
                # Send confirmation in new channel
                embed = discord.Embed(
                    title="💥 Channel Nuked",
                    description=f"Channel has been nuked and recreated.\n**Reason:** {reason}",
                    color=discord.Color.orange()
                )
                embed.set_footer(text=f"Nuked by {ctx.author}")
                await new_channel.send(embed=embed)
                
                await log_action("NUKE", ctx.author.id, f"Channel: {channel_name} | Reason: {reason}")
                
            except asyncio.TimeoutError:
                await msg.edit(embed=create_warning_embed("Timeout", "Channel nuke cancelled due to timeout."))
                
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Error", "I don't have permission to manage channels."), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=create_error_embed("Error", f"Failed to nuke channel: {str(e)}"), ephemeral=True)

    @commands.hybrid_command(name="massban", help="Ban multiple users by ID (Admin only)")
    @app_commands.describe(
        user_ids="Space-separated list of user IDs to ban",
        reason="Reason for mass ban",
        delete_days="Days of messages to delete (0-7)"
    )
    @commands.has_permissions(ban_members=True)
    async def massban(self, ctx: commands.Context, user_ids: str, delete_days: int = 1, *, reason: str = "Mass ban"):
        """Ban multiple users by their IDs"""
        assert ctx.guild is not None
        if delete_days < 0 or delete_days > 7:
            await ctx.send(embed=create_error_embed("Invalid Days", "Delete days must be between 0 and 7."), ephemeral=True)
            return
        
        # Parse user IDs
        ids = user_ids.split()
        if len(ids) > 20:
            await ctx.send(embed=create_error_embed("Too Many Users", "Maximum 20 users can be banned at once."), ephemeral=True)
            return
        
        banned_count = 0
        failed_bans = []
        
        embed = create_warning_embed(
            "⚠️ Mass Ban in Progress",
            f"Processing ban for {len(ids)} users..."
        )
        progress_msg = await ctx.send(embed=embed)
        
        for user_id in ids:
            try:
                user_id = int(user_id)
                
                # Check if user is already banned
                try:
                    banned_entries = [ban_entry async for ban_entry in ctx.guild.bans()]
                    if any(ban_entry.user.id == user_id for ban_entry in banned_entries):
                        failed_bans.append(f"{user_id} (already banned)")
                        continue
                except:
                    pass
                
                # Attempt to ban
                await ctx.guild.ban(
                    discord.Object(id=user_id),
                    reason=f"Mass ban by {ctx.author}: {reason}",
                    delete_message_days=delete_days
                )
                banned_count += 1
                await log_action("MASS_BAN", user_id, f"Reason: {reason}")
                
            except ValueError:
                failed_bans.append(f"{user_id} (invalid ID)")
            except discord.NotFound:
                failed_bans.append(f"{user_id} (user not found)")
            except discord.Forbidden:
                failed_bans.append(f"{user_id} (permission denied)")
            except Exception as e:
                failed_bans.append(f"{user_id} (error: {str(e)[:20]})")
        
        # Final result
        result_embed = discord.Embed(
            title="Mass Ban Results",
            color=discord.Color.green() if banned_count > 0 else discord.Color.red()
        )
        
        result_embed.add_field(
            name="Successfully Banned",
            value=str(banned_count),
            inline=True
        )
        
        result_embed.add_field(
            name="Failed",
            value=str(len(failed_bans)),
            inline=True
        )
        
        result_embed.add_field(
            name="Reason",
            value=reason,
            inline=True
        )
        
        if failed_bans:
            failures_text = "\n".join(failed_bans[:10])
            if len(failed_bans) > 10:
                failures_text += f"\n... and {len(failed_bans) - 10} more"
            
            result_embed.add_field(
                name="❌ Failed Bans",
                value=f"```\n{failures_text}\n```",
                inline=False
            )
        
        await progress_msg.edit(embed=result_embed)

    @commands.hybrid_command(name="listbans", help="List all banned users in the server")
    @commands.has_permissions(ban_members=True)
    async def listbans(self, ctx: commands.Context):
        """List all banned users in the server"""
        assert ctx.guild is not None
        try:
            ban_list = []
            async for ban_entry in ctx.guild.bans():
                ban_list.append(ban_entry)
            
            if not ban_list:
                await ctx.send(embed=create_warning_embed("No Bans", "This server has no banned users."))
                return
            
            embeds = []
            items_per_page = 10
            
            for i in range(0, len(ban_list), items_per_page):
                embed = discord.Embed(
                    title=f"🚫 Server Ban List ({len(ban_list)} total)",
                    color=discord.Color.red(),
                    timestamp=datetime.now(tz=timezone.utc)
                )
                
                page_bans = ban_list[i:i + items_per_page]
                ban_text = []
                
                for ban_entry in page_bans:
                    user = ban_entry.user
                    reason = ban_entry.reason or "No reason provided"
                    ban_text.append(f"**{user}** (ID: {user.id})\n└ Reason: {reason[:50]}{'...' if len(reason) > 50 else ''}")
                
                embed.description = "\n\n".join(ban_text)
                embed.set_footer(text=f"Page {len(embeds) + 1}/{(len(ban_list) + items_per_page - 1) // items_per_page}")
                embeds.append(embed)
            
            # Send first page
            if len(embeds) == 1:
                await ctx.send(embed=embeds[0])
            else:
                await ctx.send(embed=embeds[0])
                # Note: In a full implementation, you'd add pagination with buttons
                
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Error", "I don't have permission to view ban list."), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=create_error_embed("Error", f"Failed to retrieve ban list: {str(e)}"), ephemeral=True)

    # ==================== ROLE MANAGEMENT COMMANDS ====================
    
    @commands.hybrid_command(name="addrole", help="Add a role to a user")
    @app_commands.describe(
        user="User to add role to",
        role="Role to add",
        reason="Reason for adding the role"
    )
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx: commands.Context, user: discord.Member, role: discord.Role, *, reason: str = "No reason provided"):
        """Add a role to a user"""
        assert ctx.guild is not None
        assert isinstance(ctx.author, discord.Member)
        assert ctx.guild.me is not None
        # Permission checks
        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_error_embed("Permission Error", "You cannot assign a role higher than or equal to your highest role."), ephemeral=True)
            return
        
        if role >= ctx.guild.me.top_role:
            await ctx.send(embed=create_error_embed("Permission Error", "I cannot assign a role higher than or equal to my highest role."), ephemeral=True)
            return
        
        if role in user.roles:
            await ctx.send(embed=create_warning_embed("Already Has Role", f"{user.mention} already has the {role.mention} role."), ephemeral=True)
            return
        
        try:
            await user.add_roles(role, reason=f"Added by {ctx.author}: {reason}")
            
            embed = create_success_embed(
                "✅ Role Added",
                f"Added {role.mention} to {user.mention}"
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Added by {ctx.author}")
            
            await ctx.send(embed=embed)
            await log_action("ROLE_ADD", user.id, f"Role: {role.name} | Added by: {ctx.author} | Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Error", "I don't have permission to manage roles."), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=create_error_embed("Error", f"Failed to add role: {str(e)}"), ephemeral=True)

    @commands.hybrid_command(name="removerole", help="Remove a role from a user")
    @app_commands.describe(
        user="User to remove role from",
        role="Role to remove", 
        reason="Reason for removing the role"
    )
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx: commands.Context, user: discord.Member, role: discord.Role, *, reason: str = "No reason provided"):
        """Remove a role from a user"""
        assert ctx.guild is not None
        assert isinstance(ctx.author, discord.Member)
        assert ctx.guild.me is not None
        # Permission checks
        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_error_embed("Permission Error", "You cannot remove a role higher than or equal to your highest role."), ephemeral=True)
            return
        
        if role >= ctx.guild.me.top_role:
            await ctx.send(embed=create_error_embed("Permission Error", "I cannot remove a role higher than or equal to my highest role."), ephemeral=True)
            return
        
        if role not in user.roles:
            await ctx.send(embed=create_warning_embed("Doesn't Have Role", f"{user.mention} doesn't have the {role.mention} role."), ephemeral=True)
            return
        
        try:
            await user.remove_roles(role, reason=f"Removed by {ctx.author}: {reason}")
            
            embed = create_success_embed(
                "✅ Role Removed", 
                f"Removed {role.mention} from {user.mention}"
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Removed by {ctx.author}")
            
            await ctx.send(embed=embed)
            await log_action("ROLE_REMOVE", user.id, f"Role: {role.name} | Removed by: {ctx.author} | Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Error", "I don't have permission to manage roles."), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=create_error_embed("Error", f"Failed to remove role: {str(e)}"), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationExtended(bot))
