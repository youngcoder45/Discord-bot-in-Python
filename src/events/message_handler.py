from discord.ext import commands
import asyncio
import logging, discord, os, re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Channel that should get automatic intro reactions
INTRODUCTION_CHANNEL_ID = 1263070188589547541
INTRO_REACTIONS = ["👋🏻", "🔥", "❤️"]

class MessageHandler(commands.Cog):
    """Simplified message handler with auto-thanks points."""
    def __init__(self, bot):
        self.bot = bot

    async def _add_intro_reactions(self, message: discord.Message) -> None:
        for emoji in INTRO_REACTIONS:
            try:
                await message.add_reaction(emoji)
            except discord.Forbidden:
                logger.warning(
                    "Missing permission to add reactions in channel_id=%s guild_id=%s",
                    getattr(message.channel, 'id', None),
                    getattr(message.guild, 'id', None),
                )
                return
            except discord.HTTPException:
                # Non-fatal (rate limit / already reacted / transient API issue)
                continue

    @commands.command(name="introreact", hidden=True)
    @commands.has_permissions(manage_messages=True)
    async def introreact(self, ctx: commands.Context, limit: str = "all"):
        """Backfill intro reactions in the introductions channel.

        Usage:
          `?introreact` (all messages; can take a long time)
          `?introreact 500` (only last 500 messages)
        """
        if not ctx.guild:
            return

        channel = ctx.guild.get_channel(INTRODUCTION_CHANNEL_ID)
        if channel is None:
            try:
                channel = await ctx.guild.fetch_channel(INTRODUCTION_CHANNEL_ID)
            except Exception:
                channel = None

        if channel is None:
            await ctx.reply("❌ I can't access the introductions channel in this server.", mention_author=False)
            return

        history_limit = None
        if limit and limit.lower() != "all":
            try:
                history_limit = max(1, int(limit))
            except ValueError:
                await ctx.reply("❌ Invalid limit. Use `all` or a number (e.g. `?introreact 500`).", mention_author=False)
                return

        status = await ctx.reply(
            f"⏳ Adding reactions in {channel.mention} (limit={history_limit or 'all'})...",
            mention_author=False,
        )

        scanned = 0
        processed = 0
        try:
            async for msg in channel.history(limit=history_limit, oldest_first=True):
                scanned += 1
                if msg.author.bot:
                    continue

                await self._add_intro_reactions(msg)
                processed += 1

                # Conservative pacing to avoid long bursts hitting global rate limits
                if processed % 25 == 0:
                    await asyncio.sleep(1)

            await status.edit(content=f"✅ Done. Scanned {scanned} messages; reacted to {processed}.")
        except discord.Forbidden:
            await status.edit(content="❌ Missing permissions to read history and/or add reactions.")
        except Exception as e:
            await status.edit(content=f"❌ Stopped due to error: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle messages for auto-thanks detection"""
        # Ignore bot messages or DMs
        if message.author.bot or not message.guild:
            return

        # Auto-react in introductions channel
        if getattr(message.channel, 'id', None) == INTRODUCTION_CHANNEL_ID:
            await self._add_intro_reactions(message)
        
        # Check for thanks mentions
        await self.check_thanks_mention(message)
        
        # NOTE: Don't call process_commands here - the bot already does this automatically
        # Calling it here would cause duplicate responses for prefix commands

    async def check_thanks_mention(self, message):
        """Check if message contains 'thanks' and mentions/replies to staff. Only admins can award aura."""
        content = message.content.lower()
        # Check if message contains the exact word "thanks" using word boundaries
        import re
        has_thanks = bool(re.search(r'\bthanks\b', content))
        if not has_thanks:
            return

        # Only allow admins to award aura
        if not message.guild:
            return
        author_member = message.guild.get_member(message.author.id)
        if not author_member:
            return
        
        # Only server owner and admins can award aura
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
            # Only give aura to staff members (with staff role)
            if await staff_points_cog.is_staff_member(mention):
                mentioned_staff.append(mention)

        # Check if replying to a staff member
        if message.reference and message.reference.message_id:
            try:
                replied_msg = await message.channel.fetch_message(message.reference.message_id)
                # Only give aura to staff members (with staff role)
                if replied_msg.author != message.author and await staff_points_cog.is_staff_member(replied_msg.author):
                    mentioned_staff.append(replied_msg.author)
            except:
                pass

        # Give aura to mentioned/replied staff and send confirmation
        for staff_member in set(mentioned_staff):  # Remove duplicates
            success = await staff_points_cog.auto_give_point(staff_member, f"Thanks from {message.author.display_name}")
            if success:
                # Send professional bot reply message
                embed = discord.Embed(
                    title="✨ Aura Awarded",
                    description=f"Added 1 aura to {staff_member.mention} for their helpful contribution.",
                    color=0xf1c40f,
                    timestamp=datetime.now(timezone.utc)
                )
                embed.set_footer(text=f"Awarded by {message.author.display_name}")
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