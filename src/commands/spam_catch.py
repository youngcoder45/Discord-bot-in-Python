
"""Auto-ban (auto-timeout) channel protection cog.

This module sometimes fails to load silently if an import-time error occurs. To help
diagnose such cases we wrap module initialization in a try/except that prints a full
traceback to stdout so the bot owner can see the underlying issue in the logs.
"""
import traceback
try:
    # Made by @Chaosraph
    import discord
    from discord.ext import commands
    from datetime import timedelta

    PROTECTED_CHANNEL_ID = 1430566219643228210

    class AutoBanChannel(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @commands.Cog.listener()
        async def on_message(self, message: discord.Message):
            if message.author.bot:
                return
            # Guard: some messages (DMs) have no channel id
            try:
                channel_id = message.channel.id
            except Exception:
                return

            if channel_id == PROTECTED_CHANNEL_ID:
                try:
                    if message.guild is None:
                        # Can't timeout a user outside of a guild
                        print("Message was not sent in a guild; cannot timeout user.")
                    else:
                        # Get the member object
                        member = message.guild.get_member(message.author.id)
                        if member is None:
                            print(f"Could not find member {message.author} in guild.")
                            return

                        # Apply a 28-day timeout (maximum Discord allows as a duration)
                        await member.timeout(timedelta(days=28), reason="Message sent in protected channel")
                        try:
                            await message.delete()
                        except Exception:
                            pass
                        print(f"{message.author} was timed out because they wrote in the protected channel.")
                except discord.Forbidden:
                    print("Missing permissions to timeout this user.")
                except Exception as e:
                    print(f"Error timing out user: {e}")

    async def setup(bot):
        await bot.add_cog(AutoBanChannel(bot))
except Exception as _e:
    # Print full traceback so it's visible in bot logs; re-raise to preserve original behavior
    print("❌ Error importing commands.spam_catch:")
    traceback.print_exc()
    raise