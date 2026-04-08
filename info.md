# CodeVerse Bot — Full Feature Inventory

This document describes what this repository’s Discord bot does **based on the code that actually loads at runtime** (see `src/bot.py` → `COGS_TO_LOAD`) plus notable “present in repo but not really wired up” parts (dashboard, unused storage tables, etc.).

If you’re trying to trim the bot, jump to **Classification (important / ok-to-keep / bloat)**.

---

## TL;DR

- Discord bot built on **discord.py** with **hybrid commands** (prefix + slash-style) and some **prefix-only** commands.
- Uses **SQLite** for most persistence + a small **JSON store** for warnings/submissions.
- Has a separate **dashboard project** under `dash/` (FastAPI backend + React UI) that’s partially scaffolded.
- **Yes, it currently sends join DMs** (see “Member Join DMs”).

---

## Runtime / Ops

### Entry point
- Root entry: `main.py` (adds `src/` to `sys.path`, runs `src/bot.py:main()`).

### Server lock-down (hard restriction)
- The bot only “operates” in a hard-coded allowlist of guild IDs (`AUTHORIZED_SERVERS` in `src/bot.py`).
- On startup it will **auto-leave any unauthorized server** it finds itself in.

### Command style
- Prefix is set in `src/bot.py` to `?`.
- Many commands are `@commands.hybrid_command(...)` (usable as prefix and as app command when synced).
- Some commands are prefix-only `@commands.command(...)`.

### Configuration & hard-coded IDs (important)
- **Environment variables:** `DISCORD_TOKEN` (required), `GUILD_ID` (optional), `INSTANCE_ID` (optional), `BOT_LOCK_FILE` (optional).
- **Single-instance guard:** uses a lock file (`.bot_instance.lock` by default) to reduce accidental double-running.
- **Authorized guilds:** hard-coded in `src/bot.py` (`AUTHORIZED_SERVERS`).
- **Hard-coded channel IDs:** several modules embed channel IDs directly in code/strings, including:
  - Welcome DM content in `events.member_events`.
  - Report target channel in `commands.core` (`REPORT_CHANNEL_ID`).
  - Logging routing map in `src/commands/logging/config.py` (`LOG_CHANNEL_MAP`).
- **Config mismatch note:** root `config.py` contains some defaults like `COMMAND_PREFIX='!'`, but the bot’s actual prefix is set in `src/bot.py` to `?`.

---

## What’s loaded by default (COGS_TO_LOAD)

These are the extensions the bot tries to load on startup:

### Core + Diagnostics
- `commands.core`
  - Owner-only command-tree sync and cog reload.
  - `/Report Message` context menu + `?report` command (reports a message to a hard-coded report channel).
  - Utility-style info commands (`ping`, `info`, `help`).
- `commands.diagnostics`
  - `?diag` (lightweight diagnostics).

### Centralized logging (webhook-based)
- `commands.logging`
  - Captures moderation + member + channel + role + ticket + other events.
  - Routes each log “event type” to **hard-coded channel IDs** via `src/commands/logging/config.py`.
  - Uses webhooks (helps avoid embed/rate-limit pain for high-volume logs).

### Tickets
- `commands.tickets`
  - Thread-based ticket system (panel, open/close, transcript/logging hooks, partner/support/report variants).
  - Uses persistent UI components (views/buttons) and a database-backed configuration.

### Moderation
- `commands.modcog`
  - Main moderation toolbox (purge/ban/kick/warn-ish actions, role mgmt, locking, slowmode, user/server info, etc.).
- `commands.advanced_moderation`
  - Advanced actions like tempban and mute/unmute, plus some “safety” / anti-abuse guardrails.

### Protection / Anti-abuse
- `commands.protection`
  - Anti-spam / anti-raid / anti-nuke style controls.
  - “New account” detection and a conditional join DM for very new accounts.
- `commands.spam_catch`
  - Channel-level spam catching (e.g., auto-timeout for posting in protected channels).

### Appeals
- `commands.appeals`
  - Ban/mute appeal workflow using modals + DB-backed storage.
  - Staff can review / approve / deny.

### Sticky messages
- `commands.sticky_message`
  - Configure sticky posts per channel and auto-repost them.

### Reaction roles
- `commands.reaction_roles`
  - Reaction-role configuration stored in a database.

### Staff aura points
- `commands.staff_points`
  - “Aura” point tracking stored in `data/staff_points.db`.
  - Commands for add/remove/set/reset + history + leaderboard.
  - Also supports “auto-award” flow via the message handler (see Events).

### Permits
- `commands.permits`
  - Permit/whitelist-style permissions for bot-controlled moderation actions.

### Utility + Rules
- `commands.utility`
  - Embed builder commands and “list server stuff” commands (`ls_command ...`).
- `commands.rules`
  - Shortcut commands to post rules / TL;DR (prefix commands like `?r1`, `?tldr`).

### Thread tools
- `commands.thread`
  - Manage thread state via prefix commands (`?close`, `?pin`, `?unpin`).
- `commands.help_thread_notification`
  - When a help thread is created, notify a target channel and post confirmations.

### SAM module (Script’s Advanced Moderation)
- `commands.modules.sam`
  - Provides a warning system and internal DB via SQLModel.
  - Bridges its logs into the bot logging channel via `commands.modules.sam.bridge`.

### Event handlers
- `events.member_events`
  - Member join/leave handler; currently sends welcome DMs (see below).
- `events.message_handler`
  - Auto-reacts in introductions channel.
  - Auto-awards aura points when an admin/owner says “thanks” and mentions/replies to a staff member.
  - Global command error handler.

---

## Important non-command behaviors

### Member Join DMs (Yes, currently enabled)
There are multiple join listeners:

- `events.member_events:on_member_join`
  - Sends a **welcome DM embed** to every joining member (if DMs are open).
  - Message contains several hard-coded channel mentions (channel IDs baked into the string).

- `commands.protection` also has a join listener
  - Sends a **separate DM** only when the account age is below the configured threshold.

- `events.message_handler:on_member_join`
  - Explicitly “no DM” and does nothing, but it does **not** stop other listeners from DMing.

### Auto reactions in introductions
- When someone posts in a hard-coded introductions channel ID, the bot auto-reacts with 👋🏻 / 🔥 / ❤️.

### Auto aura from “thanks”
- If the **server owner or an admin** sends a message containing the word “thanks” (exact word boundary match) and mentions/replies to staff, the bot auto-awards **+1 aura** to the staff member and replies with a confirmation embed.

---

## Storage (Persistence)

### SQLite
The bot initializes (at least) the following DB files under `data/`:

- `data/staff_points.db`
  - `staff_points`, `points_history`, `staff_config` tables.

- `data/codeverse_bot.db`
  - `elections` and `bot_settings` tables (note: elections/settings tables exist even if no exposed “elections” feature is currently active via commands).

Other cogs also use SQLite-backed persistence (tickets, appeals, reaction roles, sticky messages, logging), either in their own DB files or in tables created on demand.

### JSON store (limited)
- `src/utils/json_store.py` implements a small JSON persistence layer under `data/`:
  - `warnings.json` is active and used by `commands.core` user-info output.
  - `users.json` user tracking exists but is currently **disabled** (`add_or_update_user` is a `pass`).
  - Challenge/QOTD submission stores exist but depend on features that may not currently be exposed.

---

## Dashboard (dash/)

This repo contains a separate dashboard project:

- Backend: `dash/dash-api/` (FastAPI)
- Frontend: `dash/dash-ui/` (React + TS + Vite + Tailwind)

Status (based on code/docs): it’s a real scaffold with auth + pages, but many integrations are incomplete or placeholders compared to the bot’s actual runtime features.

---

## Classification (important / ok-to-keep / bloat)

This is a pragmatic classification for a typical community Discord server.

### 1) Important (core value / safety / operations)
- Authorized-server restriction + auto-leave (security / brand control)
- Logging system (moderation audit trail)
- Moderation + advanced moderation (ban/kick/timeout/mute/tempban, locks/slowmode)
- Protection + spam catch (anti-raid/anti-spam/anti-nuke safety net)
- Tickets + appeals (member support workflows)

### 2) OK to keep (useful but optional depending on server)
- Reaction roles (good UX, but only needed if you use roles heavily)
- Sticky messages (useful for FAQs/important notices)
- Utility embed builder + listing tools
- Rules shortcuts (`?r1`…`?r11`, `?tldr`)
- Thread tools + help-thread notifications (useful if you run help forums)
- Staff aura points (nice for incentives/recognition, not required)
- Permits system (useful if you have complex moderator/staff delegation)

### 3) Might be bloat / low ROI (if you’re trying to slim down)
- Dashboard (`dash/`) if you don’t actively run/maintain it
- Diagnostics command (`?diag`) if you don’t need on-server troubleshooting
- JSON “users” tracking (already disabled)
- Extra/duplicate join-handling code paths (multiple `on_member_join` listeners; some contradict “no DM” intent)
- `elections` table / related storage if you don’t plan to implement elections

---

## Command inventory (auto-extracted)

Below is an auto-extracted list of decorator-defined commands from `src/commands/**` and `src/events/**`.

Notes:
- It does **not** include the context menu `Report Message` because that’s registered programmatically (not via decorator).
- It lists the command “name” + kind + source location.

## Command Inventory (auto-generated)

Extracted from decorators in `src/commands/**` and `src/events/**`.

| Command | Kind | Source |
|---|---|---|
| `addmod` | hybrid | src/commands/modcog.py:399 |
| `antinuke` | prefix | src/commands/protection.py:415 |
| `antiraid` | prefix | src/commands/protection.py:396 |
| `antispam` | prefix | src/commands/protection.py:375 |
| `appealcancel` | hybrid | src/commands/appeals.py:1322 |
| `appealinfo` | hybrid | src/commands/appeals.py:1286 |
| `appeals` | hybrid | src/commands/appeals.py:1236 |
| `aura` | hybrid_group | src/commands/staff_points.py:130 |
| `aura add` | slash | src/commands/staff_points.py:150 |
| `aura check` | slash | src/commands/staff_points.py:263 |
| `aura cleanup` | slash | src/commands/staff_points.py:441 |
| `aura history` | slash | src/commands/staff_points.py:279 |
| `aura leaderboard` | slash | src/commands/staff_points.py:339 |
| `aura remove` | slash | src/commands/staff_points.py:187 |
| `aura reset` | slash | src/commands/staff_points.py:497 |
| `aura set` | slash | src/commands/staff_points.py:229 |
| `avatar` | hybrid | src/commands/modcog.py:988 |
| `ban` | hybrid | src/commands/modcog.py:227 |
| `bothelp` | hybrid | src/commands/core.py:304 |
| `check_appeals` | hybrid | src/commands/appeals.py:1469 |
| `clean` | hybrid | src/commands/modcog.py:333 |
| `close` | prefix | src/commands/thread.py:133 |
| `diag` | prefix | src/commands/diagnostics.py:14 |
| `editembed` | slash | src/commands/utility.py:323 |
| `embed` | slash | src/commands/utility.py:300 |
| `embedhelp` | slash | src/commands/utility.py:560 |
| `embedquick` | slash | src/commands/utility.py:458 |
| `forceclose` | hybrid | src/commands/tickets.py:1552 |
| `getuserid` | prefix | src/commands/protection.py:481 |
| `getuserid` | slash | src/commands/protection.py:469 |
| `help` | hybrid | src/commands/core.py:249 |
| `hide` | prefix | src/commands/advanced_moderation.py:182 |
| `info` | hybrid | src/commands/core.py:105 |
| `introreact` | prefix | src/events/message_handler.py:34 |
| `kick` | hybrid | src/commands/modcog.py:184 |
| `liststicky` | hybrid | src/commands/sticky_message.py:296 |
| `load` | prefix | src/commands/core.py:40 |
| `lock` | hybrid | src/commands/modcog.py:563 |
| `lockdown` | hybrid | src/commands/modcog.py:682 |
| `ls_command boosters` | slash | src/commands/utility.py:1276 |
| `ls_command bots` | slash | src/commands/utility.py:1256 |
| `ls_command categories` | slash | src/commands/utility.py:1115 |
| `ls_command channels` | slash | src/commands/utility.py:915 |
| `ls_command members` | slash | src/commands/utility.py:718 |
| `ls_command noperms` | slash | src/commands/utility.py:804 |
| `ls_command perm` | slash | src/commands/utility.py:741 |
| `ls_command perms` | slash | src/commands/utility.py:847 |
| `ls_command role` | slash | src/commands/utility.py:669 |
| `massban` | hybrid | src/commands/modcog.py:820 |
| `mute` | hybrid | src/commands/advanced_moderation.py:115 |
| `nickname` | hybrid | src/commands/modcog.py:879 |
| `nuke` | hybrid | src/commands/modcog.py:757 |
| `permit_group add` | slash | src/commands/permits.py:107 |
| `permit_group check` | slash | src/commands/permits.py:147 |
| `permit_group list` | slash | src/commands/permits.py:129 |
| `permit_group new` | slash | src/commands/permits.py:98 |
| `pin` | prefix | src/commands/thread.py:187 |
| `ping` | hybrid | src/commands/core.py:93 |
| `purge` | hybrid | src/commands/modcog.py:97 |
| `r1` | prefix | src/commands/rules.py:34 |
| `r10` | prefix | src/commands/rules.py:70 |
| `r11` | prefix | src/commands/rules.py:74 |
| `r2` | prefix | src/commands/rules.py:38 |
| `r3` | prefix | src/commands/rules.py:42 |
| `r34` | prefix | src/commands/rules.py:78 |
| `r4` | prefix | src/commands/rules.py:46 |
| `r5` | prefix | src/commands/rules.py:50 |
| `r6` | prefix | src/commands/rules.py:54 |
| `r7` | prefix | src/commands/rules.py:58 |
| `r8` | prefix | src/commands/rules.py:62 |
| `r9` | prefix | src/commands/rules.py:66 |
| `removesticky` | hybrid | src/commands/sticky_message.py:208 |
| `report` | hybrid | src/commands/core.py:215 |
| `role` | hybrid | src/commands/modcog.py:366 |
| `roleinfo` | hybrid | src/commands/modcog.py:1008 |
| `rr` | slash | src/commands/reaction_roles.py:124 |
| `rrlist` | slash | src/commands/reaction_roles.py:361 |
| `rrremove` | slash | src/commands/reaction_roles.py:404 |
| `serverinfo` | hybrid | src/commands/modcog.py:1076 |
| `slowmode` | hybrid | src/commands/modcog.py:527 |
| `softban` | hybrid | src/commands/modcog.py:298 |
| `stickymessage` | hybrid | src/commands/sticky_message.py:151 |
| `sync` | prefix | src/commands/core.py:29 |
| `tempban` | hybrid | src/commands/advanced_moderation.py:41 |
| `ticketlog` | hybrid | src/commands/tickets.py:1108 |
| `ticketlog-disable` | hybrid | src/commands/tickets.py:1229 |
| `ticketpanel` | hybrid | src/commands/tickets.py:975 |
| `ticketpartner` | hybrid | src/commands/tickets.py:1834 |
| `ticketpartner-disable` | hybrid | src/commands/tickets.py:1923 |
| `ticketreport` | hybrid | src/commands/tickets.py:1695 |
| `ticketreport-disable` | hybrid | src/commands/tickets.py:1784 |
| `tickets` | hybrid | src/commands/tickets.py:1426 |
| `ticketstats` | hybrid | src/commands/tickets.py:1498 |
| `ticketsupport` | hybrid | src/commands/tickets.py:1284 |
| `ticketsupport-disable` | hybrid | src/commands/tickets.py:1370 |
| `timeout` | hybrid | src/commands/modcog.py:441 |
| `tldr` | prefix | src/commands/rules.py:82 |
| `unban` | hybrid | src/commands/modcog.py:270 |
| `unhide` | prefix | src/commands/advanced_moderation.py:229 |
| `unlock` | hybrid | src/commands/modcog.py:623 |
| `unlockdown` | hybrid | src/commands/modcog.py:717 |
| `unmute` | hybrid | src/commands/advanced_moderation.py:158 |
| `unpin` | prefix | src/commands/thread.py:224 |
| `untimeout` | hybrid | src/commands/modcog.py:500 |
| `unwarn` | hybrid | src/commands/modules/sam/features/warnings/cogs.py:99 |
| `userinfo` | hybrid | src/commands/modcog.py:910 |
| `warn` | hybrid | src/commands/modules/sam/features/warnings/cogs.py:48 |
| `warnings` | hybrid_group | src/commands/modules/sam/features/warnings/cogs.py:154 |
| `warnings_group clear` | slash | src/commands/modules/sam/features/warnings/cogs.py:259 |
| `warnings_group modify` | slash | src/commands/modules/sam/features/warnings/cogs.py:208 |
| `warnings_group view` | slash | src/commands/modules/sam/features/warnings/cogs.py:161 |

