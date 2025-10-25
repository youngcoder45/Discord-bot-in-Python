import os
import logging
import asyncio
import discord
import time
from discord.ext import commands
from datetime import datetime, timezone
from dotenv import load_dotenv

from commands.modules.sam import bridge as sam_bridge
import atexit

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
intents.moderation = True  # Needed for audit log events

# Essential cogs only - Moderation, Management, and Core functionality
COGS_TO_LOAD = [
    # Core Commands (Essential)
    'commands.core',          # Core hybrid commands (ping, info, help menu)
    'commands.diagnostics',   # Diagnostics (?diag, /diag)
    
    # Logging System (Essential - LOAD FIRST)
    'commands.logging',       # Centralized logging system for all events
    
    # Moderation & Protection (Essential)
    'commands.modcog',        # Combined moderation commands with warnings system
    'commands.advanced_moderation',  # Advanced moderation with automod, tempban, mute, safety features
    'commands.protection',    # Protection features (anti-spam, anti-raid, anti-nuke)
    'commands.appeals',       # Appeal system for bans and mutes
    'commands.spam_catch',    # Spam detection and catching
    
    # Staff Management (Essential)
    'commands.staff_shifts',  # Staff shift tracking and logging system
    'commands.staff_points',  # Staff aura system with leaderboard
    
    # Data & Utility (Useful but not critical)
    'commands.data_management',  # Data backup and persistence management
    'commands.utility',       # Embed builder commands for announcements
    
    # Event Handlers (Essential)
    'events.member_events',   # Member join/leave event handlers
    'events.message_handler', # Auto-thanks system for staff aura
]

# REMOVED COGS (Non-essential fun/utility commands):
# - commands.utility_extra  # Fun commands: emotes, roll, remindme, randomcolor, inviteinfo
# - commands.roles          # Self-assignable ranks (file deleted during cleanup)

class CodeVerseBot(commands.Bot):
    def __init__(self):
        """Initialize the bot with desired prefix and intents."""
        # Prefix changed from '!' to '?' per request and intents configured
        super().__init__(command_prefix='?', intents=intents, help_command=None)
        self.start_time = datetime.now(timezone.utc)
        self.instance_id = INSTANCE_ID

    async def setup_hook(self):
        """Async setup tasks (load cogs, etc.)."""
        # CRITICAL: Restore data BEFORE initializing databases or loading cogs
        try:
            from utils.data_persistence import startup_restore
            logger.info("🔄 Restoring data before cog initialization...")
            await startup_restore()
            logger.info("✅ Data restoration completed")
        except Exception as e:
            logger.error(f"⚠️ Data restoration failed: {e}")
        
        # Initialize databases AFTER data restoration
        try:
            from utils.database_init import initialize_all_databases
            if initialize_all_databases():
                logger.info("🗄️ Database initialization completed")
            else:
                logger.warning("⚠️ Database initialization had issues")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")

        # Initialize SAM module's database
        try:
            # Import models first to ensure they are registered with SQLModel
            from commands.modules.sam.features.warnings.models import Warn
            from commands.modules.sam.internal.database import init_db
            # Create database tables
            await init_db()
            logger.info("✅ SAM module database initialized")
        except Exception as e:
            logger.error(f"❌ SAM module database initialization failed: {e}", exc_info=True)
        
        # Load all cogs
        for cog in COGS_TO_LOAD:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.warning(f"Failed to load cog {cog}: {e}")
                
        # Connect SAM logger to bot's logging channel
        try:
            sam_bridge.connect_log_consumer(self)
            logger.info("🔗 SAM logging bridge connected.")
        except Exception as e:
            logger.error(f"❌ Failed to connect SAM logging bridge: {e}")

bot = CodeVerseBot()

@bot.event
async def on_ready():
    if bot.user:
        logger.info(f"Logged in as {bot.user} (ID: {bot.user.id}) [Instance: {INSTANCE_ID}]")
    else:
        logger.info(f"Bot logged in [Instance: {INSTANCE_ID}]")
    
    # Security check: Ensure bot is only in authorized servers
    if GUILD_ID:
        unauthorized_servers = []
        for guild in bot.guilds:
            if guild.id != GUILD_ID:
                unauthorized_servers.append(guild)
        
        # Leave any unauthorized servers
        for guild in unauthorized_servers:
            logger.warning(f"🚫 Found bot in unauthorized server: {guild.name} (ID: {guild.id})")
            try:
                await guild.leave()
                logger.info(f"✅ Left unauthorized server: {guild.name}")
            except Exception as e:
                logger.error(f"❌ Failed to leave server {guild.name}: {e}")
        
        # Check if bot is in the correct server
        authorized_guild = bot.get_guild(GUILD_ID)
        if authorized_guild:
            logger.info(f"✅ Bot is operating in authorized server: {authorized_guild.name}")
        else:
            logger.warning(f"⚠️ Bot is not in the configured server (ID: {GUILD_ID})")
    
    # Start periodic backup task (every 6 hours)
    try:
        from utils.data_persistence import start_periodic_backup
        await start_periodic_backup()
        logger.info("🔄 Periodic backup system started")
    except Exception as e:
        logger.error(f"⚠️ Periodic backup system failed to start: {e}")
    
    # Sync slash commands
    try:
        # Try global sync first
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash commands globally")
        
        # If we have a guild ID, also sync to guild for faster updates
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            guild_synced = await bot.tree.sync(guild=guild)
            logger.info(f"Synced {len(guild_synced)} commands to guild {GUILD_ID}")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")
    
    # Both prefix (?ping) and slash (/ping) commands are now available

@bot.event
async def on_guild_join(guild):
    """Security: Auto-leave any unauthorized servers"""
    # The allowed server ID is loaded from GUILD_ID in .env file
    # Currently set to: 1263067254153805905 (your server)
    ALLOWED_SERVER_ID = GUILD_ID
    
    if guild.id != ALLOWED_SERVER_ID:
        logger.warning(f"🚫 Bot was added to unauthorized server: {guild.name} (ID: {guild.id})")
        
        # Try to send a message to the owner if possible
        try:
            if guild.owner:
                embed = discord.Embed(
                    title="🚫 Unauthorized Server Access",
                    description=f"This bot is exclusive to a specific server and cannot be used here.\n\n"
                               f"Server: {guild.name}\n"
                               f"Server ID: {guild.id}\n\n"
                               f"The bot will now leave this server automatically.",
                    color=discord.Color.red()
                )
                await guild.owner.send(embed=embed)
        except Exception as e:
            logger.warning(f"Could not notify server owner: {e}")
        
        # Leave the unauthorized server
        await guild.leave()
        logger.info(f"✅ Successfully left unauthorized server: {guild.name}")
    else:
        logger.info(f"✅ Bot joined authorized server: {guild.name}")

def cleanup():
    """Run cleanup tasks before the bot process exits."""
    # Disconnect SAM logger
    try:
        sam_bridge.disconnect_log_consumer()
        logger.info("🔌 SAM logging bridge disconnected.")
    except Exception as e:
        logger.error(f"❌ Failed to disconnect SAM logging bridge: {e}")
    
    # Clean up the instance lock file
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
            logger.info(f"Removed instance lock file: {LOCK_FILE}")
    except Exception as e:
        logger.error(f"Failed to remove lock file: {e}")

atexit.register(cleanup)

@bot.event
async def on_connect():
    logger.info(f"Bot connected to Discord Gateway [Instance: {INSTANCE_ID}]")

@bot.event
async def on_disconnect():
    logger.info(f"Bot disconnected from Discord Gateway [Instance: {INSTANCE_ID}]")

async def main():
    if not TOKEN:
        logger.error("DISCORD_TOKEN not set.")
        return
    # Single-instance guard (avoid duplicate handlers)
    if os.getenv('ALLOW_MULTIPLE_INSTANCES', '0') != '1':
        try:
            if os.path.exists(LOCK_FILE):
                with open(LOCK_FILE, 'r', encoding='utf-8') as lf:
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
            with open(LOCK_FILE, 'w', encoding='utf-8') as f:
                f.write(f"{os.getpid()}|{time.time()}|{INSTANCE_ID}")
            # Register cleanup
            def _cleanup():
                try:
                    if os.path.exists(LOCK_FILE):
                        with open(LOCK_FILE, 'r', encoding='utf-8') as lf:
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