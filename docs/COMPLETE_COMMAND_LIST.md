# CodeVerse Bot - Complete Command List

**Last Updated:** August 2026

Complete reference of all bot commands, grouped by category.
Commands are hybrid unless marked **(prefix only)** or **(slash only)**.

---

## Table of Contents
- [Core Commands](#core-commands)
- [Moderation](#moderation)
- [Advanced Moderation](#advanced-moderation)
- [Information](#information)
- [Warnings](#warnings)
- [Permits](#permits)
- [Tickets](#tickets)
- [Appeals](#appeals)
- [Reaction Roles](#reaction-roles)
- [Sticky Messages](#sticky-messages)
- [Threads](#threads)
- [Logging](#logging)
- [Utility & Embed Builder](#utility--embed-builder)
- [Server Listing](#server-listing-prefix-only)
- [Rules](#rules-prefix-only)
- [Diagnostics & Owner](#diagnostics--owner)

---

## Core Commands
**Source:** `src/commands/core.py`

| Command | Description | Permission |
|---------|-------------|-----------|
| `/help` • `?help` | Interactive categorized help menu (`/help <command>` for details) | None |
| `/ping` | Check bot latency | None |
| `/info` • `?info` | Detailed user information (alias `userinfo`) | None |
| `/get-user-id` | Get a Discord ID from a mention | None |
| `/prefix` | View or change the per-guild prefix | Manage Server (to change) |
| `/report` • `?report` | Report a message (ID or link) to moderators | None |
| *Report Message* (context menu) | Right-click → Apps → Report Message | None |

---

## Moderation
**Source:** `src/commands/modcog.py`

| Command | Description | Permission |
|---------|-------------|-----------|
| `/purge` • `?purge` | Delete 1–100 messages (channels & threads) | Manage Messages |
| `/clean` • `?clean` | Delete bot messages & command invocations | Manage Messages |
| `/kick` • `?kick` | Kick a member | Kick Members **or** `kick_members` permit |
| `/ban` • `?ban` | Ban a member | Ban Members **or** `ban_members` permit |
| `/unban` • `?unban` | Unban a user by ID | Ban Members |
| `/softban` • `?softban` | Ban + unban to delete messages | Ban Members |
| `/role` • `?role` | Add/remove a role on a member | Manage Roles |
| `/addmod` • `?addmod` | Promote a member to the moderator role | Administrator |
| `/timeout` • `?timeout` (`?mute` alias) | Timeout a member (`10m`, `2h`, `1d`); `?mute` is prefix-only | Moderate Members |
| `/untimeout` • `?untimeout` | Remove a timeout | Moderate Members |
| `/slowmode` • `?slowmode` | View/set slowmode (0–21600s) | Manage Channels |
| `/lock` • `?lock` | Lock a channel or thread | Manage Channels |
| `/unlock` • `?unlock` | Unlock a channel or thread | Manage Channels |
| `/lockdown` • `?lockdown` | Lock all channels | Administrator |
| `/unlockdown` • `?unlockdown` | Unlock all channels | Administrator |
| `/nuke` • `?nuke` | Clone + delete a channel (clears messages) | Bot Owner |
| `/massban` • `?massban` | Ban multiple users by ID | Bot Owner |
| `/nickname` • `?nickname` | Change a member's nickname | Manage Nicknames |
| `/verify` | Verification panel with role selection | Admin bypass role / Administrator |

---

## Advanced Moderation
**Source:** `src/commands/advanced_moderation.py`

| Command | Description | Permission |
|---------|-------------|-----------|
| `/tempban` • `?tempban` | Temporarily ban a member | Ban Members |
| `/unmute` • `?unmute` | Remove a timeout | Moderate Members |
| `?hide` **(prefix only)** | Hide a channel from @everyone | Manage Channels |
| `?unhide` **(prefix only)** | Unhide a channel | Manage Channels |

---

## Information
**Source:** `src/commands/modcog.py`

| Command | Description | Permission |
|---------|-------------|-----------|
| `/serverinfo` • `?serverinfo` | Server statistics and info | None |
| `/roleinfo` • `?roleinfo` | Role information | None |
| `/avatar` • `?avatar` | View a user's avatar | None |

---

## Warnings
**Source:** `src/commands/modules/sam/features/warnings/cogs.py`

| Command | Description | Permission |
|---------|-------------|-----------|
| `/warn` • `?warn` | Issue a warning | Kick Members |
| `/unwarn` • `?unwarn` | Remove a warning by ID | Kick Members |
| `/warnings view` | View a user's warning history | Kick Members |
| `/warnings modify` | Revoke a warning by case ID | Kick Members |
| `/warnings clear` | Clear all warnings for a user | Administrator |

---

## Permits
**Source:** `src/commands/permits.py`

| Command | Description | Permission |
|---------|-------------|-----------|
| `/permit new <name>` | Create a permit role with permissions | Administrator |
| `/permit add <member> <role>` | Assign a permit role to a member | Administrator |
| `/permit list` | List all permit roles | None |
| `/permit check <member>` | Check a member's permits | None |
| `/permit delete <role>` | Delete a permit role (confirmation) | Administrator |
| `/permit rename <role> <new>` | Rename a permit role | Administrator |
| `/permit check-all` | List every user with permits (paginated) | None |

**Permit permissions:** `kick_members`, `ban_members`, `moderate_members`, `manage_messages`, `manage_nicknames`, `warn_members`

---

## Tickets
**Source:** `src/commands/tickets.py`

| Command | Description | Permission |
|---------|-------------|-----------|
| `/ticket panel` | Create a persistent ticket panel | Administrator |
| `/ticket list` | View/filter tickets | Manage Messages |
| `/ticket stats` | Ticket statistics | Manage Messages |
| `/ticket forceclose` | Force-close a ticket | Manage Messages |
| `/ticket log` / `log-disable` | Set / clear ticket log channel | Administrator |
| `/ticket support` / `support-disable` | Set / clear support role | Administrator |
| `/ticket report` / `report-disable` | Set / clear report role | Administrator |
| `/ticket partner` / `partner-disable` | Set / clear partner role | Administrator |
| `/ticket category` / `category-disable` | Set / clear ticket category channel | Administrator |

---

## Appeals
**Source:** `src/commands/appeals.py`

| Command | Description | Permission |
|---------|-------------|-----------|
| `/appeals` • `?appeals` | View appeals by status | Administrator |
| `/appealinfo` • `?appealinfo` | View appeal details | Administrator |
| `/appealcancel` • `?appealcancel` | Cancel a pending appeal | User (own appeal) |

---

## Reaction Roles
**Source:** `src/commands/reaction_roles.py`

| Command | Description | Permission |
|---------|-------------|-----------|
| `/rr` | Create a reaction-role message (up to 10 roles) | Manage Roles |
| `/rrlist` | List reaction-role setups | Manage Roles |
| `/rrremove` | Remove a reaction-role setup | Manage Roles |

---

## Sticky Messages
**Source:** `src/commands/sticky_message.py`

| Command | Description | Permission |
|---------|-------------|-----------|
| `/stickymessage` | Set a sticky message in a channel | Manage Messages |
| `/removesticky` | Remove a sticky message | Manage Messages |
| `/liststicky` | List sticky messages | Manage Messages |

---

## Threads
**Source:** `src/commands/thread.py` **(prefix only)**

| Command | Description | Permission |
|---------|-------------|-----------|
| `?close` | Archive a thread / close a ticket | Mods / Thread Creator |
| `?pin` | Pin a message | Manage Messages |
| `?unpin` | Unpin a message | Manage Messages |

---

## Logging
**Source:** `src/commands/logging/core.py`

| Command | Description | Permission |
|---------|-------------|-----------|
| `/setlogchannels` | Configure per-guild log channels | Administrator |
| `/setlogchannels-disable` | Clear a manual log channel | Administrator |

---

## Utility & Embed Builder
**Source:** `src/commands/utility.py`

| Command | Description | Permission |
|---------|-------------|-----------|
| `/embed` | Create an embed via interactive form | Manage Messages |
| `/editembed` | Edit an existing bot embed | Manage Messages |

---

## Server Listing **(prefix only)**
**Source:** `src/commands/utility.py`

| Command | Description |
|---------|-------------|
| `?ls role <role>` | Role details & permissions |
| `?ls members <role>` | Members with a role |
| `?ls perm <permission>` | Roles with a permission |
| `?ls perms [role]` | Functional roles / role permissions |
| `?ls noperms` | Cosmetic roles |
| `?ls channels [?w Target Perm]` | Channels (optionally filtered) |
| `?ls categories [?w Target Perm]` | Categories (optionally filtered) |
| `?ls bots` | All bots |
| `?ls boosters` | Server boosters |

---

## Rules **(prefix only)**
**Source:** `src/commands/rules.py`

| Command | Description |
|---------|-------------|
| `?r1` … `?r12` | Post a specific server rule |
| `?r34` | Post the extra rule |
| `?tldr` | TL;DR of the rules |

---

## Diagnostics & Owner

| Command | Description | Source | Permission |
|---------|-------------|--------|-----------|
| `?diag` **(prefix only)** | Bot diagnostics | `src/commands/diagnostics.py` | None |
| `?sync` **(prefix only)** | Sync slash commands | `src/commands/core.py` | Bot Owner |
| `?load <cog>` **(prefix only)** | Load/reload a cog | `src/commands/core.py` | Bot Owner |

---

## Need Help?

Use `/help` for the interactive menu, or open a ticket in the server for support.
