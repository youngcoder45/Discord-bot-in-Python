# BOT PRODUCTION SETUP GUIDE

## 🛡️ Making CodeVerse Bot Your Main Moderation Bot - Complete Safety Guide

### Is This Bot Safe for Production?

**YES** - This bot is designed with enterprise-grade safety mechanisms:

## 🔒 Built-in Safety Features

### 1. **Rate Limiting Protection**
- **Tempban**: Max 3 uses per 5 minutes per user
- **Mute**: Max 5 uses per 5 minutes per user
- **Point System**: 2-moderator approval required for bans
- **Mass Actions**: Built-in limits (max 20 users for massban)

### 2. **Permission Hierarchy Respect**
- Cannot ban/kick users with equal or higher roles
- Cannot target server owner
- Proper permission checks on all commands
- Role-based command restrictions

### 3. **Command Limits & Safeguards**
- **Tempban**: Maximum 7 days (10,080 minutes)
- **Mute**: Maximum 28 days (40,320 minutes) 
- **Slowmode**: Maximum 6 hours (21,600 seconds)
- **Point System**: 100-point monthly cap with resets
- **Auto-timeout**: Commands that could cause server damage require confirmation

### 4. **Automatic Protections**
- **Anti-Raid**: Detects join floods and alerts staff
- **Anti-Nuke**: Monitors mass bans/kicks and alerts staff
- **Automod**: Configurable content filtering with reasonable defaults
- **Auto-Dehoist**: Prevents nickname hoisting automatically

---

## 🤖 Discord Developer Portal Setup

### Step 1: Create Production Bot
1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Name it something like "CodeVerse Moderation Bot"
4. Go to "Bot" tab and click "Add Bot"

### Step 2: Configure Bot Settings
```
TOKEN SETTINGS:
✅ Enable "Presence Intent" 
✅ Enable "Server Members Intent"
✅ Enable "Message Content Intent"

PRIVILEGES:
❌ Disable "Public Bot" (keep it private to your server)
✅ Enable "Requires OAuth2 Code Grant" (optional security)
```

### Step 3: Bot Permissions Calculator
**Required Permissions Integer: `1394542166262`**

**Or select these individual permissions:**
```
GENERAL PERMISSIONS:
✅ View Channels
✅ Manage Channels
✅ Manage Roles
✅ Manage Server
✅ View Audit Log
✅ Read Messages/View Channels
✅ Send Messages
✅ Create Public Threads
✅ Create Private Threads
✅ Send Messages in Threads
✅ Manage Messages
✅ Manage Threads
✅ Embed Links
✅ Attach Files
✅ Read Message History
✅ Use External Emojis
✅ Add Reactions

MODERATION PERMISSIONS:
✅ Kick Members
✅ Ban Members
✅ Timeout Members
✅ Manage Nicknames
```

### Step 4: Bot Invite URL
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_CLIENT_ID&permissions=1394542166262&scope=bot%20applications.commands
```

Replace `YOUR_BOT_CLIENT_ID` with your bot's Client ID from the General Information tab.

---

## ⚙️ Server Role Setup

### 1. **Create Bot Role**
- Name: `CodeVerse Bot`
- Position: **ABOVE** all roles it needs to moderate
- Permissions: Same as above

### 2. **Role Hierarchy (CRITICAL)**
```
@Server Owner (you)
@Admin
@CodeVerse Bot  ← MUST BE HERE OR HIGHER
@Moderator
@Staff
@Members
@everyone
```

### 3. **Staff Role Configuration**
All Discord IDs (roles, channels, users, guilds) are now configured in the root `.env` file (see `.env.example` for the full list). Update the ones relevant to your server:
```dotenv
# Your main moderation role
MODERATION_ROLE_ID=your_mod_role_id_here

# Authorized guilds (comma-separated)
AUTHORIZED_GUILD_IDS=your_guild_id_here
```

---

## 🚦 Deployment Steps

### 1. **Test Environment First**
```bash
# Clone and setup
git clone https://github.com/youngcoder45/Discord-bot-in-Python.git
cd codeverse-bot
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. **Configure Environment**
Create `.env` file:
```env
DISCORD_TOKEN=your_production_bot_token
GUILD_ID=your_server_id
INSTANCE_ID=production-main
```

### 3. **Database Setup**
```bash
# Bot will create databases automatically on first run
# Locations: data/codeverse_bot.db, data/staff_points.db, etc.
```

### 4. **First Deployment**
```bash
python main.py
```

### 5. **Sync Slash Commands**
```bash
# Run once after deployment
python sync_commands.py
```

---

## 📊 Monitoring & Maintenance

### Essential Commands for Admins
```bash
# Check bot health
?diag

# Monitor moderation stats  
?modstats

# View automod settings
?automodstatus

# Check appeal system
?appeals all

# Monitor point system
?pendingbans
```

### Log Channels Setup
Create these channels for proper monitoring:
- `#automod-logs` - Automatic moderation actions
- `#mod-logs` - Manual moderation actions  
- `#staff-alerts` - Raid/nuke detection alerts
- `#appeals` - Appeal notifications (channel ID goes in `.env`, e.g. `APPEALS_LOG_CHANNEL_IDS` / `LOG_CHANNEL_WARNINGS_ID`)

---

## 🛠️ Advanced Configuration

### Automod Settings
```bash
# Configure automod features
?automod invite_links true     # Block Discord invites
?automod excessive_caps true   # Block excessive caps (>70%)
?automod excessive_mentions true  # Block mass mentions (>5)
?automod auto_dehoist true     # Remove special chars from nicknames
```

### Point System Configuration
- **Monthly Reset**: Automatic on 1st of each month
- **Ban Threshold**: 100 points
- **Approval Required**: 2 moderators with Ban Members permission
- **Appeal System**: Automatic DMs sent on moderation actions

---

## 🚨 Emergency Procedures

### If Bot Gets Compromised
1. **Immediately revoke bot token** in Developer Portal
2. **Remove bot from server** temporarily
3. **Check audit logs** for any unauthorized actions
4. **Generate new token** and update `.env`
5. **Review permissions** before re-adding

### Rollback Plan
```bash
# Stop bot
Ctrl+C

# Backup current data
cp -r data/ data_backup_$(date +%Y%m%d)

# Restore from previous backup if needed
cp -r backup/bot_data_backup_YYYYMMDD.json data/
```

---

## ✅ Production Readiness Checklist

### Pre-Deployment
- [ ] Bot created in Discord Developer Portal
- [ ] Proper permissions configured (1394542166262)
- [ ] Bot role positioned correctly in hierarchy
- [ ] `.env` file configured with production token
- [ ] Test commands in private channel first
- [ ] Backup system configured

### Post-Deployment
- [ ] Slash commands synced (`python sync_commands.py`)
- [ ] Staff trained on new commands
- [ ] Log channels created and configured
- [ ] Automod settings reviewed and configured
- [ ] Point system tested with test user
- [ ] Appeal system tested
- [ ] Emergency procedures documented

### Ongoing Maintenance
- [ ] Monitor `?diag` output daily
- [ ] Review moderation statistics weekly
- [ ] Check appeal backlog regularly
- [ ] Update bot when new features are released
- [ ] Backup data regularly

---

## 🏆 Why This Bot is Production-Ready

### Enterprise Features
1. **Point-based escalation** prevents impulsive permanent bans
2. **Two-step approval** prevents moderator abuse
3. **Professional appeal system** maintains community trust
4. **Comprehensive audit trail** for accountability
5. **Rate limiting** prevents command spam/abuse
6. **Auto-moderation** reduces manual workload
7. **Data persistence** survives deployments/restarts

### Safety Guarantees
- **Cannot ban server owner** - hardcoded protection
- **Respects role hierarchy** - cannot target equal/higher roles
- **Rate limited commands** - prevents spam abuse
- **Permission checks** - every command validates permissions
- **Confirmation required** - destructive actions need approval
- **Audit logging** - all actions are tracked and logged

**This bot is safer than most human moderators because it has consistent rules, cannot be emotionally compromised, and has built-in safeguards against abuse.**

---

## 🎯 Quick Start for Immediate Deployment

1. **Create bot** → Developer Portal → Copy token
2. **Invite bot** → Use permission integer `1394542166262`
3. **Position role** → Above roles it needs to moderate
4. **Configure `.env`** → Add token and guild ID
5. **Run bot** → `python main.py`
6. **Sync commands** → `python sync_commands.py`
7. **Test moderation** → Try `?tempban @testuser 5` in private channel
8. **Configure automod** → `?automod invite_links true`

**You're ready for production! 🚀**