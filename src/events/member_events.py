import os
from datetime import datetime, timezone
import discord
from discord.ext import commands
from discord import app_commands
from utils.json_store import add_or_update_user
from utils.helpers import log_action  # Keep for backward compatibility
import asyncio
import aiosqlite

class MemberEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Store bot welcome messages with their message IDs for auto-deletion
        self.bot_welcome_messages = {}  # {user_id: message_id}
        self.db_path = "data/member_events.db"
        
    async def is_staff_member(self, member: discord.Member) -> bool:
        """Check if member is a staff member using staff-shifts module logic"""
        if not member.guild:
            return False
            
        # Get staff shifts cog to check staff status
        staff_shifts_cog = self.bot.get_cog('StaffShifts')
        if not staff_shifts_cog:
            return False
            
        try:
            # Get staff settings from the staff shifts service
            settings = await staff_shifts_cog.service.get_settings(member.guild.id)
            
            # Check if user has any of the configured staff roles
            user_role_ids = [role.id for role in member.roles]
            return any(role_id in settings.staff_role_ids for role_id in user_role_ids)
        except:
            return False

    async def cog_load(self):
        """Initialize the database when the cog loads"""
        await self.init_database()
    
    async def init_database(self):
        """Initialize the member events database"""
        async with aiosqlite.connect(self.db_path) as db:
            # Welcome configuration table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS welcome_config (
                    guild_id INTEGER PRIMARY KEY,
                    welcome_enabled BOOLEAN DEFAULT 1,
                    welcome_channel_id INTEGER
                )
            """)
            await db.commit()

    async def get_welcome_enabled(self, guild_id: int) -> bool:
        """Get whether welcome messages are enabled for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT welcome_enabled FROM welcome_config 
                WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else True  # Default to enabled

    async def set_welcome_enabled(self, guild_id: int, enabled: bool):
        """Set whether welcome messages are enabled for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO welcome_config (guild_id, welcome_enabled)
                VALUES (?, ?)
            """, (guild_id, enabled))
            await db.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle member join: track user and send welcome message."""
        await add_or_update_user(member.id, str(member))
        # Logging now handled by centralized logging system
        
        # Send welcome message
        await self.send_welcome_message(member)
        
    async def send_welcome_message(self, member: discord.Member):
        """Send professional welcome message to new member"""
        # Check if welcome messages are enabled for this guild
        if not await self.get_welcome_enabled(member.guild.id):
            return
            
        # Check if this is the correct guild
        guild_id = int(os.getenv('GUILD_ID', 0))
        if not guild_id or member.guild.id != guild_id:
            return
            
        # Get welcome channel
        welcome_channel_id = 1263070188589547541  # The specified channel ID
        welcome_channel = self.bot.get_channel(welcome_channel_id)
        if not welcome_channel:
            return
            
        # Create professional welcome message (no embeds, no emojis)
        welcome_text = (
            f"Welcome {member.mention} to The CodeVerse Hub. "
            f"Please introduce yourself here and learn about our awesome channels and cool roles from "
            f"https://discord.com/channels/1263067254153805905/1263070845098655744 "
            f"and read our rules at "
            f"https://discord.com/channels/1263067254153805905/1263069602867445761.\n\n"
            f"We are happy to have you here!"
        )
        
        try:
            # Send the welcome message
            welcome_msg = await welcome_channel.send(welcome_text)
            
            # Store the message ID for potential auto-deletion
            self.bot_welcome_messages[member.id] = welcome_msg.id
            
            # Log the welcome message
            await log_action("WELCOME_SENT", member.id, f"Welcome message sent to {member}")
            
        except discord.Forbidden:
            print(f"❌ No permission to send welcome message in channel {welcome_channel_id}")
        except Exception as e:
            print(f"❌ Error sending welcome message: {e}")

    @commands.hybrid_group(name="welcome", description="Manage welcome message settings")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def welcome(self, ctx: commands.Context):
        """Main welcome command group"""
        assert ctx.guild is not None, "This command can only be used in a guild"
        if ctx.invoked_subcommand is None:
            # Show current welcome settings
            enabled = await self.get_welcome_enabled(ctx.guild.id)
            embed = discord.Embed(
                title="Welcome Message Settings",
                color=0x3498DB
            )
            embed.add_field(
                name="Status",
                value=f"Welcome messages are **{'enabled' if enabled else 'disabled'}**",
                inline=False
            )
            embed.add_field(
                name="Commands",
                value="• `/welcome toggle` - Toggle welcome messages on/off\n• `/welcome status` - Show current settings",
                inline=False
            )
            await ctx.reply(embed=embed)

    @welcome.command(name="toggle", description="Toggle welcome messages on/off")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def toggle_welcome(self, ctx: commands.Context):
        """Toggle welcome messages on or off"""
        assert ctx.guild is not None, "This command can only be used in a guild"
        current_status = await self.get_welcome_enabled(ctx.guild.id)
        new_status = not current_status
        
        await self.set_welcome_enabled(ctx.guild.id, new_status)
        
        embed = discord.Embed(
            title="Welcome Messages Updated",
            color=0x00FF00 if new_status else 0xFF0000
        )
        embed.add_field(
            name="Status",
            value=f"Welcome messages are now **{'enabled' if new_status else 'disabled'}**",
            inline=False
        )
        embed.set_footer(text=f"Changed by {ctx.author.display_name}")
        
        await ctx.reply(embed=embed)

    @welcome.command(name="status", description="Show welcome message status")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def welcome_status(self, ctx: commands.Context):
        """Show current welcome message settings"""
        assert ctx.guild is not None, "This command can only be used in a guild"
        enabled = await self.get_welcome_enabled(ctx.guild.id)
        
        embed = discord.Embed(
            title="Welcome Message Status",
            color=0x3498DB
        )
        embed.add_field(
            name="Welcome Messages",
            value=f"**{'Enabled' if enabled else 'Disabled'}**",
            inline=True
        )
        embed.add_field(
            name="Channel",
            value=f"<#{1263070188589547541}>",
            inline=True
        )
        
        await ctx.reply(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Monitor for staff welcome messages to auto-delete bot welcome"""
        # Ignore bot messages
        if message.author.bot:
            return
            
        # Only check in the welcome channel
        welcome_channel_id = 1263070188589547541
        if message.channel.id != welcome_channel_id:
            return
            
        # Check if author is staff
        if not isinstance(message.author, discord.Member):
            return
            
        is_staff = await self.is_staff_member(message.author)
        if not is_staff:
            return
            
        # Check if this might be a welcome message to a new member
        # Look for mentions in the message
        if not message.mentions:
            return
            
        # For each mentioned user, check if we have a bot welcome message to delete
        for mentioned_user in message.mentions:
            if mentioned_user.id in self.bot_welcome_messages:
                try:
                    # Get the bot welcome message
                    bot_message_id = self.bot_welcome_messages[mentioned_user.id]
                    bot_message = await message.channel.fetch_message(bot_message_id)
                    
                    # Delete the bot welcome message
                    await bot_message.delete()
                    
                    # Remove from tracking
                    del self.bot_welcome_messages[mentioned_user.id]
                    
                    # Log the auto-deletion
                    await log_action(
                        "WELCOME_AUTO_DELETE", 
                        mentioned_user.id, 
                        f"Bot welcome deleted after staff welcome by {message.author}"
                    )
                    
                except discord.NotFound:
                    # Message was already deleted, just remove from tracking
                    if mentioned_user.id in self.bot_welcome_messages:
                        del self.bot_welcome_messages[mentioned_user.id]
                except Exception as e:
                    print(f"❌ Error deleting bot welcome message: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Handle member leaving the guild (logging only)."""
        # Logging now handled by centralized logging system
        
        # Clean up any stored welcome message references
        if member.id in self.bot_welcome_messages:
            del self.bot_welcome_messages[member.id]

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Handle member updates (role changes, nickname changes, etc.)"""
        # Nothing to do here - role changes now handled by the centralized logging system
        # This method is kept for future compatibility
        
        # Check for nickname changes - removed per user request
        # if before.nick != after.nick:
        #     embed = discord.Embed(
        #         title="📝 Nickname Update",
        #         color=discord.Color.orange(),
        #         timestamp=datetime.utcnow()
        #     )
        #     embed.set_thumbnail(url=after.display_avatar.url)
        #     
        #     embed.add_field(
        #         name="Member",
        #         value=f"{after.mention} ({after.id})",
        #         inline=False
        #     )
        #     embed.add_field(
        #         name="Before",
        #         value=before.nick or before.name,
        #         inline=True
        #     )
        #     embed.add_field(
        #         name="After",
        #         value=after.nick or after.name,
        #         inline=True
        #     )
        #     
        #     await log_channel.send(embed=embed)

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

        # Check for avatar changes - removed per user request
        # if before.avatar != after.avatar:
        #     embed = discord.Embed(
        #         title="🖼️ Avatar Update",
        #         description=f"{after.mention} changed their avatar",
        #         color=discord.Color.green(),
        #         timestamp=datetime.now(tz=timezone.utc)
        #     )
        #     
        #     if before.avatar:
        #         embed.set_thumbnail(url=before.display_avatar.url)
        #         embed.add_field(name="Before", value="[Old Avatar](before.display_avatar.url)", inline=True)
        #     
        #     if after.avatar:
        #         embed.set_image(url=after.display_avatar.url)
        #         embed.add_field(name="After", value="[New Avatar](after.display_avatar.url)", inline=True)
        #     
        #     await log_channel.send(embed=embed)

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
        
        # Logging now handled by centralized logging system

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
        
        # Logging now handled by centralized logging system

async def setup(bot):
    await bot.add_cog(MemberEvents(bot))