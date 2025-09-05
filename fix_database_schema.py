#!/usr/bin/env python3
"""
Database Migration Script - Fix staff_points schema inconsistencies
Fixes the database schema to match what the code expects
"""
import sqlite3
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

# Load environment
from dotenv import load_dotenv
load_dotenv()

def migrate_staff_points_database():
    """Migrate staff_points database to correct schema"""
    print("🔧 MIGRATING STAFF_POINTS DATABASE SCHEMA")
    print("=" * 50)
    
    db_path = "data/staff_points.db"
    
    if not os.path.exists(db_path):
        print("ℹ️ No existing staff_points.db found - will be created with correct schema")
        return True
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Existing tables: {existing_tables}")
        
        # 1. Migrate from old staff_aura table to new staff_points table
        if 'staff_aura' in existing_tables and 'staff_points' not in existing_tables:
            print("🔄 Migrating staff_aura -> staff_points...")
            
            # Get guild_id from environment
            guild_id = int(os.getenv('GUILD_ID', 1263067254153805905))
            
            # Create new staff_points table with correct schema
            cursor.execute('''
                CREATE TABLE staff_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    points INTEGER DEFAULT 0,
                    total_earned INTEGER DEFAULT 0,
                    total_spent INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, user_id)
                )
            ''')
            
            # Copy data from staff_aura to staff_points
            cursor.execute('''
                INSERT INTO staff_points (guild_id, user_id, points, total_earned, total_spent, last_updated)
                SELECT ?, user_id, aura, total_earned, total_spent, last_updated 
                FROM staff_aura
            ''', (guild_id,))
            
            rows_migrated = cursor.rowcount
            print(f"✅ Migrated {rows_migrated} records from staff_aura to staff_points")
            
            # Drop old table
            cursor.execute("DROP TABLE staff_aura")
            print("🗑️ Dropped old staff_aura table")
        
        # 2. Migrate from old aura_history table to new points_history table
        if 'aura_history' in existing_tables and 'points_history' not in existing_tables:
            print("🔄 Migrating aura_history -> points_history...")
            
            # Get guild_id from environment
            guild_id = int(os.getenv('GUILD_ID', 1263067254153805905))
            
            # Create new points_history table with correct schema
            cursor.execute('''
                CREATE TABLE points_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    points_change INTEGER NOT NULL,
                    reason TEXT,
                    action_type TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Copy data from aura_history to points_history
            # Map admin_id -> moderator_id and change_amount -> points_change
            cursor.execute('''
                INSERT INTO points_history (guild_id, user_id, moderator_id, points_change, reason, action_type, timestamp)
                SELECT ?, user_id, COALESCE(admin_id, 0), change_amount, reason, 
                       COALESCE(change_type, 'manual'), timestamp 
                FROM aura_history
            ''', (guild_id,))
            
            rows_migrated = cursor.rowcount
            print(f"✅ Migrated {rows_migrated} history records from aura_history to points_history")
            
            # Drop old table
            cursor.execute("DROP TABLE aura_history")
            print("🗑️ Dropped old aura_history table")
        
        # 3. Create staff_config table if it doesn't exist
        if 'staff_config' not in existing_tables:
            print("🔄 Creating staff_config table...")
            cursor.execute('''
                CREATE TABLE staff_config (
                    guild_id INTEGER PRIMARY KEY,
                    staff_role_ids TEXT,
                    points_channel_id INTEGER,
                    auto_rewards TEXT,
                    daily_bonus INTEGER DEFAULT 0,
                    weekly_bonus INTEGER DEFAULT 0
                )
            ''')
            print("✅ Created staff_config table")
        
        # 4. Check if points_history table has correct columns
        if 'points_history' in existing_tables:
            cursor.execute("PRAGMA table_info(points_history)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"📋 points_history columns: {columns}")
            
            # Check for admin_id column and fix it
            if 'admin_id' in columns and 'moderator_id' not in columns:
                print("🔄 Renaming admin_id -> moderator_id in points_history...")
                
                # Create new table with correct schema
                cursor.execute('''
                    CREATE TABLE points_history_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        moderator_id INTEGER NOT NULL,
                        points_change INTEGER NOT NULL,
                        reason TEXT,
                        action_type TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Copy data, mapping column names
                cursor.execute('''
                    INSERT INTO points_history_new (id, guild_id, user_id, moderator_id, points_change, reason, action_type, timestamp)
                    SELECT id, guild_id, user_id, admin_id, 
                           CASE WHEN amount IS NOT NULL THEN amount ELSE points_change END,
                           reason, action_type, timestamp
                    FROM points_history
                ''')
                
                # Replace old table
                cursor.execute("DROP TABLE points_history")
                cursor.execute("ALTER TABLE points_history_new RENAME TO points_history")
                print("✅ Fixed points_history column names")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 Database migration completed successfully!")
        
        # Verify the new schema
        verify_schema()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_schema():
    """Verify the database has the correct schema"""
    print("\n🔍 VERIFYING DATABASE SCHEMA")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect("data/staff_points.db")
        cursor = conn.cursor()
        
        # Check staff_points table
        cursor.execute("PRAGMA table_info(staff_points)")
        columns = [row[1] for row in cursor.fetchall()]
        expected_staff_points = ['id', 'guild_id', 'user_id', 'points', 'total_earned', 'total_spent', 'last_updated']
        
        print("📊 staff_points table:")
        for col in expected_staff_points:
            status = "✅" if col in columns else "❌"
            print(f"  {status} {col}")
        
        # Check points_history table
        cursor.execute("PRAGMA table_info(points_history)")
        columns = [row[1] for row in cursor.fetchall()]
        expected_points_history = ['id', 'guild_id', 'user_id', 'moderator_id', 'points_change', 'reason', 'action_type', 'timestamp']
        
        print("\n📋 points_history table:")
        for col in expected_points_history:
            status = "✅" if col in columns else "❌"
            print(f"  {status} {col}")
        
        # Check data counts
        cursor.execute("SELECT COUNT(*) FROM staff_points")
        staff_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM points_history")
        history_count = cursor.fetchone()[0]
        
        print(f"\n📊 Data counts:")
        print(f"  • staff_points: {staff_count} records")
        print(f"  • points_history: {history_count} records")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")

if __name__ == "__main__":
    print("🔧 DATABASE SCHEMA MIGRATION TOOL")
    print("=" * 60)
    print("This script fixes database schema inconsistencies in staff_points.db")
    print()
    
    success = migrate_staff_points_database()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("✅ Your auto-thanks system should now work properly")
        print("✅ All staff aura data has been preserved")
    else:
        print("\n❌ Migration failed!")
        print("⚠️ Please check the error messages above")
    
    exit(0 if success else 1)
