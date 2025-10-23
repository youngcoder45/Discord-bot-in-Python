import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time
from collections import defaultdict
from datetime import datetime, timedelta
import sqlite3
from typing import Optional, List
import re

class AdvancedModeration(commands.Cog):
    """Advanced moderation features with built-in safety mechanisms"""
    
    def __init__(self, bot):
        self.bot = bot
        # Rate limiting for safety
        self.command_cooldowns = defaultdict(list)
        # Automod disabled by user request
        self.automod_settings = {
            'invite_links': False,
            'excessive_caps': False,
            'excessive_mentions': False,
            'banned_words': [],
            'auto_dehoist': False
        }
        # Logging channel ID
        self.log_channel_id = 1399746928585085068
        
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

    async def _log_action(self, guild: discord.Guild, embed: discord.Embed):
        """Log moderation action to designated channel"""
        try:
            log_channel = self.bot.get_channel(self.log_channel_id)
            if log_channel:
                await log_channel.send(embed=embed)
        except Exception:
            pass  # Silently fail if logging fails

    @commands.hybrid_command(name="automod")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        feature="Automod feature to toggle",
        status="Enable or disable the feature"
    )
    async def automod_config(self, ctx, feature: str, status: bool):
        """Configure automod features (Admin only)"""
        valid_features = ['invite_links', 'excessive_caps', 'excessive_mentions', 'auto_dehoist']
        
        if feature not in valid_features:
            embed = discord.Embed(
                title="❌ Invalid Feature",
                description=f"Valid features: {', '.join(valid_features)}",
                color=0xe74c3c
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        self.automod_settings[feature] = status
        
        embed = discord.Embed(
            title="✅ Automod Updated",
            description=f"**{feature}** has been {'enabled' if status else 'disabled'}",
            color=0x2ecc71
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="automodstatus")
    @commands.has_permissions(manage_messages=True)
    async def automod_status(self, ctx):
        """View current automod settings"""
        embed = discord.Embed(
            title="🤖 Automod Settings",
            color=0x3498db
        )
        
        for feature, enabled in self.automod_settings.items():
            status = "✅ Enabled" if enabled else "❌ Disabled"
            embed.add_field(name=feature.replace('_', ' ').title(), value=status, inline=True)
        
        await ctx.send(embed=embed)

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
            # Send DM before ban
            try:
                embed = discord.Embed(
                    title="Temporary Ban Notice",
                    description=f"You have been temporarily banned from **{ctx.guild.name}**",
                    color=0xe74c3c
                )
                embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Unban Time", value=f"<t:{int(time.time() + duration * 60)}:F>", inline=False)
                await member.send(embed=embed)
            except:
                pass
            
            # Ban the member
            await member.ban(reason=f"Tempban ({duration}m): {reason}")
            
            # Schedule unban
            self.bot.loop.create_task(self._schedule_unban(ctx.guild, member, duration * 60))
            
            embed = discord.Embed(
                title="⏰ Temporary Ban Issued",
                description=f"**{member}** has been temporarily banned",
                color=0xe74c3c
            )
            embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Unban Time", value=f"<t:{int(time.time() + duration * 60)}:F>", inline=False)
            
            await ctx.send(embed=embed)
            
            # Log to designated channel
            log_embed = discord.Embed(
                title="🔨 Temporary Ban Issued",
                description=f"**{member}** was temporarily banned",
                color=0xe74c3c
            )
            log_embed.add_field(name="Moderator", value=f"{ctx.author} ({ctx.author.id})", inline=True)
            log_embed.add_field(name="Target", value=f"{member} ({member.id})", inline=True)
            log_embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            log_embed.add_field(name="Reason", value=reason, inline=False)
            log_embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
            log_embed.timestamp = datetime.now()
            await self._log_action(ctx.guild, log_embed)
            
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
            until = datetime.now() + timedelta(minutes=duration)
            await member.timeout(until, reason=reason)
            
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
            
            # Log to designated channel
            log_embed = discord.Embed(
                title="🔇 Member Muted",
                description=f"**{member}** was muted",
                color=0xf39c12
            )
            log_embed.add_field(name="Moderator", value=f"{ctx.author} ({ctx.author.id})", inline=True)
            log_embed.add_field(name="Target", value=f"{member} ({member.id})", inline=True)
            log_embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            log_embed.add_field(name="Reason", value=reason, inline=False)
            log_embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
            log_embed.timestamp = datetime.now()
            await self._log_action(ctx.guild, log_embed)
            
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
            await member.timeout(None, reason=f"Unmuted by {ctx.author}")
            
            embed = discord.Embed(
                title="🔊 Member Unmuted",
                description=f"**{member}** has been unmuted",
                color=0x2ecc71
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
            # Log to designated channel
            log_embed = discord.Embed(
                title="🔊 Member Unmuted",
                description=f"**{member}** was unmuted",
                color=0x2ecc71
            )
            log_embed.add_field(name="Moderator", value=f"{ctx.author} ({ctx.author.id})", inline=True)
            log_embed.add_field(name="Target", value=f"{member} ({member.id})", inline=True)
            log_embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
            log_embed.timestamp = datetime.now()
            await self._log_action(ctx.guild, log_embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to remove timeout from this member", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Error occurred: {str(e)}", ephemeral=True)

    # Note: slowmode command removed - it's already implemented in modcog.py

    @commands.hybrid_command(name="advmodstats")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(moderator="Get stats for specific moderator")
    async def advanced_mod_stats(self, ctx, moderator: Optional[discord.Member] = None):
        """View moderation statistics"""
        embed = discord.Embed(
            title="📊 Moderation Statistics",
            color=0x3498db
        )
        
        if moderator:
            embed.description = f"Statistics for {moderator.mention}"
            # Add rate limit info for transparency
            commands_used = {}
            for key, times in self.command_cooldowns.items():
                if key.startswith(str(moderator.id)):
                    command = key.split('_', 1)[1]
                    commands_used[command] = len([t for t in times if time.time() - t < 3600])  # Last hour
            
            if commands_used:
                stats = "\n".join([f"**{cmd}**: {count} (last hour)" for cmd, count in commands_used.items()])
                embed.add_field(name="Recent Command Usage", value=stats, inline=False)
            else:
                embed.add_field(name="Recent Activity", value="No commands used in the last hour", inline=False)
        else:
            embed.description = "Server moderation overview"
            total_commands = sum(len(times) for times in self.command_cooldowns.values())
            embed.add_field(name="Total Commands Used", value=str(total_commands), inline=True)
            
            # Automod status
            enabled_features = [f for f, enabled in self.automod_settings.items() if enabled]
            embed.add_field(name="Active Automod Features", value=", ".join(enabled_features) or "None", inline=False)
        
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Advanced automod message scanning - DISABLED BY USER REQUEST"""
        # All automod features disabled per user request
        pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Auto-dehoist - DISABLED BY USER REQUEST"""
        # Auto-dehoist disabled per user request
        pass

async def setup(bot):
    await bot.add_cog(AdvancedModeration(bot))