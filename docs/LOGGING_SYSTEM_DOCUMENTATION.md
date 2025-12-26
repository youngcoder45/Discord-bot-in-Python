# 📋 Logging System Documentation

## Overview
The CodeVerse Bot features a comprehensive logging system that tracks all major server events, moderation actions, and member activities. All logs are stored in the database and can be sent to designated Discord channels for real-time monitoring.

---

## Table of Contents
1. [Setup & Configuration](#setup--configuration)
2. [Member Events](#member-events)
3. [Moderation Actions](#moderation-actions)
4. [Message Events](#message-events)
5. [Voice Events](#voice-events)
6. [Channel Events](#channel-events)
7. [Role Events](#role-events)
8. [Server Events](#server-events)
9. [Ticket Events](#ticket-events)
10. [Staff Activity](#staff-activity)
11. [Troubleshooting](#troubleshooting)

---

## Setup & Configuration

### Setting Up Log Channels
Use the `!setlogchannels` command to configure where logs are sent:

```
!setlogchannels #member-logs #mod-logs #ticket-logs
```

**Parameters:**
- `#member-logs` - Channel for member-related events (joins, leaves, role changes)
- `#mod-logs` - Channel for moderation actions (bans, kicks, timeouts, warnings)
- `#ticket-logs` - Channel for ticket system events

**View Current Configuration:**
```
!setlogchannels
```
This shows all currently configured log channels.

### Channel Types

#### Member Log Channel
Receives logs for:
- Member joins/leaves
- Role additions/removals
- Nickname changes
- Voice channel activity
- Avatar updates

#### Mod Log Channel
Receives logs for:
- Bans/unbans
- Kicks
- Timeouts/untimeouts
- Warnings
- Message deletions (by moderators)
- Channel/role modifications
- Server setting changes

#### Ticket Log Channel
Receives logs for:
- Ticket creation
- Ticket closure
- Ticket reopening
- Ticket claim/unclaim
- Ticket assignments

---

## Member Events

### JOIN
**Triggered:** When a member joins the server
**Details Logged:**
- Member ID
- Join timestamp
- Account creation date
- Current member count

**Example Log:**
```
Member Joined
User: @NewUser#1234
Joined At: 2024-01-15 10:30:45 UTC
Account Created: 2023-12-01
Total Members: 1,234
```

### LEAVE
**Triggered:** When a member leaves or is removed
**Details Logged:**
- Member ID
- Leave timestamp
- Roles they had
- Join date (how long they were in server)

**Example Log:**
```
Member Left
User: @User#5678
Left At: 2024-01-15 11:45:20 UTC
Roles: @Member, @Active, @Verified
Member Since: 2023-10-15 (3 months)
```

### ROLE_ADD
**Triggered:** When a role is added to a member
**Details Logged:**
- Member ID
- Role added (with mention)
- Moderator who added it (from audit logs)
- Timestamp

**Example Log:**
```
Role Added
User: @User#1234
Added Role: @Moderator
By: @Admin#0001
Time: 2024-01-15 12:00:00 UTC
```

### ROLE_REMOVE
**Triggered:** When a role is removed from a member
**Details Logged:**
- Member ID
- Role removed (with mention)
- Moderator who removed it (from audit logs)
- Timestamp

### NICKNAME_UPDATE
**Triggered:** When a member's nickname changes
**Details Logged:**
- Member ID
- Old nickname
- New nickname
- Timestamp

**Example Log:**
```
Nickname Changed
User: @User#1234
Old: CoolGuy
New: CoolerGuy
Time: 2024-01-15 13:30:00 UTC
```

---

## Moderation Actions

### BAN
**Triggered:** When a member is banned
**Details Logged:**
- User ID
- Moderator ID
- Ban reason
- Timestamp

**Example Log:**
```
Member Banned
User: @BadUser#9999
Banned By: @Moderator#0001
Reason: Spamming in multiple channels
Time: 2024-01-15 14:00:00 UTC
```

### UNBAN
**Triggered:** When a member is unbanned
**Details Logged:**
- User ID
- Moderator ID
- Unban reason
- Timestamp

### KICK
**Triggered:** When a member is kicked
**Details Logged:**
- User ID
- Moderator ID
- Kick reason
- Timestamp

### TIMEOUT_ADD
**Triggered:** When a member is timed out
**Details Logged:**
- User ID
- Moderator ID
- Timeout duration
- Timeout reason
- Until timestamp

**Example Log:**
```
Member Timed Out
User: @User#4567
Timed Out By: @Moderator#0001
Duration: 1 hour
Until: 2024-01-15 16:00:00 UTC
Reason: Inappropriate behavior
```

### TIMEOUT_REMOVED
**Triggered:** When a timeout is removed early
**Details Logged:**
- User ID
- Moderator ID
- Removal reason
- Original timeout end time

### WARN
**Triggered:** When a warning is issued
**Details Logged:**
- User ID
- Moderator ID
- Warning reason
- Case ID
- Total warnings

**Example Log:**
```
Warning Issued
User: @User#1111
Warned By: @Moderator#0001
Reason: Off-topic in #general
Case ID: #4567
Total Warnings: 2
```

### POINT_CHANGE
**Triggered:** When staff points are awarded/removed
**Details Logged:**
- Staff member ID
- Points changed (+/-)
- New total points
- Reason
- Moderator who changed points

---

## ~~Message Events~~ (DISABLED)

**Note:** Message logging has been removed. The bot no longer logs MESSAGE_EDIT, MESSAGE_DELETE, or MESSAGE_BULK_DELETE events.

---

## Voice Events

### VOICE_JOIN
**Triggered:** When a member joins a voice channel
**Details Logged:**
- Member ID
- Channel joined

### VOICE_LEAVE
**Triggered:** When a member leaves a voice channel
**Details Logged:**
- Member ID
- Channel left

### VOICE_MOVE
**Triggered:** When a member moves between voice channels
**Details Logged:**
- Member ID
- From channel
- To channel

### VOICE_MUTE
**Triggered:** When a member is server-muted
**Details Logged:**
- Member ID
- Channel
- Moderator (from audit logs)

### VOICE_UNMUTE
**Triggered:** When a member is server-unmuted
**Details Logged:**
- Member ID
- Channel
- Moderator (from audit logs)

### VOICE_DEAFEN
**Triggered:** When a member is server-deafened
**Details Logged:**
- Member ID
- Channel
- Moderator (from audit logs)

### VOICE_UNDEAFEN
**Triggered:** When a member is server-undeafened
**Details Logged:**
- Member ID
- Channel
- Moderator (from audit logs)

---

## Channel Events

### CHANNEL_CREATE
**Triggered:** When a new channel is created
**Details Logged:**
- Channel mention
- Channel type (Text/Voice/Announcement/etc.)
- Category
- Moderator who created it

**Example Log:**
```
Channel Created
Channel: #new-channel
Type: Text Channel
Category: General
Created By: @Admin#0001
```

### CHANNEL_DELETE
**Triggered:** When a channel is deleted
**Details Logged:**
- Channel name
- Channel type
- Category
- Moderator who deleted it

### CHANNEL_UPDATE
**Triggered:** When a channel is modified
**Details Logged:**
- Channel mention
- Changes (name, topic, etc.)
- Moderator who updated it

**Example Log:**
```
Channel Updated
Channel: #announcements
Changes:
- Name: #updates → #announcements
- Topic: "Server updates" → "Official server announcements"
Updated By: @Admin#0001
```

---

## Role Events

### ROLE_CREATE
**Triggered:** When a new role is created
**Details Logged:**
- Role mention
- Color
- Hoisted status
- Mentionable status
- Moderator who created it

**Example Log:**
```
Role Created
Role: @NewRole
Color: #FF5733
Hoisted: True
Mentionable: False
Created By: @Admin#0001
```

### ROLE_DELETE
**Triggered:** When a role is deleted
**Details Logged:**
- Role name
- Color
- Moderator who deleted it

### ROLE_UPDATE
**Triggered:** When a role is modified
**Details Logged:**
- Role mention
- Changes (name, color, permissions, etc.)
- Moderator who updated it

---

## Server Events

### GUILD_UPDATE
**Triggered:** When server settings are changed
**Details Logged:**
- Changes (name, icon, banner, description, verification level)
- Moderator who made changes

**Example Log:**
```
Server Updated
Changes:
- Name: "The Code Hub" → "The Codeverse Hub"
- Verification Level: Low → Medium
Updated By: @Owner#0001
```

### EMOJI_UPDATE
**Triggered:** When emojis are added/removed
**Details Logged:**
- Emojis added
- Emojis removed

**Example Log:**
```
Emojis Updated
Added: :custom_emoji: :another_emoji:
Removed: :old_emoji:
```

---

## Ticket Events

### TICKET_CREATE
**Triggered:** When a ticket is opened
**Details Logged:**
- User who created ticket
- Ticket thread ID
- Ticket type/category

### TICKET_CLOSE
**Triggered:** When a ticket is closed
**Details Logged:**
- Ticket thread ID
- Closed by (staff member)
- Close reason

### TICKET_REOPEN
**Triggered:** When a ticket is reopened
**Details Logged:**
- Ticket thread ID
- Reopened by
- Reopen reason

### TICKET_CLAIM
**Triggered:** When a staff member claims a ticket
**Details Logged:**
- Ticket thread ID
- Staff member who claimed

### TICKET_ASSIGN
**Triggered:** When a ticket is assigned to staff
**Details Logged:**
- Ticket thread ID
- Assigned staff member
- Assigned by

---

## Staff Activity

### STAFF_SHIFT_START
**Triggered:** When staff clocks in
**Details Logged:**
- Staff member ID
- Shift start time

### STAFF_SHIFT_END
**Triggered:** When staff clocks out
**Details Logged:**
- Staff member ID
- Shift end time
- Total shift duration

### STAFF_ACTIVITY
**Triggered:** Periodic activity tracking
**Details Logged:**
- Staff member ID
- Activity type
- Timestamp

---

## Troubleshooting

### Logs Not Appearing

**Check 1: Log Channels Configured?**
```
!setlogchannels
```
Verify channels are set correctly.

**Check 2: Bot Permissions**
Ensure bot has:
- Read Messages
- Send Messages
- Embed Links
- Read Message History
- View Audit Log (critical for moderator info)

**Check 3: Database Connection**
Check bot console for database errors.

### Missing Moderator Information

**Issue:** Logs show "Unknown Moderator"
**Cause:** Bot doesn't have "View Audit Log" permission
**Fix:** Grant bot "View Audit Log" permission

### Delayed Logs

**Normal Behavior:** Some logs may appear with 0.5-1 second delay
**Reason:** Bot waits for audit log entries to populate
**Note:** This is intentional to capture moderator information

### Duplicate Logs

**Possible Causes:**
1. Multiple bot instances running
2. Cog loaded multiple times
**Fix:** Restart bot, ensure single instance

### Old Events Not Logged

**Important:** The logging system only tracks events that occur AFTER the bot is online
**Note:** Historical events before bot startup are not retroactively logged

---

## Best Practices

### Channel Organization
- Keep log channels restricted to moderators only
- Use separate channels for different log types
- Consider using channel topics to indicate what's logged

### Monitoring
- Regularly check log channels
- Set up Discord pings/alerts for critical events (bans, kicks)
- Review logs during shift changes

### Privacy
- Protect log channels - they contain sensitive information
- Don't share logs publicly
- Use ticket logs to track support quality

### Performance
- Logs are processed asynchronously (won't slow down bot)
- Database automatically stores all logs
- Old logs can be queried from database if needed

---

## Database Schema

All logs are stored in the `logs` table:

```sql
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    user_id INTEGER,
    guild_id INTEGER NOT NULL,
    moderator_id INTEGER,
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**Querying Logs:**
```python
# Example: Get all bans by a moderator
cursor.execute('''
    SELECT * FROM logs 
    WHERE event_type = 'BAN' 
    AND moderator_id = ?
''', (moderator_id,))
```

---

## Summary

The logging system captures **40+ event types** across:
- ✅ Member activity (joins, leaves, role changes, nicknames)
- ✅ Moderation actions (bans, kicks, timeouts, warnings)
- ✅ Messages (edits, deletions, bulk purges)
- ✅ Voice activity (joins, leaves, moves, mute/deafen)
- ✅ Channels (create, delete, update)
- ✅ Roles (create, delete, update, member changes)
- ✅ Server settings (name, icon, verification level)
- ✅ Tickets (create, close, reopen, claim, assign)
- ✅ Staff management (shifts, points, activity)

All logs include timestamps, relevant user IDs, and detailed context to provide comprehensive server oversight.

---

**Need Help?** Contact the bot developer or check the bot console logs for technical errors.
