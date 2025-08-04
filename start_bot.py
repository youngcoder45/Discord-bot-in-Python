#!/usr/bin/env python3
"""
CodeVerse Bot Startup Script
"""

import os
import sys
import asyncio

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} - Compatible")

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'discord.py',
        'python-dotenv',
        'aiohttp',
        'aiosqlite'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'discord.py':
                import discord
            elif package == 'python-dotenv':
                import dotenv
            elif package == 'aiohttp':
                import aiohttp
            elif package == 'aiosqlite':
                import aiosqlite
            print(f"✅ {package} - Installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - Missing")
    
    if missing_packages:
        print(f"\nPlease install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        print("Or install all requirements:")
        print("pip install -r requirements.txt")
        sys.exit(1)

def check_environment():
    """Check environment configuration"""
    if not os.path.exists('.env'):
        print("⚠️  .env file not found!")
        print("Please copy .env.example to .env and configure it with your bot token.")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('DISCORD_TOKEN'):
        print("❌ DISCORD_TOKEN not set in .env file!")
        return False
    
    if not os.getenv('GUILD_ID'):
        print("⚠️  GUILD_ID not set - some features may not work properly")
    
    print("✅ Environment configuration looks good")
    return True

def main():
    """Main startup function"""
    print("🤖 Starting CodeVerse Bot...\n")
    
    # Check Python version
    check_python_version()
    
    # Check dependencies
    print("\nChecking dependencies...")
    check_dependencies()
    
    # Check environment
    print("\nChecking environment...")
    if not check_environment():
        print("\n❌ Environment check failed!")
        sys.exit(1)
    
    # Change to src directory and start bot
    print("\n🚀 Starting bot...")
    
    # Add src directory to Python path
    src_path = os.path.join(os.getcwd(), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    try:
        # Import and run the bot
        import subprocess
        result = subprocess.run([sys.executable, 'src/bot.py'], cwd=os.getcwd())
        if result.returncode != 0:
            print(f"❌ Bot exited with code {result.returncode}")
            sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting bot: {e}")
        print("Trying alternative startup method...")
        try:
            os.chdir('src')
            sys.path.insert(0, os.getcwd())
            import bot
        except Exception as e2:
            print(f"❌ Alternative method also failed: {e2}")
            sys.exit(1)

if __name__ == "__main__":
    main()
