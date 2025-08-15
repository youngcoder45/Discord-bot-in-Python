<div align="center">

# 🤖 CodeVerse Bot

Lightweight, modular Discord bot for programming & learning communities. Prefix **`?`**. Built with **discord.py**.

![Status](https://img.shields.io/badge/status-active-success) ![License](https://img.shields.io/badge/license-MIT-blue)

</div>

## 📌 Current State
The project was recently simplified: the old XP / leveling / leaderboard system and AFK / suggestion tracking internals were removed or are being reworked. The codebase now focuses on a minimal core (startup, slash `/ping`, `/info`, basic join/leave handlers) with placeholders for future feature packs.

If you pulled a previous revision that still exposed XP commands, note that they are deprecated and no longer loaded. This README documents both what exists **now** and what is **planned** (marked Planned).

> SECURITY: A Discord bot token was previously committed. Immediately regenerate a new token in the Discord Developer Portal and update your environment (`DISCORD_TOKEN`). Never commit `.env`.

---

## ✨ Feature Overview

| Category | Status | Description |
|----------|--------|-------------|
| Core Presence | ✅ | Startup, health keep‑alive, global `/ping`, `/info` |
| Community (quotes, memes, questions) | Planned | Random content & engagement commands |
| Learning (snippets, algorithms, quiz) | Planned | Educational helpers / prompts |
| Moderation (warn/mute/etc.) | Planned | Basic moderation utilities |
| Analytics / Stats | Planned | Activity & channel stats (non‑XP) |
| Challenges / QOTD | Planned | Scheduled content tasks |
| XP / Levels / Leaderboard | ❌ Removed | Removed per request |

## 🧪 Implemented Commands (Current)

### Slash Commands
| Command | Type | Description |
|---------|------|-------------|
| `/ping` | Global | Quick latency / availability check (ephemeral) |
| `/info` | Global | Bot info + uptime + prefix |

### Prefix Commands (`?`)
Currently none are active (all prior `!` commands removed). You can add new ones by creating Cogs in `src/commands/` and registering with the existing bot loader.

## 🗺️ Planned / Placeholder Command Sets
These modules exist with skeleton code or are intended for re‑implementation:

| Module | Planned Commands (Examples) |
|--------|------------------------------|
| `community` | `?quote`, `?question`, `?meme`, `/suggest` |
| `learning` | `/code-snippet`, `/algorithm`, `/quiz` |
| `utility` | `/serverinfo`, `/userinfo`, `/avatar`, `/reminder`, `/weather` (placeholder) |
| `analytics` | `/stats`, `/activity-graph`, `/leaderboard-chart` (non‑XP charts) |
| `fun` | Compliments, jokes, fortune responses (to be wired to commands) |
| `member_events` | Join/leave embeds (already simplified) |

> When you implement these, update the Command Reference section below.

## 📖 Command Reference (Living Section)

| Name | Slash / Prefix | Args | Status | Notes |
|------|----------------|------|--------|-------|
| ping | Slash | – | ✅ | Ephemeral Pong reply |
| info | Slash | – | ✅ | Uptime + prefix |
| quote | Hybrid | – | Planned | Random motivational / coding quote |
| question | Hybrid | – | Planned | Programming practice question |
| meme | Hybrid | – | Planned | Programming meme fetch |
| suggest | Hybrid | suggestion (str) | Planned | Store suggestion (DB table) |
| code-snippet | Slash | language? | Planned | Random / filtered snippet |
| algorithm | Slash | topic? | Planned | Explanation + example |
| quiz | Slash | topic? | Planned | Interactive multi‑Q quiz |
| serverinfo | Slash | – | Planned | Guild stats summary |
| userinfo | Slash | member? | Planned | Member profile embed |
| avatar | Slash | member? | Planned | Large avatar embed |
| reminder | Slash | time, message | Planned | Schedule DM/channel reminder |
| weather | Slash | location | Planned | Placeholder for API integration |
| roleinfo | Prefix | role | Planned | Role details (permissions, members) |

## 🏗️ Project Structure
```
codeverse-bot/
├── main.py                 # Production entrypoint
├── src/
│   ├── bot.py              # Bot creation & cog loading
│   ├── commands/           # Command cogs (many are placeholders)
│   ├── events/             # Event listeners (joins, messages)
│   ├── tasks/              # Scheduled tasks (future)
│   ├── utils/              # Helpers (keep_alive, db placeholder)
│   └── data/               # JSON resource files
├── requirements.txt
├── Procfile / railway.json # Hosting configs
├── README.md
└── .gitignore
```

## ⚙️ Setup

1. Clone
   ```bash
   git clone https://github.com/<your-user>/codeverse-bot.git
   cd codeverse-bot
   ```
2. Install deps
   ```bash
   pip install -r requirements.txt
   ```
3. Create `.env`
   ```env
   DISCORD_TOKEN=REGENERATE_THIS_TOKEN
   GUILD_ID=123456789012345678
   PORT=8080
   HOSTING_PLATFORM=local
   # Optional channel IDs (set only what you use)
   JOINS_LEAVES_CHANNEL_ID=...
   SERVER_LOGS_CHANNEL_ID=...
   ```
4. Run locally
   ```bash
   python main.py
   ```

### Windows PowerShell One‑liner
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; python main.py
```

## 🛡️ Security Best Practices
| Risk | Action |
|------|--------|
| Token leakage | Regenerate token immediately if exposed (like prior commit) |
| Committed `.env` | Add to `.gitignore` (already done) and purge from Git history if necessary |
| Excessive intents | Only enable required Gateway Intents in Developer Portal |
| Dependency vulns | Periodically run `pip list --outdated` & `pip-audit` |

## 🔄 Development Workflow
| Task | Command / Action |
|------|------------------|
| Add new Cog | Create `src/commands/new_cog.py` with a `setup(bot)` async function |
| Add slash command | Use `@app_commands.command` inside a Cog & sync (bot auto-syncs on_ready) |
| Add prefix command | Use `@commands.command()` inside a Cog |
| Hot reload (dev) | Stop & restart; dynamic reload command can be added later |

### Minimal Cog Template
```python
from discord.ext import commands
from discord import app_commands

class MyCog(commands.Cog):
   def __init__(self, bot):
      self.bot = bot

   @app_commands.command(name="example", description="Example slash command")
   async def example(self, interaction):
      await interaction.response.send_message("Example works!")

async def setup(bot):
   await bot.add_cog(MyCog(bot))
```

## 🧩 Extending Features
| Feature | Implementation Hint |
|---------|---------------------|
| Suggestions | Create DB table `suggestions(user_id INTEGER, content TEXT, ts TEXT)` |
| Quotes | Load JSON into memory once in Cog `__init__` |
| Memes | Use `requests` or `aiohttp` to fetch from a safe meme API |
| Reminders | Store scheduled jobs in memory or DB; use `asyncio.create_task` & timestamps |
| Weather | Integrate OpenWeatherMap (store API key as `WEATHER_API_KEY`) |

## 🧪 Testing
Run lightweight startup test:
```bash
python quick_test.py
```
Add unit tests (e.g., for helper functions) under a `tests/` folder (not yet present).

## 📦 Deployment (Railway Example)
1. Push repo to GitHub
2. Create Railway project → Deploy from GitHub
3. Set environment variables (same as local `.env`, but NEVER upload the file)
4. Deploy (Procfile / railway.json already provided)

### Keep-Alive
`utils/keep_alive.py` launches a tiny Flask server (port `PORT`) for uptime pings.

## 👤 Author & Credits
| Role | Person |
|------|--------|
| Original Creator | <Your Name / Handle> |
| Maintainer | <Your Name / Handle> |
| Library | discord.py |

Community contributions welcome—submit PRs or issues.

## 🤝 Contributing
1. Fork
2. Branch: `feat/<name>`
3. Commit small, logical changes
4. Open PR with summary & screenshots (if UI/log output relevant)

Coding Style: Keep functions small, prefer async IO, avoid blocking calls.

## 📄 License
MIT License – see `LICENSE` (add one if missing).

## 🆘 Support
| Need | Where |
|------|-------|
| Bug | GitHub Issues |
| Feature idea | GitHub Issues / Discussions |
| Help configuring | README + Issues |

## ✅ Checklist After Cloning
| Step | Done? |
|------|-------|
| Remove exposed token & create new one | ☐ |
| Fill `.env` with new token & IDs | ☐ |
| Run `pip install -r requirements.txt` | ☐ |
| Start bot `python main.py` | ☐ |
| Confirm `/ping` works | ☐ |
| Implement first new command | ☐ |

Made with ❤️ for developer communities. Build out the cogs and make it yours.

---
---