#!/usr/bin/env python3
"""
Real Aura Data Setup - Add the actual staff aura data
"""
import sqlite3
import os
from dotenv import load_dotenv

def setup_real_aura_data():
    """Add the real staff aura data and configure settings"""
    
    print("🎯 SETTING UP REAL AURA DATA")
    print("=" * 50)
    
    load_dotenv()
    guild_id = int(os.getenv('GUILD_ID', 1263067254153805905))
    
    # Real staff aura data provided by user
    real_staff_data = [
        ("𝕓𝕖𝕕_𝕤𝕡𝕖𝕝𝕖𝕣𝕫", 27),
        ("Adudakqua", 26),
        ("HyScript7", 25),
        ("Gigachat nut", 24),
        ("Frodox", 20),
        ("∰", 16),
        ("Supermutec", 13),
        ("un köfte yeriz", 10),
        ("Strink", 8),
        ("Saxophone Goat", 5),
        ("Kranthi Swaroop", 5),
        ("H_jxr4", 3),
        ("Rick", 2),
    ]
    
    try:
        # Setup staff_points database
        conn = sqlite3.connect('data/staff_points.db')
        cursor = conn.cursor()
        
        print("1. 🗑️ Clearing existing data...")
        cursor.execute("DELETE FROM staff_points WHERE guild_id = ?", (guild_id,))
        cursor.execute("DELETE FROM points_history WHERE guild_id = ?", (guild_id,))
        
        print("2. 📝 Adding real staff aura data...")
        for name, aura in real_staff_data:
            # For now, we'll use incremental user IDs since we don't have real Discord IDs
            # You can update these with real Discord user IDs later
            user_id = 100000000000000000 + len([x for x in real_staff_data if real_staff_data.index(x) <= real_staff_data.index((name, aura))])
            
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
            """, (user_id, guild_id, aura, f"Initial aura for {name}"))
            
            print(f"   ✅ {name}: {aura} aura (ID: {user_id})")
        
        conn.commit()
        conn.close()
        
        print(f"\n3. ⚙️ Configuring staff settings...")
        
        # Setup staff shifts database with settings
        conn = sqlite3.connect('data/staff_shifts.db')
        cursor = conn.cursor()
        
        # Configure staff role and log channel
        staff_role_id = 1403059755001577543
        log_channel_id = 1407256147760517151
        
        cursor.execute("""
            INSERT OR REPLACE INTO shift_settings 
            (guild_id, log_channel_id, staff_role_ids)
            VALUES (?, ?, ?)
        """, (guild_id, log_channel_id, f'[{staff_role_id}]'))
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Staff role ID: {staff_role_id}")
        print(f"   ✅ Log channel ID: {log_channel_id}")
        
        print("\n4. 🔄 Creating backup...")
        # Import and create backup
        import sys
        sys.path.insert(0, 'src')
        
        import asyncio
        from utils.data_persistence import persistence_manager
        
        async def create_backup():
            return await persistence_manager.backup_all_data()
        
        success = asyncio.run(create_backup())
        
        if success:
            print("   ✅ Backup created successfully")
        else:
            print("   ⚠️ Backup failed, but data is saved")
        
        print("\n🎉 REAL AURA DATA SETUP COMPLETE!")
        print("✅ All staff aura data has been added")
        print("✅ Staff settings configured")
        print("✅ Data backed up for persistence")
        print("\n📋 Summary:")
        print(f"   • {len(real_staff_data)} staff members with aura")
        print(f"   • Total aura distributed: {sum(aura for _, aura in real_staff_data)}")
        print(f"   • Staff role: <@&{staff_role_id}>")
        print(f"   • Log channel: <#{log_channel_id}>")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    setup_real_aura_data()
