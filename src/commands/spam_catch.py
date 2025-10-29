
"""Auto-timeout channel protection cog.

This module applies a timeout to users who send messages in a protected channel.
We log extensively so the bot owner can see a clear audit trail and debug info
when events occur.
"""
import traceback
import logging
try:
    # Made by @Chaosraph
    import discord
    from discord.ext import commands
    from datetime import timedelta

    # Configure a logger for this module - the bot's main app should configure handlers.
    logger = logging.getLogger("codeverse.spam_catch")

    PROTECTED_CHANNEL_ID = 1430566219643228210
    TIMEOUT_DAYS = 10  # Use a 10-day timeout instead of a ban

    class AutoBanChannel(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @commands.Cog.listener()
        async def on_message(self, message: discord.Message):
            """If a non-bot user posts in the protected channel, apply a timeout.

            Extensive logging is included for debugging and auditing purposes.
            """
            # Ignore bot messages
            if message.author.bot:
                return

            # Safely get channel id (DMs may not have id)
            channel = getattr(message, 'channel', None)
            channel_id = getattr(channel, 'id', None)
            if channel_id is None:
                logger.debug("Received message with no channel id; ignoring")
                return

            if channel_id != PROTECTED_CHANNEL_ID:
                return

            # Prepare context for logging
            guild = message.guild
            user = message.author
            content_preview = (message.content or "").replace("\n", " ")[:300]

            logger.info(
                "Protected-channel message: user=%s user_id=%s guild=%s guild_id=%s channel_id=%s preview=%s",
                getattr(user, 'name', str(user)),
                getattr(user, 'id', None),
                getattr(guild, 'name', None),
                getattr(guild, 'id', None),
                channel_id,
                content_preview,
            )

            if guild is None:
                logger.warning("Message in protected channel came from outside a guild; skipping timeout")
                return

            try:
                member = guild.get_member(user.id)
                if member is None:
                    logger.warning("Could not resolve Member for user_id=%s in guild_id=%s", user.id, guild.id)
                    return

                duration = timedelta(days=TIMEOUT_DAYS)
                logger.debug("Attempting to apply timeout: user_id=%s duration=%s", member.id, duration)
                await member.timeout(duration, reason="Message sent in protected channel")

                try:
                    await message.delete()
                    logger.debug("Deleted message id=%s from user_id=%s", getattr(message, 'id', None), member.id)
                except Exception as de:
                    logger.debug("Failed to delete offending message (non-fatal): %s", de)

                logger.info("Timeout applied: user=%s user_id=%s duration=%s guild_id=%s",
                            getattr(member, 'name', None), getattr(member, 'id', None), duration, guild.id)

            except discord.Forbidden:
                logger.exception("Missing permissions to timeout/delete in guild_id=%s", getattr(guild, 'id', None))
            except Exception:
                logger.exception("Unexpected error while processing protected-channel event for guild_id=%s", getattr(guild, 'id', None))

    async def setup(bot):
        await bot.add_cog(AutoBanChannel(bot))
except Exception:
    # Print full traceback so it's visible in bot logs; re-raise to preserve original behavior
    print("❌ Error importing commands.spam_catch:")
    traceback.print_exc()
    raise