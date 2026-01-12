# Logging Event Reference

This document provides a detailed reference for all events tracked by the logging system.

## 👥 Member Events

### `MEMBER_JOIN`
*   **Trigger**: A user joins the server.
*   **Data**: User mention, Account Age, Creation Date, Avatar.

### `MEMBER_LEAVE`
*   **Trigger**: A user leaves the server (or is kicked/banned - this event triggers alongside specific mod events).
*   **Data**: User mention.

### `NICKNAME_UPDATE`
*   **Trigger**: A member changes their server nickname.
*   **Data**: Old Nickname `->` New Nickname.
*   **Audit**: Attempts to identify if a moderator changed it.

### `USER_UPDATE`
*   **Trigger**: A user changes their global username.
*   **Data**: Old Username `->` New Username.

### `ROLE_ADD` / `ROLE_REMOVE`
*   **Trigger**: A role is added to or removed from a member.
*   **Data**: List of added/removed roles.
*   **Audit**: Attributes the change to a moderator if found in audit logs.

---

## 🛡️ Moderation Events

### `BAN` / `UNBAN`
*   **Trigger**: A member is banned or unbanned.
*   **Data**: Target User, Moderator (from audit log), Reason.

### `KICK`
*   **Trigger**: A member is kicked.
*   **Data**: Target User, Moderator, Reason.

### `TIMEOUT_APPLIED`
*   **Trigger**: A member is placed in timeout.
*   **Data**: Duration, Expiry Time, Reason, Moderator.

### `TIMEOUT_REMOVED`
*   **Trigger**: A timeout is manually removed before expiry.
*   **Data**: Moderator who removed it.

### `TIMEOUT_EXPIRED`
*   **Trigger**: A timeout expires naturally.
*   **Data**: "Timeout expired naturally".

### `WARN`
*   **Trigger**: A warning command is used by staff.
*   **Data**: Reason, Case ID, Moderator.

---

## 🔊 Voice Events

### `VOICE_MUTE` / `VOICE_UNMUTE`
*   **Trigger**: Server Mute is toggled (Right-click -> Server Mute).
*   **Scope**: Ignores self-mutes. Only logs if a moderator action is detected in audit logs.
*   **Data**: Channel, Moderator.

### `VOICE_DEAFEN` / `VOICE_UNDEAFEN`
*   **Trigger**: Server Deafen is toggled.
*   **Scope**: Ignores self-deafens. Only logs if a moderator action is detected.
*   **Data**: Channel, Moderator.

### `VOICE_DISCONNECT`
*   **Trigger**: A user is forcefully disconnected from a voice channel.
*   **Condition**: Verified via audit logs (Member Disconnect action).
*   **Data**: Channel name, Moderator.

### `VOICE_MOVE`
*   **Trigger**: A user is moved from one voice channel to another.
*   **Condition**: Verified via audit logs (Member Move action).
*   **Data**: From Channel `->` To Channel, Moderator.

---

## 📺 Channel & Server Events

### `CHANNEL_CREATE` / `CHANNEL_DELETE`
*   **Trigger**: A text/voice/category channel is created or deleted.
*   **Data**: Channel Name, Type, Category, Moderator.

### `CHANNEL_UPDATE`
*   **Trigger**: A channel setting is modified.
*   **Tracked Changes**:
    *   Name changes.
    *   Topic changes.
    *   Permission overwrites (Visibility/Access).
*   **Data**: Old/New values, Moderator who made the change.

### `ROLE_CREATE` / `ROLE_DELETE`
*   **Trigger**: A server role is created or deleted.
*   **Data**: Role Name, Color, Permissions, Moderator.

---

## 🎫 Ticket Events
*These are logged as plain text via Webhook, without Embeds.*

*   `TICKET_CREATE`
*   `TICKET_CLOSE`
*   `TICKET_DELETE`
*   `TICKET_OPEN`
*   `TICKET_TRANSCRIPT`
