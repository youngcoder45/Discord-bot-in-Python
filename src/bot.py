import os
import logging
import asyncio
import discord
import time
import atexit
from discord.ext import commands
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables once at startup
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("codeverse.bot")

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID', 0))
INSTANCE_ID = os.getenv('INSTANCE_ID', f"pid-{os.getpid()}")
LOCK_FILE = os.getenv('BOT_LOCK_FILE', '.bot_instance.lock')

intents = discord.Intents.default()
intents.message_content = True  # Needed for legacy text commands
intents.members = True
intents.guilds = True
intents.reactions = True

COGS_TO_LOAD = [
    'commands.core',          # Core hybrid commands (ping, info, help)
    'commands.diagnostics',   # Diagnostics (?diag, /diag)
    'commands.community',     # quote, question, meme, suggest
    'commands.fun',           # fun & game commands
    'events.member_events',
    'events.message_handler', # Simplified message handler
    'tasks.staff_reminder'    # Staff bump reminder every 2 hours
]

class CodeVerseBot(commands.Bot):
    def __init__(self):
        """Initialize the bot with desired prefix and intents."""
        # Prefix changed from '!' to '?' per request and intents configured
        super().__init__(command_prefix='?', intents=intents, help_command=None)
        self.start_time = datetime.now(timezone.utc)
        self.instance_id = INSTANCE_ID

    async def setup_hook(self):
        """Async setup tasks (load cogs, etc.)."""
        for cog in COGS_TO_LOAD:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.warning(f"Failed to load cog {cog}: {e}")

bot = CodeVerseBot()

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id}) [Instance: {INSTANCE_ID}]")
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash commands")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")
    
    # Both prefix (?ping) and slash (/ping) commands are now available

async def main():
    if not TOKEN:
        logger.error("DISCORD_TOKEN not set.")
        return
    # Single-instance guard (avoid duplicate handlers)
    if os.getenv('ALLOW_MULTIPLE_INSTANCES', '0') != '1':
        try:
            if os.path.exists(LOCK_FILE):
                    with open(LOCK_FILE,'r',encoding='utf-8') as lf:
                        prev_data = lf.read().strip().split('|')
                    if len(prev_data) == 3:
                        prev_pid, prev_ts, prev_id = prev_data
                        # If PID still alive (best effort) and lock age < 10 min -> block
                        lock_age = time.time() - float(prev_ts)
                        pid_alive = False
                        try:
                            os.kill(int(prev_pid), 0)
                            pid_alive = True
                        except Exception:
                            pid_alive = False
                        if lock_age < 600 and pid_alive and prev_id != INSTANCE_ID:
                            logger.error("Another bot instance running (pid=%s id=%s age=%ss).", prev_pid, prev_id, int(lock_age))
                            return
            with open(LOCK_FILE,'w',encoding='utf-8') as f:
                f.write(f"{os.getpid()}|{time.time()}|{INSTANCE_ID}")
                # Register cleanup
                def _cleanup():
                    try:
                        if os.path.exists(LOCK_FILE):
                            with open(LOCK_FILE,'r',encoding='utf-8') as lf:
                                content = lf.read().strip()
                            if content.startswith(str(os.getpid())):
                                os.remove(LOCK_FILE)
                    except Exception:
                        pass
                atexit.register(_cleanup)
        except Exception as e:
            logger.warning(f"Instance lock handling failed: {e}")
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