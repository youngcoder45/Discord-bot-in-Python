<div align="center">

# CodeVerse Bot

**Enterprise-grade Discord bot for programming communities with comprehensive management tools**

![Status](https://img.shields.io/badge/status-active-success) ![License](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/python-3.12-blue) ![Features](https://img.shields.io/badge/features-100+-green)

*Professional Staff Management • Advanced Moderation • Data Persistence • Programming Utilities • Community Engagement*

</div>

## Features Overview

### Core Commands
- **`?ping`** / **`/ping`** - Check bot latency and responsiveness
- **`?info`** / **`/info`** - View bot information, uptime, and instance details
- **`?diag`** / **`/diag`** - Comprehensive bot diagnostics and health status
- **`?help`** / **`/help`** - Display all available commands with usage

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

#### Advanced Moderation Commands
| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `?lockdown [#channel] [reason]` / `/lockdown [#channel] [reason]` | Lock channel (prevent normal users from speaking) | Manage Channels |
| `?unlock [#channel] [reason]` / `/unlock [#channel] [reason]` | Unlock previously locked channel | Manage Channels |
| `?nuke [#channel] [reason]` / `/nuke [#channel] [reason]` | Delete and recreate channel (clears all messages) | Manage Channels |
| `?massban <user_ids> [days] [reason]` / `/massban <user_ids> [days] [reason]` | Ban multiple users by ID (max 20) | Ban Members |
| `?listbans` / `/listbans` | List all banned users in server | Ban Members |
| `?addrole <@user> <role> [reason]` / `/addrole <@user> <role> [reason]` | Add role to user | Manage Roles |
| `?removerole <@user> <role> [reason]` / `/removerole <@user> <role> [reason]` | Remove role from user | Manage Roles |

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

### Staff Shift Tracking System
**Professional staff shift logging system** for tracking on-duty time with comprehensive admin controls
- **`?shift start [note]`** / **`/shift start [note]`** - Start your staff shift (Staff only)
- **`?shift end [note]`** / **`/shift end [note]`** - End your staff shift (Staff only)
- **`?shift discard`** / **`/shift discard`** - Discard current shift (Staff only)
- **`?shift admin active`** / **`/shift admin active`** - View all active shifts (Admin only)
- **`?shift admin history [user] [days]`** / **`/shift admin history [user] [days]`** - View shift history with filters (Admin only)
- **`?shift admin end <user> [reason]`** / **`/shift admin end <user> [reason]`** - Force end user's shift (Admin only)
- **`?shift admin stats [user] [days]`** / **`/shift admin stats [user] [days]`** - View shift statistics (Admin only)
- **`?shift admin summary [days]`** / **`/shift admin summary [days]`** - Staff activity summary (Admin only)
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

### Data Persistence & Backup System
**Enterprise-grade data backup and restoration** - Never lose your data on deployments!
- **`?data status`** / **`/data status`** - Check backup system status and health
- **`?data backup`** / **`/data backup`** - Create immediate backup (Admin only)
- **`?data restore`** / **`/data restore`** - Restore from backup with confirmation (Admin only)
- **`?data export`** / **`/data export`** - Export data as downloadable file (Admin only)
- **GitHub-based cloud storage** with automatic backups every 6 hours
- **Local backup files** as fallback storage
- **Complete data protection** for staff shifts, points, elections, and configurations
- **Zero-downtime deployment** support with automatic data restoration

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

2. **Configure staff shifts (if using staff management)**:
   ```
   /shift settings logs #staff-logs
   /shift settings addrole @Moderator
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
│   │   ├── staff_shifts.py      # Staff shift tracking system
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
│   ├── staff_shifts.db          # Staff shift tracking data
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

## 🌐 Deployment

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
# Configure staff shift tracking
/shift settings logs #staff-logs
/shift settings addrole @Moderator
/shift settings addrole @Admin

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

### 🎯 Core Design Principles
- ✅ **Hybrid command support** - Both prefix (`?`) and slash (`/`) commands for maximum compatibility
- ✅ **Modular cog architecture** - Each feature set is a separate, maintainable module
- ✅ **Comprehensive data persistence** - Zero data loss with automated backup systems
- ✅ **Type-safe implementation** - Full type hints for reliability and maintainability
- ✅ **Professional error handling** - Graceful degradation and informative error messages
- ✅ **Permission-based security** - Role and permission checks for all sensitive operations
- ✅ **Scalable database design** - SQLite for local efficiency, cloud backup for reliability

### 🏢 Enterprise Features
- 🔐 **Advanced staff management** - Comprehensive shift tracking and aura systems
- 📊 **Data analytics and reporting** - Detailed statistics and performance metrics
- 🔄 **Automatic data backup & restore** - GitHub-based cloud storage with local fallbacks
- 🗳️ **Democratic processes** - Built-in election system for community governance
- 🛡️ **Advanced moderation tools** - Professional-grade server management capabilities
- 📈 **Monitoring and diagnostics** - Real-time health checks and performance monitoring

### 🚀 Performance & Reliability
- ⚡ **Fast startup times** - Optimized initialization and cog loading
- 🔧 **Zero-downtime deployment** - Data persistence across restarts and updates
- 📱 **Multi-platform support** - Works on Windows, Linux, and macOS
- 🌐 **Hosting platform agnostic** - Supports Railway, Heroku, VPS, and local hosting
- 🔍 **Comprehensive logging** - Detailed logging for debugging and monitoring

### ✨ What Makes This Bot Special

#### Fully-Featured Staff Management
Unlike basic bots, this includes professional staff shift tracking, aura/points systems, and comprehensive admin controls that rival commercial solutions.

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

## 👤 Author & Credits
| Role | Person |
|------|--------|
| Original Creator | @Youngcoder45 |
| Maintainer | @youngcoder45 and @hyscript7|
| Library | discord.py |

Community contributions welcome—submit PRs or issues.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 🐛 **Issues**: Report bugs via GitHub Issues
- 💬 **Discord**: https://discord.gg/3xKFvKhuGR
- 📧 **Email**: youngcoder45@gmail.com
