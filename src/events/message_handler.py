from discord.ext import commands
import logging, discord, os, re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MessageHandler(commands.Cog):
    """Simplified message handler with auto-thanks points."""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle messages for auto-thanks detection"""
        # Ignore bot messages or DMs
        if message.author.bot or not message.guild:
            return
        
        # Check for thanks mentions
        await self.check_thanks_mention(message)
        
        # NOTE: Don't call process_commands here - the bot already does this automatically
        # Calling it here would cause duplicate responses for prefix commands

    async def check_thanks_mention(self, message):
        """Check if message contains 'thanks' and mentions/replies to staff, but only allow admins/staff to thank."""
        content = message.content.lower()
        # Check if message contains the exact word "thanks" using word boundaries
        import re
        has_thanks = bool(re.search(r'\bthanks\b', content))
        if not has_thanks:
            return

        # Only allow admins/staff to thank
        if not message.guild:
            return
        author_member = message.guild.get_member(message.author.id)
        if not author_member:
            return
        
        # Allow server owner and admins
        is_owner = author_member.id == message.guild.owner_id
        is_admin = author_member.guild_permissions.administrator
        
        if not (is_owner or is_admin):
            return

        # Get staff points cog
        staff_points_cog = self.bot.get_cog('StaffPoints')
        if not staff_points_cog:
            return

        mentioned_staff = []

        # Check direct mentions
        for mention in message.mentions:
            if await staff_points_cog.is_staff_member(mention):
                mentioned_staff.append(mention)

        # Check if replying to a staff member
        if message.reference and message.reference.message_id:
            try:
                replied_msg = await message.channel.fetch_message(message.reference.message_id)
                if replied_msg.author != message.author and await staff_points_cog.is_staff_member(replied_msg.author):
                    mentioned_staff.append(replied_msg.author)
            except:
                pass

        # Give points to mentioned/replied staff and send confirmation
        for staff_member in set(mentioned_staff):  # Remove duplicates
            success = await staff_points_cog.auto_give_point(staff_member, f"Thanks from {message.author.display_name}")
            if success:
                # Send professional bot reply message
                embed = discord.Embed(
                    title="Aura Awarded",
                    description=f"Added 1 aura to {staff_member.mention} for their helpful contribution.",
                    color=0x2ECC71,
                    timestamp=datetime.now(timezone.utc)
                )
                await message.reply(embed=embed, mention_author=False)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Handle new member joins (no DM, simplified)."""
        # Welcome messages removed per user request
        pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Global command error handler"""
        # Don't handle errors that are already handled by command-specific handlers
        if hasattr(ctx.command, 'on_error'):
            return
        
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        
        # For slash commands, check if interaction was already responded to
        if hasattr(ctx, 'interaction') and ctx.interaction and ctx.interaction.response.is_done():
            try:
                # Try to send a followup instead
                embed = discord.Embed(
                    title="❌ An Error Occurred",
                    description=f"Error: {str(error)}",
                    color=discord.Color.red()
                )
                await ctx.interaction.followup.send(embed=embed, ephemeral=True)
            except:
                pass  # If followup also fails, just ignore
            return
        
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You don't have permission to use this command!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
        
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Argument",
                description=f"Missing required argument: `{error.param}`\n"
                           f"Use `?help {ctx.command}` for usage information.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=15)
        
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Invalid Argument", 
                description="Invalid argument provided!\n"
                           f"Use `?help {ctx.command}` for usage information.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=15)
        
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Command on Cooldown",
                description=f"This command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed, delete_after=10)
        
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="❌ Member Not Found",
                description="Could not find the specified member!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
        
        else:
            # Log unexpected errors
            print(f"Unhandled error in command {ctx.command}: {error}")
            
            embed = discord.Embed(
                title="❌ An Error Occurred",
                description="An unexpected error occurred while processing your command.\n"
                           "Please try again later or contact an administrator.",
                color=discord.Color.red()
            )
            try:
                await ctx.send(embed=embed, delete_after=15)
            except:
                pass  # If sending fails, just ignore
    
    # AFK and XP systems removed per request.

async def setup(bot):
    await bot.add_cog(MessageHandler(bot))