#!/usr/bin/env python3
"""
Production startup script for hosting platforms
"""

import os
import sys
import asyncio
import logging

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Production startup"""
    print("🚀 Starting CodeVerse Bot in production mode...")
    
    # Set hosting platform flag
    os.environ['HOSTING_PLATFORM'] = 'production'
    
    # Add src directory to Python path
    src_path = os.path.join(os.getcwd(), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    try:
        # Import and run the bot
        import bot
        asyncio.run(bot.main())
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
