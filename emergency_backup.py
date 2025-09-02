#!/usr/bin/env python3
"""
Emergency Data Backup - Create immediate backup of all current data
"""

import sys
import os
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def emergency_backup():
    """Create immediate backup of all bot data"""
    print("🚨 EMERGENCY DATA BACKUP STARTING...")
    
    try:
        from utils.data_persistence import persistence_manager
        
        # Check existing data first
        existing_data = await persistence_manager.check_existing_data()
        
        if existing_data["has_data"]:
            print(f"📊 Found existing data: {existing_data['databases']}")
            
            # Create backup
            success = await persistence_manager.backup_all_data()
            
            if success:
                print("✅ EMERGENCY BACKUP COMPLETED SUCCESSFULLY!")
                print("\n📁 Your data is now safely backed up and will be restored automatically")
                print("   when the bot starts up after any code changes.")
                
                # List backup files
                backup_dir = Path("backup")
                if backup_dir.exists():
                    backup_files = list(backup_dir.glob("bot_data_backup_*.json"))
                    print(f"\n💾 Local backups available: {len(backup_files)}")
                    if backup_files:
                        latest = sorted(backup_files)[-1]
                        print(f"   Latest: {latest.name}")
                
                return True
            else:
                print("❌ EMERGENCY BACKUP FAILED!")
                return False
        else:
            print("ℹ️ No existing data found to backup")
            return True
            
    except Exception as e:
        print(f"❌ Emergency backup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚨 Starting emergency data backup...")
    success = asyncio.run(emergency_backup())
    
    if success:
        print("\n🎉 YOUR DATA IS SAFE!")
        print("✅ You can now commit and push code changes without losing any data")
        print("✅ The bot will automatically restore your data on startup")
    else:
        print("\n❌ BACKUP FAILED - DO NOT COMMIT YET!")
        print("   Check the error messages above and try again")
    
    exit(0 if success else 1)
