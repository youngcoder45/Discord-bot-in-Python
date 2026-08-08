import discord
from discord.ext import commands
import asyncio
import logging
import time

class ModerationLogMixin(commands.Cog):
    async def log_event(self, event_type: str, user_id=None, guild_id=None, moderator_id=None, details=None, **kwargs):
        raise NotImplementedError("Implemented in host class")

    # -------- Command-Initiated Action Registry --------
    # When a moderation command (e.g. /ban or ?ban) performs an action, it
    # registers the real invoker here BEFORE calling the Discord API. The event
    # listeners below consume this registry first, so the logged moderator is
    # the actual command invoker instead of whatever Discord attributes in the
    # audit log (which is usually the bot application). Audit logs are only used
    # as a fallback for actions the bot did not initiate via a command.
    #
    # Registry keys: (guild_id, user_id, action_type)
    # Registry values: (moderator_id, reason, timestamp)

    def register_command_action(self, guild_id: int, user_id: int, moderator_id: int, reason: str, action_type: str, source=None):
        """Record a moderation action performed through a bot command so the
        log entry attributes it to the actual command invoker. `source` is an
        optional context flag (e.g. "appeal") describing how the action happened."""
        self._pending_mod_actions[(guild_id, user_id, action_type)] = (moderator_id, reason, time.time(), source)
        # Keep the registry bounded: prune stale entries that were never
        # consumed (e.g. if a gateway event was missed and never re-dispatched).
        if len(self._pending_mod_actions) > 64:
            cutoff = time.time() - 120
            self._pending_mod_actions = {
                key: entry for key, entry in self._pending_mod_actions.items()
                if entry[2] > cutoff
            }

    def discard_command_action(self, guild_id: int, user_id: int, action_type: str):
        """Remove a pending moderation action (e.g. after the API call failed)."""
        self._pending_mod_actions.pop((guild_id, user_id, action_type), None)

    def _consume_pending_action(self, guild_id: int, user_id: int, action_type: str):
        """Pop a command-initiated moderation action if present and fresh (< 2 min).

        Returns (moderator_id, reason, source) or None.
        """
        entry = self._pending_mod_actions.pop((guild_id, user_id, action_type), None)
        if entry and time.time() - entry[2] <= 120:
            return entry[0], entry[1], entry[3]
        return None

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        reason = "No reason provided"
        moderator_id = None
        registered = self._consume_pending_action(guild.id, user.id, "BAN")
        if registered:
            moderator_id, reason, _ = registered
        else:
            # Fallback only for actions not initiated through a bot command
            # (manual bans in Discord or bot-initiated bans). The bot will show
            # as the executor here, which is correct for those cases.
            await asyncio.sleep(1)
            try:
                async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=5):
                    if entry.target and entry.target.id == user.id:
                        if entry.reason: reason = entry.reason
                        if entry.user: moderator_id = entry.user.id
                        break
            except: pass
        
        await self.log_event(
            event_type="BAN",
            user_id=user.id,
            guild_id=guild.id,
            moderator_id=moderator_id,
            details=reason
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        reason = "No reason provided"
        moderator_id = None
        registered = self._consume_pending_action(guild.id, user.id, "UNBAN")
        if registered:
            moderator_id, reason, _ = registered
        else:
            await asyncio.sleep(1)
            try:
                async for entry in guild.audit_logs(action=discord.AuditLogAction.unban, limit=5):
                    if entry.target and entry.target.id == user.id:
                        if entry.reason: reason = entry.reason
                        if entry.user: moderator_id = entry.user.id
                        break
            except: pass
        
        await self.log_event(
            event_type="UNBAN",
            user_id=user.id,
            guild_id=guild.id,
            moderator_id=moderator_id,
            details=reason
        )

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry):
        # Handle kicks
        if entry.action == discord.AuditLogAction.kick:
            if entry.target and isinstance(entry.target, (discord.User, discord.Member)):
                registered = self._consume_pending_action(entry.guild.id, entry.target.id, "KICK")
                if registered:
                    moderator_id, reason, _ = registered
                else:
                    moderator_id = entry.user.id if entry.user else None
                    reason = entry.reason or "No reason provided"
                await self.log_event(
                    event_type="KICK",
                    user_id=entry.target.id,
                    guild_id=entry.guild.id,
                    moderator_id=moderator_id,
                    details=reason
                )
