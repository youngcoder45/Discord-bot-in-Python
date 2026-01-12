import discord
from discord.ext import commands
import asyncio
import logging

logger = logging.getLogger("codeverse.logging.channels")

class ChannelLogMixin(commands.Cog):
    async def log_event(self, event_type: str, user_id=None, guild_id=None, moderator_id=None, details=None, **kwargs):
        raise NotImplementedError("This method should be implemented by the host class")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        moderator_id = None
        try:
            await asyncio.sleep(0.5)
            async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_create, limit=5):
                if entry.target and entry.target.id == channel.id:
                    moderator_id = entry.user.id
                    break
        except Exception as e:
            logger.error(f"Error fetching audit logs for channel create: {e}")
        
        channel_type = str(channel.type).replace('_', ' ').title()
        await self.log_event(
            event_type="CHANNEL_CREATE",
            guild_id=channel.guild.id,
            moderator_id=moderator_id,
            details=f"Channel: {channel.mention}\nType: {channel_type}\nCategory: {channel.category.name if channel.category else 'None'}"
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        moderator_id = None
        try:
            await asyncio.sleep(0.5)
            async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=5):
                if entry.target and hasattr(entry.target, 'name') and entry.target.name == channel.name:
                    moderator_id = entry.user.id
                    break
        except Exception as e:
            logger.error(f"Error fetching audit logs for channel delete: {e}")
        
        channel_type = str(channel.type).replace('_', ' ').title()
        await self.log_event(
            event_type="CHANNEL_DELETE",
            guild_id=channel.guild.id,
            moderator_id=moderator_id,
            details=f"Channel Name: #{channel.name}\nType: {channel_type}\nCategory: {channel.category.name if channel.category else 'None'}"
        )

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        before_topic = getattr(before, "topic", None)
        after_topic = getattr(after, "topic", None)
        
        changes = []
        if before.name != after.name:
            changes.append(f"Name: `{before.name}` → `{after.name}`")
        if before_topic != after_topic:
            before_topic_val = before_topic or "(none)"
            after_topic_val = after_topic or "(none)"
            changes.append(f"Topic: `{before_topic_val[:100]}` → `{after_topic_val[:100]}`")
        if before.overwrites != after.overwrites:
             changes.append("Permissions Updated (Visibility/Access changed)")
        
        if not changes:
            return
            
        moderator_id = None
        try:
            await asyncio.sleep(0.5)
            # General Update
            async for entry in after.guild.audit_logs(action=discord.AuditLogAction.channel_update, limit=5):
                if entry.target and entry.target.id == after.id:
                    moderator_id = entry.user.id
                    break
            
            # If mod not found and perms changed, check overwrite logs
            if not moderator_id and "Permissions Updated (Visibility/Access changed)" in changes:
                async for entry in after.guild.audit_logs(action=discord.AuditLogAction.overwrite_update, limit=5):
                    if entry.target and entry.target.id == after.id:
                        moderator_id = entry.user.id
                        break
                if not moderator_id:
                    async for entry in after.guild.audit_logs(action=discord.AuditLogAction.overwrite_create, limit=5):
                        if entry.target and entry.target.id == after.id:
                            moderator_id = entry.user.id
                            break
                if not moderator_id:
                    async for entry in after.guild.audit_logs(action=discord.AuditLogAction.overwrite_delete, limit=5):
                        if entry.target and entry.target.id == after.id:
                            moderator_id = entry.user.id
                            break

        except Exception as e:
            logger.error(f"Error fetching audit logs for channel update: {e}")
        
        await self.log_event(
            event_type="CHANNEL_UPDATE",
            guild_id=after.guild.id,
            moderator_id=moderator_id,
            details=f"Channel: {after.mention}\n" + "\n".join(changes)
        )
