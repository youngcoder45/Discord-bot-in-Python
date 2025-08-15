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
                        COALESCE((SELECT xp FROM users WHERE user_id = ?), 0) + ?,
                        COALESCE((SELECT level FROM users WHERE user_id = ?), 1),
                        COALESCE((SELECT message_count FROM users WHERE user_id = ?), 0) + 1,
                        ?,
                        COALESCE((SELECT join_date FROM users WHERE user_id = ?), ?),
                        COALESCE((SELECT total_warnings FROM users WHERE user_id = ?), 0)
                    )
                ''', (user_id, username, user_id, xp_gain, user_id, user_id, 
                     now.isoformat(), user_id, now.isoformat(), user_id))
                
                # Update level based on XP
                await self._update_user_level(db, user_id)
                await db.commit()
    
    async def _update_user_level(self, db, user_id: int):
        """Calculate and update user level based on XP"""
        cursor = await db.execute('SELECT xp FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
        
        if result:
            xp = result[0]
            # Level formula: level = sqrt(xp / 100) + 1
            new_level = int((xp / 100) ** 0.5) + 1
            await db.execute('UPDATE users SET level = ? WHERE user_id = ?', (new_level, user_id))
    
    async def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Get user statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT xp, level, message_count, join_date, total_warnings
                FROM users WHERE user_id = ?
            ''', (user_id,))
            result = await cursor.fetchone()
            
            if result:
                return {
                    'xp': result[0],
                    'level': result[1], 
                    'message_count': result[2],
                    'join_date': result[3],
                    'total_warnings': result[4]
                }
            return None
    
    async def get_leaderboard(self, limit: int = 10) -> List[Tuple]:
        """Get XP leaderboard"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT user_id, username, xp, level, message_count
                FROM users 
                ORDER BY xp DESC 
                LIMIT ?
            ''', (limit,))
            return await cursor.fetchall()
    
    # Challenge Methods
    async def add_challenge_submission(self, user_id: int, challenge_id: str, submission_link: str):
        """Add a challenge submission"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO challenge_submissions (user_id, challenge_id, submission_link, submission_date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, challenge_id, submission_link, datetime.now(tz=timezone.utc).isoformat()))
            await db.commit()
    
    async def get_challenge_submissions(self, challenge_id: str) -> List[Tuple]:
        """Get submissions for a specific challenge"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT user_id, submission_link, submission_date, status
                FROM challenge_submissions 
                WHERE challenge_id = ?
                ORDER BY submission_date ASC
            ''', (challenge_id,))
            return await cursor.fetchall()
    
    # QOTD Methods
    async def add_qotd_submission(self, user_id: int, question_id: str, answer: str):
        """Add a QOTD submission"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO qotd_submissions (user_id, question_id, answer, submission_date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, question_id, answer, datetime.now(tz=timezone.utc).isoformat()))
            await db.commit()
    
    async def set_qotd_winner(self, user_id: int, question_id: str):
        """Set QOTD winner"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE qotd_submissions 
                SET is_winner = 1 
                WHERE user_id = ? AND question_id = ?
            ''', (user_id, question_id))
            await db.commit()
    
    async def get_qotd_winner(self, question_id: str) -> Optional[int]:
        """Get QOTD winner for a specific question"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT user_id FROM qotd_submissions 
                WHERE question_id = ? AND is_winner = 1
            ''', (question_id,))
            result = await cursor.fetchone()
            return result[0] if result else None
    
    # Moderation Methods
    async def add_warning(self, user_id: int, moderator_id: int, reason: str):
        """Add a warning to a user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO warnings (user_id, moderator_id, reason, warning_date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, moderator_id, reason, datetime.now(tz=timezone.utc).isoformat()))
            
            # Update user's total warnings count
            await db.execute('''
                UPDATE users 
                SET total_warnings = total_warnings + 1 
                WHERE user_id = ?
            ''', (user_id,))
            await db.commit()
    
    async def get_user_warnings(self, user_id: int) -> List[Tuple]:
        """Get all warnings for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT moderator_id, reason, warning_date
                FROM warnings 
                WHERE user_id = ?
                ORDER BY warning_date DESC
            ''', (user_id,))
            return await cursor.fetchall()
    
    async def add_mute(self, user_id: int, duration_minutes: int, reason: str, moderator_id: int):
        """Add a mute to a user"""
        muted_until = datetime.now(tz=timezone.utc) + timedelta(minutes=duration_minutes)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO mutes (user_id, muted_until, reason, moderator_id)
                VALUES (?, ?, ?, ?)
            ''', (user_id, muted_until.isoformat(), reason, moderator_id))
            await db.commit()
    
    async def remove_mute(self, user_id: int):
        """Remove a mute from a user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM mutes WHERE user_id = ?', (user_id,))
            await db.commit()
    
    async def is_user_muted(self, user_id: int) -> bool:
        """Check if a user is currently muted"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT muted_until FROM mutes WHERE user_id = ?
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