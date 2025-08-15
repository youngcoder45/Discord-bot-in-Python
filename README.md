<div align="center">

# 🤖 CodeVerse Bot

Lightweight, modular Discord bot for programming & learning communities. Prefix **`?`**. Built with **discord.py**.

![Status](https://img.shields.io/badge/status-active-success) ![License](https://img.shields.io/badge/license-MIT-blue)

</div>

## 📌 Current State
The project was recently simplified: the old XP / leveling / leaderboard system and AFK / suggestion tracking internals were removed or are being reworked. The codebase now focuses on a minimal core (startup, slash `/ping`, `/info`, basic join/leave handlers) with placeholders for future feature packs.

If you pulled a previous revision that still exposed XP commands, note that they are deprecated and no longer loaded. This README documents both what exists **now** and what is **planned** (marked Planned).


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

| Command | Type | Description |
|---------|------|-------------|
| `/ping` | Slash/Hybrid | Latency check (ephemeral) |
| `/info` | Slash/Hybrid | Bot info + uptime + prefix |
| `/diag` | Slash/Hybrid | Diagnostics snapshot (instance, latency, users) |

Prefix (`?`) equivalents for `ping`, `info`, `diag` also work because they are hybrid commands. No other prefix commands are currently active.
## 📖 Command Reference (Living Section)

| Name | Slash / Prefix | Args | Status | Notes |
|------|----------------|------|--------|-------|
| ping | Slash | – | ✅ | Ephemeral Pong reply |
| info | Slash | – | ✅ | Uptime + prefix |
| diag | Slash | – | ✅ | Diagnostics (instance, latency, uptime, JSON store) |
| quote | Hybrid | – | Planned | Random motivational / coding quote |
| question | Hybrid | – | Planned | Programming practice question |
| meme | Hybrid | – | Planned | Programming meme fetch |
| suggest | Hybrid | suggestion (str) | Planned | Store suggestion (DB table) |
| code-snippet | Slash | language? | Planned | Random / filtered snippet |
| algorithm | Slash | topic? | Planned | Explanation + example |
| quiz | Slash | topic? | Planned | Interactive multi‑Q quiz |
| serverinfo | Slash | – | Planned | Guild stats summary |
| avatar | Slash | member? | Planned | Large avatar embed |
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
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   # Linux/macOS
   # source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Create `.env`
   ```env
   DISCORD_TOKEN=REPLACE_ME
   GUILD_ID=123456789012345678
   PORT=8080
   HOSTING_PLATFORM=local
   # Optional
   JOINS_LEAVES_CHANNEL_ID=
   SERVER_LOGS_CHANNEL_ID=
   ```
4. Run locally
   ```bash
   python src/bot.py
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

### Minimal Hybrid Cog Template
```python
from discord.ext import commands
from discord import app_commands

class MyCog(commands.Cog):
   def __init__(self, bot):
      self.bot = bot

   @commands.hybrid_command(name="hello", description="Say hello")
   async def hello(self, ctx: commands.Context):
      if getattr(ctx, 'interaction', None) and not ctx.interaction.response.is_done():
         await ctx.interaction.response.defer(ephemeral=True)
      message = "Hey there!"
      if getattr(ctx, 'interaction', None):
         await ctx.interaction.followup.send(message, ephemeral=True)
      else:
         await ctx.reply(message)

async def setup(bot):
   await bot.add_cog(MyCog(bot))
```

## 🧩 Extending Features
| Feature | Implementation Hint |
|---------|---------------------|
| Quotes | Use `utils.helpers.get_random_quote` on preloaded list |
| Questions | Similar to quotes via `get_random_question` |
| Memes | Implement `fetch_programming_meme` (API call) |
| Suggestions | Store suggestions in a JSON list (new file) with timestamp |
| Reminders | Track with in‑memory tasks; persist schedule JSON if needed |
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
| Original Creator | @Youngcoder45 |
| Maintainer | @youngcoder45 and @hyscript7|
| Library | discord.py |

Community contributions welcome—submit PRs or issues.

## 🤝 Contributing
1. Fork
2. Branch: `feat/<name>`
3. Commit small, logical changes
4. Open PR with summary & screenshots (if UI/log output relevant)

Coding Style: Keep functions small, prefer async IO, avoid blocking calls.

## 📄 License
MIT License – see `LICENSE` 
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