import sqlite3
import discord
from datetime import datetime
from config import DATABASE_NAME, MODERATION_POINT_CAP, MODERATION_POINT_RESET_DAYS

# NOTE: This module now acts as a compatibility layer. The new point system lives in
# `commands/point_moderation.py`. We retain these functions so existing imports
# (e.g., protection.py) do not crash.

# Global data storage
moderation_points = {}
last_reset = datetime.utcnow()

def init_db():
    """Initialize legacy tables if still relied upon by old code."""
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
        # Keep legacy moderation_points for backward compatibility (not authoritative anymore)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS moderation_points (
                user_id INTEGER PRIMARY KEY,
                points INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
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

async def add_points(member: discord.Member, points: int, reason: str, moderator: discord.Member | None = None):
    """Compatibility wrapper: route to new point system if available, else legacy in-memory fallback."""
    guild = member.guild
    moderator_id = (moderator.id if moderator else (guild.me.id if guild and guild.me else member.id))
    guild_id = guild.id if guild else 0

    # Try new point system
    point_system = getattr(guild._state._get_client(), 'point_system', None) if guild else None
    if point_system:
        try:
            # Use underlying internal add (amount positive) and attribute action to moderator_id
            point_system._add_points_internal(guild_id, member.id, moderator_id, points, reason)
            await log_action(guild_id, member.id, moderator_id, f"Added {points} points (bridge)", reason)
            return
        except Exception:
            pass  # Fallback to legacy path

    # Legacy fallback (non-persistent except for log table)
    moderation_points[member.id] = moderation_points.get(member.id, 0) + points
    await log_action(guild_id, member.id, moderator_id, f"Added {points} points (legacy)", reason)

def get_user_points(user_id: int) -> int:
    """Get moderation points for a user"""
    return moderation_points.get(user_id, 0)

def clear_user_points(user_id: int) -> int:
    """Clear moderation points for a user and return the previous amount"""
    old_points = moderation_points.get(user_id, 0)
    if user_id in moderation_points:
        del moderation_points[user_id]
    return old_points

def reset_all_points():
    """Reset all moderation points"""
    global moderation_points, last_reset
    moderation_points.clear()
    last_reset = datetime.utcnow()