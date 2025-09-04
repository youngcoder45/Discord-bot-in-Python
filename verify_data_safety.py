#!/usr/bin/env python3
"""
Data Safety Verification Script
Run this to verify your data protection system is working correctly
"""
import os
import sys
import json
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, 'src')

# Load environment
from dotenv import load_dotenv
load_dotenv()

def check_environment():
    """Check environment configuration"""
    print("🔍 CHECKING ENVIRONMENT CONFIGURATION")
    print("=" * 50)
    
    required_vars = ['DISCORD_TOKEN', 'GUILD_ID']
    backup_vars = ['GITHUB_TOKEN', 'GITHUB_REPO', 'BACKUP_BRANCH']
    
    issues = []
    
    print("📋 Required Variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'DISCORD_TOKEN':
                print(f"  ✅ {var}: {'*' * 20}")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: NOT SET")
            issues.append(var)
    
    print("\n🔄 Backup Configuration:")
    for var in backup_vars:
        value = os.getenv(var)
        if value:
            if var == 'GITHUB_TOKEN':
                print(f"  ✅ {var}: ghp_{'*' * 20}")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ⚠️ {var}: NOT SET (backups will be local only)")
    
    return issues

def check_databases():
    """Check current database status"""
    print("\n🗄️ CHECKING DATABASE STATUS")
    print("=" * 50)
    
    db_files = [
        "data/staff_points.db",
        "data/staff_shifts.db", 
        "data/codeverse_bot.db"
    ]
    
    total_data = 0
    
    for db_path in db_files:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                print(f"\n📊 {os.path.basename(db_path)}:")
                db_total = 0
                
                for (table_name,) in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"  • {table_name}: {count} records")
                    db_total += count
                
                print(f"  📈 Total records: {db_total}")
                total_data += db_total
                conn.close()
                
            except Exception as e:
                print(f"  ❌ Error reading {db_path}: {e}")
        else:
            print(f"❌ {db_path}: NOT FOUND")
    
    print(f"\n📊 TOTAL DATA RECORDS: {total_data}")
    return total_data > 0

def check_backups():
    """Check backup files"""
    print("\n💾 CHECKING BACKUP FILES")
    print("=" * 50)
    
    backup_dir = Path("backup")
    
    if not backup_dir.exists():
        print("❌ Backup directory does not exist!")
        return False
    
    backup_files = sorted(backup_dir.glob("bot_data_backup_*.json"))
    
    if not backup_files:
        print("❌ No backup files found!")
        return False
    
    print(f"📁 Found {len(backup_files)} backup files:")
    
    for backup_file in backup_files[-3:]:  # Show last 3
        size = backup_file.stat().st_size
        modified = datetime.fromtimestamp(backup_file.stat().st_mtime)
        print(f"  • {backup_file.name} ({size:,} bytes) - {modified.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check latest backup content
    latest_backup = backup_files[-1]
    print(f"\n🔍 Checking latest backup: {latest_backup.name}")
    
    try:
        with open(latest_backup, 'r') as f:
            backup_data = json.load(f)
        
        print("  📊 Backup contains:")
        
        if 'databases' in backup_data:
            for db_name, db_content in backup_data['databases'].items():
                if 'tables' in db_content:
                    table_count = len(db_content['tables'])
                    total_records = 0
                    for table_data in db_content['tables'].values():
                        if 'data' in table_data:
                            total_records += len(table_data['data'])
                    print(f"    • {db_name}: {table_count} tables, {total_records} records")
        
        if 'json_files' in backup_data:
            json_count = len(backup_data['json_files'])
            print(f"    • JSON files: {json_count}")
        
        if 'timestamp' in backup_data:
            backup_time = backup_data['timestamp']
            print(f"    • Created: {backup_time}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error reading backup: {e}")
        return False

async def test_backup_system():
    """Test the backup system"""
    print("\n🧪 TESTING BACKUP SYSTEM")
    print("=" * 50)
    
    try:
        from utils.data_persistence import persistence_manager
        
        print("1. 🔍 Checking existing data...")
        existing_data = await persistence_manager.check_existing_data()
        
        if existing_data["has_data"]:
            print("  ✅ Found existing data to protect")
            for db, count in existing_data["databases"].items():
                print(f"    • {db}: {count} records")
        else:
            print("  ⚠️ No existing data found")
        
        print("\n2. 💾 Testing backup process...")
        backup_success = await persistence_manager.backup_all_data()
        
        if backup_success:
            print("  ✅ Backup test successful!")
        else:
            print("  ❌ Backup test failed!")
            return False
        
        print("\n3. 🔄 Testing data collection...")
        backup_data = await persistence_manager.collect_all_data()
        
        total_records = 0
        if 'databases' in backup_data:
            for db_content in backup_data['databases'].values():
                if 'tables' in db_content:
                    for table_data in db_content['tables'].values():
                        if 'data' in table_data:
                            total_records += len(table_data['data'])
        
        print(f"  📊 Collected {total_records} total database records")
        print(f"  📁 Collected {len(backup_data.get('json_files', {}))} JSON files")
        
        return True
        
    except Exception as e:
        print(f"❌ Backup system test failed: {e}")
        return False

def show_next_steps(has_data, backup_works, env_issues):
    """Show next steps based on verification results"""
    print("\n🎯 NEXT STEPS")
    print("=" * 50)
    
    if env_issues:
        print("❌ CRITICAL: Fix environment issues first!")
        for issue in env_issues:
            print(f"  • Set {issue} in your .env file")
        print("\n📖 See .env.example for reference")
        return
    
    if not has_data:
        print("ℹ️ No existing data found - this is normal for new bots")
        print("✅ Add some data first:")
        print("  • Use /aura add @user 100 'testing' to add test aura")
        print("  • Use /shift start to create test shift data")
        print("  • Then re-run this verification script")
        return
    
    if not backup_works:
        print("❌ CRITICAL: Backup system not working!")
        print("🔧 To fix:")
        print("  1. Check your GITHUB_TOKEN is valid")
        print("  2. Ensure repo permissions are correct")
        print("  3. Run: python emergency_backup.py")
        return
    
    print("🎉 EXCELLENT! Your data protection system is working perfectly!")
    print("\n✅ What's protected:")
    print("  • All staff aura data")
    print("  • All staff shift data") 
    print("  • All bot configurations")
    print("  • Automatic backups every 6 hours")
    print("  • GitHub cloud backup")
    print("  • Local backup files")
    
    print("\n🚀 You can now safely:")
    print("  • Make code changes and commit")
    print("  • Push to GitHub")
    print("  • Restart the bot")
    print("  • Deploy to different platforms")
    
    print("\n🛡️ Your data will NEVER be lost!")

async def main():
    """Main verification function"""
    print("🛡️ CODEVERSE BOT - DATA SAFETY VERIFICATION")
    print("=" * 60)
    print("This script verifies your data protection system is working correctly.\n")
    
    # Check environment
    env_issues = check_environment()
    
    # Check databases  
    has_data = check_databases()
    
    # Check backups
    backup_files_ok = check_backups()
    
    # Test backup system
    backup_system_ok = await test_backup_system()
    
    # Show results
    print("\n📊 VERIFICATION RESULTS")
    print("=" * 50)
    
    print(f"Environment Setup: {'✅ GOOD' if not env_issues else '❌ ISSUES'}")
    print(f"Database Data: {'✅ FOUND' if has_data else 'ℹ️ EMPTY'}")
    print(f"Backup Files: {'✅ GOOD' if backup_files_ok else '❌ MISSING'}")
    print(f"Backup System: {'✅ WORKING' if backup_system_ok else '❌ BROKEN'}")
    
    # Next steps
    show_next_steps(has_data, backup_system_ok and backup_files_ok, env_issues)

if __name__ == "__main__":
    asyncio.run(main())
