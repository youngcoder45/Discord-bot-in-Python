import discord
from discord.ext import commands
import asyncio
import logging

class ModerationLogMixin(commands.Cog):
    async def log_event(self, event_type: str, user_id=None, guild_id=None, moderator_id=None, details=None, **kwargs):
        raise NotImplementedError("Implemented in host class")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await asyncio.sleep(1)
        reason = "No reason provided"
        moderator_id = None
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
        await asyncio.sleep(1)
        reason = "No reason provided"
        moderator_id = None
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
                await self.log_event(
                    event_type="KICK",
                    user_id=entry.target.id,
                    guild_id=entry.guild.id,
                    moderator_id=entry.user.id if entry.user else None,
                    details=entry.reason or "No reason provided"
                )
