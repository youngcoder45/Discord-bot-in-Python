#!/usr/bin/env python3
"""
Main entry point for CodeVerse Discord Bot
Redirects to src/bot.py for better organization
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the bot
if __name__ == "__main__":
    from bot import main
    import asyncio
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot shutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
