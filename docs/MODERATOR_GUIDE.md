# CodeVerse Bot - Moderator Guide

**Last Updated:** December 26, 2025

## Introduction

Welcome to the CodeVerse Bot Moderator Guide! This bot is exclusively designed for **The Codeverse Hub** server and provides comprehensive moderation, management, and utility tools.

## Quick Start

### Command Prefixes
- **Prefix Commands:** Use `?` before command names (e.g., `?ban @user`)
- **Slash Commands:** Use `/` before command names (e.g., `/ban @user`)
- Both methods work identically for all commands

### Essential Permissions Required
To use moderation commands, you need:
- `Manage Messages` - Basic moderation access
- `Kick Members` - For kick commands
- `Ban Members` - For ban commands
- `Moderate Members` - For timeout/mute commands
- `Administrator` - For advanced configuration

---

## Core Moderation Commands

### Ban Management

#### `/ban` or `?ban`
**Permission Required:** Ban Members

Permanently ban a user from the server.

**Usage:**
```
/ban @username [reason]
?ban @username [reason]
```

**Examples:**
- `/ban @spammer Repeated spam after warnings`
- `?ban @rulebreaker Harassment in multiple channels`

**What happens:**
- User is immediately banned from the server
- Action is logged to the mod log channel
- Ban reason is recorded in audit log
- User cannot rejoin unless unbanned

---

#### `/unban` or `?unban`
**Permission Required:** Ban Members

Remove a ban from a user, allowing them to rejoin.

**Usage:**
```
/unban <user_id> [reason]
?unban <user_id> [reason]
```

**Examples:**
- `/unban 123456789012345678 Appeal approved`
- `?unban 123456789012345678 Ban duration completed`

**Note:** You need the user's ID since they're not in the server.

---

### Kick Management

#### `/kick` or `?kick`
**Permission Required:** Kick Members

Remove a user from the server (they can rejoin immediately).

**Usage:**
```
/kick @username [reason]
?kick @username [reason]
```

**Examples:**
- `/kick @troublemaker First offense warning`
- `?kick @inactive Inactive for 90 days`

**What happens:**
- User is removed from the server
- They can rejoin with an invite link
- Action is logged
- Useful for warnings without permanent bans

---

### Timeout/Mute Management

#### `/timeout` or `?timeout`
**Permission Required:** Moderate Members

Temporarily prevent a user from sending messages.

**Usage:**
```
/timeout @username <duration> [reason]
?timeout @username <duration> [reason]
```

**Duration Format:**
- `10m` - 10 minutes
- `2h` - 2 hours
- `1d` - 1 day
- `1w` - 1 week

**Examples:**
- `/timeout @user 30m Spamming in general`
- `?timeout @user 2h Inappropriate behavior`

**What happens:**
- User cannot send messages in any channel
- User cannot add reactions
- User cannot join voice channels
- Timeout expires automatically
- Action is logged with duration

---

#### `/untimeout` or `?untimeout`
**Permission Required:** Moderate Members

Remove timeout from a user early.

**Usage:**
```
/untimeout @username [reason]
?untimeout @username [reason]
```

**Examples:**
- `/untimeout @user Apologized and understood rules`
- `?untimeout @user Timeout too harsh`

---

### Warning System

#### `/warn` or `?warn`
**Permission Required:** Manage Messages

Issue an official warning to a user.

**Usage:**
```
/warn @username <reason>
?warn @username <reason>
```

**Examples:**
- `/warn @user Please keep discussions on-topic`
- `?warn @user No political discussions in general chat`

**What happens:**
- Warning is recorded in the database
- User receives a DM with the warning
- Warning appears in `/warnings` list
- Contributes to user's warning history
- Logged to mod channel

---

#### `/warnings` or `?warnings`
**Permission Required:** None

Show the server warnings leaderboard (top warned users).

**Usage:**
```
/warnings
?warnings
```

---

#### `/warnings view` or `?warnings view`
**Permission Required:** None

View all warnings for a specific user.

**Usage:**
```
/warnings view user:@username
?warnings view @username
```

**Example:**
- `/warnings view @user` - Shows all active and revoked warnings for the user

**Information Displayed:**
- Total active/revoked warnings
- Warning ID (Case #)
- Date issued
- Moderator who issued it
- Reason for warning
- Current status (active/revoked)

---

#### `/removewarn` or `?removewarn`
**Permission Required:** Manage Messages

Remove a warning from a user's record.

**Usage:**
```
/removewarn <case_id>
?removewarn <case_id>
```

**Examples:**
- `/removewarn 42` - Removes warning case #42
- `?removewarn 15` - Removes warning case #15

**When to use:**
- Warning was issued by mistake
- User has shown improvement
- Appeal was approved
- Punishment was too harsh

---

### Message Management

#### `/purge` or `?purge`
**Permission Required:** Manage Messages

Delete multiple messages at once.

**Usage:**
```
/purge <amount>
?purge <amount>
```

**Examples:**
- `/purge 50` - Deletes last 50 messages
- `?purge 10` - Deletes last 10 messages

**Limits:**
- Minimum: 1 message
- Maximum: 100 messages per command
- Cannot delete messages older than 14 days (Discord limitation)

**What happens:**
- Messages are permanently deleted
- Action is logged with count
- Bot's confirmation message auto-deletes after 5 seconds

---

#### `/clean` or `?clean`
**Permission Required:** Manage Messages

Delete bot messages and command invocations.

**Usage:**
```
/clean [amount]
?clean [amount]
```

**Examples:**
- `/clean` - Cleans last 100 messages (default)
- `?clean 50` - Cleans last 50 messages

**What it removes:**
- Bot's own messages
- Commands that triggered bot responses
- Useful for cleaning up clutter

---

### Channel Management

#### `/lock` or `?lock`
**Permission Required:** Manage Channels

Lock a channel to prevent members from sending messages.

**Usage:**
```
/lock [reason]
?lock [reason]
```

**Examples:**
- `/lock Emergency situation`
- `?lock Channel maintenance`

**What happens:**
- @everyone role loses Send Messages permission
- Moderators can still send messages
- Announcement posted in channel
- Action is logged

---

#### `/unlock` or `?unlock`
**Permission Required:** Manage Channels

Unlock a previously locked channel.

**Usage:**
```
/unlock [reason]
?unlock [reason]
```

**Examples:**
- `/unlock Situation resolved`
- `?unlock Maintenance complete`

**What happens:**
- @everyone role regains Send Messages permission
- Announcement posted in channel
- Action is logged

---

#### `/slowmode` or `?slowmode`
**Permission Required:** Manage Channels

Set a slowmode delay for the current channel.

**Usage:**
```
/slowmode <seconds>
?slowmode <seconds>
```

**Examples:**
- `/slowmode 5` - 5 seconds between messages
- `?slowmode 30` - 30 seconds between messages
- `/slowmode 0` - Disable slowmode

**Limits:**
- Minimum: 0 seconds (disabled)
- Maximum: 21600 seconds (6 hours)

---

### Advanced Moderation

#### `/lockdown` or `?lockdown`
**Permission Required:** Administrator

Lock ALL channels in the server at once.

**Usage:**
```
/lockdown [reason]
?lockdown [reason]
```

**Examples:**
- `/lockdown Raid in progress`
- `?lockdown Server-wide emergency`

**What happens:**
- All channels are locked simultaneously
- Moderators can still send messages
- Use only in emergencies
- Action is logged

---

#### `/unlockdown` or `?unlockdown`
**Permission Required:** Administrator

Unlock all previously locked channels.

**Usage:**
```
/unlockdown [reason]
?unlockdown [reason]
```

**Examples:**
- `/unlockdown Raid ended`
- `?unlockdown Emergency resolved`

---

## User Information Commands

#### `/info` or `?info`
**Permission Required:** None

Get detailed information about a user. (Renamed from `userinfo`; the old `userinfo` name still works as a prefix alias.)

**Usage:**
```
/info [@user]
?info [@user]
```

**Examples:**
- `/info @user` - Info about mentioned user
- `/info` - Info about yourself

**Information Shown:**
- Account creation date
- Server join date
- Current roles
- Warning history
- Permissions
- Account status

---

#### `/avatar` or `?avatar`
**Permission Required:** None

View a user's avatar in full size.

**Usage:**
```
/avatar [@user]
?avatar [@user]
```

---

## Staff Management

> ⚠️ The **Staff Points / Aura system** (`/staffpoints`, `/aura`) has been **removed** and is no longer loaded.
> Use the **Warning system** (`/warn`, `/warnings view`) and **Permit system** (`/permit`) for staff tooling instead.

---


---

## Ticket System

### For Users

Users can create tickets by clicking the "Create Ticket" button in the ticket panel.

### For Moderators

#### Ticket Categories
- **General Support** - General help and questions
- **Role Issues** - Role-related problems
- **Warn Appeals** - Appeal warnings or moderation actions
- **Partnership** - Partnership applications
- **Reports** - Report rule violations or users
- **Other Issues** - Everything else

#### Managing Tickets

**Close Ticket Button:**
- Click "🔒 Close Ticket" in any ticket thread
- Ticket is archived and marked as closed
- Transcript is generated immediately
- The channel remains visible for 24 hours before automatic deletion
- User is notified

**Claim Ticket Button:**
- Click "📌 Claim Ticket" to assign yourself
- Shows you're handling this ticket
- Your name appears in ticket info

#### Ticket Commands

##### `/ticket panel`
**Permission Required:** Administrator

Create a new ticket panel in a channel.

**Usage:**
```
/ticket panel [channel] [support_role] [report_role] [partner_role] [color]
```

**Example:**
```
/ticket panel channel:#tickets support_role:@Support report_role:@Moderator
```

---

##### `/ticket list`
**Permission Required:** Manage Messages

View all tickets, optionally filtered.

**Usage:**
```
/ticket list [status] [user]
?ticket list [status] [user]
```

**Status Options:**
- `open` - Only open tickets
- `closed` - Only closed tickets
- `all` - All tickets (default)

**Examples:**
- `/ticket list` - View all tickets
- `/ticket list open` - View only open tickets
- `/ticket list closed @user` - View user's closed tickets

---

##### `/ticket stats`
**Permission Required:** Manage Messages

View statistics about the ticket system.

**Usage:**
```
/ticket stats
?ticket stats
```

**Shows:**
- Total tickets created
- Open tickets
- Closed tickets
- Tickets by category

---

##### `/ticket forceclose`
**Permission Required:** Manage Messages

Force close a ticket by ID.

**Usage:**
```
/ticket forceclose <ticket_id> [reason]
?forceclose <ticket_id> [reason]
```

**Example:**
```
/ticket forceclose 42 User not responding
```

---

## Best Practices

### When to Use Each Command

**Warning → Timeout → Kick → Ban** (Escalation order)

1. **First Offense:** Use `/warn` for minor violations
2. **Second Offense:** Use `/timeout` for repeated violations
3. **Third Offense:** Use `/kick` for serious violations
4. **Persistent Issues:** Use `/ban` for repeated serious violations

### Always Include Reasons
- Helps track moderation history
- Transparent for appeals
- Shows in audit logs
- Required for serious actions

### Communication
- Be professional and clear
- Explain the rule that was broken
- Tell users how to avoid future issues
- Direct serious issues to tickets

### Documentation
- Check user's warning history before actions
- Review ticket history for context
- Use `/info` before major actions
- Keep mod team informed

---

## Emergency Procedures

### Raid Response
1. `/lockdown` - Lock all channels immediately
2. Enable verification if needed
3. `/ban` raiders as identified
4. `/unlockdown` when situation is under control

### Spam Attack
1. `/lock` affected channel
2. `/purge` spam messages
3. `/timeout` or `/ban` spammer
4. `/unlock` channel

### Inappropriate Content
1. Delete messages immediately
2. `/timeout` user while investigating
3. `/ban` if content is severe (NSFW, illegal, harassment)
4. Report to Discord if needed

---

## Getting Help

### For Moderators
- Use ticket system for moderation discussions
- Contact senior moderators for guidance
- Check `/help` for command documentation
- Review user warnings before major actions

### Support Channels
- **Mod Chat:** Internal discussions
- **Tickets:** Complex issues or appeals
- **Appeals System:** For users appealing punishments

---

## Appendix

### Command Summary Table

| Command | Permission | Purpose |
|---------|-----------|---------|
| `/ban` | Ban Members | Permanently ban user |
| `/unban` | Ban Members | Remove ban |
| `/kick` | Kick Members | Remove user temporarily |
| `/timeout` | Moderate Members | Mute user temporarily |
| `/warn` | Manage Messages | Issue warning |
| `/purge` | Manage Messages | Delete messages |
| `/lock` | Manage Channels | Lock channel |
| `/slowmode` | Manage Channels | Set message delay |

### Quick Reference
- **Prefix:** `?` or `/`
- **Help Command:** `/help` or `?help`
- **Check Warnings:** `/warnings view @user`
- **View Tickets:** `/ticket list`
- **Permits:** `/permit check-all`
- **Warnings:** `/warnings view @user`

---

## Updates and Changes

This guide is maintained alongside bot updates. Check the bot's changelog for new features and command changes.

**Bot Version:** Latest
**Documentation Version:** 1.0
**Last Updated:** December 26, 2025
