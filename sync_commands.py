#!/usr/bin/env python3
"""
Manual command sync utility to fix "unknown integration" errors
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

async def sync_commands():
    """Manually sync all slash commands"""
    if not TOKEN:
        print("❌ No DISCORD_TOKEN found in environment")
        return

    # Create a simple bot instance
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(command_prefix='?', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"✅ Connected as {bot.user}")
        
        # Load all cogs
        cogs_to_load = [
            'commands.core',
            'commands.diagnostics', 
            'commands.community',
            'commands.fun',
            'commands.moderation',
            'commands.staff_points',
            'commands.election',
            'commands.data_management'
        ]
        
        loaded_cogs = 0
        for cog in cogs_to_load:
            try:
                await bot.load_extension(cog)
                loaded_cogs += 1
                print(f"✅ Loaded: {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")
        
        print(f"\n📊 Loaded {loaded_cogs}/{len(cogs_to_load)} cogs")
        
        # Sync commands globally
        try:
            print("\n🔄 Syncing commands globally...")
            global_synced = await bot.tree.sync()
            print(f"✅ Synced {len(global_synced)} commands globally")
            
            for cmd in global_synced:
                print(f"  - /{cmd.name}")
                
        except Exception as e:
            print(f"❌ Global sync failed: {e}")
        
        # Sync to guild if specified
        if GUILD_ID:
            try:
                print(f"\n🔄 Syncing commands to guild {GUILD_ID}...")
                guild = discord.Object(id=GUILD_ID)
                guild_synced = await bot.tree.sync(guild=guild)
                print(f"✅ Synced {len(guild_synced)} commands to guild")
                
                for cmd in guild_synced:
                    print(f"  - /{cmd.name}")
                    
            except Exception as e:
                print(f"❌ Guild sync failed: {e}")
        
        print(f"\n🎉 Command sync complete! Slash commands should now work.")
        await bot.close()
    
    try:
        await bot.start(TOKEN)
    except Exception as e:
        print(f"❌ Bot startup failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting command sync utility...")
    asyncio.run(sync_commands())
