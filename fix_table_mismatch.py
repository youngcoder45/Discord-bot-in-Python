#!/usr/bin/env python3
import sqlite3
import os
from dotenv import load_dotenv

def fix_aura_table_mismatch():
    """Fix the table mismatch between points and staff_points tables"""
    
    print("🔧 FIXING AURA TABLE MISMATCH")
    print("=" * 50)
    
    load_dotenv()
    guild_id = int(os.getenv('GUILD_ID', 1263067254153805905))
    
    try:
        conn = sqlite3.connect('data/staff_points.db')
        cursor = conn.cursor()
        
        # 1. Check data in points table
        print("1. 📊 Checking points table data...")
        cursor.execute("SELECT user_id, points FROM points ORDER BY points DESC")
        points_data = cursor.fetchall()
        print(f"   Found {len(points_data)} records in points table")
        
        # 2. Check data in staff_points table
        print("2. 📊 Checking staff_points table data...")
        cursor.execute("SELECT user_id, points FROM staff_points WHERE guild_id = ? ORDER BY points DESC", (guild_id,))
        staff_points_data = cursor.fetchall()
        print(f"   Found {len(staff_points_data)} records in staff_points table")
        
        # 3. Copy data from points to staff_points if needed
        if points_data and not staff_points_data:
            print("3. 🔄 Copying data from points to staff_points table...")
            
            for user_id, points in points_data:
                # Insert into staff_points with guild_id
                cursor.execute("""
                    INSERT OR REPLACE INTO staff_points 
                    (user_id, guild_id, points, total_earned, last_updated)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, guild_id, points, points))
                
                print(f"   ✅ Copied User {user_id}: {points} points")
            
            conn.commit()
            print(f"   🎉 Successfully copied {len(points_data)} records!")
        
        elif staff_points_data:
            print("3. ✅ staff_points table already has data")
        
        else:
            print("3. ❌ No data found in either table")
        
        # 4. Verify final state
        print("\n4. ✅ Final verification:")
        cursor.execute("SELECT user_id, points FROM staff_points WHERE guild_id = ? ORDER BY points DESC", (guild_id,))
        final_data = cursor.fetchall()
        
        if final_data:
            print(f"   📋 staff_points table now has {len(final_data)} records:")
            for user_id, points in final_data:
                print(f"     👤 User {user_id}: {points} aura")
        else:
            print("   ❌ staff_points table is still empty")
        
        conn.close()
        
        print("\n🎉 TABLE MISMATCH FIXED!")
        print("✅ /aura leaderboard should now work properly")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_aura_table_mismatch()
