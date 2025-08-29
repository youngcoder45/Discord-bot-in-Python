# 🔄 Data Persistence Setup Guide - CodeVerse Bot

## 🎯 Overview

This guide will help you set up **automatic data persistence** for your CodeVerse Bot, ensuring that all your staff data, points, shifts, and configurations are **never lost** when you redeploy or make code changes.

---

## 🚨 **CRITICAL: Why You Need This**

**Without data persistence:**
- ❌ Staff shift data gets wiped on every deployment
- ❌ Staff points and leaderboards reset to zero
- ❌ Election data and votes are lost
- ❌ All configurations need to be redone
- ❌ Bot suggestions and history disappear

**With data persistence:**
- ✅ All data survives code changes and deployments
- ✅ Automatic backups every 6 hours
- ✅ Manual backup/restore commands
- ✅ GitHub-based cloud storage
- ✅ Local backup files as fallback

---

## 🔧 Quick Setup (5 Minutes)

### Step 1: Create GitHub Personal Access Token

1. **Go to GitHub Settings:**
   - Visit: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"

2. **Configure Token:**
   - **Note:** `CodeVerse Bot Data Backup`
   - **Expiration:** `No expiration` (recommended) or `1 year`
   - **Scopes:** Check ✅ `repo` (Full control of private repositories)

3. **Generate and Copy:**
   - Click "Generate token"
   - **COPY THE TOKEN NOW** (you won't see it again!)

### Step 2: Configure Environment Variables

Add these to your hosting platform's environment variables:

```env
# Your existing variables
DISCORD_TOKEN=your_bot_token
GUILD_ID=your_server_id

# NEW: Data persistence variables
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_REPO=youngcoder45/Discord-bot-in-Python
BACKUP_BRANCH=bot-data-backup
```

### Step 3: Deploy and Test

1. **Deploy your bot** with the new environment variables
2. **Use the command:** `/data status` to verify setup
3. **Create manual backup:** `/data backup`

---

## 🎮 Bot Commands

### 📊 Status and Monitoring

#### `/data status`
**Check data backup and persistence status**
- Shows GitHub configuration status
- Lists local backup files
- Displays database file status
- Shows backup schedule info

#### `/data backup`
**Create immediate backup of all bot data** *(Admin only)*
- Backs up staff shifts, points, elections
- Saves to GitHub and local files
- Includes all configuration data

#### `/data export`
**Export data as downloadable JSON file** *(Admin only)*
- Downloads complete data export
- Perfect for manual backups
- Human-readable format

#### `/data restore`
**Restore data from backup** *(Admin only)*
- **⚠️ DANGEROUS:** Overwrites current data
- Requires confirmation
- Restores from latest backup

---

## 🔄 How It Works

### Automatic Backups
- **Every 6 hours** while bot is running
- **On bot startup** (restores data first)
- **Stores in:** GitHub repository + local files

### Data Included
✅ **Staff Shifts Database** - All shift history and settings  
✅ **Staff Points Database** - Points, leaderboards, history  
✅ **Election Data** - Active and past elections  
✅ **JSON Data Files** - Questions, quotes, challenges  
✅ **Configuration Settings** - Channel IDs, role IDs  

### Storage Locations
1. **GitHub Repository** - Primary cloud storage
2. **Local Backup Files** - Secondary fallback storage

---

## 🔒 Security and Privacy

### GitHub Repository Access
- Uses your **private repository** by default
- Data stored in `bot-data-backup` branch
- Only you have access to the backup data

### Environment Variables
- GitHub token is stored as environment variable
- Never committed to code repository
- Secure hosting platform storage

### Data Encryption
- Data transmitted via HTTPS to GitHub
- GitHub provides enterprise-level security
- Local files stored securely on hosting platform

---

## 🚨 Troubleshooting

### "GitHub backup failed" Error

**Check these:**
1. ✅ GitHub token is correct and not expired
2. ✅ Token has `repo` scope permission
3. ✅ Repository name is correct
4. ✅ Internet connection is available

**Solution:**
```bash
# Test your token manually:
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

### "No backup found" on Startup

**This is normal for:**
- First time setup
- Fresh deployments
- New GitHub repositories

**The bot will:**
- Start with fresh databases
- Create backups on first run
- Restore properly on next deployment

### Missing Environment Variables

**Required variables:**
```env
DISCORD_TOKEN=your_bot_token
GUILD_ID=your_server_id
GITHUB_TOKEN=your_github_token  # For data persistence
```

**Check in hosting platform:**
- bot-hosting.net dashboard
- Environment variables section
- Verify all variables are set

---

## 🎯 Best Practices

### 1. Test Before Important Changes
```bash
# Before major code changes:
/data backup           # Create manual backup
/data export           # Download local copy
```

### 2. Monitor Backup Status
```bash
# Check regularly:
/data status          # Verify backups are working
```

### 3. Keep GitHub Token Secure
- Never share your GitHub token
- Use environment variables only
- Set expiration reminders

### 4. Regular Verification
- Test restore process occasionally
- Verify data integrity after deployments
- Keep local exports for critical data

---

## 🔗 Environment Variables Reference

```env
# ===== REQUIRED =====
DISCORD_TOKEN=your_discord_bot_token
GUILD_ID=your_server_id

# ===== DATA PERSISTENCE =====
GITHUB_TOKEN=ghp_your_github_personal_access_token
GITHUB_REPO=youngcoder45/Discord-bot-in-Python
BACKUP_BRANCH=bot-data-backup

# ===== HOSTING =====
HOSTING_PLATFORM=bot-hosting.net
PORT=8080
INSTANCE_ID=production

# ===== OPTIONAL =====
SERVER_LOGS_CHANNEL_ID=your_log_channel_id
BACKUP_INTERVAL_HOURS=6
MAX_LOCAL_BACKUPS=5
```

---

## 🆘 Emergency Recovery

### If All Backups Fail

1. **Check GitHub repository:**
   - Go to your repository
   - Switch to `bot-data-backup` branch
   - Download `bot_data_backup.json`

2. **Manual restore:**
   - Contact support with backup file
   - Use `/data restore` command
   - Restore from exported JSON

3. **Prevention:**
   - Set up multiple backup methods
   - Export data before major changes
   - Monitor `/data status` regularly

---

## ✅ Success Checklist

- [ ] GitHub personal access token created
- [ ] Environment variables configured in hosting platform
- [ ] Bot deployed with new settings
- [ ] `/data status` shows "✅ Configured" for GitHub
- [ ] `/data backup` completes successfully
- [ ] Backup files appear in GitHub repository
- [ ] Data survives a test redeployment

**🎉 Congratulations!** Your bot data is now protected and will persist across all deployments and code changes!
