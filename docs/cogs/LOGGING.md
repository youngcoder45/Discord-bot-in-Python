# Logging System Cog

## Overview
The `LoggingCog` provides a centralized system for logging server events to Discord channels. It handles a wide variety of events including member changes, moderation actions, voice activity, and server modifications. It uses a queue-based system to process logs asynchronously and avoid blocking the bot's main loop.

## Architecture
- **Queue System**: Uses `asyncio.Queue` to buffer log events.
- **Database**: Stores log configuration and history in `bot_logs` and `guild_log_channels` tables.
- **Routing**: Automatically routes different event types to specific log channels (Message, Member, Server, Ticket, Mod, Other).

## Configure Logging Channels
The logging channels are stored in the database. Defaults are set for the main server.
- **Command**: `!setlogchannels` (Admin only)
- **Usage**: (Code reference suggests existence, check implementation for arguments)
- **Automatic Setup**: The code includes auto-configuration for "The CodeVerse Hub" (Guild ID: `1263067254153805905`).

## Logged Events

### Member Events
- **MEMBER_JOIN**: Member joined (includes account age).
- **MEMBER_LEAVE**: Member left.
- **ROLE_ADD/REMOVE/UPDATE**: Role changes for a member.
- **NICKNAME_UPDATE**: Member nickname changes.

### Moderation Events
- **BAN/UNBAN**: Member banned or unbanned.
- **KICK**: Member kicked.
- **TIMEOUT/MUTE**: Member timed out (includes duration and expiration).
- **WARN**: Member warned (includes Case ID).
- **APPEAL**: Status changes for appeals (Submitted, Approved, Denied).
- **POINT**: Staff point updates.

### Voice Events
- **VOICE_MUTE/UNMUTE**: Server voice mute status.
- **VOICE_DEAFEN/UNDEAFEN**: Server voice deafen status.
- **VOICE_DISCONNECT**: Forced voice disconnection.

### Server Events
- **CHANNEL_CREATE/DELETE/UPDATE**: Channel modifications.
- **ROLE_CREATE/DELETE**: Role creation/deletion.
- **GUILD_UPDATE**: Server setting changes.
- **EMOJI_UPDATE**: Emoji changes.

## Database Tables
1. **`bot_logs`**: Stores individual log entries.
   - Columns: `id, timestamp, event_type, guild_id, user_id, moderator_id, channel_id, details, sent_to_discord`
2. **`guild_log_channels`**: configuration for where logs are sent.
   - Columns: `guild_id, message_log_channel_id, member_log_channel_id, server_log_channel_id, ticket_log_channel_id, mod_log_channel_id, other_log_channel_id`.

## Usage
Events are typically triggered by other cogs (like `advanced_moderation.py`) simply by adding an item to the queue or triggering a specific listener. The `LoggingCog` listens for standard Discord events (e.g., `on_member_join`) and generates logs automatically.
