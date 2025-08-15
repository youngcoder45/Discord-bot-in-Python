<div align="center">

# 🤖 CodeVerse Bot

Lightweight, modular Discord bot for programming & learning communities. **Prefix-only (`?`)**. Built with **discord.py**.

![Status](https://img.shields.io/badge/status-active-success) ![License](https://img.shields.io/badge/license-MIT-blue)

</div>

## 📌 Current State
The project has been aggressively simplified. Removed: XP / leveling / leaderboard, challenges, QOTD, slash & hybrid commands, database layer, AFK, persistent suggestions. Only fast prefix commands and lightweight JSON resources remain.

If you pulled a previous revision with slash commands or XP features, those are gone; everything is prefix-only now.


## ✨ Feature Overview

| Category | Status | Description |
|----------|--------|-------------|
| Core Presence | ✅ | Startup, keep‑alive, ?ping, ?info, ?diag |
| Community (quotes, memes, questions) | ✅ | Random content & engagement (quote, question, meme, suggest) |
| Fun (games, jokes, etc.) | ✅ | Compliment, dadjoke, fortune, wyr, hangman, joke, riddle, trivia, rps, flip, roll, 8ball, poll, guess |
| Challenges / QOTD | ❌ Removed | Removed per simplification |
| XP / Levels / Leaderboard | ❌ Removed | Removed per request |
| Slash Commands | ❌ Removed | Prefix-only interface |

## 🧪 Implemented Commands (Prefix Only)

| Command | Description |
|---------|-------------|
| ?ping | Latency check |
| ?info | Bot info + uptime + prefix |
| ?diag | Diagnostics snapshot |
| ?quote | Random quote |
| ?question | Random programming question |
| ?meme | Random programming meme or text joke |
| ?suggest <text> | Ephemeral suggestion acknowledgement |
| ?compliment [@user] | Random compliment |
| ?dadjoke | Dad joke |
| ?fortune | Programming fortune |
| ?wyr | Would you rather (30s cooldown / channel) |
| ?hangman | Start hangman game (per-channel) |
| ?joke | Programming joke |
| ?riddle | Riddle mini-game |
| ?trivia | Trivia question |
| ?rps <choice> | Rock Paper Scissors |
| ?flip | Coin flip |
| ?roll [NdN] | Dice roll (e.g. 2d6) |
| ?8ball <question> | Magic 8-ball |
| ?poll Q | Opt1 | Opt2 [| Opt3 | Opt4] | Reaction poll |
| ?guess [max] | Number guessing game |
| ?help | Custom help menu |
## 📖 Roadmap (Post-Simplification)

| Feature | Status | Notes |
|---------|--------|-------|
| Moderation basics | Planned | warn, purge, simple logging |
| Educational snippets | Planned | code snippets / explanations |
| Lightweight reminders | Planned | JSON scheduled reminders |
| Optional slash re-intro | Deferred | Only if needed; design clean layer |

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

### Minimal Prefix Cog Template
```python
from discord.ext import commands

class MyCog(commands.Cog):
   def __init__(self, bot):
      self.bot = bot

   @commands.command(name="hello", help="Say hello")
   async def hello(self, ctx: commands.Context):
      await ctx.reply("Hey there!", mention_author=False)

async def setup(bot: commands.Bot):
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