#!/usr/bin/env python3
"""
Bot Diagnostics Script - Check all bot functionality
"""

import os
import sys
import json
import asyncio
import aiosqlite
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment_vars():
    """Check all required environment variables"""
    print("🔍 Checking Environment Variables...")
    
    required_vars = ['DISCORD_TOKEN', 'GUILD_ID']
    optional_vars = [
        'QUESTIONS_CHANNEL_ID', 'STAFF_UPDATES_CHANNEL_ID', 
        'LEADERBOARD_CHANNEL_ID', 'SUGGESTIONS_CHANNEL_ID',
        'MOD_TOOLS_CHANNEL_ID', 'BOT_COMMANDS_CHANNEL_ID'
    ]
    
    issues = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            issues.append(f"❌ {var} is not set")
            print(f"❌ {var} is not set")
        else:
            print(f"✅ {var} is set")
    
    for var in optional_vars:
        value = os.getenv(var)
        if not value or value == '0':
            print(f"⚠️  {var} is not set (optional)")
        else:
            print(f"✅ {var} is set")
    
    return issues

def check_data_files():
    """Check if all required data files exist"""
    print("\n📁 Checking Data Files...")
    
    required_files = [
        'src/data/questions.json',
        'src/data/challenges.json',
        'src/data/quotes.json'
    ]
    
    issues = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ {file_path} exists and is valid JSON ({len(data)} items)")
            except json.JSONDecodeError:
                issues.append(f"❌ {file_path} contains invalid JSON")
                print(f"❌ {file_path} contains invalid JSON")
            except Exception as e:
                issues.append(f"❌ Error reading {file_path}: {e}")
                print(f"❌ Error reading {file_path}: {e}")
        else:
            issues.append(f"❌ {file_path} does not exist")
            print(f"❌ {file_path} does not exist")
    
    return issues

async def check_database():
    """Check database connectivity and tables"""
    print("\n🗄️  Checking Database...")
    
    db_path = os.getenv('DATABASE_PATH', 'data/codeverse_bot.db')
    issues = []
    
    try:
        async with aiosqlite.connect(db_path) as db:
            # Check if tables exist
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = await cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            expected_tables = ['users', 'challenge_submissions', 'qotd_submissions']
            
            for table in expected_tables:
                if table in table_names:
                    print(f"✅ Table '{table}' exists")
                else:
                    issues.append(f"❌ Table '{table}' missing")
                    print(f"❌ Table '{table}' missing")
            
            # Check if we can perform basic operations
            await db.execute("SELECT COUNT(*) FROM users")
            print("✅ Database is accessible and functional")
            
    except Exception as e:
        issues.append(f"❌ Database error: {e}")
        print(f"❌ Database error: {e}")
    
    return issues

def check_bot_permissions():
    """Check if bot has required Discord permissions"""
    print("\n🔐 Bot Permissions Check...")
    print("⚠️  Manual check required - Ensure your bot has these permissions:")
    print("   • Read Messages")
    print("   • Send Messages")
    print("   • Embed Links")
    print("   • Add Reactions")
    print("   • Manage Messages")
    print("   • Use Slash Commands")
    print("   • Create Public Threads")
    print("   • Moderate Members (for moderation commands)")

def check_cog_files():
    """Check if all cog files exist and are valid Python"""
    print("\n🧩 Checking Cog Files...")
    
    cog_files = [
        'src/commands/moderation.py',
        'src/commands/community.py',
        'src/commands/leaderboard.py',
        'src/events/message_handler.py',
        'src/events/member_events.py',
        'src/tasks/daily_qotd.py',
        'src/tasks/weekly_challenge.py',
        'src/utils/database.py',
        'src/utils/helpers.py'
    ]
    
    issues = []
    
    for file_path in cog_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Basic syntax check
                compile(content, file_path, 'exec')
                print(f"✅ {file_path} exists and has valid syntax")
            except SyntaxError as e:
                issues.append(f"❌ {file_path} has syntax error: {e}")
                print(f"❌ {file_path} has syntax error: {e}")
            except Exception as e:
                issues.append(f"❌ Error checking {file_path}: {e}")
                print(f"❌ Error checking {file_path}: {e}")
        else:
            issues.append(f"❌ {file_path} does not exist")
            print(f"❌ {file_path} does not exist")
    
    return issues

async def main():
    """Run all diagnostic checks"""
    print("🤖 CodeVerse Bot Diagnostics\n")
    print("="*50)
    
    all_issues = []
    
    # Run all checks
    all_issues.extend(check_environment_vars())
    all_issues.extend(check_data_files())
    all_issues.extend(await check_database())
    check_bot_permissions()
    all_issues.extend(check_cog_files())
    
    # Summary
    print("\n" + "="*50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*50)
    
    if not all_issues:
        print("🎉 All checks passed! Your bot should be working correctly.")
        print("\nIf you're still experiencing issues, they might be:")
        print("• Discord permissions on your server")
        print("• Network connectivity issues")
        print("• Rate limiting from Discord")
        print("• Specific command errors (check bot logs)")
    else:
        print(f"❌ Found {len(all_issues)} issues:")
        for issue in all_issues:
            print(f"   {issue}")
        print("\n🔧 Fix these issues to resolve bot problems.")
    
    print("\n💡 Common solutions:")
    print("• Regenerate bot token if authentication fails")
    print("• Check channel IDs are correct for your server")
    print("• Ensure bot is invited with proper permissions")
    print("• Verify your server ID (GUILD_ID) is correct")

if __name__ == "__main__":
    asyncio.run(main())
