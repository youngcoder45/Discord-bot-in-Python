"""
Auto Bump Task - Automatically sends /bump command every 2 hours
"""

import asyncio
import logging
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone

logger = logging.getLogger("codeverse.auto_bump")

class AutoBump(commands.Cog):
    """Automatically sends /bump command in designated channel every 2 hours"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bump_channel_id = None
        self.bump_channel = None
        self.last_bump_time = None
        
    async def cog_load(self):
        """Start the auto bump task when cog loads"""
        logger.info("Auto bump task loaded")
        
    async def cog_unload(self):
        """Clean up when cog unloads"""
        if self.auto_bump_task.is_running():
            self.auto_bump_task.cancel()
        logger.info("Auto bump task unloaded")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Start auto bump when bot is ready"""
        await self.setup_bump_channel()
        if not self.auto_bump_task.is_running():
            self.auto_bump_task.start()
            logger.info("Auto bump task started")
    
    async def setup_bump_channel(self):
        """Find and set up the bump channel"""
        for guild in self.bot.guilds:
            # Look for channel named 'bump' or containing 'bump'
            bump_channel = discord.utils.get(guild.channels, name='bump')
            if not bump_channel:
                # Try variations
                for channel in guild.channels:
                    if isinstance(channel, discord.TextChannel) and 'bump' in channel.name.lower():
                        bump_channel = channel
                        break
            
            if bump_channel:
                self.bump_channel = bump_channel
                self.bump_channel_id = bump_channel.id
                logger.info(f"Found bump channel: #{bump_channel.name} in {guild.name}")
                return
        
        logger.warning("No bump channel found. Auto bump will not work.")
    
    @tasks.loop(hours=2)
    async def auto_bump_task(self):
        """Send bump command every 2 hours"""
        if not self.bump_channel:
            logger.warning("No bump channel configured, skipping bump")
            return
        
        try:
            # Try multiple bump methods for different bots
            bump_sent = False
            
            # Method 1: Try Disboard slash command using application commands
            try:
                # Look for Disboard bot (ID: 302050872383242240)
                guild = self.bump_channel.guild
                disboard = guild.get_member(302050872383242240)
                
                if disboard:
                    # Use Disboard's prefix command (more reliable than slash for bots)
                    await self.bump_channel.send("!d bump")
                    bump_sent = True
                    logger.info(f"Disboard bump sent in #{self.bump_channel.name}")
                
            except Exception as e:
                logger.debug(f"Disboard method failed: {e}")
            
            # Method 2: Try MEE6 if Disboard not available
            if not bump_sent:
                try:
                    mee6 = self.bump_channel.guild.get_member(159985870458322944)  # MEE6's ID
                    if mee6:
                        await self.bump_channel.send("!bump")
                        bump_sent = True
                        logger.info(f"MEE6 bump sent in #{self.bump_channel.name}")
                except Exception as e:
                    logger.debug(f"MEE6 method failed: {e}")
            
            # Method 3: Try generic /bump slash command
            if not bump_sent:
                try:
                    # Create a webhook to send the slash command
                    # This is a workaround since bots can't directly invoke other bots' slash commands
                    await self.bump_channel.send("/bump")
                    bump_sent = True
                    logger.info(f"Generic /bump sent in #{self.bump_channel.name}")
                except Exception as e:
                    logger.debug(f"Generic slash command failed: {e}")
            
            # Method 4: Fallback - send text and log
            if not bump_sent:
                await self.bump_channel.send("Automatic bump reminder - please use your server's bump command!")
                logger.warning(f"All bump methods failed, sent reminder in #{self.bump_channel.name}")
            
            self.last_bump_time = datetime.now(timezone.utc)
            
        except discord.Forbidden:
            logger.error(f"No permission to send messages in #{self.bump_channel.name}")
        except discord.NotFound:
            logger.error("Bump channel not found, trying to find it again")
            await self.setup_bump_channel()
        except Exception as e:
            logger.error(f"Error sending auto bump: {e}")
    
    @auto_bump_task.before_loop
    async def before_auto_bump(self):
        """Wait for bot to be ready before starting the loop"""
        await self.bot.wait_until_ready()
        logger.info("Auto bump task ready to start")
    
    @commands.hybrid_command(name="bump-status", help="Check auto bump status and next bump time")
    @commands.has_permissions(manage_guild=True)
    async def bump_status(self, ctx: commands.Context):
        """Check the status of auto bump feature"""
        embed = discord.Embed(title="🔔 Auto Bump Status", color=discord.Color.blue())
        
        if self.bump_channel:
            embed.add_field(name="Bump Channel", value=f"#{self.bump_channel.name}", inline=True)
            
            if self.auto_bump_task.is_running():
                embed.add_field(name="Status", value="✅ Running", inline=True)
                next_iteration = self.auto_bump_task.next_iteration
                if next_iteration:
                    embed.add_field(name="Next Bump", value=f"<t:{int(next_iteration.timestamp())}:R>", inline=True)
            else:
                embed.add_field(name="Status", value="❌ Stopped", inline=True)
            
            if self.last_bump_time:
                embed.add_field(name="Last Bump", value=f"<t:{int(self.last_bump_time.timestamp())}:R>", inline=True)
        else:
            embed.add_field(name="Status", value="❌ No bump channel found", inline=False)
            embed.add_field(name="Solution", value="Create a channel named 'bump' or add 'bump' to an existing channel name", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="bump-now", help="Manually trigger a bump (Admin only)")
    @commands.has_permissions(manage_guild=True)
    async def bump_now(self, ctx: commands.Context):
        """Manually trigger a bump"""
        if not self.bump_channel:
            await ctx.send("❌ No bump channel configured!")
            return
        
        try:
            # Try multiple bump methods
            bump_sent = False
            method_used = ""
            
            # Method 1: Disboard
            guild = self.bump_channel.guild
            disboard = guild.get_member(302050872383242240)
            if disboard:
                await self.bump_channel.send("!d bump")
                bump_sent = True
                method_used = "Disboard (!d bump)"
            
            # Method 2: MEE6
            elif guild.get_member(159985870458322944):
                await self.bump_channel.send("!bump")
                bump_sent = True
                method_used = "MEE6 (!bump)"
            
            # Method 3: Generic slash command
            else:
                await self.bump_channel.send("/bump")
                bump_sent = True
                method_used = "Generic (/bump)"
            
            self.last_bump_time = datetime.now(timezone.utc)
            
            embed = discord.Embed(
                title="✅ Manual Bump Sent",
                description=f"Sent bump command in #{self.bump_channel.name}\nMethod: {method_used}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            logger.info(f"Manual bump triggered by {ctx.author} using {method_used}")
            
        except Exception as e:
            await ctx.send(f"❌ Error sending bump: {e}")
    
    @commands.hybrid_command(name="bump-channel", help="Set or change the bump channel (Admin only)")
    @commands.has_permissions(manage_guild=True)
    async def set_bump_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set the bump channel"""
        if channel is None:
            channel = ctx.channel
        
        self.bump_channel = channel
        self.bump_channel_id = channel.id
        
        embed = discord.Embed(
            title="✅ Bump Channel Set",
            description=f"Auto bump will now use #{channel.name}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        logger.info(f"Bump channel set to #{channel.name} by {ctx.author}")

    @commands.hybrid_command(name="bump-test", help="Test which bump method works in your server (Admin only)")
    @commands.has_permissions(manage_guild=True)
    async def test_bump_methods(self, ctx: commands.Context):
        """Test different bump methods to see which works"""
        if not self.bump_channel:
            await ctx.send("❌ No bump channel configured! Use `?bump-channel` first.")
            return
        
        embed = discord.Embed(
            title="🧪 Bump Method Test",
            description=f"Testing bump methods in #{self.bump_channel.name}...",
            color=discord.Color.orange()
        )
        
        guild = self.bump_channel.guild
        methods_available = []
        
        # Check for Disboard
        if guild.get_member(302050872383242240):
            methods_available.append("✅ **Disboard** - `!d bump` (Recommended)")
        else:
            methods_available.append("❌ **Disboard** - Bot not found")
        
        # Check for MEE6
        if guild.get_member(159985870458322944):
            methods_available.append("✅ **MEE6** - `!bump`")
        else:
            methods_available.append("❌ **MEE6** - Bot not found")
        
        methods_available.append("⚠️ **Generic** - `/bump` (May not work)")
        
        embed.add_field(
            name="Available Methods",
            value="\n".join(methods_available),
            inline=False
        )
        
        embed.add_field(
            name="💡 Recommendation",
            value="• **Disboard** is most reliable for server bumping\n• **MEE6** works for servers using MEE6's bump feature\n• **Generic** /bump may not trigger other bots properly",
            inline=False
        )
        
        embed.set_footer(text="The bot will automatically use the best available method")
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoBump(bot))
