# ModBot Configuration
import os
from dotenv import load_dotenv

load_dotenv()

# Bot Token
BOT_TOKEN = os.getenv('DISCORD_TOKEN') or os.getenv('BOT_TOKEN')


def _env_int(name: str, default: int) -> int:
    """Read an integer environment variable, falling back to a default."""
    return int(os.getenv(name, default))


def _env_int_list(name: str, default: str) -> list[int]:
    """Read a comma-separated list of integers from an environment variable."""
    return [
        int(x.strip())
        for x in os.getenv(name, default).split(',')
        if x.strip()
    ]


# =============================================================================
# Discord IDs (all overridable via .env)
# The literals below are fallback defaults so the bot keeps working even if a
# variable is missing from .env.
# =============================================================================

# --- Guilds ---
AUTHORIZED_GUILD_IDS = _env_int_list(
    'AUTHORIZED_GUILD_IDS', '1410939321812258928,1263067254153805905'
)
MAIN_GUILD_ID = _env_int('MAIN_GUILD_ID', 1263067254153805905)

# --- Roles ---
MODERATION_ROLE_ID = _env_int('MODERATION_ROLE_ID', 1403059755001577543)
STAFF_ROLE_ID = _env_int('STAFF_ROLE_ID', 1417900662053671073)
ADMIN_BYPASS_ROLE_ID = _env_int('ADMIN_BYPASS_ROLE_ID', 1403059755001577543)
HELP_MODERATOR_ROLE_ID = _env_int('HELP_MODERATOR_ROLE_ID', 1403059755001577543)
VERIFY_STREAM_ROLE_ID = _env_int('VERIFY_STREAM_ROLE_ID', 1417578146407911455)
VERIFY_VOICE_ROLE_ID = _env_int('VERIFY_VOICE_ROLE_ID', 1414651719995883560)
VERIFY_EMBED_ROLE_ID = _env_int('VERIFY_EMBED_ROLE_ID', 1486406987091677315)
VERIFY_JOIN_VC_ROLE_ID = _env_int('VERIFY_JOIN_VC_ROLE_ID', 1345308261133455430)

# --- Users ---
BOT_OWNER_ID = _env_int('BOT_OWNER_ID', 955695820999639120)
APPEALS_MODERATOR_USER_ID = _env_int('APPEALS_MODERATOR_USER_ID', 1403059755001577543)

# --- Channels ---
INTRODUCTION_CHANNEL_ID = _env_int('INTRODUCTION_CHANNEL_ID', 1263070188589547541)
WELCOME_ROLES_CHANNEL_ID = _env_int('WELCOME_ROLES_CHANNEL_ID', 1263070845098655744)
WELCOME_GENERAL_CHANNEL_ID = _env_int('WELCOME_GENERAL_CHANNEL_ID', 1263067254803796030)
WELCOME_IDEAS_CHANNEL_ID = _env_int('WELCOME_IDEAS_CHANNEL_ID', 1347581046753067050)
HELP_FORUM_ID = _env_int('HELP_FORUM_ID', 1388169643234955354)
WELCOME_TICKET_CHANNEL_ID = _env_int('WELCOME_TICKET_CHANNEL_ID', 1410169473180241971)
HELP_NOTIFY_TARGET_CHANNEL_ID = _env_int('HELP_NOTIFY_TARGET_CHANNEL_ID', 1456979344504258570)
HELP_GUIDE_CHANNEL_ID = _env_int('HELP_GUIDE_CHANNEL_ID', 1419678687103680522)
REPORT_CHANNEL_ID = _env_int('REPORT_CHANNEL_ID', 1418492683277570109)
PROTECTED_CHANNEL_ID = _env_int('PROTECTED_CHANNEL_ID', 1430566219643228210)
TICKET_LOGS_CHANNEL_ID = _env_int('TICKET_LOGS_CHANNEL_ID', 1438487366305190018)

# --- Logging channels (default destinations for LOG_CHANNEL_MAP) ---
LOG_CHANNEL_MEMBERS_ID = _env_int('LOG_CHANNEL_MEMBERS_ID', 1460213277333389412)
LOG_CHANNEL_ROLES_ID = _env_int('LOG_CHANNEL_ROLES_ID', 1460207115082661984)
LOG_CHANNEL_CHANNELS_ID = _env_int('LOG_CHANNEL_CHANNELS_ID', 1460207608119038034)
LOG_CHANNEL_TIMEOUTS_ID = _env_int('LOG_CHANNEL_TIMEOUTS_ID', 1460207558605275188)
LOG_CHANNEL_VOICE_ID = _env_int('LOG_CHANNEL_VOICE_ID', 1460207532814503986)
LOG_CHANNEL_WARNINGS_ID = _env_int('LOG_CHANNEL_WARNINGS_ID', 1460207507703070813)
LOG_CHANNEL_MEMBER_ROLE_CHANGES_ID = _env_int(
    'LOG_CHANNEL_MEMBER_ROLE_CHANGES_ID', 1460207477248495716
)
LOG_CHANNEL_MODERATION_ID = _env_int('LOG_CHANNEL_MODERATION_ID', 1460207055745978611)
LOG_CHANNEL_TICKETS_ID = _env_int('LOG_CHANNEL_TICKETS_ID', 1438487366305190018)
LOG_CHANNEL_STAFF_POINTS_ID = _env_int('LOG_CHANNEL_STAFF_POINTS_ID', 1454024682700537968)

# =============================================================================
# Other settings
# =============================================================================

# Configuration
MODERATION_POINT_CAP = _env_int('MODERATION_POINT_CAP', 100)
MODERATION_POINT_RESET_DAYS = _env_int('MODERATION_POINT_RESET_DAYS', 30)

# Bot settings (actual prefix is '?' in src/bot.py; this was legacy)
STATUS_MESSAGE = os.getenv('STATUS_MESSAGE', 'Professional Moderation | !help')

# Appeals system settings
APPEALS_LOG_CHANNEL_IDS = [
    int(x.strip())
    for x in os.getenv('APPEALS_LOG_CHANNEL_IDS', '1423642446616592385,1444013659134361703').split(',')
    if x.strip()
]

# Database settings
DATABASE_NAME = os.getenv('DATABASE_NAME', 'data/modbot.db')

# Logging settings
LOG_CHANNEL_NAME = os.getenv('LOG_CHANNEL_NAME', 'mod-logs')
