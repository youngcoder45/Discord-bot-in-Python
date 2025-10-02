import sqlite3
import discord
from datetime import datetime
from config import DATABASE_NAME, MODERATION_POINT_CAP, MODERATION_POINT_RESET_DAYS

# Global data storage
moderation_points = {}
last_reset = datetime.utcnow()

def init_db():
    """Initialize the database with required tables"""
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS moderation_points (
            user_id INTEGER PRIMARY KEY,
            points INTEGER DEFAULT 0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

async def log_action(guild_id: int, user_id: int, moderator_id: int, action: str, reason: str):
    """Log moderation actions to database"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO moderation_log (guild_id, user_id, moderator_id, action, reason)
        VALUES (?, ?, ?, ?, ?)
    ''', (guild_id, user_id, moderator_id, action, reason))
    conn.commit()
    conn.close()

async def add_points(member: discord.Member, points: int, reason: str, moderator: discord.Member | None = None):
    """Add moderation points to a user"""
    from utils.embeds import create_points_embed, create_ban_embed
    
    user_id = member.id
    guild_id = member.guild.id
    moderator_id = moderator.id if moderator else member.guild.me.id
    
    # Update points
    moderation_points[user_id] = moderation_points.get(user_id, 0) + points
    
    # Log the action
    await log_action(guild_id, user_id, moderator_id, f"Added {points} points", reason)
    
    # Check if user should be banned
    if moderation_points[user_id] >= MODERATION_POINT_CAP:
        try:
            await member.ban(reason=f'Reached {MODERATION_POINT_CAP} moderation points: {reason}')
            await log_action(guild_id, user_id, moderator_id, "Auto-ban", f"Reached {MODERATION_POINT_CAP} points")
            
            # Send DM to banned user
            try:
                embed = create_ban_embed(member.guild.name, reason)
                await member.send(embed=embed)
            except:
                pass
        except discord.Forbidden:
            pass
    else:
        # Send points notification
        try:
            embed = create_points_embed(member.guild.name, points, reason, moderation_points[user_id])
            await member.send(embed=embed)
        except:
            pass

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