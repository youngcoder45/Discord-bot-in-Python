# Permits System Cog

## Overview
The `PermitSystem` cog manages a custom permission system allowing administrators to create specific "permit roles" with granular permissions (e.g., kick, ban, timeout) and assign them to users. This avoids giving users full administrative or moderation roles when only specific capabilities are needed.

## Database Structure
The system uses SQLite (defined in `config.DATABASE_NAME`) with the following tables:
- `permit_roles`: Stores the names of permit roles per guild.
- `permit_permissions`: Maps permit roles to specific allowed actions.
- `permit_assignments`: Assigns permit roles to specific users.

## Commands

All commands are slash commands under the `/permit` group.

### 1. Create New Permit Role
- **Command**: `/permit new <name>`
- **Description**: Creates a new permit role and opens a UI (dropdown) to select permissions.
- **Permissions Required**: Administrator
- **Available Permissions**:
    - `kick_members`: Allow kicking members.
    - `ban_members`: Allow banning members.
    - `moderate_members`: Allow timing out users.
    - `manage_messages`: Allow purging/deleting messages.
    - `manage_nicknames`: Allow changing nicknames.
    - `warn_members`: Allow warning members.

### 2. Assign Permit to User
- **Command**: `/permit add <member> <role_name>`
- **Description**: Assigns an existing permit role to a user.
- **Permissions Required**: Administrator

### 3. List Permit Roles
- **Command**: `/permit list`
- **Description**: Lists all created permit roles in the server.

### 4. Check User Permits
- **Command**: `/permit check <member>`
- **Description**: Displays all permit roles and specific permissions assigned to a user.

## Programmatic Usage
The cog provides a helper method for other cogs to check permissions:
```python
check_permit(user_id: int, guild_id: int, permission: str) -> bool
```
Other cogs can use this to verify if a user is allowed to perform an action based on their assigned permits.
