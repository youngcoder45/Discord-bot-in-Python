# ModBot Configuration
import os
from dotenv import load_dotenv

load_dotenv()

# Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_TOKEN_HERE')

# Configuration
MODERATION_ROLE_ID = 1403059755001577543
MODERATION_POINT_CAP = 100
MODERATION_POINT_RESET_DAYS = 30

# Anti-spam settings
SPAM_THRESHOLD = 5  # messages per time window
SPAM_TIME_WINDOW = 10  # seconds
DUPLICATE_THRESHOLD = 3  # duplicate messages
MENTION_THRESHOLD = 5  # mentions per message
CAPS_THRESHOLD = 0.7  # percentage of caps

# Anti-raid settings
JOIN_THRESHOLD = 10  # joins per time window
JOIN_TIME_WINDOW = 60  # seconds
NEW_ACCOUNT_THRESHOLD = 7  # days

# Anti-nuke settings
MASS_DELETE_THRESHOLD = 20  # messages deleted
MASS_BAN_THRESHOLD = 5  # bans in short time
MASS_KICK_THRESHOLD = 5  # kicks in short time
NUKE_TIME_WINDOW = 300  # 5 minutes

# Bot settings
COMMAND_PREFIX = '!'
STATUS_MESSAGE = 'Professional Moderation | !help'

# Database settings
DATABASE_NAME = 'modbot.db'

# Logging settings
LOG_CHANNEL_NAME = 'mod-logs'
STAFF_ALERT_CHANNEL = 'staff-alerts'