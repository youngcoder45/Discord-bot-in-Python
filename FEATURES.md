# CodeVerse Hub Bot - Complete Feature Guide

## 🤖 Bot Overview
CodeVerse Hub Bot is a comprehensive Discord bot designed for programming communities. It features moderation tools, XP/leveling system, automated daily questions, weekly challenges, and community engagement features.

## 🚀 Features

### 📊 XP & Leveling System
- **Automatic XP**: Gain XP by sending messages (with cooldown to prevent spam)
- **Level Roles**: Automatic role assignment based on level progression
- **Leaderboard**: Track top members by XP and level

### 🛡️ Moderation Tools
- **Warning System**: Issue and track warnings with automatic DM notifications
- **Timeout/Mute**: Temporary mute members with duration control
- **Kick/Ban**: Remove members with reason logging
- **Automated Logging**: All moderation actions logged to database

### 🎯 Daily Content
- **Question of the Day (QOTD)**: Automatic daily programming questions
- **Weekly Challenges**: Coding challenges posted every Monday
- **Random Quotes**: Motivational and programming quotes
- **Programming Memes**: Random memes for community fun

### 💬 Community Features
- **Suggestion System**: Members can submit server improvement suggestions
- **Challenge Submissions**: Submit solutions to weekly coding challenges
- **Welcome/Farewell**: Automated member join/leave messages
- **Activity Tracking**: Track member engagement and participation

## 📝 Command List

### 🔧 Prefix Commands (Using `!`)

#### Community Commands
- `!quote` - Get a random motivational quote
- `!question` - Get a random programming question
- `!meme` - Get a random programming meme
- `!suggest <suggestion>` - Submit a suggestion for the server
- `!submit-challenge <link>` - Submit your challenge solution
- `!reload-data` - Reload bot data files (Admin only)

#### Leaderboard Commands
- `!rank [member]` - Check rank and XP stats
- `!leaderboard [page]` - View server XP leaderboard
- `!level [member]` - Check level information and progress
- `!top` - Quick view of top 5 members
- `!reset-xp <member>` - Reset a member's XP (Moderator only)

#### Moderation Commands
- `!warn <member> [reason]` - Warn a member
- `!warnings <member>` - View member's warning history
- `!kick <member> [reason]` - Kick a member
- `!ban <member> [reason] [delete_days]` - Ban a member
- `!unban <user_id> [reason]` - Unban a user
- `!timeout <member> <duration> [reason]` - Timeout a member
- `!untimeout <member>` - Remove timeout from member
- `!clear <amount>` - Delete messages (bulk delete)
- `!slowmode <seconds>` - Set channel slowmode
- `!lock` - Lock a channel
- `!unlock` - Unlock a channel

### ⚡ Slash Commands (Using `/`)

#### Community Slash Commands
- `/quote` - Get a random motivational quote
- `/question` - Get a random programming question  
- `/meme` - Get a random programming meme
- `/suggest <suggestion>` - Submit a suggestion for the server
- `/submit-challenge <link>` - Submit your challenge solution

#### Leaderboard Slash Commands
- `/rank [member]` - Check rank and XP stats
- `/leaderboard [page]` - View server XP leaderboard
- `/level [member]` - Check level information and progress

#### Moderation Slash Commands
- `/warn <member> [reason]` - Warn a member
- `/kick <member> [reason]` - Kick a member
- `/ban <member> [reason] [delete_days]` - Ban a member
- `/timeout <member> <duration> [reason]` - Timeout a member

## 🎭 Level Roles

The bot automatically assigns roles based on member levels:

- **Level 1-4**: 🌱 Seedling Coder
- **Level 5-9**: 🌿 Growing Developer  
- **Level 10-19**: 🌳 Code Gardener
- **Level 20-29**: 🚀 Syntax Navigator
- **Level 30-39**: ⚡ Algorithm Ace
- **Level 40-49**: 🏆 Code Champion
- **Level 50+**: 👑 Programming Legend

## 🔄 Automated Features

### Daily Question of the Day (QOTD)
- Posted every day at 9:00 AM UTC
- Random programming questions from curated list
- Encourages daily community engagement

### Weekly Coding Challenge
- Posted every Monday at 10:00 AM UTC
- New coding challenge with varying difficulty
- Members can submit solutions using commands

### XP System
- Gain 1-3 XP per message (random)
- 60-second cooldown between XP gains
- Level progression formula: `level^2 * 100` XP required
- Bonus XP for various activities (submissions, suggestions, etc.)

### Member Events
- Welcome messages for new members
- Farewell messages when members leave
- Activity tracking and statistics

## 🗃️ Database Tables

The bot uses SQLite with the following tables:
- `users` - User XP, levels, and activity data
- `warnings` - Warning history and details
- `suggestions` - Community suggestions
- `challenge_submissions` - Weekly challenge solutions
- `qotd_submissions` - Question of the day responses
- `mutes` - Timeout/mute tracking

## ⚙️ Configuration

### Required Environment Variables
```env
DISCORD_TOKEN=your_bot_token
GUILD_ID=your_server_id
GENERAL_CHANNEL_ID=channel_for_general_messages
QOTD_CHANNEL_ID=channel_for_daily_questions
CHALLENGE_CHANNEL_ID=channel_for_weekly_challenges
ANNOUNCEMENTS_CHANNEL_ID=channel_for_announcements
SUGGESTIONS_CHANNEL_ID=channel_for_suggestions
MOD_TOOLS_CHANNEL_ID=channel_for_moderation_logs
BOT_COMMANDS_CHANNEL_ID=channel_for_bot_commands
JOINS_LEAVES_CHANNEL_ID=channel_for_member_events
SERVER_LOGS_CHANNEL_ID=channel_for_server_logs
```

### Required Permissions
The bot needs the following Discord permissions:
- Send Messages
- Embed Links
- Attach Files
- Read Message History
- Add Reactions
- Manage Messages (for moderation)
- Kick Members (for moderation)
- Ban Members (for moderation)
- Manage Roles (for level roles)
- Moderate Members (for timeouts)

## 🛠️ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository_url>
   cd codeverse-bot
   ```

2. **Install dependencies**
   ```bash
   pip install discord.py python-dotenv aiohttp aiosqlite
   ```

3. **Configure environment**
   - Copy `.env.example` to `.env`
   - Fill in your Discord bot token and channel IDs

4. **Run the bot**
   ```bash
   python start_bot.py
   ```

## 📊 Data Files

### Questions (`src/data/questions.json`)
Contains programming questions for QOTD feature. Format:
```json
{
  "question": "What is the difference between == and === in JavaScript?",
  "difficulty": "Beginner",
  "category": "JavaScript"
}
```

### Challenges (`src/data/challenges.json`)
Contains weekly coding challenges. Format:
```json
{
  "title": "Two Sum Problem",
  "description": "Given an array of integers and a target sum...",
  "difficulty": "Easy",
  "tags": ["Array", "Hash Table"]
}
```

### Quotes (`src/data/quotes.json`)
Contains motivational and programming quotes. Simple string array format.

## 🎯 Usage Examples

### For Members
1. **Check your rank**: `/rank` or `!rank`
2. **Get daily inspiration**: `/quote` or `!quote`
3. **Submit a suggestion**: `/suggest Make the bot even more awesome!`
4. **Submit challenge solution**: `/submit-challenge https://github.com/username/solution`

### For Moderators
1. **Warn a member**: `/warn @member Please follow the rules`
2. **Timeout someone**: `/timeout @member 30 Spamming in general`
3. **Check warnings**: `!warnings @member`
4. **Bulk delete messages**: `!clear 10`

### For Admins
1. **Reset member XP**: `!reset-xp @member`
2. **Reload bot data**: `!reload-data`
3. **Check bot logs**: View MOD_TOOLS_CHANNEL for all actions

## 🔍 Troubleshooting

### Common Issues
1. **Slash commands not showing**: Ensure bot has application commands permission
2. **XP not updating**: Check for cooldown period (60 seconds)
3. **Bot not responding**: Verify token and permissions
4. **Database errors**: Ensure data directory exists and is writable

### Debug Mode
Run with additional logging:
```bash
python start_bot.py --debug
```

## 🤝 Contributing

To add new features:
1. Create new command files in `src/commands/`
2. Add event handlers in `src/events/`
3. Update database schema in `src/utils/database.py`
4. Add configuration in `.env`

## 📞 Support

For support or feature requests:
- Create an issue on GitHub
- Contact server administrators
- Use the suggestion system in Discord

---

**CodeVerse Hub Bot** - Empowering programming communities with automation and engagement! 🚀
