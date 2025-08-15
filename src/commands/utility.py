import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import re
from datetime import datetime, timedelta, timezone
from utils.database import db
from utils.helpers import create_success_embed, create_error_embed, create_info_embed

class UtilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="serverinfo", description="Get information about the server")
    async def server_info(self, interaction: discord.Interaction):
        """Display server information"""
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"📊 {guild.name} Server Info",
            color=discord.Color.blue(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Basic info
        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
        embed.add_field(name="📅 Created", value=guild.created_at.strftime("%B %d, %Y"), inline=True)
        
        # Member counts
        total_members = guild.member_count
        bots = sum(1 for member in guild.members if member.bot)
        humans = total_members - bots
        
        embed.add_field(name="👥 Total Members", value=total_members, inline=True)
        embed.add_field(name="👨‍👩‍👧‍👦 Humans", value=humans, inline=True)
        embed.add_field(name="🤖 Bots", value=bots, inline=True)
        
        # Channel counts
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(name="💬 Text Channels", value=text_channels, inline=True)
        embed.add_field(name="🔊 Voice Channels", value=voice_channels, inline=True)
        embed.add_field(name="📁 Categories", value=categories, inline=True)
        
        # Other info
        embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="😀 Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="⚡ Boost Level", value=guild.premium_tier, inline=True)
        
        if guild.description:
            embed.add_field(name="📝 Description", value=guild.description, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Get information about a user")
    @app_commands.describe(member="The member to get info about (defaults to you)")
    async def user_info(self, interaction: discord.Interaction, member: discord.Member = None):
        """Display user information"""
        if member is None:
            member = interaction.user
        
        embed = discord.Embed(
            title=f"👤 {member.display_name}",
            color=member.color if member.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Basic info
        embed.add_field(name="🏷️ Username", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="🆔 User ID", value=member.id, inline=True)
        embed.add_field(name="🤖 Bot", value="Yes" if member.bot else "No", inline=True)
        
        # Dates
        embed.add_field(name="📅 Account Created", value=member.created_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="📥 Joined Server", value=member.joined_at.strftime("%B %d, %Y") if member.joined_at else "Unknown", inline=True)
        
        # Status
        status_emojis = {
            discord.Status.online: "🟢 Online",
            discord.Status.idle: "🟡 Idle", 
            discord.Status.dnd: "🔴 Do Not Disturb",
            discord.Status.offline: "⚫ Offline"
        }
        embed.add_field(name="📶 Status", value=status_emojis.get(member.status, "❓ Unknown"), inline=True)
        
        # Roles (excluding @everyone)
        roles = [role.mention for role in member.roles[1:]]
        if roles:
            roles_text = ", ".join(roles[:10])  # Limit to first 10 roles
            if len(member.roles) > 11:
                roles_text += f" (+{len(member.roles) - 11} more)"
            embed.add_field(name="🎭 Roles", value=roles_text, inline=False)
        
        # Permissions
        if member.guild_permissions.administrator:
            embed.add_field(name="⚡ Permissions", value="Administrator", inline=True)
        elif member.guild_permissions.manage_guild:
            embed.add_field(name="⚡ Permissions", value="Manage Server", inline=True)
        elif member.guild_permissions.manage_messages:
            embed.add_field(name="⚡ Permissions", value="Moderator", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Get a user's avatar")
    @app_commands.describe(member="The member to get avatar of (defaults to you)")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        """Display user's avatar"""
        if member is None:
            member = interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ {member.display_name}'s Avatar",
            color=member.color if member.color != discord.Color.default() else discord.Color.blue()
        )
        embed.set_image(url=member.display_avatar.url)
        embed.add_field(name="🔗 Avatar URL", value=f"[Click here]({member.display_avatar.url})", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="reminder", description="Set a reminder")
    @app_commands.describe(
        time="Time until reminder (e.g., 1h, 30m, 2d)",
        message="What to remind you about"
    )
    async def reminder(self, interaction: discord.Interaction, time: str, message: str):
        """Set a personal reminder"""
        # Parse time
        time_regex = re.compile(r'(\d+)([smhd])')
        matches = time_regex.findall(time.lower())
        
        if not matches:
            await interaction.response.send_message(
                "❌ Invalid time format! Use: `1h` (hours), `30m` (minutes), `2d` (days), `45s` (seconds)",
                ephemeral=True
            )
            return
        
        total_seconds = 0
        for amount, unit in matches:
            amount = int(amount)
            if unit == 's':
                total_seconds += amount
            elif unit == 'm':
                total_seconds += amount * 60
            elif unit == 'h':
                total_seconds += amount * 3600
            elif unit == 'd':
                total_seconds += amount * 86400
        
        if total_seconds < 10:
            await interaction.response.send_message("❌ Minimum reminder time is 10 seconds!", ephemeral=True)
            return
        
        if total_seconds > 7 * 86400:  # 7 days
            await interaction.response.send_message("❌ Maximum reminder time is 7 days!", ephemeral=True)
            return
        
        # Set reminder
        reminder_time = datetime.now(tz=timezone.utc) + timedelta(seconds=total_seconds)
        
        embed = create_success_embed(
            "⏰ Reminder Set!",
            f"I'll remind you about: **{message}**\n"
            f"⏱️ In: **{time}**\n"
            f"📅 At: <t:{int(reminder_time.timestamp())}:F>"
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Wait and send reminder
        await asyncio.sleep(total_seconds)
        
        reminder_embed = discord.Embed(
            title="⏰ Reminder!",
            description=message,
            color=discord.Color.orange(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        try:
            await interaction.user.send(embed=reminder_embed)
        except discord.Forbidden:
            # If DM fails, try to send in the channel
            try:
                await interaction.followup.send(f"{interaction.user.mention}", embed=reminder_embed)
            except:
                pass

    @app_commands.command(name="weather", description="Get weather information")
    @app_commands.describe(location="City name or location")
    async def weather(self, interaction: discord.Interaction, location: str):
        """Get weather information (placeholder for API integration)"""
        # This is a placeholder - you would integrate with a weather API
        embed = create_info_embed(
            "🌤️ Weather Command",
            f"Weather feature for **{location}** is coming soon!\n\n"
            "To enable this feature:\n"
            "1. Get an API key from OpenWeatherMap\n"
            "2. Add `WEATHER_API_KEY` to your .env file\n"
            "3. The bot will automatically fetch real weather data!"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="afk", description="Set your AFK status")
    @app_commands.describe(reason="Reason for being AFK (optional)")
    async def afk(self, interaction: discord.Interaction, reason: str = "No reason provided"):
        """Set AFK status"""
        # Store AFK status in database
        await db.set_user_afk(interaction.user.id, reason, datetime.now(tz=timezone.utc).isoformat())
        
        embed = create_success_embed(
            "😴 AFK Status Set",
            f"You are now AFK: **{reason}**\n"
            "I'll notify others when they mention you!"
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name='roleinfo', help='Get information about a role')
    async def role_info(self, ctx, *, role: discord.Role):
        """Display role information"""
        embed = discord.Embed(
            title=f"🎭 Role: {role.name}",
            color=role.color if role.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        embed.add_field(name="🆔 Role ID", value=role.id, inline=True)
        embed.add_field(name="📅 Created", value=role.created_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="👥 Members", value=len(role.members), inline=True)
        embed.add_field(name="🎨 Color", value=str(role.color), inline=True)
        embed.add_field(name="📌 Position", value=role.position, inline=True)
        embed.add_field(name="🔗 Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        embed.add_field(name="👁️ Display Separately", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="🤖 Bot Role", value="Yes" if role.is_bot_managed() else "No", inline=True)
        
        # Permissions
        if role.permissions.administrator:
            embed.add_field(name="⚡ Key Permissions", value="Administrator (All Permissions)", inline=False)
        else:
            key_perms = []
            perm_checks = [
                ("Manage Server", role.permissions.manage_guild),
                ("Manage Channels", role.permissions.manage_channels),
                ("Manage Roles", role.permissions.manage_roles),
                ("Kick Members", role.permissions.kick_members),
                ("Ban Members", role.permissions.ban_members),
                ("Manage Messages", role.permissions.manage_messages)
            ]
            
            key_perms = [name for name, has_perm in perm_checks if has_perm]
            
            if key_perms:
                embed.add_field(name="⚡ Key Permissions", value=", ".join(key_perms), inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))
