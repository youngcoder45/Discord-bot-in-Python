import logging
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
        # I assume codeverse is a configured root logger for the bot
        self.logger = logging.getLogger("codeverse").getChild(__name__)

    @commands.hybrid_command(name="serverinfo", description="Get information about the server")
    @commands.guild_only()
    async def server_info(self, ctx: commands.Context):
        """Display server information"""
        await ctx.defer()
        guild: discord.Guild | None = ctx.guild

        if guild is None:
            # This should never happen and is here purely to shut pyright up
            return
        
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
        total_members = 0
        bots = 0
        humans = 0
        for member in guild.members:
            if member.bot:
                bots += 1
            else:
                humans += 1
            total_members += 0
        
        bans = len([i async for i in guild.bans(limit=1000)]) # Potentially expensive, if we hit rate limits often, add a cache
        
        embed.add_field(name="👥 Total Members", value=total_members, inline=True)
        embed.add_field(name="👨‍👩‍👧‍👦 Humans", value=humans, inline=True)
        embed.add_field(name="🤖 Bots", value=bots, inline=True)
        embed.add_field(name="⛔ Bans", value="999+" if bans > 999 else bans, inline=True)
        
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
        
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="userinfo", description="Get information about a user")
    @app_commands.describe(member="The member to get info about (defaults to you)")
    async def user_info(self, ctx: commands.Context, member: discord.Member | None = None):
        """Display user information"""
        user: discord.User | discord.Member = member or ctx.author
            
        embed = discord.Embed(
            title=f"👤 {user.display_name}",
            color=user.color if user.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Basic info
        embed.add_field(name="🏷️ Username", value=f"{user.name}#{user.discriminator}" if user.discriminator else user.name, inline=True)
        embed.add_field(name="🆔 User ID", value=user.id, inline=True)
        embed.add_field(name="🤖 Bot", value="Yes" if user.bot else "No", inline=True)
        
        # Dates
        embed.add_field(name="📅 Account Created", value=user.created_at.strftime("%B %d, %Y"), inline=True)
        if isinstance(user, discord.Member):
            # Only applicable when the command is ran in a guild
            embed.add_field(name="📥 Joined Server", value=user.joined_at.strftime("%B %d, %Y") if user.joined_at else "Unknown", inline=True)
        
        # Status
        status_emojis = {
            discord.Status.online: "🟢 Online",
            discord.Status.idle: "🟡 Idle", 
            discord.Status.dnd: "🔴 Do Not Disturb",
            discord.Status.offline: "⚫ Offline"
        }
        if isinstance(user, discord.Member):
            embed.add_field(name="📶 Status", value=status_emojis.get(user.status, "❓ Unknown"), inline=True)
        embed.add_field(name="📶 Status", value="❓ Unknown", inline=True)
        
        if isinstance(user, discord.Member):
            # Roles (excluding @everyone)
            roles = [role.mention for role in user.roles[1:]]
            if roles:
                roles_text = ", ".join(roles[:10])  # Limit to first 10 roles
                if len(user.roles) > 11:
                    roles_text += f" (+{len(user.roles) - 11} more)"
                embed.add_field(name="🎭 Roles", value=roles_text, inline=False)
        
            # Permissions
            if user.guild_permissions.administrator:
                embed.add_field(name="⚡ Permissions", value="Administrator", inline=True)
            elif user.guild_permissions.manage_guild:
                embed.add_field(name="⚡ Permissions", value="Manage Server", inline=True)
            elif user.guild_permissions.manage_messages:
                embed.add_field(name="⚡ Permissions", value="Moderator", inline=True)
        
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="avatar", description="Get a user's avatar")
    @app_commands.describe(member="The member to get avatar of (defaults to you)")
    async def avatar(self, ctx: commands.Context, member: discord.Member | None = None):
        """Display user's avatar"""
        user: discord.User | discord.Member = member or ctx.author
        
        embed = discord.Embed(
            title=f"🖼️ {user.display_name}'s Avatar",
            color=user.color if user.color != discord.Color.default() else discord.Color.blue()
        )
        embed.set_image(url=user.display_avatar.url)
        embed.add_field(name="🔗 Avatar URL", value=f"[Click here]({user.display_avatar.url})", inline=False)
        
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="reminder", description="Set a reminder")
    @app_commands.describe(
        time="Time until reminder (e.g., 1h, 30m, 2d)",
        message="What to remind you about"
    )
    async def reminder(self, ctx: commands.Context, time: str, message: str):
        """Set a personal reminder"""
        # Parse time
        time_regex = re.compile(r'(\d+)([smhd])')
        matches = time_regex.findall(time.lower())
        
        if not matches:
            await ctx.reply(
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
            await ctx.reply("❌ Minimum reminder time is 10 seconds!", ephemeral=True)
            return
        
        if total_seconds > 7 * 86400:  # 7 days
            await ctx.reply("❌ Maximum reminder time is 7 days!", ephemeral=True)
            return
        
        # Set reminder
        reminder_time = datetime.now(tz=timezone.utc) + timedelta(seconds=total_seconds)
        
        embed = create_success_embed(
            "⏰ Reminder Set!",
            f"I'll remind you about: **{message}**\n"
            f"⏱️ In: **{time}**\n"
            f"📅 At: <t:{int(reminder_time.timestamp())}:F>"
        )
        
        await ctx.reply(embed=embed, ephemeral=True)
        
        # TODO: This sucks. Save reminders to DB and have a background task check for passed reminders or reminders that are about to expire.
        # The way this is done right now will throw away all reminders when a restart happens.

        # Wait and send reminder
        await asyncio.sleep(total_seconds)
        
        reminder_embed = discord.Embed(
            title="⏰ Reminder!",
            description=message,
            color=discord.Color.orange(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        try:
            await ctx.author.send(embed=reminder_embed)
        except discord.Forbidden:
            # If DM fails, try to send in the channel
            try:
                await ctx.channel.send(f"{ctx.author.mention}", embed=reminder_embed)
            except (discord.Forbidden, discord.NotFound):
                self.logger.warning(f"Failed to send reminder to {ctx.author} (Requested in {ctx.channel}) due to either missing permissions or the channel being deleted. Reminder will be discarded.")

    @commands.hybrid_command(name="weather", description="Get weather information")
    @app_commands.describe(location="City name or location")
    async def weather(self, ctx: commands.Context, location: str):
        """Get weather information (placeholder for API integration)"""
        # This is a placeholder - you would integrate with a weather API
        embed = create_info_embed(
            "🌤️ Weather Command",
            f"Weather feature for **{location}** is coming soon!\n\n"
            "To enable this feature once it is implemented:\n"
            "1. Get an API key from OpenWeatherMap\n"
            "2. Add `WEATHER_API_KEY` to your .env file\n"
            "3. The bot will automatically fetch real weather data!"
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="afk", description="Set your AFK status")
    @app_commands.describe(reason="Reason for being AFK (optional)")
    async def afk(self, ctx: commands.Context, reason: str = "No reason provided"):
        """Set AFK status"""
        await ctx.defer(ephemeral=True)
        # Store AFK status in database
        await db.set_user_afk(ctx.author.id, reason, datetime.now(tz=timezone.utc).isoformat())
        
        embed = create_success_embed(
            "😴 AFK Status Set",
            f"You are now AFK: **{reason}**\n"
            "I'll notify others when they mention you!"
        )
        
        await ctx.reply(embed=embed, ephemeral=True)

    @commands.hybrid_command(name='roleinfo', help='Get information about a role')
    @commands.guild_only()
    @app_commands.describe(role='The role to get information about')
    async def role_info(self, ctx, role: discord.Role):
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
