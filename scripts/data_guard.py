#!/usr/bin/env python3
"""
Data Guard - Prevents data loss during git operations
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

async def pre_commit_backup():
    """Create backup before committing"""
    print("🛡️ PRE-COMMIT DATA GUARD ACTIVATED...")
    
    try:
        from utils.data_persistence import persistence_manager
        
        # Check if we have data to protect
        existing_data = await persistence_manager.check_existing_data()
        
        if existing_data["has_data"]:
            print(f"📊 Protecting data: {existing_data['databases']}")
            
            # Create backup
            success = await persistence_manager.backup_all_data()
            
            if success:
                print("✅ DATA PROTECTION SUCCESSFUL - Safe to commit!")
                return True
            else:
                print("❌ DATA PROTECTION FAILED - Aborting commit!")
                return False
        else:
            print("ℹ️ No data to protect - Safe to commit")
            return True
            
    except Exception as e:
        print(f"❌ Data guard failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(pre_commit_backup())
    
    if not success:
        print("\n🚨 COMMIT BLOCKED TO PROTECT YOUR DATA!")
        print("   Fix the backup system before committing")
        exit(1)
    
    print("\n🔒 Your data is protected - proceeding with commit...")
    exit(0)
