#!/usr/bin/env python3
"""
Quick bot test to identify the unknown integration error
"""

import os
import sys
import asyncio
import discord
from discord.ext import commands

# Add src directory to Python path
sys.path.insert(0, 'src')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID', 0))

# Simple test bot
intents = discord.Intents.default()
intents.message_content = True

class TestBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='?', intents=intents)

    async def setup_hook(self):
        # Load only the fun cog to test
        try:
            await self.load_extension('commands.fun')
            print("✅ Fun cog loaded successfully")
        except Exception as e:
            print(f"❌ Error loading fun cog: {e}")
            import traceback
            traceback.print_exc()

    async def on_ready(self):
        print(f"✅ Bot ready: {self.user}")
        
        # Try to sync commands
        try:
            if GUILD_ID:
                guild = discord.Object(id=GUILD_ID)
                synced = await self.tree.sync(guild=guild)
                print(f"✅ Synced {len(synced)} commands to guild")
            else:
                synced = await self.tree.sync()
                print(f"✅ Synced {len(synced)} commands globally")
        except Exception as e:
            print(f"❌ Command sync error: {e}")
            import traceback
            traceback.print_exc()

async def test_bot():
    if not TOKEN:
        print("❌ No DISCORD_TOKEN found")
        return
    
    bot = TestBot()
    
    try:
        print("🚀 Starting test bot...")
        await bot.start(TOKEN)
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bot())
