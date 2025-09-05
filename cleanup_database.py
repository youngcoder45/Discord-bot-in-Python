#!/usr/bin/env python3
"""
Database Cleanup Script - Remove old duplicate tables
"""
import sqlite3
import os

def cleanup_old_tables():
    """Remove old duplicate tables that are no longer needed"""
    print("🧹 CLEANING UP OLD DATABASE TABLES")
    print("=" * 40)
    
    db_path = "data/staff_points.db"
    
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Current tables: {all_tables}")
        
        # Tables to remove (old duplicates)
        tables_to_remove = ['staff_aura', 'aura_history', 'points', 'point_logs']
        
        for table in tables_to_remove:
            if table in all_tables:
                print(f"🗑️ Removing old table: {table}")
                cursor.execute(f"DROP TABLE {table}")
            else:
                print(f"ℹ️ Table {table} not found (already removed)")
        
        conn.commit()
        
        # Check final tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        final_tables = [row[0] for row in cursor.fetchall()]
        print(f"\n✅ Final tables: {final_tables}")
        
        conn.close()
        
        print("\n🎉 Database cleanup completed!")
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

if __name__ == "__main__":
    cleanup_old_tables()
