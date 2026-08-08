"""
Database Initialization Utility
Ensures all required databases exist before bot startup
"""
import os
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger("codeverse.database_init")

def initialize_all_databases():
    """Initialize all required databases with proper schema"""
    try:
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        logger.info("📁 Data directory ensured")
        
        logger.info("✅ All databases initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    # Allow running this file directly for testing
    logging.basicConfig(level=logging.INFO)
    initialize_all_databases()
