"""
Basic moderation commands for server management
"""

import discord
import asyncio
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta
from typing import Optional
from ..utils.helpers import create_success_embed, create_error_embed, create_warning_embed, log_action

class Moderation(commands.Cog):
    """Basic moderation commands for server management"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="purge", help="Delete a specified number of messages (Mod only)")
    @app_commands.describe(
        amount="Number of messages to delete (1-100)",
        user="Optional: Only delete messages from this user"
    )
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(self, ctx: commands.Context, amount: int, user: Optional[discord.Member] = None):
        """Delete a specified number of messages"""
        if amount < 1 or amount > 100:
            await ctx.send(embed=create_error_embed("Invalid Amount", "Please specify between 1 and 100 messages."), ephemeral=True)
            return
        
        try:
            def check(message):
                if user:
                    return message.author == user
                return True
            
            # Delete the command message if it's a prefix command
            if ctx.interaction is None:
                await ctx.message.delete()
            
            deleted = await ctx.channel.purge(limit=amount, check=check)  # type: ignore
            deleted_count = len(deleted)
            
            # Send confirmation message that auto-deletes
            if user:
                embed = create_success_embed(
                    "Messages Purged", 
                    f"Deleted {deleted_count} messages from {user.mention}"
                )
            else:
                embed = create_success_embed(
                    "Messages Purged", 
                    f"Deleted {deleted_count} messages"
                )
            
            embed.set_footer(text="This message will be deleted in 5 seconds")
            
            if ctx.interaction:
                # for slash/hybrid commands: send initial response (ephemeral)
                await ctx.interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                msg = await ctx.send(embed=embed)
                await asyncio.sleep(5)
                await msg.delete()
            
            await log_action("PURGE", ctx.author.id, f"Deleted {deleted_count} messages in #{ctx.channel.name}")  # type: ignore
            
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Error", "I don't have permission to delete messages in this channel."), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=create_error_embed("Purge Failed", f"An error occurred: {str(e)}"), ephemeral=True)

    @commands.hybrid_command(name="kick", help="Kick a member from the server (Admin only)")
    @app_commands.describe(
        member="The member to kick",
        reason="Reason for the kick"
    )
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server"""
        if member == ctx.author:
            await ctx.send(embed=create_error_embed("Error", "You cannot kick yourself."), ephemeral=True)
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:  # type: ignore
            await ctx.send(embed=create_error_embed("Permission Error", "You cannot kick someone with a higher or equal role."), ephemeral=True)
            return
        
        if member.top_role >= ctx.guild.me.top_role:  # type: ignore
            await ctx.send(embed=create_error_embed("Permission Error", "I cannot kick someone with a higher or equal role than mine."), ephemeral=True)
            return
        
        try:
            # Try to DM the user first
            try:
                dm_embed = discord.Embed(
                    title="🦵 You were kicked",
                    description=f"You have been kicked from **{ctx.guild.name}**",  # type: ignore
                    color=discord.Color.orange(),
                    timestamp=datetime.now(timezone.utc)
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                await member.send(embed=dm_embed)
            except:
                pass  # DM failed, continue with kick
            
            await member.kick(reason=f"{reason} - Kicked by {ctx.author}")
            
            embed = create_success_embed(
                "Member Kicked",
                f"{member.mention} has been kicked from the server."
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            await log_action("KICK", member.id, f"Kicked by {ctx.author} - Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Error", "I don't have permission to kick this member."), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=create_error_embed("Kick Failed", f"An error occurred: {str(e)}"), ephemeral=True)

    @commands.hybrid_command(name="ban", help="Ban a member from the server (Admin only)")
    @app_commands.describe(
        member="The member to ban",
        reason="Reason for the ban",
        delete_days="Number of days of messages to delete (0-7)"
    )
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx: commands.Context, member: discord.Member, delete_days: int = 0, *, reason: str = "No reason provided"):
        """Ban a member from the server"""
        if member == ctx.author:
            await ctx.send(embed=create_error_embed("Error", "You cannot ban yourself."), ephemeral=True)
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:  # type: ignore
            await ctx.send(embed=create_error_embed("Permission Error", "You cannot ban someone with a higher or equal role."), ephemeral=True)
            return
        
        if member.top_role >= ctx.guild.me.top_role:  # type: ignore
            await ctx.send(embed=create_error_embed("Permission Error", "I cannot ban someone with a higher or equal role than mine."), ephemeral=True)
            return
        
        if delete_days < 0 or delete_days > 7:
            await ctx.send(embed=create_error_embed("Invalid Days", "Delete days must be between 0 and 7."), ephemeral=True)
            return
        
        try:
            # Try to DM the user first
            try:
                dm_embed = discord.Embed(
                    title="🔨 You were banned",
                    description=f"You have been banned from **{ctx.guild.name}**",  # type: ignore
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                await member.send(embed=dm_embed)
            except:
                pass  # DM failed, continue with ban
            
            await member.ban(reason=f"{reason} - Banned by {ctx.author}", delete_message_days=delete_days)
            
            embed = create_success_embed(
                "Member Banned",
                f"{member.mention} has been banned from the server."
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            if delete_days > 0:
                embed.add_field(name="Messages Deleted", value=f"{delete_days} days", inline=True)
            
            await ctx.send(embed=embed)
            await log_action("BAN", member.id, f"Banned by {ctx.author} - Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Error", "I don't have permission to ban this member."), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=create_error_embed("Ban Failed", f"An error occurred: {str(e)}"), ephemeral=True)

    @commands.hybrid_command(name="unban", help="Unban a user from the server (Admin only)")
    @app_commands.describe(
        user="The user ID or username#discriminator to unban",
        reason="Reason for the unban"
    )
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self, ctx: commands.Context, user: str, *, reason: str = "No reason provided"):
        """Unban a user from the server"""
        try:
            # Try to parse as user ID first
            try:
                user_id = int(user)
                banned_user = await self.bot.fetch_user(user_id)
            except ValueError:
                # Try to find by username#discriminator
                banned_users = await ctx.guild.bans()  # returns list[BanEntry]
                banned_user = None
                for ban_entry in banned_users:
                    if str(ban_entry.user) == user:
                        banned_user = ban_entry.user
                        break
                
                if not banned_user:
                    await ctx.send(embed=create_error_embed("User Not Found", "Could not find a banned user with that name or ID."), ephemeral=True)
                    return
            
            # Check if user is actually banned
            try:
                await ctx.guild.fetch_ban(banned_user)  # type: ignore
            except discord.NotFound:
                await ctx.send(embed=create_error_embed("Not Banned", f"{banned_user} is not banned from this server."), ephemeral=True)
                return
            
            await ctx.guild.unban(banned_user, reason=f"{reason} - Unbanned by {ctx.author}")  # type: ignore
            
            embed = create_success_embed(
                "Member Unbanned",
                f"{banned_user.mention} has been unbanned from the server."
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            await log_action("UNBAN", banned_user.id, f"Unbanned by {ctx.author} - Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Error", "I don't have permission to unban members."), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=create_error_embed("Unban Failed", f"An error occurred: {str(e)}"), ephemeral=True)

    @commands.hybrid_command(name="timeout", help="Timeout a member for a specified duration (Admin only)")
    @app_commands.describe(
        member="The member to timeout",
        duration="Duration in minutes (max 40320 = 28 days)",
        reason="Reason for the timeout"
    )
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def timeout(self, ctx: commands.Context, member: discord.Member, duration: int, *, reason: str = "No reason provided"):
        """Timeout a member for a specified duration"""
        if member == ctx.author:
            await ctx.send(embed=create_error_embed("Error", "You cannot timeout yourself."), ephemeral=True)
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:  # type: ignore
            await ctx.send(embed=create_error_embed("Permission Error", "You cannot timeout someone with a higher or equal role."), ephemeral=True)
            return
        
        if member.top_role >= ctx.guild.me.top_role:  # type: ignore
            await ctx.send(embed=create_error_embed("Permission Error", "I cannot timeout someone with a higher or equal role than mine."), ephemeral=True)
            return
        
        if duration < 1 or duration > 40320:  # 28 days max
            await ctx.send(embed=create_error_embed("Invalid Duration", "Duration must be between 1 minute and 40320 minutes (28 days)."), ephemeral=True)
            return
        
        try:
            until = datetime.now(timezone.utc) + timedelta(minutes=duration)
            
            # Try to DM the user first
            try:
                dm_embed = discord.Embed(
                    title="⏰ You were timed out",
                    description=f"You have been timed out in **{ctx.guild.name}**",  # type: ignore
                    color=discord.Color.orange(),
                    timestamp=datetime.now(timezone.utc)
                )
                dm_embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
                dm_embed.add_field(name="Until", value=f"<t:{int(until.timestamp())}:F>", inline=True)
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                await member.send(embed=dm_embed)
            except:
                pass  # DM failed, continue with timeout
            
            await member.timeout(until, reason=f"{reason} - Timed out by {ctx.author}")
            
            embed = create_success_embed(
                "Member Timed Out",
                f"{member.mention} has been timed out."
            )
            embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            embed.add_field(name="Until", value=f"<t:{int(until.timestamp())}:R>", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            await log_action("TIMEOUT", member.id, f"Timed out by {ctx.author} for {duration} minutes - Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Error", "I don't have permission to timeout this member."), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=create_error_embed("Timeout Failed", f"An error occurred: {str(e)}"), ephemeral=True)

    @commands.hybrid_command(name="untimeout", help="Remove timeout from a member (Admin only)")
    @app_commands.describe(
        member="The member to remove timeout from",
        reason="Reason for removing the timeout"
    )
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def untimeout(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Remove timeout from a member"""
        if not member.is_timed_out():
            await ctx.send(embed=create_error_embed("Not Timed Out", f"{member.mention} is not currently timed out."), ephemeral=True)
            return
        
        try:
            await member.timeout(None, reason=f"{reason} - Timeout removed by {ctx.author}")
            
            embed = create_success_embed(
                "Timeout Removed",
                f"Timeout has been removed from {member.mention}."
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            await log_action("UNTIMEOUT", member.id, f"Timeout removed by {ctx.author} - Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Error", "I don't have permission to remove timeout from this member."), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=create_error_embed("Untimeout Failed", f"An error occurred: {str(e)}"), ephemeral=True)

    @commands.hybrid_command(name="warn", help="Issue a warning to a member (Admin only)")
    @app_commands.describe(
        member="The member to warn",
        reason="Reason for the warning"
    )
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Issue a warning to a member"""
        if member == ctx.author:
            await ctx.send(embed=create_error_embed("Error", "You cannot warn yourself."), ephemeral=True)
            return
        
        try:
            # Try to DM the user first
            try:
                dm_embed = discord.Embed(
                    title="⚠️ Warning",
                    description=f"You have received a warning in **{ctx.guild.name}**",  # type: ignore
                    color=discord.Color.yellow(),
                    timestamp=datetime.now(timezone.utc)
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                dm_embed.set_footer(text="Please follow the server rules to avoid further action.")
                await member.send(embed=dm_embed)
                dm_sent = True
            except:
                dm_sent = False
            
            embed = create_warning_embed(
                "Member Warned",
                f"{member.mention} has been warned."
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="DM Sent", value="Yes" if dm_sent else "No", inline=True)
            
            await ctx.send(embed=embed)
            await log_action("WARN", member.id, f"Warned by {ctx.author} - Reason: {reason}")
            
        except Exception as e:
            await ctx.send(embed=create_error_embed("Warning Failed", f"An error occurred: {str(e)}"), ephemeral=True)

    @commands.hybrid_command(name="slowmode", help="Set slowmode for a channel (Admin only)")
    @app_commands.describe(
        seconds="Slowmode delay in seconds (0-21600, 0 to disable)",
        channel="Channel to apply slowmode to (current channel if not specified)"
    )
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def slowmode(self, ctx: commands.Context, seconds: int, channel: Optional[discord.TextChannel] = None):
        """Set slowmode for a channel"""
        if channel is None:
            channel = ctx.channel  # type: ignore
        
        if seconds < 0 or seconds > 21600:  # 6 hours max
            await ctx.send(embed=create_error_embed("Invalid Duration", "Slowmode must be between 0 and 21600 seconds (6 hours)."), ephemeral=True)
            return
        
        try:
            await channel.edit(slowmode_delay=seconds)  # type: ignore
            
            if seconds == 0:
                embed = create_success_embed(
                    "Slowmode Disabled",
                    f"Slowmode has been disabled in {channel.mention}."  # type: ignore
                )
            else:
                embed = create_success_embed(
                    "Slowmode Enabled",
                    f"Slowmode set to {seconds} seconds in {channel.mention}."  # type: ignore
                )
            
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)
            await log_action("SLOWMODE", ctx.author.id, f"Set slowmode to {seconds} seconds in #{channel.name}")  # type: ignore
            
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Error", "I don't have permission to edit this channel."), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=create_error_embed("Slowmode Failed", f"An error occurred: {str(e)}"), ephemeral=True)

    @commands.hybrid_command(name="nick", help="Change a member's nickname (Admin only)")
    @app_commands.describe(
        member="The member to change nickname for",
        nickname="New nickname (leave empty to remove nickname)"
    )
    @commands.has_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def nick(self, ctx: commands.Context, member: discord.Member, *, nickname: Optional[str] = None):
        """Change a member's nickname"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner and member != ctx.author:  # type: ignore
            await ctx.send(embed=create_error_embed("Permission Error", "You cannot change the nickname of someone with a higher or equal role."), ephemeral=True)
            return
        
        if member.top_role >= ctx.guild.me.top_role and member != ctx.guild.me:  # type: ignore
            await ctx.send(embed=create_error_embed("Permission Error", "I cannot change the nickname of someone with a higher or equal role than mine."), ephemeral=True)
            return
        
        try:
            old_nick = member.display_name
            await member.edit(nick=nickname)
            
            if nickname:
                embed = create_success_embed(
                    "Nickname Changed",
                    f"{member.mention}'s nickname has been changed."
                )
                embed.add_field(name="Old Nickname", value=old_nick, inline=True)
                embed.add_field(name="New Nickname", value=nickname, inline=True)
            else:
                embed = create_success_embed(
                    "Nickname Removed",
                    f"{member.mention}'s nickname has been removed."
                )
                embed.add_field(name="Old Nickname", value=old_nick, inline=True)
            
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)
            await log_action("NICK_CHANGE", member.id, f"Nickname changed by {ctx.author} from '{old_nick}' to '{nickname or 'None'}'")
            
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Error", "I don't have permission to change this member's nickname."), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=create_error_embed("Nickname Change Failed", f"An error occurred: {str(e)}"), ephemeral=True)

    # Error handlers for missing permissions
    @purge.error
    @kick.error
    @ban.error
    @unban.error
    @timeout.error
    @untimeout.error
    @warn.error
    @slowmode.error
    async def moderation_error(self, ctx: commands.Context, error):
        # helper to send ephemeral when appropriate
        async def _send(embed):
            if getattr(ctx, "interaction", None):
                # try to send initial response
                try:
                    await ctx.interaction.response.send_message(embed=embed, ephemeral=True)
                except Exception:
                    # if already responded, fallback to followup
                    await ctx.interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await ctx.send(embed=embed)

        if isinstance(error, commands.MissingPermissions):
            await _send(create_error_embed("Missing Permissions", "You don't have the required permissions to use this command."))
        elif isinstance(error, commands.BotMissingPermissions):
            await _send(create_error_embed("Bot Missing Permissions", "I don't have the required permissions to execute this command."))
        else:
            # fallback: log or send a generic message
            # print(error)  # uncomment or log properly in production
            await _send(create_error_embed("Error", f"An error occurred: {str(error)}"))

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
