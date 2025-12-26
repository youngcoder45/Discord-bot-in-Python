# 📋 Log Channel Configuration

## Auto-Configured for The CodeVerse Hub

Your server log channels have been **automatically configured** with 6 separate channels for different event types!

### 🎯 Channel Mapping

| # | Channel Type | Channel ID | What Gets Logged |
|---|--------------|------------|------------------|
| 1️⃣ | **Message Logs** | `1411766480302772435` | Message edits, deletions, bulk purges |
| 2️⃣ | **Member Logs** | `1263434413581008956` | Joins, leaves, role changes, nickname updates |
| 3️⃣ | **Server Logs** | `1411766078920458333` | Channel/role create/delete/update, server settings, emojis |
| 4️⃣ | **Ticket Logs** | `1438487366305190018` | Ticket creation, closure, claims, assignments |
| 5️⃣ | **Moderation Logs** | `1444013659134361703` | Bans, kicks, timeouts, warnings, appeals, points |
| 6️⃣ | **Other Logs** | `1454024682700537968` | Voice activity, staff shifts, misc events |

---

## 📊 Event Routing Details

### 1️⃣ Message Logs Channel
**Events:**
- `MESSAGE_EDIT` - Message edits with before/after content
- `MESSAGE_DELETE` - Message deletions with moderator info
- `MESSAGE_BULK_DELETE` - Bulk purges/message cleanups

### 2️⃣ Member Logs Channel
**Events:**
- `MEMBER_JOIN` - Member joins server
- `MEMBER_LEAVE` - Member leaves server
- `MEMBER_JOIN_BOT` - Bot joins server
- `ROLE_ADD` - Role added to member
- `ROLE_REMOVE` - Role removed from member
- `NICKNAME_UPDATE` - Nickname changes

### 3️⃣ Server Logs Channel
**Events:**
- `CHANNEL_CREATE` - New channel created
- `CHANNEL_DELETE` - Channel deleted
- `CHANNEL_UPDATE` - Channel modified (name/topic/permissions)
- `ROLE_CREATE` - New role created
- `ROLE_DELETE` - Role deleted
- `ROLE_UPDATE` - Role modified (name/color/permissions)
- `GUILD_UPDATE` - Server settings changed (name/icon/verification)
- `EMOJI_UPDATE` - Emojis added/removed

### 4️⃣ Ticket Logs Channel
**Events:**
- `TICKET_CREATE` - Ticket opened
- `TICKET_CLOSE` - Ticket closed
- `TICKET_REOPEN` - Ticket reopened
- `TICKET_CLAIM` - Staff claims ticket
- `TICKET_ASSIGN` - Ticket assigned to staff

### 5️⃣ Moderation Logs Channel
**Events:**
- `BAN` - Member banned
- `UNBAN` - Member unbanned
- `KICK` - Member kicked
- `WARN` - Warning issued
- `TIMEOUT` - Member timed out
- `TIMEOUT_REMOVED` - Timeout removed
- `MUTE` / `UNMUTE` - Voice mute changes
- `POINT_CHANGE` - Staff points changed
- `APPEAL_*` - Appeal submitted/approved/denied

### 6️⃣ Other Logs Channel
**Events:**
- `VOICE_JOIN` - User joins voice channel
- `VOICE_LEAVE` - User leaves voice channel
- `VOICE_MOVE` - User moves between channels
- `VOICE_MUTE` / `VOICE_UNMUTE` - Voice mute state
- `VOICE_DEAFEN` / `VOICE_UNDEAFEN` - Voice deafen state
- `STAFF_SHIFT_START` / `STAFF_SHIFT_END` - Staff shift tracking
- Any other misc events

---

## 🔄 Managing Configuration

### View Current Setup
```
!setlogchannels
```

### Update Specific Channels
```
!setlogchannels #new-message-logs #new-member-logs #new-server-logs #new-ticket-logs #new-mod-logs #new-other-logs
```

### Update Just One Channel Type
To update just one channel while keeping others:
```
!setlogchannels #new-message-logs
```
This updates only message logs, keeping all others unchanged.

---

## ⚙️ Technical Details

### Database Schema
```sql
CREATE TABLE guild_log_channels (
    guild_id INTEGER PRIMARY KEY,
    message_log_channel_id INTEGER,
    member_log_channel_id INTEGER,
    server_log_channel_id INTEGER,
    ticket_log_channel_id INTEGER,
    mod_log_channel_id INTEGER,
    other_log_channel_id INTEGER,
    set_by INTEGER,
    set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Auto-Configuration
The channels for **The CodeVerse Hub** (ID: `1263067254153805905`) were automatically configured during bot initialization. This happens only once when the table is created.

---

## ✅ Verification Steps

1. **Check channels exist in Discord** - Verify all 6 channel IDs are valid
2. **Test with !setlogchannels** - Should show all 6 channels configured
3. **Verify bot permissions** - Bot needs:
   - View Channel
   - Send Messages
   - Embed Links
   - Read Message History
   - **View Audit Log** (critical for moderator attribution)
4. **Test logging** - Try actions like:
   - Edit/delete messages → Message logs
   - Add/remove roles → Member logs
   - Create/delete channels → Server logs
   - Open tickets → Ticket logs
   - Ban/kick users → Moderation logs
   - Join voice → Other logs

---

## 🆘 Troubleshooting

### "Logs not appearing"
1. Run `!setlogchannels` to verify configuration
2. Check bot has permissions in log channels
3. Check bot has "View Audit Log" permission
4. Check channel IDs are valid

### "Wrong channel receiving logs"
- Event routing is automatic based on event type
- Check [LOG CHANNEL CONFIGURATION] section above for routing rules
- Some events may fall under "Other Logs" if not explicitly categorized

### "Want to change channels"
```
!setlogchannels #new-msg #new-mem #new-srv #new-tkt #new-mod #new-other
```

---

## 📚 Additional Documentation

- [LOGGING_SYSTEM_DOCUMENTATION.md](./LOGGING_SYSTEM_DOCUMENTATION.md) - Complete event reference
- [LOGGING_QUICK_SETUP.md](./LOGGING_QUICK_SETUP.md) - Quick setup guide
- [LOGGING_IMPROVEMENTS_SUMMARY.md](./LOGGING_IMPROVEMENTS_SUMMARY.md) - Technical improvements

---

**Status:** ✅ Configured and Active
**Last Updated:** December 26, 2025
**Configuration:** Automatic (hardcoded for The CodeVerse Hub)
