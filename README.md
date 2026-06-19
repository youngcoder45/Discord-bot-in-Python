<div align="center">

# CodeVerse Bot

**Enterprise-grade Discord bot for programming communities with comprehensive management tools**

![Status](https://img.shields.io/badge/status-active-success) ![License](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/python-3.12-blue) ![Features](https://img.shields.io/badge/features-100+-green)

*Professional Staff Management • Advanced Moderation • Support Ticket System • Data Persistence • Programming Utilities • Community Engagement*

</div>

## Features Overview
### Recent Updates (January 15, 2026)
- **Bot Optimization** - Removed unused Automod features and statistics commands for better performance.
- **Command Updates** - `/diag` is now prefix-only (`?diag`) for simplified diagnostics.
- **Stability Fixes** - Fixed configuration loading issues for local databases.

### Recent Updates (January 2026)
- **Log System Refactor** - Migrated to Webhook-based logging to eliminate rate-limit bottlenecks.
- **Backup System Upgrade** - Switched to active cloud repository with real-time failure alerting.
- **Codebase Optimization** - Removed legacy shift tracking systems for better performance.
- **Enhanced Stability** - Fixes for static analysis errors in moderation commands.
### Recent Updates (December 22, 2025)
- **Guild-Specific Logging** - Fixed cross-guild logging issue. Each server now has its own log channels configured separately.
- **Persistent Panels** - Ticket panels and sticky messages now survive bot restarts and updates without breaking.
- **Redesigned Ticket System** - Clean, professional black theme without emojis for better aesthetics.
- **New Utility Command** - Added `/getuserid` command to quickly get user IDs from mentions.
- **Enhanced Stability** - Major improvements to button persistence and interaction handling.

### Recent Updates (December 2025)
- **Enhanced Ticket System** - New categories: Partnership, Role Issues, Warn Appeals. Improved UI and guidelines.
- **Revamped User Info** - `/info` now provides detailed user analytics, including warning history, whitelist status, and permissions.
- **New Report System** - `/report` command and "Report Message" context menu for direct reporting to moderators.
- **Visual Logging Improvements** - Color-coded log embeds (Red for negative actions, Green for positive) for better visibility.
- **Slash Command Sync** - Automatic syncing of slash commands to authorized guilds on startup.

### Recent Updates (November 2025)
- ** Professional Support Ticket System** - Enterprise thread-based ticket system with specialized role routing, information preview, and partnership guidelines
- ** Thread Lock with Emoji Prefix** - `/lock` command now automatically renames threads with prefix for visibility
- ** Appeal Confirmation System** - Appeals now show confirmation embed with Yes/No buttons before submission; window persists until punishment expires; new `/appealcancel` command for canceling pending appeals
- ** Dual-Window Anti-Nuke Protection** - Max 5 bans/kicks per minute OR 12 per 20 minutes; automatic action reversal and actor blocking on violation; detailed staff alerts
- ** Enhanced Thread Close** - `/close` command now sends professional embed notification before archiving (prevents message from reopening); restricted to mods and thread creator only
- ** Lock/Unlock Emoji Management** - `/lock` adds emoji prefix, `/unlock` removes it to restore original thread name

### Core Commands
- **`?ping`** / **`/ping`** - Check bot latency and responsiveness
- **`?info`** / **`/info`** - View detailed user information, warnings, and permissions
- **`?report`** / **`/report`** - Report a message to moderators (supports ID or Link)
- **`?diag`** - Comprehensive bot diagnostics and health status (Prefix Only)
- **`?help`** / **`/help`** - Display all available commands with usage

### Ticket System
**Professional thread-based ticket system with specialized categories**

**Setup Commands:**
- `?ticket_panel [#channel] [support_role] [report_role] [partner_role]` - Create a persistent ticket panel
- Panel buttons remain functional after bot restarts and updates
- Supports custom role assignments for different ticket types

**Categories:**
- **Partnership** - Business partnerships and collaborations (with detailed requirements)
- **General Support** - Get help with using services and features
- **Role Issues** - Issues related to roles and permissions
- **Reports** - Report inappropriate behavior or rule violations
- **Warn Appeals** - Appeal warnings or moderation actions
- **Other Issues** - Anything else that needs attention

**Features:**
- ✅ **Persistent Panels** - Ticket buttons work forever, even after bot restarts
- ✅ **Clean Design** - Professional black theme without emojis
- ✅ **Database-Backed** - All panels stored in database for reliability
- ✅ **Auto-Restore** - Views automatically re-registered on bot startup
- ✅ **Thread-Based** - Private threads for better organization
- ✅ **Role Routing** - Different ticket types notify different staff roles

### Advanced Moderation System

#### Server Information Commands
| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `?serverinfo` / `/serverinfo` | Detailed server statistics and info | None |
| `?userinfo [@user]` / `/userinfo [@user]` | Comprehensive user information | None |
| `?roleinfo <role>` / `/roleinfo <role>` | Detailed role information | None |
| `?channelinfo [#channel]` / `/channelinfo [#channel]` | Channel information and stats | None |

#### Basic Moderation Commands
| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `?purge <amount> [@user]` / `/purge <amount> [@user]` | Delete 1-100 messages | Manage Messages |
| `?kick <member> [reason]` / `/kick <member> [reason]` | Kick a member from server | Kick Members |
| `?ban <member> [days] [reason]` / `/ban <member> [days] [reason]` | Ban a member from server | Ban Members |
| `?unban <user> [reason]` / `/unban <user> [reason]` | Unban a user by ID/name | Ban Members |
| `?timeout <member> <minutes> [reason]` / `/timeout <member> <minutes> [reason]` | Timeout member (max 28 days) | Moderate Members |
| `?untimeout <member> [reason]` / `/untimeout <member> [reason]` | Remove timeout from member | Moderate Members |
| `?warn <member> [reason]` / `/warn <member> [reason]` | Issue warning to member | Manage Messages |
| `?slowmode <seconds> [#channel]` / `/slowmode <seconds> [#channel]` | Set channel slowmode (0-6hrs) | Manage Channels |
| `?nick <member> [nickname]` / `/nick <member> [nickname]` | Change member nickname | Manage Nicknames |
| `/getuserid <user>` | Get the Discord ID of a user | None |

#### Advanced Moderation Commands
| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `?lockdown [#channel] [reason]` / `/lockdown [#channel] [reason]` | Lock channel (prevent normal users from speaking) | Manage Channels |
| `?unlock [#channel] [reason]` / `/unlock [#channel] [reason]` | Unlock previously locked channel | Manage Channels |
| `?hide [#channel]` | Hide channel from @everyone (channel visibility) | Manage Channels |
| `?unhide [#channel]` | Unhide channel for @everyone (restore visibility) | Manage Channels |
| `?nuke [#channel] [reason]` / `/nuke [#channel] [reason]` | Delete and recreate channel (clears all messages) | Manage Channels |
| `?massban <user_ids> [days] [reason]` / `/massban <user_ids> [days] [reason]` | Ban multiple users by ID (max 20) | Ban Members |
| `?listbans` / `/listbans` | List all banned users in server | Ban Members |
| `?addrole <@user> <role> [reason]` / `/addrole <@user> <role> [reason]` | Add role to user | Manage Roles |
| `?removerole <@user> <role> [reason]` / `/removerole <@user> <role> [reason]` | Remove role from user | Manage Roles |

### 🎭 Reaction Role System
**Automated role assignment through emoji reactions**

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/rr <title> <#channel> <description> <role1> [role2]... [role_toggle] [emoji1]...` | Create reaction role message (up to 10 roles) | Manage Roles |
| `/rrlist` | List all active reaction role messages in server | Manage Roles |
| `/rrremove <message_id>` | Remove reaction role tracking for a message | Manage Roles |

**Features:**
- ✅ **Up to 10 Roles** - Support for multiple emoji-role pairs per message
- ✅ **Automatic Assignment** - Instantly adds/removes roles on reaction
- ✅ **Optional Role Toggle** - Limit members to one role from a specific reaction-role message
- ✅ **Data Persistence** - Survives bot restarts with SQLite storage
- ✅ **Permission Validation** - Checks role hierarchy and bot permissions
- ✅ **Embed Integration** - Works with `/editembed` for easy editing
- ✅ **Real-time Tracking** - Live reaction monitoring and role management

#### Anti-Nuke Protection System
**Dual-window rate limiting with automatic action reversal and actor blocking**

**Protection Thresholds:**
- **1-Minute Window:** Max 5 bans/kicks per minute
- **20-Minute Window:** Max 12 bans/kicks across 20 minutes
- **Violation Response:** Automatic ban reversal, 5-minute actor block, staff alerts

**Features:**
- **Dual-Window Tracking** - Sophisticated sliding window detection
- **Actor Attribution** - Identifies who performed illegal actions via audit logs
- **Auto-Unban** - Bans are automatically reversed when limits exceeded
- **Actor Blocking** - Violators blocked for 5 minutes from taking moderation actions
- **Staff Alerts** - Professional embed notifications with detailed information
- **Real-Time Status** - `/antinuke status` shows current protection metrics

**Commands:**
- **`/antinuke status`** - View current anti-nuke protection status and real-time metrics
- **`/antinuke [action] [value]`** - Configure protection settings *(Admin)*

**Example Alert:**
When a user tries to ban/kick more than the limits, staff receives an embed showing:
- Violator identity and action
- Violation details (action count, time window, limit exceeded)
- Block duration (5 minutes)
- Automatic action taken (ban reversed)

### Point-Based Moderation System
**Advanced escalation-based moderation** with monthly resets and approval workflow
- **`?addpoints <@user> <amount> [reason]`** / **`/addpoints <@user> <amount> [reason]`** - Add moderation points (Ban Members)
- **`?points [@user]`** / **`/points [@user]`** - Check moderation points for any user
- **`?pendingbans`** / **`/pendingbans`** - View users with pending point-based bans (Ban Members)
- **`?approveban <@user>`** / **`/approveban <@user>`** - Approve point-based ban (Ban Members)
- **`?declineban <@user>`** / **`/declineban <@user>`** - Decline point-based ban (Ban Members)
- **100-point monthly cap** - Automatic ban request at 100 points
- **Two-moderator approval** - Requires 2 staff approvals for execution
- **Monthly reset system** - Points reset on the 1st of each month
- **Audit logging** - All point actions logged for transparency
- **Interactive approval** - Discord UI buttons for ban approvals

### Appeal System
**Professional unban appeal workflow** with auto-DM and staff management
- **`?appeals [status]`** / **`/appeals [status]`** - View appeal requests by status (Admin)
- **`?approve <appeal_id> [reason]`** / **`/approve <appeal_id> [reason]`** - Approve unban appeal (Admin)
- **`?deny <appeal_id> <reason>`** / **`/deny <appeal_id> <reason>`** - Deny unban appeal (Admin)
- **`?appealinfo <appeal_id>`** / **`/appealinfo <appeal_id>`** - Get detailed appeal information (Admin)
- **`?appealcancel`** - Cancel pending appeal with confirmation *(User)*

**Appeal Confirmation System** *(NEW)*
- **Confirmation Embed** - Users see appeal preview with Yes/No buttons before submission
- **Persistent Window** - Confirmation window stays open until punishment (ban/timeout) expires
- **Appeal Revision** - Users can click "No" to revise their appeal before sending
- **No Response** - If user doesn't respond, nothing happens (stays open indefinitely)
- **Auto-Expiry Check** - System validates punishment is still active before final submission
- **Appeal Cancel** - Users can cancel pending appeals with `/appealcancel` command

**Appeal Workflow:**
1. User gets kicked/banned/timed out
2. Bot sends DM with appeal form
3. **NEW:** Shows confirmation embed with preview
4. User clicks Yes/No or ignores
5. If Yes: Appeal submitted to staff for review
6. If No: User can revise and submit again
7. Staff approves or denies with reason

- **Auto-DM system** - Appeals automatically sent when users are kicked/banned/timed out
- **Professional embeds** - Clean, modern design without emojis
- **Staff notifications** - Automatic notifications in designated appeals channel
- **User guidance** - Clear instructions for appeal process and requirements
- **Status tracking** - Pending, approved, denied status with timestamps

### Professional Support Ticket System
**Enterprise-grade thread-based ticket system** with specialized role routing and information preview
- **`/ticketpanel [#channel] [@support] [@report] [@partner]`** - Create ticket panel with specialized roles (Admin)
- **`?close`** - Intelligent ticket closure (auto-detects ticket threads)
- **` Create Ticket`** - Interactive button with category selection and information preview

#### Setup & Configuration Commands
| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/ticketsupport [@role]` | Set/view general support team role | Administrator |
| `/ticketreport [@role]` | Set/view specialized report team role | Administrator |
| `/ticketpartner [@role]` | Set/view specialized partnership team role | Administrator |
| `/ticketlog [#channel]` | Set/view ticket logging channel | Administrator |
| `/ticketsupport-disable` | Remove support role setting | Administrator |
| `/ticketreport-disable` | Remove report team role setting | Administrator |
| `/ticketpartner-disable` | Remove partner team role setting | Administrator |

#### Management Commands
| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/forceclose <thread_id> [reason]` | Force close any ticket with reason | Administrator |
| ` Close` | Close button within ticket threads | Staff/Thread Creator |
| ` Claim` | Claim ticket button (Staff only) | Staff |

#### Key Features
- ** Information Preview** - Users see detailed guidelines and examples before creating tickets
- ** Specialized Routing** - Different teams handle different ticket types:
  - **Bug Reports** → General support team
  - **General Support** → General support team  
  - **Partnerships** → Partner team (with server requirements and terms)
  - **Reports** → Report team (with evidence guidelines)
  - **Suggestions** → General support team
- ** Thread-Based** - Each ticket creates a private thread with automatic staff assignment
- ** Complete Logging** - All ticket actions logged with timestamps and details
- ** Smart Closure** - Intelligent detection between regular threads and ticket threads
- ** Role Integration** - Automatic addition of relevant team members to ticket threads
- ** Fallback System** - Specialized roles fall back to general support if not configured

#### Partnership Requirements *(Built-in Guidelines)*
- **Server Requirements:** 100+ members, 1/9 activity ratio, 500+ daily messages, SFW content
- **Community Focus:** Tech/IT related but different specialization from CodeVerse
- **Staff Requirements:** Active and reliable moderation team
- **Mutual Benefits:** Custom advertisement channels, partnership channels, collaborative events
- **Terms & Conditions:** Clear partnership removal conditions and guidelines

#### Ticket Workflow
1. User clicks ** Create Ticket** button
2. Selects category from dropdown menu
3. Views detailed information and guidelines for selected category
4. Clicks **Create This Ticket** button to confirm
5. Private thread created with appropriate team automatically added
6. Staff receives notification and can manage via embed controls
7. Ticket tracked and logged throughout entire lifecycle

### Staff Aura System (Points & Recognition)
**Comprehensive staff recognition and promotion system** with leaderboards and statistics
- **`?aura check [@user]`** / **`/aura check [@user]`** - Check aura balance
- **`?aura leaderboard`** / **`/aura leaderboard`** - View staff rankings (all staff with aura)
- **`?aura top`** / **`/aura top`** - Quick top 3 view with medals
- **`?aura stats [@user]`** / **`/aura stats [@user]`** - Detailed performance statistics
- **`?aura add <@user> <amount> [reason]`** / **`/aura add <@user> <amount> [reason]`** - Award aura (Admin only)
- **`?aura remove <@user> <amount> [reason]`** / **`/aura remove <@user> <amount> [reason]`** - Remove aura (Admin only)
- **`?aura set <@user> <amount> [reason]`** / **`/aura set <@user> <amount> [reason]`** - Set exact aura (Admin only)
- **`?aura reset <@user> [reason]`** / **`/aura reset <@user> [reason]`** - Reset to zero (Admin only)
- **`?aura history [@user] [limit]`** / **`/aura history [@user] [limit]`** - View aura activity log (Mod+)
- **`?aura config <action> [value]`** / **`/aura config <action> [value]`** - Configure system (Admin only)
- **Automatic aura for "thanks"** - Staff get +1 aura when thanked via mention/reply


- **`?shift settings logs [#channel]`** / **`/shift settings logs [#channel]`** - Set shift log channel (Admin only)
- **`?shift settings addrole <role>`** / **`/shift settings addrole <role>`** - Add staff role (Admin only)
- **`?shift settings removerole <role>`** / **`/shift settings removerole <role>`** - Remove staff role (Admin only)
- **`?shift settings clearroles`** / **`/shift settings clearroles`** - Clear all staff roles (Admin only)
- **`?shift settings listroles`** / **`/shift settings listroles`** - List staff roles

### Election System
**Professional staff election system** with weighted voting and comprehensive management
- **`?election create <title> <candidates> [duration]`** / **`/election create <title> <candidates> [duration]`** - Create new election (Manage Messages+)
- **`?election results`** / **`/election results`** - View current election results
- **`?election end`** / **`/election end`** - Force end active election (Admin only)
- **Interactive voting** with buttons and real-time results
- **Weighted voting system** based on user roles and permissions
- **Multiple candidate support** (up to 10 candidates per election)
- **Automatic result calculation** with percentage breakdown

### Data Persistence
**Reliable data storage system**
- Uses SQLite and JSON for stable data storage
- Critical data (users, warnings, tickets) is persisted immediately to disk
- **Note**: Automated cloud backups disabled for performance optimization


### Logging System
**Guild-specific logging with separate channels per server**

**Configuration:**
- **`!setlogchannels [#member-logs] [#mod-logs] [#ticket-logs]`** - Configure log channels for your server
- Run without arguments to view current configuration
- Each server has independent log channel settings
- Logs never cross between different guilds

**Log Categories:**
- **Member Logs** - Join/leave events, role updates, nickname changes
- **Moderation Logs** - Bans, kicks, warns, timeouts, unbans, appeals
- **Ticket Logs** - Ticket creation, closure, claiming, transcripts

**Features:**
- ✅ **Guild-Specific** - Each server's logs go only to that server's channels
- ✅ **Color-Coded** - Red for negative actions, green for positive
- ✅ **Detailed Information** - User IDs, timestamps, reasons, moderators
- ✅ **Database-Backed** - All logs stored in database for history
- ✅ **Auto-Cleanup** - Failed logs handled gracefully

### Community & Engagement
- **`?quote`** / **`/quote`** - Get inspirational programming quotes
- **`?question`** / **`/question`** - Random programming questions for learning
- **`?meme`** / **`/meme`** - Programming memes and jokes from multiple sources
- **`?suggest <text>`** / **`/suggest <text>`** - Submit suggestions (ephemeral acknowledgment)

### Fun & Games
**Professional entertainment commands** with programming themes
| Command | Description |
|---------|-------------|
| `?compliment [@user]` / `/compliment [@user]` | Send a random programming-themed compliment |
| `?joke` / `/joke` | Programming jokes and puns |
| `?fortune` / `/fortune` | Programming fortune cookie wisdom |
| `?trivia` / `/trivia` | Interactive programming trivia questions |
| `?flip` / `/flip` | Coin flip with emoji visualization |
| `?roll [NdN]` / `/roll [NdN]` | Advanced dice rolling (e.g., 2d6, 1d20) |
| `?choose <options>` / `/choose <options>` | Choose between comma-separated options |

### Utility Commands
**Advanced utility and embed generation tools**
- **`?embed create`** / **`/embed create`** - Interactive embed builder with form
- **`?embed json <json>`** / **`/embed json <json>`** - Create embed from JSON data
- **`?embed edit <message_id>`** / **`/embed edit <message_id>`** - Edit existing embed
- **Advanced embed customization** with colors, fields, footers, and images
- **JSON import/export** for embed templates
- **Message editing capabilities** for dynamic content

### Thread Management System
**Professional thread and post management tools with enhanced visibility and safety**

#### Thread Control Commands
- **`?close [thread_id]`** / **`/close [thread_id]`** - Archive thread with embed notification *(Mods / Thread Creator)*
  - Sends professional embed before archiving to prevent message-induced reopening
  - Only moderators and thread creator can execute
  - Creates audit trail for compliance
  
- **`?lock [thread_id]`** / **`/lock [thread_id]`** - Lock thread and add emoji prefix *(Manage Threads)*
  - Example: `"discussion about linux"` → `" discussion about linux"`
  - Prevents accidental reopening by members
  - Clear visual indicator for locked threads
  
- **`?unlock [thread_id]`** / **`/unlock [thread_id]`** - Unlock thread and remove emoji *(Manage Threads)*
  - Restores original thread name automatically
  - Allows members to participate again

#### Message Management
- **`?pin [message_id]`** / **`/pin [message_id]`** - Pin important messages *(Manage Messages)*
- **`?unpin [message_id]`** / **`/unpin [message_id]`** - Unpin messages *(Manage Messages)*
- **`?purge <amount>`** / **`/purge <amount>`** - Delete 1-100 messages *(Manage Messages)*

#### Features
- Works in channels and threads
- Reply feature for pinning specific messages
- Automatic permission validation
- Requires `manage_messages` or `manage_threads` permissions

### AFK System
**Away From Keyboard status management with auto-responses**
- **`?afk [reason]`** / **`/afk [reason]`** - Set yourself as AFK with optional reason
- **`?unafk`** / **`/unafk`** - Manually remove your AFK status
- **`?afklist`** / **`/afklist`** - View all currently AFK users in the server
- **Auto-return** when you send any message
- **Automatic responses** when AFK users are mentioned
- **Duration tracking** and mention counters
- **Server-specific** AFK status per guild

### Programming Utilities (Coming Soon)
*Advanced programming utilities and code tools are planned for future releases*
- Code snippet generation and management
- Regex pattern helpers and validation
- Big O complexity explanations
- HTTP status code lookup
- Git command reference
- Text encoding/decoding tools
- Hash generation utilities
- JSON formatting and validation
- Color format conversion
- UUID generation
- Timestamp conversion tools

## Quick Start

### Prerequisites
- Python 3.12+
- Discord bot token
- Server/Guild ID
- Required bot permissions (see [Configuration](#-configuration))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/youngcoder45/codeverse-bot.git
   cd codeverse-bot
   ```

2. **Set up environment**
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file:
   ```env
   # Required
   DISCORD_TOKEN=your_bot_token_here
   GUILD_ID=your_server_id_here
   
   # Optional - Data Backup (Recommended)
   GITHUB_TOKEN=your_github_personal_access_token
   GITHUB_REPO=yourusername/your-repo-name
   BACKUP_BRANCH=bot-data-backup
   
   # Optional - Logging & Monitoring
   SERVER_LOGS_CHANNEL_ID=123456789
   INSTANCE_ID=production
   PORT=8080
   HOSTING_PLATFORM=Railway
   ```

5. **Run the bot**
   ```bash
   python main.py
   ```

### Windows One-Liner
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; python main.py
```

### First-Time Setup

After the bot is running, configure your server:

1. **Set up data backup (highly recommended)**:
   ```
   /data status
   ```

2. **Configure staff management (Optional)**:
   ```
   /aura config enable true
   /aura config channel #staff-updates
   ```

3. **Test core functionality**:
   ```
   /ping
   /info
   /diag
   ```

## Project Structure

```
codeverse-bot/
├── main.py                      # Production entrypoint
├── src/
│   ├── bot.py                   # Bot initialization & cog loading
│   ├── commands/                # Command modules (cogs)
│   │   ├── core.py              # Core commands (ping, info, help, diag)
│   │   ├── community.py         # Community engagement (quote, question, meme, suggest)
│   │   ├── fun.py               # Fun commands & games (compliment, joke, fortune, trivia, etc.)
│   │   ├── utility.py           # Utility commands (embed builder, tools)
│   │   ├── moderation.py        # Basic moderation commands
│   │   ├── moderation_extended.py # Advanced moderation (lockdown, nuke, massban, etc.)
│   │   ├── staff_points.py      # Staff aura/points system with leaderboards
│   │   ├── election.py          # Staff election system with weighted voting
│   │   ├── data_management.py   # Data backup/restore/export system
│   │   ├── afk.py               # AFK system with auto-responses and tracking
│   │   └── diagnostics.py       # Bot diagnostics and health monitoring
│   ├── events/                  # Event listeners
│   │   ├── member_events.py     # Member tracking and logging
│   │   └── message_handler.py   # Message processing and auto-features
│   ├── tasks/                   # Background tasks
│   │   ├── daily_qotd.py        # Daily question of the day
│   │   └── weekly_challenge.py  # Weekly coding challenges
│   ├── utils/                   # Utilities and helpers
│   │   ├── helpers.py           # Helper functions and embed creators
│   │   ├── database.py          # Database connection and operations
│   │   ├── json_store.py        # JSON-based data storage
│   │   └── keep_alive.py        # Web server for hosting platforms
│   └── data/                    # JSON data files
│       ├── quotes.json          # Motivational and programming quotes
│       ├── questions.json       # Programming questions database
│       ├── challenges.json      # Coding challenges
│       └── code_snippets.json   # Code snippet templates
├── data/                        # Database files (SQLite)
│   ├── codeverse_bot.db         # Main bot database
│   ├── staff_points.db          # Staff aura/points data
│   └── afk.db                   # AFK system database
├── backup/                      # Local backup storage
│   └── bot_data_backup_*.json   # Automated backup files
├── requirements.txt             # Python dependencies
├── runtime.txt                  # Python version for hosting
├── Procfile                     # Process file for deployment
├── railway.json                 # Railway deployment configuration
├── bot_diagnostics.py           # Standalone diagnostics tool
├── quick_test.py                # Quick functionality test
├── deploy.py                    # Deployment helper script
├── sync_commands.py             # Command synchronization utility
├── test_commands.py             # Command testing suite
├── DEPLOYMENT_CHECKLIST.md     # Pre-deployment verification
├── HOSTING_GUIDE.md             # Comprehensive hosting guide
├── ENHANCED_FEATURES.md         # Advanced feature documentation
└── README_DEPLOY.md             # Deployment-specific instructions
```

## Development

### Adding New Commands

1. **Create or edit a cog file** in `src/commands/`
2. **Add command using the prefix decorator**:
   ```python
   @commands.command(name="mycommand", help="Description")
   async def my_command(self, ctx):
       await ctx.send("Hello!")
   ```
3. **Ensure the cog is loaded** in `src/bot.py` COGS_TO_LOAD list

### Running Diagnostics

```bash
python bot_diagnostics.py
```

### Testing Changes

```bash
python quick_test.py
```

## Deployment

### Railway
1. Connect your GitHub repository
2. Set environment variables in Railway dashboard
3. Deploy automatically on push

### Heroku
1. Create new Heroku app
2. Set config vars for environment variables
3. Deploy using Git or GitHub integration

### VPS/Self-Hosted
1. Clone repository on server
2. Set up systemd service or PM2
3. Configure reverse proxy if needed

## Configuration

### Required Environment Variables
- `DISCORD_TOKEN` - Your Discord bot token (from Discord Developer Portal)
- `GUILD_ID` - Your Discord server ID (for command synchronization)

### Optional Environment Variables

#### Data Backup & Persistence (Highly Recommended)
- `GITHUB_TOKEN` - GitHub personal access token for cloud backups
- `GITHUB_REPO` - Repository for backups (default: `youngcoder45/Discord-bot-in-Python`)
- `BACKUP_BRANCH` - Branch for backups (default: `bot-data-backup`)

#### Logging & Monitoring
- `SERVER_LOGS_CHANNEL_ID` - Channel for server event logs
- `INSTANCE_ID` - Custom instance identifier for multi-deployment setups
- `HOSTING_PLATFORM` - Platform identifier (Railway, Heroku, VPS, etc.)
- `PORT` - Port for keep-alive server (default: 8080)

### Required Bot Permissions

#### Essential Permissions
- **View Channels** - Access server channels
- **Send Messages** - Basic bot functionality
- **Embed Links** - Rich embed messages
- **Add Reactions** - Interactive features
- **Use Slash Commands** - Modern Discord interactions
- **Read Message History** - Context-aware responses

#### Moderation Permissions (If Using Moderation Features)
- **Manage Messages** - Message purging and warnings
- **Kick Members** - Member removal
- **Ban Members** - Member banning/unbanning
- **Moderate Members** - Timeout functionality
- **Manage Channels** - Slowmode, lockdown, channel operations
- **Manage Nicknames** - Nickname changes
- **Manage Roles** - Role management for staff systems

#### Advanced Feature Permissions (If Using Staff Systems)
- **Create Public Threads** - Advanced community features
- **Manage Threads** - Thread management
- **Use External Emojis** - Enhanced visual features

### Initial Setup Guide

#### 1. Basic Bot Setup
```bash
# Clone and install
git clone https://github.com/youngcoder45/codeverse-bot.git
cd codeverse-bot
python -m venv .venv && .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure environment
# Create .env file with DISCORD_TOKEN and GUILD_ID
python main.py
```

#### 2. Data Backup Setup (Recommended)
```bash
# 1. Create GitHub personal access token with repo permissions
# 2. Add GITHUB_TOKEN to .env file
# 3. Check backup status
/data status
```

#### 3. Staff Management Setup (Optional)
```bash
# Configure staff aura system
/aura config enable true
/aura config channel #staff-updates
```

#### 4. Moderation Setup (Optional)
```bash
# Test moderation commands
/serverinfo
/userinfo @user
/purge 5

# Advanced moderation (Admin only)
/lockdown #general "Maintenance"
/unlock #general
```

### Troubleshooting

#### Common Issues
1. **Commands not appearing**: Ensure `GUILD_ID` is correct and bot has proper permissions
2. **Database errors**: Check file permissions in `data/` directory
3. **Backup failures**: Verify GitHub token permissions and repository access
4. **Permission errors**: Ensure bot role is above managed roles in server hierarchy

#### Diagnostic Commands
```bash
/diag          # Bot health and diagnostics
/data status   # Data backup system status
/info          # Bot information and uptime
```

## Design Philosophy & Architecture

This bot follows **enterprise-grade design principles** for scalability and maintainability:

### Core Design Principles
- **Hybrid command support** - Both prefix (`?`) and slash (`/`) commands for maximum compatibility
- **Modular cog architecture** - Each feature set is a separate, maintainable module
- **Comprehensive data persistence** - Zero data loss with automated backup systems
- **Type-safe implementation** - Full type hints for reliability and maintainability
- **Professional error handling** - Graceful degradation and informative error messages
- **Permission-based security** - Role and permission checks for all sensitive operations
- **Scalable database design** - SQLite for local efficiency, cloud backup for reliability

### Enterprise Features
- **Advanced staff management** - Comprehensive shift tracking and aura systems
- **Data analytics and reporting** - Detailed statistics and performance metrics
- **Automatic data backup & restore** - GitHub-based cloud storage with local fallbacks
- **Democratic processes** - Built-in election system for community governance
- **Advanced moderation tools** - Professional-grade server management capabilities
- **Monitoring and diagnostics** - Real-time health checks and performance monitoring

### Performance & Reliability
- **Fast startup times** - Optimized initialization and cog loading
- **Zero-downtime deployment** - Data persistence across restarts and updates
- **Multi-platform support** - Works on Windows, Linux, and macOS
- **Hosting platform agnostic** - Supports Railway, Heroku, VPS, and local hosting
- **Comprehensive logging** - Detailed logging for debugging and monitoring

### What Makes This Bot Special

#### Fully-Featured Staff Management
Unlike basic bots, this includes professional staff aura/points systems, and comprehensive admin controls that rival commercial solutions.

#### Enterprise Data Protection
Automatic GitHub-based cloud backups ensure your data survives any deployment issues, server crashes, or hosting changes.

#### Democratic Community Tools
Built-in election system allows communities to democratically select staff and make decisions with weighted voting.

#### Professional Moderation Suite
Advanced moderation tools including channel lockdown, mass operations, and comprehensive audit trails.

#### Developer-Friendly Architecture
Clean, modular code with full type hints, comprehensive documentation, and easy extensibility.

### Technical Stack
- **Language**: Python 3.12+ with async/await
- **Discord Library**: discord.py with full hybrid command support
- **Database**: SQLite for local storage, JSON for configuration
- **Backup**: GitHub API for cloud storage
- **Architecture**: Cog-based modular design with dependency injection
- **Type Safety**: Full type annotations and runtime validation

## Author & Credits
| Role | Person |
|------|--------|
| Original Creator | @Youngcoder45 |
| Maintainer | [@youngcoder45](https://github.com/youngcoder45) and [@hyscript7](https://github.com/hyscript7)|
| Library | discord.py |

Community contributions welcome—submit PRs or issues.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs via GitHub Issues
- **Discord**: https://discord.gg/3xKFvKhuGR
- **Email**: youngcoder45@gmail.com
