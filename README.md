# 🤖 CodeVerse Bot

A comprehensive Discord bot designed for **The CodeVerse Hub** - a programming community with 220+ members. This bot automates moderation, community engagement, XP tracking, and educational activities to keep your server active and well-managed.

## ✨ Features

### 🔧 Moderation Commands
- **`!warn @user [reason]`** - Issue warnings to users with tracking
- **`!mute @user [duration] [reason]`** - Temporarily mute users (e.g., `!mute @user 1h spam`)
- **`!timeout @user [duration] [reason]`** - Use Discord's built-in timeout feature
- **`!clear [number]`** - Delete multiple messages (max 100)
- **`!warnings @user`** - View a user's warning history
- **`!unmute @user`** - Remove mute from a user

### 📢 Community Management
- **Daily QOTD** - Automatically posts programming questions at 9 AM UTC
- **Weekly Challenges** - Announces coding challenges every Monday for staff review
- **`!submit-challenge [link]`** - Submit solutions with automatic tracking
- **`!suggest [message]`** - Submit server suggestions with reaction voting
- **`!qotd-answer [answer]`** - Submit QOTD answers for tracking and XP

### 📈 Activity & XP System
- **Automatic XP** - Earn 5 XP per message (1-minute cooldown)
- **Bonus XP** - Extra points for long messages, helpful content, submissions
- **Level Roles** - Auto-assigned based on activity:
  - 🆕 **Newcomer** (Level 1-4)
  - 🟢 **Active** (Level 5-14) 
  - 🔥 **Very Active** (Level 15-29)
  - ⚡ **Ultra Active** (Level 30-49)
  - 👑 **Elite Member** (Level 50+)

### 🏆 Leaderboard & Stats
- **`!leaderboard [limit]`** - View top users by XP
- **`!rank [@user]`** - Check your/someone's rank and progress
- **`!level-roles`** - View available roles and requirements
- **`!xp-leaderboard`** - Simple XP-only leaderboard

### 💬 Community Interaction
- **`!quote`** - Random programming/motivational quotes
- **`!question`** - Get random programming questions
- **`!meme`** - Fetch programming memes from API
- **Welcome/goodbye messages** - Automated member join/leave notifications
- **Comprehensive logging** - Track role changes, username updates, bans

### 🎯 Special Features
- **Thread Creation** - Auto-creates discussion threads for QOTD and challenges
- **Winner Announcements** - Special recognition for QOTD/challenge winners
- **Anti-spam** - Muted users can't send messages
- **Rich Embeds** - Beautiful, consistent formatting for all bot messages
- **Progress Tracking** - Visual progress bars for leveling up

## 🚀 Quick Setup

### Prerequisites
- Python 3.8 or higher
- A Discord bot token
- A Discord server with appropriate permissions

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd codeverse-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your actual values
   # At minimum, set DISCORD_TOKEN and GUILD_ID
   ```

4. **Get Channel IDs**:
   - Enable Developer Mode in Discord
   - Right-click channels → Copy ID
   - Add them to your `.env` file

5. **Run the bot**:
   ```bash
   python src/bot.py
   ```

## ⚙️ Configuration

### Required Environment Variables
```env
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_server_id_here
```

### Channel Configuration
Set these channel IDs in your `.env` file:
- `QUESTIONS_CHANNEL_ID` - Daily QOTD posts
- `STAFF_UPDATES_CHANNEL_ID` - Weekly challenge announcements for staff
- `SUGGESTIONS_CHANNEL_ID` - User suggestions
- `MOD_TOOLS_CHANNEL_ID` - Challenge submissions logging
- `JOINS_LEAVES_CHANNEL_ID` - Welcome/goodbye messages
- `SERVER_LOGS_CHANNEL_ID` - Moderation and member update logs

## 🏗️ Project Structure

```
codeverse-bot/
├── src/
│   ├── bot.py                    # Main bot file
│   ├── commands/
│   │   ├── moderation.py         # Moderation commands
│   │   ├── community.py          # Community features
│   │   └── leaderboard.py        # XP and ranking system
│   ├── events/
│   │   ├── message_handler.py    # XP tracking, level-ups
│   │   └── member_events.py      # Join/leave, logging
│   ├── tasks/
│   │   ├── daily_qotd.py         # Daily question posting
│   │   └── weekly_challenge.py   # Weekly challenge system
│   ├── utils/
│   │   ├── database.py           # SQLite database operations
│   │   └── helpers.py            # Utility functions
│   └── data/
│       ├── questions.json        # QOTD questions pool
│       ├── challenges.json       # Coding challenges
│       └── quotes.json           # Motivational quotes
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
└── README.md                     # This file
```

## 📝 Usage Examples

### Admin Commands
```bash
# Moderation
!warn @spammer Please follow the rules
!mute @user 30m inappropriate language
!clear 10

# XP Management
!give-xp @user 100
!qotd-winner @user  # Set QOTD winner
!challenge-submissions  # View submissions
```

### User Commands
```bash
# Community
!quote
!question  
!meme
!suggest Add more programming channels

# Submissions
!submit-challenge https://github.com/user/solution
!qotd-answer Polymorphism allows different implementations

# Stats
!rank
!leaderboard 20
!level-roles
```

## 🎮 Hosting Options

### Local Development
Run directly with `python src/bot.py`

### Replit
1. Import this repository
2. Set environment variables in Secrets
3. Run the bot

### Railway
1. Connect your GitHub repository
2. Set environment variables
3. Deploy automatically

### VPS/Cloud
1. Clone repository
2. Install dependencies
3. Set up systemd service for auto-restart
4. Configure reverse proxy if needed

## 🔧 Customization

### Adding New Questions/Challenges
Edit the JSON files in `src/data/`:
- `questions.json` - Add new QOTD questions
- `challenges.json` - Add coding challenges
- `quotes.json` - Add motivational quotes

### Modifying XP Values
Edit values in `src/events/message_handler.py`:
```python
base_xp = 5  # Base XP per message
bonus_xp = 2  # Bonus for longer messages
```

### Changing Level Thresholds
Modify role requirements in `src/utils/helpers.py`:
```python
def get_level_role(level: int) -> str:
    if level >= 50:
        return "Elite Member"
    # ... etc
```

## 🛠️ Database Schema

The bot uses SQLite with these tables:
- **users** - XP, levels, message counts, warnings
- **challenge_submissions** - Challenge solution tracking
- **qotd_submissions** - Daily question answers
- **warnings** - Moderation warning history
- **suggestions** - User suggestions
- **mutes** - Temporary mute tracking

## 🚨 Common Issues

### Bot Not Responding
- Check bot token is correct
- Ensure bot has necessary permissions
- Verify bot is in your server

### Missing Permissions
The bot needs these permissions:
- Send Messages
- Manage Messages (for purging)
- Manage Roles (for auto-roles)
- Create Public Threads
- Add Reactions
- Embed Links

### Database Errors
- Ensure the `data/` directory exists
- Check file permissions
- Run database initialization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Discord.py** - The amazing Python Discord library
- **The CodeVerse Hub** - Our wonderful community
- **Contributors** - Everyone who helped improve this bot

## 📞 Support

- Create an issue on GitHub
- Join our Discord server for help
- Check the documentation for common solutions

---

**Made with ❤️ for The CodeVerse Hub community** 🚀

## Usage

- Use the commands as specified in the features section to interact with the bot.
- Ensure that the bot has the necessary permissions in your Discord server to function correctly.

## Contributing

Feel free to contribute to the project by submitting issues or pull requests. Your feedback and contributions are welcome!

## License

This project is licensed under the MIT License. See the LICENSE file for more details.