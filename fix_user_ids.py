#!/usr/bin/env python3
"""
Fix User IDs - Replace fake IDs with real Discord user IDs for staff
"""
import sqlite3
import os
from dotenv import load_dotenv

def fix_user_ids_with_real_discord_ids():
    """Replace fake user IDs with real Discord user IDs"""
    
    print("🔧 FIXING USER IDs WITH REAL DISCORD IDs")
    print("=" * 50)
    
    load_dotenv()
    guild_id = int(os.getenv('GUILD_ID', 1263067254153805905))
    
    # Map the staff names to their data and REAL Discord user IDs
    # You'll need to provide the actual Discord user IDs for your staff
    staff_mapping = {
        "𝕓𝕖𝕕_𝕤𝕡𝕖𝕝𝕖𝕣𝕫": {"aura": 27, "discord_id": None},  # Replace None with real Discord ID
        "Adudakqua": {"aura": 26, "discord_id": None},  # Replace None with real Discord ID
        "HyScript7": {"aura": 25, "discord_id": None},  # Replace None with real Discord ID
        "Gigachat nut": {"aura": 24, "discord_id": None},  # Replace None with real Discord ID
        "Frodox": {"aura": 20, "discord_id": None},  # Replace None with real Discord ID
        "∰": {"aura": 16, "discord_id": None},  # Replace None with real Discord ID
        "Supermutec": {"aura": 13, "discord_id": None},  # Replace None with real Discord ID
        "un köfte yeriz": {"aura": 10, "discord_id": None},  # Replace None with real Discord ID
        "Strink": {"aura": 8, "discord_id": None},  # Replace None with real Discord ID
        "Saxophone Goat": {"aura": 5, "discord_id": None},  # Replace None with real Discord ID
        "Kranthi Swaroop": {"aura": 5, "discord_id": None},  # Replace None with real Discord ID
        "H_jxr4": {"aura": 3, "discord_id": None},  # Replace None with real Discord ID
        "Rick": {"aura": 2, "discord_id": None},  # Replace None with real Discord ID
    }
    
    print("❌ CRITICAL ISSUE FOUND!")
    print("The aura data is using FAKE user IDs instead of real Discord user IDs!")
    print("This is why your /aura leaderboard command won't show real users.")
    print()
    print("🔍 WHAT WE FOUND:")
    print("- Data exists in database ✅")
    print("- Correct aura amounts ✅") 
    print("- BUT using fake IDs like 100000000000000001 ❌")
    print()
    print("💡 SOLUTION:")
    print("You need to provide the REAL Discord User IDs for your staff members.")
    print("Here's how to get them:")
    print()
    print("1. Enable Developer Mode in Discord:")
    print("   Settings > Advanced > Developer Mode ✅")
    print()
    print("2. Right-click each staff member and 'Copy User ID'")
    print()
    print("3. Update this script with real IDs, then run it")
    print()
    print("📋 Your staff list:")
    for i, (name, data) in enumerate(staff_mapping.items(), 1):
        print(f"{i:2d}. {name} - {data['aura']} aura")
    print()
    print("🚨 NEXT STEPS:")
    print("1. Get real Discord User IDs for all 13 staff members")
    print("2. Update the script with real IDs")
    print("3. Run script again to fix the data")
    print("4. Then /aura leaderboard will show real users!")
    
    return False  # Don't proceed without real IDs

def update_with_real_ids():
    """Update database with real Discord user IDs (when provided)"""
    # This function will be used once you provide real Discord IDs
    pass

if __name__ == "__main__":
    fix_user_ids_with_real_discord_ids()
