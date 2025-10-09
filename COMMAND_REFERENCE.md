# CodeVerse Bot - Command Reference

This document provides a comprehensive list of all commands available in the CodeVerse Bot, organized by category with locations of the source files.

## Table of Contents
- [Core Commands](#core-commands)
- [Moderation Commands](#moderation-commands)
  - [Basic Moderation & Server Information](#basic-moderation--server-information)
  - [Advanced Moderation](#advanced-moderation)
- [Staff Management](#staff-management)
  - [Staff Shifts](#staff-shifts)
  - [Staff Points (Aura)](#staff-points-aura)
- [Utility](#utility)
  - [AFK System](#afk-system)
  - [Embed Builder](#embed-builder)
  - [Data Management](#data-management)
- [Diagnostics](#diagnostics)

---

## Core Commands
**Source:** `src/commands/core.py`

| Command | Description | Usage |
|---------|-------------|-------|
| `/help`, `?help` | Interactive help menu with dropdown categories | `/help [command]` |
| `/ping`, `?ping` | Check bot latency and responsiveness | `/ping` |
| `/info`, `?info` | View bot information, uptime, and instance details | `/info` |

---

## Moderation Commands

### Basic Moderation & Server Information
**Source:** `src/commands/modcog.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/purge`, `?purge` | Delete messages from a channel | `/purge <amount> [@user]` | Manage Messages |
| `/kick`, `?kick` | Kick a member from the server | `/kick <member> [reason]` | Kick Members |
| `/ban`, `?ban` | Ban a member from the server | `/ban <member> [days] [reason]` | Ban Members |
| `/unban`, `?unban` | Unban a previously banned user | `/unban <user_id> [reason]` | Ban Members |
| `/softban`, `?softban` | Kick user and delete their messages | `/softban <member> [reason]` | Ban Members |
| `/clean`, `?clean` | Delete bot messages and commands | `/clean [count=100]` | Manage Messages |
| `/role`, `?role` | Toggle a role for a user | `/role <user> <role_name>` | Manage Roles |
| `/serverinfo`, `?serverinfo` | Get detailed server information | `/serverinfo` | None |
| `/warnings add`, `?warnings add` | Add a warning to a user | `/warnings add <user> [reason]` | Kick Members |
| `/warnings remove`, `?warnings remove` | Remove a warning from a user | `/warnings remove <user> <case_id> [reason]` | Kick Members |
| `/warnings list`, `?warnings list` | List warnings for a user | `/warnings list <user>` | Kick Members |
| `/warnings clear`, `?warnings clear` | Clear all warnings for a user | `/warnings clear <user> [reason]` | Kick Members |
| `/warnings view`, `?warnings view` | View details of a specific warning | `/warnings view <case_id>` | Kick Members |

### Advanced Moderation
**Source:** `src/commands/advanced_moderation.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/serverinfo`, `?serverinfo` | Get detailed server information | `/serverinfo` | None |
| `/userinfo`, `?userinfo` | Get detailed user information | `/userinfo [@user]` | None |
| `/roleinfo`, `?roleinfo` | Get information about a role | `/roleinfo <role>` | None |
| `/lockdown`, `?lockdown` | Restrict sending messages in a channel | `/lockdown [#channel] [reason]` | Manage Channels |
| `/unlock`, `?unlock` | Remove sending restrictions from a channel | `/unlock [#channel] [reason]` | Manage Channels |
| `/slowmode`, `?slowmode` | Set channel slowmode (rate limit) | `/slowmode <seconds> [#channel]` | Manage Channels |
| `/nuke`, `?nuke` | Clone and replace a channel (deletes all messages) | `/nuke [#channel] [reason]` | Manage Channels |
| `/tempban`, `?tempban` | Temporarily ban a member | `/tempban <member> <minutes> [reason]` | Ban Members |
| `/mute`, `?mute` | Timeout a member temporarily | `/mute <member> <minutes> [reason]` | Moderate Members |
| `/unmute`, `?unmute` | Remove timeout from a member | `/unmute <member>` | Moderate Members |
| `/automod`, `?automod` | Configure automatic moderation settings | `/automod <feature> <enable/disable>` | Administrator |
| `/massban`, `?massban` | Ban multiple users at once | `/massban <user_ids> [reason]` | Ban Members |

*Note: Point Moderation system has been removed.*

### Appeals System
**Source:** `src/commands/appeals.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/appeals`, `?appeals` | View appeal requests | `/appeals [status]` | Administrator |
| `/approve`, `?approve` | Approve unban appeal | `/approve <id> [reason]` | Administrator |
| `/deny`, `?deny` | Deny unban appeal | `/deny <id> <reason>` | Administrator |
| `/appealinfo`, `?appealinfo` | Get detailed appeal info | `/appealinfo <id>` | Administrator |

*Note: SAM module warning system has been integrated into the ModCog system.*

---

## Staff Management

### Staff Shifts
**Source:** `src/commands/staff_shifts.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/shift start`, `?shift start` | Start staff shift | `/shift start [note]` | Staff Role |
| `/shift end`, `?shift end` | End staff shift | `/shift end [note]` | Staff Role |
| `/shift pause`, `?shift pause` | Pause staff shift | `/shift pause [reason]` | Staff Role |
| `/shift resume`, `?shift resume` | Resume paused shift | `/shift resume` | Staff Role |
| `/shift admin active`, `?shift admin active` | View active shifts | `/shift admin active` | Administrator |
| `/shift admin stats`, `?shift admin stats` | View statistics | `/shift admin stats [user]` | Administrator |

### Staff Points (Aura)
**Source:** `src/commands/staff_points.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/aura check`, `?aura check` | Check aura balance | `/aura check [@user]` | None |
| `/aura leaderboard`, `?aura leaderboard` | View staff rankings | `/aura leaderboard` | None |
| `/aura top`, `?aura top` | Quick top 3 view | `/aura top` | None |
| `/aura add`, `?aura add` | Award aura points | `/aura add <@user> <amount> [reason]` | Administrator |
| `/aura stats`, `?aura stats` | Detailed statistics | `/aura stats [@user]` | None |

---

## Utility

### AFK System
**Source:** `src/commands/afk.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/afk`, `?afk` | Set yourself as AFK | `/afk [reason]` | None |
| `/unafk`, `?unafk` | Remove AFK status | `/unafk` | None |
| `/afklist`, `?afklist` | List all AFK users | `/afklist` | None |

### Embed Builder
**Source:** `src/commands/utility.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/embed`, `?embed` | Interactive embed creator | `/embed` | Manage Messages |
| `/editembed`, `?editembed` | Edit existing embeds | `/editembed <message_id>` | Manage Messages |
| `/embedquick`, `?embedquick` | Quick embed creation | `/embedquick <title> <description> [color]` | Manage Messages |

### Data Management
**Source:** `src/commands/data_management.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/data backup`, `?data backup` | Create immediate backup | `/data backup` | Administrator |
| `/data restore`, `?data restore` | Restore data from backup | `/data restore` | Administrator |
| `/data status`, `?data status` | Show backup status | `/data status` | Administrator |
| `/data export`, `?data export` | Export data as file | `/data export` | Administrator |

---

## Diagnostics
**Source:** `src/commands/diagnostics.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/diag`, `?diag` | Comprehensive bot diagnostics | `/diag` | None |

---

## Protection Systems
**Source:** `src/commands/protection.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/antispam`, `?antispam` | Anti-spam protection settings | `/antispam <status>` | Administrator |
| `/antiraid`, `?antiraid` | Configure anti-raid protection | `/antiraid <status>` | Administrator |
| `/antinuke`, `?antinuke` | Server anti-nuke protection | `/antinuke <status>` | Administrator |

---

## File Structure Overview

```
src/
├── bot.py                                # Main bot file
├── commands/
│   ├── advanced_moderation.py            # Advanced moderation features
│   ├── afk.py                            # AFK system
│   ├── appeals.py                        # Appeal system for bans and mutes
│   ├── core.py                           # Core commands (ping, info, help)
│   ├── data_management.py                # Data backup and management
│   ├── diagnostics.py                    # Bot diagnostics
│   ├── moderation.py                     # Basic moderation commands
│   ├── moderation_extended.py            # Extended moderation commands
│   ├── point_moderation.py               # Point-based moderation system
│   ├── protection.py                     # Anti-spam, anti-raid, anti-nuke
│   ├── staff_points.py                   # Staff aura system
│   ├── staff_shifts.py                   # Staff shift tracking
│   ├── utility.py                        # Embed builder
│   └── modules/
│       └── sam/                          # Staff Activity Management
│           ├── bridge.py                 # Bridge to connect SAM logging to bot
│           ├── features/
│           │   └── warnings/             # Warning system
│           │       ├── cogs.py           # Warning commands
│           │       ├── models.py         # Database models
│           │       ├── repositories.py   # Database repositories
│           │       └── services.py       # Business logic
│           ├── internal/                 # Internal SAM functionality
│           └── public/                   # Public APIs for other modules
├── events/
│   ├── member_events.py                  # Member join/leave handlers
│   └── message_handler.py                # Message event handlers
└── utils/                                # Utility functions and helpers
```

## Configuration

The bot uses environment variables for configuration. Copy `.env.example` to `.env` and fill in the values:

```
DISCORD_TOKEN=your_token_here
GUILD_ID=your_guild_id
SERVER_LOGS_CHANNEL_ID=your_log_channel_id
```

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Configure your `.env` file
3. Run the bot: `python main.py`

---

Made with ❤️ for CodeVerse