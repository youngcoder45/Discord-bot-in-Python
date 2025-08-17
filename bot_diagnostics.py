#!/usr/bin/env python3
"""
Bot Diagnostics Script - Check all bot functionality
"""

import os
import sys
import json
import asyncio
from dotenv import load_dotenv

# Add src to path so we can import utils
sys.path.insert(0, 'src')

try:
    from utils.json_store import health_snapshot
except Exception:
    health_snapshot = None

# Load environment variables
load_dotenv()

def check_environment_vars():
    """Check required + optional environment variables."""
    print("🔍 Checking Environment Variables...")

    required_vars = ['DISCORD_TOKEN', 'GUILD_ID']
    optional_vars = [
        'JOINS_LEAVES_CHANNEL_ID', 'SERVER_LOGS_CHANNEL_ID',
        'HOSTING_PLATFORM', 'PORT'
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
    """Check required JSON resource files exist + are valid."""
    print("\n📁 Checking Data Files...")

    required_files = [
        'src/data/questions.json',
        'src/data/challenges.json',
        'src/data/quotes.json'
    ]

    issues = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            issues.append(f"❌ {file_path} does not exist")
            print(f"❌ {file_path} does not exist")
            continue
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            size = len(data) if isinstance(data, (list, dict)) else 'n/a'
            print(f"✅ {file_path} valid JSON (items: {size})")
        except json.JSONDecodeError:
            issues.append(f"❌ {file_path} invalid JSON")
            print(f"❌ {file_path} invalid JSON")
        except Exception as e:
            issues.append(f"❌ Error reading {file_path}: {e}")
            print(f"❌ Error reading {file_path}: {e}")
    return issues

async def check_json_store():
    """Check JSON persistence layer (health snapshot)."""
    print("\n🗄️  Checking JSON Store...")
    issues = []
    if not health_snapshot:
        issues.append("❌ json_store not importable")
        print("❌ json_store not importable")
        return issues
    try:
        snap = await health_snapshot()
        users = snap.get('users', 'n/a')
        updated = snap.get('last_update')
        print(f"✅ JSON store accessible (users tracked: {users}, last_update: {updated})")
    except Exception as e:
        issues.append(f"❌ JSON store error: {e}")
        print(f"❌ JSON store error: {e}")
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
    """Check stable cog files exist & have valid syntax."""
    print("\n🧩 Checking Cog Files...")
    cog_files = [
        'src/commands/core.py',
        'src/commands/diagnostics.py',
        'src/commands/community.py',
        'src/commands/fun.py',
        'src/events/member_events.py',
        'src/events/message_handler.py',
        'src/tasks/staff_reminder.py',
        'src/utils/helpers.py',
        'src/utils/json_store.py'
    ]
    issues = []
    for file_path in cog_files:
        if not os.path.exists(file_path):
            issues.append(f"❌ {file_path} missing")
            print(f"❌ {file_path} missing")
            continue
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            compile(content, file_path, 'exec')
            print(f"✅ {file_path} syntax OK")
        except SyntaxError as e:
            issues.append(f"❌ {file_path} syntax error: {e}")
            print(f"❌ {file_path} syntax error: {e}")
        except Exception as e:
            issues.append(f"❌ {file_path} error: {e}")
            print(f"❌ {file_path} error: {e}")
    return issues

async def main():
    """Run all diagnostic checks"""
    print("🤖 CodeVerse Bot Diagnostics\n")
    print("="*50)
    
    all_issues = []
    
    # Run all checks
    all_issues.extend(check_environment_vars())
    all_issues.extend(check_data_files())
    all_issues.extend(await check_json_store())
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
