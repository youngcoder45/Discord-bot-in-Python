import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import sys
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import MODERATION_ROLE_ID

from utils.database import DATABASE_NAME, init_db
from utils.embeds import create_error_embed, create_success_embed, create_info_embed


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
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle appeal submission"""
        try:
            # Check if user still has punishment
            is_punished = await self._check_punishment_active(interaction.user)
            if not is_punished:
                await interaction.response.send_message(
                    embed=create_error_embed(
                        "Punishment Expired",
                        "Your punishment appears to have been lifted. No appeal is needed."
                    ),
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
            
            print(f"[Appeals] ✅ Appeal #{appeal_id} submitted by {interaction.user} ({interaction.user.id}) - {self.punishment_type} in {self.guild.name}")
            
            # Send confirmation to user
            success_embed = discord.Embed(
                title="✅ Appeal Submitted Successfully",
                description="Your appeal has been submitted to our moderation team.",
                color=0x2ecc71
            )
            success_embed.add_field(name="📋 Appeal ID", value=f"#{appeal_id}", inline=True)
            success_embed.add_field(name="📊 Status", value="Pending Review", inline=True)
            success_embed.add_field(name="⏱️ Review Time", value="24-48 hours", inline=True)
            success_embed.set_footer(text=f"{self.guild.name} • Professional Moderation")
            
            await interaction.response.send_message(embed=success_embed, ephemeral=False)
            
            # Send to staff channel
            if appeal_id:
                await self._send_staff_notification(appeal_id, interaction.user, appeal_content)
            
        except Exception as e:
            print(f"[Appeals] ❌ Error submitting appeal: {e}")
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Submission Error",
                    "There was an error submitting your appeal. Please try again later."
                ),
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
        for cid in (1423642446616592385, 1399746928585085068):
            ch = self.cog.bot.get_channel(cid)
            if ch:
                staff_channel = ch
                break
        
        if staff_channel:
            staff_embed = discord.Embed(
                title="📨 New Appeal Submitted",
                description=f"Appeal #{appeal_id} from {user}",
                color=0x3498db
            )
            trimmed = content[:800] + ("..." if len(content) > 800 else "")
            staff_embed.add_field(name="👤 User", value=f"{user} ({user.id})", inline=True)
            staff_embed.add_field(name="⚠️ Punishment", value=f"{self.punishment_type.title()} in {self.guild.name}", inline=True)
            staff_embed.add_field(name="📝 Appeal Content", value=f"```{trimmed}```", inline=False)
            staff_embed.add_field(name="🔧 Review", value="Use the buttons below to approve or deny this appeal", inline=False)
            
            # Create view with approve/deny buttons
            view = AppealReviewView(self.cog, appeal_id, user.id, content, self.punishment_type, self.guild.name)
            staff_embed.timestamp = datetime.now(timezone.utc)
            
            try:
                await staff_channel.send(embed=staff_embed, view=view)
            except Exception as e:
                print(f"[Appeals] ❌ Failed to send staff notification: {e}")


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
            print(f"[Appeals] ❌ Error in approval modal: {e}")
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
            embed = discord.Embed(title='✅ Appeal Approved', color=0x2ecc71)
            embed.add_field(name='Appeal ID', value=f"#{self.appeal_id}", inline=True)
            embed.add_field(name='User', value=f'{display_target} ({self.user_id})', inline=True)
            embed.add_field(name='Action', value=action_taken or 'Completed', inline=True)
            embed.add_field(name='Approved By', value=interaction.user.mention, inline=True)
            embed.add_field(name='Reason', value=reason, inline=False)
            await interaction.followup.send(embed=embed)
            
            # Disable the buttons in the original message
            await self._disable_appeal_buttons(interaction)
            
            # DM user
            if user:
                try:
                    dm = discord.Embed(
                        title="✅ Appeal Approved",
                        description=f"## Your appeal has been reviewed and **approved**\n\nWelcome back to **{guild.name if guild else 'the server'}**! We're glad to have you return.",
                        color=0x2ecc71
                    )
                    dm.add_field(name="📋 Appeal ID", value=f"`#{self.appeal_id}`", inline=True)
                    dm.add_field(name="📊 Result", value=f"**{action_taken or 'Processed'}**", inline=True)
                    dm.add_field(name="📝 Staff Response", value=f"```{reason}```", inline=False)
                    dm.add_field(
                        name="🚀 Moving Forward",
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
            embed = discord.Embed(title='❌ Appeal Denied', color=0xe74c3c)
            embed.add_field(name='Appeal ID', value=f"#{self.appeal_id}", inline=True)
            embed.add_field(name='User ID', value=str(self.user_id), inline=True)
            embed.add_field(name='Denied By', value=interaction.user.mention, inline=True)
            embed.add_field(name='Reason', value=reason, inline=False)
            await interaction.followup.send(embed=embed)
            
            # Disable the buttons in the original message
            await self._disable_appeal_buttons(interaction)
            
            # DM user
            try:
                user = await self.cog.bot.fetch_user(self.user_id)
                embed_dm = discord.Embed(
                    title="❌ Appeal Denied",
                    description=f"## Your appeal has been reviewed\n\nAfter careful consideration, your appeal for **{interaction.guild.name if interaction.guild else 'the server'}** has been denied.",
                    color=0xe74c3c
                )
                embed_dm.add_field(name="📋 Appeal ID", value=f"`#{self.appeal_id}`", inline=True)
                embed_dm.add_field(name="👮 Reviewed By", value=str(interaction.user), inline=True)
                embed_dm.add_field(name="📝 Staff Response", value=f"```{reason}```", inline=False)
                embed_dm.add_field(
                    name="🔄 Submit Another Appeal",
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
            print(f"[Appeals] ❌ Error in denial modal: {e}")
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
    
    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green, emoji="✅")
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
    
    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, emoji="❌")
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
    """View with Send Appeal button"""
    
    def __init__(self, cog, guild: discord.Guild, punishment_type: str, reason: str, user_id: int):
        super().__init__(timeout=None)  # Persistent view
        self.cog = cog
        self.guild = guild
        self.punishment_type = punishment_type
        self.reason = reason
        self.user_id = user_id
    
    @discord.ui.button(label="Send Appeal", style=discord.ButtonStyle.primary, emoji="📝")
    async def send_appeal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open appeal modal"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ This button is not for you.", ephemeral=True
            )
            return
        
        # Check if user already has a pending appeal
        conn = sqlite3.connect(DATABASE_NAME)
        cur = conn.cursor()
        cur.execute('SELECT id FROM unban_requests WHERE user_id = ? AND status = "pending"', 
                   (interaction.user.id,))
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
        
        # Open modal
        modal = AppealModal(self.cog, self.guild, self.punishment_type, self.reason)
        await interaction.response.send_modal(modal)



class Appeals(commands.Cog):
    """Unban appeal system with auto-DM for moderation actions"""

    def __init__(self, bot):
        self.bot = bot
        init_db()
        self._timeout_dedupe_cache = {}  # {(user_id, guild_id, action): timestamp} - prevents double DM
        self._appeal_cleanup_task = None
        self._setup_appeal_cleanup_task()
        self._ban_event_handled = set()  # Track recently handled ban events to prevent duplicates
        
    def _setup_appeal_cleanup_task(self):
        """Start background task to clean up expired appeals"""
        if self._appeal_cleanup_task is None or self._appeal_cleanup_task.done():
            self._appeal_cleanup_task = asyncio.create_task(self._cleanup_expired_appeals())
            
    async def _cleanup_expired_appeals(self):
        """Background task that checks for appeals where punishment is expired and disables buttons"""
        try:
            print("[Appeals] Background cleanup task started - checking for expired punishments every 1500 seconds (debug mode)")
            while not self.bot.is_closed():
                # Run every 1500 seconds (25 minutes) for testing (normally 5 minutes)
                await asyncio.sleep(1500)
                
                print("[Appeals] Running background cleanup check for expired punishments...")
                
                # Get all pending appeals with their message info
                conn = sqlite3.connect(DATABASE_NAME)
                cursor = conn.cursor()
                cursor.execute('SELECT id, user_id, reason FROM unban_requests WHERE status = "pending"')
                pending_appeals = cursor.fetchall()
                conn.close()
                
                if not pending_appeals:
                    print("[Appeals] No pending appeals found for cleanup")
                    continue
                
                print(f"[Appeals] Found {len(pending_appeals)} pending appeals to check")
                resolved_appeals = []
                
                for appeal_id, user_id, reason in pending_appeals:
                    # Check all guilds the bot is in
                    for guild in self.bot.guilds:
                        punishment_resolved = False
                        status_message = ""
                        
                        try:
                            print(f"[Appeals] Checking appeal #{appeal_id} for user {user_id} in guild {guild.name}")
                            
                            # Check if user is still banned
                            try:
                                await guild.fetch_ban(discord.Object(id=user_id))
                                # User is still banned, appeal is valid
                                print(f"[Appeals] User {user_id} is still banned in {guild.name}, appeal #{appeal_id} remains valid")
                                continue
                            except discord.NotFound:
                                # User is not banned
                                punishment_resolved = True
                                status_message = "User is no longer banned"
                                print(f"[Appeals] User {user_id} is no longer banned in {guild.name}, appeal #{appeal_id} should be resolved")
                            except discord.Forbidden:
                                # Can't check ban status, assume valid
                                print(f"[Appeals] Cannot check ban status for user {user_id} in {guild.name}, assuming valid")
                                continue
                            
                            # If not banned, check timeout status
                            if not punishment_resolved:
                                member = guild.get_member(user_id)
                                if member:
                                    timeout_until = getattr(member, 'timed_out_until', None)
                                    current_time = datetime.now(timezone.utc)
                                    
                                    if not timeout_until:
                                        # User has no timeout, could be manually removed or never had one
                                        punishment_resolved = True
                                        status_message = "User timeout has been removed or expired"
                                        print(f"[Appeals] User {user_id} has no timeout in {guild.name}, appeal #{appeal_id} should be resolved")
                                    elif timeout_until <= current_time:
                                        # Timeout has naturally expired
                                        punishment_resolved = True
                                        status_message = f"User timeout naturally expired at <t:{int(timeout_until.timestamp())}:F>"
                                        print(f"[Appeals] User {user_id} timeout expired naturally at {timeout_until} in {guild.name}, appeal #{appeal_id} should be resolved")
                                    else:
                                        print(f"[Appeals] User {user_id} is still timed out until {timeout_until} in {guild.name}, appeal #{appeal_id} remains valid")
                                else:
                                    # User not in server
                                    punishment_resolved = True
                                    status_message = "User is no longer in the server"
                                    print(f"[Appeals] User {user_id} is not in {guild.name}, appeal #{appeal_id} should be resolved")
                            
                            if punishment_resolved:
                                resolved_appeals.append((appeal_id, user_id, guild.id, status_message))
                                print(f"[Appeals] Auto-resolved appeal #{appeal_id} - {status_message}")
                                break  # Found the guild where punishment was resolved
                        
                        except Exception as e:
                            print(f"[Appeals] Error checking appeal #{appeal_id} in guild {guild.id}: {e}")
                            continue
                
                # Update database and disable buttons for resolved appeals
                if resolved_appeals:
                    print(f"[Appeals] Processing {len(resolved_appeals)} resolved appeals for database update and button disabling")
                    conn = sqlite3.connect(DATABASE_NAME)
                    cursor = conn.cursor()
                    
                    for appeal_id, user_id, guild_id, status_msg in resolved_appeals:
                        print(f"[Appeals] Processing appeal #{appeal_id}: {status_msg}")
                        
                        # Mark as auto-resolved in database
                        cursor.execute('UPDATE unban_requests SET status = "auto_resolved" WHERE id = ?', (appeal_id,))
                        
                        # Try to find and disable buttons in appeal messages
                        print(f"[Appeals] Attempting to disable buttons for appeal #{appeal_id}")
                        await self._disable_appeal_buttons_by_id(appeal_id, guild_id)
                        
                        # Log to appeals channel
                        print(f"[Appeals] Attempting to log punishment expiry for appeal #{appeal_id}")
                        await self._log_punishment_expiry(appeal_id, user_id, guild_id, status_msg)
                    
                    conn.commit()
                    conn.close()
                    
                    print(f"[Appeals] Auto-resolved {len(resolved_appeals)} expired appeals and disabled their buttons")
                else:
                    print("[Appeals] No appeals needed resolution during this cleanup cycle")
                
        except asyncio.CancelledError:
            print("[Appeals] Appeal cleanup task cancelled")
        except Exception as e:
            print(f"[Appeals] Error in appeal cleanup task: {e}")
            # Restart the task after a delay
            await asyncio.sleep(60)
            self._setup_appeal_cleanup_task()
    
    async def _disable_appeal_buttons_by_id(self, appeal_id: int, guild_id: int):
        """Find and disable appeal buttons in messages for a specific appeal ID"""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
            
            # Look for appeals channels where buttons might be
            appeals_channels = [
                channel for channel in guild.text_channels 
                if 'appeal' in channel.name.lower() or 'unban' in channel.name.lower()
            ]
            
            # Add some common moderation channel names
            mod_channels = [
                channel for channel in guild.text_channels 
                if any(name in channel.name.lower() for name in ['mod', 'staff', 'admin', 'log'])
            ]
            
            search_channels = appeals_channels + mod_channels
            
            for channel in search_channels:
                try:
                    # Search recent messages (last 50) for this appeal ID
                    async for message in channel.history(limit=50):
                        if (message.author.id == self.bot.user.id and 
                            message.embeds and 
                            f"Appeal #{appeal_id}" in str(message.embeds[0].to_dict()) and
                            message.components):
                            
                            # Found the appeal message with components
                            # Create new disabled view
                            new_view = discord.ui.View(timeout=None)
                            
                            # Add disabled buttons
                            approve_button = discord.ui.Button(
                                label="Appeal Resolved", 
                                style=discord.ButtonStyle.gray, 
                                emoji="✅", 
                                disabled=True
                            )
                            deny_button = discord.ui.Button(
                                label="Appeal Resolved", 
                                style=discord.ButtonStyle.gray, 
                                emoji="❌", 
                                disabled=True
                            )
                            
                            new_view.add_item(approve_button)
                            new_view.add_item(deny_button)
                            
                            # Update the message
                            await message.edit(view=new_view)
                            print(f"[Appeals] Disabled buttons for appeal #{appeal_id} in {channel.name}")
                            return
                            
                except Exception as e:
                    print(f"[Appeals] Error searching channel {channel.name}: {e}")
                    continue
                    
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
                title = "⏰ Appeal Auto-Resolved - Timeout Naturally Expired"
                color = 0x95a5a6  # Gray for natural expiration
                description = f"Appeal #{appeal_id} has been automatically resolved because the timeout naturally expired."
            elif is_ban_removal:
                title = "🔓 Appeal Auto-Resolved - Ban Removed"
                color = 0x3498db  # Blue for ban removal
                description = f"Appeal #{appeal_id} has been automatically resolved because the ban was removed."
            else:
                title = "⚠️ Appeal Auto-Resolved - Punishment Invalid"
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
                name="👤 User",
                value=str(user),
                inline=True
            )
            
            log_embed.add_field(
                name="📋 Appeal ID",
                value=f"#{appeal_id}",
                inline=True
            )
            
            log_embed.add_field(
                name="📝 Details",
                value=status_message,
                inline=False
            )
            
            log_embed.add_field(
                name="🔄 Action",
                value="Appeal buttons have been automatically disabled",
                inline=False
            )
            
            log_embed.set_footer(text=f"Guild: {guild.name}", icon_url=guild.icon.url if guild.icon else None)
            
            # Send to appeals channel
            print(f"[Appeals] Sending log embed to {appeals_channels[0].name}")
            await appeals_channels[0].send(embed=log_embed)
            print(f"[Appeals] 📝 Successfully logged punishment expiry for appeal #{appeal_id} to {appeals_channels[0].name}")
            
        except Exception as e:
            print(f"[Appeals] Error logging punishment expiry for appeal #{appeal_id}: {e}")
            import traceback
            traceback.print_exc()

    async def _send_appeal_form(self, user: discord.User | discord.Member, guild: discord.Guild, action_type: str, reason: str | None = None):
        """Send appeal form with modal button to user"""
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
            
            # Modern appeal form with button
            embed = discord.Embed(
                title="⚖️ Moderation Appeal System",
                description=f"## You have been **{action_type}** from {guild.name}\n\nWe understand mistakes happen. You have the right to appeal this decision.",
                color=0x5865F2
            )
            
            if reason and reason != "No reason provided":
                embed.add_field(
                    name="📋 Reason for Action",
                    value=f"```{reason}```",
                    inline=False
                )
            
            embed.add_field(
                name="📝 How to Submit Your Appeal",
                value=(
                    "**Click the button below** to open the appeal form.\n\n"
                    "The form will ask you to:\n"
                    "• Confirm what punishment you're appealing\n"
                    "• Explain why you think you were punished\n"
                    "• Provide your appeal message with what you've learned"
                ),
                inline=False
            )
            
            embed.add_field(
                name="⏱️ Processing Time",
                value="Staff typically review appeals within 24-48 hours.",
                inline=True
            )
            
            embed.add_field(
                name="📬 Next Steps",
                value="Your appeal will be forwarded to our moderation team.",
                inline=True
            )
            
            embed.set_footer(
                text=f"{guild.name} • Professional Moderation System",
                icon_url=guild.icon.url if guild.icon else None
            )
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            
            # Create view with appeal button
            view = AppealButtonView(self, guild, action_type, reason or "No reason provided", user.id)
            
            await user.send(embed=embed, view=view)
            dm_success = True
            print(f"[Appeals] ✅ Sent appeal form with button to {user} ({user.id}) for {action_type} in {guild.name}")
            
            # Log success to appeals channel
            await self._log_dm_success(user, guild, action_type, reason or "No reason provided")
        except discord.Forbidden:
            dm_error = "DMs are closed or bot is blocked"
            print(f"[Appeals] ❌ Cannot DM {user} ({user.id}) - DMs closed or bot blocked")
        except Exception as e:
            dm_error = str(e)
            print(f"[Appeals] ❌ DM error to {user} ({user.id}): {e}")
        
        # Log DM failure to appeals channel
        if not dm_success and dm_error:
            await self._log_dm_failure(user, guild, action_type, reason or "No reason provided", dm_error)
    
    async def _log_dm_failure(self, user: discord.User | discord.Member, guild: discord.Guild, action_type: str, reason: str, error: str):
        """Log to appeals channel when DM fails"""
        for cid in (1423642446616592385, 1399746928585085068):
            ch = self.bot.get_channel(cid)
            if ch:
                embed = discord.Embed(
                    title="⚠️ Appeal DM Failed",
                    description=f"**Could not send appeal form to {user.mention}**\n\nUser will NOT be able to submit an appeal via DM.",
                    color=0xe67e22
                )
                embed.add_field(name="👤 User", value=f"{user} ({user.id})", inline=True)
                embed.add_field(name="🏛️ Guild", value=guild.name, inline=True)
                embed.add_field(name="⚠️ Action", value=action_type.title(), inline=True)
                embed.add_field(name="📋 Reason", value=reason or "No reason provided", inline=False)
                embed.add_field(name="❌ Error", value=f"```{error}```", inline=False)
                embed.add_field(
                    name="💡 Note", 
                    value="This user's DMs are blocked. They cannot submit appeals through the bot. Consider alternative appeal methods or manual review.",
                    inline=False
                )
                embed.timestamp = datetime.now(timezone.utc)
                embed.set_footer(text="Appeals System - DM Delivery Failed")
                try:
                    await ch.send(embed=embed)
                    print(f"[Appeals] 📝 Logged DM failure to channel {cid}")
                except Exception as e:
                    print(f"[Appeals] Failed to send DM failure log to channel {cid}: {e}")
                break
    
    async def _log_dm_success(self, user: discord.User | discord.Member, guild: discord.Guild, action_type: str, reason: str):
        """Log to appeals channel when DM is successfully sent"""
        for cid in (1423642446616592385, 1399746928585085068):
            ch = self.bot.get_channel(cid)
            if ch:
                embed = discord.Embed(
                    title="📧 Appeal DM Sent",
                    description=f"Successfully sent appeal form to {user.mention}",
                    color=0x2ecc71
                )
                embed.add_field(name="👤 User", value=f"{user} ({user.id})", inline=True)
                embed.add_field(name="🏛️ Guild", value=guild.name, inline=True)
                embed.add_field(name="⚠️ Action", value=action_type.title(), inline=True)
                embed.add_field(name="📋 Reason", value=reason or "No reason provided", inline=False)
                embed.timestamp = datetime.now(timezone.utc)
                embed.set_footer(text="Appeals System")
                try:
                    await ch.send(embed=embed)
                except Exception as e:
                    print(f"[Appeals] Failed to send DM success log to channel {cid}: {e}")
                break

    # ---------------- Listeners ----------------
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Handle ban events and send appeals - PRIMARY ban handler"""
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
        
        print(f"[Appeals] 🚫 Ban detected for {user} ({user.id}) in {guild.name}: {reason}")
        
        # Send appeal form (logs will be sent by _send_appeal_form)
        await self._send_appeal_form(user, guild, "banned", reason)

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
                        log_title = "⏰ Natural Timeout Expiry Detected"
                        log_description = f"User {after.mention} (`{after.id}`) had their timeout naturally expire while having a pending appeal."
                        color = 0x95a5a6  # Gray for natural expiry
                    else:
                        print(f"[Appeals] Manual timeout removal detected for user {after.id} with pending appeal #{appeal[0]}")
                        action_text = "Manual timeout removal"
                        log_title = "⚠️ Manual Timeout Removal Detected"
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
            
            print(f"[Appeals] ⏱️ Timeout APPLIED to {after} ({after.id}): before={before_timeout}, after={after_timeout}, reason={reason}")
            
            # Send appeal form (logs will be sent by _send_appeal_form)
            await self._send_appeal_form(after, after.guild, "timed out", reason)
        
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
                    print(f"[Appeals] ✅ Auto-approved appeal #{appeal_id} - timeout removed for {after} ({after.id})")
                
                conn.commit()
                
                # Try to DM the user about approval
                try:
                    dm = discord.Embed(
                        title="✅ Appeal Automatically Approved",
                        description=f"## Your appeal has been automatically approved\n\nYour timeout in **{after.guild.name}** has been removed.",
                        color=0x2ecc71
                    )
                    dm.add_field(name="📋 Result", value="**Timeout removed**", inline=True)
                    dm.set_footer(text=f"{after.guild.name} • Moderation System")
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
        
        embed = discord.Embed(title=f'{status.title()} Appeals', color=0x3498db)
        
        for appeal in appeals:
            appeal_id, user_id, reason, appeal_status, timestamp = appeal
            try:
                user = await self.bot.fetch_user(user_id)
                user_name = f"{user} ({user_id})"
            except:
                user_name = f"Unknown ({user_id})"
            
            status_emoji = {"pending": "🟡", "approved": "🟢", "denied": ""}.get(appeal_status, "")
            
            embed.add_field(
                name=f'{status_emoji} Appeal #{appeal_id}', 
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
        
        status_emoji = {"pending": "🟡", "approved": "🟢", "denied": ""}.get(status, "")
        
        embed = discord.Embed(title=f'{status_emoji} Appeal #{appeal_id} Details', color=0x3498db)
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
            await ctx.send(embed=embed, ephemeral=True)
            conn.close()
            return
        
        appeal_id = result[0]
        
        # Ask for confirmation
        confirm_embed = discord.Embed(
            title="⚠️ Cancel Appeal?",
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
            
            @discord.ui.button(label="✅ Yes, Cancel", style=discord.ButtonStyle.red)
            async def confirm(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != self.author_id:
                    await button_interaction.response.send_message("❌ This button is not for you.", ephemeral=True)
                    return
                
                self.confirmed = True
                
                # Delete the appeal from database
                conn = sqlite3.connect(DATABASE_NAME)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM unban_requests WHERE id = ?', (self.appeal_id_val,))
                conn.commit()
                conn.close()
                
                result_embed = discord.Embed(
                    title="✅ Appeal Cancelled",
                    description=f"Your appeal **#{self.appeal_id_val}** has been cancelled successfully.\n\nYou can submit a new appeal at any time.",
                    color=0x2ecc71
                )
                await button_interaction.response.send_message(embed=result_embed, ephemeral=True)
                
                print(f"[Appeals] 🗑️ Appeal #{self.appeal_id_val} cancelled by {button_interaction.user} ({self.author_id})")
            
            @discord.ui.button(label="❌ No, Keep It", style=discord.ButtonStyle.green)
            async def cancel(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != self.author_id:
                    await button_interaction.response.send_message("❌ This button is not for you.", ephemeral=True)
                    return
                
                result_embed = discord.Embed(
                    title="Cancelled",
                    description="Your appeal was not cancelled.",
                    color=0x95a5a6
                )
                await button_interaction.response.send_message(embed=result_embed, ephemeral=True)
        
        view = CancelConfirmView(self, appeal_id, ctx.author.id, ctx.author.id)
        await ctx.send(embed=confirm_embed, view=view, ephemeral=True)
    
    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        if self._appeal_cleanup_task and not self._appeal_cleanup_task.done():
            self._appeal_cleanup_task.cancel()
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
                                title="⚠️ Manual Unban Detected",
                                description=f"User {user.mention} (`{user.id}`) was manually unbanned while having a pending appeal.",
                                color=0xff9900
                            )
                            log_embed.add_field(name="Unbanned By", value=f"{entry.user.mention}" if entry.user else "Unknown", inline=True)
                            log_embed.add_field(name="Appeal ID", value=f"#{appeal[0]}", inline=True)
                            log_embed.add_field(name="Action", value="Appeal automatically resolved and buttons disabled", inline=False)
                            log_embed.set_footer(text=f"User: {user.name}")
                            
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
            processing_msg = await ctx.send("🔍 Checking pending appeals...")
            
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('SELECT id, user_id, reason FROM unban_requests WHERE status = "pending"')
            pending_appeals = cursor.fetchall()
            conn.close()
            
            if not pending_appeals:
                embed = discord.Embed(
                    title="✅ Appeal Check Complete",
                    description="No pending appeals found.",
                    color=0x2ecc71
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
            
            embed = discord.Embed(
                title="📋 Appeal Validity Check",
                description=f"Found {len(pending_appeals)} pending appeals",
                color=0x3498db
            )
            
            if valid_appeals:
                valid_text = "\\n".join([f"#{aid}: <@{uid}> - {status}" for aid, uid, status in valid_appeals[:10]])
                embed.add_field(name=f"✅ Valid Appeals ({len(valid_appeals)})", value=valid_text, inline=False)
            
            if invalid_appeals:
                invalid_text = "\\n".join([f"#{aid}: <@{uid}> - {status}" for aid, uid, status in invalid_appeals[:10]])
                embed.add_field(name=f"⚠️ Invalid Appeals ({len(invalid_appeals)})", value=invalid_text, inline=False)
                
                # Auto-resolve invalid appeals
                conn = sqlite3.connect(DATABASE_NAME)
                cursor = conn.cursor()
                for appeal_id, user_id, status in invalid_appeals:
                    cursor.execute('UPDATE unban_requests SET status = "auto_resolved" WHERE id = ?', (appeal_id,))
                    print(f"[Appeals] Auto-resolved appeal #{appeal_id} - {status}")
                conn.commit()
                conn.close()
                
                embed.add_field(name="🔄 Action Taken", value="Invalid appeals have been automatically resolved", inline=False)
            
            if len(valid_appeals) > 10 or len(invalid_appeals) > 10:
                embed.set_footer(text="Showing first 10 of each category")
            
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