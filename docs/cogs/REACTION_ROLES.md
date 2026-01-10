# Reaction Roles Cog

## Overview
The `ReactionRoles` cog allows administrators to create self-assignable roles using reactions. It supports creating embeds with up to 10 role-emoji pairs. The state is saved in `data/reaction_roles.json`.

## Commands

### Create Reaction Role
- **Command**: `/rr` (Slash Command)
- **Permissions**: `Manage Roles`
- **Arguments**:
    - `title`: Title of the embed.
    - `channel`: Channel where the message will be sent.
    - `description`: Text description for the embed.
    - `role1` - `role10`: Roles to assign.
    - `emoji1` - `emoji10`: Custom emojis (optional, defaults to number emojis 1️⃣-🔟).

**Usage**:
1. Run `/rr title:"Get Roles" channel:#roles description:"React below..." role1:@Member ...`
2. The bot sends an embed to the specified channel.
3. The bot reacts with the configured emojis.
4. Users reacting to the message will receive the corresponding role.

## Features
- **Automatic Role Assignment**: Listens to `on_raw_reaction_add` to give roles.
- **Automatic Role Removal**: Listens to `on_raw_reaction_remove` to take roles away.
- **Permissions Check**: Verifies that the bot has `Manage Roles` and that the role to be assigned is lower than the bot's highest role.
- **Persistence**: Reaction role configurations are saved to a JSON file to survive bot restarts.

## Data Storage
- File: `data/reaction_roles.json`
- Format:
```json
{
  "MESSAGE_ID": {
    "channel_id": 123456789,
    "guild_id": 987654321,
    "roles": {
      "EMOJI_STRING": ROLE_ID
    }
  }
}
```
