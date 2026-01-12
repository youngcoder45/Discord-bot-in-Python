# CodeVerse Bot - Complete Command List

**Last Updated:** December 26, 2025

Complete reference of all bot commands organized by category.

---

## Table of Contents
- [Core Commands](#core-commands)
- [Moderation Commands](#moderation-commands)
- [Advanced Moderation](#advanced-moderation)
- [Warning System](#warning-system)
- [Ticket System](#ticket-system)
- [Staff Management](#staff-management)
- [Channel Management](#channel-management)
- [Message Management](#message-management)
- [User Information](#user-information)
- [Utility Commands](#utility-commands)
- [Thread Management](#thread-management)
- [AFK System](#afk-system)

---

## Core Commands

### `/help` • `?help`
**Permission:** None  
**Description:** Display the interactive help menu with all command categories.

**Usage:**
```
/help
/help <command_name>
?help
?help <command_name>
```

**Examples:**
- `/help` - Show main help menu
- `/help ban` - Show detailed help for ban command

---

### `/ping` • `?ping`
**Permission:** None  
**Description:** Check bot latency and responsiveness.

**Usage:**
```
/ping
?ping
```

**Response:** Shows WebSocket latency in milliseconds.

---

### `/info` • `?info`
**Permission:** None  
**Description:** Get detailed information about a user or yourself.

**Usage:**
```
/info [@user]
?info [@user]
```

**Shows:**
- Account creation date
- Server join date
- Warning history
- Permissions
- Staff status
- Dangerous user flags

---

## Moderation Commands

### `/ban` • `?ban`
**Permission:** Ban Members  
**Description:** Permanently ban a user from the server.

**Usage:**
```
/ban <@user> [reason]
?ban <@user> [reason]
```

**Parameters:**
- `@user` - The user to ban (required)
- `reason` - Reason for ban (optional but recommended)

**Example:**
```
/ban @spammer Repeated spam after multiple warnings
```

---

### `/unban` • `?unban`
**Permission:** Ban Members  
**Description:** Remove a ban from a user.

**Usage:**
```
/unban <user_id> [reason]
?unban <user_id> [reason]
```

**Parameters:**
- `user_id` - Discord ID of banned user (required)
- `reason` - Reason for unban (optional)

**Example:**
```
/unban 123456789012345678 Appeal approved
```

---

### `/kick` • `?kick`
**Permission:** Kick Members  
**Description:** Remove a user from the server (they can rejoin).

**Usage:**
```
/kick <@user> [reason]
?kick <@user> [reason]
```

**Example:**
```
/kick @troublemaker First offense warning
```

---

### `/timeout` • `?timeout`
**Permission:** Moderate Members  
**Description:** Temporarily mute a user for a specified duration.

**Usage:**
```
/timeout <@user> <duration> [reason]
?timeout <@user> <duration> [reason]
```

**Duration Format:**
- `m` - Minutes (e.g., `30m`)
- `h` - Hours (e.g., `2h`)
- `d` - Days (e.g., `7d`)
- `w` - Weeks (e.g., `1w`)

**Examples:**
```
/timeout @user 30m Spamming
/timeout @user 2h Inappropriate behavior
/timeout @user 1d Repeated violations
```

---

### `/untimeout` • `?untimeout`
**Permission:** Moderate Members  
**Description:** Remove timeout from a user early.

**Usage:**
```
/untimeout <@user> [reason]
?untimeout <@user> [reason]
```

**Example:**
```
/untimeout @user Apologized and understood rules
```

---

### `/softban` • `?softban`
**Permission:** Ban Members  
**Description:** Ban then immediately unban to delete user's messages.

**Usage:**
```
/softban <@user> [reason]
?softban <@user> [reason]
```

**Use Case:** Clean up spam without permanent ban.

---

### `/nickname` • `?nickname`
**Permission:** Manage Nicknames  
**Description:** Change a member's nickname.

**Usage:**
```
/nickname <@user> <new_nickname>
?nickname <@user> <new_nickname>
```

**Example:**
```
/nickname @user Appropriate Name
```

---

## Advanced Moderation

### `/lockdown` • `?lockdown`
**Permission:** Administrator  
**Description:** Lock ALL channels in the server simultaneously.

**Usage:**
```
/lockdown [reason]
?lockdown [reason]
```

**When to use:** Server-wide emergencies, raids

**Example:**
```
/lockdown Raid in progress
```

---

### `/unlockdown` • `?unlockdown`
**Permission:** Administrator  
**Description:** Unlock all locked channels.

**Usage:**
```
/unlockdown [reason]
?unlockdown [reason]
```

---

### `/massban` • `?massban`
**Permission:** Server Owner  
**Description:** Ban multiple users by ID at once.

**Usage:**
```
/massban <user_id1> <user_id2> <user_id3> ... [reason]
?massban <user_id1> <user_id2> <user_id3> ... [reason]
```

**Example:**
```
/massban 123456 789012 345678 Raid bots
```

---

### `/nuke` • `?nuke`
**Permission:** Server Owner  
**Description:** Clone and delete a channel to clear all messages.

**Usage:**
```
/nuke [reason]
?nuke [reason]
```

**Warning:** Deletes entire channel history permanently.

---

## Warning System

### `/warn` • `?warn`
**Permission:** Manage Messages  
**Description:** Issue an official warning to a user.

**Usage:**
```
/warn <@user> <reason>
?warn <@user> <reason>
```

**Example:**
```
/warn @user Please stay on topic in general chat
```

**What happens:**
- User receives DM notification
- Warning saved to database
- Logged to mod channel
- Shows in warning history

---

### `/warnings` • `?warnings`
**Permission:** Manage Messages  
**Description:** View all warnings for a user.

**Usage:**
```
/warnings <@user>
?warnings <@user>
```

**Shows:**
- Case ID
- Date issued
- Moderator
- Reason
- Current status

---

### `/removewarn` • `?removewarn`
**Permission:** Manage Messages  
**Description:** Remove a warning by case ID.

**Usage:**
```
/removewarn <case_id>
?removewarn <case_id>
```

**Example:**
```
/removewarn 42
```

---

## Ticket System

### `/ticketpanel`
**Permission:** Administrator  
**Description:** Create a ticket panel in a channel.

**Usage:**
```
/ticketpanel [channel] [support_role] [report_role] [partner_role]
```

**Example:**
```
/ticketpanel channel:#support support_role:@Support
```

---

### `/tickets`
**Permission:** Manage Messages  
**Description:** View and filter all tickets.

**Usage:**
```
/tickets [status] [user]
?tickets [status] [user]
```

**Status Options:** `open`, `closed`, `all`

**Examples:**
```
/tickets open
/tickets closed @user
```

---

### `/ticketstats`
**Permission:** Manage Messages  
**Description:** View ticket system statistics.

**Usage:**
```
/ticketstats
?ticketstats
```

---

### `/forceclose`
**Permission:** Manage Messages  
**Description:** Force close a ticket by ID.

**Usage:**
```
/forceclose <ticket_id> [reason]
?forceclose <ticket_id> [reason]
```

---

### `/ticketlog`
**Permission:** Administrator  
**Description:** Set or view ticket log channel.

**Usage:**
```
/ticketlog [channel]
?ticketlog [channel]
```

---

### `/ticketsupport`
**Permission:** Administrator  
**Description:** Set support team role for tickets.

**Usage:**
```
/ticketsupport [role]
?ticketsupport [role]
```

---

## Staff Management

### `/staffpoints` • `?staffpoints`
**Permission:** Manage Messages (to view others)  
**Description:** View staff points leaderboard or specific user.

**Usage:**
```
/staffpoints [@user]
?staffpoints [@user]
```

**How it works:**
- Staff gain points when thanked
- Keywords: "thanks", "thank you", "ty"
- Leaderboard tracks top helpers

---



---

## Channel Management

### `/lock` • `?lock`
**Permission:** Manage Channels  
**Description:** Lock a channel to prevent messages.

**Usage:**
```
/lock [reason]
?lock [reason]
```

**Example:**
```
/lock Cleaning up spam
```

---

### `/unlock` • `?unlock`
**Permission:** Manage Channels  
**Description:** Unlock a locked channel.

**Usage:**
```
/unlock [reason]
?unlock [reason]
```

---

### `/slowmode` • `?slowmode`
**Permission:** Manage Channels  
**Description:** Set slowmode delay.

**Usage:**
```
/slowmode <seconds>
?slowmode <seconds>
```

**Range:** 0-21600 seconds (0 to disable)

**Examples:**
```
/slowmode 5 - 5 second delay
/slowmode 0 - Disable slowmode
```

---

## Message Management

### `/purge` • `?purge`
**Permission:** Manage Messages  
**Description:** Delete multiple messages at once.

**Usage:**
```
/purge <amount>
?purge <amount>
```

**Range:** 1-100 messages

**Example:**
```
/purge 50
```

---

### `/clean` • `?clean`
**Permission:** Manage Messages  
**Description:** Delete bot messages and command invocations.

**Usage:**
```
/clean [amount]
?clean [amount]
```

**Default:** 100 messages

---

## User Information

### `/userinfo` • `?userinfo`
**Permission:** None  
**Description:** Get detailed user information.

**Usage:**
```
/userinfo [@user]
?userinfo [@user]
```

**Shows:**
- Account creation
- Server join date
- Roles
- Permissions
- Status

---

### `/avatar` • `?avatar`
**Permission:** None  
**Description:** View user's avatar in full size.

**Usage:**
```
/avatar [@user]
?avatar [@user]
```

---

### `/serverinfo` • `?serverinfo`
**Permission:** None  
**Description:** Get detailed server information.

**Usage:**
```
/serverinfo
?serverinfo
```

**Shows:**
- Server creation date
- Member count
- Channel count
- Role count
- Server owner
- Boost status

---

### `/roleinfo` • `?roleinfo`
**Permission:** None  
**Description:** Get information about a role.

**Usage:**
```
/roleinfo <@role>
?roleinfo <@role>
```

---

## Utility Commands

### `/embed` • `?embed`
**Permission:** Manage Messages  
**Description:** Create a professional embed with popup form.

**Usage:**
```
/embed
?embed
```

**Interactive form for:**
- Title
- Description
- Color
- Footer
- Images

---

### `/editembed` • `?editembed`
**Permission:** Manage Messages  
**Description:** Edit an existing bot embed.

**Usage:**
```
/editembed <message_id>
?editembed <message_id>
```

---

### `/embedquick` • `?embedquick`
**Permission:** Manage Messages  
**Description:** Quick embed creation via command.

**Usage:**
```
/embedquick <title> <description> [color]
?embedquick <title> <description> [color]
```

---

### `?ls`
**Permission:** None (Public)
**Description:** Advanced role listing and permission auditing tool. (Prefix only)

**Usage:**
```
?ls role <@role/ID>
?ls perm <PermissionName>
?ls perms
?ls noperms
```

**Subcommands:**
- **`role`**: View detailed info, key permissions, and raw stats for a role.
- **`perm`**: List all roles that have a specific permission (e.g., `ManageMessages`).
- **`perms`**: List all functional roles (roles with >0 permissions).
- **`noperms`**: List cosmetic roles (roles with 0 permissions).

**Examples:**
- `?ls role @Admin` - Inspect Admin role
- `?ls perm AddReactions` - See who can add reactions
- `?ls perm Administrator` - Find all admin roles

---

## Thread Management

### `/close` • `?close`
**Permission:** Manage Threads  
**Description:** Close/archive a thread.

**Usage:**
```
/close [reason]
?close [reason]
```

---

### `/pin` • `?pin`
**Permission:** Manage Messages  
**Description:** Pin a message in thread or channel.

**Usage:**
```
/pin [message_id]
?pin [message_id]
```

**Note:** Reply to message or provide ID

---

### `/unpin` • `?unpin`
**Permission:** Manage Messages  
**Description:** Unpin a message.

**Usage:**
```
/unpin [message_id]
?unpin [message_id]
```

---

## AFK System

### `/afk` • `?afk`
**Permission:** None  
**Description:** Set yourself as away from keyboard.

**Usage:**
```
/afk [reason]
?afk [reason]
```

**Example:**
```
/afk Going to sleep
```

**What happens:**
- Status shown when mentioned
- Auto-return when you send message
- Reason displayed to others

---

### `/afklist` • `?afklist`
**Permission:** None  
**Description:** List all AFK users in server.

**Usage:**
```
/afklist
?afklist
```

---

## Owner-Only Commands

### `?sync`
**Permission:** Bot Owner  
**Description:** Sync slash commands globally.

**Usage:**
```
?sync
```

---

### `?load`
**Permission:** Bot Owner  
**Description:** Load or reload a cog.

**Usage:**
```
?load <cog_name>
```

**Examples:**
```
?load help
?load tickets
?load mod
```

---

## Command Permissions Quick Reference

| Permission Level | Commands Available |
|-----------------|-------------------|
| **None** | help, ping, info, userinfo, avatar, serverinfo, afk |
| **Manage Messages** | warn, warnings, purge, clean, embed, pin, unpin |
| **Kick Members** | kick |
| **Ban Members** | ban, unban, softban |
| **Moderate Members** | timeout, untimeout |
| **Manage Channels** | lock, unlock, slowmode |
| **Administrator** | lockdown, unlockdown, ticketpanel, data commands |
| **Server Owner** | massban, nuke |
| **Bot Owner** | sync, load |

---

## Need Help?

Use `/help` for interactive command help or create a ticket for support!

**Last Updated:** December 26, 2025
