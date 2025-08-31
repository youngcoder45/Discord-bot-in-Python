"""
Database Initialization Utility
Ensures all required databases exist before bot startup
"""
import os
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger("codeverse.database_init")

def initialize_all_databases():
    """Initialize all required databases with proper schema"""
    try:
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        logger.info("📁 Data directory ensured")
        
        # Initialize staff_shifts.db
        init_staff_shifts_db()
        
        # Initialize staff_points.db
        init_staff_points_db()
        
        # Initialize main bot database
        init_main_bot_db()
        
        logger.info("✅ All databases initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

def init_staff_shifts_db():
    """Initialize staff shifts database"""
    db_path = "data/staff_shifts.db"
    
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            start_note TEXT,
            end_note TEXT,
            guild_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS shift_settings (
            guild_id INTEGER PRIMARY KEY,
            log_channel_id INTEGER,
            staff_roles TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ staff_shifts.db initialized")

def init_staff_points_db():
    """Initialize staff points (aura) database"""
    db_path = "data/staff_points.db"
    
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS staff_aura (
            user_id INTEGER PRIMARY KEY,
            aura INTEGER DEFAULT 0,
            total_earned INTEGER DEFAULT 0,
            total_spent INTEGER DEFAULT 0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS aura_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            change_amount INTEGER NOT NULL,
            change_type TEXT NOT NULL,
            reason TEXT,
            admin_id INTEGER,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ staff_points.db initialized")

def init_main_bot_db():
    """Initialize main bot database for general data"""
    db_path = "data/codeverse_bot.db"
    
    conn = sqlite3.connect(db_path)
    
    # Elections table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS elections (
            guild_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            candidates TEXT NOT NULL,
            votes TEXT DEFAULT '{}',
            end_time TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # General settings table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            guild_id INTEGER PRIMARY KEY,
            settings_json TEXT DEFAULT '{}'
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ codeverse_bot.db initialized")

if __name__ == "__main__":
    # Allow running this file directly for testing
    logging.basicConfig(level=logging.INFO)
    initialize_all_databases()
