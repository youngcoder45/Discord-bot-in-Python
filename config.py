# ModBot Configuration
import os
from dotenv import load_dotenv

load_dotenv()

# Bot Token
BOT_TOKEN = os.getenv('DISCORD_TOKEN') or os.getenv('BOT_TOKEN')

# Configuration
MODERATION_ROLE_ID = int(os.getenv('MODERATION_ROLE_ID', 1403059755001577543))
MODERATION_POINT_CAP = int(os.getenv('MODERATION_POINT_CAP', 100))
MODERATION_POINT_RESET_DAYS = int(os.getenv('MODERATION_POINT_RESET_DAYS', 30))

# Bot settings (actual prefix is '?' in src/bot.py; this was legacy)
STATUS_MESSAGE = os.getenv('STATUS_MESSAGE', 'Professional Moderation | !help')

# Appeals system settings
APPEALS_MODERATOR_USER_ID = int(os.getenv('APPEALS_MODERATOR_USER_ID', '1403059755001577543'))
APPEALS_LOG_CHANNEL_IDS = [
    int(x.strip())
    for x in os.getenv('APPEALS_LOG_CHANNEL_IDS', '1423642446616592385,1444013659134361703').split(',')
    if x.strip()
]

# Database settings
DATABASE_NAME = os.getenv('DATABASE_NAME', 'data/modbot.db')

# Logging settings
LOG_CHANNEL_NAME = os.getenv('LOG_CHANNEL_NAME', 'mod-logs')