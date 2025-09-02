#!/usr/bin/env python3
"""
Data Recovery - Check backup files for lost aura data
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def check_backup_for_aura_data():
    """Check all backup files for aura data"""
    print("🔍 SEARCHING FOR LOST AURA DATA...")
    print("=" * 50)
    
    backup_dir = Path("backup")
    if not backup_dir.exists():
        print("❌ No backup directory found!")
        return False
    
    backup_files = sorted(backup_dir.glob("bot_data_backup_*.json"))
    
    if not backup_files:
        print("❌ No backup files found!")
        return False
    
    found_aura_data = False
    
    for backup_file in backup_files:
        print(f"\n📁 Checking: {backup_file.name}")
        
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Check staff_points.db for aura data
            staff_points_db = backup_data.get("databases", {}).get("staff_points.db", {})
            
            if staff_points_db:
                tables = staff_points_db.get("tables", {})
                
                # Check points table
                points_table = tables.get("points", {})
                points_data = points_table.get("data", [])
                
                if points_data:
                    print(f"   ✅ FOUND AURA DATA! {len(points_data)} records")
                    for record in points_data:
                        user_id = record.get("user_id", "Unknown")
                        points = record.get("points", 0)
                        guild_id = record.get("guild_id", "Unknown")
                        print(f"      User {user_id}: {points} aura (Guild: {guild_id})")
                    found_aura_data = True
                else:
                    print("   ⚠️ No aura data in this backup")
                
                # Check logs table
                logs_table = tables.get("point_logs", {})
                logs_data = logs_table.get("data", [])
                
                if logs_data:
                    print(f"   📋 Found {len(logs_data)} aura transaction logs")
                    for log in logs_data[:3]:  # Show first 3
                        amount = log.get("amount", 0)
                        reason = log.get("reason", "No reason")
                        timestamp = log.get("timestamp", "Unknown")
                        print(f"      {timestamp}: {amount:+} aura - {reason}")
            else:
                print("   ❌ No staff_points database in this backup")
                
        except Exception as e:
            print(f"   ❌ Error reading backup: {e}")
    
    return found_aura_data

def restore_from_specific_backup(backup_file):
    """Restore from a specific backup file"""
    print(f"\n🔄 RESTORING FROM: {backup_file}")
    
    try:
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        # Get aura data
        staff_points_db = backup_data.get("databases", {}).get("staff_points.db", {})
        
        if not staff_points_db:
            print("❌ No staff points data in this backup!")
            return False
        
        # Restore the database manually
        import sqlite3
        
        db_path = "data/staff_points.db"
        print(f"📝 Restoring to: {db_path}")
        
        # Backup current database
        if os.path.exists(db_path):
            backup_current = f"{db_path}.backup_{int(asyncio.get_event_loop().time())}"
            import shutil
            shutil.copy2(db_path, backup_current)
            print(f"💾 Current database backed up to: {backup_current}")
        
        # Connect and restore
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM points")
        cursor.execute("DELETE FROM point_logs")
        
        # Restore points
        points_data = staff_points_db.get("tables", {}).get("points", {}).get("data", [])
        
        if points_data:
            for record in points_data:
                cursor.execute("""
                    INSERT INTO points (user_id, guild_id, points, last_updated) 
                    VALUES (?, ?, ?, ?)
                """, (
                    record.get("user_id"),
                    record.get("guild_id"), 
                    record.get("points"),
                    record.get("last_updated")
                ))
            print(f"✅ Restored {len(points_data)} aura records")
        
        # Restore logs
        logs_data = staff_points_db.get("tables", {}).get("point_logs", {}).get("data", [])
        
        if logs_data:
            for record in logs_data:
                cursor.execute("""
                    INSERT INTO point_logs (user_id, guild_id, amount, reason, admin_id, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    record.get("user_id"),
                    record.get("guild_id"),
                    record.get("amount"), 
                    record.get("reason"),
                    record.get("admin_id"),
                    record.get("timestamp")
                ))
            print(f"✅ Restored {len(logs_data)} aura transaction logs")
        
        conn.commit()
        conn.close()
        
        print("🎉 AURA DATA RESTORATION COMPLETE!")
        return True
        
    except Exception as e:
        print(f"❌ Restoration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚨 EMERGENCY AURA DATA RECOVERY")
    print("=" * 50)
    
    # First, check all backups for aura data
    found_data = check_backup_for_aura_data()
    
    if found_data:
        print("\n" + "=" * 50)
        print("🎯 RECOVERY OPTIONS:")
        
        backup_dir = Path("backup")
        backup_files = sorted(backup_dir.glob("bot_data_backup_*.json"), reverse=True)
        
        for i, backup_file in enumerate(backup_files[:5]):  # Show last 5 backups
            print(f"{i+1}. {backup_file.name}")
        
        print("\nSelect a backup to restore from (enter number):")
        print("Or press Enter to restore from the latest backup")
        
        try:
            choice = input("Choice: ").strip()
            
            if choice == "":
                # Use latest backup
                selected_backup = backup_files[0]
            else:
                idx = int(choice) - 1
                if 0 <= idx < len(backup_files):
                    selected_backup = backup_files[idx]
                else:
                    print("❌ Invalid choice!")
                    exit(1)
            
            print(f"\n🔄 Restoring from: {selected_backup.name}")
            success = restore_from_specific_backup(selected_backup)
            
            if success:
                print("\n🎉 SUCCESS! Your aura data has been restored!")
                print("✅ Run your bot now and check /aura leaderboard")
                print("✅ All staff aura should be back!")
            else:
                print("\n❌ Restoration failed!")
                
        except KeyboardInterrupt:
            print("\n❌ Recovery cancelled by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    else:
        print("\n❌ NO AURA DATA FOUND IN ANY BACKUP!")
        print("   This means the aura data was never properly saved.")
        print("   You'll need to re-add the aura manually.")
