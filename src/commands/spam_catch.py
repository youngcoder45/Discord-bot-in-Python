
# Made by @Chaosraph
import discord
from discord.ext import commands

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
                await message.author.ban(reason="Message sent in protected channel")
                await message.delete()
                print(f"{message.author} was banned because he wrote in the protected channel.")
            except discord.Forbidden:
                print("Missing permissions to ban this user.")
            except Exception as e:
                print(f"Error banning: {e}")

async def setup(bot):
    await bot.add_cog(AutoBanChannel(bot))