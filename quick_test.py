#!/usr/bin/env python3
"""
Quick Bot Test - Test specific bot functionality
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_bot_startup():
    """Test if bot can start without errors"""
    print("🧪 Testing bot startup process...")
    
    # Check if we can import all modules
    try:
        import sys
        sys.path.insert(0, 'src')
        import discord
        from utils.json_store import health_snapshot, add_or_update_user
        from utils.helpers import create_success_embed

        print("✅ All imports successful")

        # Test JSON store
        await add_or_update_user(123456789, "TestUser#0001")
        snap = await health_snapshot()
        print(f"✅ JSON store working (users tracked: {snap['users']})")

        # Test embed creation
        embed = create_success_embed("Test", "This is a test embed")
        print("✅ Embed creation successful")

        print("\n🎉 All basic functionality tests passed!")
        print("Your bot should work correctly when started.")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False
    
    return True

async def main():
    """Run quick tests"""
    print("🤖 Quick Bot Functionality Test\n")
    
    success = await test_bot_startup()
    
    if success:
        print("\n✅ Bot is ready to run!")
        print("\nTo start your bot:")
        print('1. Get a new bot token from Discord Developer Portal')
        print('2. Replace "YOUR_NEW_BOT_TOKEN_HERE" in .env file')
        print('3. Run: python start_bot.py')
    else:
        print("\n❌ Issues found - check the errors above")

if __name__ == "__main__":
    asyncio.run(main())
