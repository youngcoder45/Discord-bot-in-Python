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
from utils.helpers import create_success_embed, create_error_embed, create_warning_embed, log_action
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

    # ==================== ADDITIONAL MODERATION & MANAGEMENT (LIGHTWEIGHT) ====================
    # In-memory state (temporary). Replace with persistent storage for production durability.
    _guild_state: dict[int, dict] = {}

    def _state(self, guild_id: int):
        return self._guild_state.setdefault(guild_id, {
            'warnings': {},      # user_id -> list[{id, reason, time}]
            'notes': {},         # user_id -> list[{id, note, time, mod_id}]
            'cases': [],         # list of case dicts
            'case_counter': 0,
            'ignored': {'channels': set(), 'roles': set(), 'users': set()},
            'mod_roles': set(),
        })

    def _add_case(self, guild_id: int, user_id: int, mod_id: int, action: str, reason: str = "No reason provided", duration: str | None = None):
        s = self._state(guild_id)
        s['case_counter'] += 1
        case = {
            'id': s['case_counter'], 'user_id': user_id, 'mod_id': mod_id,
            'action': action, 'reason': reason, 'duration': duration,
            'timestamp': datetime.now(timezone.utc)
        }
        s['cases'].append(case)
        return case

    # ---- WARN / WARNINGS ----
    @commands.hybrid_command(name="warn", help="Warn a member (temporary in-memory store)")
    @app_commands.describe(user="Member to warn", reason="Reason for warning")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def warn(self, ctx: commands.Context, user: discord.Member, *, reason: str = "No reason provided"):
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        warns = st['warnings'].setdefault(user.id, [])
        warns.append({'id': len(warns)+1, 'reason': reason, 'time': datetime.now(timezone.utc)})
        case = self._add_case(ctx.guild.id, user.id, ctx.author.id, 'WARN', reason)
        embed = create_warning_embed("⚠️ User Warned", f"{user.mention} warned. Case #{case['id']}")
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="warnings", help="List warnings for a member")
    @app_commands.describe(user="Member to list warnings for")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def warnings(self, ctx: commands.Context, user: discord.Member):
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        warns = st['warnings'].get(user.id, [])
        if not warns:
            await ctx.send(f"✅ {user.mention} has no warnings.")
            return
        embed = discord.Embed(title=f"Warnings for {user.display_name}", color=discord.Color.orange())
        for w in warns[:15]:
            embed.add_field(name=f"#{w['id']}", value=f"{w['reason']} - <t:{int(w['time'].timestamp())}:R>", inline=False)
        if len(warns) > 15:
            embed.set_footer(text=f"Showing first 15 of {len(warns)} warnings")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="clearwarn", help="Clear all warnings for a user")
    @app_commands.describe(user="Member to clear")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def clearwarn(self, ctx: commands.Context, user: discord.Member):
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        if user.id not in st['warnings']:
            await ctx.send("User has no warnings.")
            return
        del st['warnings'][user.id]
        self._add_case(ctx.guild.id, user.id, ctx.author.id, 'CLEARWARN', 'All warnings cleared')
        await ctx.send(f"🧹 Cleared warnings for {user.mention}.")

    @commands.hybrid_command(name="delwarn", help="Delete a single warning by number")
    @app_commands.describe(user="Member", number="Warning number (see /warnings)")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def delwarn(self, ctx: commands.Context, user: discord.Member, number: int):
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        warns = st['warnings'].get(user.id)
        if not warns:
            await ctx.send("No warnings found.")
            return
        if number < 1 or number > len(warns):
            await ctx.send("Invalid warning number.")
            return
        removed = warns.pop(number-1)
        for idx, w in enumerate(warns, start=1):
            w['id'] = idx
        self._add_case(ctx.guild.id, user.id, ctx.author.id, 'DELWARN', f"Removed warn #{number}: {removed['reason']}")
        await ctx.send(f"🗑️ Removed warning #{number}.")

    # ---- NOTES ----
    @commands.hybrid_command(name="note", help="Add a staff note (in-memory)")
    @app_commands.describe(user="Member", note="Note text")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def note(self, ctx: commands.Context, user: discord.Member, *, note: str):
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        notes = st['notes'].setdefault(user.id, [])
        notes.append({'id': len(notes)+1, 'note': note, 'time': datetime.now(timezone.utc), 'mod': ctx.author.id})
        self._add_case(ctx.guild.id, user.id, ctx.author.id, 'NOTE', note)
        await ctx.send(f"📝 Added note for {user.mention}.")

    @commands.hybrid_command(name="notes", help="List notes for a member")
    @app_commands.describe(user="Member")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def notes(self, ctx: commands.Context, user: discord.Member):
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        notes = st['notes'].get(user.id, [])
        if not notes:
            await ctx.send("No notes for that user.")
            return
        embed = discord.Embed(title=f"Notes for {user.display_name}", color=discord.Color.gold())
        for n in notes[:15]:
            embed.add_field(name=f"#{n['id']}", value=f"{n['note']} - <t:{int(n['time'].timestamp())}:R>", inline=False)
        if len(notes) > 15:
            embed.set_footer(text=f"Showing first 15 of {len(notes)} notes")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="delnote", help="Delete a note by number")
    @app_commands.describe(user="Member", number="Note number")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def delnote(self, ctx: commands.Context, user: discord.Member, number: int):
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        notes = st['notes'].get(user.id)
        if not notes:
            await ctx.send("No notes for that user.")
            return
        if number < 1 or number > len(notes):
            await ctx.send("Invalid note number.")
            return
        notes.pop(number-1)
        for idx, n in enumerate(notes, start=1):
            n['id'] = idx
        self._add_case(ctx.guild.id, user.id, ctx.author.id, 'DELNOTE', f"Deleted note #{number}")
        await ctx.send("🗑️ Note deleted.")

    @commands.hybrid_command(name="clearnotes", help="Clear all notes for a member")
    @app_commands.describe(user="Member")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def clearnotes(self, ctx: commands.Context, user: discord.Member):
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        if user.id not in st['notes']:
            await ctx.send("No notes to clear.")
            return
        del st['notes'][user.id]
        self._add_case(ctx.guild.id, user.id, ctx.author.id, 'CLEARNOTES', 'All notes cleared')
        await ctx.send("🧹 Cleared all notes for that user.")

    # ---- CASE & REASON ----
    @commands.hybrid_command(name="case", help="Show a moderation case by ID")
    @app_commands.describe(number="Case number")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def case(self, ctx: commands.Context, number: int):
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        case = next((c for c in st['cases'] if c['id'] == number), None)
        if not case:
            await ctx.send("Case not found.")
            return
        embed = discord.Embed(title=f"Case #{case['id']}", color=discord.Color.blurple())
        embed.add_field(name="User ID", value=str(case['user_id']), inline=True)
        embed.add_field(name="Moderator ID", value=str(case['mod_id']), inline=True)
        embed.add_field(name="Action", value=case['action'], inline=True)
        embed.add_field(name="Reason", value=case['reason'], inline=False)
        if case.get('duration'):
            embed.add_field(name="Duration", value=case['duration'], inline=True)
        embed.set_footer(text=f"{case['timestamp'].isoformat()}Z")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="reason", help="Update a case reason")
    @app_commands.describe(number="Case number", new_reason="New reason text")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def reason(self, ctx: commands.Context, number: int, *, new_reason: str):
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        for c in st['cases']:
            if c['id'] == number:
                c['reason'] = new_reason
                await ctx.send("✅ Reason updated.")
                return
        await ctx.send("Case not found.")

    # ---- IGNORE SYSTEM ----
    @commands.hybrid_command(name="ignorechannel", help="Toggle ignoring a channel")
    @app_commands.describe(channel="Channel to toggle")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def ignorechannel(self, ctx: commands.Context, channel: discord.TextChannel):
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        channels = st['ignored']['channels']
        if channel.id in channels:
            channels.remove(channel.id)
            await ctx.send(f"✅ {channel.mention} unignored.")
        else:
            channels.add(channel.id)
            await ctx.send(f"🚫 {channel.mention} ignored.")

    @commands.hybrid_command(name="ignorerole", help="Toggle ignoring a role")
    @app_commands.describe(role="Role to toggle")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def ignorerole(self, ctx: commands.Context, role: discord.Role):
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        roles = st['ignored']['roles']
        if role.id in roles:
            roles.remove(role.id)
            await ctx.send(f"✅ {role.mention} unignored.")
        else:
            roles.add(role.id)
            await ctx.send(f"🚫 {role.mention} ignored.")

    @commands.hybrid_command(name="ignoreuser", help="Toggle ignoring a user")
    @app_commands.describe(user="User to toggle", reason="Optional reason")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def ignoreuser(self, ctx: commands.Context, user: discord.Member, *, reason: str = ""):
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        users = st['ignored']['users']
        if user.id in users:
            users.remove(user.id)
            await ctx.send(f"✅ {user.mention} unignored.")
        else:
            users.add(user.id)
            await ctx.send(f"🚫 {user.mention} ignored. {('Reason: '+reason) if reason else ''}")

    @commands.hybrid_command(name="ignored", help="List ignored channels/roles/users")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def ignored(self, ctx: commands.Context):
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        ch = ", ".join(f"<#{c}>" for c in st['ignored']['channels']) or "None"
        rl = ", ".join(f"<@&{r}>" for r in st['ignored']['roles']) or "None"
        us = ", ".join(f"<@{u}>" for u in st['ignored']['users']) or "None"
        embed = discord.Embed(title="Ignored Entities", color=discord.Color.dark_grey())
        embed.add_field(name="Channels", value=ch, inline=False)
        embed.add_field(name="Roles", value=rl, inline=False)
        embed.add_field(name="Users", value=us, inline=False)
        await ctx.send(embed=embed)

    # ---- SIMPLE PLACEHOLDER UTILS ----
    @commands.hybrid_command(name="announce", help="Send an announcement to a channel")
    @app_commands.describe(channel="Target channel", message="Announcement text")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def announce(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        embed = discord.Embed(title="📢 Announcement", description=message, color=discord.Color.gold())
        embed.set_footer(text=f"Sent by {ctx.author.display_name}")
        await channel.send(embed=embed)
        await ctx.send("✅ Announcement sent.")

    @commands.hybrid_command(name="nick", help="Change the bot nickname")
    @app_commands.describe(new_nick="New nickname")
    @commands.has_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def nick(self, ctx: commands.Context, *, new_nick: str):
        assert ctx.guild is not None and ctx.guild.me is not None
        try:
            await ctx.guild.me.edit(nick=new_nick[:32])
            await ctx.send(f"✅ Bot nickname changed to `{new_nick[:32]}`")
        except discord.Forbidden:
            await ctx.send("❌ Cannot change nickname.")

    @commands.hybrid_command(name="setnick", help="Change a member's nickname")
    @app_commands.describe(user="Member", new_nick="New nickname (omit to clear)")
    @commands.has_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def setnick(self, ctx: commands.Context, user: discord.Member, *, new_nick: str | None = None):
        try:
            await user.edit(nick=(new_nick[:32] if new_nick else None))
            await ctx.send("✅ Nickname updated." if new_nick else "✅ Nickname cleared.")
        except discord.Forbidden:
            await ctx.send("❌ Cannot change that nickname.")

    @commands.hybrid_command(name="rolecolor", help="Change a role color")
    @app_commands.describe(role="Role", hex_color="Hex color like #FFAA00")
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def rolecolor(self, ctx: commands.Context, role: discord.Role, hex_color: str):
        hex_color = hex_color.strip().lstrip('#')
        if len(hex_color) not in (3,6):
            await ctx.send("Provide a valid hex color.")
            return
        try:
            color = discord.Color(int(hex_color, 16))
            await role.edit(color=color)
            await ctx.send(f"🎨 Updated color for {role.mention}.")
        except Exception:
            await ctx.send("Failed to update color.")

    @commands.hybrid_command(name="rolename", help="Rename a role")
    @app_commands.describe(role="Role", new_name="New name")
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def rolename(self, ctx: commands.Context, role: discord.Role, *, new_name: str):
        try:
            await role.edit(name=new_name[:100])
            await ctx.send("✅ Role renamed.")
        except discord.Forbidden:
            await ctx.send("❌ Cannot rename that role.")

    @commands.hybrid_command(name="delrole", help="Delete a role")
    @app_commands.describe(role="Role")
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def delrole(self, ctx: commands.Context, role: discord.Role):
        try:
            await role.delete(reason=f"Deleted by {ctx.author}")
            await ctx.send("🗑️ Role deleted.")
        except discord.Forbidden:
            await ctx.send("❌ Cannot delete that role.")

    @commands.hybrid_command(name="mentionable", help="Toggle role mentionable")
    @app_commands.describe(role="Role")
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def mentionable(self, ctx: commands.Context, role: discord.Role):
        try:
            await role.edit(mentionable=not role.mentionable)
            await ctx.send(f"🔁 Mentionable now {not role.mentionable}.")
        except discord.Forbidden:
            await ctx.send("❌ Cannot edit that role.")

    # ---- ADDITIONAL MODERATION COMMANDS ----
    
    @commands.hybrid_command(name="addemote", help="Add an emoji to the server")
    @commands.has_permissions(manage_emojis=True)
    @commands.guild_only()
    async def addemote(self, ctx: commands.Context, name: str, url: str):
        """Add an emoji to the server from a URL"""
        assert ctx.guild is not None
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return await ctx.send("❌ Could not download image from that URL.")
                    
                    image_data = await resp.read()
                    
            emoji = await ctx.guild.create_custom_emoji(
                name=name,
                image=image_data,
                reason=f"Added by {ctx.author}"
            )
            await ctx.send(f"✅ Added emoji {emoji}")
            
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to add emoji: {str(e)}")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.hybrid_command(name="addmod", help="Register a moderator role")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def addmod(self, ctx: commands.Context, role: discord.Role):
        """Register a role as a moderator role for tracking purposes"""
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        st['mod_roles'].add(role.id)
        
        embed = discord.Embed(
            title="✅ Moderator Role Added",
            description=f"{role.mention} has been registered as a moderator role.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Added by {ctx.author}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="delmod", help="Remove a moderator role")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def delmod(self, ctx: commands.Context, role: discord.Role):
        """Unregister a moderator role"""
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        if role.id in st['mod_roles']:
            st['mod_roles'].remove(role.id)
            embed = discord.Embed(
                title="✅ Moderator Role Removed",
                description=f"{role.mention} is no longer registered as a moderator role.",
                color=discord.Color.orange()
            )
            embed.set_footer(text=f"Removed by {ctx.author}")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {role.mention} is not registered as a moderator role.")

    @commands.hybrid_command(name="listmods", help="List moderator roles")
    @commands.guild_only()
    async def listmods(self, ctx: commands.Context):
        """List all registered moderator roles"""
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        if not st['mod_roles']:
            await ctx.send("📋 No moderator roles have been registered.")
            return
        roles = [f"<@&{rid}>" for rid in st['mod_roles']]
        
        embed = discord.Embed(
            title="📋 Registered Moderator Roles",
            description="\n".join(f"• {role}" for role in roles),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="prefix", help="Show current prefix (static)")
    async def prefix(self, ctx: commands.Context):
        await ctx.send("Current prefix: `?` (changing not implemented).")

    @commands.hybrid_command(name="modules", help="List loaded bot modules (cogs)")
    @commands.guild_only()
    async def modules(self, ctx: commands.Context):
        """List all loaded cogs/modules"""
        cogs = list(self.bot.cogs.keys())
        
        embed = discord.Embed(
            title="📦 Loaded Modules",
            description=f"Total: **{len(cogs)}** modules loaded",
            color=discord.Color.blue()
        )
        
        # Group cogs by category
        command_cogs = [c for c in cogs if c.startswith('Command') or 'command' in c.lower()]
        event_cogs = [c for c in cogs if 'Event' in c or 'event' in c.lower()]
        other_cogs = [c for c in cogs if c not in command_cogs and c not in event_cogs]
        
        if command_cogs:
            embed.add_field(name="Command Modules", value="\n".join(f"• {c}" for c in command_cogs), inline=False)
        if event_cogs:
            embed.add_field(name="Event Modules", value="\n".join(f"• {c}" for c in event_cogs), inline=False)
        if other_cogs:
            embed.add_field(name="Other Modules", value="\n".join(f"• {c}" for c in other_cogs), inline=False)
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="moderations", help="Show recent moderation actions")
    @app_commands.describe(user="Optional: Filter by specific user")
    @commands.guild_only()
    async def moderations(self, ctx: commands.Context, user: discord.Member | None = None):
        """Show recent moderation actions in this server"""
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        
        cases = st['cases']
        if not cases:
            return await ctx.send("📋 No moderation actions recorded yet.")
        
        # Filter by user if specified
        if user:
            cases = [c for c in cases if c['user_id'] == user.id]
            if not cases:
                return await ctx.send(f"📋 No moderation actions found for {user.mention}.")
        
        # Get last 10 cases
        recent_cases = cases[-10:]
        
        embed = discord.Embed(
            title=f"📋 Recent Moderations" + (f" for {user.display_name}" if user else ""),
            color=discord.Color.blue()
        )
        
        for case in reversed(recent_cases):
            mod = ctx.guild.get_member(case['mod_id'])
            mod_name = mod.display_name if mod else f"<@{case['mod_id']}>"
            target = ctx.guild.get_member(case['user_id'])
            target_name = target.display_name if target else f"<@{case['user_id']}>"
            
            embed.add_field(
                name=f"Case #{cases.index(case) + 1} - {case['action']}",
                value=f"**Target:** {target_name}\n**Moderator:** {mod_name}\n**Reason:** {case['reason']}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="modlogs", help="Show moderation history for a user")
    @app_commands.describe(user="User to check moderation history for")
    @commands.guild_only()
    async def modlogs(self, ctx: commands.Context, user: discord.Member):
        """Show all moderation actions taken against a specific user"""
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        
        user_cases = [c for c in st['cases'] if c['user_id'] == user.id]
        
        if not user_cases:
            return await ctx.send(f"📋 No moderation history found for {user.mention}.")
        
        embed = discord.Embed(
            title=f"📋 Moderation History: {user.display_name}",
            description=f"Total actions: **{len(user_cases)}**",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Group by action type
        from collections import Counter
        action_counts = Counter(c['action'] for c in user_cases)
        
        embed.add_field(
            name="Action Summary",
            value="\n".join(f"• {action}: {count}" for action, count in action_counts.items()),
            inline=False
        )
        
        # Show last 5 actions
        recent = user_cases[-5:]
        if recent:
            embed.add_field(
                name="Recent Actions",
                value="\n".join(
                    f"**{c['action']}** - {c['reason'][:50]}" 
                    for c in reversed(recent)
                ),
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="modstats", help="Show moderator statistics")
    @app_commands.describe(moderator="Optional: Specific moderator to check")
    @commands.guild_only()
    async def modstats(self, ctx: commands.Context, moderator: discord.Member | None = None):
        """Show statistics about moderation actions"""
        assert ctx.guild is not None
        st = self._state(ctx.guild.id)
        
        cases = st['cases']
        if not cases:
            return await ctx.send("📊 No moderation actions recorded yet.")
        
        # Filter by moderator if specified
        if moderator:
            mod_cases = [c for c in cases if c['mod_id'] == moderator.id]
            if not mod_cases:
                return await ctx.send(f"📊 {moderator.mention} hasn't performed any moderation actions.")
            
            from collections import Counter
            action_counts = Counter(c['action'] for c in mod_cases)
            
            embed = discord.Embed(
                title=f"📊 Moderator Stats: {moderator.display_name}",
                description=f"Total actions: **{len(mod_cases)}**",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=moderator.display_avatar.url)
            
            for action, count in action_counts.most_common():
                embed.add_field(name=action, value=str(count), inline=True)
        else:
            # Server-wide stats
            from collections import Counter
            mod_counts = Counter(c['mod_id'] for c in cases)
            action_counts = Counter(c['action'] for c in cases)
            
            embed = discord.Embed(
                title="📊 Server Moderation Statistics",
                description=f"Total actions: **{len(cases)}**",
                color=discord.Color.gold()
            )
            
            # Top moderators
            top_mods = []
            for mod_id, count in mod_counts.most_common(5):
                mod = ctx.guild.get_member(mod_id)
                name = mod.display_name if mod else f"<@{mod_id}>"
                top_mods.append(f"• {name}: {count}")
            
            if top_mods:
                embed.add_field(name="Top Moderators", value="\n".join(top_mods), inline=False)
            
            # Action breakdown
            action_list = [f"• {action}: {count}" for action, count in action_counts.most_common()]
            if action_list:
                embed.add_field(name="Action Breakdown", value="\n".join(action_list), inline=False)
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="vcmute", help="Voice mute a member in voice channels")
    @app_commands.describe(user="Member to voice mute", reason="Reason for voice muting")
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def vcmute(self, ctx: commands.Context, user: discord.Member, *, reason: str = "No reason provided"):
        """Mute a member in voice channels"""
        assert ctx.guild is not None
        
        if not user.voice:
            return await ctx.send("❌ User is not in a voice channel.")
        
        try:
            await user.edit(mute=True, reason=reason)
            self._add_case(ctx.guild.id, user.id, ctx.author.id, 'VCMUTE', reason)
            
            embed = discord.Embed(
                title="🔇 Voice Muted",
                description=f"{user.mention} has been voice muted.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Muted by {ctx.author}")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to voice mute that user.")
        except Exception as e:
            await ctx.send(f"❌ Failed to voice mute: {str(e)}")

    @commands.hybrid_command(name="vcunmute", help="Voice unmute a member in voice channels")
    @app_commands.describe(user="Member to voice unmute", reason="Reason for voice unmuting")
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def vcunmute(self, ctx: commands.Context, user: discord.Member, *, reason: str = "No reason provided"):
        """Unmute a member in voice channels"""
        assert ctx.guild is not None
        
        try:
            await user.edit(mute=False, reason=reason)
            self._add_case(ctx.guild.id, user.id, ctx.author.id, 'VCUNMUTE', reason)
            
            embed = discord.Embed(
                title="🔊 Voice Unmuted",
                description=f"{user.mention} has been voice unmuted.",
                color=discord.Color.green()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Unmuted by {ctx.author}")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to voice unmute that user.")
        except Exception as e:
            await ctx.send(f"❌ Failed to voice unmute: {str(e)}")

    @commands.hybrid_command(name="deafen", help="Server deafen a member in voice channels")
    @app_commands.describe(user="Member to deafen", reason="Reason for deafening")
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def deafen(self, ctx: commands.Context, user: discord.Member, *, reason: str = "No reason provided"):
        """Server deafen a member in voice channels"""
        assert ctx.guild is not None
        
        if not user.voice:
            return await ctx.send("❌ User is not in a voice channel.")
        
        try:
            await user.edit(deafen=True, reason=reason)
            self._add_case(ctx.guild.id, user.id, ctx.author.id, 'DEAFEN', reason)
            
            embed = discord.Embed(
                title="🔇 Deafened",
                description=f"{user.mention} has been server deafened.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Deafened by {ctx.author}")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to deafen that user.")
        except Exception as e:
            await ctx.send(f"❌ Failed to deafen: {str(e)}")

    @commands.hybrid_command(name="undeafen", help="Server undeafen a member in voice channels")
    @app_commands.describe(user="Member to undeafen", reason="Reason for undeafening")
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def undeafen(self, ctx: commands.Context, user: discord.Member, *, reason: str = "No reason provided"):
        """Server undeafen a member in voice channels"""
        assert ctx.guild is not None
        
        try:
            await user.edit(deafen=False, reason=reason)
            self._add_case(ctx.guild.id, user.id, ctx.author.id, 'UNDEAFEN', reason)
            
            embed = discord.Embed(
                title="🔊 Undeafened",
                description=f"{user.mention} has been server undeafened.",
                color=discord.Color.green()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Undeafened by {ctx.author}")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to undeafen that user.")
        except Exception as e:
            await ctx.send(f"❌ Failed to undeafen: {str(e)}")

    @commands.hybrid_command(name="softban", help="Softban (ban then immediately unban to delete messages)")
    @app_commands.describe(user="Member to softban", reason="Reason for softban")
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def softban(self, ctx: commands.Context, user: discord.Member, *, reason: str = "No reason provided"):
        """Ban then immediately unban to delete user's messages"""
        assert ctx.guild is not None
        
        try:
            await ctx.guild.ban(user, reason=f"Softban: {reason}", delete_message_days=1)
            await ctx.guild.unban(user, reason="Softban automatic unban")
            self._add_case(ctx.guild.id, user.id, ctx.author.id, 'SOFTBAN', reason)
            
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
                self._add_case(ctx.guild.id, user.id, ctx.author.id, 'REMROLE', role.name)
                
                embed = discord.Embed(
                    title="➖ Role Removed",
                    description=f"Removed {role.mention} from {user.mention}.",
                    color=discord.Color.orange()
                )
            else:
                await user.add_roles(role, reason=f"Role toggle by {ctx.author}")
                self._add_case(ctx.guild.id, user.id, ctx.author.id, 'ADDROLE', role.name)
                
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

    @commands.hybrid_command(name="clean", help="Delete bot messages and command invocations")
    @app_commands.describe(count="Number of messages to check (default 100)")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def clean(self, ctx: commands.Context, count: int = 100):
        """Delete bot messages and command invocations from the channel"""
        if count < 1 or count > 1000:
            return await ctx.send("❌ Count must be between 1 and 1000.")
        
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

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationExtended(bot))
