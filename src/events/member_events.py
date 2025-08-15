import os
from datetime import datetime, timezone
import discord
from discord.ext import commands
from utils.json_store import add_or_update_user
from utils.helpers import log_action

class MemberEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle member join: track user and post welcome (if channel configured)."""
        await add_or_update_user(member.id, str(member))
        joins_channel_id = int(os.getenv('JOINS_LEAVES_CHANNEL_ID', 0))
        if joins_channel_id:
            channel = self.bot.get_channel(joins_channel_id)
            if channel:
                embed = discord.Embed(
                    title="👋 Welcome!",
                    description=(
                        f"{member.mention} joined **{member.guild.name}**!\n"
                        "Share what you're building and have fun coding."
                    ),
                    color=discord.Color.green(),
                    timestamp=datetime.now(tz=timezone.utc)
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Member #{len(member.guild.members)} • Enjoy your stay")
                await channel.send(embed=embed)
        await log_action("MEMBER_JOIN", member.id, f"Username: {member}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Handle member leaving the guild."""
        joins_channel_id = int(os.getenv('JOINS_LEAVES_CHANNEL_ID', 0))
        if joins_channel_id:
            channel = self.bot.get_channel(joins_channel_id)
            if channel:
                embed = discord.Embed(
                    title="👋 Member Left",
                    description=f"{member.display_name} has left the server.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(tz=timezone.utc)
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Members remaining: {len(member.guild.members)}")
                await channel.send(embed=embed)
        await log_action("MEMBER_LEAVE", member.id, f"Username: {member}")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Handle member updates (role changes, nickname changes, etc.)"""
        # Log significant changes to server logs channel
        server_logs_id = int(os.getenv('SERVER_LOGS_CHANNEL_ID', 0))
        if not server_logs_id:
            return
            
        log_channel = self.bot.get_channel(server_logs_id)
        if not log_channel:
            return

        # Check for role changes
        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            
            if added_roles or removed_roles:
                embed = discord.Embed(
                    title="🔄 Member Role Update",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed.set_thumbnail(url=after.display_avatar.url)
                
                embed.add_field(
                    name="Member",
                    value=f"{after.mention} ({after.id})",
                    inline=False
                )
                
                if added_roles:
                    roles_text = ", ".join([role.mention for role in added_roles])
                    embed.add_field(
                        name="➕ Roles Added",
                        value=roles_text,
                        inline=False
                    )
                
                if removed_roles:
                    roles_text = ", ".join([role.name for role in removed_roles])
                    embed.add_field(
                        name="➖ Roles Removed", 
                        value=roles_text,
                        inline=False
                    )
                
                await log_channel.send(embed=embed)
        
        # Check for nickname changes
        if before.nick != after.nick:
            embed = discord.Embed(
                title="📝 Nickname Update",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            
            embed.add_field(
                name="Member",
                value=f"{after.mention} ({after.id})",
                inline=False
            )
            embed.add_field(
                name="Before",
                value=before.nick or before.name,
                inline=True
            )
            embed.add_field(
                name="After",
                value=after.nick or after.name,
                inline=True
            )
            
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        """Handle user updates (username, avatar changes)"""
        # Only log for members in our guild
        guild_id = int(os.getenv('GUILD_ID', 0))
        if not guild_id:
            return
            
        guild = self.bot.get_guild(guild_id)
        if not guild or not guild.get_member(after.id):
            return
        
        server_logs_id = int(os.getenv('SERVER_LOGS_CHANNEL_ID', 0))
        if not server_logs_id:
            return
            
        log_channel = self.bot.get_channel(server_logs_id)
        if not log_channel:
            return

        # Check for username changes
        if before.name != after.name:
            embed = discord.Embed(
                title="👤 Username Update",
                color=discord.Color.purple(),
                timestamp=datetime.now(tz=timezone.utc)
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            
            embed.add_field(
                name="User",
                value=f"{after.mention} ({after.id})",
                inline=False
            )
            embed.add_field(
                name="Before",
                value=before.name,
                inline=True
            )
            embed.add_field(
                name="After",
                value=after.name,
                inline=True
            )
            
            await log_channel.send(embed=embed)
            
            # Update cached username
            await add_or_update_user(after.id, str(after))

        # Check for avatar changes
        if before.avatar != after.avatar:
            embed = discord.Embed(
                title="🖼️ Avatar Update",
                description=f"{after.mention} changed their avatar",
                color=discord.Color.green(),
                timestamp=datetime.now(tz=timezone.utc)
            )
            
            if before.avatar:
                embed.set_thumbnail(url=before.display_avatar.url)
                embed.add_field(name="Before", value="[Old Avatar](before.display_avatar.url)", inline=True)
            
            if after.avatar:
                embed.set_image(url=after.display_avatar.url)
                embed.add_field(name="After", value="[New Avatar](after.display_avatar.url)", inline=True)
            
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Handle member ban events"""
        server_logs_id = int(os.getenv('SERVER_LOGS_CHANNEL_ID', 0))
        if server_logs_id:
            log_channel = self.bot.get_channel(server_logs_id)
            if log_channel:
                embed = discord.Embed(
                    title="🔨 Member Banned",
                    description=f"**{user}** ({user.id}) has been banned from the server.",
                    color=discord.Color.dark_red(),
                    timestamp=datetime.now(tz=timezone.utc)
                )
                embed.set_thumbnail(url=user.display_avatar.url)
                
                await log_channel.send(embed=embed)
        
        await log_action("MEMBER_BAN", user.id, f"Username: {user}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Handle member unban events"""
        server_logs_id = int(os.getenv('SERVER_LOGS_CHANNEL_ID', 0))
        if server_logs_id:
            log_channel = self.bot.get_channel(server_logs_id)
            if log_channel:
                embed = discord.Embed(
                    title="🔓 Member Unbanned",
                    description=f"**{user}** ({user.id}) has been unbanned from the server.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(tz=timezone.utc)
                )
                embed.set_thumbnail(url=user.display_avatar.url)
                
                await log_channel.send(embed=embed)
        
        await log_action("MEMBER_UNBAN", user.id, f"Username: {user}")

async def setup(bot):
    await bot.add_cog(MemberEvents(bot))