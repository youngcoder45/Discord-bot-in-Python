# Logging Configuration

This document outlines the configuration of the logging system, specifically focusing on the Channel Mapping which routes different event types to specific Discord channels.

## 📁 Source Configuration
The configuration is defined in `src/commands/logging/config.py`. 

## 📍 Channel Mapping (The CodeVerse Hub)

| Event Category | Log Channel ID | Discord Channel | Description |
| :--- | :--- | :--- | :--- |
| **Join / Leave** | `1460213277333389412` | `#join-leave-logs` | Member joins, leaves, and bot additions. |
| **Member Roles** | `1460207115082661984` | `#member-role-logs` | Roles added or removed from a member. |
| **Member Misc** | `1263434413581008956` | `#member-logs` | Nickname changes, Username updates. |
| **Channel Config** | `1460207608119038034` | `#channel-updates` | Permission updates, Topic changes, Name changes. |
| **Channel Lifecycle**| `1460207206736724181` | `#channel-lifecycle` | Channel creation and deletion events. |
| **Role Lifecycle** | `1460207477248495716` | `#role-logs` | Role creation and deletion in the server. |
| **Moderation** | `1460207055745978611` | `#mod-logs` | Kicks, Bans, and Unbans. |
| **Warnings** | `1460207507703070813` | `#warning-logs` | Manual warnings issued by staff. |
| **Timeouts** | `1460207558605275188` | `#timeout-logs` | Timeout applied, removed, or expired. |
| **Voice Logs** | `1460207532814503986` | `#voice-logs` | Server Mute/Deafen, Voice Disconnects, Moves. |
| **Tickets** | `1438487366305190018` | `#ticket-logs` | Ticket creation, closing, transcripts (Webhook Text Only). |

## ⚙️ How to Change Channels

To update the logging channels:

1.  Open `src/commands/logging/config.py`.
2.  Locate the `LOG_CHANNEL_MAP` dictionary.
3.  Update the ID corresponding to the event you wish to re-route.
4.  Restart the bot for changes to take effect.

```python
# Example: Changing the Ban Log Channel
LOG_CHANNEL_MAP = {
    # ...
    "BAN": 123456789012345678, # <-- New ID Here
    # ...
}
```

## 🔌 Default Fallback

The system currently uses a hardcoded map optimized for "The CodeVerse Hub". If you deploy this bot to another server, you may need to:
1.  Extend `config.py` to support multiple Guild IDs.
2.  Or rely on the database configuration (Legacy table `guild_log_channels`) which is still checked as a fallback if an event isn't found in `LOG_CHANNEL_MAP`.

## 🔄 Webhook Management

The bot automatically creates and manages webhooks for logging.
*   **Webhook Name**: `CodeVerse Logger`
*   **Behavior**:
    *   Checks if a webhook exists in the cached list.
    *   If not, checks the channel permissions.
    *   Creates a new webhook if permission `MANAGE_WEBHOOKS` is available.
    *   Falls back to standard `channel.send()` if webhooks cannot be used.
