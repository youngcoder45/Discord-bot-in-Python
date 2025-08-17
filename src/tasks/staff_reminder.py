"""
Staff Bump Reminder Task - Reminds staff every 2 hours to bump the server
"""

import asyncio
import logging
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
        
    async def cog_load(self):
        """Start the staff reminder task when cog loads"""
        logger.info("Staff bump reminder task loaded")
        
    async def cog_unload(self):
        """Clean up when cog unloads"""
        if self.staff_reminder_task.is_running():
            self.staff_reminder_task.cancel()
        logger.info("Staff bump reminder task unloaded")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Start staff reminder when bot is ready"""
        await self.setup_staff_channel()
        if not self.staff_reminder_task.is_running():
            self.staff_reminder_task.start()
            logger.info("Staff bump reminder task started")
    
    async def setup_staff_channel(self):
        """Find and set up the staff channel"""
        for guild in self.bot.guilds:
            # Look for channel named 'staff-chat' or containing 'staff'
            staff_channel = discord.utils.get(guild.channels, name='staff-chat')
            if not staff_channel:
                # Try variations
                for channel in guild.channels:
                    if isinstance(channel, discord.TextChannel) and any(term in channel.name.lower() for term in ['staff', 'mod', 'admin']):
                        staff_channel = channel
                        break
            
            if staff_channel:
                self.staff_channel = staff_channel
                self.staff_channel_id = staff_channel.id
                logger.info(f"Found staff channel: #{staff_channel.name} in {guild.name}")
                return
        
        logger.warning("No staff channel found. Staff reminders will not work.")
    
    @tasks.loop(hours=2)
    async def staff_reminder_task(self):
        """Send bump reminder to staff every 2 hours"""
        if not self.staff_channel:
            logger.warning("No staff channel configured, skipping reminder")
            return
        
        try:
            # Create reminder embed
            embed = discord.Embed(
                title="🔔 Bump Reminder",
                description="Time to bump the server! Please use the appropriate bump command.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Add bump method suggestions
            guild = self.staff_channel.guild
            bump_methods = []
            
            # Check for Disboard
            if guild.get_member(302050872383242240):
                bump_methods.append("🎯 **Disboard**: Use `/bump` in your bump channel")
            
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
                name="📌 Why Bump?",
                value="• Increases server visibility\n• Attracts new members\n• Grows the community\n• Improves server ranking",
                inline=False
            )
            
            embed.set_footer(text="Next reminder in 2 hours • Manual bumping keeps us ToS compliant")
            
            # Send reminder
            await self.staff_channel.send(embed=embed)
            self.last_reminder_time = datetime.now(timezone.utc)
            logger.info(f"Staff bump reminder sent in #{self.staff_channel.name}")
            
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
    
    @commands.hybrid_command(name="reminder-status", help="Check staff reminder status and next reminder time")
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
                    embed.add_field(name="Next Reminder", value=f"<t:{int(next_iteration.timestamp())}:R>", inline=True)
            else:
                embed.add_field(name="Status", value="❌ Stopped", inline=True)
            
            if self.last_reminder_time:
                embed.add_field(name="Last Reminder", value=f"<t:{int(self.last_reminder_time.timestamp())}:R>", inline=True)
        else:
            embed.add_field(name="Status", value="❌ No staff channel found", inline=False)
            embed.add_field(name="Solution", value="Create a channel named 'staff-chat' or add 'staff' to an existing channel name", inline=False)
        
        embed.add_field(
            name="💡 Purpose", 
            value="Reminds staff to manually bump the server (ToS compliant)", 
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="remind-now", help="Manually send a bump reminder to staff (Admin only)")
    @commands.has_permissions(manage_guild=True)
    async def remind_now(self, ctx: commands.Context):
        """Manually trigger a bump reminder"""
        if not self.staff_channel:
            await ctx.send("❌ No staff channel configured!")
            return
        
        try:
            # Send the reminder immediately
            embed = discord.Embed(
                title="🔔 Manual Bump Reminder",
                description="A staff member has requested a bump reminder.",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="📢 Action Needed",
                value="Please bump the server using your preferred method:\n• Disboard: `/bump`\n• MEE6: `!bump`\n• Other: Check your server's bump commands",
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
