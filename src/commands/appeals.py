import discord  # type: ignore[import-not-found]
from discord.ext import commands  # type: ignore[import-not-found]
from discord import app_commands  # type: ignore[import-not-found]
import sqlite3
import sys
import asyncio
import math
import re
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Literal

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import MODERATION_ROLE_ID

from utils.database import DATABASE_NAME, init_db
from utils.embeds import (
    create_error_embed as _base_create_error_embed,
    create_success_embed as _base_create_success_embed,
    create_info_embed as _base_create_info_embed,
)


def _appeals_footer_text(guild_name: str | None = None) -> str:
    return f"{guild_name} • Appeals" if guild_name else "Appeals"


def create_error_embed(title: str, description: str, guild_name: str | None = None) -> discord.Embed:
    embed = _base_create_error_embed(title, description)
    embed.set_footer(text=_appeals_footer_text(guild_name))
    embed.timestamp = datetime.now(timezone.utc)
    return embed


def create_success_embed(title: str, description: str, guild_name: str | None = None) -> discord.Embed:
    embed = _base_create_success_embed(title, description)
    embed.set_footer(text=_appeals_footer_text(guild_name))
    embed.timestamp = datetime.now(timezone.utc)
    return embed


def create_info_embed(title: str, description: str, guild_name: str | None = None) -> discord.Embed:
    embed = _base_create_info_embed(title, description)
    embed.set_footer(text=_appeals_footer_text(guild_name))
    embed.timestamp = datetime.now(timezone.utc)
    return embed


async def _safe_ctx_send(
    ctx: commands.Context,
    *,
    content: str | None = None,
    embed: discord.Embed | None = None,
    view: discord.ui.View | None = None,
    ephemeral: bool = False,
):
    send_kwargs: dict[str, Any] = {}
    if content is not None:
        send_kwargs["content"] = content
    if embed is not None:
        send_kwargs["embed"] = embed
    if view is not None:
        send_kwargs["view"] = view

    interaction = getattr(ctx, "interaction", None)
    if ephemeral and interaction is not None:
        try:
            return await interaction.response.send_message(**send_kwargs, ephemeral=True)
        except discord.InteractionResponded:
            return await interaction.followup.send(**send_kwargs, ephemeral=True)
    return await ctx.send(**send_kwargs)


def _format_relative(dt: Optional[datetime]) -> str:
    if dt is None:
        return "Unknown"
    return f"<t:{int(dt.timestamp())}:R> (<t:{int(dt.timestamp())}:F>)"


def _truncate(text: str, limit: int = 900) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _clean_reason(text: Optional[str]) -> str:
    if not text:
        return "No reason provided"
    text = str(text).strip()
    return text or "No reason provided"


@dataclass(slots=True)
class AppealRecord:
    appeal_id: int
    guild_id: int
    guild_name: str
    user_id: int
    username: str
    punishment_type: str
    punishment_reason: str
    timeout_issued_at: Optional[datetime]
    timeout_expires_at: Optional[datetime]
    appeal_reason: str
    should_remove: str
    appeal_learned: str
    appeal_extra: Optional[str]
    submitted_at: datetime
    status: str = "pending"
    review_channel_id: Optional[int] = None
    review_message_id: Optional[int] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_reason: Optional[str] = None
    jump_url: Optional[str] = None


class AppealModal(discord.ui.Modal):
    """Modal for collecting appeal information"""

    def __init__(self, cog, guild: discord.Guild, punishment_type: str, reason: str):
        super().__init__(title="Submit Your Appeal", timeout=300)
        self.cog = cog
        self.guild = guild
        self.punishment_type = punishment_type
        self.reason = reason

        # Question 1: What are you appealing?
        self.punishment_input = discord.ui.TextInput(
            label="What punishment are you appealing?",
            placeholder=f"e.g., {punishment_type} from {guild.name}",
            default=f"{punishment_type.title()} from {guild.name}",
            max_length=100,
            required=True
        )
        self.add_item(self.punishment_input)

        # Question 2: Why did you get punished?
        self.reason_input = discord.ui.TextInput(
            label="Why did you get this punishment?",
            placeholder="Brief explanation of what happened...",
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=True
        )
        self.add_item(self.reason_input)

        # Question 3: Your appeal message
        self.appeal_input = discord.ui.TextInput(
            label="Your appeal message",
            placeholder="Explain why this punishment should be removed, what you've learned, or what you'll do differently...",
            style=discord.TextStyle.paragraph,
            max_length=1500,
            required=True
        )
        self.add_item(self.appeal_input)

    def reappeal_limit_check(self, user_id: int) -> bool:
        """check if user reappealed 2 times this month"""
        if self.punishment_type.lower() not in ['ban', 'banned', 'timeout', 'timed out', 'mute']:
            return False

        current_time = datetime.now(timezone.utc)
        start_of_month = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        conn = sqlite3.connect(DATABASE_NAME)
        cur = conn.cursor()
        cur.execute('''
            SELECT COUNT(*) FROM unban_requests
            WHERE user_id = ? AND status = 'denied'
            AND timestamp >= ?
        ''', (user_id, start_of_month.strftime('%Y-%m-%d %H:%M:%S')))
        denied_count = cur.fetchone()[0]
        conn.close()

        return denied_count >= 2
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle appeal submission"""
        try:
            # CVH Policy: bans are not appealable via the bot.
            if self.punishment_type.lower() in ["ban", "banned"]:
                await interaction.response.send_message(
                    embed=create_error_embed(
                        "Ban Appeals Disabled",
                        "Ban appeals are not accepted via the bot. Only timeouts can be appealed.",
                        guild_name=self.guild.name,
                    ),
                    ephemeral=True,
                )
                return

            # Check if user still has punishment
            is_punished = await self._check_punishment_active(interaction.user)
            if not is_punished:
                await interaction.response.send_message(
                    embed=create_error_embed(
                        "Punishment Expired",
                        "Your punishment appears to have been lifted. No appeal is needed."
                    , guild_name=self.guild.name),
                    ephemeral=True
                )
                return

            # Check monthly reappeal limit for ban/timeout/mute appeals
            if self.reappeal_limit_check(interaction.user.id):
                await interaction.response.send_message(
                    embed=create_error_embed(
                        "Monthly Reappeal Limit Exceeded",
                        "You have reached the maximum of 2 reappeals per month for ban/timeout/mute appeals.\n\nPlease wait until next month to submit another appeal."
                    , guild_name=self.guild.name),
                    ephemeral=True
                )
                return

            # Create full appeal content
            appeal_content = (
                f"**Punishment Being Appealed:** {self.punishment_input.value}\n\n"
                f"**Why I think I was punished:** {self.reason_input.value}\n\n"
                f"**My Appeal:** {self.appeal_input.value}"
            )
            
            # Submit to database
            conn = sqlite3.connect(DATABASE_NAME)
            cur = conn.cursor()
            cur.execute('INSERT INTO unban_requests (user_id, reason) VALUES (?, ?)', 
                       (interaction.user.id, appeal_content))
            conn.commit()
            appeal_id = cur.lastrowid
            conn.close()
            
            print(f"[Appeals] Appeal #{appeal_id} submitted by {interaction.user} ({interaction.user.id}) - {self.punishment_type} in {self.guild.name}")
            
            # Send confirmation to user
            success_embed = create_success_embed(
                "Appeal Submitted",
                "Your appeal has been submitted to our moderation team.",
                guild_name=self.guild.name,
            )
            success_embed.add_field(name="Appeal ID", value=f"#{appeal_id}", inline=True)
            success_embed.add_field(name="Status", value="Pending review", inline=True)
            success_embed.add_field(name="Estimated review time", value="24-48 hours", inline=True)
            
            await interaction.response.send_message(embed=success_embed)
            
            # Send to staff channel
            if appeal_id:
                await self._send_staff_notification(appeal_id, interaction.user, appeal_content)
            
        except Exception as e:
            print(f"[Appeals] Error submitting appeal: {e}")
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Submission Error",
                    "There was an error submitting your appeal. Please try again later."
                , guild_name=self.guild.name),
                ephemeral=True
            )
    
    async def _check_punishment_active(self, user: discord.Member | discord.User) -> bool:
        """Check if user still has active punishment"""
        try:
            # Check if banned
            try:
                await self.guild.fetch_ban(discord.Object(id=user.id))
                return True
            except discord.NotFound:
                pass
            
            # Check if timed out
            member = self.guild.get_member(user.id)
            if member and getattr(member, 'timed_out_until', None):
                timeout_until = member.timed_out_until
                if timeout_until and timeout_until > datetime.now(timezone.utc):
                    return True
            
            return False
        except Exception:
            return True  # Assume still punished on error
    
    async def _send_staff_notification(self, appeal_id: int, user: discord.Member | discord.User, content: str):
        """Send appeal notification to staff channel"""
        staff_channel = None
        for cid in (1423642446616592385, 1444013659134361703):
            ch = self.cog.bot.get_channel(cid)
            if ch:
                staff_channel = ch
                break
        
        if staff_channel:
            staff_embed = discord.Embed(
                title="New Appeal Submitted",
                description=f"Appeal #{appeal_id} from {user}",
                color=0x0000ff
            )
            trimmed = content[:800] + ("..." if len(content) > 800 else "")
            staff_embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
            staff_embed.add_field(name="Punishment", value=f"{self.punishment_type.title()} in {self.guild.name}", inline=True)
            staff_embed.add_field(name="Appeal", value=f"```{trimmed}```", inline=False)
            staff_embed.add_field(name="Review", value="Use the buttons below to approve or deny this appeal.", inline=False)
            
            # Create view with approve/deny buttons
            view = AppealReviewView(self.cog, appeal_id, user.id, content, self.punishment_type, self.guild.name)
            staff_embed.set_footer(text=_appeals_footer_text(self.guild.name))
            staff_embed.timestamp = datetime.now(timezone.utc)
            
            try:
                allowed_mentions = discord.AllowedMentions(everyone=True, users=False, roles=False, replied_user=False)
                await staff_channel.send(content="@here", embed=staff_embed, view=view, allowed_mentions=allowed_mentions)
            except Exception as e:
                print(f"[Appeals] Failed to send staff notification: {e}")


class AppealApproveModal(discord.ui.Modal):
    """Modal for staff to provide approval reason"""
    
    def __init__(self, cog, appeal_id: int, user_id: int, punishment_type: str, guild_name: str):
        super().__init__(title=f"Approve Appeal #{appeal_id}", timeout=300)
        self.cog = cog
        self.appeal_id = appeal_id
        self.user_id = user_id
        self.punishment_type = punishment_type
        self.guild_name = guild_name
        
        self.reason_input = discord.ui.TextInput(
            label="Approval Reason",
            placeholder="Brief note explaining why this appeal was approved...",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            default="Appeal approved",
            required=True
        )
        self.add_item(self.reason_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process appeal approval"""
        try:
            await interaction.response.defer()
            
            # Check role permission
            if not isinstance(interaction.user, discord.Member) or not any(role.id == 1403059755001577543 for role in interaction.user.roles):
                await interaction.followup.send(
                    embed=create_error_embed("Permission Denied", "You don't have permission to approve appeals."),
                    ephemeral=True
                )
                return
            
            reason = self.reason_input.value
            
            # Process the approval (similar logic to old approve command)
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM unban_requests WHERE id = ? AND status = "pending"', (self.appeal_id,))
            result = cursor.fetchone()
            
            if not result:
                await interaction.followup.send(
                    embed=create_error_embed("Appeal Not Found", "Appeal not found or already processed."),
                    ephemeral=True
                )
                conn.close()
                return
            
            # Update appeal status
            cursor.execute('UPDATE unban_requests SET status = "approved" WHERE id = ?', (self.appeal_id,))
            conn.commit()
            conn.close()
            
            # Process punishment removal
            await self._process_appeal_approval(interaction, reason)
            
        except Exception as e:
            print(f"[Appeals] Error in approval modal: {e}")
            await interaction.followup.send(
                embed=create_error_embed("Processing Error", "There was an error processing the approval."),
                ephemeral=True
            )
    
    async def _process_appeal_approval(self, interaction: discord.Interaction, reason: str):
        """Handle the actual appeal approval process"""
        guild = interaction.guild
        member = guild.get_member(self.user_id) if guild else None
        user = None
        try:
            user = await self.cog.bot.fetch_user(self.user_id)
        except Exception:
            pass

        action_taken = None
        error_message = None

        if member:
            # User is in server - clear timeout if active
            try:
                if getattr(member, 'timed_out_until', None):
                    await member.timeout(None, reason=f"Appeal #{self.appeal_id} approved by {interaction.user}")
                    action_taken = "Timeout Cleared"
                else:
                    action_taken = "No Punishment Active"
            except discord.Forbidden:
                error_message = "I lack permission to modify this member's timeout."
            except Exception as e:
                error_message = f"Failed clearing timeout: {e}"
        else:
            # User not in guild - attempt unban
            try:
                if user is None or not guild:
                    raise ValueError("User fetch failed or guild not found; cannot unban")
                await guild.unban(user, reason=f'Appeal #{self.appeal_id} approved by {interaction.user}')
                action_taken = "User Unbanned"
            except discord.NotFound:
                error_message = "User not found or already unbanned."
            except discord.Forbidden:
                error_message = "I don't have permission to unban this user."
            except Exception as e:
                error_message = f"Error processing unban: {e}"

        # Clear points if punishment was lifted
        if action_taken in ("Timeout Cleared", "User Unbanned"):
            try:
                from utils.database import clear_user_points
                clear_user_points(self.user_id)
            except Exception:
                pass

        if error_message:
            await interaction.followup.send(
                embed=create_error_embed("Action Failed", error_message),
                ephemeral=True
            )
        else:
            # Send success message
            display_target = member or user or f"User {self.user_id}"
            embed = discord.Embed(title='Appeal Approved', color=0x00ff00)
            embed.add_field(name='Appeal ID', value=f"#{self.appeal_id}", inline=True)
            embed.add_field(name='User', value=f'{display_target} ({self.user_id})', inline=True)
            embed.add_field(name='Action', value=action_taken or 'Completed', inline=True)
            embed.add_field(name='Approved By', value=interaction.user.mention, inline=True)
            embed.add_field(name='Reason', value=reason, inline=False)
            embed.set_footer(text=_appeals_footer_text(guild.name if guild else None))
            embed.timestamp = datetime.now(timezone.utc)
            await interaction.followup.send(embed=embed)
            
            # Disable the buttons in the original message
            await self._disable_appeal_buttons(interaction)
            
            # DM user
            if user:
                try:
                    dm = discord.Embed(
                        title="Appeal Approved",
                        description=f"## Your appeal has been reviewed and **approved**\n\nWelcome back to **{guild.name if guild else 'the server'}**! We're glad to have you return.",
                        color=0x00ff00
                    )
                    dm.add_field(name="Appeal ID", value=f"`#{self.appeal_id}`", inline=True)
                    dm.add_field(name="Result", value=f"**{action_taken or 'Processed'}**", inline=True)
                    dm.add_field(name="Staff Response", value=f"```{reason}```", inline=False)
                    dm.add_field(
                        name="Moving Forward",
                        value="Please review our community guidelines and ensure compliance with all server rules. We appreciate your cooperation.",
                        inline=False
                    )
                    dm.set_footer(
                        text=f"{guild.name if guild else 'Server'} • Professional Moderation Team",
                        icon_url=guild.icon.url if guild and guild.icon else None
                    )
                    dm.set_thumbnail(url=guild.icon.url if guild and guild.icon else None)
                    await user.send(embed=dm)
                except Exception:
                    pass
    
    async def _disable_appeal_buttons(self, interaction: discord.Interaction):
        """Disable the appeal review buttons in the original message"""
        try:
            # Find the original message with the buttons by looking for the appeal ID in the embed
            channel = interaction.channel
            # Only iterate history on channel types that support it
            if channel and isinstance(channel, (discord.TextChannel, discord.Thread, discord.DMChannel)):
                async for message in channel.history(limit=50):
                    if (message.author.id == self.cog.bot.user.id and 
                        message.embeds and 
                        f"Appeal #{self.appeal_id}" in str(message.embeds[0].to_dict())):
                        
                        # Create disabled view
                        disabled_view = AppealReviewView(self.cog, self.appeal_id, self.user_id, 
                                                       "", self.punishment_type, self.guild_name)
                        
                        # Disable all buttons
                        for item in disabled_view.children:
                            if isinstance(item, discord.ui.Button):
                                item.disabled = True
                        
                        # Update the message with disabled buttons
                        await message.edit(view=disabled_view)
                        break
        except Exception as e:
            print(f"[Appeals] Failed to disable buttons: {e}")


class AppealDenyModal(discord.ui.Modal):
    """Modal for staff to provide denial reason"""
    
    def __init__(self, cog, appeal_id: int, user_id: int, punishment_type: str, guild_name: str):
        super().__init__(title=f"Deny Appeal #{appeal_id}", timeout=300)
        self.cog = cog
        self.appeal_id = appeal_id
        self.user_id = user_id
        self.punishment_type = punishment_type
        self.guild_name = guild_name
        
        self.reason_input = discord.ui.TextInput(
            label="Denial Reason",
            placeholder="Explain why this appeal was denied and what the user needs to improve...",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            default="Appeal denied - please review our community guidelines and submit a new appeal demonstrating understanding of the issue.",
            required=True
        )
        self.add_item(self.reason_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process appeal denial"""
        try:
            await interaction.response.defer()
            
            # Check role permission
            if not isinstance(interaction.user, discord.Member) or not any(role.id == 1403059755001577543 for role in interaction.user.roles):
                await interaction.followup.send(
                    embed=create_error_embed("Permission Denied", "You don't have permission to deny appeals."),
                    ephemeral=True
                )
                return
            
            reason = self.reason_input.value
            
            # Update database
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM unban_requests WHERE id = ? AND status = "pending"', (self.appeal_id,))
            result = cursor.fetchone()
            
            if not result:
                await interaction.followup.send(
                    embed=create_error_embed("Appeal Not Found", "Appeal not found or already processed."),
                    ephemeral=True
                )
                conn.close()
                return
            
            cursor.execute('UPDATE unban_requests SET status = "denied" WHERE id = ?', (self.appeal_id,))
            conn.commit()
            conn.close()
            
            # Send response
            embed = discord.Embed(title='Appeal Denied', color=0xff0000)
            embed.add_field(name='Appeal ID', value=f"#{self.appeal_id}", inline=True)
            embed.add_field(name='User ID', value=str(self.user_id), inline=True)
            embed.add_field(name='Denied By', value=interaction.user.mention, inline=True)
            embed.add_field(name='Reason', value=reason, inline=False)
            embed.set_footer(text=_appeals_footer_text(interaction.guild.name if interaction.guild else None))
            embed.timestamp = datetime.now(timezone.utc)
            await interaction.followup.send(embed=embed)
            
            # Disable the buttons in the original message
            await self._disable_appeal_buttons(interaction)
            
            # DM user
            try:
                user = await self.cog.bot.fetch_user(self.user_id)
                embed_dm = discord.Embed(
                    title="Appeal Denied",
                    description=f"## Your appeal has been reviewed\n\nAfter careful consideration, your appeal for **{interaction.guild.name if interaction.guild else 'the server'}** has been denied.",
                    color=0xff0000
                )
                embed_dm.add_field(name="Appeal ID", value=f"`#{self.appeal_id}`", inline=True)
                embed_dm.add_field(name="Reviewed By", value=str(interaction.user), inline=True)
                embed_dm.add_field(name="Staff Response", value=f"```{reason}```", inline=False)
                embed_dm.add_field(
                    name="Submit Another Appeal",
                    value="You may submit a new appeal after reflecting on the feedback provided. Click the button below to submit another appeal.",
                    inline=False
                )
                embed_dm.set_footer(
                    text=f"{interaction.guild.name if interaction.guild else 'Server'} • Professional Moderation Team",
                    icon_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None
                )
                embed_dm.set_thumbnail(url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None)
                
                # Create new appeal button for denied appeal
                if interaction.guild:
                    view = AppealButtonView(self.cog, interaction.guild, self.punishment_type, reason, self.user_id)
                    await user.send(embed=embed_dm, view=view)
                else:
                    await user.send(embed=embed_dm)
            except Exception:
                pass

        except Exception as e:
            print(f"[Appeals] Error in denial modal: {e}")
            await interaction.followup.send(
                embed=create_error_embed("Processing Error", "There was an error processing the denial."),
                ephemeral=True
            )
    
    async def _disable_appeal_buttons(self, interaction: discord.Interaction):
        """Disable the buttons in the original appeal message"""
        try:
            channel = interaction.channel
            if channel and isinstance(channel, (discord.TextChannel, discord.Thread, discord.DMChannel)):
                async for message in channel.history(limit=50):
                    if (message.author.id == self.cog.bot.user.id and 
                        message.embeds and 
                        f"Appeal #{self.appeal_id}" in str(message.embeds[0].to_dict())):
                        
                        # Create disabled view
                        disabled_view = AppealReviewView(self.cog, self.appeal_id, self.user_id, 
                                                       "", self.punishment_type, self.guild_name)
                        
                        # Disable all buttons
                        for item in disabled_view.children:
                            if isinstance(item, discord.ui.Button):
                                item.disabled = True
                        
                        # Update the message with disabled buttons
                        await message.edit(view=disabled_view)
                        break
        except Exception as e:
            print(f"[Appeals] Failed to disable buttons: {e}")


class AppealReviewView(discord.ui.View):
    """View with approve/deny buttons for staff"""
    
    def __init__(self, cog, appeal_id: int, user_id: int, appeal_content: str, punishment_type: str, guild_name: str):
        super().__init__(timeout=None)  # Persistent view
        self.cog = cog
        self.appeal_id = appeal_id
        self.user_id = user_id
        self.appeal_content = appeal_content
        self.punishment_type = punishment_type
        self.guild_name = guild_name
    
    async def _check_punishment_status(self, guild: discord.Guild) -> tuple[bool, str]:
        """Check if the punishment is still active. Returns (is_active, status_message)"""
        try:
            # Check if user is banned
            if self.punishment_type.lower() in ['ban', 'banned']:
                try:
                    await guild.fetch_ban(discord.Object(id=self.user_id))
                    return True, "User is still banned"
                except discord.NotFound:
                    return False, "User is no longer banned (ban was removed or expired)"
                except discord.Forbidden:
                    return True, "Cannot check ban status (insufficient permissions)"
            
            # Check if user is timed out
            elif self.punishment_type.lower() in ['timeout', 'mute', 'timed out']:
                member = guild.get_member(self.user_id)
                if not member:
                    return False, "User is no longer in the server"
                
                timeout_until = getattr(member, 'timed_out_until', None)
                if timeout_until and timeout_until > datetime.now(timezone.utc):
                    return True, f"User is still timed out until <t:{int(timeout_until.timestamp())}:F>"
                else:
                    return False, "User timeout has expired or was removed"
            
            # For other punishment types, assume they might still be valid
            else:
                return True, f"Cannot verify status of punishment type: {self.punishment_type}"
                
        except Exception as e:
            print(f"[Appeals] Error checking punishment status: {e}")
            return True, f"Error checking punishment status: {e}"
    
    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green, emoji=None)
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open approval modal"""
        # Check role permission
        if not isinstance(interaction.user, discord.Member) or not any(role.id == 1403059755001577543 for role in interaction.user.roles):
            await interaction.response.send_message(
                embed=create_error_embed("Permission Denied", "You don't have permission to approve appeals."),
                ephemeral=True
            )
            return
        
        # Check if punishment is still active
        if interaction.guild:
            is_active, status_msg = await self._check_punishment_status(interaction.guild)
            if not is_active:
                # Disable all buttons in this view
                for item in self.children:
                    if isinstance(item, discord.ui.Button):
                        item.disabled = True
                        item.label = "Appeal Resolved"
                
                # Update the message with disabled buttons
                try:
                    await interaction.response.edit_message(view=self)
                except discord.InteractionResponded:
                    await interaction.edit_original_response(view=self)
                
                # Log the auto-resolution
                try:
                    conn = sqlite3.connect(DATABASE_NAME)
                    cursor = conn.cursor()
                    cursor.execute('UPDATE unban_requests SET status = "auto_resolved" WHERE id = ?', (self.appeal_id,))
                    conn.commit()
                    conn.close()
                    print(f"[Appeals] Appeal #{self.appeal_id} auto-resolved and buttons disabled - {status_msg}")
                except Exception as e:
                    print(f"[Appeals] Error updating appeal status: {e}")
                
                return
        
        modal = AppealApproveModal(self.cog, self.appeal_id, self.user_id, self.punishment_type, self.guild_name)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, emoji=None)
    async def deny_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open denial modal"""
        # Check role permission
        if not isinstance(interaction.user, discord.Member) or not any(role.id == 1403059755001577543 for role in interaction.user.roles):
            await interaction.response.send_message(
                embed=create_error_embed("Permission Denied", "You don't have permission to deny appeals."),
                ephemeral=True
            )
            return
        
        # Check if punishment is still active
        if interaction.guild:
            is_active, status_msg = await self._check_punishment_status(interaction.guild)
            if not is_active:
                # Disable all buttons in this view
                for item in self.children:
                    if isinstance(item, discord.ui.Button):
                        item.disabled = True
                        item.label = "Appeal Resolved"
                
                # Update the message with disabled buttons
                try:
                    await interaction.response.edit_message(view=self)
                except discord.InteractionResponded:
                    await interaction.edit_original_response(view=self)
                
                # Log the auto-resolution
                try:
                    conn = sqlite3.connect(DATABASE_NAME)
                    cursor = conn.cursor()
                    cursor.execute('UPDATE unban_requests SET status = "auto_resolved" WHERE id = ?', (self.appeal_id,))
                    conn.commit()
                    conn.close()
                    print(f"[Appeals] Appeal #{self.appeal_id} auto-resolved and buttons disabled - {status_msg}")
                except Exception as e:
                    print(f"[Appeals] Error updating appeal status: {e}")
                
                return
        
        modal = AppealDenyModal(self.cog, self.appeal_id, self.user_id, self.punishment_type, self.guild_name)
        await interaction.response.send_modal(modal)


class AppealButtonView(discord.ui.View):
    """Legacy appeal button view."""
    
    def __init__(self, cog, guild: discord.Guild, punishment_type: str, reason: str, user_id: int):
        super().__init__(timeout=None)  # Persistent view
        self.cog = cog
        self.guild = guild
        self.punishment_type = punishment_type
        self.reason = reason
        self.user_id = user_id
    
    @discord.ui.button(label="📝 Submit Appeal", style=discord.ButtonStyle.primary, emoji=None)
    async def send_appeal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open appeal modal"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This button is not for you.", ephemeral=True
            )
            return

        # CVH Policy: bans are not appealable via the bot.
        if str(self.punishment_type).lower() in ["ban", "banned"]:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Ban Appeals Disabled",
                    "Ban appeals are not accepted via the bot. Only timeouts can be appealed.",
                    guild_name=self.guild.name,
                ),
                ephemeral=True,
            )
            return
        
        # Check if user already has a pending appeal
        conn = sqlite3.connect(DATABASE_NAME)
        cur = conn.cursor()
        cur.execute(
            'SELECT id FROM unban_requests WHERE user_id = ? AND guild_id = ? AND status = "pending"',
            (interaction.user.id, self.guild.id),
        )
        existing = cur.fetchone()
        conn.close()
        
        if existing:
            appeal_id = existing[0]
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Appeal Already Submitted",
                    f"You already have a pending appeal (#{appeal_id}). Please wait for staff review."
                ),
                ephemeral=True
            )
            return
        
        timeout_member = self.guild.get_member(interaction.user.id)
        timeout_until = getattr(timeout_member, "timed_out_until", None) if timeout_member else None
        temp_record = AppealRecord(
            appeal_id=0,
            guild_id=self.guild.id,
            guild_name=self.guild.name,
            user_id=self.user_id,
            username=str(interaction.user),
            punishment_type=self.punishment_type,
            punishment_reason=_clean_reason(self.reason),
            timeout_issued_at=None,
            timeout_expires_at=timeout_until if isinstance(timeout_until, datetime) else None,
            appeal_reason="Not submitted yet.",
            should_remove="Not submitted yet.",
            appeal_learned="Not submitted yet.",
            appeal_extra=None,
            submitted_at=datetime.now(timezone.utc),
            status="pending",
        )
        modal = AppealSubmissionModal(self.cog, temp_record, source_message=interaction.message)
        await interaction.response.send_modal(modal)


class AppealSubmissionDashboard(discord.ui.LayoutView):
    """Components V2 DM card shown to a punished user."""

    def __init__(
        self,
        cog: "Appeals",
        record: AppealRecord,
        *,
        can_submit: bool,
        disabled_reason: Optional[str] = None,
    ):
        super().__init__(timeout=None)
        self.cog = cog
        self.record = record
        self.can_submit = can_submit
        self.disabled_reason = disabled_reason
        self._render()

    def _icon_url(self) -> str:
        guild = self.cog.bot.get_guild(self.record.guild_id)
        if guild and guild.icon:
            return guild.icon.url
        if self.cog.bot.user:
            return self.cog.bot.user.display_avatar.url
        return "https://cdn.discordapp.com/embed/avatars/0.png"

    def _render(self) -> None:
        self.clear_items()

        container = discord.ui.Container(accent_color=discord.Color.blurple())
        container.add_item(
            discord.ui.TextDisplay(
                "## 🛡 Moderation Appeal System\n"
                f"You are currently timed out from **{self.record.guild_name}**.\n\n"
                "We understand mistakes happen.\n\n"
                "If you believe your timeout was unfair or you would like another chance, "
                "you may submit an appeal."
            )
        )
        container.add_item(discord.ui.Separator())
        container.add_item(
            discord.ui.Section(
                discord.ui.TextDisplay(
                    "### Current Punishment\n"
                    f"• `{self.record.punishment_type.title()}`\n\n"
                    f"**Reason**\n"
                    f"• {self.record.punishment_reason}\n\n"
                    f"**Issued**\n"
                    f"• {_format_relative(self.record.timeout_issued_at)}\n\n"
                    f"**Expires**\n"
                    f"• {_format_relative(self.record.timeout_expires_at)}"
                ),
                accessory=discord.ui.Thumbnail(
                    self._icon_url(),
                    description=f"{self.record.guild_name} moderation appeal",
                ),
            )
        )
        container.add_item(discord.ui.Separator())
        container.add_item(
            discord.ui.TextDisplay(
                "### Appeal Requirements\n"
                "✓ Be honest\n\n"
                "✓ Explain what happened\n\n"
                "✓ Explain what you learned\n\n"
                "✓ Tell us why your punishment should be reduced or removed"
            )
        )
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay("### Average Review Time\n12–48 hours"))
        if self.disabled_reason:
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(f"**Status:** {self.disabled_reason}"))

        self.add_item(container)

        row = discord.ui.ActionRow()
        submit = discord.ui.Button(
            label="📝 Submit Appeal",
            style=discord.ButtonStyle.primary,
            disabled=not self.can_submit,
            custom_id=f"appeal:submit:{self.record.guild_id}:{self.record.user_id}",
        )
        submit.callback = self.submit_appeal  # type: ignore[assignment]
        row.add_item(submit)
        self.add_item(row)

    async def submit_appeal(self, interaction: discord.Interaction):
        if interaction.user.id != self.record.user_id:
            await interaction.response.send_message(
                "This appeal card is not for you.", ephemeral=True
            )
            return

        if not self.can_submit:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Appeal Unavailable",
                    self.disabled_reason or "This appeal is not available right now.",
                    guild_name=self.record.guild_name,
                ),
                ephemeral=True,
            )
            return

        modal = AppealSubmissionModal(self.cog, self.record, source_message=interaction.message)
        await interaction.response.send_modal(modal)


class AppealSubmissionModal(discord.ui.Modal):
    """Collects the four required timeout appeal answers."""

    def __init__(
        self,
        cog: "Appeals",
        record: AppealRecord,
        *,
        source_message: Optional[discord.Message] = None,
    ):
        super().__init__(title="Submit Appeal", timeout=300)
        self.cog = cog
        self.record = record
        self.source_message = source_message

        self.what_happened = discord.ui.TextInput(
            label="Why were you timed out?",
            placeholder="Explain the situation clearly and honestly.",
            style=discord.TextStyle.paragraph,
            max_length=1200,
            required=True,
        )
        self.should_remove = discord.ui.TextInput(
            label="Why should we remove the timeout?",
            placeholder="Tell us why the timeout should be reduced or removed.",
            style=discord.TextStyle.paragraph,
            max_length=1200,
            required=True,
        )
        self.learned = discord.ui.TextInput(
            label="What have you learned?",
            placeholder="Explain what you learned from the situation.",
            style=discord.TextStyle.paragraph,
            max_length=1200,
            required=True,
        )
        self.extra = discord.ui.TextInput(
            label="Anything else?",
            placeholder="Optional additional context for the moderation team.",
            style=discord.TextStyle.paragraph,
            max_length=1200,
            required=False,
        )

        self.add_item(self.what_happened)
        self.add_item(self.should_remove)
        self.add_item(self.learned)
        self.add_item(self.extra)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.process_appeal_submission(
            interaction,
            self.record,
            what_happened=self.what_happened.value,
            should_remove=self.should_remove.value,
            learned=self.learned.value,
            extra=self.extra.value if self.extra.value else None,
            source_message=self.source_message,
        )


class AppealDecisionConfirmView(discord.ui.View):
    """Small confirmation dialog for staff decisions."""

    def __init__(self, cog: "Appeals", record: AppealRecord, action: Literal["approved", "denied"]):
        super().__init__(timeout=90)
        self.cog = cog
        self.record = record
        self.action = action

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.finalize_appeal_decision(interaction, self.record, self.action)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Decision cancelled.", view=None)


class AppealExtendTimeoutModal(discord.ui.Modal):
    """Extend a timeout from the review dashboard."""

    def __init__(self, cog: "Appeals", record: AppealRecord):
        super().__init__(title=f"Extend Timeout #{record.appeal_id}", timeout=300)
        self.cog = cog
        self.record = record

        self.duration = discord.ui.TextInput(
            label="Duration",
            placeholder="Examples: 1d 2h, 12h, 45m",
            max_length=30,
            required=True,
        )
        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="Explain why the timeout is being extended.",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True,
        )

        self.add_item(self.duration)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.extend_timeout_for_appeal(
            interaction,
            self.record,
            duration_text=self.duration.value,
            reason=self.reason.value,
        )


class AppealReviewDashboard(discord.ui.LayoutView):
    """Components V2 moderation dashboard for reviewing appeals."""

    def __init__(
        self,
        cog: "Appeals",
        record: AppealRecord,
        *,
        decision: Optional[str] = None,
        decision_reason: Optional[str] = None,
        moderator: Optional[discord.Member | discord.User] = None,
        alert_text: Optional[str] = None,
    ):
        super().__init__(timeout=None)
        self.cog = cog
        self.record = record
        self.decision = decision
        self.decision_reason = decision_reason
        self.moderator = moderator
        self.alert_text = alert_text
        self._render()

    def _render(self) -> None:
        self.clear_items()

        color_map = {
            None: discord.Color.blurple(),
            "approved": discord.Color.green(),
            "denied": discord.Color.red(),
            "extended": discord.Color.orange(),
            "auto_resolved": discord.Color.greyple(),
        }
        container = discord.ui.Container(
            accent_color=color_map.get(self.decision, discord.Color.blurple())
        )
        avatar = self._user_avatar()

        status_line = "Pending review"
        if self.decision == "approved":
            status_line = "Approved"
        elif self.decision == "denied":
            status_line = "Rejected"
        elif self.decision == "extended":
            status_line = "Timeout extended"
        elif self.decision == "auto_resolved":
            status_line = "Auto-resolved"

        header = (
            "## Moderation Appeal Review Dashboard\n"
            f"### Appeal #{self.record.appeal_id}\n"
            f"Status: **{status_line}**"
        )
        container.add_item(discord.ui.TextDisplay(header))
        container.add_item(discord.ui.Separator())

        if self.alert_text:
            container.add_item(discord.ui.TextDisplay(f"**{self.alert_text}**"))
            container.add_item(discord.ui.Separator())

        meta_section = discord.ui.Section(
            discord.ui.TextDisplay(
                "### Appeal Snapshot\n"
                f"**User**\n• {self.record.username} (<@{self.record.user_id}>)\n\n"
                f"**User ID**\n• `{self.record.user_id}`\n\n"
                f"**Account Created**\n• {_format_relative(self._account_created)}\n\n"
                f"**Joined Server**\n• {_format_relative(self._joined_at)}\n\n"
                f"**Timeout Ends**\n• {_format_relative(self.record.timeout_expires_at)}\n\n"
                f"**Reason**\n• {_clean_reason(self.record.punishment_reason)}\n\n"
                f"**Appeal Time**\n• {_format_relative(self.record.submitted_at)}"
            ),
            accessory=discord.ui.Thumbnail(
                avatar,
                description=f"{self.record.username} profile",
            ),
        )
        container.add_item(meta_section)
        container.add_item(discord.ui.Separator())

        answers = discord.ui.TextDisplay(
            "### All Appeal Answers\n"
            f"**1. Why were you timed out?**\n{_truncate(self.record.appeal_reason, 1200)}\n\n"
            f"**2. Why should we remove the timeout?**\n{_truncate(self.record.should_remove, 1200)}\n\n"
            f"**3. What have you learned?**\n{_truncate(self.record.appeal_learned, 1200)}\n\n"
            f"**4. Anything else?**\n{_truncate(self.record.appeal_extra or 'Not provided.', 1200)}"
        )
        container.add_item(answers)

        if self.decision_reason:
            container.add_item(discord.ui.Separator())
            container.add_item(
                discord.ui.TextDisplay(
                    f"### Decision Note\n{_truncate(self.decision_reason, 1200)}"
                )
            )

        self.add_item(container)

        row = discord.ui.ActionRow()
        for button in self._build_buttons():
            row.add_item(button)
        self.add_item(row)

    @property
    def _account_created(self) -> Optional[datetime]:
        member = self.cog._resolve_member(self.record.guild_id, self.record.user_id)
        if member and hasattr(member, "created_at"):
            return member.created_at
        return None

    @property
    def _joined_at(self) -> Optional[datetime]:
        member = self.cog._resolve_member(self.record.guild_id, self.record.user_id)
        if member and hasattr(member, "joined_at"):
            return member.joined_at
        return None

    def _user_avatar(self) -> str:
        member = self.cog._resolve_member(self.record.guild_id, self.record.user_id)
        if member and getattr(member, "display_avatar", None):
            return member.display_avatar.url
        if self.cog.bot.user:
            return self.cog.bot.user.display_avatar.url
        return "https://cdn.discordapp.com/embed/avatars/0.png"

    def _build_buttons(self) -> list[discord.ui.Button]:
        resolved = self.decision is not None
        buttons: list[discord.ui.Button] = []

        accept = discord.ui.Button(
            label="✅ Accept",
            style=discord.ButtonStyle.success,
            disabled=resolved,
            custom_id=f"appeal:{self.record.appeal_id}:accept",
        )
        accept.callback = self.accept  # type: ignore[assignment]
        buttons.append(accept)

        reject = discord.ui.Button(
            label="❌ Reject",
            style=discord.ButtonStyle.danger,
            disabled=resolved,
            custom_id=f"appeal:{self.record.appeal_id}:reject",
        )
        reject.callback = self.reject  # type: ignore[assignment]
        buttons.append(reject)

        extend = discord.ui.Button(
            label="🕒 Extend Timeout",
            style=discord.ButtonStyle.primary,
            disabled=resolved,
            custom_id=f"appeal:{self.record.appeal_id}:extend",
        )
        extend.callback = self.extend_timeout  # type: ignore[assignment]
        buttons.append(extend)

        view_user = discord.ui.Button(
            label="👤 View User",
            style=discord.ButtonStyle.secondary,
            disabled=False,
            custom_id=f"appeal:{self.record.appeal_id}:user",
        )
        view_user.callback = self.view_user  # type: ignore[assignment]
        buttons.append(view_user)

        view_history = discord.ui.Button(
            label="📜 View History",
            style=discord.ButtonStyle.secondary,
            disabled=False,
            custom_id=f"appeal:{self.record.appeal_id}:history",
        )
        view_history.callback = self.view_history  # type: ignore[assignment]
        buttons.append(view_history)

        return buttons

    async def _must_be_moderator(self, interaction: discord.Interaction) -> bool:
        if not self.cog._is_moderator(interaction):
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Permission Denied",
                    "You don't have permission to review appeals.",
                    guild_name=interaction.guild.name if interaction.guild else None,
                ),
                ephemeral=True,
            )
            return False
        return True

    async def accept(self, interaction: discord.Interaction):
        if not await self._must_be_moderator(interaction):
            return
        if self.decision is not None:
            await interaction.response.send_message(
                "This appeal has already been processed.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            view=AppealDecisionConfirmView(self.cog, self.record, "approved"),
            ephemeral=True,
        )

    async def reject(self, interaction: discord.Interaction):
        if not await self._must_be_moderator(interaction):
            return
        if self.decision is not None:
            await interaction.response.send_message(
                "This appeal has already been processed.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            view=AppealDecisionConfirmView(self.cog, self.record, "denied"),
            ephemeral=True,
        )

    async def extend_timeout(self, interaction: discord.Interaction):
        if not await self._must_be_moderator(interaction):
            return
        if self.decision is not None:
            await interaction.response.send_message(
                "This appeal has already been processed.", ephemeral=True
            )
            return
        await interaction.response.send_modal(AppealExtendTimeoutModal(self.cog, self.record))

    async def view_user(self, interaction: discord.Interaction):
        if not await self._must_be_moderator(interaction):
            return
        dashboard = await self.cog.build_user_profile_dashboard(self.record)
        await interaction.response.send_message(view=dashboard, ephemeral=True)

    async def view_history(self, interaction: discord.Interaction):
        if not await self._must_be_moderator(interaction):
            return
        dashboard = await self.cog.build_history_dashboard(self.record)
        await interaction.response.send_message(view=dashboard, ephemeral=True)


class Appeals(commands.Cog):
    """Unban appeal system with auto-DM for moderation actions"""

    def __init__(self, bot):
        self.bot = bot
        init_db()
        self._timeout_dedupe_cache = {}  # {(user_id, guild_id, action): timestamp} - prevents double DM
        self._ban_event_handled = set()  # Track recently handled ban events to prevent duplicates
        self._ensure_appeal_schema()
        self.bot.loop.create_task(self._restore_review_dashboards())

    def _ensure_appeal_schema(self):
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            for column_sql in (
                "ALTER TABLE unban_requests ADD COLUMN punishment_type TEXT",
                "ALTER TABLE unban_requests ADD COLUMN punishment_reason TEXT",
                "ALTER TABLE unban_requests ADD COLUMN appeal_reason TEXT",
                "ALTER TABLE unban_requests ADD COLUMN should_remove TEXT",
                "ALTER TABLE unban_requests ADD COLUMN appeal_learned TEXT",
                "ALTER TABLE unban_requests ADD COLUMN appeal_extra TEXT",
                "ALTER TABLE unban_requests ADD COLUMN timeout_issued_at DATETIME",
                "ALTER TABLE unban_requests ADD COLUMN timeout_expires_at DATETIME",
                "ALTER TABLE unban_requests ADD COLUMN appeal_message_id INTEGER",
                "ALTER TABLE unban_requests ADD COLUMN review_channel_id INTEGER",
                "ALTER TABLE unban_requests ADD COLUMN review_message_id INTEGER",
                "ALTER TABLE unban_requests ADD COLUMN reviewed_by INTEGER",
                "ALTER TABLE unban_requests ADD COLUMN reviewed_at DATETIME",
                "ALTER TABLE unban_requests ADD COLUMN review_reason TEXT",
                "ALTER TABLE unban_requests ADD COLUMN jump_url TEXT",
            ):
                try:
                    cursor.execute(column_sql)
                except sqlite3.OperationalError:
                    pass

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS appeal_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appeal_id INTEGER NOT NULL,
                    guild_id INTEGER,
                    action TEXT NOT NULL,
                    actor_id INTEGER,
                    reason TEXT,
                    jump_url TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        finally:
            try:
                conn.close()
            except Exception:
                pass

    async def _restore_review_dashboards(self):
        await self.bot.wait_until_ready()
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, guild_id, reason, status, timestamp, punishment_type, punishment_reason,
                       appeal_reason, should_remove, appeal_learned, appeal_extra, timeout_issued_at,
                       timeout_expires_at, appeal_message_id, review_channel_id, review_message_id,
                       reviewed_by, reviewed_at, review_reason, jump_url
                FROM unban_requests
                WHERE status = 'pending' AND review_channel_id IS NOT NULL AND review_message_id IS NOT NULL
                """
            )
            rows = cursor.fetchall()
            conn.close()
            restored = 0
            for row in rows:
                record = self._build_appeal_record_from_row(row)
                channel = self.bot.get_channel(record.review_channel_id)
                if channel is None:
                    continue
                try:
                    await channel.fetch_message(record.review_message_id)
                    self.bot.add_view(AppealReviewDashboard(self, record), message_id=record.review_message_id)
                    restored += 1
                except Exception:
                    continue
            if restored:
                print(f"[Appeals] Restored {restored} appeal review dashboards")
        except Exception as e:
            print(f"[Appeals] Error restoring appeal review dashboards: {e}")

    def _resolve_member(self, guild_id: int, user_id: int) -> Optional[discord.Member]:
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return None
        member = guild.get_member(user_id)
        return member if isinstance(member, discord.Member) else None

    def _is_moderator(self, interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            return False
        allowed = {1403059755001577543}
        if interaction.guild:
            role = interaction.guild.get_role(MODERATION_ROLE_ID)
            if role:
                allowed.add(role.id)
        return (
            any(role.id in allowed for role in interaction.user.roles)
            or interaction.user.guild_permissions.manage_messages
            or interaction.user.guild_permissions.administrator
        )

    def _parse_timestamp(self, value: Any) -> Optional[datetime]:
        if not value:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        try:
            parsed = datetime.fromisoformat(str(value))
        except ValueError:
            try:
                parsed = datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _format_roles(self, member: Optional[discord.Member]) -> str:
        if not member:
            return "Unavailable"
        roles = [role.mention for role in member.roles if not role.is_default()]
        if not roles:
            return "None"
        return ", ".join(roles[:8]) + ("..." if len(roles) > 8 else "")

    def _parse_duration(self, text: str) -> Optional[timedelta]:
        text = text.strip().lower().replace(",", " ")
        match = re.fullmatch(
            r"(?:(\d+)\s*d)?\s*(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?",
            text,
        )
        if not match:
            return None
        days, hours, minutes, seconds = (int(part) if part else 0 for part in match.groups())
        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        return delta if delta.total_seconds() > 0 else None

    def _build_appeal_record_from_row(self, row: tuple) -> AppealRecord:
        (
            appeal_id,
            user_id,
            guild_id,
            reason,
            status,
            timestamp,
            punishment_type,
            punishment_reason,
            appeal_reason,
            should_remove,
            appeal_learned,
            appeal_extra,
            timeout_issued_at,
            timeout_expires_at,
            appeal_message_id,
            review_channel_id,
            review_message_id,
            reviewed_by,
            reviewed_at,
            review_reason,
            jump_url,
        ) = row
        guild = self.bot.get_guild(guild_id) if guild_id else None
        member = self._resolve_member(guild_id, user_id) if guild_id else None
        return AppealRecord(
            appeal_id=appeal_id,
            guild_id=guild_id,
            guild_name=guild.name if guild else "the server",
            user_id=user_id,
            username=str(member) if member else f"User {user_id}",
            punishment_type=punishment_type or "timeout",
            punishment_reason=punishment_reason or "No reason provided",
            timeout_issued_at=self._parse_timestamp(timeout_issued_at),
            timeout_expires_at=self._parse_timestamp(timeout_expires_at),
            appeal_reason=appeal_reason or "No answer provided.",
            should_remove=should_remove or "No answer provided.",
            appeal_learned=appeal_learned or "No answer provided.",
            appeal_extra=appeal_extra,
            submitted_at=self._parse_timestamp(timestamp) or datetime.now(timezone.utc),
            status=status or "pending",
            review_channel_id=review_channel_id,
            review_message_id=review_message_id,
            reviewed_by=reviewed_by,
            reviewed_at=self._parse_timestamp(reviewed_at),
            review_reason=review_reason,
            jump_url=jump_url,
        )

    async def _log_appeal_event(
        self,
        event_type: str,
        record: AppealRecord,
        *,
        moderator: Optional[discord.Member | discord.User] = None,
        reason: Optional[str] = None,
        jump_url: Optional[str] = None,
    ) -> None:
        logging_cog = self.bot.get_cog("LoggingCog")
        if not logging_cog or not hasattr(logging_cog, "log_event"):
            return
        details = reason or record.review_reason or record.punishment_reason
        await logging_cog.log_event(
            event_type,
            user_id=record.user_id,
            guild_id=record.guild_id,
            moderator_id=getattr(moderator, "id", None),
            details=details,
            title=f"Appeal {event_type.replace('APPEAL_', '').title()}",
            description=details,
            fields=[
                {"name": "Appeal ID", "value": f"#{record.appeal_id}", "inline": True},
                {"name": "User", "value": f"<@{record.user_id}> ({record.user_id})", "inline": True},
                {"name": "Decision", "value": event_type.replace("APPEAL_", "").title(), "inline": True},
                {"name": "Reason", "value": _truncate(details, 900), "inline": False},
                {"name": "Timestamp", "value": f"<t:{int(datetime.now(timezone.utc).timestamp())}:F>", "inline": True},
                {"name": "Jump URL", "value": jump_url or record.jump_url or "Unavailable", "inline": False},
            ],
            color={
                "APPEAL_SUBMITTED": 0x5865F2,
                "APPEAL_APPROVED": 0x2ECC71,
                "APPEAL_DENIED": 0xE74C3C,
                "APPEAL_EXTENDED": 0xF39C12,
            }.get(event_type, 0x5865F2),
            jump_url=jump_url or record.jump_url,
        )

    async def _get_timeout_history(self, user_id: int, guild_id: int) -> list[dict[str, Any]]:
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, action, reason
                FROM moderation_log
                WHERE user_id = ? AND guild_id = ? AND (action LIKE 'Timeout%' OR action LIKE 'timeout%')
                ORDER BY timestamp DESC LIMIT 10
                """,
                (user_id, guild_id),
            )
            rows = cursor.fetchall()
            conn.close()
            return [
                {"timestamp": row[0], "action": row[1], "reason": row[2] or "No reason provided"}
                for row in rows
            ]
        except Exception:
            return []

    async def _get_appeal_history(self, user_id: int, guild_id: int) -> list[dict[str, Any]]:
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, status, timestamp
                FROM unban_requests
                WHERE user_id = ? AND guild_id = ?
                ORDER BY timestamp DESC LIMIT 10
                """,
                (user_id, guild_id),
            )
            rows = cursor.fetchall()
            conn.close()
            return [{"id": row[0], "status": row[1], "timestamp": row[2]} for row in rows]
        except Exception:
            return []

    async def _get_notes_history(self, user_id: int, guild_id: int) -> list[dict[str, Any]]:
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, action, reason
                FROM moderation_log
                WHERE user_id = ? AND guild_id = ? AND action LIKE '%note%'
                ORDER BY timestamp DESC LIMIT 10
                """,
                (user_id, guild_id),
            )
            rows = cursor.fetchall()
            conn.close()
            return [
                {"timestamp": row[0], "action": row[1], "details": row[2] or "No details"}
                for row in rows
            ]
        except Exception:
            return []

    async def _get_message_count(self, guild_id: int, user_id: int) -> str:
        return "Unavailable"

    async def build_user_profile_dashboard(self, record: AppealRecord) -> discord.ui.LayoutView:
        member = self._resolve_member(record.guild_id, record.user_id)
        try:
            from utils.json_store import get_warnings

            warnings = await get_warnings(record.user_id)
        except Exception:
            warnings = []
        timeouts = await self._get_timeout_history(record.user_id, record.guild_id)
        appeals = await self._get_appeal_history(record.user_id, record.guild_id)

        view = discord.ui.LayoutView(timeout=120)
        container = discord.ui.Container(accent_color=discord.Color.orange())
        container.add_item(
            discord.ui.TextDisplay(
                "## 👤 User Profile\n"
                f"**User**: {record.username}\n"
                f"**User ID**: `{record.user_id}`\n"
                f"**Roles**: {self._format_roles(member)}\n"
                f"**Joined Server**: {_format_relative(member.joined_at if member and member.joined_at else None)}\n"
                f"**Account Created**: {_format_relative(member.created_at if member and member.created_at else None)}\n"
                f"**Warnings**: {len(warnings)}\n"
                f"**Timeouts**: {len(timeouts)}\n"
                f"**Appeals**: {len(appeals)}\n"
                f"**Message Count**: Unavailable"
            )
        )
        view.add_item(container)
        return view

    async def build_history_dashboard(self, record: AppealRecord) -> discord.ui.LayoutView:
        try:
            from utils.json_store import get_warnings

            warnings = await get_warnings(record.user_id)
        except Exception:
            warnings = []
        timeouts = await self._get_timeout_history(record.user_id, record.guild_id)
        appeals = await self._get_appeal_history(record.user_id, record.guild_id)
        notes = await self._get_notes_history(record.user_id, record.guild_id)

        view = discord.ui.LayoutView(timeout=120)
        container = discord.ui.Container(accent_color=discord.Color.dark_grey())
        container.add_item(
            discord.ui.TextDisplay(
                "## 📜 History\n"
                f"**Warnings**: {len(warnings)}\n"
                f"**Timeouts**: {len(timeouts)}\n"
                f"**Appeals**: {len(appeals)}\n"
                f"**Notes**: {len(notes)}"
            )
        )
        if warnings:
            warning_lines = "\n".join(
                f"• {item.get('ts', 'Unknown')} - {item.get('reason', 'No reason')}"
                for item in warnings[:5]
            )
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(f"### Warnings\n{warning_lines}"))
        if timeouts:
            timeout_lines = "\n".join(
                f"• {item['timestamp']} - {item['reason']}" for item in timeouts[:5]
            )
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(f"### Timeouts\n{timeout_lines}"))
        if appeals:
            appeal_lines = "\n".join(
                f"• #{item['id']} - {item['status']} ({item['timestamp']})"
                for item in appeals[:5]
            )
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(f"### Appeals\n{appeal_lines}"))
        if notes:
            note_lines = "\n".join(
                f"• {item['timestamp']} - {item['details']}" for item in notes[:5]
            )
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(f"### Notes\n{note_lines}"))
        view.add_item(container)
        return view

    async def process_appeal_submission(
        self,
        interaction: discord.Interaction,
        record: AppealRecord,
        *,
        what_happened: str,
        should_remove: str,
        learned: str,
        extra: Optional[str] = None,
        source_message: Optional[discord.Message] = None,
    ) -> None:
        if interaction.user.id != record.user_id:
            await interaction.response.send_message(
                "This appeal form is not for you.", ephemeral=True
            )
            return

        existing = await self._get_pending_appeal(record.user_id, record.guild_id)
        if existing and existing.appeal_id != record.appeal_id:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Appeal Already Submitted",
                    f"You already have a pending appeal (#{existing.appeal_id}).",
                    guild_name=record.guild_name,
                ),
                ephemeral=True,
            )
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO unban_requests (
                user_id, guild_id, reason, status, punishment_type, punishment_reason,
                appeal_reason, should_remove, appeal_learned, appeal_extra,
                timeout_issued_at, timeout_expires_at, jump_url
            ) VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.user_id,
                record.guild_id,
                "\n\n".join(
                    [
                        f"**Why I was timed out:** {what_happened}",
                        f"**Why it should be removed:** {should_remove}",
                        f"**What I learned:** {learned}",
                        f"**Anything else:** {extra or 'Not provided.'}",
                    ]
                ),
                record.punishment_type,
                record.punishment_reason,
                what_happened,
                should_remove,
                learned,
                extra,
                record.timeout_issued_at.strftime("%Y-%m-%d %H:%M:%S") if record.timeout_issued_at else None,
                record.timeout_expires_at.strftime("%Y-%m-%d %H:%M:%S") if record.timeout_expires_at else None,
                interaction.message.jump_url if interaction.message else None,
            ),
        )
        appeal_id = cursor.lastrowid
        conn.commit()
        conn.close()

        updated_record = await self._fetch_appeal_record(appeal_id)
        if updated_record is None:
            await interaction.response.send_message(
                "Failed to persist the appeal.", ephemeral=True
            )
            return

        await self._log_appeal_event(
            "APPEAL_SUBMITTED",
            updated_record,
            moderator=None,
            reason="User submitted a timeout appeal.",
            jump_url=interaction.message.jump_url if interaction.message else None,
        )

        review_view = AppealReviewDashboard(self, updated_record)
        review_channel = await self._resolve_review_channel(updated_record.guild_id)
        if review_channel:
            staff_message = await review_channel.send(view=review_view)
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE unban_requests SET review_channel_id = ?, review_message_id = ?, jump_url = ? WHERE id = ?",
                (review_channel.id, staff_message.id, staff_message.jump_url, updated_record.appeal_id),
            )
            conn.commit()
            conn.close()

        await interaction.response.send_message(
            embed=create_success_embed(
                "Appeal Submitted",
                "Your appeal has been sent to the moderation team.",
                guild_name=record.guild_name,
            ),
            ephemeral=True,
        )

        disabled_view = AppealSubmissionDashboard(
            self,
            updated_record,
            can_submit=False,
            disabled_reason="Appeal already submitted and awaiting review.",
        )
        try:
            target_message = source_message or interaction.message
            if target_message is not None:
                await target_message.edit(view=disabled_view)
        except Exception:
            pass

    async def finalize_appeal_decision(
        self,
        interaction: discord.Interaction,
        record: AppealRecord,
        decision: Literal["approved", "denied"],
    ) -> None:
        if not self._is_moderator(interaction):
            await interaction.response.send_message(
                embed=create_error_embed("Permission Denied", "You don't have permission to review appeals."),
                ephemeral=True,
            )
            return

        updated_record = await self._fetch_appeal_record(record.appeal_id)
        if updated_record is None or updated_record.status != "pending":
            await interaction.response.send_message(
                "This appeal has already been processed.", ephemeral=True
            )
            return

        if decision == "approved":
            member = self._resolve_member(record.guild_id, record.user_id)
            if member is None:
                await interaction.response.send_message(
                    embed=create_error_embed(
                        "Member Not Found",
                        "The user is no longer in the server, so the timeout cannot be removed.",
                    ),
                    ephemeral=True,
                )
                return
            try:
                await member.timeout(None, reason=f"Appeal #{record.appeal_id} approved by {interaction.user}")
            except Exception as e:
                await interaction.response.send_message(
                    embed=create_error_embed("Action Failed", f"Could not clear timeout: {e}"),
                    ephemeral=True,
                )
                return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE unban_requests
            SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP, review_reason = ?, jump_url = ?
            WHERE id = ?
            """,
            (
                decision,
                interaction.user.id,
                f"{decision.title()} by {interaction.user}",
                interaction.message.jump_url if interaction.message else None,
                record.appeal_id,
            ),
        )
        conn.commit()
        conn.close()

        decision_reason = f"{decision.title()} by {interaction.user.mention}"
        resolved_view = AppealReviewDashboard(
            self,
            updated_record,
            decision=decision,
            decision_reason=decision_reason,
            moderator=interaction.user,
        )

        if updated_record.review_channel_id and updated_record.review_message_id:
            try:
                channel = self.bot.get_channel(updated_record.review_channel_id)
                if channel is None:
                    channel = await self.bot.fetch_channel(updated_record.review_channel_id)
                if channel:
                    message = await channel.fetch_message(updated_record.review_message_id)
                    await message.edit(view=resolved_view)
            except Exception:
                pass

        await interaction.response.send_message(
            embed=create_success_embed(
                f"Appeal {decision.title()}",
                f"Appeal #{record.appeal_id} has been {decision}.",
                guild_name=record.guild_name,
            ),
            ephemeral=True,
        )

        await self._log_appeal_event(
            f"APPEAL_{decision.upper()}",
            updated_record,
            moderator=interaction.user,
            reason=decision_reason,
            jump_url=updated_record.jump_url,
        )

        await self._dm_decision(updated_record, decision, interaction.user)

    async def extend_timeout_for_appeal(
        self,
        interaction: discord.Interaction,
        record: AppealRecord,
        *,
        duration_text: str,
        reason: str,
    ) -> None:
        if not self._is_moderator(interaction):
            await interaction.response.send_message(
                embed=create_error_embed("Permission Denied", "You don't have permission to extend timeouts."),
                ephemeral=True,
            )
            return

        delta = self._parse_duration(duration_text)
        if delta is None:
            await interaction.response.send_message(
                embed=create_error_embed("Invalid Duration", "Use a format like `1d 2h`, `12h`, or `45m`."),
                ephemeral=True,
            )
            return

        member = self._resolve_member(record.guild_id, record.user_id)
        if not member:
            await interaction.response.send_message(
                embed=create_error_embed("Member Not Found", "The user is no longer in the server."),
                ephemeral=True,
            )
            return

        new_until = datetime.now(timezone.utc) + delta
        try:
            await member.timeout(new_until, reason=reason)
        except Exception as e:
            await interaction.response.send_message(
                embed=create_error_embed("Timeout Failed", str(e)),
                ephemeral=True,
            )
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE unban_requests SET timeout_expires_at = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP, review_reason = ? WHERE id = ?",
            (
                new_until.strftime("%Y-%m-%d %H:%M:%S"),
                interaction.user.id,
                reason,
                record.appeal_id,
            ),
        )
        conn.commit()
        conn.close()

        refreshed = await self._fetch_appeal_record(record.appeal_id)
        await self._log_appeal_event(
            "APPEAL_EXTENDED",
            refreshed or record,
            moderator=interaction.user,
            reason=reason,
            jump_url=(refreshed.jump_url if refreshed else record.jump_url),
        )
        await self._dm_extended_timeout(refreshed or record, interaction.user, new_until, reason)
        await interaction.response.send_message(
            embed=create_success_embed(
                "Timeout Extended",
                f"The timeout for {record.username} has been extended until {_format_relative(new_until)}.",
                guild_name=record.guild_name,
            ),
            ephemeral=True,
        )
        if refreshed and refreshed.review_channel_id and refreshed.review_message_id:
            try:
                channel = self.bot.get_channel(refreshed.review_channel_id)
                if channel is None:
                    channel = await self.bot.fetch_channel(refreshed.review_channel_id)
                if channel:
                    message = await channel.fetch_message(refreshed.review_message_id)
                    await message.edit(
                        view=AppealReviewDashboard(
                            self,
                            refreshed,
                            decision="extended",
                            decision_reason=reason,
                            moderator=interaction.user,
                            alert_text="Timeout extension applied.",
                        )
                    )
            except Exception:
                pass

    async def _get_pending_appeal(self, user_id: int, guild_id: int) -> Optional[AppealRecord]:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, user_id, guild_id, reason, status, timestamp, punishment_type, punishment_reason,
                   appeal_reason, should_remove, appeal_learned, appeal_extra, timeout_issued_at,
                   timeout_expires_at, appeal_message_id, review_channel_id, review_message_id,
                   reviewed_by, reviewed_at, review_reason, jump_url
            FROM unban_requests
            WHERE user_id = ? AND guild_id = ? AND status = 'pending'
            ORDER BY timestamp DESC LIMIT 1
            """,
            (user_id, guild_id),
        )
        row = cursor.fetchone()
        conn.close()
        return self._build_appeal_record_from_row(row) if row else None

    async def _fetch_appeal_record(self, appeal_id: int) -> Optional[AppealRecord]:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, user_id, guild_id, reason, status, timestamp, punishment_type, punishment_reason,
                   appeal_reason, should_remove, appeal_learned, appeal_extra, timeout_issued_at,
                   timeout_expires_at, appeal_message_id, review_channel_id, review_message_id,
                   reviewed_by, reviewed_at, review_reason, jump_url
            FROM unban_requests
            WHERE id = ?
            """,
            (appeal_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return self._build_appeal_record_from_row(row) if row else None

    async def _resolve_review_channel(self, guild_id: int) -> Optional[discord.TextChannel]:
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return None
        for channel in guild.text_channels:
            name = channel.name.lower()
            if "appeal" in name or "mod" in name or "staff" in name or "log" in name:
                return channel
        return guild.text_channels[0] if guild.text_channels else None

    async def _dm_decision(
        self,
        record: AppealRecord,
        decision: Literal["approved", "denied"],
        moderator: discord.Member | discord.User,
    ) -> None:
        try:
            user = await self.bot.fetch_user(record.user_id)
        except Exception:
            return
        guild = self.bot.get_guild(record.guild_id)
        if decision == "approved":
            text = (
                "## Your appeal has been reviewed and approved.\n\n"
                f"Your timeout in **{record.guild_name}** has been removed."
            )
            accent = discord.Color.green()
        else:
            text = (
                "## Your appeal has been reviewed and denied.\n\n"
                f"Your timeout in **{record.guild_name}** remains in place."
            )
            accent = discord.Color.red()

        view = discord.ui.LayoutView(timeout=None)
        container = discord.ui.Container(accent_color=accent)
        container.add_item(discord.ui.TextDisplay(text))
        if guild and guild.icon:
            container.add_item(discord.ui.Separator())
            container.add_item(
                discord.ui.TextDisplay(
                    f"**Reviewed By:** {moderator}\n**Appeal ID:** #{record.appeal_id}\n**Reason:** {record.review_reason or 'Reviewed by staff'}"
                )
            )
        view.add_item(container)
        try:
            await user.send(view=view)
        except Exception:
            pass

    async def _dm_extended_timeout(
        self,
        record: AppealRecord,
        moderator: discord.Member | discord.User,
        new_until: datetime,
        reason: str,
    ) -> None:
        try:
            user = await self.bot.fetch_user(record.user_id)
        except Exception:
            return
        view = discord.ui.LayoutView(timeout=None)
        container = discord.ui.Container(accent_color=discord.Color.orange())
        container.add_item(
            discord.ui.TextDisplay(
                "## Timeout Extended\n"
                f"Your timeout in **{record.guild_name}** has been extended until {_format_relative(new_until)}.\n\n"
                f"**Reason:** {reason}\n"
                f"**Reviewed By:** {moderator}"
            )
        )
        view.add_item(container)
        try:
            await user.send(view=view)
        except Exception:
            pass

    async def _disable_appeal_buttons_by_id(self, appeal_id: int, guild_id: int):
        """Find and disable appeal buttons in messages for a specific appeal ID"""
        try:
            record = await self._fetch_appeal_record(appeal_id)
            if not record:
                return
            if record.review_channel_id and record.review_message_id:
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    return
                channel = guild.get_channel(record.review_channel_id)
                if channel is None:
                    channel = await guild.fetch_channel(record.review_channel_id)
                if channel:
                    message = await channel.fetch_message(record.review_message_id)
                    await message.edit(
                        view=AppealReviewDashboard(
                            self,
                            record,
                            decision="auto_resolved",
                            decision_reason="The timeout expired or was removed while this appeal was pending.",
                            alert_text="This appeal has been automatically resolved.",
                        )
                    )
                    print(f"[Appeals] Disabled buttons for appeal #{appeal_id} in review dashboard")
                    return
        except Exception as e:
            print(f"[Appeals] Error disabling buttons for appeal #{appeal_id}: {e}")

    async def _log_punishment_expiry(self, appeal_id: int, user_id: int, guild_id: int, status_message: str):
        """Log punishment expiry to appeals channel"""
        try:
            print(f"[Appeals] Starting to log punishment expiry for appeal #{appeal_id}")
            
            guild = self.bot.get_guild(guild_id)
            if not guild:
                print(f"[Appeals] Could not find guild {guild_id} for logging appeal #{appeal_id}")
                return
            
            # Find appeals channel
            appeals_channels = [channel for channel in guild.text_channels if 'appeal' in channel.name.lower()]
            if not appeals_channels:
                print(f"[Appeals] No appeals channel found in {guild.name} for logging punishment expiry")
                # Try to find any channel with "appeal" in the name or description
                all_channels = [ch.name for ch in guild.text_channels]
                print(f"[Appeals] Available channels in {guild.name}: {', '.join(all_channels)}")
                return
                
            print(f"[Appeals] Found appeals channel: {appeals_channels[0].name} in {guild.name}")
            
            user = self.bot.get_user(user_id) or f"<@{user_id}>"
            
            # Determine the type of expiry for better messaging
            is_natural_expiry = "naturally expired" in status_message.lower()
            is_ban_removal = "no longer banned" in status_message.lower()
            
            if is_natural_expiry:
                title = "Appeal Auto-Resolved - Timeout Naturally Expired"
                color = 0x95a5a6  # Gray for natural expiration
                description = f"Appeal #{appeal_id} has been automatically resolved because the timeout naturally expired."
            elif is_ban_removal:
                title = "Appeal Auto-Resolved - Ban Removed"
                color = 0x0000ff  # Blue for ban removal
                description = f"Appeal #{appeal_id} has been automatically resolved because the ban was removed."
            else:
                title = "Appeal Auto-Resolved - Punishment Invalid"
                color = 0xf39c12  # Orange for other cases
                description = f"Appeal #{appeal_id} has been automatically resolved because the punishment is no longer valid."
            
            print(f"[Appeals] Creating log embed with title: {title}")
            
            # Create log embed
            log_embed = discord.Embed(
                title=title,
                description=description,
                color=color,
                timestamp=datetime.now(timezone.utc)
            )
            
            log_embed.add_field(
                name="User",
                value=str(user),
                inline=True
            )
            
            log_embed.add_field(
                name="Appeal ID",
                value=f"#{appeal_id}",
                inline=True
            )
            
            log_embed.add_field(
                name="Details",
                value=status_message,
                inline=False
            )
            
            log_embed.add_field(
                name="Action",
                value="Appeal buttons have been automatically disabled",
                inline=False
            )
            
            log_embed.set_footer(text=f"Guild: {guild.name}", icon_url=guild.icon.url if guild.icon else None)
            
            # Send to appeals channel
            print(f"[Appeals] Sending log embed to {appeals_channels[0].name}")
            await appeals_channels[0].send(embed=log_embed)
            print(f"[Appeals] Successfully logged punishment expiry for appeal #{appeal_id} to {appeals_channels[0].name}")
            
        except Exception as e:
            print(f"[Appeals] Error logging punishment expiry for appeal #{appeal_id}: {e}")
            import traceback
            traceback.print_exc()

    async def _send_appeal_form(
        self,
        user: discord.User | discord.Member,
        guild: discord.Guild,
        action_type: str,
        reason: str | None = None,
        *,
        issued_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
    ):
        """Send the timeout appeal dashboard to the user."""
        dm_success = False
        dm_error = None
        
        try:
            if user.bot or (self.bot.user and user.id == self.bot.user.id):
                return
            
            # Improved dedupe: use (user_id, guild_id, action_type) as key
            import time
            now = time.time()
            dedupe_key = (user.id, guild.id, action_type)
            last_sent = self._timeout_dedupe_cache.get(dedupe_key)
            
            # Prevent duplicate DMs within 30 seconds for same action
            if last_sent and (now - last_sent) < 30:
                print(f"[Appeals] Skipped duplicate DM to {user} for {action_type} in {guild.name} (sent {now - last_sent:.1f}s ago)")
                return
            
            self._timeout_dedupe_cache[dedupe_key] = now
            
            # Cleanup old cache entries (keep last 100)
            if len(self._timeout_dedupe_cache) > 200:
                oldest = sorted(self._timeout_dedupe_cache.items(), key=lambda x: x[1])[:100]
                for key, _ in oldest:
                    del self._timeout_dedupe_cache[key]
            
            timeout_member = guild.get_member(user.id)
            timeout_until = getattr(timeout_member, "timed_out_until", None) if timeout_member else None
            pending_record = await self._get_pending_appeal(user.id, guild.id)
            can_submit = timeout_until is not None and timeout_until > datetime.now(timezone.utc) and pending_record is None
            disabled_reason = None
            if pending_record is not None:
                disabled_reason = f"Appeal already submitted as #{pending_record.appeal_id}."
            elif timeout_until is None or timeout_until <= datetime.now(timezone.utc):
                disabled_reason = "This timeout has already expired or was removed."

            temp_record = AppealRecord(
                appeal_id=0,
                guild_id=guild.id,
                guild_name=guild.name,
                user_id=user.id,
                username=str(user),
                punishment_type=action_type,
                punishment_reason=_clean_reason(reason),
                timeout_issued_at=issued_at,
                timeout_expires_at=expires_at or (timeout_until if isinstance(timeout_until, datetime) else None),
                appeal_reason="Not submitted yet.",
                should_remove="Not submitted yet.",
                appeal_learned="Not submitted yet.",
                appeal_extra=None,
                submitted_at=datetime.now(timezone.utc),
                status="pending",
            )
            view = AppealSubmissionDashboard(
                self,
                temp_record,
                can_submit=can_submit,
                disabled_reason=disabled_reason,
            )

            await user.send(view=view)
            dm_success = True
            print(f"[Appeals] Sent appeal dashboard to {user} ({user.id}) for {action_type} in {guild.name}")
            
            # Log success to appeals channel
            await self._log_dm_success(user, guild, action_type, reason or "No reason provided")
        except discord.Forbidden:
            dm_error = "DMs are closed or bot is blocked"
            print(f"[Appeals] Cannot DM {user} ({user.id}) - DMs closed or bot blocked")
        except Exception as e:
            dm_error = str(e)
            print(f"[Appeals] DM error to {user} ({user.id}): {e}")
        
        # Log DM failure to appeals channel
        if not dm_success and dm_error:
            await self._log_dm_failure(user, guild, action_type, reason or "No reason provided", dm_error)
    
    async def _log_dm_failure(self, user: discord.User | discord.Member, guild: discord.Guild, action_type: str, reason: str, error: str):
        """Log to appeals channel when DM fails"""
        for cid in (1423642446616592385, 1444013659134361703):
            ch = self.bot.get_channel(cid)
            if ch:
                embed = discord.Embed(
                    title="Appeal DM Failed",
                    description=f"**Could not send appeal form to {user.mention}**\n\nUser will NOT be able to submit an appeal via DM.",
                    color=0xff0000
                )
                embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
                embed.add_field(name="Guild", value=guild.name, inline=True)
                embed.add_field(name="Action", value=action_type.title(), inline=True)
                embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                embed.add_field(name="Error", value=f"```{error}```", inline=False)
                embed.add_field(
                    name="Note",
                    value="This user's DMs are blocked. They cannot submit appeals through the bot. Consider alternative appeal methods or manual review.",
                    inline=False
                )
                embed.timestamp = datetime.now(timezone.utc)
                embed.set_footer(text=_appeals_footer_text(guild.name))
                try:
                    await ch.send(embed=embed)
                    print(f"[Appeals] Logged DM failure to channel {cid}")
                except Exception as e:
                    print(f"[Appeals] Failed to send DM failure log to channel {cid}: {e}")
                break
    
    async def _log_dm_success(self, user: discord.User | discord.Member, guild: discord.Guild, action_type: str, reason: str):
        """Log to appeals channel when DM is successfully sent"""
        for cid in (1423642446616592385, 1444013659134361703):
            ch = self.bot.get_channel(cid)
            if ch:
                embed = discord.Embed(
                    title="Appeal DM Sent",
                    description=f"Successfully sent appeal form to {user.mention}",
                    color=0x00ff00
                )
                embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
                embed.add_field(name="Guild", value=guild.name, inline=True)
                embed.add_field(name="Action", value=action_type.title(), inline=True)
                embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                embed.timestamp = datetime.now(timezone.utc)
                embed.set_footer(text=_appeals_footer_text(guild.name))
                try:
                    await ch.send(embed=embed)
                except Exception as e:
                    print(f"[Appeals] Failed to send DM success log to channel {cid}: {e}")
                break

    # ---------------- Listeners ----------------
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Handle ban events.

        CVH Policy: ban appeals are disabled, so we do NOT DM an appeal form on bans.
        """
        if user.bot or (self.bot.user and user.id == self.bot.user.id):
            return
        
        # Create unique event key to prevent duplicate processing
        import time
        event_key = (user.id, guild.id, 'ban', int(time.time() / 5))  # 5-second window
        
        if event_key in self._ban_event_handled:
            print(f"[Appeals] Skipped duplicate ban event for {user} in {guild.name}")
            return
        
        self._ban_event_handled.add(event_key)
        
        # Clean up old entries (keep last 50)
        if len(self._ban_event_handled) > 100:
            # Remove all entries, will be recreated as needed
            self._ban_event_handled.clear()
        
        # Get reason from audit logs with retry
        reason = "No reason provided"
        try:
            await asyncio.sleep(1.5)  # Longer wait for audit log to be created
            
            # Check multiple entries to find the right one
            async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=10):
                if entry.target and entry.target.id == user.id:
                    # Check if this is recent (within last 10 seconds)
                    if entry.created_at:
                        time_diff = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
                        if time_diff < 10:
                            if entry.reason:
                                reason = entry.reason
                            print(f"[Appeals] Found ban audit log for {user}: {reason}")
                            break
        except Exception as e:
            print(f"[Appeals] Error fetching ban audit logs: {e}")
        
        print(f"[Appeals] Ban detected for {user} ({user.id}) in {guild.name}: {reason}")
        # Intentionally no DM appeal form for bans.

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Handle timeout changes - improved to prevent double DMs and log manual removals"""
        if after.bot:
            return
        
        before_timeout = before.timed_out_until
        after_timeout = after.timed_out_until
        
        # Check if timeout was manually removed OR naturally expired
        if (before_timeout and before_timeout > datetime.now(timezone.utc) and 
            (not after_timeout or after_timeout <= datetime.now(timezone.utc))):
            
            # Determine if this was manual removal or natural expiration
            current_time = datetime.now(timezone.utc)
            was_natural_expiry = False
            
            # If the before_timeout was very close to current time (within 30 seconds), 
            # it's likely natural expiration
            if before_timeout and (current_time - before_timeout).total_seconds() >= -30:
                was_natural_expiry = True
            
            # Check if there are pending appeals for this user
            try:
                conn = sqlite3.connect(DATABASE_NAME)
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM unban_requests WHERE user_id = ? AND status = "pending" ORDER BY id DESC LIMIT 1', (after.id,))
                appeal = cursor.fetchone()
                conn.close()
                
                if appeal:
                    if was_natural_expiry:
                        print(f"[Appeals] Natural timeout expiry detected for user {after.id} with pending appeal #{appeal[0]}")
                        action_text = "Natural timeout expiry"
                        log_title = "Natural Timeout Expiry Detected"
                        log_description = f"User {after.mention} (`{after.id}`) had their timeout naturally expire while having a pending appeal."
                        color = 0x95a5a6  # Gray for natural expiry
                    else:
                        print(f"[Appeals] Manual timeout removal detected for user {after.id} with pending appeal #{appeal[0]}")
                        action_text = "Manual timeout removal"
                        log_title = "Manual Timeout Removal Detected"
                        log_description = f"User {after.mention} (`{after.id}`) had their timeout manually removed while having a pending appeal."
                        color = 0xff9900  # Orange for manual removal
                    
                    # IMMEDIATELY mark as auto-resolved and disable buttons
                    try:
                        conn = sqlite3.connect(DATABASE_NAME)
                        cursor = conn.cursor()
                        cursor.execute('UPDATE unban_requests SET status = "auto_resolved" WHERE id = ?', (appeal[0],))
                        conn.commit()
                        conn.close()
                        
                        # Disable buttons immediately
                        await self._disable_appeal_buttons_by_id(appeal[0], after.guild.id)
                        print(f"[Appeals] Auto-resolved appeal #{appeal[0]} and disabled buttons due to {action_text}")
                    except Exception as e:
                        print(f"[Appeals] Error auto-resolving appeal #{appeal[0]}: {e}")
                    
                    # Create log message
                    log_embed = discord.Embed(
                        title=log_title,
                        description=log_description,
                        color=color
                    )
                    log_embed.add_field(name="Appeal ID", value=f"#{appeal[0]}", inline=True)
                    log_embed.add_field(name="Previous Timeout", value=f"Until <t:{int(before_timeout.timestamp())}:F>", inline=True)
                    log_embed.add_field(name="Action", value="Appeal automatically resolved and buttons disabled", inline=False)
                    log_embed.set_footer(text=f"User: {after.name}")
                    
                    # Try to send to appeals channel or log it
                    appeals_channels = [channel for channel in after.guild.text_channels if 'appeal' in channel.name.lower()]
                    if appeals_channels:
                        await appeals_channels[0].send(embed=log_embed)
                    else:
                        print(f"[Appeals] {log_embed.description}")
                        
            except Exception as e:
                print(f"[Appeals] Error checking for appeals during timeout removal: {e}")
        
        # Only send appeal form when timeout is APPLIED (not removed)
        if before_timeout is None and after_timeout is not None:
            reason = "Timeout applied"
            try:
                # Wait for audit log
                await asyncio.sleep(1.5)
                async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=10):
                    if entry.target and entry.target.id == after.id:
                        # Check if this is recent
                        if entry.created_at:
                            time_diff = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
                            if time_diff < 10:
                                audit_reason = entry.reason or reason
                                # Skip if audit reason contains appeal-related keywords
                                if audit_reason and not any(keyword in audit_reason.lower() for keyword in ['appeal', 'approved', 'unbanned', 'untimeout']):
                                    reason = audit_reason
                                break
            except Exception as e:
                print(f"[Appeals] Error fetching timeout audit logs: {e}")
            
            print(f"[Appeals] Timeout APPLIED to {after} ({after.id}): before={before_timeout}, after={after_timeout}, reason={reason}")
            
            # Send appeal form (logs will be sent by _send_appeal_form)
            await self._send_appeal_form(
                after,
                after.guild,
                "timed out",
                reason,
                issued_at=entry.created_at if "entry" in locals() and entry.created_at else None,
                expires_at=after_timeout,
            )
        
        # Check if timeout was REMOVED before expiry (manual untimeout/appeal approved)
        elif before_timeout is not None and after_timeout is None:
            # Auto-approve any pending appeals for this user in this guild
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM unban_requests WHERE user_id = ? AND status = "pending"', (after.id,))
            appeals = cursor.fetchall()
            
            if appeals:
                for (appeal_id,) in appeals:
                    cursor.execute('UPDATE unban_requests SET status = "approved" WHERE id = ?', (appeal_id,))
                    print(f"[Appeals] Auto-approved appeal #{appeal_id} - timeout removed for {after} ({after.id})")
                
                conn.commit()
                
                # Try to DM the user about approval
                try:
                    dm = create_success_embed(
                        "Appeal Automatically Approved",
                        f"## Your appeal has been automatically approved\n\nYour timeout in **{after.guild.name}** has been removed.",
                        guild_name=after.guild.name,
                    )
                    dm.add_field(name="Result", value="**Timeout removed**", inline=True)
                    await after.send(embed=dm)
                except Exception:
                    pass
            conn.close()

    @commands.hybrid_command(name="appeals")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(status="Filter appeals by status: pending, approved, denied, or all")
    async def appeals(self, ctx, status: str = "pending"):
        """View appeal requests"""
        valid_statuses = ["pending", "approved", "denied", "all"]
        if status not in valid_statuses:
            embed = create_error_embed("Invalid Status", f"Valid statuses: {', '.join(valid_statuses)}")
            await ctx.send(embed=embed)
            return
        
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        if status == "all":
            cursor.execute('SELECT id, user_id, reason, status, timestamp FROM unban_requests ORDER BY timestamp DESC LIMIT 20')
        else:
            cursor.execute('SELECT id, user_id, reason, status, timestamp FROM unban_requests WHERE status = ? ORDER BY timestamp DESC LIMIT 20', (status,))
        
        appeals = cursor.fetchall()
        conn.close()
        
        if not appeals:
            embed = create_info_embed("No Appeals", f"No {status} appeals found.")
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(title=f'{status.title()} Appeals', color=0x0000ff)
        
        for appeal in appeals:
            appeal_id, user_id, reason, appeal_status, timestamp = appeal
            try:
                user = await self.bot.fetch_user(user_id)
                user_name = f"{user} ({user_id})"
            except:
                user_name = f"Unknown ({user_id})"
            
            embed.add_field(
                name=f'Appeal #{appeal_id}',
                value=f'**User:** {user_name}\n**Status:** {appeal_status.title()}\n**Reason:** {reason[:100]}{"..." if len(reason) > 100 else ""}\n**Time:** {timestamp}', 
                inline=False
            )
        
        embed.set_footer(text=f"Appeals are processed using interactive buttons in staff notifications")
        await ctx.send(embed=embed)





    @commands.hybrid_command(name="appealinfo")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(appeal_id="The ID of the appeal to get information about")
    async def appealinfo(self, ctx, appeal_id: int):
        """Get detailed information about an appeal"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, reason, status, timestamp FROM unban_requests WHERE id = ?', (appeal_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            embed = create_error_embed("Appeal Not Found", f"No appeal found with ID #{appeal_id}")
            await ctx.send(embed=embed)
            return
        
        user_id, reason, status, timestamp = result
        
        try:
            user = await self.bot.fetch_user(user_id)
            user_info = f"{user} ({user.id})"
            account_created = user.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            user_info = f"Unknown User ({user_id})"
            account_created = "Unknown"
        
        embed = discord.Embed(title=f'Appeal #{appeal_id} Details', color=0x0000ff)
        embed.add_field(name="User", value=user_info, inline=True)
        embed.add_field(name="Status", value=status.title(), inline=True)
        embed.add_field(name="Submitted", value=timestamp, inline=True)
        embed.add_field(name="Account Created", value=account_created, inline=True)
        embed.add_field(name="Appeal Content", value=reason[:1000] + "..." if len(reason) > 1000 else reason, inline=False)
        
        await ctx.send(embed=embed)


    
    @commands.hybrid_command(name="appealcancel")
    @app_commands.describe()
    async def appeal_cancel(self, ctx):
        """Cancel your own pending appeal (users can use this, staff can add @user to cancel another's appeal)"""
        # Check if user has a pending appeal
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM unban_requests WHERE user_id = ? AND status = "pending"', (ctx.author.id,))
        result = cursor.fetchone()
        
        if not result:
            embed = create_error_embed(
                "No Pending Appeal",
                "You don't have any pending appeals to cancel."
            )
            await _safe_ctx_send(ctx, embed=embed, ephemeral=True)
            conn.close()
            return
        
        appeal_id = result[0]
        
        # Ask for confirmation
        confirm_embed = discord.Embed(
            title="Cancel Appeal?",
            description=f"Are you sure you want to cancel appeal **#{appeal_id}**?\n\nYou can submit a new appeal after this is cancelled.",
            color=0xf39c12
        )
        
        class CancelConfirmView(discord.ui.View):
            def __init__(self, cog_ref: 'Appeals', appeal_id_val: int, user_id: int, author_id: int):
                super().__init__(timeout=60)
                self.confirmed = False
                self.cog_ref = cog_ref
                self.appeal_id_val = appeal_id_val
                self.user_id_val = user_id
                self.author_id = author_id
            
            @discord.ui.button(label="Yes, Cancel", style=discord.ButtonStyle.red)
            async def confirm(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != self.author_id:
                    await button_interaction.response.send_message("This button is not for you.", ephemeral=True)
                    return
                
                self.confirmed = True
                
                # Delete the appeal from database
                conn = sqlite3.connect(DATABASE_NAME)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM unban_requests WHERE id = ?', (self.appeal_id_val,))
                conn.commit()
                conn.close()
                
                result_embed = discord.Embed(
                    title="Appeal Cancelled",
                    description=f"Your appeal **#{self.appeal_id_val}** has been cancelled successfully.\n\nYou can submit a new appeal at any time.",
                    color=0x00ff00
                )
                result_embed.set_footer(text=_appeals_footer_text(button_interaction.guild.name if button_interaction.guild else None))
                result_embed.timestamp = datetime.now(timezone.utc)
                await button_interaction.response.send_message(embed=result_embed, ephemeral=True)
                
                print(f"[Appeals] Appeal #{self.appeal_id_val} cancelled by {button_interaction.user} ({self.author_id})")
            
            @discord.ui.button(label="No, Keep It", style=discord.ButtonStyle.green)
            async def cancel(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != self.author_id:
                    await button_interaction.response.send_message("This button is not for you.", ephemeral=True)
                    return
                
                result_embed = discord.Embed(
                    title="Cancelled",
                    description="Your appeal was not cancelled.",
                    color=0x95a5a6
                )
                result_embed.set_footer(text=_appeals_footer_text(button_interaction.guild.name if button_interaction.guild else None))
                result_embed.timestamp = datetime.now(timezone.utc)
                await button_interaction.response.send_message(embed=result_embed, ephemeral=True)
        
        view = CancelConfirmView(self, appeal_id, ctx.author.id, ctx.author.id)
        await _safe_ctx_send(ctx, embed=confirm_embed, view=view, ephemeral=True)
    
    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        self._timeout_dedupe_cache.clear()
        self._ban_event_handled.clear()
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Log when a user is manually unbanned"""
        try:
            # Check if there are pending appeals for this user
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM unban_requests WHERE user_id = ? AND status = "pending" ORDER BY id DESC LIMIT 1', (user.id,))
            appeal = cursor.fetchone()
            conn.close()
            
            if appeal:
                print(f"[Appeals] Manual unban detected for user {user.id} with pending appeal #{appeal[0]}")
                
                # IMMEDIATELY mark as auto-resolved and disable buttons
                try:
                    conn = sqlite3.connect(DATABASE_NAME)
                    cursor = conn.cursor()
                    cursor.execute('UPDATE unban_requests SET status = "auto_resolved" WHERE id = ?', (appeal[0],))
                    conn.commit()
                    conn.close()
                    
                    # Disable buttons immediately
                    await self._disable_appeal_buttons_by_id(appeal[0], guild.id)
                    print(f"[Appeals] Auto-resolved appeal #{appeal[0]} and disabled buttons due to manual unban")
                except Exception as e:
                    print(f"[Appeals] Error auto-resolving appeal #{appeal[0]}: {e}")
                
                # Get audit log entry to see who unbanned the user
                try:
                    async for entry in guild.audit_logs(action=discord.AuditLogAction.unban, limit=5):
                        if entry.target and entry.target.id == user.id:
                            # Create log message
                            log_embed = discord.Embed(
                                title="Manual Unban Detected",
                                description=f"User {user.mention} (`{user.id}`) was manually unbanned while having a pending appeal.",
                                color=0xff9900
                            )
                            log_embed.add_field(name="Unbanned By", value=f"{entry.user.mention}" if entry.user else "Unknown", inline=True)
                            log_embed.add_field(name="Appeal ID", value=f"#{appeal[0]}", inline=True)
                            log_embed.add_field(name="Action", value="Appeal automatically resolved and buttons disabled", inline=False)
                            log_embed.set_footer(text=f"{_appeals_footer_text(guild.name)} • User: {user.name}")
                            log_embed.timestamp = datetime.now(timezone.utc)
                            
                            # Try to send to appeals channel or log it
                            appeals_channels = [channel for channel in guild.text_channels if 'appeal' in channel.name.lower()]
                            if appeals_channels:
                                await appeals_channels[0].send(embed=log_embed)
                            else:
                                print(f"[Appeals] {log_embed.description}")
                            break
                except Exception as e:
                    print(f"[Appeals] Error checking audit log for unban: {e}")
                    
        except Exception as e:
            print(f"[Appeals] Error in on_member_unban: {e}")
    
    @commands.hybrid_command(
        name="check_appeals", 
        description="Check for appeals that may no longer be valid due to expired/removed punishments"
    )
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def check_appeals(self, ctx: commands.Context):
        """Check all pending appeals for validity"""
        try:
            # Send initial processing message
            processing_msg = await ctx.send("Checking pending appeals...")
            
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('SELECT id, user_id, reason FROM unban_requests WHERE status = "pending"')
            pending_appeals = cursor.fetchall()
            conn.close()
            
            if not pending_appeals:
                embed = create_success_embed(
                    "Appeal Check Complete",
                    "No pending appeals found.",
                    guild_name=ctx.guild.name if ctx.guild else None,
                )
                await processing_msg.edit(content=None, embed=embed)
                return
            
            invalid_appeals = []
            valid_appeals = []
            
            for appeal_id, user_id, reason in pending_appeals:
                # Check ban status
                try:
                    if ctx.guild:
                        await ctx.guild.fetch_ban(discord.Object(id=user_id))
                        valid_appeals.append((appeal_id, user_id, "Still banned"))
                        continue
                except discord.NotFound:
                    invalid_appeals.append((appeal_id, user_id, "No longer banned"))
                    continue
                except discord.Forbidden:
                    valid_appeals.append((appeal_id, user_id, "Cannot check ban status"))
                    continue
                
                # Check timeout status
                if ctx.guild:
                    member = ctx.guild.get_member(user_id)
                    if member:
                        timeout_until = getattr(member, 'timed_out_until', None)
                        if timeout_until and timeout_until > datetime.now(timezone.utc):
                            valid_appeals.append((appeal_id, user_id, f"Still timed out until <t:{int(timeout_until.timestamp())}:F>"))
                        else:
                            invalid_appeals.append((appeal_id, user_id, "Timeout expired or removed"))
                    else:
                        invalid_appeals.append((appeal_id, user_id, "User left the server"))
            
            embed = create_info_embed(
                "Appeal Validity Check",
                f"Found {len(pending_appeals)} pending appeals",
                guild_name=ctx.guild.name if ctx.guild else None,
            )
            
            if valid_appeals:
                valid_text = "\\n".join([f"#{aid}: <@{uid}> - {status}" for aid, uid, status in valid_appeals[:10]])
                embed.add_field(name=f"Valid Appeals ({len(valid_appeals)})", value=valid_text, inline=False)
            
            if invalid_appeals:
                invalid_text = "\\n".join([f"#{aid}: <@{uid}> - {status}" for aid, uid, status in invalid_appeals[:10]])
                embed.add_field(name=f"Invalid Appeals ({len(invalid_appeals)})", value=invalid_text, inline=False)
                
                # Auto-resolve invalid appeals
                conn = sqlite3.connect(DATABASE_NAME)
                cursor = conn.cursor()
                for appeal_id, user_id, status in invalid_appeals:
                    cursor.execute('UPDATE unban_requests SET status = "auto_resolved" WHERE id = ?', (appeal_id,))
                    print(f"[Appeals] Auto-resolved appeal #{appeal_id} - {status}")
                conn.commit()
                conn.close()
                
                embed.add_field(name="Action Taken", value="Invalid appeals have been automatically resolved", inline=False)
            
            if len(valid_appeals) > 10 or len(invalid_appeals) > 10:
                embed.set_footer(text=f"{_appeals_footer_text(ctx.guild.name if ctx.guild else None)} • Showing first 10 of each category")
            
            await processing_msg.edit(content=None, embed=embed)
            
        except Exception as e:
            print(f"[Appeals] Error in check_appeals: {e}")
            error_embed = create_error_embed("Error", f"Failed to check appeals: {e}")
            if 'processing_msg' in locals():
                await processing_msg.edit(content=None, embed=error_embed)
            else:
                await ctx.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Appeals(bot))
