# Utility Scripts

This folder contains utility scripts for maintenance and migrations.

## Available Scripts

### migrate_staff_shifts_db.py
**Purpose:** Database migration script for staff shifts system  
**Usage:** `python scripts/migrate_staff_shifts_db.py`  
**Description:** Adds pause/resume functionality columns to existing staff_shifts.db

**When to use:**
- After updating staff shifts cog with new features
- When database schema changes require migration
- First-time setup if database already exists

### data_guard.py
**Purpose:** Data protection and integrity monitoring  
**Usage:** `python scripts/data_guard.py`  
**Description:** Monitors and protects bot data from corruption

**When to use:**
- Regular data integrity checks
- Before major updates
- After system crashes or unexpected shutdowns

---

## Best Practices

1. **Always backup before running migrations**
   ```bash
   cp -r data/ data_backup_$(date +%Y%m%d)/
   ```

2. **Test scripts in development first**
   - Never run untested scripts on production data
   - Keep backups of production databases

3. **Run migrations during low traffic**
   - Stop the bot before running migrations
   - Verify success before restarting

4. **Keep scripts updated**
   - Version control all migration scripts
   - Document schema changes

---

**Note:** These scripts are utilities and not part of the main bot runtime.
