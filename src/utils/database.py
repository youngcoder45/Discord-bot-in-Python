import sqlite3
import discord
from datetime import datetime
from config import DATABASE_NAME

def init_db():
    """Initialize core tables used by the bot."""
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
    finally:
        try:
            conn.close()
        except Exception:
            pass

async def log_action(guild_id: int, user_id: int, moderator_id: int, action: str, reason: str):
    """Log moderation actions to legacy table (best effort)."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO moderation_log (guild_id, user_id, moderator_id, action, reason)
            VALUES (?, ?, ?, ?, ?)
        ''', (guild_id, user_id, moderator_id, action, reason))
        conn.commit()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass
