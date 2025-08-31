#!/usr/bin/env python3
"""
Quick Discord Command Test - Check if slash commands are actually working
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

async def test_commands():
    """Test if commands are actually registered and working"""
    if not TOKEN:
        print("❌ No DISCORD_TOKEN found")
        return

    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(command_prefix='?', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"✅ Connected as {bot.user}")
        print(f"🔍 Bot is in {len(bot.guilds)} guild(s)")
        
        # Check global commands
        try:
            global_commands = await bot.tree.fetch_commands()
            print(f"\n🌍 Global commands registered: {len(global_commands)}")
            for cmd in global_commands[:10]:  # Show first 10
                print(f"   • {cmd.name} - {cmd.description}")
            if len(global_commands) > 10:
                print(f"   ... and {len(global_commands) - 10} more")
        except Exception as e:
            print(f"❌ Error fetching global commands: {e}")
        
        # Check guild commands
        if GUILD_ID:
            try:
                guild = discord.Object(id=GUILD_ID)
                guild_commands = await bot.tree.fetch_commands(guild=guild)
                print(f"\n🏰 Guild commands registered: {len(guild_commands)}")
                for cmd in guild_commands[:5]:
                    print(f"   • {cmd.name}")
            except Exception as e:
                print(f"❌ Error fetching guild commands: {e}")
        
        # Check bot permissions in the guild
        if GUILD_ID:
            guild = bot.get_guild(GUILD_ID)
            if guild:
                bot_member = guild.get_member(bot.user.id)
                if bot_member:
                    permissions = bot_member.guild_permissions
                    print(f"\n🔑 Bot permissions in {guild.name}:")
                    print(f"   • Use Slash Commands: {permissions.use_slash_commands}")
                    print(f"   • Send Messages: {permissions.send_messages}")
                    print(f"   • Embed Links: {permissions.embed_links}")
                    print(f"   • Administrator: {permissions.administrator}")
                else:
                    print(f"❌ Bot not found in guild {GUILD_ID}")
            else:
                print(f"❌ Guild {GUILD_ID} not found")
        
        print(f"\n📊 Summary:")
        print(f"   • Bot User ID: {bot.user.id}")
        print(f"   • Application ID: {bot.application_id}")
        print(f"   • Latency: {round(bot.latency * 1000)}ms")
        
        print(f"\n🎯 DIAGNOSIS:")
        if len(global_commands) > 0:
            print(f"   ✅ Slash commands ARE registered with Discord!")
            print(f"   ✅ {len(global_commands)} commands available globally")
            print(f"   ℹ️  If you still see 'unknown integration', try:")
            print(f"      1. Restart your Discord client completely")
            print(f"      2. Wait 5-10 minutes for Discord cache to update")
            print(f"      3. Try typing '/' in a channel to see if commands appear")
            print(f"      4. Check bot permissions in server settings")
        else:
            print(f"   ❌ No commands registered - there's an issue")
        
        await bot.close()
    
    try:
        await bot.start(TOKEN)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 Testing Discord slash commands registration...")
    asyncio.run(test_commands())
