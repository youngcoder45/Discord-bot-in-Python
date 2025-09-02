#!/usr/bin/env python3
import sqlite3

def check_aura_data():
    """Check current aura data in the database"""
    try:
        conn = sqlite3.connect('data/staff_points.db')
        
        print("🔍 Current aura data:")
        guild_id = 1263067254153805905  # Your server ID
        rows = list(conn.execute('SELECT user_id, points, total_earned FROM staff_points WHERE guild_id = ?', (guild_id,)))
        
        if rows:
            print(f"📊 Found {len(rows)} records:")
            for row in rows:
                print(f"  👤 User {row[0]}: {row[1]} aura (earned {row[2]} total)")
        else:
            print("❌ No aura data found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking aura data: {e}")

if __name__ == "__main__":
    check_aura_data()
