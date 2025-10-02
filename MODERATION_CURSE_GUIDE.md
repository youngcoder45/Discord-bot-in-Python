# 🔨 Moderation Curse System Guide

## Overview
The Moderation Curse System is an advanced, curse-point-based infraction tracking mechanism that automatically manages user behavior through a fair and transparent system. When users violate rules, they receive "curse points" - not achievements, but punishments. The system includes monthly resets, automatic bans at 100 curse points, and a 2-moderator approval system for unbans.

## 🎯 Key Features

### 1. **Curse Point-Based Infractions**
- Moderators add curse points to users for rule violations
- Curse range: 1-100
- Cap: 100 curse points (automatic ban when reached)
- **Monthly automatic reset** - Curse points reset to 0 at the start of each month

### 2. **Automatic Ban System**
- When a user reaches 100 curse points, they are **automatically banned**
- The system sends them a DM with:
  - Ban notification
  - Reason for ban
  - Instructions for requesting an unban

### 3. **2-Moderator Unban Approval**
- Unban requests require approval from **2 different moderators**
- Prevents abuse and ensures fair decisions
- Once approved, user is unbanned and curse is lifted (reset to 0)

### 4. **User Notifications (DMs)**
- Users receive DMs when:
  - They receive curse points
  - They approach 80+ curse points (warning)
  - They are banned at 100 curse points
  - Their unban request is approved and curse is lifted

### 5. **Complete History Tracking**
- All infractions are logged with timestamps
- Monthly infraction history available
- Tracks which moderator issued points

## 📋 Commands

### For Moderators

All curse commands are now grouped under `/curse` to save slash command slots!

#### `/curse add <member> <points> [reason]`
Add curse points to a user for rule violations.
- **Permission Required:** `Moderate Members`
- **Curse Range:** 1-100
- **Example:** `/curse add @User 15 Spamming in general chat`
- **Auto-ban:** If user reaches 100 curse points, they're automatically banned

#### `/curse view [member]`
View curse points for a user (or yourself).
- **Permission Required:** None (anyone can check their own curse)
- **Example:** `/curse view @User` or `/curse view`
- **Shows:**
  - Current curse points
  - Ban status
  - Recent curses/infractions (last 5)
  - Unban request status

#### `/curse remove <member>`
Remove all curse points from a user (reset to 0).
- **Permission Required:** `Administrator`
- **Example:** `/curse remove @User`
- **Use Case:** Forgive all infractions or administrative corrections

#### `/curse history <member>`
View complete curse history for a user.
- **Permission Required:** `Moderate Members`
- **Example:** `/curse history @User`
- **Shows:** Last 20 infractions with dates and reasons

#### `/curse leaderboard`
View top 10 most cursed users this month.
- **Permission Required:** None (anyone can view)
- **Example:** `/curse leaderboard`
- **Shows:** Rankings, curse points, and ban status

#### `/unbanrequest <user> <message>`
Submit an unban request on behalf of a banned user.
- **Permission Required:** `Moderate Members`
- **Example:** `/unbanrequest @BannedUser They apologized and promise to follow rules`
- **Note:** User must be currently banned

#### `/approveunban <user_id>`
Approve an unban request (requires 2 approvals total).
- **Permission Required:** `Moderate Members`
- **Example:** `/approveunban 123456789012345678`
- **Process:**
  - First moderator approval: Request is recorded (1/2)
  - Second moderator approval: User is unbanned automatically (2/2)
  - Cannot approve your own request twice
  - Requires 2 **different** moderators

#### `/pendingunbans`
View all pending unban requests.
- **Permission Required:** `Moderate Members`
- **Shows:**
  - User information
  - Unban request message
  - Current approval count (X/2)
  - Request timestamp

### Basic Moderation (Still Available)

#### `/purge <amount>`
Delete messages from the channel.
- **Permission Required:** `Manage Messages`

#### `/kick <member> [reason]`
Kick a member from the server.
- **Permission Required:** `Kick Members`

#### `/ban <member> [reason]`
Ban a member from the server.
- **Permission Required:** `Ban Members`

#### `/unban <user>`
Directly unban a user (bypasses approval system).
- **Permission Required:** `Ban Members`

## 🔄 How It Works

### Monthly Reset System
```
Current Month: 2025-10
- User receives curse points throughout October
- On November 1st, curse automatically resets to 0
- Infraction history is preserved for records
```

### Auto-Ban Flow
```
1. User receives curse points → Total reaches 100
2. System automatically bans the user
3. User receives DM:
   - "You've been banned for reaching 100 curse points"
   - "Contact a moderator to request unban"
4. Moderator can submit unban request on their behalf
```

### Unban Approval Flow
```
1. Moderator A: /unbanrequest @User "They've apologized"
   → Request created (0/2 approvals)

2. Moderator B: /approveunban 123456789
   → First approval recorded (1/2 approvals)

3. Moderator C: /approveunban 123456789
   → Second approval recorded (2/2 approvals)
   → User is automatically unbanned
   → Curse lifted (reset to 0)
   → User receives success DM
```

## 📊 Database Structure

### Tables Created
1. **`moderation_points`** - Main user curse tracking
2. **`infractions`** - Complete infraction/curse history
3. **`unban_approvals`** - Tracks moderator approvals

### Data Location
- Database: `data/moderation_points.db`
- Auto-created on first use
- Persistent across bot restarts

## 🎨 Curse Point Recommendation Guide

Suggested curse point values for common infractions:

| Infraction | Curse Points | Reasoning |
|-----------|-------------|-----------|
| Minor spam | 5-10 | First-time, small amount |
| Excessive spam | 15-25 | Repeated or disruptive |
| Inappropriate language | 10-15 | Mild profanity/rudeness |
| Harassment | 25-40 | Targeting users |
| Hate speech | 50-75 | Serious violation |
| NSFW content | 30-50 | Depending on severity |
| Raid participation | 75-100 | Immediate serious action |
| Advertising/Scams | 40-60 | Commercial spam |

**Note:** These are recommendations. Adjust based on your server's rules and severity.

## 🔒 Security & Fairness Features

### 1. **2-Moderator Approval**
- Prevents single moderator from having too much power
- Ensures community consensus on unbans
- Different moderators required (can't approve twice)

### 2. **Monthly Reset**
- Gives users fresh starts
- Prevents permanent "cursed records"
- Encourages long-term good behavior

### 3. **Transparent System**
- Users can check their own curse anytime
- All curses are logged and timestamped
- Complete infraction history available

### 4. **Automatic Notifications**
- Users are always informed about curse points received
- Warnings at 80+ curse points prevent surprises
- Clear instructions for appeal process

## 🚨 Important Notes

1. **Cannot curse bots** - System prevents this automatically
2. **Curse range: 1-100** - Cannot add negative curse points
3. **Monthly reset is automatic** - Curse lifted at start of month
4. **Ban at 100 is automatic** - Maximum curse triggers auto-ban
5. **Unban requires 2 moderators** - Cannot be bypassed (except with direct `/unban`)

## 🔧 Troubleshooting

### User didn't receive DM?
- User may have DMs disabled
- Bot logs will show "Cannot send DM" message
- Inform them manually through server channels

### How to check who approved an unban?
- Use `/pendingunbans` to see approval counts
- Check bot logs for moderator names

### Can we change the 100 curse point limit?
- Currently hardcoded to 100
- Contact bot developer to modify

### What happens to old curses/infractions?
- They're preserved in the database
- Can be viewed with `/viewcurse`
- Monthly reset only affects curse total, not history

## 📈 Best Practices

1. **Be Consistent:** Use similar curse values for similar infractions
2. **Warn First:** For minor first-time offenses, consider warnings before cursing
3. **Document Reasons:** Always provide clear reasons when adding curse
4. **Review Regularly:** Check `/pendingunbans` frequently
5. **Communicate:** Let your community know about the curse system

## 🎯 Success Tips

- **Post rules with curse values** so users know consequences
- **Train moderators** on consistent curse assignment
- **Use `/viewcurse`** before banning to see history
- **Be fair with unban approvals** - give genuine second chances
- **Monitor monthly resets** - announce curse lifts to community

---

**System Version:** 1.0  
**Last Updated:** October 2025  
**Database:** SQLite (`data/moderation_points.db`)  
**Compatible with:** Discord.py 2.0+
