# Moderation Points System

A structured monthly point-based moderation escalation with two-step ban approval.

## Core Rules
- Each user has 0–100 moderation points per month (period = YYYY-MM).
- Points reset automatically when a new month begins (first access triggers reset).
- Staff add points for rule violations via `/addpoints`.
- At **100 points**, user enters a PENDING BAN state instead of instant ban.
- A ban requires **two distinct moderators** with `ban_members` permission to approve.
- User is DM'd when a pending ban is created (best effort).
- If a pending ban is declined, their points drop to a fallback value (default 80) and status clears.

## Database Tables
```
mod_points(guild_id, user_id, points, period, last_updated)
mod_point_bans(id, guild_id, user_id, created_at, reason, points_at_creation, status, approver_one, approver_two, finalized_at)
mod_point_config(guild_id, fallback_points)
```

Statuses: `PENDING`, `APPROVED`, `CANCELLED`.

## Commands
| Command | Permission | Description |
|---------|------------|-------------|
| `/addpoints <user> <amount> [reason]` | moderate_members | Adds points; may trigger pending ban panel |
| `/points [user]` | none | Shows current points and pending status |
| `/pendingbans` | moderate_members | Lists all active pending bans |
| `/approveban <user>` | ban_members | Approve a pending ban (step 1 or 2) |
| `/declineban <user>` | ban_members | Decline and reduce points to fallback |

### Interactive Approval Panel
When a user reaches 100 points:
- Bot sends an embed + buttons (Approve / Decline).
- First approval marks partial.
- Second approval executes ban (DM attempt + mod case logged).
- Decline: cancels, reduces points to fallback, logs cancellation.

## Logging
Actions recorded into `mod_cases`:
- `POINTS` (+N -> total)
- `POINTBAN` (final approved ban)
- `POINTBAN-CANCEL` (declined pending ban)

## Fallback Behavior
- Default fallback after decline: 80 points (config table allows future customization).
- Prevents immediate re-trigger unless further violations occur.

## Edge Cases & Safeguards
- Adding non-positive points is ignored with a warning.
- If a pending ban already exists, further cap-reaching additions do not recreate it.
- If member leaves before approval, second approval still finalizes record (ban attempt silently ignored).
- DM failures are silently ignored to prevent blocking workflow.

## Potential Future Enhancements
- Configurable required approvals (default 2).
- Subtract / set points commands.
- Scheduled summary reports to staff channel.
- Appeal integration bridging `appeals` cog.
- Web dashboard or CSV export.

## Developer Notes
- All DB writes are synchronous SQLite; low volume acceptable.
- Period checked on each access rather than cron job.
- Buttons timeout after 48h, but command approvals continue to work.

---
**Status:** Implemented and active.
