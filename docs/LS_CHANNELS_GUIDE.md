# `?ls channels` Command Guide

The `?ls channels` command allows you to audit channel permissions efficiently. You can list all channels or filter them to find where a specific user or role has a certain permission.

## syntax

```
?ls channels [?w <Target> <Permission>]
```

-   **`?w`**: The flag that triggers the "where" filter.
-   **`<Target>`**: The User, Role, or Special Entity (e.g., `everyone`, `here`) to check.
-   **`<Permission>`**: The specific permission to check for.

---

## Examples

1.  **Check where `@everyone` can send messages:**
    ```
    ?ls channels ?w Everyone SendMessage
    ```

2.  **Check where a specific role (e.g., `@Moderators`) can view channels:**
    ```
    ?ls channels ?w @Moderators ViewChannel
    ```

3.  **Check where a user has `Manage Messages`:**
    ```
    ?ls channels ?w @User ManageMessages
    ```

4.  **Check administrative access:**
    ```
    ?ls channels ?w Everyone Admin
    ```

---

## Permission Aliases

The bot accepts these short-hand aliases for common permissions:

| Alias | Startup Permission |
| :--- | :--- |
| `send` | `send_messages` |
| `sendmessage` | `send_messages` |
| `view` | `view_channel` |
| `read` | `view_channel` |
| `admin` | `administrator` |
| `manage` | `manage_channels` |
| `embed` | `embed_links` |
| `attach` | `attach_files` |

---

## Full List of Supported Permissions

You can use any of the following standard Discord permissions. The input is case-insensitive, ignores spaces, and ignores underscores. You can type `SendMessage`, `send messages`, or `send_messages`.

### General Server Permissions
-   `administrator`
-   `view_audit_log`
-   `manage_guild` (Manage Server)
-   `manage_roles`
-   `manage_channels`
-   `kick_members`
-   `ban_members`
-   `create_instant_invite`
-   `change_nickname`
-   `manage_nicknames`
-   `manage_emojis`
-   `manage_webhooks`
-   `view_guild_insights`

### Text Channel Permissions
-   `view_channel` (Read Messages)
-   `send_messages`
-   `send_tts_messages`
-   `manage_messages`
-   `embed_links`
-   `attach_files`
-   `read_message_history`
-   `mention_everyone`
-   `use_external_emojis`
-   `add_reactions`
-   `use_application_commands` (Slash Commands)

### Thread Permissions
-   `create_public_threads`
-   `create_private_threads`
-   `send_messages_in_threads`
-   `manage_threads`

### Voice Channel Permissions
-   `connect`
-   `speak`
-   `stream` (Video)
-   `use_voice_activation`
-   `priority_speaker`
-   `mute_members`
-   `deafen_members`
-   `move_members`
-   `use_embedded_activities` (Activities)
-   `request_to_speak` (Stage Channels)

### Membership Permissions
-   `moderate_members` (Timeout members)

