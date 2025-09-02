#!/usr/bin/env python3
import sqlite3

def debug_database():
    """Debug the staff_points database"""
    try:
        conn = sqlite3.connect('data/staff_points.db')
        cursor = conn.cursor()
        
        print("🔍 Database Debug Information:")
        print("=" * 50)
        
        # Check tables
        print("\n📋 Tables in database:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check staff_aura table structure
        print("\n🏗️ staff_aura table structure:")
        cursor.execute("PRAGMA table_info(staff_aura);")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Check all data in staff_aura
        print("\n📊 All data in staff_aura table:")
        cursor.execute("SELECT * FROM staff_aura;")
        rows = cursor.fetchall()
        if rows:
            print(f"Found {len(rows)} records:")
            for row in rows:
                print(f"  {row}")
        else:
            print("❌ No data found")
        
        # Check row count
        cursor.execute("SELECT COUNT(*) FROM staff_aura;")
        count = cursor.fetchone()[0]
        print(f"\n🔢 Total rows: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_database()
