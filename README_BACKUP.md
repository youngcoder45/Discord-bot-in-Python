# Bot Data Backup Branch

This branch contains automated backups of the CodeVerse Discord Bot data.

## What gets backed up:
- Staff points/aura database
- Staff shifts database  
- Main bot database
- Configuration data
- JSON data files

## Backup Schedule:
- Automatic backups every 6 hours
- Manual backups via `/data backup` command

## File Format:
- `bot_data_backup.json` - Complete bot data snapshot
- Backup timestamp included in commit messages

---

**Note:** This branch is automatically managed by the bot's data persistence system.
Do not manually edit files in this branch unless you know what you're doing.
