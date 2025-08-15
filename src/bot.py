import os, logging, asyncio, discord
from discord.ext import commands
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables once at startup
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("codeverse.bot")

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID', 0))

intents = discord.Intents.default()
intents.message_content = True  # Needed for legacy text commands
intents.members = True
intents.guilds = True
intents.reactions = True

COGS_TO_LOAD = [
    'commands.core',          # New core hybrid commands (ping, info)
    'commands.utility',
    'commands.analytics',      # May be partial / placeholder
    'commands.community',
    'commands.learning',
    'commands.fun',
    'events.member_events',
    'events.message_handler'   # Simplified; XP system removed
]

class CodeVerseBot(commands.Bot):
    def __init__(self):
        # Prefix changed from '!' to '?' per request and intents configured
        super().__init__(command_prefix='?', intents=intents, help_command=None)
        self.start_time = datetime.now(timezone.utc)

    async def setup_hook(self):
        # Load cogs
        for cog in COGS_TO_LOAD:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.warning(f"Failed to load cog {cog}: {e}")

bot = CodeVerseBot()

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync(guild=None)  # Global sync
        logger.info(f"Synced {len(synced)} global application commands")
    except Exception as e:
        logger.warning(f"Slash command sync failed: {e}")

# NOTE: ping & info have been moved to a hybrid Cog at commands/core.py so they work
#       both as slash commands (/ping, /info) and prefix commands (?ping, ?info).

async def main():
    if not TOKEN:
        logger.error("DISCORD_TOKEN not set.")
        return
    # Start lightweight keep-alive server (optional)
    try:
        from utils.keep_alive import keep_alive
        keep_alive()
    except Exception as e:
        logger.warning(f"Keep-alive server failed to start: {e}")
    await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as exc:
        logger.error(f"Fatal error: {exc}")