# Developer Guide: Logging System

This guide is intended for developers who want to extend or modify the CodeVerse Bot logging system.

## 🏗️ Architecture

The logging system is built using a **Mixin Pattern** to keep code organized and modular.

### Core Component: `LoggingCog`
Located in `src/commands/logging/core.py`.
*   Inherits from all Mixins (`MemberLogMixin`, `ChannelLogMixin`, etc.) and `commands.Cog`.
*   Manages the **Log Queue** (`asyncio.Queue`) and the **Processing Loop** (`process_logs`).
*   Handles **Database Interaction** (Storing logs).
*   Manages **Webhook Delivery** via `WebhookManager`.

### Mixins
Located in `src/commands/logging/events/`.
Each mixin is a standard `commands.Cog` that defines event listeners (`@commands.Cog.listener()`).
*   **Target**: Capture Discord events.
*   **Action**: Process data, fetch audit logs, and call `self.log_event()`.
*   **Restriction**: Mixins do NOT handle sending data to specific channels; they only dispatch standardized events to the Core.

### Config
Located in `src/commands/logging/config.py`.
*   Maps pure `event_type` strings to Discord Channel IDs.

### Formatter
Located in `src/commands/logging/formatter.py`.
*   Responsible for converting raw log data dictionaries into `discord.Embed` objects.

## 🛠️ How to Add a New Event

1.  **Identify the Event**: Determine which Discord event you need (e.g., `on_message_edit`).
2.  **Choose a Mixin**:
    *   If it fits an existing category (e.g., Members), add it to `src/commands/logging/events/members.py`.
    *   If it's new, create `src/commands/logging/events/new_category.py`.
3.  **Implement Listener**:
    ```python
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        # Logic to extract details
        await self.log_event(
            event_type="MESSAGE_EDIT",
            user_id=after.author.id,
            guild_id=after.guild.id,
            details=f"Old: {before.content}\nNew: {after.content}"
        )
    ```
    *Note: If creating a new file, ensure the Mixin class has the stub method `async def log_event(...)` and import/inherit it in `core.py`.*
4.  **Register Channel**:
    *   Add `MESSAGE_EDIT` to `LOG_CHANNEL_MAP` in `src/commands/logging/config.py`.
5.  **Update Formatter**:
    *   Add a case for `MESSAGE_EDIT` in `src/commands/logging/formatter.py` to style the embed.

## 📡 Internal API

### `log_event(...)`
The primary internal method used by mixins.
```python
await self.log_event(
    event_type="TYPE",
    user_id=123,
    guild_id=456,
    moderator_id=789, # Optional
    details="Description",
    **kwargs # Extra data passed to formatter
)
```

### `log_mod_action(...)`
Public method for **other cogs** to use (e.g., `modcog.py`).
```python
logging_cog = bot.get_cog("LoggingCog")
if logging_cog:
    await logging_cog.log_mod_action(
        action_type="WARN",
        user_id=target_id,
        guild_id=guild_id,
        moderator_id=mod_id,
        reason="Being rude"
    )
```
