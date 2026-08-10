# Logging Configuration

This document outlines the configuration of the logging system, specifically focusing on the Channel Mapping which routes different event types to specific Discord channels.

## 📁 Source Configuration
The configuration is defined in `src/commands/logging/config.py`, which builds
the event → channel mapping from environment variables. All channel IDs now live
in the root `.env` file (see `config.py` for the fallback defaults).

## 📍 Channel Mapping (The CodeVerse Hub)

| Event Category | .env Variable | Discord Channel | Description |
| :--- | :--- | :--- | :--- |
| **Join / Leave** | `LOG_CHANNEL_MEMBERS_ID` | `#join-leave-logs` | Member joins, leaves, and bot additions. |
| **Member Roles** | `LOG_CHANNEL_MEMBER_ROLE_CHANGES_ID` | `#member-role-logs` | Roles added or removed from a member. |
| **Member Misc** | `LOG_CHANNEL_MEMBER_ROLE_CHANGES_ID` | `#member-logs` | Nickname changes, Username updates. |
| **Channel Config** | `LOG_CHANNEL_CHANNELS_ID` | `#channel-updates` | Permission updates, Topic changes, Name changes. |
| **Channel Lifecycle**| `LOG_CHANNEL_CHANNELS_ID` | `#channel-lifecycle` | Channel creation and deletion events. |
| **Role Lifecycle** | `LOG_CHANNEL_ROLES_ID` | `#role-logs` | Role creation and deletion in the server. |
| **Moderation** | `LOG_CHANNEL_MODERATION_ID` | `#mod-logs` | Kicks, Bans, and Unbans. |
| **Warnings** | `LOG_CHANNEL_WARNINGS_ID` | `#warning-logs` | Manual warnings issued by staff. |
| **Timeouts** | `LOG_CHANNEL_TIMEOUTS_ID` | `#timeout-logs` | Timeout applied, removed, or expired. |
| **Voice Logs** | `LOG_CHANNEL_VOICE_ID` | `#voice-logs` | Server Mute/Deafen, Voice Disconnects, Moves. |
| **Tickets** | `LOG_CHANNEL_TICKETS_ID` | `#ticket-logs` | Ticket creation, closing, transcripts (Webhook Text Only). |

## ⚙️ How to Change Channels

To update the logging channels:

1.  Open the root `.env` file.
2.  Locate the `LOG_CHANNEL_*_ID` variable for the event you wish to re-route (see table above).
3.  Update the ID.
4.  Restart the bot for changes to take effect.

```dotenv
# Example: Changing the Ban Log Channel
LOG_CHANNEL_MODERATION_ID=123456789012345678
```

## 🔌 Default Fallback

The map defaults are optimized for "The CodeVerse Hub". If you deploy this bot to another server, you may need to:
1.  Update the `LOG_CHANNEL_*_ID` variables in `.env` (and `MAIN_GUILD_ID`).
2.  Or rely on the database configuration (Legacy table `guild_log_channels`) which is still checked as a fallback if an event isn't found in `LOG_CHANNEL_MAP`.

## 🔄 Webhook Management

The bot automatically creates and manages webhooks for logging.
*   **Webhook Name**: `CodeVerse Logger`
*   **Behavior**:
    *   Checks if a webhook exists in the cached list.
    *   If not, checks the channel permissions.
    *   Creates a new webhook if permission `MANAGE_WEBHOOKS` is available.
    *   Falls back to standard `channel.send()` if webhooks cannot be used.
