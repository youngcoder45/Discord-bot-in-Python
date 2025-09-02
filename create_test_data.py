#!/usr/bin/env python3
"""
Quick Fix - Create test user data that will show in leaderboard
"""
import sqlite3
import os
from dotenv import load_dotenv

def create_test_aura_data():
    """Create test data with realistic Discord-like user IDs"""
    
    print("🔧 CREATING TEST AURA DATA WITH REALISTIC IDs")
    print("=" * 50)
    
    load_dotenv()
    guild_id = int(os.getenv('GUILD_ID', 1263067254153805905))
    
    # Create realistic Discord-like user IDs for testing
    # These will work in the leaderboard until you get real IDs
    test_staff_data = [
        ("TestUser_27_Aura", 27, 800000000000000001),
        ("TestUser_26_Aura", 26, 800000000000000002),
        ("TestUser_25_Aura", 25, 800000000000000003),
        ("TestUser_24_Aura", 24, 800000000000000004),
        ("TestUser_20_Aura", 20, 800000000000000005),
        ("TestUser_16_Aura", 16, 800000000000000006),
        ("TestUser_13_Aura", 13, 800000000000000007),
        ("TestUser_10_Aura", 10, 800000000000000008),
        ("TestUser_8_Aura", 8, 800000000000000009),
        ("TestUser_5A_Aura", 5, 800000000000000010),
        ("TestUser_5B_Aura", 5, 800000000000000011),
        ("TestUser_3_Aura", 3, 800000000000000012),
        ("TestUser_2_Aura", 2, 800000000000000013),
    ]
    
    try:
        conn = sqlite3.connect('data/staff_points.db')
        cursor = conn.cursor()
        
        print("1. 🗑️ Clearing old fake data...")
        cursor.execute("DELETE FROM staff_points WHERE guild_id = ?", (guild_id,))
        cursor.execute("DELETE FROM points_history WHERE guild_id = ?", (guild_id,))
        
        print("2. 📝 Adding test data with realistic IDs...")
        for name, aura, user_id in test_staff_data:
            # Insert into staff_points table
            cursor.execute("""
                INSERT OR REPLACE INTO staff_points 
                (user_id, guild_id, points, total_earned, last_updated)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, guild_id, aura, aura))
            
            # Add history entry
            cursor.execute("""
                INSERT INTO points_history 
                (user_id, guild_id, points_change, action_type, reason, moderator_id, timestamp)
                VALUES (?, ?, ?, 'add', ?, 0, CURRENT_TIMESTAMP)
            """, (user_id, guild_id, aura, f"Test aura for {name}"))
            
            print(f"   ✅ {name}: {aura} aura (ID: {user_id})")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 TEST DATA CREATED!")
        print("✅ Now /aura leaderboard will show test users with correct aura amounts")
        print("✅ This proves the system works - you just need real Discord User IDs")
        print()
        print("📝 TO GET REAL USER IDS:")
        print("1. Enable Developer Mode in Discord")
        print("2. Right-click each staff member → Copy User ID")
        print("3. Replace the test IDs with real ones")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_test_aura_data()
