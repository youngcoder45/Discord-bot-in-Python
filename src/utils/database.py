import aiosqlite
import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple

class Database:
    def __init__(self, db_path: str = 'data/codeverse_bot.db'):
        self.db_path = db_path
        self.ensure_directory()
        
    def ensure_directory(self):
        """Ensure the database directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    async def init_db(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table for XP and activity tracking
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    message_count INTEGER DEFAULT 0,
                    last_xp_gain TEXT,
                    join_date TEXT,
                    total_warnings INTEGER DEFAULT 0
                )
            ''')
            
            # Challenge submissions table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS challenge_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    challenge_id TEXT,
                    submission_link TEXT,
                    submission_date TEXT,
                    status TEXT DEFAULT 'pending'
                )
            ''')
            
            # QOTD submissions table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS qotd_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    question_id TEXT,
                    answer TEXT,
                    submission_date TEXT,
                    is_winner BOOLEAN DEFAULT 0
                )
            ''')
            
            # Warnings table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    moderator_id INTEGER,
                    reason TEXT,
                    warning_date TEXT
                )
            ''')
            
            # Suggestions table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    suggestion TEXT,
                    suggestion_date TEXT,
                    status TEXT DEFAULT 'pending'
                )
            ''')
            
            # AFK table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS afk_users (
                    user_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    afk_since TEXT
                )
            ''')
            
            # Mutes table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS mutes (
                    user_id INTEGER PRIMARY KEY,
                    muted_until TEXT,
                    reason TEXT,
                    moderator_id INTEGER
                )
            ''')
            
            await db.commit()
    
    # User XP and Activity Methods
    async def add_user(self, user_id: int, username: str):
        """Add a new user to the database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR IGNORE INTO users (user_id, username, join_date)
                VALUES (?, ?, ?)
            ''', (user_id, username, datetime.now(tz=timezone.utc).isoformat()))
            await db.commit()
    
    async def update_user_activity(self, user_id: int, username: str, xp_gain: int = 5):
        """Update user activity and XP"""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if user can gain XP (cooldown of 1 minute)
            cursor = await db.execute('''
                SELECT last_xp_gain FROM users WHERE user_id = ?
            ''', (user_id,))
            result = await cursor.fetchone()
            
            now = datetime.now(tz=timezone.utc)
            can_gain_xp = True
            
            if result and result[0]:
                last_gain = datetime.fromisoformat(result[0])
                can_gain_xp = (now - last_gain).total_seconds() > 60
            
            if can_gain_xp:
                await db.execute('''
                    INSERT OR REPLACE INTO users (
                        user_id, username, xp, level, message_count, last_xp_gain, join_date, total_warnings
                    ) VALUES (
                        ?, ?,

                        """Deprecated database layer.

                        The original SQLite / XP system was removed in favor of lightweight JSON
                        storage (`utils/json_store.py`). This module is kept as a stub so legacy
                        imports don't crash. All methods are no‑ops.
                        """

                        import warnings

                        class Database:
                            def __init__(self):
                                warnings.warn(
                                    "utils.database is deprecated – XP/SQL features removed. Use utils.json_store instead.",
                                    DeprecationWarning,
                                    stacklevel=2,
                                )

                            async def init_db(self):
                                return

                            # Generic no-op methods maintained for backward compatibility
                            def __getattr__(self, name):  # Called for any missing async method
                                async def _noop(*args, **kwargs):
                                    return None
                                return _noop

                        db = Database()

                        async def init_database():  # Legacy entry point
                            await db.init_db()

                        COALESCE((SELECT xp FROM users WHERE user_id = ?), 0) + ?,
                        """Deprecated database layer (stub).

                        The original SQLite-based XP / activity system has been removed. This stub
                        is kept so legacy imports (`from utils.database import db`) do not break.
                        All operations are no-ops. Use `utils.json_store` for persistence.
                        """

                        import warnings

                        class Database:
                            def __init__(self):
                                warnings.warn(
                                    "utils.database is deprecated – use utils.json_store instead.",
                                    DeprecationWarning,
                                    stacklevel=2
                                )

                            async def init_db(self):  # legacy entry point
                                return

                            def __getattr__(self, name):
                                async def _noop(*args, **kwargs):
                                    return None
                                return _noop

                        db = Database()

                        async def init_database():
                            await db.init_db()
            ''', (user_id,))
            result = await cursor.fetchone()
            
            if result:
                muted_until = datetime.fromisoformat(result[0])
                if datetime.now(tz=timezone.utc) < muted_until:
                    return True
                else:
                    await self.remove_mute(user_id)
            return False
    
    # Suggestions
    async def add_suggestion(self, user_id: int, suggestion: str):
        """Add a suggestion"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO suggestions (user_id, suggestion, suggestion_date)
                VALUES (?, ?, ?)
            ''', (user_id, suggestion, datetime.now(tz=timezone.utc).isoformat()))
            await db.commit()
    
    # AFK System
    async def set_user_afk(self, user_id: int, reason: str, afk_since: str):
        """Set user as AFK"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO afk_users (user_id, reason, afk_since)
                VALUES (?, ?, ?)
            ''', (user_id, reason, afk_since))
            await db.commit()
    
    async def remove_user_afk(self, user_id: int):
        """Remove user from AFK"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM afk_users WHERE user_id = ?', (user_id,))
            await db.commit()
    
    async def get_user_afk(self, user_id: int):
        """Get user AFK status"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT reason, afk_since FROM afk_users WHERE user_id = ?
            ''', (user_id,))
            return await cursor.fetchone()

# Create global database instance
db = Database()

async def init_database():
    """Initialize the database"""
    await db.init_db()