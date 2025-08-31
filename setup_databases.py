#!/usr/bin/env python3
"""
Database Setup Script - Initialize all bot databases
Run this before deploying to ensure databases exist
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def setup_databases():
    """Setup all required databases"""
    try:
        from utils.database_init import initialize_all_databases
        
        print("🚀 Initializing CodeVerse Bot databases...")
        
        if initialize_all_databases():
            print("✅ All databases created successfully!")
            print("\n📁 Created files:")
            
            data_dir = Path("data")
            if data_dir.exists():
                for db_file in data_dir.glob("*.db"):
                    size = db_file.stat().st_size
                    print(f"   • {db_file.name} ({size} bytes)")
            
            return True
        else:
            print("❌ Database initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = setup_databases()
    exit(0 if success else 1)
