import discord
from discord.ext import commands
import asyncio
import logging

logger = logging.getLogger("codeverse.logging.roles")

class RoleLogMixin(commands.Cog):
    async def log_event(self, event_type: str, user_id=None, guild_id=None, moderator_id=None, details=None, **kwargs):
        raise NotImplementedError("Implemented in host class")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        moderator_id = None
        try:
            await asyncio.sleep(0.5)
            async for entry in role.guild.audit_logs(action=discord.AuditLogAction.role_create, limit=5):
                if entry.target and entry.target.id == role.id:
                    moderator_id = entry.user.id
                    break
        except Exception as e:
            logger.error(f"Error fetching audit logs for role create: {e}")
        
        await self.log_event(
            event_type="ROLE_CREATE",
            guild_id=role.guild.id,
            moderator_id=moderator_id,
            details=f"Role: {role.mention}\nColor: {str(role.color)}\nHoisted: {role.hoist}\nMentionable: {role.mentionable}"
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        moderator_id = None
        try:
            await asyncio.sleep(0.5)
            async for entry in role.guild.audit_logs(action=discord.AuditLogAction.role_delete, limit=5):
                if entry.target and entry.target.id == role.id:
                    moderator_id = entry.user.id
                    break
        except Exception as e:
            logger.error(f"Error fetching audit logs for role delete: {e}")
        
        await self.log_event(
            event_type="ROLE_DELETE",
            guild_id=role.guild.id,
            moderator_id=moderator_id,
            details=f"Role Name: {role.name}\nColor: {str(role.color)}"
        )
