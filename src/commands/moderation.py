import discord
from discord.ext import commands
from discord import app_commands, Member, TextChannel
from datetime import datetime, timedelta, timezone
import asyncio
from utils.database import db
from utils.helpers import (
    create_success_embed, 
    create_error_embed, 
    create_warning_embed,
    parse_duration,
    format_duration,
    extract_user_id_from_mention,
    log_action
)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.muted_role_name = "Muted"
    
    async def get_muted_role(self, guild):
        """Get or create the muted role"""
        muted_role = discord.utils.get(guild.roles, name=self.muted_role_name)
        
        if not muted_role:
            # Create muted role
            muted_role = await guild.create_role(
                name=self.muted_role_name,
                color=discord.Color.dark_gray(),
                reason="Muted role for moderation"
            )
            
            # Set permissions for muted role in all channels
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    await channel.set_permissions(
                        muted_role,
                        send_messages=False,
                        add_reactions=False,
                        create_public_threads=False,
                        create_private_threads=False,
                        send_messages_in_threads=False
                    )
                elif isinstance(channel, discord.VoiceChannel):
                    await channel.set_permissions(
                        muted_role,
                        speak=False,
                        stream=False
                    )
        
        return muted_role

    @commands.command(name='warn', help='Warn a member')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: Member, *, reason: str = "No reason provided"):
        """Warn a member"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = create_error_embed("Permission Denied", "You cannot warn this member!")
            await ctx.send(embed=embed)
            return
        
        if member.bot:
            embed = create_error_embed("Invalid Target", "You cannot warn a bot!")
            await ctx.send(embed=embed)
            return
        
        # Add warning to database
        await db.add_warning(member.id, ctx.author.id, reason)
        
        # Get user's total warnings
        warnings = await db.get_user_warnings(member.id)
        warning_count = len(warnings)
        
        # Create embed
        embed = create_warning_embed(
            "⚠️ Member Warned",
            f"**Member:** {member.mention}\n"
            f"**Moderator:** {ctx.author.mention}\n"
            f"**Reason:** {reason}\n"
            f"**Total Warnings:** {warning_count}"
        )
        
        await ctx.send(embed=embed)
        
        # Try to DM the user
        try:
            dm_embed = create_warning_embed(
                "⚠️ Warning Received",
                f"You have been warned in **{ctx.guild.name}**\n\n"
                f"**Reason:** {reason}\n"
                f"**Moderator:** {ctx.author}\n"
                f"**Total Warnings:** {warning_count}"
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass
        
        # Log action
        await log_action("WARN", member.id, f"Reason: {reason} | Moderator: {ctx.author.id}")

    @commands.command(name='warnings', help='Check warnings for a member')
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx, member: Member):
        """Check warnings for a member"""
        warnings = await db.get_user_warnings(member.id)
        
        if not warnings:
            embed = create_success_embed(
                "No Warnings",
                f"{member.mention} has no warnings."
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"⚠️ Warnings for {member.display_name}",
            color=discord.Color.orange(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        for i, (mod_id, reason, date) in enumerate(warnings[:10], 1):  # Show last 10 warnings
            moderator = self.bot.get_user(mod_id) or "Unknown Moderator"
            warning_date = datetime.fromisoformat(date).strftime("%Y-%m-%d %H:%M")
            
            embed.add_field(
                name=f"Warning #{i}",
                value=f"**Moderator:** {moderator}\n**Reason:** {reason}\n**Date:** {warning_date}",
                inline=False
            )
        
        if len(warnings) > 10:
            embed.set_footer(text=f"Showing 10 of {len(warnings)} warnings")
        
        await ctx.send(embed=embed)

    @commands.command(name='mute', help='Mute a member for a specified duration')
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: Member, duration: str, *, reason: str = "No reason provided"):
        """Mute a member for a specified duration"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = create_error_embed("Permission Denied", "You cannot mute this member!")
            await ctx.send(embed=embed)
            return
        
        if member.bot:
            embed = create_error_embed("Invalid Target", "You cannot mute a bot!")
            await ctx.send(embed=embed)
            return
        
        # Parse duration
        duration_seconds = parse_duration(duration)
        if not duration_seconds:
            embed = create_error_embed(
                "Invalid Duration",
                "Please provide a valid duration (e.g., 1h, 30m, 45s)"
            )
            await ctx.send(embed=embed)
            return
        
        if duration_seconds > 7 * 24 * 3600:  # 7 days max
            embed = create_error_embed("Duration Too Long", "Maximum mute duration is 7 days!")
            await ctx.send(embed=embed)
            return
        
        # Get muted role
        muted_role = await self.get_muted_role(ctx.guild)
        
        # Add muted role
        await member.add_roles(muted_role, reason=f"Muted by {ctx.author}: {reason}")
        
        # Add to database
        await db.add_mute(member.id, duration_seconds // 60, reason, ctx.author.id)
        
        # Create embed
        duration_text = format_duration(duration_seconds)
        embed = create_warning_embed(
            "🔇 Member Muted",
            f"**Member:** {member.mention}\n"
            f"**Duration:** {duration_text}\n"
            f"**Moderator:** {ctx.author.mention}\n"
            f"**Reason:** {reason}"
        )
        
        await ctx.send(embed=embed)
        
        # Try to DM the user
        try:
            dm_embed = create_warning_embed(
                "🔇 You Have Been Muted",
                f"You have been muted in **{ctx.guild.name}**\n\n"
                f"**Duration:** {duration_text}\n"
                f"**Reason:** {reason}\n"
                f"**Moderator:** {ctx.author}"
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass
        
        # Log action
        await log_action("MUTE", member.id, f"Duration: {duration_text} | Reason: {reason} | Moderator: {ctx.author.id}")
        
        # Schedule unmute
        await asyncio.sleep(duration_seconds)
        
        # Check if user is still muted
        if await db.is_user_muted(member.id):
            await self.unmute_user(member, "Automatic unmute (duration expired)")

    @commands.command(name='unmute', help='Unmute a member')
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: Member):
        """Unmute a member"""
        if not await db.is_user_muted(member.id):
            embed = create_error_embed("Not Muted", f"{member.mention} is not muted!")
            await ctx.send(embed=embed)
            return
        
        await self.unmute_user(member, f"Unmuted by {ctx.author}")
        
        embed = create_success_embed(
            "🔊 Member Unmuted",
            f"**Member:** {member.mention}\n"
            f"**Moderator:** {ctx.author.mention}"
        )
        
        await ctx.send(embed=embed)
        
        # Log action
        await log_action("UNMUTE", member.id, f"Moderator: {ctx.author.id}")

    async def unmute_user(self, member: Member, reason: str):
        """Helper function to unmute a user"""
        muted_role = discord.utils.get(member.guild.roles, name=self.muted_role_name)
        
        if muted_role in member.roles:
            await member.remove_roles(muted_role, reason=reason)
        
        await db.remove_mute(member.id)
        
        # Try to DM the user
        try:
            embed = create_success_embed(
                "🔊 You Have Been Unmuted",
                f"You have been unmuted in **{member.guild.name}**"
            )
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.command(name='clear', aliases=['purge'], help='Clear messages from a channel')
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """Clear messages from a channel"""
        if amount <= 0:
            embed = create_error_embed("Invalid Amount", "Amount must be greater than 0!")
            await ctx.send(embed=embed)
            return
        
        if amount > 100:
            embed = create_error_embed("Amount Too Large", "Cannot clear more than 100 messages at once!")
            await ctx.send(embed=embed)
            return
        
        # Delete the command message
        await ctx.message.delete()
        
        # Purge messages
        deleted = await ctx.channel.purge(limit=amount)
        
        # Send confirmation
        embed = create_success_embed(
            "🗑️ Messages Cleared",
            f"Cleared **{len(deleted)}** messages from {ctx.channel.mention}"
        )
        
        confirmation = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await confirmation.delete()
        
        # Log action
        await log_action("CLEAR", ctx.author.id, f"Cleared {len(deleted)} messages in {ctx.channel.name}")

    @commands.command(name='timeout', help='Timeout a member using Discord\'s built-in timeout')
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: Member, duration: str, *, reason: str = "No reason provided"):
        """Timeout a member using Discord's built-in timeout feature"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = create_error_embed("Permission Denied", "You cannot timeout this member!")
            await ctx.send(embed=embed)
            return
        
        if member.bot:
            embed = create_error_embed("Invalid Target", "You cannot timeout a bot!")
            await ctx.send(embed=embed)
            return
        
        # Parse duration
        duration_seconds = parse_duration(duration)
        if not duration_seconds:
            embed = create_error_embed(
                "Invalid Duration",
                "Please provide a valid duration (e.g., 1h, 30m, 45s)"
            )
            await ctx.send(embed=embed)
            return
        
        if duration_seconds > 28 * 24 * 3600:  # 28 days max (Discord limit)
            embed = create_error_embed("Duration Too Long", "Maximum timeout duration is 28 days!")
            await ctx.send(embed=embed)
            return
        
        # Calculate timeout until
        timeout_until = datetime.now(tz=timezone.utc) + timedelta(seconds=duration_seconds)
        
        try:
            await member.timeout(timeout_until, reason=f"{ctx.author}: {reason}")
            
            duration_text = format_duration(duration_seconds)
            embed = create_warning_embed(
                "⏰ Member Timed Out",
                f"**Member:** {member.mention}\n"
                f"**Duration:** {duration_text}\n"
                f"**Moderator:** {ctx.author.mention}\n"
                f"**Reason:** {reason}"
            )
            
            await ctx.send(embed=embed)
            
            # Try to DM the user
            try:
                dm_embed = create_warning_embed(
                    "⏰ You Have Been Timed Out",
                    f"You have been timed out in **{ctx.guild.name}**\n\n"
                    f"**Duration:** {duration_text}\n"
                    f"**Reason:** {reason}\n"
                    f"**Moderator:** {ctx.author}"
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass
            
            # Log action
            await log_action("TIMEOUT", member.id, f"Duration: {duration_text} | Reason: {reason} | Moderator: {ctx.author.id}")
            
        except discord.Forbidden:
            embed = create_error_embed("Permission Error", "I don't have permission to timeout this member!")
            await ctx.send(embed=embed)

    @commands.command(name='untimeout', help='Remove timeout from a member')
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: Member):
        """Remove timeout from a member"""
        if not member.timed_out_until:
            embed = create_error_embed("Not Timed Out", f"{member.mention} is not timed out!")
            await ctx.send(embed=embed)
            return
        
        try:
            await member.timeout(None, reason=f"Timeout removed by {ctx.author}")
            
            embed = create_success_embed(
                "⏰ Timeout Removed",
                f"**Member:** {member.mention}\n"
                f"**Moderator:** {ctx.author.mention}"
            )
            
            await ctx.send(embed=embed)
            
            # Log action
            await log_action("UNTIMEOUT", member.id, f"Moderator: {ctx.author.id}")
            
        except discord.Forbidden:
            embed = create_error_embed("Permission Error", "I don't have permission to remove timeout from this member!")
            await ctx.send(embed=embed)

    @mute.error
    @unmute.error
    @warn.error
    @clear.error
    @timeout.error
    @untimeout.error
    async def moderation_error(self, ctx, error):
        """Error handler for moderation commands"""
        if isinstance(error, commands.MissingPermissions):
            embed = create_error_embed(
                "Missing Permissions",
                "You don't have permission to use this command!"
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MemberNotFound):
            embed = create_error_embed(
                "Member Not Found",
                "Could not find the specified member!"
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = create_error_embed(
                "Missing Argument",
                f"Missing required argument: `{error.param}`"
            )
            await ctx.send(embed=embed)

    # Slash Commands
    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(member="The member to warn", reason="Reason for the warning")
    @app_commands.default_permissions(kick_members=True)
    async def slash_warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Slash command version of warn"""
        if not interaction.user.guild_permissions.kick_members:
            embed = create_error_embed("Permission Denied", "You don't have permission to warn members!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            embed = create_error_embed("Permission Denied", "You cannot warn members with equal or higher roles!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Add warning to database
        await db.add_warning(member.id, interaction.user.id, reason)
        
        # Get warning count
        warning_count = await db.get_warning_count(member.id)
        
        # Create embed for public announcement
        embed = create_warning_embed(
            "⚠️ Member Warned",
            f"**Member:** {member.mention}\n"
            f"**Warned by:** {interaction.user.mention}\n"
            f"**Reason:** {reason}\n"
            f"**Total warnings:** {warning_count}"
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Try to DM the user
        try:
            dm_embed = create_warning_embed(
                f"⚠️ Warning from {interaction.guild.name}",
                f"**Reason:** {reason}\n"
                f"**Total warnings:** {warning_count}\n\n"
                "Please review the server rules to avoid further warnings."
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="The member to kick", reason="Reason for kicking")
    @app_commands.default_permissions(kick_members=True)
    async def slash_kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Slash command version of kick"""
        if not interaction.user.guild_permissions.kick_members:
            embed = create_error_embed("Permission Denied", "You don't have permission to kick members!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            embed = create_error_embed("Permission Denied", "You cannot kick members with equal or higher roles!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Try to DM before kicking
        try:
            dm_embed = create_warning_embed(
                f"🦶 Kicked from {interaction.guild.name}",
                f"**Reason:** {reason}\n\n"
                "You have been kicked from the server. You may rejoin if you have an invite link."
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass
        
        # Kick the member
        await member.kick(reason=reason)
        
        # Send confirmation
        embed = create_success_embed(
            "👢 Member Kicked",
            f"**Member:** {member}\n"
            f"**Kicked by:** {interaction.user.mention}\n"
            f"**Reason:** {reason}"
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="The member to ban", reason="Reason for banning", delete_days="Days of messages to delete (0-7)")
    @app_commands.default_permissions(ban_members=True)
    async def slash_ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided", delete_days: int = 0):
        """Slash command version of ban"""
        if not interaction.user.guild_permissions.ban_members:
            embed = create_error_embed("Permission Denied", "You don't have permission to ban members!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            embed = create_error_embed("Permission Denied", "You cannot ban members with equal or higher roles!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Validate delete_days
        delete_days = max(0, min(7, delete_days))
        
        # Try to DM before banning
        try:
            dm_embed = create_error_embed(
                f"🔨 Banned from {interaction.guild.name}",
                f"**Reason:** {reason}\n\n"
                "You have been permanently banned from the server."
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass
        
        # Ban the member
        await member.ban(reason=reason, delete_message_days=delete_days)
        
        # Send confirmation
        embed = create_success_embed(
            "🔨 Member Banned",
            f"**Member:** {member}\n"
            f"**Banned by:** {interaction.user.mention}\n"
            f"**Reason:** {reason}\n"
            f"**Messages deleted:** {delete_days} days"
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.describe(member="The member to timeout", duration="Duration in minutes", reason="Reason for timeout")
    @app_commands.default_permissions(moderate_members=True)
    async def slash_timeout(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):
        """Slash command version of timeout"""
        if not interaction.user.guild_permissions.moderate_members:
            embed = create_error_embed("Permission Denied", "You don't have permission to timeout members!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            embed = create_error_embed("Permission Denied", "You cannot timeout members with equal or higher roles!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Validate duration (1 minute to 28 days)
        duration = max(1, min(40320, duration))  # 28 days = 40320 minutes
        timeout_until = discord.utils.utcnow() + timedelta(minutes=duration)
        
        # Apply timeout
        await member.timeout(timeout_until, reason=reason)
        
        # Send confirmation
        embed = create_warning_embed(
            "⏰ Member Timed Out",
            f"**Member:** {member.mention}\n"
            f"**Timed out by:** {interaction.user.mention}\n"
            f"**Duration:** {duration} minutes\n"
            f"**Reason:** {reason}\n"
            f"**Timeout ends:** <t:{int(timeout_until.timestamp())}:F>"
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))