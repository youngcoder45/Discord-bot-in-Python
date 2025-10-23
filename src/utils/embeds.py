import discord
from config import MODERATION_POINT_CAP, MODERATION_POINT_RESET_DAYS

def create_points_embed(guild_name: str, points: int, reason: str, total_points: int) -> discord.Embed:
    """Create embed for moderation points notification"""
    embed = discord.Embed(
        title="Moderation Notice",
        description=f"You have received **{points}** moderation points in **{guild_name}**.",
        color=0xf39c12
    )
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Current Points", value=f"{total_points}/{MODERATION_POINT_CAP}", inline=True)
    embed.add_field(name="Points Reset", value=f"In {MODERATION_POINT_RESET_DAYS} days", inline=True)
    embed.set_footer(text="Professional Moderation System")
    return embed

def create_ban_embed(guild_name: str, reason: str) -> discord.Embed:
    """Create embed for auto-ban notification"""
    embed = discord.Embed(
        title="Account Suspended",
        description=f"You have been banned from **{guild_name}** for reaching {MODERATION_POINT_CAP} moderation points.",
        color=0xe74c3c
    )
    embed.add_field(name="Final Violation", value=reason, inline=False)
    embed.add_field(name="Appeal Process", value="Reply to this message with your appeal to request an unban review.", inline=False)
    embed.set_footer(text="Professional Moderation System")
    return embed

def create_warning_embed(user: discord.Member, moderator: discord.Member, reason: str, points: int, total_points: int) -> discord.Embed:
    """Create embed for warning notification"""
    embed = discord.Embed(title='User Warning Issued', color=0xf39c12)
    embed.add_field(name='User', value=user.mention, inline=True)
    embed.add_field(name='Moderator', value=moderator.mention, inline=True)
    embed.add_field(name='Reason', value=reason, inline=False)
    embed.add_field(name='Points Added', value=str(points), inline=True)
    embed.add_field(name='Current Points', value=f'{total_points}/{MODERATION_POINT_CAP}', inline=True)
    return embed

def create_kick_embed(user: discord.Member, moderator: discord.Member, reason: str) -> discord.Embed:
    """Create embed for kick notification"""
    embed = discord.Embed(title='User Kicked', color=0xe67e22)
    embed.add_field(name='User', value=f'{user} ({user.id})', inline=True)
    embed.add_field(name='Moderator', value=moderator.mention, inline=True)
    embed.add_field(name='Reason', value=reason, inline=False)
    return embed

def create_ban_action_embed(user: discord.Member, moderator: discord.Member, reason: str) -> discord.Embed:
    """Create embed for ban action notification"""
    embed = discord.Embed(title='User Banned', color=0xe74c3c)
    embed.add_field(name='User', value=f'{user} ({user.id})', inline=True)
    embed.add_field(name='Moderator', value=moderator.mention, inline=True)
    embed.add_field(name='Reason', value=reason, inline=False)
    return embed

def create_unban_embed(user: discord.User, moderator: discord.Member, reason: str) -> discord.Embed:
    """Create embed for unban notification"""
    embed = discord.Embed(title='User Unbanned', color=0x2ecc71)
    embed.add_field(name='User', value=f'{user} ({user.id})', inline=True)
    embed.add_field(name='Moderator', value=moderator.mention, inline=True)
    embed.add_field(name='Reason', value=reason, inline=False)
    return embed

def create_mute_embed(user: discord.Member, moderator: discord.Member, duration: str, reason: str) -> discord.Embed:
    """Create embed for mute notification"""
    embed = discord.Embed(title='User Muted', color=0x95a5a6)
    embed.add_field(name='User', value=user.mention, inline=True)
    embed.add_field(name='Duration', value=duration, inline=True)
    embed.add_field(name='Moderator', value=moderator.mention, inline=True)
    embed.add_field(name='Reason', value=reason, inline=False)
    return embed

def create_unmute_embed(user: discord.Member, moderator: discord.Member, reason: str) -> discord.Embed:
    """Create embed for unmute notification"""
    embed = discord.Embed(title='User Unmuted', color=0x2ecc71)
    embed.add_field(name='User', value=user.mention, inline=True)
    embed.add_field(name='Moderator', value=moderator.mention, inline=True)
    embed.add_field(name='Reason', value=reason, inline=False)
    return embed

def create_purge_embed(amount: int, moderator: discord.Member, target_user: discord.Member | None = None) -> discord.Embed:
    """Create embed for purge notification"""
    embed = discord.Embed(title='Messages Purged', color=0x3498db)
    embed.add_field(name='Amount', value=str(amount), inline=True)
    embed.add_field(name='Moderator', value=moderator.mention, inline=True)
    if target_user:
        embed.add_field(name='Target User', value=target_user.mention, inline=True)
    return embed

def create_lockdown_embed(channel: discord.TextChannel, moderator: discord.Member) -> discord.Embed:
    """Create embed for lockdown notification"""
    embed = discord.Embed(title='Channel Locked', color=0xe74c3c)
    embed.add_field(name='Channel', value=channel.mention, inline=True)
    embed.add_field(name='Moderator', value=moderator.mention, inline=True)
    return embed

def create_unlock_embed(channel: discord.TextChannel, moderator: discord.Member) -> discord.Embed:
    """Create embed for unlock notification"""
    embed = discord.Embed(title='Channel Unlocked', color=0x2ecc71)
    embed.add_field(name='Channel', value=channel.mention, inline=True)
    embed.add_field(name='Moderator', value=moderator.mention, inline=True)
    return embed

def create_slowmode_embed(channel: discord.TextChannel, moderator: discord.Member, seconds: int) -> discord.Embed:
    """Create embed for slowmode notification"""
    embed = discord.Embed(title='Slowmode Updated', color=0x3498db)
    embed.add_field(name='Channel', value=channel.mention, inline=True)
    embed.add_field(name='Delay', value=f'{seconds} seconds', inline=True)
    embed.add_field(name='Moderator', value=moderator.mention, inline=True)
    return embed

def create_points_check_embed(user: discord.Member, points: int) -> discord.Embed:
    """Create embed for points check"""
    embed = discord.Embed(title='Moderation Points', color=0x3498db)
    embed.add_field(name='User', value=user.mention, inline=True)
    embed.add_field(name='Current Points', value=f'{points}/{MODERATION_POINT_CAP}', inline=True)
    status = 'Good Standing' if points < 50 else 'Warning' if points < 80 else 'Critical'
    embed.add_field(name='Status', value=status, inline=True)
    return embed

def create_points_cleared_embed(user: discord.Member, moderator: discord.Member, old_points: int, reason: str) -> discord.Embed:
    """Create embed for points cleared notification"""
    embed = discord.Embed(title='Points Cleared', color=0x2ecc71)
    embed.add_field(name='User', value=user.mention, inline=True)
    embed.add_field(name='Previous Points', value=str(old_points), inline=True)
    embed.add_field(name='Moderator', value=moderator.mention, inline=True)
    embed.add_field(name='Reason', value=reason, inline=False)
    return embed

def create_error_embed(title: str, description: str) -> discord.Embed:
    """Create error embed"""
    return discord.Embed(title=title, description=description, color=0xe74c3c)

def create_success_embed(title: str, description: str) -> discord.Embed:
    """Create success embed"""
    return discord.Embed(title=title, description=description, color=0x2ecc71)

def create_info_embed(title: str, description: str) -> discord.Embed:
    """Create info embed"""
    return discord.Embed(title=title, description=description, color=0x3498db)