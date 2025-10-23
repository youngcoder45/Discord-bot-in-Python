#!/usr/bin/env python3
"""
Main entry point for CodeVerse Discord Bot
Optimized for bot-hosting.net deployment
"""

import sys
import os
import asyncio

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the bot
if __name__ == "__main__":
    try:
        from bot import main
        print("Starting CodeVerse Bot...")
        print(f"Platform: {os.getenv('HOSTING_PLATFORM', 'unknown')}")
        print(f"Instance: {os.getenv('INSTANCE_ID', 'production')}")
        
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot shutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
