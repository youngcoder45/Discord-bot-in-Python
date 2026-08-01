import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timezone
import logging

logger = logging.getLogger("codeverse.logging.members")

class MemberLogMixin(commands.Cog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Type hint for bot, expected to be injected
        self.bot: commands.Bot 

    async def log_event(self, event_type: str, user_id=None, guild_id=None, moderator_id=None, details=None, **kwargs):
        raise NotImplementedError("Implemented in host class")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            event_type = "MEMBER_JOIN_BOT"
        else:
            event_type = "MEMBER_JOIN"
            
        await self.log_event(
            event_type=event_type,
            user_id=member.id,
            guild_id=member.guild.id,
            details=f"Username: {member}"
        )
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.bot:
            event_type = "MEMBER_LEAVE_BOT" 
        else:
            event_type = "MEMBER_LEAVE"
            
        await self.log_event(
            event_type=event_type,
            user_id=member.id,
            guild_id=member.guild.id,
            details=f"Username: {member}"
        )

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Log member update events, focusing on roles and timeouts"""
        if after.bot:
            return
            
        # --- ROLES ---
        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            
            # Filter out roles that were deleted from the guild (avoids spam when a role is deleted)
            removed_roles = [role for role in removed_roles if after.guild.get_role(role.id) is not None]

            moderator_id = None
            if added_roles or removed_roles:
                registered = self._consume_pending_action(after.guild.id, after.id, "ROLE_ADD") or self._consume_pending_action(after.guild.id, after.id, "ROLE_REMOVE")
                if registered:
                    moderator_id, _ = registered
                else:
                    try:
                        await asyncio.sleep(0.5)
                        async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=10):
                            if entry.target and entry.target.id == after.id:
                                if entry.user:
                                    moderator_id = entry.user.id
                                break
                    except Exception as e:
                        logger.error(f"Error fetching audit log for role update: {e}")

                # Emit specific events for Add/Remove if possible, or mixed
                # User config asked for "all role addition/removing to a member logs in ..."
                # I'll log them as ROLE_ADD or ROLE_REMOVE if distinct, or ROLE_UPDATE_MEMBER
                
                if added_roles:
                    added_text = ", ".join(role.mention for role in added_roles)
                    await self.log_event(
                        event_type="ROLE_ADD", # Mapped to 1460207115082661984
                        user_id=after.id,
                        guild_id=after.guild.id,
                        moderator_id=moderator_id,
                        details=f"Added: {added_text}"
                    )

                if removed_roles:
                    removed_text = ", ".join(role.mention for role in removed_roles)
                    await self.log_event(
                        event_type="ROLE_REMOVE", # Mapped to 1460207115082661984
                        user_id=after.id,
                        guild_id=after.guild.id,
                        moderator_id=moderator_id,
                        details=f"Removed: {removed_text}"
                    )

        # --- NICKNAMES ---
        if before.nick != after.nick:
            moderator_id = None
            registered = self._consume_pending_action(after.guild.id, after.id, "NICKNAME_UPDATE")
            if registered:
                moderator_id, _ = registered
            else:
                try:
                    await asyncio.sleep(0.5)
                    async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=10):
                        if entry.target and entry.target.id == after.id:
                            if entry.user:
                                moderator_id = entry.user.id
                            break
                except Exception as e:
                    logger.error(f"Error fetching audit log for nickname update: {e}")
            
            old_nick = before.nick or before.name
            new_nick = after.nick or after.name
            
            await self.log_event(
                event_type="NICKNAME_UPDATE",
                user_id=after.id,
                guild_id=after.guild.id,
                moderator_id=moderator_id,
                details=f"**Before:** {old_nick}\n**After:** {new_nick}"
            )
        
        # --- TIMEOUTS ---
        before_timeout = getattr(before, 'timed_out_until', None)
        after_timeout = getattr(after, 'timed_out_until', None)
        
        before_timeout_active = before_timeout and before_timeout > datetime.now(timezone.utc)
        after_timeout_active = after_timeout and after_timeout > datetime.now(timezone.utc)
        
        if not before_timeout_active and after_timeout_active:
            # TIMEOUT APPLIED
            reason = "No reason provided"
            moderator_id = None
            registered = self._consume_pending_action(after.guild.id, after.id, "TIMEOUT_APPLIED")
            if registered:
                moderator_id, reason = registered
            else:
                try:
                    await asyncio.sleep(1)
                    async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=5):
                        if entry.target and entry.target.id == after.id:
                            if entry.reason:
                                reason = entry.reason
                                # Check for appended moderator info
                                if " | By: " in reason:
                                    try:
                                        parts = reason.split(" | By: ")
                                        reason = parts[0]
                                        mod_info = parts[1]
                                        if "(" in mod_info and ")" in mod_info:
                                            mod_id_str = mod_info.split("(")[1].split(")")[0]
                                            moderator_id = int(mod_id_str)
                                    except: pass
                            
                            if entry.user and not moderator_id:
                                moderator_id = entry.user.id
                            break
                except: pass
            
            duration = "Unknown"
            if after_timeout:
                delta = after_timeout - datetime.now(timezone.utc)
                hours, remainder = divmod(delta.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                if hours >= 24:
                    days, hours = divmod(hours, 24)
                    duration = f"{int(days)}d {int(hours)}h {int(minutes)}m"
                elif hours >= 1:
                    duration = f"{int(hours)}h {int(minutes)}m"
                else:
                    duration = f"{int(minutes)}m {int(seconds)}s"
            
            await self.log_event(
                event_type="TIMEOUT_APPLIED",
                user_id=after.id,
                guild_id=after.guild.id,
                moderator_id=moderator_id,
                details=reason,
                duration=duration,
                expires=after_timeout
            )
        
        elif before_timeout_active and not after_timeout_active:
            # TIMEOUT REMOVED / EXPIRED
            natural_expiry = before_timeout and before_timeout <= datetime.now(timezone.utc)
            reason = "Timeout expired naturally" if natural_expiry else "No reason provided"
            moderator_id = None

            registered = self._consume_pending_action(after.guild.id, after.id, "TIMEOUT_REMOVED")
            if registered:
                moderator_id, reason = registered
                natural_expiry = False
            elif not natural_expiry:
                try:
                    await asyncio.sleep(1)
                    async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=5):
                        if entry.target and entry.target.id == after.id:
                            if entry.reason:
                                reason = entry.reason
                                # Check for appended moderator info
                                if " | By: " in reason:
                                    try:
                                        parts = reason.split(" | By: ")
                                        reason = parts[0]
                                        mod_info = parts[1]
                                        if "(" in mod_info and ")" in mod_info:
                                            mod_id_str = mod_info.split("(")[1].split(")")[0]
                                            moderator_id = int(mod_id_str)
                                    except: pass

                            if entry.user and not moderator_id:
                                moderator_id = entry.user.id
                            break
                except Exception: pass
            
            await self.log_event(
                event_type="TIMEOUT_EXPIRED" if natural_expiry else "TIMEOUT_REMOVED",
                user_id=after.id,
                guild_id=after.guild.id,
                moderator_id=moderator_id,
                details=reason
            )

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if before.name != after.name:
            # Iterate guilds to find shared ones
            for guild in self.bot.guilds:
                if guild.get_member(after.id):
                    await self.log_event(
                        event_type="USER_UPDATE",
                        user_id=after.id,
                        guild_id=guild.id,
                        moderator_id=None,
                        details=f"**Before:** {before.name}\n**After:** {after.name}"
                    )
