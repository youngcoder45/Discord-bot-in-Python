import discord
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class LogFormatter:
    """Handles formatting of log events into Embeds or text"""
    
    def __init__(self, bot):
        self.bot = bot

    async def create_log_embed(self, log_item: Dict[str, Any]) -> Optional[discord.Embed]:
        """Create an appropriate embed for the log item"""
        event_type = log_item.get("event_type", "UNKNOWN")
        
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
        user = None
        moderator = None
        
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
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} joined the server"
            embed.color = discord.Color(0x2B2D31) # Standard Dark
            
            # Add account creation date if available
            if isinstance(user, discord.User):
                account_age = (datetime.now(timezone.utc) - user.created_at).days
                embed.add_field(name="Account Age", value=f"{account_age} days", inline=True)
                embed.add_field(name="Created On", value=f"<t:{int(user.created_at.timestamp())}:F>", inline=True)
                
                if user.avatar:
                    embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("MEMBER_LEAVE"):
            embed.title = "Member Left"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} left the server"
            embed.color = discord.Color(0x2B2D31)
            
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("BAN"):
            embed.title = "Member Banned"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was banned"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
                
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("UNBAN"):
            embed.title = "Member Unbanned"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was unbanned"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
            
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("KICK"):
            embed.title = "Member Kicked"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was kicked"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
                
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("TIMEOUT") or event_type.startswith("MUTE"):
            if "APPLIED" in event_type:
                embed.title = "Member Timed Out"
                embed.description = f"{user.mention if isinstance(user, discord.User) else user} was timed out"
                embed.color = discord.Color(0x2B2D31)
                
                if moderator:
                    embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
                
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
                embed.description = f"{user.mention if isinstance(user, discord.User) else user}'s timeout naturally expired"
                embed.color = discord.Color(0x95a5a6)

                if details:
                    embed.add_field(name="Details", value=details, inline=False)
            elif "REMOVED" in event_type:
                embed.title = "Timeout Removed"
                embed.description = f"{user.mention if isinstance(user, discord.User) else user} had their timeout removed early"
                embed.color = discord.Color(0xff9900)

                if moderator:
                    embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)

                if details:
                    embed.add_field(name="Reason", value=details, inline=False)
            
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        
        elif event_type.startswith("WARN"):
            embed.title = "Warning Issued"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} was warned"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if "case_id" in log_item:
                case_id = log_item.get("case_id")
                embed.add_field(name="Case ID", value=f"#{case_id}", inline=True)
            
            if details:
                embed.add_field(name="Reason", value=details, inline=False)
                
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)

        elif "ROLE_UPDATE_MEMBER" in event_type or "ROLE_ADD" in event_type or "ROLE_REMOVE" in event_type:
            embed.title = "Role Updated"
            embed.description = f"Role change for {user.mention if isinstance(user, discord.User) else user}"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Updated By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
                
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)

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
            embed.description = f"Voice event for {user.mention if isinstance(user, discord.User) else user}"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)

        # Server/Channel Logs
        elif event_type.startswith("CHANNEL_CREATE"):
            embed.title = "Channel Created"
            embed.description = "A new channel was created"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Created By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type.startswith("CHANNEL_DELETE"):
            embed.title = "Channel Deleted"
            embed.description = "A channel was deleted"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Deleted By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type.startswith("CHANNEL_UPDATE"):
            embed.title = "Channel Updated"
            embed.description = "A channel was modified"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Updated By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Changes", value=details, inline=False)

        # Role Lifecycle
        elif event_type == "ROLE_CREATE":
            embed.title = "Role Created"
            embed.description = "A new role was created"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Created By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
        
        elif event_type == "ROLE_DELETE":
            embed.title = "Role Deleted"
            embed.description = "A role was deleted"
            embed.color = discord.Color(0x2B2D31)
            
            if moderator:
                embed.add_field(name="Deleted By", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)

        # Member Updates
        elif event_type.startswith("NICKNAME_"):
            embed.title = "Nickname Changed"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} changed nickname"
            embed.color = discord.Color(0x2B2D31)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
                
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)

        elif event_type.startswith("USER_UPDATE"):
            embed.title = "Username Changed"
            embed.description = f"{user.mention if isinstance(user, discord.User) else user} changed username"
            embed.color = discord.Color(0x2B2D31)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
                
            if isinstance(user, discord.User) and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)

        else:
            # Default
            embed.title = f"{event_type.replace('_', ' ').title()}"
            embed.description = details if details else "No details provided"
            embed.color = discord.Color(0x2B2D31)
            
            if user:
                embed.add_field(name="User", value=f"{user.mention if isinstance(user, discord.User) else user}", inline=True)
            
            if moderator:
                embed.add_field(name="Moderator", value=f"{moderator.mention if isinstance(moderator, discord.User) else moderator}", inline=True)
        
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
