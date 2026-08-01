import sqlite3
import discord
from datetime import datetime
import logging
from config import DATABASE_NAME

logger = logging.getLogger(__name__)

def init_db():
    """Initialize core tables used by the bot."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS moderation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                moderator_id INTEGER,
                action TEXT,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unban_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                guild_id INTEGER,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.warning("Failed to close database connection: %s", e)

async def log_action(guild_id: int, user_id: int, moderator_id: int, action: str, reason: str):
    """Log moderation actions to legacy table (best effort)."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO moderation_log (guild_id, user_id, moderator_id, action, reason)
            VALUES (?, ?, ?, ?, ?)
        ''', (guild_id, user_id, moderator_id, action, reason))
        conn.commit()
    except Exception as e:
        logger.warning("Failed to log action to database: %s", e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.warning("Failed to close database connection: %s", e)
