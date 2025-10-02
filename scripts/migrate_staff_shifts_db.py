"""
Database migration script to add pause functionality columns to staff_shifts.db
Run this once to update your existing database schema.
"""
import sqlite3
import sys
from pathlib import Path

def migrate_database():
    db_path = Path("data/staff_shifts.db")
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        print("No migration needed - database will be created with correct schema on first run.")
        return
    
    print(f"🔍 Found database at {db_path}")
    print("Starting migration...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(shifts)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"Current columns: {', '.join(columns)}")
        
        columns_to_add = []
        if 'paused' not in columns:
            columns_to_add.append(('paused', 'BOOLEAN DEFAULT 0'))
        if 'pause_time' not in columns:
            columns_to_add.append(('pause_time', 'DATETIME DEFAULT NULL'))
        if 'pause_intervals' not in columns:
            columns_to_add.append(('pause_intervals', "TEXT DEFAULT '[]'"))
        
        if not columns_to_add:
            print("✅ Database is already up to date! No migration needed.")
            conn.close()
            return
        
        # Add missing columns
        for column_name, column_def in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE shifts ADD COLUMN {column_name} {column_def}")
                print(f"✅ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"⚠️  Column {column_name} already exists, skipping")
                else:
                    raise
        
        conn.commit()
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(shifts)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"\n✅ Migration complete!")
        print(f"Updated columns: {', '.join(new_columns)}")
        
        conn.close()
        
        print("\n🎉 Database migration successful!")
        print("You can now restart your bot.")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_database()
