# Centralized Logging System

This document describes the centralized logging system implemented for the CodeVerse Bot.

## Overview

The logging system centralizes all event logging for the Discord bot to ensure consistent format and storage of logs. It handles:

1. Member events (join, leave, ban, unban)
2. Moderation actions (warn, timeout, kick)
3. Role updates
4. Point system changes
5. Appeal system actions

All logs are:
- Stored in a SQLite database
- Sent to appropriate Discord channels based on log type

## Channels

The system uses two designated logging channels:
- **Member Logs Channel** (ID: 1263434413581008956): For member-related events like joins, leaves, role changes
- **Moderation Logs Channel** (ID: 1399746928585085068): For moderation actions like bans, kicks, warnings

## Usage

### Direct Usage

To log events directly from a cog:

```python
# Get the logging cog
logging_cog = self.bot.get_cog('LoggingCog')

# Log an event
await logging_cog.log_event(
    event_type="CUSTOM_EVENT",
    user_id=user.id,
    guild_id=guild.id,
    moderator_id=moderator.id,
    details="Details about the event",
    # Additional data as needed
    custom_field="Custom value"
)
```

### Specific Logging Methods

For common events, specialized methods are provided:

```python
# Log moderation action
await logging_cog.log_mod_action(
    action_type="MUTE",
    user_id=user.id,
    guild_id=guild.id,
    moderator_id=moderator.id,
    reason="User was spamming"
)

# Log warning
await logging_cog.log_warning(
    user_id=user.id,
    guild_id=guild.id,
    moderator_id=moderator.id,
    reason="First warning for rule violation",
    case_id=1
)

# Log point changes
await logging_cog.log_points(
    user_id=user.id,
    guild_id=guild.id,
    moderator_id=moderator.id,
    points=5,
    total=10,
    reason="Helpful contribution"
)

# Log appeal actions
await logging_cog.log_appeal(
    appeal_type="CREATED",
    user_id=user.id,
    guild_id=guild.id,
    moderator_id=moderator.id,
    appeal_id=1,
    details="Appeal for ban"
)
```

### Legacy Usage (Helpers)

For backward compatibility, you can still use the helper function:

```python
from utils.helpers import log_action

await log_action(
    "CUSTOM_EVENT", 
    user_id,
    "Details about the event",
    guild_id=guild.id,
    moderator_id=moderator.id
)
```

## Database Structure

Logs are stored in the `bot_logs` table with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | TEXT | ISO format timestamp |
| event_type | TEXT | Type of event (e.g., BAN, WARN) |
| guild_id | INTEGER | Discord guild ID |
| user_id | INTEGER | Target user ID |
| moderator_id | INTEGER | Moderator user ID (if applicable) |
| channel_id | INTEGER | Related channel ID (if applicable) |
| details | TEXT | Additional details/reason |
| sent_to_discord | BOOLEAN | Whether log was sent to Discord |

## Event Types

Common event types include:

- `MEMBER_JOIN`: Member joined the server
- `MEMBER_LEAVE`: Member left the server
- `BAN`: Member banned
- `UNBAN`: Member unbanned
- `KICK`: Member kicked
- `TIMEOUT`: Member timed out
- `TIMEOUT_REMOVE`: Member timeout removed
- `WARN`: Member warned
- `ROLE_UPDATE`: Member roles changed
- `POINT_CHANGE`: Staff points changed
- `APPEAL_CREATED`: Appeal created
- `APPEAL_APPROVED`: Appeal approved
- `APPEAL_REJECTED`: Appeal rejected

Custom event types can be created as needed.