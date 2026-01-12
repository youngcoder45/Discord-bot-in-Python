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
        """Check if member is a staff member (has Manage Messages permission)"""
        if not member.guild:
            return False
        
        # Simple permission check instead of using removed StaffShifts module
        return member.guild_permissions.manage_messages

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

    async def get_welcome_channel(self, guild_id: int) -> int:
        """Get the welcome channel ID for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT welcome_channel_id FROM welcome_config 
                WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result and result[0] else 1263070188589547541  # Default channel

    async def set_welcome_channel(self, guild_id: int, channel_id: int):
        """Set the welcome channel for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO welcome_config (guild_id, welcome_channel_id)
                VALUES (?, ?)
            """, (guild_id, channel_id))
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
            
        # Get welcome channel from database
        welcome_channel_id = await self.get_welcome_channel(member.guild.id)
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
                color=0x0000ff
            )
            embed.add_field(
                name="Status",
                value=f"Welcome messages are **{'enabled' if enabled else 'disabled'}**",
                inline=False
            )
            embed.add_field(
                name="Commands",
                value="• `/welcome toggle [channel]` - Toggle welcome messages on/off and set channel\n• `/welcome status` - Show current settings\n• `/welcome channel <#channel>` - Set welcome channel",
                inline=False
            )
            await ctx.reply(embed=embed)

    @welcome.command(name="toggle", description="Toggle welcome messages on/off and optionally set channel")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @app_commands.describe(channel="Channel where welcome messages will be sent (optional)")
    async def toggle_welcome(self, ctx: commands.Context, channel: discord.TextChannel | None = None):
        """Toggle welcome messages on or off and optionally set the channel"""
        assert ctx.guild is not None, "This command can only be used in a guild"
        current_status = await self.get_welcome_enabled(ctx.guild.id)
        new_status = not current_status
        
        await self.set_welcome_enabled(ctx.guild.id, new_status)
        
        # If a channel is provided, update the welcome channel
        if channel:
            await self.set_welcome_channel(ctx.guild.id, channel.id)
        
        # Get current welcome channel to display
        current_channel_id = await self.get_welcome_channel(ctx.guild.id)
        current_channel = ctx.guild.get_channel(current_channel_id)
        
        embed = discord.Embed(
            title="Welcome Messages Updated",
            color=0x00FF00 if new_status else 0xFF0000
        )
        embed.add_field(
            name="Status",
            value=f"Welcome messages are now **{'enabled' if new_status else 'disabled'}**",
            inline=False
        )
        embed.add_field(
            name="Channel",
            value=f"{current_channel.mention if current_channel else 'Channel not found'}",
            inline=True
        )
        if channel:
            embed.add_field(
                name="Updated",
                value=f"Welcome channel set to {channel.mention}",
                inline=True
            )
        embed.set_footer(text=f"Changed by {ctx.author.display_name}")
        
        await ctx.reply(embed=embed)

    @welcome.command(name="channel", description="Set the welcome message channel")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @app_commands.describe(channel="Channel where welcome messages will be sent")
    async def welcome_channel_command(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel where welcome messages will be sent"""
        assert ctx.guild is not None, "This command can only be used in a guild"
        
        await self.set_welcome_channel(ctx.guild.id, channel.id)
        
        embed = discord.Embed(
            title="Welcome Channel Updated",
            color=0x00FF00
        )
        embed.add_field(
            name="New Welcome Channel",
            value=f"{channel.mention}",
            inline=False
        )
        embed.add_field(
            name="Note",
            value="Welcome messages will now be sent to this channel when enabled.",
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
        channel_id = await self.get_welcome_channel(ctx.guild.id)
        channel = ctx.guild.get_channel(channel_id)
        
        embed = discord.Embed(
            title="Welcome Message Status",
            color=0x0000ff
        )
        embed.add_field(
            name="Welcome Messages",
            value=f"**{'Enabled' if enabled else 'Disabled'}**",
            inline=True
        )
        embed.add_field(
            name="Channel",
            value=f"{channel.mention if channel else 'Channel not found'}",
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

    # on_user_update removed - strictly handled by LoggingCog now


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
        # Logging now handled by centralized logging system
        pass

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Handle member unban events"""
        # Logging now handled by centralized logging system
        pass

async def setup(bot):
    await bot.add_cog(MemberEvents(bot))