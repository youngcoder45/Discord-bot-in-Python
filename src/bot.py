import discord
from discord.ext import commands, tasks
import os
import asyncio
import logging
from datetime import datetime, time, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID', 0))

# Channel IDs (you'll need to replace these with your actual channel IDs)
CHANNELS = {
    'questions': int(os.getenv('QUESTIONS_CHANNEL_ID', 0)),
    'staff_updates': int(os.getenv('STAFF_UPDATES_CHANNEL_ID', 0)),
    'leaderboard': int(os.getenv('LEADERBOARD_CHANNEL_ID', 0)),
    'suggestions': int(os.getenv('SUGGESTIONS_CHANNEL_ID', 0)),
    'mod_tools': int(os.getenv('MOD_TOOLS_CHANNEL_ID', 0)),
    'bot_commands': int(os.getenv('BOT_COMMANDS_CHANNEL_ID', 0))
}

# Initialize bot with proper intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.reactions = True

class CodeVerseBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=['!', '/'],
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        self.start_time = datetime.now(timezone.utc)

    async def setup_hook(self):
        """This is called when the bot is started, after login"""
        # Load cogs first
        await load_cogs(self)
        
        # Then sync commands
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

# Create bot instance
bot = CodeVerseBot()

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    
    # Initialize database
    from utils.database import init_database
    await init_database()
    logger.info('Database initialized')
    
    # Log available commands for debugging
    logger.info(f'Available commands: {[cmd.name for cmd in bot.commands]}')
    logger.info(f'Available app commands: {[cmd.name for cmd in bot.tree.get_commands()]}')
    
    # Start background tasks
    if not daily_qotd.is_running():
        daily_qotd.start()
    if not weekly_challenge.is_running():
        weekly_challenge.start()
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="The CodeVerse Hub 🚀"
        )
    )

async def load_cogs(bot_instance):
    """Load all command cogs"""
    cogs = [
        'commands.moderation',
        'commands.community',
        'commands.leaderboard',
        'commands.fun',
        'commands.learning',
        'commands.utility',
        'commands.analytics',
        'events.message_handler',
        'events.member_events'
    ]
    
    for cog in cogs:
        try:
            await bot_instance.load_extension(cog)
            logger.info(f'Loaded {cog}')
        except Exception as e:
            logger.error(f'Failed to load {cog}: {e}')

# Daily QOTD task (runs at 9:00 AM UTC daily)
@tasks.loop(time=time(9, 0))
async def daily_qotd():
    from tasks.daily_qotd import post_daily_qotd
    await post_daily_qotd(bot, CHANNELS['questions'])

# Weekly challenge task (runs every Monday at 10:00 AM UTC)
@tasks.loop(time=time(10, 0))
async def weekly_challenge():
    from tasks.weekly_challenge import announce_weekly_challenge
    if datetime.utcnow().weekday() == 0:  # Monday
        await announce_weekly_challenge(bot, CHANNELS['staff_updates'])

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: `{error.param}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument provided!")
    else:
        logger.error(f'Unhandled error: {error}')
        await ctx.send("❌ An unexpected error occurred!")

# Keep-alive function for hosting
async def keep_alive():
    """Simple keep-alive server for hosting platforms"""
    from aiohttp import web
    
    async def health_check(request):
        uptime = datetime.now(timezone.utc) - bot.start_time
        return web.json_response({
            "status": "online",
            "uptime": str(uptime),
            "guilds": len(bot.guilds),
            "users": len(bot.users) if hasattr(bot, 'users') else 0
        })
    
    async def ping(request):
        return web.Response(text="pong")
    
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    app.router.add_get("/ping", ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()
    logger.info(f"Health server started on port {os.getenv('PORT', 8080)}")

# Main execution
# Global slash commands (always available)
@bot.tree.command(name="ping", description="Check if the bot is working")
async def ping(interaction: discord.Interaction):
    """Test command to check bot connectivity"""
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Bot is working! Latency: {latency}ms",
        color=0x00ff00
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="info", description="Get information about the bot")
async def info(interaction: discord.Interaction):
    """Display bot information"""
    embed = discord.Embed(
        title="🤖 CodeVerse Bot",
        description="A feature-rich Discord bot for programming communities!",
        color=0x00ff00
    )
    embed.add_field(name="📊 Servers", value=len(bot.guilds), inline=True)
    embed.add_field(name="👥 Users", value=len(bot.users), inline=True)
    embed.add_field(name="⏰ Uptime", value=f"<t:{int(bot.start_time.timestamp())}:R>", inline=True)
    embed.add_field(name="🔧 Commands", value="Use `/help` to see all commands", inline=False)
    await interaction.response.send_message(embed=embed)

async def main():
    """Main function to start the bot"""
    if not TOKEN:
        logger.error("Discord token not found! Please check your .env file.")
        return
    
    # Start keep-alive server for hosting
    from utils.keep_alive import keep_alive
    keep_alive()
    
    # Start the bot
    await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")