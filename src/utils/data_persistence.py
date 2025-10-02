"""
Data Persistence Manager - Ensures bot data survives deployments
Supports multiple storage backends: GitHub, JSON files, and future cloud storage
"""
import os
import json
import aiosqlite
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import base64
import aiohttp
from pathlib import Path

logger = logging.getLogger("codeverse.persistence")

class DataPersistenceManager:
    """Manages data persistence across bot deployments"""
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repo = os.getenv('GITHUB_REPO', 'youngcoder45/Discord-bot-in-Python')
        self.backup_branch = os.getenv('BACKUP_BRANCH', 'bot-data-backup')
        self.data_dir = Path("data")
        self.backup_dir = Path("backup")
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
    async def startup_restore(self):
        """Restore data on bot startup"""
        logger.info("🔄 Starting data restoration process...")
        
        try:
            # First, check if we have any existing data to preserve
            existing_data = await self.check_existing_data()
            
            if existing_data["has_data"]:
                logger.info("📊 Found existing data, creating safety backup before restoration...")
                await self.backup_all_data()
            
            # Try GitHub backup first
            if self.github_token:
                restored = await self.restore_from_github()
                if not restored:
                    logger.warning("⚠️ GitHub restore failed, trying local backup...")
                    await self.restore_from_local()
            else:
                logger.warning("⚠️ No GITHUB_TOKEN found, using local backup only")
                await self.restore_from_local()
                
            logger.info("✅ Data restoration completed successfully")
        except Exception as e:
            logger.error(f"❌ Data restoration failed: {e}")
            # Continue with fresh data if restore fails
            await self.initialize_fresh_databases()
    
    async def check_existing_data(self):
        """Check if we have existing data in databases"""
        has_data = False
        data_info = {"has_data": False, "databases": {}}
        
        db_files = [
            "data/staff_shifts.db",
            "data/staff_points.db", 
            "data/codeverse_bot.db"
        ]
        
        for db_path in db_files:
            if os.path.exists(db_path):
                try:
                    async with aiosqlite.connect(db_path) as db:
                        # Get all tables and count rows
                        async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
                            tables = await cursor.fetchall()
                        
                        total_rows = 0
                        for table in tables:
                            table_name = table[0]
                            async with db.execute(f"SELECT COUNT(*) FROM {table_name}") as cursor:
                                count = await cursor.fetchone()
                                total_rows += count[0] if count else 0
                        
                        data_info["databases"][os.path.basename(db_path)] = total_rows
                        if total_rows > 0:
                            has_data = True
                            
                except Exception as e:
                    logger.warning(f"⚠️ Error checking {db_path}: {e}")
        
        data_info["has_data"] = has_data
        if has_data:
            logger.info(f"📊 Existing data found: {data_info['databases']}")
        
        return data_info
    
    async def backup_all_data(self):
        """Backup all bot data"""
        logger.info("💾 Starting comprehensive data backup...")
        
        try:
            backup_data = await self.collect_all_data()
            
            # Save to local backup
            local_success = await self.save_local_backup(backup_data)
            
            # Save to GitHub if token available
            github_success = False
            if self.github_token:
                github_success = await self.save_to_github(backup_data)
            
            if local_success or github_success:
                logger.info("✅ Data backup completed successfully")
                return True
            else:
                logger.error("❌ Both local and GitHub backups failed!")
                return False
                
        except Exception as e:
            logger.error(f"❌ Data backup failed: {e}")
            return False
    
    async def collect_all_data(self) -> Dict[str, Any]:
        """Collect all data from databases and files"""
        backup_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "databases": {},
            "json_files": {},
            "config": {}
        }
        
        # Backup SQLite databases
        db_files = [
            "data/staff_shifts.db",
            "data/staff_points.db",
            "data/codeverse_bot.db"
        ]
        
        for db_path in db_files:
            if os.path.exists(db_path):
                backup_data["databases"][os.path.basename(db_path)] = await self.backup_database(db_path)
        
        # Backup JSON data files
        json_files = [
            "src/data/questions.json",
            "src/data/challenges.json", 
            "src/data/quotes.json",
            "src/data/quotes_new.json",
            "src/data/code_snippets.json"
        ]
        
        for json_path in json_files:
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    backup_data["json_files"][os.path.basename(json_path)] = json.load(f)
        
        # Backup configuration data (environment-specific settings)
        backup_data["config"] = {
            "last_backup": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
            "bot_instance": os.getenv('INSTANCE_ID', 'unknown')
        }
        
        return backup_data
    
    async def backup_database(self, db_path: str) -> Dict[str, Any]:
        """Backup a SQLite database to JSON format"""
        db_backup: Dict[str, Any] = {"tables": {}}
        
        try:
            async with aiosqlite.connect(db_path) as db:
                # Get all table names (excluding internal SQLite tables)
                async with db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'") as cursor:
                    tables = await cursor.fetchall()
                
                for (table_name,) in tables:
                    # Get table schema
                    async with db.execute(f"PRAGMA table_info({table_name})") as cursor:
                        schema = await cursor.fetchall()
                    
                    # Get all table data
                    async with db.execute(f"SELECT * FROM {table_name}") as cursor:
                        rows = await cursor.fetchall()
                    
                    # Get column names
                    columns = [col[1] for col in schema]
                    
                    # Convert rows to dictionaries
                    table_data = []
                    for row in rows:
                        row_dict = {}
                        for i, value in enumerate(row):
                            row_dict[columns[i]] = value
                        table_data.append(row_dict)
                    
                    db_backup["tables"][table_name] = {
                        "schema": schema,
                        "data": table_data
                    }
        
        except Exception as e:
            logger.error(f"Failed to backup database {db_path}: {e}")
            db_backup["error"] = str(e)
        
        return db_backup
    
    async def restore_database(self, db_path: str, backup_data: Dict[str, Any]):
        """Restore a SQLite database from backup data"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            async with aiosqlite.connect(db_path) as db:
                for table_name, table_info in backup_data.get("tables", {}).items():
                    if "error" in backup_data:
                        continue
                    
                    # Skip internal SQLite tables
                    if table_name in ['sqlite_sequence', 'sqlite_stat1', 'sqlite_stat2', 'sqlite_stat3', 'sqlite_stat4']:
                        continue
                        
                    schema = table_info.get("schema", [])
                    data = table_info.get("data", [])
                    
                    if not schema:
                        continue
                    
                    # Create table
                    columns = []
                    for col_info in schema:
                        col_name = col_info[1]
                        col_type = col_info[2]
                        not_null = " NOT NULL" if col_info[3] else ""
                        primary_key = " PRIMARY KEY" if col_info[5] else ""
                        default_val = f" DEFAULT {col_info[4]}" if col_info[4] is not None else ""
                        
                        columns.append(f"{col_name} {col_type}{not_null}{primary_key}{default_val}")
                    
                    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
                    await db.execute(create_sql)
                    
                    # Clear existing data
                    await db.execute(f"DELETE FROM {table_name}")
                    
                    # Insert backed up data
                    if data:
                        placeholders = ", ".join(["?" for _ in data[0].keys()])
                        columns_str = ", ".join(data[0].keys())
                        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                        
                        for row in data:
                            values = list(row.values())
                            await db.execute(insert_sql, values)
                
                await db.commit()
                logger.info(f"✅ Successfully restored database: {db_path}")
        
        except Exception as e:
            logger.error(f"❌ Failed to restore database {db_path}: {e}")
    
    async def save_local_backup(self, backup_data: Dict[str, Any]):
        """Save backup to local file"""
        try:
            backup_file = self.backup_dir / f"bot_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            # Keep only last 5 local backups
            backup_files = sorted(self.backup_dir.glob("bot_data_backup_*.json"))
            while len(backup_files) > 5:
                oldest = backup_files.pop(0)
                oldest.unlink()
            
            logger.info(f"💾 Local backup saved: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Local backup failed: {e}")
            return False
    
    async def restore_from_local(self):
        """Restore from most recent local backup"""
        backup_files = sorted(self.backup_dir.glob("bot_data_backup_*.json"))
        
        if not backup_files:
            logger.info("ℹ️ No local backups found, starting fresh")
            return False
        
        latest_backup = backup_files[-1]
        logger.info(f"📂 Restoring from local backup: {latest_backup}")
        
        try:
            with open(latest_backup, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            await self.restore_from_backup_data(backup_data)
            logger.info("✅ Local restore completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Local restore failed: {e}")
            return False
    
    async def save_to_github(self, backup_data: Dict[str, Any]):
        """Save backup to GitHub repository"""
        if not self.github_token:
            logger.warning("⚠️ No GitHub token available for backup")
            return
        
        try:
            # Prepare backup content
            backup_content = json.dumps(backup_data, indent=2, ensure_ascii=False)
            encoded_content = base64.b64encode(backup_content.encode('utf-8')).decode('utf-8')
            
            # GitHub API endpoints
            base_url = f"https://api.github.com/repos/{self.github_repo}"
            file_path = "bot_data_backup.json"
            
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with aiohttp.ClientSession() as session:
                # First, ensure backup branch exists
                await self._ensure_backup_branch_exists(session, base_url, headers)
                
                # Check if file exists to get SHA
                get_url = f"{base_url}/contents/{file_path}?ref={self.backup_branch}"
                sha = None
                
                async with session.get(get_url, headers=headers) as response:
                    if response.status == 200:
                        file_info = await response.json()
                        sha = file_info.get("sha")
                    elif response.status == 404:
                        # File doesn't exist yet, that's fine for first backup
                        logger.info("📁 Creating first backup file in GitHub")
                
                # Prepare commit data
                commit_data = {
                    "message": f"Bot data backup - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    "content": encoded_content,
                    "branch": self.backup_branch
                }
                
                if sha:
                    commit_data["sha"] = sha
                
                # Create or update file
                put_url = f"{base_url}/contents/{file_path}"
                async with session.put(put_url, headers=headers, json=commit_data) as response:
                    if response.status in [200, 201]:
                        logger.info("✅ Data backed up to GitHub successfully")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ GitHub backup failed: {response.status} - {error_text}")
                        return False
        
        except Exception as e:
            logger.error(f"❌ GitHub backup error: {e}")
            return False
    
    async def restore_from_github(self):
        """Restore data from GitHub backup"""
        if not self.github_token:
            logger.warning("⚠️ No GitHub token available for restore")
            return False
        
        try:
            base_url = f"https://api.github.com/repos/{self.github_repo}"
            file_path = "bot_data_backup.json"
            
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with aiohttp.ClientSession() as session:
                get_url = f"{base_url}/contents/{file_path}?ref={self.backup_branch}"
                
                async with session.get(get_url, headers=headers) as response:
                    if response.status == 200:
                        file_info = await response.json()
                        content = base64.b64decode(file_info["content"]).decode('utf-8')
                        backup_data = json.loads(content)
                        
                        logger.info("📥 Restoring data from GitHub backup...")
                        await self.restore_from_backup_data(backup_data)
                        logger.info("✅ GitHub restore completed successfully")
                        return True
                    else:
                        logger.info("ℹ️ No GitHub backup found")
                        return False
        
        except Exception as e:
            logger.error(f"❌ GitHub restore error: {e}")
            return False
    
    async def restore_from_backup_data(self, backup_data: Dict[str, Any]):
        """Restore from backup data dictionary"""
        try:
            # Restore databases
            for db_name, db_backup in backup_data.get("databases", {}).items():
                db_path = f"data/{db_name}"
                await self.restore_database(db_path, db_backup)
            
            # Restore JSON files
            for file_name, file_data in backup_data.get("json_files", {}).items():
                file_path = f"src/data/{file_name}"
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(file_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"📄 Restored JSON file: {file_path}")
            
            logger.info("✅ All data restored successfully")
        
        except Exception as e:
            logger.error(f"❌ Data restoration failed: {e}")
    
    async def initialize_fresh_databases(self):
        """Initialize fresh databases if no backup is available"""
        logger.info("🆕 Initializing fresh databases...")
        
        # This will be called by each cog's init_database method
        # No need to do anything here, just log
        logger.info("ℹ️ Fresh database initialization will be handled by individual cogs")
    
    async def _ensure_backup_branch_exists(self, session, base_url: str, headers: dict):
        """Ensure the backup branch exists, create it if it doesn't"""
        try:
            # Check if branch exists
            branch_url = f"{base_url}/branches/{self.backup_branch}"
            async with session.get(branch_url, headers=headers) as response:
                if response.status == 200:
                    return  # Branch exists
                
            # Branch doesn't exist, create it from master
            logger.info(f"🌿 Creating backup branch: {self.backup_branch}")
            
            # Get master branch SHA
            master_url = f"{base_url}/git/refs/heads/master"
            async with session.get(master_url, headers=headers) as response:
                if response.status != 200:
                    logger.error("❌ Could not get master branch SHA")
                    return
                
                master_info = await response.json()
                master_sha = master_info["object"]["sha"]
            
            # Create new branch
            create_branch_data = {
                "ref": f"refs/heads/{self.backup_branch}",
                "sha": master_sha
            }
            
            create_url = f"{base_url}/git/refs"
            async with session.post(create_url, headers=headers, json=create_branch_data) as response:
                if response.status == 201:
                    logger.info(f"✅ Backup branch created: {self.backup_branch}")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to create backup branch: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"❌ Error ensuring backup branch exists: {e}")
    
    async def schedule_periodic_backup(self, interval_hours: int = 6):
        """Schedule periodic backups"""
        while True:
            try:
                await asyncio.sleep(interval_hours * 3600)  # Convert hours to seconds
                await self.backup_all_data()
                logger.info(f"⏰ Periodic backup completed (every {interval_hours} hours)")
            except Exception as e:
                logger.error(f"❌ Periodic backup failed: {e}")


# Global instance
persistence_manager = DataPersistenceManager()

async def startup_restore():
    """Called during bot startup to restore data"""
    await persistence_manager.startup_restore()

async def backup_data():
    """Called to backup data"""
    await persistence_manager.backup_all_data()

async def start_periodic_backup():
    """Start periodic backup task"""
    asyncio.create_task(persistence_manager.schedule_periodic_backup())
