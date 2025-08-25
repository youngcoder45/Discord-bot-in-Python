# CodeVerse Discord Bot - Wispbyte Deployment

## Bot Information
- **Name**: CodeVerse Bot
- **Language**: Python 3.12
- **Framework**: discord.py
- **Type**: Discord Bot with 24/7 uptime requirements

## Features
- Hybrid commands (prefix & slash)
- Staff shift tracking
- Moderation tools
- Programming utilities
- Fun commands & games
- Automatic server bump reminders

## Installation & Setup

### Environment Variables Required:
```
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_server_id_here
```

### Optional Environment Variables:
```
SERVER_LOGS_CHANNEL_ID=channel_id_for_logs
HOSTING_PLATFORM=wispbyte
PORT=8080
```

### Start Command:
```bash
python src/bot.py
```

### Alternative Start Commands:
```bash
bash start.sh
```

## Dependencies
All dependencies are listed in `requirements.txt`:
- discord.py>=2.3.0
- python-dotenv>=1.0.0
- aiohttp>=3.8.0
- requests>=2.31.0
- aiosqlite>=0.19.0

## File Structure
```
codeverse-bot/
├── src/
│   ├── bot.py (main entry point)
│   ├── commands/
│   ├── events/
│   ├── tasks/
│   └── utils/
├── data/
├── requirements.txt
├── runtime.txt
└── start.sh
```

## Support
For bot-specific issues, check the diagnostics:
- Run diagnostics: `python bot_diagnostics.py`
- Check logs in the console output
