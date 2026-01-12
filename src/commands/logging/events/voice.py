import discord
from discord.ext import commands
import asyncio
import logging

logger = logging.getLogger("codeverse.logging.voice")

class VoiceLogMixin(commands.Cog):
    async def log_event(self, event_type: str, user_id=None, guild_id=None, moderator_id=None, details=None, **kwargs):
        raise NotImplementedError("Implemented in host class")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.guild:
            return
            
        # MUTE / DEAFEN - Only if by moderator
        
        # MUTE
        if before.mute != after.mute and not before.self_mute and not after.self_mute:
            moderator_id = None
            try:
                await asyncio.sleep(0.5)
                async for entry in member.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=10):
                    if entry.target and entry.target.id == member.id:
                        if entry.user and entry.user.id != member.id:
                            moderator_id = entry.user.id
                            break
            except Exception as e:
                logger.error(f"Error fetching audit logs for voice mute: {e}")
            
            if moderator_id:
                event_type = "VOICE_MUTE" if after.mute else "VOICE_UNMUTE"
                channel = after.channel or before.channel
                details = f"{'Muted' if after.mute else 'Unmuted'} in {channel.mention if channel else 'voice'}"
                
                await self.log_event(
                    event_type=event_type,
                    user_id=member.id,
                    guild_id=member.guild.id,
                    moderator_id=moderator_id,
                    details=details
                )

        # DEAFEN
        if before.deaf != after.deaf and not before.self_deaf and not after.self_deaf:
            moderator_id = None
            try:
                await asyncio.sleep(0.5)
                async for entry in member.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=10):
                    if entry.target and entry.target.id == member.id:
                        if entry.user and entry.user.id != member.id:
                            moderator_id = entry.user.id
                            break
            except Exception as e:
                logger.error(f"Error fetching audit logs for voice deafen: {e}")
            
            if moderator_id:
                event_type = "VOICE_DEAFEN" if after.deaf else "VOICE_UNDEAFEN"
                channel = after.channel or before.channel
                details = f"{'Deafened' if after.deaf else 'Undeafened'} in {channel.mention if channel else 'voice'}"
                
                await self.log_event(
                    event_type=event_type,
                    user_id=member.id,
                    guild_id=member.guild.id,
                    moderator_id=moderator_id,
                    details=details
                )

        # DISCONNECT / MOVE
        if before.channel != after.channel:
            # Check for Move or Disconnect
            if before.channel and not after.channel:
                # Disconnect
                 moderator_id = None
                 try:
                    await asyncio.sleep(0.5)
                    async for entry in member.guild.audit_logs(action=discord.AuditLogAction.member_disconnect, limit=10):
                        if entry.target and entry.target.id == member.id:
                            if entry.user and entry.user.id != member.id:
                                moderator_id = entry.user.id
                                break
                 except Exception: pass
                 
                 if moderator_id:
                     await self.log_event(
                        event_type="VOICE_DISCONNECT",
                        user_id=member.id,
                        guild_id=member.guild.id,
                        moderator_id=moderator_id,
                        details=f"Disconnected from {before.channel.mention}"
                     )

            elif before.channel and after.channel:
                # Move
                 moderator_id = None
                 try:
                    await asyncio.sleep(0.5)
                    async for entry in member.guild.audit_logs(action=discord.AuditLogAction.member_move, limit=10):
                        if entry.target and entry.target.id == member.id:
                            if entry.user and entry.user.id != member.id:
                                moderator_id = entry.user.id
                                break
                 except Exception: pass
                 
                 if moderator_id:
                     await self.log_event(
                        event_type="VOICE_MOVE",
                        user_id=member.id,
                        guild_id=member.guild.id,
                        moderator_id=moderator_id,
                        details=f"Moved from {before.channel.mention} to {after.channel.mention}"
                     )
