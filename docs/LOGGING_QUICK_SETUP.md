# 🚀 Quick Logging Setup Guide

## 1. Create Log Channels

Create three text channels in your Discord server:
- `#member-logs` - For member activity
- `#mod-logs` - For moderation actions  
- `#ticket-logs` - For ticket system events

## 2. Set Permissions

For all three log channels, configure permissions:

**Bot Permissions (Required):**
- ✅ View Channel
- ✅ Send Messages
- ✅ Embed Links
- ✅ Read Message History
- ✅ View Audit Log (CRITICAL - without this, moderator info won't show)

**Moderator Role:**
- ✅ View Channel
- ✅ Read Message History

**@everyone:**
- ❌ View Channel (DENIED)

## 3. Configure Bot

Run this command in any channel:
```
!setlogchannels #member-logs #mod-logs #ticket-logs
```

Or configure them individually:
```
!setlogchannels #member-logs
!setlogchannels #member-logs #mod-logs
```

## 4. Verify Setup

Check current configuration:
```
!setlogchannels
```

## What Gets Logged Where?

### Member Logs Channel (`#member-logs`)
- Member joins/leaves
- Role additions/removals
- Nickname changes
- Voice channel activity (join/leave/move)
- Voice mute/unmute/deafen/undeafen

### Mod Logs Channel (`#mod-logs`)
- Bans/unbans
- Kicks
- Timeouts/untimeouts
- Warnings
- Message edits/deletions
- Message purges
- Channel create/delete/update
- Role create/delete/update
- Server setting changes
- Emoji updates
- Moderation points changes

### Ticket Logs Channel (`#ticket-logs`)
- Ticket creation
- Ticket closure
- Ticket reopening
- Ticket claims
- Ticket assignments

## Troubleshooting

### "Logs not appearing"
1. Check bot has all required permissions
2. Verify channels are configured: `!setlogchannels`
3. Check bot is online
4. Check console for errors

### "Unknown Moderator" showing in logs
- Bot needs **View Audit Log** permission

### Logs are delayed by 0.5-1 second
- This is normal - bot waits for Discord audit logs to populate

## Examples

### Full Setup Command
```
!setlogchannels #member-logs #mod-logs #ticket-logs
```

### Check Configuration
```
!setlogchannels
```

### Update Just One Channel
```
!setlogchannels #new-member-logs
```
This updates member logs while keeping mod/ticket logs unchanged.

## Important Notes

- **Privacy:** Logs contain sensitive information - keep channels private
- **Audit Log Permission:** Required for tracking WHO performed actions
- **Database:** All logs are stored in database even if channels aren't configured
- **No Retroactive Logging:** Only events after bot startup are logged

---

For complete event documentation, see [LOGGING_SYSTEM_DOCUMENTATION.md](./LOGGING_SYSTEM_DOCUMENTATION.md)
