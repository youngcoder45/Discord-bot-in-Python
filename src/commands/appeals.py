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
        init_db()
        self._timeout_dedupe_cache = {}  # {user_id: timestamp} - prevents double DM within 5s

    # ---------------- Internal Helper ----------------
    async def _send_appeal_form(self, user: discord.User | discord.Member, guild: discord.Guild, action_type: str, reason: str | None = None):
        try:
            if user.bot or (self.bot.user and user.id == self.bot.user.id):
                return
            
            # Dedupe check: if sent within 5s, skip (prevents both audit log + member_update firing)
            import time
            now = time.time()
            last_sent = self._timeout_dedupe_cache.get(user.id)
            if last_sent and (now - last_sent) < 5:
                print(f"[Appeals] Skipped duplicate DM to {user} (sent {now - last_sent:.1f}s ago)")
                return
            self._timeout_dedupe_cache[user.id] = now
            
            # Cleanup old cache entries (keep last 50)
            if len(self._timeout_dedupe_cache) > 50:
                oldest = sorted(self._timeout_dedupe_cache.items(), key=lambda x: x[1])[:25]
                for uid, _ in oldest:
                    del self._timeout_dedupe_cache[uid]
            
            # Modern, professional appeal form
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
                    "**Simply reply to this DM** with your appeal. Include:\n"
                    "• What happened from your perspective\n"
                    "• Why you believe this action was unwarranted\n"
                    "• What you'll do differently moving forward"
                ),
                inline=False
            )
            
            embed.add_field(
                name="⏱️ Processing Time",
                value="Staff typically review appeals within 24-48 hours.",
                inline=True
            )
            
            embed.add_field(
                name="✅ Next Steps",
                value="Your appeal will be forwarded to our moderation team.",
                inline=True
            )
            
            embed.set_footer(
                text=f"{guild.name} • Professional Moderation System",
                icon_url=guild.icon.url if guild.icon else None
            )
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            
            await user.send(embed=embed)
            print(f"[Appeals] Sent appeal form to {user} for {action_type}")
        except discord.Forbidden:
            print(f"[Appeals] Cannot DM {user} (forbidden)")
        except Exception as e:
            print(f"[Appeals] DM error to {user}: {e}")

    # ---------------- Listeners ----------------
    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        if not entry.target or not isinstance(entry.target, (discord.User, discord.Member)):
            return
        if getattr(entry.target, 'bot', False):
            return
        action_type = None
        if entry.action == discord.AuditLogAction.kick:
            action_type = "kicked"
        elif entry.action == discord.AuditLogAction.ban:
            action_type = "banned"
        elif entry.action == discord.AuditLogAction.member_update:
            # timeout detection
            try:
                changes = entry.changes
                if hasattr(changes, 'timed_out_until') or 'timed_out_until' in str(changes):
                    action_type = "timed out"
            except Exception:
                pass
        if action_type:
            await self._send_appeal_form(entry.target, entry.guild, action_type, entry.reason)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if after.bot:
            return
        # Only send appeal form when timeout is APPLIED (not removed)
        if before.timed_out_until is None and after.timed_out_until is not None:
            reason = "Timeout applied"
            try:
                async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=5):
                    if entry.target and entry.target.id == after.id:
                        reason = entry.reason or reason
                        break
            except Exception:
                pass
            await self._send_appeal_form(after, after.guild, "timed out", reason)
            # Log channel notification
            for cid in (1423635286520500406, 1399746928585085068):
                ch = self.bot.get_channel(cid)
                if ch:
                    embed = discord.Embed(
                        title="📨 Appeal DM Sent",
                        description=f"Sent appeal form to {after.mention} (timeout)",
                        color=0x3498db
                    )
                    embed.add_field(name="User", value=f"{after} ({after.id})", inline=True)
                    embed.add_field(name="Until", value=f"<t:{int(after.timed_out_until.timestamp())}:F>", inline=True)
                    embed.add_field(name="Reason", value=reason, inline=False)
                    await ch.send(embed=embed)
                    break

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Phase 1: Accept any first DM as appeal, ignore duplicates. Verify user is still punished."""
        if not isinstance(message.channel, discord.DMChannel) or message.author.bot:
            return
        content = message.content.strip()
        if not content:
            print(f"[Appeals] Empty DM ignored from {message.author.id}")
            return
        
        # Check if user is actually banned or timed out in ANY mutual guild
        is_punished = False
        punishment_type = "unknown"
        guild_name = "the server"
        
        for guild in self.bot.guilds:
            # Check if banned
            try:
                await guild.fetch_ban(discord.Object(id=message.author.id))
                is_punished = True
                punishment_type = "banned"
                guild_name = guild.name
                break
            except discord.NotFound:
                pass
            except Exception:
                pass
            
            # Check if timed out (must be a member)
            member = guild.get_member(message.author.id)
            if member and getattr(member, 'timed_out_until', None):
                is_punished = True
                punishment_type = "timed out"
                guild_name = guild.name
                break
        
        # If not punished, auto-close any approved appeals and reject new appeal
        if not is_punished:
            try:
                embed = discord.Embed(
                    title="❌ No Active Punishment",
                    description="You don't currently have any active punishments (ban or timeout) in our servers.",
                    color=0xe74c3c
                )
                embed.add_field(
                    name="ℹ️ Note",
                    value="Appeals can only be submitted if you have an active punishment. If your punishment was already lifted, no appeal is needed.",
                    inline=False
                )
                await message.author.send(embed=embed)
            except Exception:
                pass
            print(f"[Appeals] DM rejected from {message.author.id} - no active punishment found")
            return
        
        conn = sqlite3.connect(DATABASE_NAME)
        cur = conn.cursor()
        
        # Check for pending appeals only - allows new appeal if re-punished after approval
        cur.execute('SELECT id, status FROM unban_requests WHERE user_id = ? AND status = "pending"', (message.author.id,))
        existing = cur.fetchone()
        if existing:
            appeal_id, appeal_status = existing
            conn.close()
            try:
                embed = discord.Embed(
                    title="⏳ Appeal Already Submitted",
                    description="You already have a **pending** appeal. Please wait for staff review.",
                    color=0xf39c12
                )
                embed.add_field(name="📋 Appeal ID", value=f"`#{appeal_id}`", inline=True)
                embed.add_field(name="ℹ️ Note", value="Any additional messages sent here will **NOT** be added to your appeal. Staff will review your original submission.", inline=False)
                await message.author.send(embed=embed)
            except Exception:
                pass
            print(f"[Appeals] DM blocked for user {message.author.id} - existing pending appeal #{appeal_id}")
            return
        cur.execute('INSERT INTO unban_requests (user_id, reason) VALUES (?, ?)', (message.author.id, content))
        conn.commit()
        appeal_id = cur.lastrowid
        conn.close()
        print(f"[Appeals] New appeal #{appeal_id} stored from {message.author.id} - {punishment_type} in {guild_name}")
        # User confirmation
        try:
            user_embed = discord.Embed(title="Appeal Received", description="Staff will review your appeal.", color=0x3498db)
            user_embed.add_field(name="Appeal ID", value=f"#{appeal_id}")
            user_embed.add_field(name="Status", value="Pending")
            await message.author.send(embed=user_embed)
        except Exception:
            pass
        # Staff channel notify
        staff_channel = None
        for cid in (1423635286520500406, 1399746928585085068):
            ch = self.bot.get_channel(cid)
            if ch:
                staff_channel = ch
                if cid != 1423635286520500406:
                    print(f"[Appeals] Using fallback staff channel {cid}")
                break
        if not staff_channel:
            print("[Appeals] No staff channel available to post appeal.")
            return
        staff_embed = discord.Embed(title="📨 New Appeal Submitted", description=f"Appeal #{appeal_id} from {message.author}", color=0x3498db)
        trimmed = content[:500] + ("..." if len(content) > 500 else "")
        staff_embed.add_field(name="User", value=f"{message.author} ({message.author.id})", inline=True)
        staff_embed.add_field(name="Punishment", value=f"{punishment_type.title()} in {guild_name}", inline=True)
        staff_embed.add_field(name="Content", value=trimmed, inline=False)
        staff_embed.add_field(name="Review", value="/appeals • /approve <id> • /deny <id> <reason>", inline=False)
        try:
            await staff_channel.send(embed=staff_embed)
        except Exception as e:
            print(f"[Appeals] Failed to send staff embed: {e}")

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
        
        embed.set_footer(text=f"Use /approve <id> or /deny <id> <reason> to process appeals")
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
        
        # Determine if user is still a member (timeout case) or banned
        guild = ctx.guild
        member = guild.get_member(user_id) if guild else None
        user = None
        try:
            user = await self.bot.fetch_user(user_id)
        except Exception:
            pass

        action_taken = None
        error_embed = None

        if member:
            # User is still in server (likely timeout appeal). Clear timeout if active.
            try:
                if getattr(member, 'timed_out_until', None):
                    await member.timeout(None, reason=f"Appeal #{appeal_id} approved by {ctx.author}")
                    action_taken = "Timeout Cleared"
                else:
                    action_taken = "No Punishment Active"
            except discord.Forbidden:
                error_embed = create_error_embed("Permission Error", "I lack permission to modify this member's timeout.")
            except Exception as e:
                error_embed = create_error_embed("Error", f"Failed clearing timeout: {e}")
        else:
            # User not in guild; attempt unban (ban appeal)
            try:
                if user is None:
                    raise ValueError("User fetch failed; cannot unban")
                await guild.unban(user, reason=f'Appeal #{appeal_id} approved by {ctx.author}')
                action_taken = "User Unbanned"
            except discord.NotFound:
                error_embed = create_error_embed("User Not Found", "User not found or already unbanned.")
            except discord.Forbidden:
                error_embed = create_error_embed("Permission Error", "I don't have permission to unban this user.")
            except Exception as e:
                error_embed = create_error_embed("Error", f"Error processing unban: {e}")

        # Clear points only if we actually lifted a punishment
        if action_taken in ("Timeout Cleared", "User Unbanned"):
            try:
                from utils.database import clear_user_points
                clear_user_points(user_id)
            except Exception:
                pass

        if error_embed:
            await ctx.send(embed=error_embed)
        else:
            display_target = member or user or f"User {user_id}"
            embed = discord.Embed(title='Appeal Approved', color=0x2ecc71)
            embed.add_field(name='Appeal ID', value=f"#{appeal_id}", inline=True)
            embed.add_field(name='User', value=f'{display_target} ({user_id})', inline=True)
            embed.add_field(name='Action', value=action_taken or 'Completed', inline=True)
            embed.add_field(name='Approved By', value=ctx.author.mention, inline=True)
            embed.add_field(name='Reason', value=reason, inline=False)
            await ctx.send(embed=embed)
            # DM user if possible
            if user:
                try:
                    dm = discord.Embed(
                        title="✅ Appeal Approved",
                        description=f"## Your appeal has been reviewed and **approved**\n\nWelcome back to **{ctx.guild.name}**! We're glad to have you return.",
                        color=0x2ecc71
                    )
                    dm.add_field(name="📋 Appeal ID", value=f"`#{appeal_id}`", inline=True)
                    dm.add_field(name="⚡ Result", value=f"**{action_taken or 'Processed'}**", inline=True)
                    dm.add_field(name="💬 Staff Response", value=f"```{reason}```", inline=False)
                    dm.add_field(
                        name="📖 Moving Forward",
                        value="Please review our community guidelines and ensure compliance with all server rules. We appreciate your cooperation.",
                        inline=False
                    )
                    dm.set_footer(
                        text=f"{ctx.guild.name} • Professional Moderation Team",
                        icon_url=ctx.guild.icon.url if ctx.guild.icon else None
                    )
                    dm.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
                    await user.send(embed=dm)
                except Exception:
                    pass

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
                title="❌ Appeal Denied",
                description=f"## Your appeal has been reviewed\n\nAfter careful consideration, your appeal for **{ctx.guild.name}** has been denied.",
                color=0xe74c3c
            )
            embed_dm.add_field(name="📋 Appeal ID", value=f"`#{appeal_id}`", inline=True)
            embed_dm.add_field(name="👤 Reviewed By", value=str(ctx.author), inline=True)
            embed_dm.add_field(name="💬 Staff Response", value=f"```{reason}```", inline=False)
            embed_dm.add_field(
                name="🔄 Future Appeals",
                value="You may submit another appeal after taking time to reflect on the feedback provided. Please ensure any future appeals demonstrate understanding of our guidelines.",
                inline=False
            )
            embed_dm.set_footer(
                text=f"{ctx.guild.name} • Professional Moderation Team",
                icon_url=ctx.guild.icon.url if ctx.guild.icon else None
            )
            embed_dm.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
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
            # Send test appeal form to user
            embed_dm = discord.Embed(
                title=f"You have been {action_type}",
                description=f"You have been {action_type} from **{ctx.guild.name}**.",
                color=0xe74c3c
            )
            embed_dm.add_field(name="Reason", value=f"Test {action_type} action from {ctx.author.mention}", inline=False)
            embed_dm.add_field(name="Appeal", value="If you believe this action was unjust, you can submit an appeal by sending a DM to this bot with your reasoning.", inline=False)
            embed_dm.set_footer(text="Professional Moderation System")
            await user.send(embed=embed_dm)
            
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