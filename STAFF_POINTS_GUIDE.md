# ⭐ Staff Aura System - CodeVerse Bot

## 🎯 Overview

The Staff Aura System is a comprehensive reward and recognition system for staff members. It allows administrators to track staff performance, reward good behavior, and maintain a competitive leaderboard to help with promotions and recognition.

---

## 🚀 Features

### ✨ Core Features
- **Aura Management** - Add, remove, set, and reset staff aura *(Admin Only)*
- **Leaderboard System** - Simple ranking showing all staff with aura
- **Activity Tracking** - Complete history of all aura changes
- **Automatic Thanks Aura** - Staff get 1 aura when thanked via mention/reply
- **Staff Recognition** - Promote healthy competition and recognition
- **Detailed Statistics** - In-depth performance analytics

### 🔒 Permission Levels
- **Everyone** - View own aura, leaderboard, stats
- **Moderators** - View detailed histories and staff statistics
- **Administrators Only** - Full aura management and configuration

---

## 🎮 Command Reference

### 📊 Viewing Commands (Everyone)

#### `/aura` or `/aura check [@user]`
**View aura balance for yourself or another staff member**
```
/aura                      # Your own aura
/aura check @John          # Check John's aura
```

#### `/aura leaderboard`
**View all staff members with aura**
```
/aura leaderboard          # Shows all staff with aura (no limit)
```
**Shows:** Simple ranking without emojis, all staff members with aura

#### `/aura top`
**Quick view of top 3 staff members**
```
/aura top                  # Shows top 3 with medals
```

#### `/aura stats [@user]`
**Detailed statistics for a staff member**
```
/aura stats                # Your own detailed stats
/aura stats @Alice         # Alice's detailed stats
```
**Shows:**
- Current aura and rank
- Total aura earned/spent
- Recent activity (30 days)
- Retention rate
- Last activity timestamp

---

### 📈 Management Commands (Admin Only)

#### `/aura add <@user> <amount> [reason]`
**Award aura to a staff member** *(Administrator Only)*
```
/aura add @John 50 Great help with moderation today
/aura add @Alice 25 Excellent community engagement
```
**Limits:** 1-1000 aura per action

#### `/aura remove <@user> <amount> [reason]`
**Remove aura from a staff member** *(Administrator Only)*
```
/aura remove @John 10 Late to shift without notice
/aura remove @Alice 5 Minor policy violation
```
**Limits:** 1-1000 aura per action, cannot go below 0

#### `/aura set <@user> <amount> [reason]`
**Set a staff member's aura to exact amount** *(Administrator Only)*
```
/aura set @John 100 Promotion adjustment
/aura set @Alice 0 Starting fresh
```
**Limits:** 0-10000 aura total

---

## 🤖 Automatic Thanks System

### How It Works
When someone mentions or replies to a staff member and says "thanks", that staff member automatically gets **1 aura**!

### Trigger Word
The system detects the exact word: **`thanks`**

### How to Give Auto Aura
1. **Mention a staff member:** `@StaffMember thanks for the help!`
2. **Reply to a staff member:** Reply to their message with `thanks!`
3. **Multiple staff:** `@Staff1 @Staff2 thanks for helping!`

### What Happens
- Staff member gets +1 aura automatically
- Bot replies with "Added 1 aura to @StaffMember"
- Aura is logged as "Thanks from [username]"
- Only works for configured staff roles

### Examples
```
@ModeratorJohn thanks for helping with that issue!
# ✅ Bot replies: "Added 1 aura to @ModeratorJohn"

Reply to staff message: "thanks for the quick response!"
# ✅ Bot replies: "Added 1 aura to @StaffMember"

@Staff1 @Staff2 thanks for the help!  
# ✅ Both staff get +1 aura each

thank you for helping!
# ❌ No aura (must say exact word "thanks")
```

---

#### `/points reset <@user> [reason]`
**Reset a staff member's points to zero (with confirmation)**
```
/points reset @John End of probation period
```
**Requires confirmation - cannot be undone**

---

### 📜 History & Analytics (Moderator+)

#### `/points history [@user] [limit]`
**View detailed points activity history**
```
/points history @John      # John's last 10 activities
/points history @Alice 25  # Alice's last 25 activities (max 50)
```
**Shows:**
- Points changes with reasons
- Who made the changes
- Timestamps (Discord relative time)
- Action types (add/remove/set/reset)

---

### ⚙️ Configuration Commands (Admin Only)

#### `/points config channel <#channel>`
**Set channel for points activity logging**
```
/points config channel #staff-logs
/points config channel disable        # Disable logging
```

#### `/points config addrole <@role>`
**Add a role as "staff" for points eligibility**
```
/points config addrole @Moderator
/points config addrole @Helper
/points config addrole @Trial Staff
```

#### `/points config`
**View current configuration**
```
/points config            # Shows current settings
```

---

## 🎨 Visual Features

### 🏆 Leaderboard Design
- **Gold/Silver/Bronze medals** for top 3
- **Numbered rankings** for others
- **Points and total earned** display
- **Server statistics** summary
- **Beautiful embeds** with proper formatting

### 📊 Statistics Dashboard
- **Current points and rank**
- **Total earned/spent breakdown**
- **30-day activity summary**
- **Retention rate calculation**
- **Last activity tracking**

### 📝 Activity Logging
- **Color-coded embeds** (Green=add, Red=remove, Orange=reset)
- **Detailed information** (who, what, when, why)
- **Real-time updates** to configured channel
- **Professional formatting** for easy reading

---

## 🗄️ Database Structure

### Staff Points Table
- **User points tracking** (current, earned, spent)
- **Guild-specific data** (multi-server support)
- **Timestamp tracking** for last updates
- **Automatic initialization** for new users

### Points History Table
- **Complete audit trail** of all changes
- **Moderator tracking** (who made changes)
- **Detailed reasons** for transparency
- **Action type categorization**

### Configuration Table
- **Staff role management**
- **Channel settings**
- **Guild-specific configuration**
- **Future expansion ready**

---

## 🎯 Use Cases

### 👑 Staff Recognition
- **Daily performance rewards** (5-20 points)
- **Weekly achievements** (50-100 points)
- **Special contributions** (25-75 points)
- **Event participation** (10-30 points)

### 📈 Promotion System
- **Rank requirements** based on points
- **Performance tracking** over time
- **Objective promotion criteria**
- **Historical performance review**

### 🏅 Gamification
- **Healthy competition** between staff
- **Achievement milestones**
- **Seasonal competitions**
- **Recognition programs**

---

## 🔧 Administrative Features

### 🛡️ Safety Features
- **Confirmation prompts** for dangerous actions
- **Audit trails** for all changes
- **Permission checks** for all operations
- **Error handling** and validation

### 📊 Analytics
- **Server-wide statistics**
- **Individual performance metrics**
- **Activity trends tracking**
- **Retention analysis**

### ⚙️ Flexibility
- **Configurable staff roles**
- **Custom point amounts**
- **Detailed reason tracking**
- **Multi-server support**

---

## 💡 Best Practices

### 🎯 Point Distribution Guidelines
- **Small daily tasks:** 5-10 points
- **Medium contributions:** 15-25 points
- **Major achievements:** 50-100 points
- **Exceptional service:** 100+ points

### 📝 Reason Guidelines
- **Be specific and positive**
- **Reference specific actions**
- **Include context when needed**
- **Maintain professional tone**

### 🔄 Regular Maintenance
- **Review point distribution monthly**
- **Adjust criteria as needed**
- **Celebrate top performers**
- **Address any concerns promptly**

---

## 🚀 Getting Started

### 1. **Configure Staff Roles**
```
/points config addrole @Moderator
/points config addrole @Helper
```

### 2. **Set Logging Channel**
```
/points config channel #staff-logs
```

### 3. **Start Awarding Points**
```
/points add @Staff 25 Great work today!
```

### 4. **Check the Leaderboard**
```
/points leaderboard
```

---

## 🎉 Success!

Your staff points system is now ready to help recognize and reward your amazing staff team! Use it to build a positive, competitive environment that encourages excellence and recognizes outstanding contributions.

**Remember:** The goal is to create a positive, motivating environment where staff feel valued and recognized for their contributions to the community.
