#!/usr/bin/env python3
"""
Test script to verify bot functionality
"""

import asyncio
import aiosqlite
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_database():
    """Test database functionality"""
    print("🧪 Testing database functionality...")
    
    # Test database connection
    db_path = os.path.join('data', 'codeverse_bot.db')
    
    try:
        async with aiosqlite.connect(db_path) as db:
            # Check if tables exist
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = await cursor.fetchall()
            
            print(f"✅ Database connected successfully")
            print(f"📊 Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table[0]}")
                
            # Test a simple query
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            count = await cursor.fetchone()
            print(f"👥 Current user records: {count[0]}")
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")

def test_data_files():
    """Test data file loading"""
    print("\n📁 Testing data files...")
    
    data_files = [
        'src/data/questions.json',
        'src/data/challenges.json', 
        'src/data/quotes.json'
    ]
    
    for file_path in data_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import json
                data = json.load(f)
                print(f"✅ {file_path}: {len(data)} items loaded")
        except Exception as e:
            print(f"❌ {file_path}: Failed to load - {e}")

def test_environment():
    """Test environment variables"""
    print("\n🔧 Testing environment configuration...")
    
    required_vars = [
        'DISCORD_TOKEN',
        'GUILD_ID',
        'GENERAL_CHANNEL_ID',
        'QOTD_CHANNEL_ID',
        'CHALLENGE_CHANNEL_ID',
        'SUGGESTIONS_CHANNEL_ID',
        'MOD_TOOLS_CHANNEL_ID',
        'ANNOUNCEMENTS_CHANNEL_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Hide sensitive info
            display_value = value[:8] + "..." if var == 'DISCORD_TOKEN' else value
            print(f"✅ {var}: {display_value}")
        else:
            missing_vars.append(var)
            print(f"❌ {var}: Not set")
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
    else:
        print(f"\n✅ All environment variables are configured")

async def main():
    """Run all tests"""
    print("🚀 CodeVerse Bot - Functionality Test\n")
    
    test_environment()
    test_data_files()
    await test_database()
    
    print("\n✨ Test completed!")

if __name__ == "__main__":
    asyncio.run(main())
