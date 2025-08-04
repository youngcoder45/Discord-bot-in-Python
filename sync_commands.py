"""
Slash Command Sync Utility
Run this script to sync all slash commands with Discord
"""

import asyncio
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def sync_commands():
    """Sync all slash commands to Discord"""
    TOKEN = os.getenv('DISCORD_TOKEN')
    GUILD_ID = int(os.getenv('GUILD_ID', 0))
    
    if not TOKEN:
        print("❌ Error: DISCORD_TOKEN not found in environment variables")
        return
    
    # Create bot with minimal intents for syncing
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"✅ Logged in as {bot.user}")
        
        try:
            if GUILD_ID:
                # Sync to specific guild (faster, for development)
                guild = discord.Object(id=GUILD_ID)
                synced = await bot.tree.sync(guild=guild)
                print(f"🔄 Synced {len(synced)} commands to guild {GUILD_ID}")
            else:
                # Sync globally (slower, up to 1 hour to propagate)
                synced = await bot.tree.sync()
                print(f"🌍 Synced {len(synced)} commands globally")
                
            print("✨ Slash commands are now available!")
            print("Use / in your Discord server to see them")
            
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")
        
        await bot.close()
    
    # Add a simple test command
    @bot.tree.command(name="ping", description="Test if the bot is working")
    async def ping(interaction: discord.Interaction):
        await interaction.response.send_message("🏓 Pong! Bot is working!")
    
    @bot.tree.command(name="help", description="Show available bot commands")
    async def help_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 CodeVerse Bot Commands",
            description="Here are the available slash commands:",
            color=0x00ff00
        )
        embed.add_field(name="/ping", value="Test bot connectivity", inline=False)
        embed.add_field(name="/quote", value="Get a motivational quote", inline=False)
        embed.add_field(name="/rank", value="Check your XP and level", inline=False)
        embed.add_field(name="/leaderboard", value="View server leaderboard", inline=False)
        embed.add_field(name="/qotd", value="Get question of the day", inline=False)
        embed.set_footer(text="More commands coming soon!")
        await interaction.response.send_message(embed=embed)
    
    # Connect and sync
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    print("🚀 Starting slash command sync...")
    asyncio.run(sync_commands())
