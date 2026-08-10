# CodeVerse Bot - Command Reference

This document provides a comprehensive list of all commands available in the CodeVerse Bot, organized by category with locations of the source files.

> **Prefix:** `?` (default) • **Slash:** `/` — hybrid commands work both ways.
> This list reflects only the cogs actually loaded in `src/bot.py` → `COGS_TO_LOAD`.

## Table of Contents
- [Core Commands](#core-commands)
- [Diagnostics](#diagnostics)
- [Moderation Commands](#moderation-commands)
  - [Basic Moderation](#basic-moderation)
  - [Advanced Moderation](#advanced-moderation)
  - [Information Commands](#information-commands)
- [Warning System](#warning-system)
- [Permit System](#permit-system)
- [Ticket System](#ticket-system)
- [Appeals System](#appeals-system)
- [Reaction Roles](#reaction-roles)
- [Sticky Messages](#sticky-messages)
- [Thread Management](#thread-management)
- [Logging](#logging)
- [Utility Commands](#utility-commands)
  - [Embed Builder](#embed-builder)
  - [Server Listing (`?ls`)](#server-listing-ls)
- [Rules Commands](#rules-commands)
- [Owner Commands](#owner-commands)

---

## Core Commands
**Source:** `src/commands/core.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/help`, `?help` | Interactive help menu with dropdown categories | `/help [command]` | None |
| `/ping`, `?ping` | Check bot latency and responsiveness | `/ping` | None |
| `/info`, `?info` | Detailed user information (alias: `userinfo`) | `/info [@user]` | None |
| `/get-user-id`, `?get-user-id` | Get the Discord ID of a user (alias: `getuserid`) | `/get-user-id [user]` | None |
| `/prefix`, `?prefix` | View or change the per-guild command prefix | `/prefix [new_prefix]` | Manage Server (to change) |
| `/report`, `?report` | Report a message to moderators (ID or link) | `/report <message_reference>` | None |
| *Report Message* (context menu) | Right-click a message → Apps → Report Message | — | None |

---

## Diagnostics
**Source:** `src/commands/diagnostics.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `?diag` | Comprehensive bot diagnostics and health status (prefix only) | `?diag` | None |

---

## Moderation Commands

### Basic Moderation
**Source:** `src/commands/modcog.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/purge`, `?purge` | Delete a number of messages (works in channels & threads) | `/purge <amount>` | Manage Messages |
| `/clean`, `?clean` | Delete bot messages and command invocations | `/clean [count=100]` | Manage Messages |
| `/kick`, `?kick` | Kick a member from the server | `/kick <member> [reason]` | Kick Members **or** `kick_members` permit |
| `/ban`, `?ban` | Ban a member from the server | `/ban <member> [reason]` | Ban Members **or** `ban_members` permit |
| `/unban`, `?unban` | Unban a previously banned user (use their ID) | `/unban <user_id> [reason]` | Ban Members |
| `/softban`, `?softban` | Ban and immediately unban to delete recent messages | `/softban <member> [reason]` | Ban Members |
| `/role`, `?role` | Add or remove a role from a user | `/role <member> <role>` | Manage Roles |
| `/addmod`, `?addmod` | Promote a user to the configured moderator role | `/addmod <member>` | Administrator |
| `/timeout`, `?timeout` | Timeout a member for a duration (`10m`, `2h`, `1d`) | `/timeout <member> <duration> [reason]` | Moderate Members |
| `/untimeout`, `?untimeout` | Remove a timeout from a member | `/untimeout <member> [reason]` | Moderate Members |
| `/slowmode`, `?slowmode` | View or set slowmode (0–21600s) | `/slowmode [seconds]` | Manage Channels |
| `/lock`, `?lock` | Lock a channel or thread | `/lock [channel]` | Manage Channels |
| `/unlock`, `?unlock` | Unlock a previously locked channel or thread | `/unlock [channel]` | Manage Channels |
| `/lockdown`, `?lockdown` | Lock all channels in the server | `/lockdown` | Administrator |
| `/unlockdown`, `?unlockdown` | Unlock all previously locked channels | `/unlockdown` | Administrator |
| `/nuke`, `?nuke` | Clone and delete a channel to clear all messages | `/nuke [channel]` | Bot Owner |
| `/massban`, `?massban` | Ban multiple users by ID (max 50) | `/massban <user_ids> [reason]` | Bot Owner |
| `/nickname`, `?nickname` | Change a member's nickname | `/nickname <member> [nickname]` | Manage Nicknames |
| `/verify` | Open a verification panel for a member | `/verify <member>` | Admin bypass role or Administrator |

### Advanced Moderation
**Source:** `src/commands/advanced_moderation.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/tempban`, `?tempban` | Temporarily ban a member | `/tempban <member> <duration> [reason]` | Ban Members |
| `/mute`, `?mute` | Timeout a member temporarily | `/mute <member> <duration> [reason]` | Moderate Members |
| `/unmute`, `?unmute` | Remove a timeout from a member | `/unmute <member> [reason]` | Moderate Members |
| `?hide` | Hide a channel from @everyone (prefix only) | `?hide [channel]` | Manage Channels |
| `?unhide` | Unhide a channel for @everyone (prefix only) | `?unhide [channel]` | Manage Channels |

### Information Commands
**Source:** `src/commands/modcog.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/serverinfo`, `?serverinfo` | Detailed server statistics and info | `/serverinfo` | None |
| `/info`, `?info` | Comprehensive user information (alias: `userinfo`) | `/info [@user]` | None |
| `/roleinfo`, `?roleinfo` | Detailed role information | `/roleinfo <role>` | None |
| `/avatar`, `?avatar` | View a user's avatar in high resolution | `/avatar [@user]` | None |

---

## Warning System
**Source:** `src/commands/modules/sam/features/warnings/cogs.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/warn`, `?warn` | Issue a warning to a user | `/warn <member> [reason]` | Kick Members |
| `/unwarn`, `?unwarn` | Remove a warning by ID | `/unwarn <warning_id>` | Kick Members |
| `/warnings view`, `?warnings view` | View all warnings for a user | `/warnings view <member>` | Kick Members |
| `/warnings modify`, `?warnings modify` | Revoke a warning by case ID | `/warnings modify <case_id> [reason]` | Kick Members |
| `/warnings clear`, `?warnings clear` | Clear all warnings for a user | `/warnings clear <member> [reason]` | Administrator |

---

## Permit System
**Source:** `src/commands/permits.py`

Permit roles are bot-controlled permission groups. A member with a permit can use the
corresponding moderation commands without native Discord permissions (e.g. `kick_members`
permit lets a member use `/kick`).

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/permit new <name>` | Create a permit role and pick its permissions | `/permit new mod` | Administrator |
| `/permit add <member> <role_name>` | Assign a permit role to a member | `/permit add @user mod` | Administrator |
| `/permit list` | List all permit roles | `/permit list` | None |
| `/permit check <member>` | Check what permits a member has | `/permit check @user` | None |
| `/permit delete <role_name>` | Delete a permit role (confirmation required) | `/permit delete mod` | Administrator |
| `/permit rename <role_name> <new_name>` | Rename a permit role (applies to all assignments) | `/permit rename mod senior_mod` | Administrator |
| `/permit check-all` | Show every user with permits and their permissions (paginated) | `/permit check-all` | None |

**Available permit permissions:** `kick_members`, `ban_members`, `moderate_members`, `manage_messages`, `manage_nicknames`, `warn_members`

---

## Ticket System
**Source:** `src/commands/tickets.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/ticket panel` | Create a persistent ticket panel | `/ticket panel [channel] [support_role] [report_role] [partner_role] [color]` | Administrator |
| `/ticket list` | View/filter tickets by status or user | `/ticket list [status] [user]` | Manage Messages |
| `/ticket stats` | View ticket system statistics | `/ticket stats` | Manage Messages |
| `/ticket forceclose` | Force close a ticket by ID or channel | `/ticket forceclose [ticket_id] [channel] [reason]` | Manage Messages |
| `/ticket log` | Set/view the ticket log channel | `/ticket log [channel]` | Administrator |
| `/ticket log-disable` | Remove the custom ticket log channel setting | `/ticket log-disable` | Administrator |
| `/ticket support` | Set/view the support team role | `/ticket support [role]` | Administrator |
| `/ticket support-disable` | Remove the support role setting | `/ticket support-disable` | Administrator |
| `/ticket report` | Set/view the report team role | `/ticket report [role]` | Administrator |
| `/ticket report-disable` | Remove the report role setting | `/ticket report-disable` | Administrator |
| `/ticket partner` | Set/view the partnership team role | `/ticket partner [role]` | Administrator |
| `/ticket partner-disable` | Remove the partner role setting | `/ticket partner-disable` | Administrator |
| `/ticket category` | Set/view the category where tickets are created | `/ticket category [category]` | Administrator |
| `/ticket category-disable` | Remove the ticket category setting | `/ticket category-disable` | Administrator |

---

## Appeals System
**Source:** `src/commands/appeals.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/appeals`, `?appeals` | View appeal requests by status | `/appeals [status]` | Administrator |
| `/appealinfo`, `?appealinfo` | Get detailed appeal information | `/appealinfo <appeal_id>` | Administrator |
| `/appealcancel`, `?appealcancel` | Cancel a pending appeal (with confirmation) | `/appealcancel` | User (their own appeal) |

---

## Reaction Roles
**Source:** `src/commands/reaction_roles.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/rr` | Create a reaction-role message (up to 10 roles) | `/rr <title> <#channel> <description> <role1> [role2]...` | Manage Roles |
| `/rrlist` | List all reaction-role messages in the server | `/rrlist` | Manage Roles |
| `/rrremove` | Remove reaction-role tracking for a message | `/rrremove <message_id>` | Manage Roles |

---

## Sticky Messages
**Source:** `src/commands/sticky_message.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/stickymessage`, `?stickymessage` | Set a sticky message in a channel | `/stickymessage <channel> <content>` | Manage Messages |
| `/removesticky`, `?removesticky` | Remove a sticky message from a channel | `/removesticky <channel>` | Manage Messages |
| `/liststicky`, `?liststicky` | List all sticky messages | `/liststicky` | Manage Messages |

---

## Thread Management
**Source:** `src/commands/thread.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `?close` | Archive a thread (or close a ticket channel/thread) | `?close [thread_id]` | Mods / Thread Creator |
| `?pin` | Pin a message in a thread or channel | `?pin [message_id]` | Manage Messages |
| `?unpin` | Unpin a message | `?unpin [message_id]` | Manage Messages |

---

## Logging
**Source:** `src/commands/logging/core.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/setlogchannels`, `?setlogchannels` | Configure per-guild log channels (member/mod/server/ticket/other) | `/setlogchannels <type> [#channel]` | Administrator |
| `/setlogchannels-disable` | Clear a manual log channel (falls back to defaults) | `/setlogchannels-disable <type>` | Administrator |

Default log destinations are configured in `.env` (`LOG_CHANNEL_*_ID` variables). See `docs/logging/CONFIGURATION.md`.

---

## Utility Commands

### Embed Builder
**Source:** `src/commands/utility.py`

| Command | Description | Usage | Permission |
|---------|-------------|-------|------------|
| `/embed` | Create a beautiful embed with an interactive form | `/embed` | Manage Messages |
| `/editembed` | Edit an existing bot-made embed (ID or message URL) | `/editembed [message_id] [message_url]` | Manage Messages |

### Server Listing (`?ls`)
**Source:** `src/commands/utility.py` (prefix only)

| Command | Description |
|---------|-------------|
| `?ls role <role>` | View full details and permissions of a role |
| `?ls members <role>` | List members who have a specific role |
| `?ls perm <permission>` | See which roles have a specific permission |
| `?ls perms [role]` | List functional roles, or permissions of a specific role |
| `?ls noperms` | List cosmetic roles (no permissions) |
| `?ls channels [?w <Target> <Perm>]` | List channels, optionally filter by permission |
| `?ls categories [?w <Target> <Perm>]` | List categories, optionally filter by permission |
| `?ls bots` | List all bots in the server |
| `?ls boosters` | List server boosters |

---

## Rules Commands
**Source:** `src/commands/rules.py` (prefix only)

| Command | Description |
|---------|-------------|
| `?r1` … `?r12` | Post a specific server rule |
| `?r34` | Post the extra rule |
| `?tldr` | Post the TL;DR summary of the rules |

---

## Owner Commands
**Source:** `src/commands/core.py` (prefix only, bot owner)

| Command | Description |
|---------|-------------|
| `?sync` | Sync the slash command tree |
| `?load <cog>` | Load or reload a cog |

---

## Configuration

The bot is configured entirely through the `.env` file (see `.env.example` for the full
template). This includes the Discord token, authorized guilds, and every
channel/role/user/guild ID used by the bot. See the [README](../README.md#configuration)
for the complete variable reference.

---

Made with ❤️ for CodeVerse
