import discord  # type: ignore[import-not-found]
from discord.ext import commands  # type: ignore[import-not-found]
from discord import app_commands  # type: ignore[import-not-found]
import asyncio
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import sqlite3
from typing import Optional, List
import re

class AdvancedModeration(commands.Cog):
    """Advanced moderation features with built-in safety mechanisms"""
    
    def __init__(self, bot):
        self.bot = bot
        # Rate limiting for safety
        self.command_cooldowns = defaultdict(list)
        
    def _check_rate_limit(self, user_id: int, command: str, max_uses: int = 5, window: int = 60) -> bool:
        """Check if user is rate limited for a command (safety mechanism)"""
        now = time.time()
        user_commands = self.command_cooldowns[f"{user_id}_{command}"]
        
        # Remove old entries
        user_commands[:] = [cmd_time for cmd_time in user_commands if now - cmd_time < window]
        
        if len(user_commands) >= max_uses:
            return False  # Rate limited
        
        user_commands.append(now)
        return True

    @commands.hybrid_command(name="tempban")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(
        member="Member to temporarily ban",
        duration="Ban duration in minutes (max 10080 = 7 days)",
        reason="Reason for the ban"
    )
    async def tempban(self, ctx, member: discord.Member, duration: int, *, reason: str = "No reason provided"):
        """Temporarily ban a member (max 7 days for safety)"""
        # Safety checks
        if not self._check_rate_limit(ctx.author.id, "tempban", 3, 300):  # 3 tempbans per 5 minutes
            await ctx.send("❌ Rate limit: You can only use tempban 3 times per 5 minutes.", ephemeral=True)
            return
            
        if duration > 10080:  # Max 7 days
            await ctx.send("❌ Maximum tempban duration is 7 days (10080 minutes)", ephemeral=True)
            return
            
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot ban someone with equal or higher role", ephemeral=True)
            return
            
        if member == ctx.guild.owner:
            await ctx.send("❌ Cannot ban the server owner", ephemeral=True)
            return

        try:
            # Note: per server policy we do not DM users for ban actions.
            
            # Ban the member
            await member.ban(reason=f"Tempban ({duration}m): {reason}")
            
            # Schedule unban
            self.bot.loop.create_task(self._schedule_unban(ctx.guild, member, duration * 60))
            
            embed = discord.Embed(
                title="⏰ Temporary Ban Issued",
                description=f"**{member}** has been temporarily banned",
                color=0xff0000
            )
            embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Unban Time", value=f"<t:{int(time.time() + duration * 60)}:F>", inline=False)
            
            await ctx.send(embed=embed)
            
            # Log to designated channel handled by LoggingCog (via audit logs)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban this member", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Error occurred: {str(e)}", ephemeral=True)

    async def _schedule_unban(self, guild: discord.Guild, member: discord.Member, delay: int):
        """Schedule automatic unban"""
        await asyncio.sleep(delay)
        try:
            await guild.unban(member, reason="Temporary ban expired")
        except:
            pass  # Member may have been manually unbanned

    @commands.hybrid_command(name="mute")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(
        member="Member to mute",
        duration="Mute duration in minutes (max 40320 = 28 days)",
        reason="Reason for the mute"
    )
    async def mute(self, ctx, member: discord.Member, duration: int, *, reason: str = "No reason provided"):
        """Mute a member using timeout (max 28 days)"""
        # Safety checks
        if not self._check_rate_limit(ctx.author.id, "mute", 5, 300):  # 5 mutes per 5 minutes
            await ctx.send("❌ Rate limit: You can only use mute 5 times per 5 minutes.", ephemeral=True)
            return
            
        if duration > 40320:  # Max 28 days
            await ctx.send("❌ Maximum mute duration is 28 days (40320 minutes)", ephemeral=True)
            return
            
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot mute someone with equal or higher role", ephemeral=True)
            return

        try:
            until = datetime.now(timezone.utc) + timedelta(minutes=duration)
            # Add moderator info to reason for logging
            audit_reason = f"{reason} | By: {ctx.author} ({ctx.author.id})"
            await member.timeout(until, reason=audit_reason)
            
            embed = discord.Embed(
                title="🔇 Member Muted",
                description=f"**{member}** has been muted",
                color=0xf39c12
            )
            embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Until", value=f"<t:{int(until.timestamp())}:F>", inline=False)
            
            await ctx.send(embed=embed)
            
            # Log to designated channel handled by LoggingCog (via audit logs)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to timeout this member", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Error occurred: {str(e)}", ephemeral=True)

    @commands.hybrid_command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to unmute")
    async def unmute(self, ctx, member: discord.Member):
        """Remove timeout from a member"""
        try:
            audit_reason = f"Unmuted | By: {ctx.author} ({ctx.author.id})"
            await member.timeout(None, reason=audit_reason)
            
            embed = discord.Embed(
                title="🔊 Member Unmuted",
                description=f"**{member}** has been unmuted",
                color=0x00ff00
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
            # Log to designated channel handled by LoggingCog (via audit logs)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to remove timeout from this member", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Error occurred: {str(e)}", ephemeral=True)

    @commands.command(name="hide")
    @commands.has_permissions(manage_channels=True)
    async def hide_channel(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Hide a channel from @everyone"""
        guild = ctx.guild
        if guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        resolved_channel = channel or ctx.channel

        # Type guard to ensure channel is TextChannel
        if not isinstance(resolved_channel, discord.TextChannel):
            await ctx.send("❌ This command can only be used in text channels.", ephemeral=True)
            return

        target_channel: discord.TextChannel = resolved_channel
        
        try:
            overwrite = target_channel.overwrites_for(guild.default_role)
            overwrite.view_channel = False
            await target_channel.set_permissions(guild.default_role, overwrite=overwrite, 
                                        reason=f"Channel hidden by {ctx.author}")
            
            embed = discord.Embed(
                title="👁️‍🗨️ Channel Hidden",
                description=f"**{target_channel.name}** has been hidden from @everyone",
                color=0x95a5a6
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)
            
            # Log to designated channel
            logging_cog = self.bot.get_cog("LoggingCog")
            if logging_cog:
                await logging_cog.log_event(
                    event_type="CHANNEL_UPDATE",
                    guild_id=guild.id,
                    moderator_id=ctx.author.id,
                    details=f"**#{target_channel.name}** was hidden from @everyone"
                )
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to manage this channel", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Error occurred: {str(e)}", ephemeral=True)

    @commands.command(name="unhide")
    @commands.has_permissions(manage_channels=True)
    async def unhide_channel(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Unhide a channel for @everyone"""
        guild = ctx.guild
        if guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        resolved_channel = channel or ctx.channel

        # Type guard to ensure channel is TextChannel
        if not isinstance(resolved_channel, discord.TextChannel):
            await ctx.send("❌ This command can only be used in text channels.", ephemeral=True)
            return

        target_channel: discord.TextChannel = resolved_channel
        
        try:
            overwrite = target_channel.overwrites_for(guild.default_role)
            overwrite.view_channel = True
            await target_channel.set_permissions(guild.default_role, overwrite=overwrite, 
                                        reason=f"Channel unhidden by {ctx.author}")
            
            embed = discord.Embed(
                title="👁️ Channel Unhidden",
                description=f"**{target_channel.name}** is now visible to @everyone",
                color=0x00ff00
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)
            
            # Log to designated channel
            logging_cog = self.bot.get_cog("LoggingCog")
            if logging_cog:
                await logging_cog.log_event(
                    event_type="CHANNEL_UPDATE",
                    guild_id=guild.id,
                    moderator_id=ctx.author.id,
                    details=f"**#{target_channel.name}** is now visible to @everyone"
                )
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to manage this channel", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Error occurred: {str(e)}", ephemeral=True)

    # Note: slowmode command already exists in modcog.py, so not implementing here to avoid conflicts

async def setup(bot):
    await bot.add_cog(AdvancedModeration(bot))