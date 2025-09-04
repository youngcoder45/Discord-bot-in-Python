# 🛡️ Complete Data Persistence Guide - Never Lose Your Bot Data Again!

## 🎯 **CRITICAL OVERVIEW**

This guide ensures your **staff aura data, shift data, and all bot configurations** survive:
- ✅ Git commits and pushes
- ✅ Code deployments
- ✅ Bot restarts
- ✅ Hosting platform changes
- ✅ Server crashes
- ✅ Accidental data loss

**Your data is protected by a 3-layer backup system:**
1. **Local JSON backups** (automatic every 6 hours)
2. **GitHub cloud backups** (automatic + manual)
3. **Emergency scripts** (instant backup/restore)

---

## 🚨 **IMMEDIATE SETUP (5 Minutes)**

### Step 1: Check Current Data Status

First, verify what data you currently have:

```bash
# Run this to see your current aura data
python check_aura.py

# Create immediate backup of current data
python emergency_backup.py
```

### Step 2: Set Up GitHub Backup (ESSENTIAL)

1. **Create GitHub Personal Access Token:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - **Name:** `CodeVerse Bot Data Backup`
   - **Scopes:** Check ✅ `repo` (Full control of private repositories)
   - **Generate and COPY the token** (you won't see it again!)

2. **Add to Environment Variables:**

Edit your `.env` file and add these lines:
```bash
# ===== DATA PERSISTENCE (REQUIRED) =====
GITHUB_TOKEN=ghp_your_github_personal_access_token_here
GITHUB_REPO=youngcoder45/Discord-bot-in-Python
BACKUP_BRANCH=bot-data-backup
BACKUP_INTERVAL_HOURS=6
MAX_LOCAL_BACKUPS=5
```

### Step 3: Test the System

```bash
# Test the backup system
python emergency_backup.py

# Start your bot normally
python main.py

# In Discord, test manual backup
/data backup

# Check backup status
/data status
```

---

## 🔧 **HOW IT WORKS**

### Automatic Protection (Zero Effort)

Your bot automatically:
1. **Backs up data every 6 hours** to GitHub and local files
2. **Restores data on startup** from the most recent backup
3. **Creates safety backups** before any data operations
4. **Maintains 5 local backup files** as fallback

### Protected Data

The system backs up:
- ✅ **Staff aura points** (all points, history, logs)
- ✅ **Staff shift data** (all shifts, settings, logs)
- ✅ **Election data** (votes, candidates, results)
- ✅ **Bot configuration** (settings, role IDs, channel IDs)
- ✅ **JSON data files** (quotes, questions, challenges)

### Data Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Your Bot      │    │   Backup System  │    │  GitHub Cloud   │
│   Databases     │───▶│   (Automatic)    │───▶│   Storage       │
│                 │    │                  │    │                 │
│ • staff_points  │    │ • Every 6 hours  │    │ • bot-data-     │
│ • staff_shifts  │    │ • On data change │    │   backup branch │
│ • codeverse_bot │    │ • Before commits │    │ • JSON format   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Local Backups   │
                       │                  │
                       │ • 5 files kept   │
                       │ • backup/ folder │
                       │ • Timestamped    │
                       └──────────────────┘
```

---

## 🚀 **USAGE GUIDE**

### Daily Operations (Set and Forget)

Once configured, the system runs automatically:

```bash
# Just run your bot normally - data is protected!
python main.py

# Your data is automatically:
# ✅ Backed up every 6 hours
# ✅ Restored on bot startup  
# ✅ Protected during git operations
```

### Manual Backup Commands

**In Discord (Admin only):**

```
/data backup     # Create immediate backup
/data status     # Check backup system health  
/data restore    # Restore from backup (DANGEROUS!)
```

**Command Line Scripts:**

```bash
# Emergency backup (before risky operations)
python emergency_backup.py

# Check current aura data
python check_aura.py

# Verify all data is safe
python verify_data_safety.py
```

### Safe Git Workflow

Your data is now safe during git operations:

```bash
# 1. Create backup before changes (optional - auto backup runs anyway)
python emergency_backup.py

# 2. Make your code changes
git add .
git commit -m "Your changes"

# 3. Push without worry - data is protected!  
git push origin master

# 4. Bot automatically restores data on restart!
```

---

## 🛠️ **CONFIGURATION OPTIONS**

### Environment Variables

```bash
# Required
GITHUB_TOKEN=ghp_your_token_here           # GitHub Personal Access Token
GITHUB_REPO=youngcoder45/Discord-bot-in-Python  # Your repo
BACKUP_BRANCH=bot-data-backup              # Branch for backups

# Optional  
BACKUP_INTERVAL_HOURS=6                    # Backup frequency (default: 6)
MAX_LOCAL_BACKUPS=5                        # Local files to keep (default: 5)
```

### Backup Frequency

You can adjust automatic backup frequency:

```bash
# Backup every 2 hours (more frequent)
BACKUP_INTERVAL_HOURS=2

# Backup every 12 hours (less frequent)  
BACKUP_INTERVAL_HOURS=12
```

### Local Backup Management

Local backups are stored in `backup/` folder:
- Files named: `bot_data_backup_YYYYMMDD_HHMMSS.json`
- Only 5 most recent files kept
- Automatic cleanup of old files

---

## 🔍 **TROUBLESHOOTING**

### Problem: "No data found after restart"

**Solution:**
```bash
# 1. Check if backups exist
ls backup/

# 2. Check latest backup content
python emergency_backup.py

# 3. Manually restore from backup
/data restore

# 4. Verify GitHub token is correct
echo $GITHUB_TOKEN
```

### Problem: "Backup failed"

**Check GitHub token:**
```bash
# Verify token has repo permissions
# Go to: https://github.com/settings/tokens
# Make sure 'repo' scope is checked
```

**Check internet connection:**
```bash
# Test GitHub API access
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

### Problem: "Data partially missing"

**Force full restore:**
```bash
# 1. Stop bot
# 2. Delete current databases
rm data/*.db

# 3. Start bot (automatic restore)
python main.py

# OR manually restore
/data restore
```

### Problem: "Backup branch not found"

The system automatically creates the backup branch. If missing:

```bash
# System will auto-create on first backup
python emergency_backup.py

# Or check GitHub repo for 'bot-data-backup' branch
```

---

## 📊 **MONITORING YOUR DATA**

### Check Data Health

```bash
# View current aura data
python check_aura.py

# Check all database contents
python debug_db.py

# View backup status
/data status
```

### Backup Verification

```bash
# List all backups
ls -la backup/

# Check latest backup size (should be > 1KB)
du -h backup/bot_data_backup_*.json | tail -1

# View backup contents
python -c "import json; print(json.load(open('backup/bot_data_backup_20250904_120110.json'))['databases'].keys())"
```

### GitHub Backup Status

1. Go to your repository: https://github.com/youngcoder45/Discord-bot-in-Python
2. Switch to `bot-data-backup` branch
3. Check `bot_data_backup.json` file exists and is recent
4. File should be updated every 6 hours

---

## ⚡ **EMERGENCY PROCEDURES**

### Emergency Backup (Before Risky Operations)

```bash
# ALWAYS run before:
# - Major code changes
# - Git operations  
# - Server maintenance
# - Bot updates

python emergency_backup.py
```

### Emergency Restore (Data Lost)

```bash
# If all data is lost:

# 1. Check available backups
ls backup/

# 2. Stop bot if running

# 3. Force restore from latest backup
python -c "
import asyncio
import sys
sys.path.insert(0, 'src')
from utils.data_persistence import persistence_manager
asyncio.run(persistence_manager.restore_from_local())
"

# 4. Start bot
python main.py
```

### Nuclear Option (Complete Reset with Data Restore)

```bash
# ONLY if everything is broken:

# 1. Backup current state
python emergency_backup.py

# 2. Delete all databases
rm data/*.db

# 3. Start fresh with restored data
python main.py

# Bot will automatically:
# - Restore from latest backup
# - Initialize fresh databases with your data
```

---

## 🎯 **VERIFICATION CHECKLIST**

After setup, verify everything works:

- [ ] ✅ GitHub token is set in `.env`
- [ ] ✅ `python emergency_backup.py` runs without errors
- [ ] ✅ Bot starts with `python main.py` 
- [ ] ✅ `/data backup` works in Discord
- [ ] ✅ `/data status` shows healthy backups
- [ ] ✅ `backup/` folder contains JSON files
- [ ] ✅ GitHub repo has `bot-data-backup` branch
- [ ] ✅ Aura data persists after bot restart
- [ ] ✅ Shift data persists after bot restart

### Test Data Persistence

```bash
# 1. Note current aura data
/aura leaderboard

# 2. Make a code change and commit
git add . && git commit -m "test"

# 3. Restart bot
# Stop bot, then start: python main.py

# 4. Verify data is unchanged
/aura leaderboard

# Should be identical to step 1!
```

---

## 🎉 **SUCCESS!**

Once configured, your bot data is **bulletproof**! 

You can now:
- ✅ Commit and push code changes without fear
- ✅ Restart the bot anytime  
- ✅ Deploy to different hosting platforms
- ✅ Recover from any data loss scenario
- ✅ Focus on bot features, not data management

**Your staff aura, shift data, and configurations will NEVER be lost again!**

---

## 📞 **Support**

If you encounter issues:

1. **Check logs:** Bot console shows backup status
2. **Run diagnostics:** `python emergency_backup.py`
3. **Verify setup:** Use verification checklist above
4. **Test manually:** `/data backup` and `/data status` in Discord

The system is designed to be **bulletproof** - your data is safe! 🛡️
