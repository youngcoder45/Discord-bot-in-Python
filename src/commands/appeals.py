import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import MODERATION_ROLE_ID

from utils.database import DATABASE_NAME, init_db
from utils.embeds import create_error_embed, create_success_embed, create_info_embed

class Appeals(commands.Cog):
    """Unban appeal system with auto-DM for moderation actions"""
    
    def __init__(self, bot):
        self.bot = bot
        # Ensure database tables exist
        init_db()
    
    async def _send_appeal_form(self, user: discord.User | discord.Member, guild: discord.Guild, action_type: str, reason: str | None = None):
        """Send modern appeal form DM to user"""
        try:
            embed = discord.Embed(
                title="Moderation Action Appeal",
                description=f"You have been {action_type} from **{guild.name}**. If you believe this action was taken in error or would like to appeal, please read the information below.",
                color=0x5865F2  # Discord Blurple
            )
            
            if reason and reason != "No reason provided":
                embed.add_field(
                    name="Reason",
                    value=reason,
                    inline=False
                )
            
            embed.add_field(
                name="Appeal Process",
                value="To submit an appeal, simply reply to this message with:\n"
                      "• A detailed explanation of what happened\n"
                      "• Why you believe the action was incorrect\n"
                      "• What you will do differently in the future",
                inline=False
            )
            
            embed.add_field(
                name="Guidelines",
                value="• Be respectful and honest in your appeal\n"
                      "• Provide specific details about the situation\n"
                      "• Appeals are reviewed within 24-48 hours\n"
                      "• Only one appeal per action is allowed",
                inline=False
            )
            
            embed.add_field(
                name="Alternative Contact",
                value=f"If you're unable to use this system, you can contact server moderators through other means if available.",
                inline=False
            )
            
            embed.set_footer(text=f"Server: {guild.name} | Appeal System")
            
            await user.send(embed=embed)
            
        except discord.Forbidden:
            # User has DMs disabled, silently fail
            pass
        except Exception:
            # Any other error, silently fail
            pass

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        """Auto-send appeal forms for kick, ban, and timeout actions"""
        if not entry.target or not isinstance(entry.target, (discord.User, discord.Member)):
            return
        
        # Check for kick, ban, or timeout actions
        action_type = None
        if entry.action == discord.AuditLogAction.kick:
            action_type = "kicked"
        elif entry.action == discord.AuditLogAction.ban:
            action_type = "banned"
        elif entry.action == discord.AuditLogAction.member_update:
            # Check if this is a timeout action
            if hasattr(entry, 'changes'):
                try:
                    # Discord.py 2.0+ audit log changes structure
                    changes_dict = entry.changes
                    if hasattr(changes_dict, 'timed_out_until') or 'timed_out_until' in str(changes_dict):
                        action_type = "timed out"
                except Exception as e:
                    print(f"Error checking audit log changes: {e}")
        
        if action_type:
            # Send appeal form
            await self._send_appeal_form(
                user=entry.target,
                guild=entry.guild,
                action_type=action_type,
                reason=entry.reason
            )

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Handle timeout detection via member update"""
        # Check if member was timed out (using the correct attribute for discord.py 2.0+)
        before_timeout = before.timed_out_until
        after_timeout = after.timed_out_until
        
        if before_timeout is None and after_timeout is not None:
            # Member was just timed out
            print(f"🚨 Timeout detected for {after.display_name} until {after_timeout}")
            
            # Get timeout reason from audit log
            reason = "Timeout applied"
            try:
                async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=5):
                    if entry.target and entry.target.id == after.id:
                        reason = entry.reason or "Timeout applied"
                        break
            except Exception as e:
                print(f"Could not fetch audit log for timeout: {e}")
            
            await self._send_appeal_form(
                user=after,
                guild=after.guild,
                action_type="timed out",
                reason=reason
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle DM appeals"""
        # Only process DMs to the bot
        if not isinstance(message.channel, discord.DMChannel) or message.author.bot:
            return
        
        # Check if message contains appeal keywords
        content_lower = message.content.lower()
        appeal_keywords = ['unban', 'appeal', 'banned', 'sorry', 'apologize', 'mistake']
        
        if any(keyword in content_lower for keyword in appeal_keywords):
            # Store the appeal in database
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            
            # Check if user already has a pending appeal
            cursor.execute('SELECT id FROM unban_requests WHERE user_id = ? AND status = "pending"', (message.author.id,))
            existing = cursor.fetchone()
            
            if existing:
                embed = discord.Embed(
                    title="Appeal Already Submitted",
                    description="You already have a pending appeal. Please wait for staff to review it.",
                    color=0xf39c12
                )
                embed.set_footer(text="Professional Moderation System")
                await message.author.send(embed=embed)
                conn.close()
                return
            
            # Insert new appeal
            cursor.execute('''
                INSERT INTO unban_requests (user_id, reason)
                VALUES (?, ?)
            ''', (message.author.id, message.content))
            conn.commit()
            appeal_id = cursor.lastrowid
            conn.close()
            
            # Send confirmation to user
            embed = discord.Embed(
                title="Appeal Received",
                description="Your unban appeal has been submitted and will be reviewed by staff.",
                color=0x3498db
            )
            embed.add_field(name="Appeal ID", value=f"#{appeal_id}", inline=True)
            embed.add_field(name="Status", value="Pending Review", inline=True)
            embed.add_field(name="Next Steps", value="Staff will review your appeal and respond within 24-48 hours.", inline=False)
            embed.set_footer(text="Professional Moderation System")
            await message.author.send(embed=embed)
            
            # Notify staff in appeals channel
            appeals_channel_id = 1396353386429026304
            appeals_channel = self.bot.get_channel(appeals_channel_id)
            if appeals_channel:
                embed_staff = discord.Embed(
                    title="New Appeal Submitted",
                    description=f"Appeal #{appeal_id} from {message.author}",
                    color=0x3498db
                )
                embed_staff.add_field(name="User", value=f"{message.author} ({message.author.id})", inline=True)
                embed_staff.add_field(name="Appeal Content", value=message.content[:500] + "..." if len(message.content) > 500 else message.content, inline=False)
                embed_staff.add_field(name="Review Commands", value="`?appeals` to view all\n`?approve <id>` to approve\n`?deny <id> <reason>` to deny", inline=False)
                await appeals_channel.send(embed=embed_staff)

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
            
            status_emoji = {"pending": "🟡", "approved": "🟢", "denied": "🔴"}.get(appeal_status, "⚪")
            
            embed.add_field(
                name=f'{status_emoji} Appeal #{appeal_id}', 
                value=f'**User:** {user_name}\n**Status:** {appeal_status.title()}\n**Reason:** {reason[:100]}{"..." if len(reason) > 100 else ""}\n**Time:** {timestamp}', 
                inline=False
            )
        
        embed.set_footer(text=f"Use ?approve <id> or ?deny <id> <reason> to process appeals")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="approve")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        appeal_id="The ID of the appeal to approve",
        reason="Reason for approving the appeal"
    )
    async def approve(self, ctx, appeal_id: int, *, reason: str = "Appeal approved"):
        """Approve an unban appeal"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM unban_requests WHERE id = ? AND status = "pending"', (appeal_id,))
        result = cursor.fetchone()
        
        if not result:
            embed = create_error_embed("Appeal Not Found", "Appeal not found or already processed.")
            await ctx.send(embed=embed)
            conn.close()
            return
        
        user_id = result[0]
        cursor.execute('UPDATE unban_requests SET status = "approved" WHERE id = ?', (appeal_id,))
        conn.commit()
        conn.close()
        
        # Unban the user
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f'Appeal #{appeal_id} approved by {ctx.author}')
            
            # Clear points for unbanned user
            from utils.database import clear_user_points
            clear_user_points(user_id)
            
            embed = discord.Embed(title='Appeal Approved', color=0x2ecc71)
            embed.add_field(name='Appeal ID', value=f"#{appeal_id}", inline=True)
            embed.add_field(name='User', value=f'{user} ({user_id})', inline=True)
            embed.add_field(name='Approved By', value=ctx.author.mention, inline=True)
            embed.add_field(name='Reason', value=reason, inline=False)
            await ctx.send(embed=embed)
            
            # Send DM to user
            try:
                embed_dm = discord.Embed(
                    title="Appeal Approved",
                    description=f"Your appeal has been approved! You have been unbanned from **{ctx.guild.name}**.",
                    color=0x2ecc71
                )
                embed_dm.add_field(name="Appeal ID", value=f"#{appeal_id}", inline=True)
                embed_dm.add_field(name="Approved By", value=str(ctx.author), inline=True)
                embed_dm.add_field(name="Reason", value=reason, inline=False)
                embed_dm.add_field(name="Welcome Back", value="Please make sure to follow our community guidelines.", inline=False)
                embed_dm.set_footer(text="Professional Moderation System")
                await user.send(embed=embed_dm)
            except:
                pass
                
        except discord.NotFound:
            embed = create_error_embed("User Not Found", "User not found or not banned.")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = create_error_embed("Permission Error", "I don't have permission to unban this user.")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = create_error_embed("Error", f"Error processing appeal: {str(e)}")
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="deny")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        appeal_id="The ID of the appeal to deny",
        reason="Reason for denying the appeal"
    )
    async def deny(self, ctx, appeal_id: int, *, reason: str = "Appeal denied"):
        """Deny an unban appeal"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM unban_requests WHERE id = ? AND status = "pending"', (appeal_id,))
        result = cursor.fetchone()
        
        if not result:
            embed = create_error_embed("Appeal Not Found", "Appeal not found or already processed.")
            await ctx.send(embed=embed)
            conn.close()
            return
        
        user_id = result[0]
        cursor.execute('UPDATE unban_requests SET status = "denied" WHERE id = ?', (appeal_id,))
        conn.commit()
        conn.close()
        
        embed = discord.Embed(title='Appeal Denied', color=0xe74c3c)
        embed.add_field(name='Appeal ID', value=f"#{appeal_id}", inline=True)
        embed.add_field(name='User ID', value=str(user_id), inline=True)
        embed.add_field(name='Denied By', value=ctx.author.mention, inline=True)
        embed.add_field(name='Reason', value=reason, inline=False)
        await ctx.send(embed=embed)
        
        # Send DM to user
        try:
            user = await self.bot.fetch_user(user_id)
            embed_dm = discord.Embed(
                title="Appeal Denied",
                description=f"Your appeal has been denied for **{ctx.guild.name}**.",
                color=0xe74c3c
            )
            embed_dm.add_field(name="Appeal ID", value=f"#{appeal_id}", inline=True)
            embed_dm.add_field(name="Denied By", value=str(ctx.author), inline=True)
            embed_dm.add_field(name="Reason", value=reason, inline=False)
            embed_dm.add_field(name="Future Appeals", value="You may submit another appeal after reflecting on the reason for denial.", inline=False)
            embed_dm.set_footer(text="Professional Moderation System")
            await user.send(embed=embed_dm)
        except:
            pass

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
        
        status_emoji = {"pending": "🟡", "approved": "🟢", "denied": "🔴"}.get(status, "⚪")
        
        embed = discord.Embed(title=f'{status_emoji} Appeal #{appeal_id} Details', color=0x3498db)
        embed.add_field(name="User", value=user_info, inline=True)
        embed.add_field(name="Status", value=status.title(), inline=True)
        embed.add_field(name="Submitted", value=timestamp, inline=True)
        embed.add_field(name="Account Created", value=account_created, inline=True)
        embed.add_field(name="Appeal Content", value=reason[:1000] + "..." if len(reason) > 1000 else reason, inline=False)
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="test_appeal")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(user="User to send a test appeal DM to", action="Type of moderation action (timeout, kick, ban)")
    async def test_appeal(self, ctx, user: discord.Member, action: str = "timeout"):
        """Test the appeal DM system by manually sending an appeal form"""
        valid_actions = ["timeout", "kick", "ban", "timed out", "kicked", "banned"]
        
        if action not in valid_actions:
            embed = create_error_embed("Invalid Action", f"Valid actions: {', '.join(valid_actions)}")
            await ctx.send(embed=embed)
            return
        
        # Normalize action names
        action_map = {
            "timeout": "timed out",
            "kick": "kicked", 
            "ban": "banned"
        }
        action_type = action_map.get(action, action)
        
        try:
            await self._send_appeal_form(
                user=user,
                guild=ctx.guild,
                action_type=action_type,
                reason=f"Test {action_type} action from {ctx.author.mention}"
            )
            
            embed = create_success_embed(
                "Test Appeal Sent",
                f"Successfully sent test appeal DM to {user.mention} for '{action_type}' action."
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed("Failed to Send Appeal", f"Error: {str(e)}")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Appeals(bot))