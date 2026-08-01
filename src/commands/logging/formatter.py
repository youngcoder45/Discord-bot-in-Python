import discord  # type: ignore[import-not-found]
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class LogFormatter:
    """Handles formatting of log events into Embeds or text"""
    
    def __init__(self, bot):
        self.bot = bot

    async def create_log_embed(self, log_item: Dict[str, Any]) -> Optional[discord.Embed]:
        """Create an appropriate embed for the log item"""
        event_type = log_item.get("event_type", "UNKNOWN")

        def _fmt_mention(obj: Any) -> str:
            mention = getattr(obj, "mention", None)
            if isinstance(mention, str):
                return mention
            if obj is None:
                return "Unknown User"
            return str(obj)

        def _avatar_url(obj: Any) -> Optional[str]:
            avatar = getattr(obj, "avatar", None)
            url = getattr(avatar, "url", None)
            return url if isinstance(url, str) else None

        def _created_at(obj: Any) -> Optional[datetime]:
            created_at = getattr(obj, "created_at", None)
            return created_at if isinstance(created_at, datetime) else None
        
        # Tickets -> Return None to signal "No Embed" if configured, 
        # BUT the caller needs to know it's a no-embed text message.
        # Actually, if I return None here, the caller might skip sending.
        # I should probably return a special object or Handle this in the caller.
        # For now, I will format embeds for everything, and the caller handles "no embed" logic 
        # by checking if it's a ticket event. 
        # OR I can return a minimal embed? No, User said "no embed logs anywhere all will be webhook".
        # This implies standard text message via webhook.
        if event_type.startswith("TICKET_"):
            return None 

        user_id = log_item.get("user_id")
        details = log_item.get("details", "")
        moderator_id = log_item.get("moderator_id")
        timestamp = log_item.get("timestamp", datetime.now(timezone.utc))
        
        # Resolve user and moderator objects
        user: Any = None
        moderator: Any = None
        
        if user_id:
            try:
                user = await self.bot.fetch_user(user_id)
            except:
                user = f"Unknown User ({user_id})"
        
        if moderator_id:
            try:
                moderator = await self.bot.fetch_user(moderator_id)
            except:
                moderator = f"Unknown Moderator ({moderator_id})"
        
        # Base embed with timestamp
        embed = discord.Embed(timestamp=timestamp)
        
        # Configure embed based on event type
        if event_type.startswith("MEMBER_JOIN"):
            embed.title = "Member Joined"
            embed.description = f"{_fmt_mention(user)} joined the server"
            embed.color = discord.Color(0x2B2D31) # Standard Dark
            
            # Add account creation date if available
            created_at = _created_at(user)
            if created_at is not None:
                account_age = (datetime.now(timezone.utc) - created_at).days
                embed.add_field(name="Account Age", value=f"{account_age} days", inline=True)
                embed.add_field(name="Created On", value=f"<t:{int(created_at.timestamp())}:F>", inline=True)

                avatar_url = _avatar_url(user)
                if avatar_url:
                    embed.set_thumbnail(url=avatar_url)
        
        elif event_type.startswith("MEMBER_LEAVE"):
            embed.title = "Member Left"
            embed.description = f"{_fmt_mention(user)} left the server"
            embed.color = discord.Color(0x2B2D31)
            
            avatar_url = _avatar_url(user)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
        
        elif event_type == "EXTERNAL_LOG":
            # For logs coming from external modules like SAM
            embed.title = log_item.get("title", "System Log")
            embed.description = log_item.get("description", details)
            
            # Allow custom color
            color_val = log_item.get("color")
            if color_val:
                try:
                    embed.color = discord.Color(color_val) if isinstance(color_val, int) else color_val
                except:
                    embed.color = discord.Color.blue()
            else:
                embed.color = discord.Color.blue()
                
            # Add fields if provided
            fields = log_item.get("fields", [])
            for field in fields:
                # Handle both object and dict styles if possible, but bridge sends objects usually. 
                # bridge.py sends 'fields' which are objects with name/value/inline
                name = getattr(field, 'name', None) or field.get('name')
                value = getattr(field, 'value', None) or field.get('value')
                inline = getattr(field, 'inline', True) if hasattr(field, 'inline') else field.get('inline', True)
                
                if name and value:
                    embed.add_field(name=str(name), value=str(value), inline=inline)

        elif event_type.startswith("APPEAL_"):
            decision = event_type.removeprefix("APPEAL_").title()
            color_map = {
                "SUBMITTED": 0x2B2D31,
                "APPROVED": 0x00FF00,
                "DENIED": 0xFF0000,
                "EXTENDED": 0x2B2D31,
            }
            embed.title = f"Appeal {decision}"
            embed.description = log_item.get(
                "description",
                f"Appeal activity recorded for #{log_item.get('fields', [{}])[0].get('value', 'unknown')}",
            )
            embed.color = discord.Color(color_map.get(decision.upper(), 0x5865F2))
            fields = log_item.get("fields", [])
            for field in fields:
                name = getattr(field, "name", None) or field.get("name")
                value = getattr(field, "value", None) or field.get("value")
                inline = getattr(field, "inline", True) if hasattr(field, "inline") else field.get("inline", True)
                if name and value:
                    embed.add_field(name=str(name), value=str(value), inline=inline)

            if moderator:
                embed.add_field(name="Moderator", value=_fmt_mention(moderator), inline=True)

            jump_url = log_item.get("jump_url")
            if jump_url:
                embed.add_field(name="Jump URL", value=str(jump_url), inline=False)

        elif event_type.startswith("BAN"):
            embed.title = "Member Banned"
            embed.description = f"{_fmt_mention(user)} was banned"
            embed.color = discord.Color(0x2B2D31)
            
            if user_id:
                embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
            
            if moderator:
                embed.add_field(name="Moderator", value=_fmt_mention(moderator), inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
                
            avatar_url = _avatar_url(user)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
        
        elif event_type.startswith("UNBAN"):
            embed.title = "Member Unbanned"
            embed.description = f"{_fmt_mention(user)} was unbanned"
            embed.color = discord.Color(0x2B2D31)
            
            if user_id:
                embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
            
            if moderator:
                embed.add_field(name="Moderator", value=_fmt_mention(moderator), inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
            
            avatar_url = _avatar_url(user)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
        
        elif event_type.startswith("KICK"):
            embed.title = "Member Kicked"
            embed.description = f"{_fmt_mention(user)} was kicked"
            embed.color = discord.Color(0x2B2D31)
            
            if user_id:
                embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
            
            if moderator:
                embed.add_field(name="Moderator", value=_fmt_mention(moderator), inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
                
            avatar_url = _avatar_url(user)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
        
        elif event_type.startswith("TIMEOUT") or event_type.startswith("MUTE"):
            if "APPLIED" in event_type:
                embed.title = "Member Timed Out"
                embed.description = f"{_fmt_mention(user)} was timed out"
                embed.color = discord.Color(0x2B2D31)
                
                if moderator:
                    embed.add_field(name="Moderator", value=_fmt_mention(moderator), inline=True)
                
                if "duration" in log_item:
                    duration = log_item.get("duration", "Unknown")
                    embed.add_field(name="Duration", value=duration, inline=True)
                    
                if "expires" in log_item:
                    expires = log_item.get("expires")
                    if expires:
                        embed.add_field(name="Expires", value=f"<t:{int(expires.timestamp())}:R>", inline=True)
                
                if details:
                    embed.add_field(name="Reason", value=details, inline=False)
            elif "EXPIRED" in event_type:
                embed.title = "Timeout Expired"
                embed.description = f"{_fmt_mention(user)}'s timeout naturally expired"
                embed.color = discord.Color(0xF9F504)

                if details:
                    embed.add_field(name="Details", value=details, inline=False)
            elif "REMOVED" in event_type:
                embed.title = "Timeout Removed"
                if log_item.get("source") == "appeal":
                    embed.description = f"{_fmt_mention(user)}'s timeout was removed via an approved appeal"
                else:
                    embed.description = f"{_fmt_mention(user)} had their timeout removed manually"
                embed.color = discord.Color(0xF9F504)

                if moderator:
                    embed.add_field(name="Moderator", value=_fmt_mention(moderator), inline=True)

                if details:
                    embed.add_field(name="Reason", value=details, inline=False)
            
            avatar_url = _avatar_url(user)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
        
        elif event_type.startswith("WARN"):
            embed.title = "Warning Issued"
            embed.description = f"{_fmt_mention(user)} was warned"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Moderator", value=_fmt_mention(moderator), inline=True)
            
            if "case_id" in log_item:
                case_id = log_item.get("case_id")
                embed.add_field(name="Case ID", value=f"#{case_id}", inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
                
            avatar_url = _avatar_url(user)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)

        elif "ROLE_UPDATE_MEMBER" in event_type or "ROLE_ADD" in event_type or "ROLE_REMOVE" in event_type:
            embed.title = "Role Updated"
            embed.description = f"Role change for {_fmt_mention(user)}"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Updated By", value=_fmt_mention(moderator), inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
                
            avatar_url = _avatar_url(user)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)

        # Voice Logs
        elif event_type.startswith("VOICE_"):
            title_map = {
                "VOICE_MUTE": "Voice Server Muted",
                "VOICE_UNMUTE": "Voice Server Unmuted",
                "VOICE_DEAFEN": "Voice Server Deafened",
                "VOICE_UNDEAFEN": "Voice Server Undeafened",
                "VOICE_DISCONNECT": "Voice Disconnected",
                "VOICE_MOVE": "Voice Moved"
            }
            
            embed.title = title_map.get(event_type, "Voice Event")
            embed.description = f"Voice event for {_fmt_mention(user)}"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="By", value=_fmt_mention(moderator), inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)

        # Server/Channel Logs
        elif event_type.startswith("CHANNEL_CREATE"):
            embed.title = "Channel Created"
            embed.description = "A new channel was created"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Created By", value=_fmt_mention(moderator), inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type.startswith("CHANNEL_DELETE"):
            embed.title = "Channel Deleted"
            embed.description = "A channel was deleted"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Deleted By", value=_fmt_mention(moderator), inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type.startswith("CHANNEL_UPDATE"):
            embed.title = "Channel Updated"
            embed.description = "A channel was modified"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Updated By", value=_fmt_mention(moderator), inline=True)
            
            if details:
                embed.add_field(name="Changes", value=details, inline=False)

        # Role Lifecycle
        elif event_type == "ROLE_CREATE":
            embed.title = "Role Created"
            embed.description = "A new role was created"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Created By", value=_fmt_mention(moderator), inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type == "ROLE_DELETE":
            embed.title = "Role Deleted"
            embed.description = "A role was deleted"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Deleted By", value=_fmt_mention(moderator), inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)

        # Member Updates
        elif event_type.startswith("NICKNAME_"):
            embed.title = "Nickname Changed"
            embed.description = f"{_fmt_mention(user)} changed nickname"
            embed.color = discord.Color(0x2B2D31)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
                
            avatar_url = _avatar_url(user)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)

        elif event_type.startswith("USER_UPDATE"):
            embed.title = "Username Changed"
            embed.description = f"{_fmt_mention(user)} changed username"
            embed.color = discord.Color(0x2B2D31)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
                
            avatar_url = _avatar_url(user)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)

        else:
            # Default
            embed.title = f"{event_type.replace('_', ' ').title()}"
            embed.description = details if details else "No details provided"
            embed.color = discord.Color(0x2B2D31)
            
            if user:
                embed.add_field(name="User", value=_fmt_mention(user), inline=True)
            
            if moderator:
                embed.add_field(name="Moderator", value=_fmt_mention(moderator), inline=True)
        
        # Add footer with log ID if available
        if "log_id" in log_item:
            log_id = log_item.get("log_id")
            embed.set_footer(text=f"Log ID: {log_id}")
        else:
            embed.set_footer(text=f"Event: {event_type}")
        
        return embed

    async def create_log_message(self, log_item: Dict[str, Any]) -> str:
        """Create a text message for logs (mainly tickets)"""
        event_type = log_item.get("event_type", "UNKNOWN")
        details = log_item.get("details", "")
        # Very simple formatting for tickets
        return f"**{event_type}**\n{details}"
