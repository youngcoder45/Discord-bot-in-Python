# ⏰ Staff Shifts Guide - CodeVerse Bot

## 🎯 Overview

The Staff Shifts system allows staff members to log their on-duty time with automatic logging to a designated channel. This helps track staff activity and accountability.

---

## 🚀 Setup (Admin Only)

### 1. Configure Log Channel
Set up a channel where shift logs will be posted:
```
/shift settings logs #staff-logs
```

### 2. Add Staff Roles
Add roles that should be able to use shift commands:
```
/shift settings addrole @Moderator
/shift settings addrole @Admin
/shift settings addrole @Helper
```

### 3. Verify Configuration
List current staff roles:
```
/shift settings listroles
```

---

## 👥 Staff Usage

### Starting a Shift
Staff members can start their shift with an optional note:
```
/shift start
/shift start Working on moderation today
```

**What happens:**
- ✅ Logs start time in database
- 📝 Posts embed to log channel with timestamp
- 🚫 Prevents multiple active shifts per user

### Ending a Shift
End your current shift with an optional note:
```
/shift end
/shift end Great shift, helped 15 users
```

**What happens:**
- ✅ Logs end time and calculates duration
- 📝 Posts embed to log channel with full shift summary
- 📊 Shows total time on duty

### Discarding a Shift
Remove current shift without logging an end time:
```
/shift discard
```

**Use cases:**
- Accidentally started a shift
- Need to restart shift tracking
- System errors during shift

---

## 📊 Features

### ✨ Rich Embeds
All shift activities generate beautiful Discord embeds with:
- 🟢 **Green** for shift start
- 🔴 **Red** for shift end  
- 🟡 **Yellow** for shift discard
- 👤 User avatar and name
- ⏰ Discord timestamps (automatically timezone-aware)
- 📝 Start/end notes if provided

### 🔒 Permission System
- **Staff commands** - Only users with configured staff roles
- **Settings commands** - Require appropriate Discord permissions:
  - `logs` - Manage Channels
  - `addrole/removerole/clearroles` - Manage Roles
  - `listroles` - Available to everyone

### 💾 Persistent Database
- Uses SQLite database (`data/staff_shifts.db`)
- Stores shift history and guild settings
- Automatic database creation and migration
- Handles timezone-aware datetime storage

---

## 🎮 Command Reference

### Staff Commands
| Command | Permission | Description |
|---------|------------|-------------|
| `/shift start [note]` | Staff | Start your shift with optional note |
| `/shift end [note]` | Staff | End your shift with optional note |
| `/shift discard` | Staff | Discard current shift without logging end |

### Admin Management Commands
| Command | Permission | Description |
|---------|------------|-------------|
| `/shift admin active` | Manage Guild | View all currently active shifts |
| `/shift admin history [user] [days]` | Manage Guild | View shift history (default: 7 days) |
| `/shift admin end <user> [reason]` | Manage Guild | Force end a user's active shift |
| `/shift admin stats [user] [days]` | Manage Guild | View shift statistics (default: 30 days) |
| `/shift admin summary [days]` | Manage Guild | Staff activity summary (default: 7 days) |

### Settings Commands
| Command | Permission | Description |
|---------|------------|-------------|
| `/shift settings logs [#channel]` | Manage Channels | Set log channel (none to disable) |
| `/shift settings addrole <role>` | Manage Roles | Add role to staff list |
| `/shift settings removerole <role>` | Manage Roles | Remove role from staff list |
| `/shift settings clearroles` | Manage Roles | Clear all staff roles |
| `/shift settings listroles` | None | List current staff roles |

---

## 🛠️ Admin Management

### Role Management
```bash
# Add multiple roles
/shift settings addrole @Moderator
/shift settings addrole @Admin
/shift settings addrole @Helper

# Remove a role
/shift settings removerole @Helper

# Start fresh (clear all roles)
/shift settings clearroles

# Check current setup
/shift settings listroles
```

### Log Channel Management
```bash
# Set log channel
/shift settings logs #staff-shifts

# Disable logging
/shift settings logs
```

---

## � Admin Features

### View Active Shifts
See who's currently on duty with real-time information:
```
/shift admin active
```

**Shows:**
- All currently active staff shifts
- How long each staff member has been on duty
- Start notes for context
- Real-time duration updates

### Shift History
View detailed shift history with filtering options:
```
/shift admin history                    # Last 7 days, all staff
/shift admin history @StaffMember      # Specific user, 7 days
/shift admin history @StaffMember 30   # Specific user, 30 days
```

**Features:**
- Filter by specific staff member
- Custom time range (1-365 days)
- Shows completed and ongoing shifts
- Start/end times and notes
- Shift duration for completed shifts

### Force End Shifts
Manually end a staff member's shift when needed:
```
/shift admin end @StaffMember System maintenance
/shift admin end @StaffMember          # No reason required
```

**Use cases:**
- Staff forgot to end their shift
- Emergency situations requiring immediate shift end
- System maintenance or bot restarts
- Disciplinary actions

### Shift Statistics
Get comprehensive statistics for monitoring:
```
/shift admin stats                     # Server-wide stats, 30 days
/shift admin stats @StaffMember       # Individual stats, 30 days
/shift admin stats @StaffMember 90    # Individual stats, 90 days
```

**Server Stats Include:**
- Total shifts started
- Completed vs ongoing shifts
- Total hours logged
- Average shift length
- Number of active staff members

**Individual Stats Include:**
- Personal shift count
- Total hours on duty
- Average shift duration
- Completion rate

### Staff Activity Summary
Monitor overall staff engagement:
```
/shift admin summary                   # Last 7 days
/shift admin summary 30               # Last 30 days
```

**Shows:**
- Most active staff (by hours)
- Inactive staff members (no shifts)
- Overall server activity metrics
- Staff participation rates

---

## 📊 Sample Usage Workflow

### Initial Setup
1. **Admin**: `/shift settings logs #staff-logs`
2. **Admin**: `/shift settings addrole @Moderator`
3. **Admin**: `/shift settings addrole @Admin`

### Daily Staff Use
1. **Staff**: `/shift start Morning shift - focusing on general chat`
2. *[Works for several hours]*
3. **Staff**: `/shift end Helped 12 users, resolved 3 issues`

### Admin Monitoring
1. **Admin**: `/shift admin active` - Check who's currently on duty
2. **Admin**: `/shift admin stats @TopStaff 7` - Review individual performance
3. **Admin**: `/shift admin summary 30` - Monthly activity report

### Emergency Management
1. **Issue**: Staff member forgot to end shift before going offline
2. **Admin**: `/shift admin end @ForgetfulStaff Shift ended - user went offline`
3. **Result**: Clean shift logs and accurate duration tracking

---

## �📋 Sample Usage Workflow

### Initial Setup
1. **Admin**: `/shift settings logs #staff-logs`
2. **Admin**: `/shift settings addrole @Moderator`
3. **Admin**: `/shift settings addrole @Admin`

### Staff Member Daily Use
1. **Staff**: `/shift start Morning shift - focusing on general chat`
2. *[Works for several hours]*
3. **Staff**: `/shift end Helped 12 users, resolved 3 issues`

### Log Channel Output
```
🟢 Shift Started
@StaffMember has just started their shift.

Start Time: Today at 9:00 AM
Start Note:
```
Morning shift - focusing on general chat
```

🔴 Shift Ended
@StaffMember has just ended their shift.

Start Time: Today at 9:00 AM    End Time: Today at 2:30 PM
Start Note:
```
Morning shift - focusing on general chat
```
End Note:
```
Helped 12 users, resolved 3 issues
```
```

---

## 🚨 Error Handling

### Common Scenarios
- **"You are not a staff member"** - User doesn't have configured staff roles
- **"You already have a shift in progress"** - User tries to start when already active
- **"You don't have an active shift"** - User tries to end/discard when no active shift
- **"Log channel not found"** - Configured log channel was deleted

### Data Integrity
- ✅ Prevents duplicate active shifts per user
- ✅ Automatic database schema creation
- ✅ Timezone-aware timestamp handling
- ✅ Graceful handling of missing channels/roles

---

## 🔧 Technical Details

### Database Schema
```sql
-- Shift records
CREATE TABLE shifts (
    shift_id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    start DATETIME NOT NULL,
    end DATETIME DEFAULT NULL,
    start_note TEXT DEFAULT NULL,
    end_note TEXT DEFAULT NULL
);

-- Guild settings
CREATE TABLE shift_settings (
    guild_id INTEGER PRIMARY KEY,
    log_channel_id INTEGER DEFAULT NULL,
    staff_role_ids TEXT DEFAULT '[]'  -- JSON array
);
```

### File Structure
- **Database**: `data/staff_shifts.db`
- **Cog**: `src/commands/staff_shifts.py`
- **Dependencies**: `aiosqlite>=0.19.0`

---

## 💡 Pro Tips

1. **Use descriptive notes** to help track what work was done during shifts
2. **Set up a dedicated log channel** to keep shift logs organized
3. **Review shift logs regularly** to understand staff activity patterns
4. **Use `/shift discard` sparingly** - it doesn't log end times for analytics
5. **Staff roles can be any Discord role** - doesn't need special permissions

---

**The Staff Shifts system is now fully integrated with your CodeVerse Bot and ready to help manage your staff team effectively!**
