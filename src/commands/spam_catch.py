
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
        if message.channel.id == PROTECTED_CHANNEL_ID:
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
                    
                    # Apply permanent timeout (28 days, the maximum Discord allows)
                    await member.timeout(timedelta(days=28), reason="Message sent in protected channel")
                    await message.delete()
                    print(f"{message.author} was permanently timed out because they wrote in the protected channel.")
            except discord.Forbidden:
                print("Missing permissions to timeout this user.")
            except Exception as e:
                print(f"Error timing out user: {e}")

async def setup(bot):
    await bot.add_cog(AutoBanChannel(bot))