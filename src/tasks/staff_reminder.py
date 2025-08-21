"""
Staff Bump Reminder Task - Reminds staff every 2 hours to bump the server
"""

import asyncio
import logging
import os
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone

logger = logging.getLogger("codeverse.staff_reminder")

class StaffBumpReminder(commands.Cog):
    """Reminds staff every 2 hours to bump the server manually"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.staff_channel_id = None
        self.staff_channel = None
        self.last_reminder_time = None
        self.last_bump_time = None  # Track when last bump happened
        self.bump_cooldown = 7200  # 2 hours in seconds for Disboard
        self.task_started = False  # Prevent duplicate task starts
        
    async def cog_load(self):
        """Start the staff reminder task when cog loads"""
        logger.info("Staff bump reminder task loaded")
        
    async def cog_unload(self):
        """Clean up when cog unloads"""
        if self.staff_reminder_task.is_running():
            self.staff_reminder_task.cancel()
        self.task_started = False
        logger.info("Staff bump reminder task unloaded")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Start staff reminder when bot is ready"""
        if self.task_started:
            return  # Prevent duplicate starts
            
        await self.setup_staff_channel()
        if not self.staff_reminder_task.is_running():
            self.staff_reminder_task.start()
            self.task_started = True
            logger.info("Staff bump reminder task started")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Track bump commands and responses"""
        if not message.guild or message.author.bot:
            return
        
        # Track when bumps happen based on bot responses
        if message.author.id == 302050872383242240:  # Disboard
            if "Bump done!" in message.content or "Server bumped!" in message.content:
                self.last_bump_time = datetime.now(timezone.utc)
                logger.info("Disboard bump detected")
        elif message.author.id == 159985870458322944:  # MEE6
            if "bumped" in message.content.lower() and "server" in message.content.lower():
                self.last_bump_time = datetime.now(timezone.utc)
                logger.info("MEE6 bump detected")
    
    def can_bump(self):
        """Check if server can be bumped (not on cooldown)"""
        if not self.last_bump_time:
            return True  # No previous bump recorded
        
        time_since_bump = (datetime.now(timezone.utc) - self.last_bump_time).total_seconds()
        return time_since_bump >= self.bump_cooldown
    
    async def setup_staff_channel(self):
        """Find and set up the staff channel"""
        # Get the main guild (first one or specific GUILD_ID)
        target_guild = None
        guild_id = int(os.getenv('GUILD_ID', 0))
        
        if guild_id:
            target_guild = self.bot.get_guild(guild_id)
        else:
            target_guild = self.bot.guilds[0] if self.bot.guilds else None
        
        if not target_guild:
            logger.warning("No target guild found for staff reminders")
            return
        
        # ONLY look for 'staff-chat' - be very specific
        staff_channel = discord.utils.get(target_guild.channels, name='staff-chat')
        
        if not staff_channel:
            # Only check for exact matches to avoid conflicts
            for channel in target_guild.channels:
                if isinstance(channel, discord.TextChannel):
                    name = channel.name.lower()
                    # Be very specific - only these exact names
                    if name in ['staff', 'staff-general', 'staff-channel']:
                        # Make sure it's NOT shifts, logs, or mod related
                        if 'shift' not in name and 'log' not in name and 'mod' not in name:
                            staff_channel = channel
                            break
        
        if staff_channel:
            self.staff_channel = staff_channel
            self.staff_channel_id = staff_channel.id
            logger.info(f"Found staff channel: #{staff_channel.name} in {target_guild.name}")
            return
        
        logger.warning("No staff-chat channel found. Please create #staff-chat channel.")
    
    @tasks.loop(hours=2)
    async def staff_reminder_task(self):
        """Send bump reminder to staff every 2 hours (only when bump is available)"""
        logger.info("Staff reminder task running - checking conditions...")
        
        if not self.staff_channel:
            logger.warning("No staff channel configured, skipping reminder")
            return
        
        # Check if bump is available
        if not self.can_bump():
            time_until_available = self.bump_cooldown - (datetime.now(timezone.utc) - self.last_bump_time).total_seconds()
            logger.info(f"Bump still on cooldown for {int(time_until_available/60)} more minutes, skipping reminder")
            return
        
        # Check if we sent a reminder recently (prevent spam)
        if self.last_reminder_time:
            time_since_last = (datetime.now(timezone.utc) - self.last_reminder_time).total_seconds()
            if time_since_last < 3600:  # Less than 1 hour since last reminder
                logger.info(f"Reminder sent recently ({int(time_since_last/60)} minutes ago), skipping")
                return
        
        logger.info(f"Sending bump reminder to #{self.staff_channel.name}")
        
        try:
            # Create reminder embed
            embed = discord.Embed(
                title="🔔 Bump Available!",
                description="The server bump cooldown has ended. Time to bump the server!",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Add bump method suggestions
            guild = self.staff_channel.guild
            bump_methods = []
            
            # Check for Disboard
            if guild.get_member(302050872383242240):
                bump_methods.append("🎯 **Disboard**: Use `/bump` in any channel")
            
            # Check for MEE6
            if guild.get_member(159985870458322944):
                bump_methods.append("🤖 **MEE6**: Use `!bump` command")
            
            # Generic suggestion
            if not bump_methods:
                bump_methods.append("📢 Use your server's bump command")
            
            embed.add_field(
                name="Available Bump Methods",
                value="\n".join(bump_methods),
                inline=False
            )
            
            embed.add_field(
                name="📌 Why Bump Now?",
                value="• Cooldown period has ended\n• Perfect timing for maximum visibility\n• Helps attract new members\n• Improves server ranking",
                inline=False
            )
            
            # Show cooldown info if we have bump history
            if self.last_bump_time:
                embed.add_field(
                    name="⏰ Last Bump",
                    value=f"<t:{int(self.last_bump_time.timestamp())}:R>",
                    inline=True
                )
            
            embed.set_footer(text="Bump reminders only sent when bump is available • ToS compliant")
            
            # Send reminder
            await self.staff_channel.send(embed=embed)
            self.last_reminder_time = datetime.now(timezone.utc)
            logger.info(f"Staff bump reminder sent in #{self.staff_channel.name} (bump available)")
            
        except discord.Forbidden:
            logger.error(f"No permission to send messages in #{self.staff_channel.name}")
        except discord.NotFound:
            logger.error("Staff channel not found, trying to find it again")
            await self.setup_staff_channel()
        except Exception as e:
            logger.error(f"Error sending staff reminder: {e}")
    
    @staff_reminder_task.before_loop
    async def before_staff_reminder(self):
        """Wait for bot to be ready before starting the loop"""
        await self.bot.wait_until_ready()
        logger.info("Staff reminder task ready to start")
    
    @commands.hybrid_command(name="reminder-status", help="Check staff reminder status and bump availability")
    @commands.has_permissions(manage_guild=True)
    async def reminder_status(self, ctx: commands.Context):
        """Check the status of staff reminder feature"""
        embed = discord.Embed(title="🔔 Staff Reminder Status", color=discord.Color.blue())
        
        if self.staff_channel:
            embed.add_field(name="Staff Channel", value=f"#{self.staff_channel.name}", inline=True)
            
            if self.staff_reminder_task.is_running():
                embed.add_field(name="Status", value="✅ Running", inline=True)
                next_iteration = self.staff_reminder_task.next_iteration
                if next_iteration:
                    embed.add_field(name="Next Check", value=f"<t:{int(next_iteration.timestamp())}:R>", inline=True)
            else:
                embed.add_field(name="Status", value="❌ Stopped", inline=True)
            
            # Bump availability status
            if self.can_bump():
                embed.add_field(name="Bump Status", value="✅ Available", inline=True)
            else:
                time_until_available = self.bump_cooldown - (datetime.now(timezone.utc) - self.last_bump_time).total_seconds()
                minutes_left = int(time_until_available / 60)
                embed.add_field(name="Bump Status", value=f"❌ Cooldown ({minutes_left}m left)", inline=True)
            
            if self.last_bump_time:
                embed.add_field(name="Last Bump", value=f"<t:{int(self.last_bump_time.timestamp())}:R>", inline=True)
            
            if self.last_reminder_time:
                embed.add_field(name="Last Reminder", value=f"<t:{int(self.last_reminder_time.timestamp())}:R>", inline=True)
        else:
            embed.add_field(name="Status", value="❌ No staff channel found", inline=False)
            embed.add_field(name="Solution", value="Create a channel named 'staff-chat' or use `/staff-channel` command", inline=False)
        
        embed.add_field(
            name="💡 Smart Reminders", 
            value="Only sends reminders when bump is actually available (no spam!)", 
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="remind-now", help="Manually send a bump reminder to staff (only if bump available)")
    @commands.has_permissions(manage_guild=True)
    async def remind_now(self, ctx: commands.Context):
        """Manually trigger a bump reminder (only if bump is available)"""
        if not self.staff_channel:
            await ctx.send("❌ No staff channel configured! Use `/staff-channel` to set one.")
            return
        
        # Check if bump is available
        if not self.can_bump():
            time_until_available = self.bump_cooldown - (datetime.now(timezone.utc) - self.last_bump_time).total_seconds()
            minutes_left = int(time_until_available / 60)
            
            embed = discord.Embed(
                title="⏰ Bump Not Available",
                description=f"Server bump is still on cooldown for **{minutes_left} more minutes**.",
                color=discord.Color.orange()
            )
            if self.last_bump_time:
                embed.add_field(
                    name="Last Bump",
                    value=f"<t:{int(self.last_bump_time.timestamp())}:R>",
                    inline=False
                )
            embed.set_footer(text="Reminders are only sent when bump is actually available")
            await ctx.send(embed=embed)
            return
        
        try:
            # Send the reminder immediately
            embed = discord.Embed(
                title="🔔 Manual Bump Reminder",
                description="A staff member has requested a bump reminder. Bump is available!",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="📢 Action Needed",
                value="Please bump the server using your preferred method:\n• **Disboard**: `/bump`\n• **MEE6**: `!bump`\n• **Other**: Check your server's bump commands",
                inline=False
            )
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
            
            await self.staff_channel.send(embed=embed)
            self.last_reminder_time = datetime.now(timezone.utc)
            
            confirmation_embed = discord.Embed(
                title="✅ Reminder Sent",
                description=f"Manual bump reminder sent to #{self.staff_channel.name}",
                color=discord.Color.green()
            )
            await ctx.send(embed=confirmation_embed)
            logger.info(f"Manual reminder triggered by {ctx.author}")
            
        except Exception as e:
            await ctx.send(f"❌ Error sending reminder: {e}")
    
    @commands.hybrid_command(name="staff-channel", help="Set or change the staff reminder channel (Admin only)")
    @commands.has_permissions(manage_guild=True)
    async def set_staff_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set the staff reminder channel"""
        if channel is None:
            channel = ctx.channel
        
        self.staff_channel = channel
        self.staff_channel_id = channel.id
        
        embed = discord.Embed(
            title="✅ Staff Channel Set",
            description=f"Staff reminders will now be sent to #{channel.name}",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📋 What This Does",
            value="• Sends bump reminders every 2 hours\n• Helps maintain ToS compliance\n• Keeps your server active on listing sites",
            inline=False
        )
        await ctx.send(embed=embed)
        logger.info(f"Staff channel set to #{channel.name} by {ctx.author}")

    @commands.hybrid_command(name="reminder-debug", help="Debug staff reminder channel detection (Admin only)")
    @commands.has_permissions(manage_guild=True)
    async def debug_reminder_system(self, ctx: commands.Context):
        """Debug staff reminder channel detection"""
        embed = discord.Embed(
            title="🔍 Staff Reminder Debug",
            description="Current channel detection status",
            color=discord.Color.blue()
        )
        
        # Show current configuration
        if self.staff_channel:
            embed.add_field(
                name="✅ Current Staff Channel",
                value=f"#{self.staff_channel.name} (ID: {self.staff_channel.id})",
                inline=False
            )
        else:
            embed.add_field(
                name="❌ No Staff Channel",
                value="No staff channel currently configured",
                inline=False
            )
        
        # Show available channels with 'staff' in name
        staff_like_channels = []
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel) and 'staff' in channel.name.lower():
                staff_like_channels.append(f"#{channel.name}")
        
        if staff_like_channels:
            embed.add_field(
                name="📋 Channels with 'staff' in name",
                value="\n".join(staff_like_channels),
                inline=False
            )
        
        # Show task status
        embed.add_field(
            name="🔄 Task Status",
            value=f"Running: {self.staff_reminder_task.is_running()}\nStarted: {self.task_started}",
            inline=True
        )
        
        # Show bump status
        if self.can_bump():
            embed.add_field(name="💚 Bump Status", value="Available", inline=True)
        else:
            time_until = self.bump_cooldown - (datetime.now(timezone.utc) - self.last_bump_time).total_seconds()
            embed.add_field(name="⏰ Bump Status", value=f"Cooldown ({int(time_until/60)}m left)", inline=True)
        
        embed.add_field(
            name="💡 Tip",
            value="Create a channel named exactly 'staff-chat' for automatic detection",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="reminder-test", help="Test the staff reminder system (Admin only)")
    @commands.has_permissions(manage_guild=True)
    async def test_reminder_system(self, ctx: commands.Context):
        """Test the staff reminder system"""
        if not self.staff_channel:
            await ctx.send("❌ No staff channel configured! Use `?staff-channel` first.")
            return
        
        embed = discord.Embed(
            title="🧪 Staff Reminder System Test",
            description=f"Testing reminder system in #{self.staff_channel.name}...",
            color=discord.Color.orange()
        )
        
        guild = self.staff_channel.guild
        system_info = []
        
        # Check for bump bots
        if guild.get_member(302050872383242240):
            system_info.append("✅ **Disboard** detected - Staff can use `/bump`")
        else:
            system_info.append("❌ **Disboard** not found")
        
        if guild.get_member(159985870458322944):
            system_info.append("✅ **MEE6** detected - Staff can use `!bump`")
        else:
            system_info.append("❌ **MEE6** not found")
        
        system_info.append(f"📅 **Reminder Frequency**: Every 2 hours")
        system_info.append(f"🛡️ **ToS Compliant**: Manual bumping only")
        
        embed.add_field(
            name="System Status",
            value="\n".join(system_info),
            inline=False
        )
        
        embed.add_field(
            name="💡 Benefits",
            value="• No risk of bot violations\n• Staff controlled bumping\n• Regular reminder schedule\n• Maintains server visibility",
            inline=False
        )
        
        embed.set_footer(text="Use ?remind-now to send a test reminder")
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(StaffBumpReminder(bot))
