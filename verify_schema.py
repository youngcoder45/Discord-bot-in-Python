#!/usr/bin/env python3
"""
Database Schema Verification Script
"""

import sqlite3
import sys
from pathlib import Path

def check_database_schema():
    """Check that database schemas match code expectations"""
    
    print("🔍 Checking database schemas...")
    
    # Check staff_shifts.db
    try:
        conn = sqlite3.connect("data/staff_shifts.db")
        cursor = conn.cursor()
        
        # Check shifts table schema
        cursor.execute("PRAGMA table_info(shifts)")
        shifts_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 shifts table columns: {shifts_columns}")
        
        expected_shifts = ['shift_id', 'guild_id', 'user_id', 'start', 'end', 'start_note', 'end_note']
        missing_shifts = [col for col in expected_shifts if col not in shifts_columns]
        
        if missing_shifts:
            print(f"❌ Missing columns in shifts table: {missing_shifts}")
        else:
            print("✅ shifts table schema is correct")
        
        # Check shift_settings table schema
        cursor.execute("PRAGMA table_info(shift_settings)")
        settings_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 shift_settings table columns: {settings_columns}")
        
        expected_settings = ['guild_id', 'log_channel_id', 'staff_role_ids']
        missing_settings = [col for col in expected_settings if col not in settings_columns]
        
        if missing_settings:
            print(f"❌ Missing columns in shift_settings table: {missing_settings}")
        else:
            print("✅ shift_settings table schema is correct")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking staff_shifts.db: {e}")
        return False
    
    # Check staff_points.db
    try:
        conn = sqlite3.connect("data/staff_points.db")
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(staff_aura)")
        aura_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 staff_aura table columns: {aura_columns}")
        
        expected_aura = ['user_id', 'aura', 'total_earned', 'total_spent', 'last_updated']
        missing_aura = [col for col in expected_aura if col not in aura_columns]
        
        if missing_aura:
            print(f"❌ Missing columns in staff_aura table: {missing_aura}")
        else:
            print("✅ staff_aura table schema is correct")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking staff_points.db: {e}")
        return False
    
    print("\n🎉 Database schema verification complete!")
    return True

if __name__ == "__main__":
    success = check_database_schema()
    if success:
        print("✅ All database schemas are correct and ready for use!")
    else:
        print("❌ Database schema issues found")
        sys.exit(1)
