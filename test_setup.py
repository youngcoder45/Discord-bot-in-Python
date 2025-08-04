#!/usr/bin/env python3
"""
Simple test script to verify bot setup
"""

import os
import sys
import asyncio

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    
    try:
        from utils.database import db, init_database
        print("✅ Database module imported successfully")
        
        from utils.helpers import create_success_embed, get_random_quote
        print("✅ Helpers module imported successfully")
        
        from commands.moderation import Moderation
        print("✅ Moderation commands imported successfully")
        
        from commands.community import CommunityCommands
        print("✅ Community commands imported successfully")
        
        from commands.leaderboard import Leaderboard
        print("✅ Leaderboard commands imported successfully")
        
        from events.message_handler import MessageHandler
        print("✅ Message handler imported successfully")
        
        from events.member_events import MemberEvents
        print("✅ Member events imported successfully")
        
        from tasks.daily_qotd import post_daily_qotd
        print("✅ Daily QOTD task imported successfully")
        
        from tasks.weekly_challenge import announce_weekly_challenge
        print("✅ Weekly challenge task imported successfully")
        
        # Test database initialization
        await init_database()
        print("✅ Database initialized successfully")
        
        print("\n🎉 All imports successful! Bot should be ready to run.")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

async def test_data_files():
    """Test if data files exist and are valid"""
    print("\nTesting data files...")
    
    import json
    
    files = [
        'src/data/questions.json',
        'src/data/challenges.json', 
        'src/data/quotes.json'
    ]
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ {file_path}: {len(data)} items loaded")
        except FileNotFoundError:
            print(f"❌ {file_path}: File not found")
        except json.JSONDecodeError:
            print(f"❌ {file_path}: Invalid JSON")
        except Exception as e:
            print(f"❌ {file_path}: Error - {e}")

def test_environment():
    """Test environment configuration"""
    print("\nTesting environment...")
    
    env_file = '.env'
    if os.path.exists(env_file):
        print("✅ .env file exists")
        
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = ['DISCORD_TOKEN', 'GUILD_ID']
        for var in required_vars:
            if os.getenv(var):
                print(f"✅ {var} is set")
            else:
                print(f"⚠️  {var} is not set (required)")
    else:
        print("⚠️  .env file not found. Copy .env.example to .env and configure it.")

async def main():
    """Run all tests"""
    print("🤖 CodeVerse Bot Setup Test\n")
    
    test_environment()
    await test_data_files()
    await test_imports()
    
    print("\n" + "="*50)
    print("Test completed! Check for any ❌ or ⚠️  messages above.")
    print("If all tests pass, you can run the bot with: python src/bot.py")

if __name__ == "__main__":
    asyncio.run(main())
