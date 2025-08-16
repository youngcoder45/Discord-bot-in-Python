<div align="center">

# 🤖 CodeVerse Bot

**Lightweight, prefix-only Discord bot for programming communities**

![Status](https://img.shields.io/badge/status-active-success) ![License](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/python-3.12-blue)

*Simple • Fast • Reliable*

</div>

## ✨ Features

### 🎯 Core Commands
- **`?ping`** - Check bot latency and responsiveness
- **`?info`** - View bot information, uptime, and instance details
- **`?diag`** - Get bot diagnostics and health status
- **`?help`** - Display all available commands

### 🎪 Community & Engagement
- **`?quote`** - Get inspirational programming quotes
- **`?question`** - Random programming questions for learning
- **`?meme`** - Programming memes and jokes
- **`?suggest <text>`** - Submit suggestions (ephemeral acknowledgment)

### 🎮 Fun & Games
| Command | Description |
|---------|-------------|
| `?compliment [@user]` | Send a random compliment |
| `?dadjoke` | Get a dad joke |
| `?fortune` | Programming fortune cookie |
| `?wyr` | Would you rather (30s cooldown) |
| `?hangman` | Programming-themed hangman game |
| `?joke` | Programming jokes |
| `?riddle` | Interactive riddle mini-game |
| `?trivia` | Programming trivia questions |
| `?rps <choice>` | Rock Paper Scissors |
| `?flip` | Coin flip |
| `?roll [NdN]` | Dice rolling (e.g., 2d6) |
| `?8ball <question>` | Magic 8-ball |
| `?poll Q \| Opt1 \| Opt2` | Create reaction polls |
| `?guess [max]` | Number guessing game |

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Discord bot token
- Server/Guild ID

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
   DISCORD_TOKEN=your_bot_token_here
   GUILD_ID=your_server_id_here
   # Optional
   JOINS_LEAVES_CHANNEL_ID=123456789
   SERVER_LOGS_CHANNEL_ID=123456789
   ```

5. **Run the bot**
   ```bash
   python main.py
   ```

### Windows One-Liner
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; python main.py
```

## 🏗️ Project Structure

```
codeverse-bot/
├── main.py                 # Production entrypoint
├── src/
│   ├── bot.py              # Bot initialization & cog loading
│   ├── commands/           # Command modules
│   │   ├── core.py         # Core commands (ping, info, help)
│   │   ├── diagnostics.py  # Bot diagnostics
│   │   ├── community.py    # Community engagement
│   │   └── fun.py          # Fun commands & games
│   ├── events/             # Event listeners
│   │   ├── member_events.py # Join/leave handling
│   │   └── message_handler.py # Message processing
│   ├── utils/              # Utilities
│   │   ├── helpers.py      # Helper functions
│   │   ├── json_store.py   # Lightweight data storage
│   │   └── keep_alive.py   # Web server for hosting
│   └── data/               # JSON data files
│       ├── quotes.json     # Motivational quotes
│       ├── questions.json  # Programming questions
│       └── challenges.json # Coding challenges
├── requirements.txt        # Python dependencies
├── bot_diagnostics.py      # Standalone diagnostics tool
├── quick_test.py           # Quick functionality test
└── deployment files...     # Procfile, railway.json, etc.
```

## 🛠️ Development

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

## 🔧 Configuration

### Required Environment Variables
- `DISCORD_TOKEN` - Your Discord bot token
- `GUILD_ID` - Your Discord server ID

### Optional Environment Variables
- `JOINS_LEAVES_CHANNEL_ID` - Channel for member join/leave messages
- `SERVER_LOGS_CHANNEL_ID` - Channel for server logs
- `INSTANCE_ID` - Custom instance identifier
- `PORT` - Port for keep-alive server (default: 8080)

### Bot Permissions Required
- Read Messages
- Send Messages
- Embed Links
- Add Reactions
- Manage Messages
- Create Public Threads

## 📊 Design Philosophy

This bot is intentionally **simplified** and **lightweight**:

- ✅ **Prefix-only commands** (`?`) - No slash commands
- ✅ **JSON-based storage** - No database complexity
- ✅ **Stateless design** - Minimal persistent data
- ✅ **Single-file modules** - Easy to understand and modify
- ✅ **Fast startup** - Minimal dependencies and initialization

### What's NOT Included
- ❌ XP/Leveling system
- ❌ Complex database operations
- ❌ Slash command integration
- ❌ Advanced moderation tools
- ❌ Persistent challenge/QOTD systems

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
