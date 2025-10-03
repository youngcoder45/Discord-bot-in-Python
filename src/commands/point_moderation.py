import discord
import sqlite3
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from typing import Optional

DB_PATH = 'data/codeverse_bot.db'
POINT_CAP = 100
REQUIRED_APPROVALS = 2
DEFAULT_FALLBACK = 80  # Points set after decline
PERIOD_FORMAT = '%Y-%m'

class PointApprovalView(discord.ui.View):
    def __init__(self, cog: 'PointModeration', guild_id: int, user_id: int):
        super().__init__(timeout=172800)  # 48h
        self.cog = cog
        self.guild_id = guild_id
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only allow users with ban_members to interact
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("❌ You don't have permission to approve this.", ephemeral=True)
            return False
        return True

    async def _refresh_embed(self) -> discord.Embed:
        pending = self.cog._get_pending(self.guild_id, self.user_id)
        embed = discord.Embed(
            title="🚨 Pending Point Ban",
            description=f"User <@{self.user_id}> reached {POINT_CAP} moderation points and requires approval.",
            color=discord.Color.orange()
        )
        if pending:
            approvers = []
            if pending['approver_one']:
                approvers.append(f"<@{pending['approver_one']}> ✔")
            if pending['approver_two']:
                approvers.append(f"<@{pending['approver_two']}> ✔")
            if not approvers:
                approvers.append("No approvals yet")
            embed.add_field(name="Approvals", value='\n'.join(approvers), inline=False)
            embed.add_field(name="Reason", value=pending['reason'] or 'No reason', inline=False)
            embed.set_footer(text=f"Status: {pending['status']}")
        return embed

    @discord.ui.button(label='Approve', style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await self.cog._add_approval(self.guild_id, self.user_id, interaction.user.id)
        if result == 'already-approved':
            await interaction.response.send_message("⚠️ You already approved this pending ban.", ephemeral=True)
            return
        if result == 'not-pending':
            await interaction.response.send_message("⚠️ This pending ban no longer exists.", ephemeral=True)
            self.stop()
            return
        if result == 'approved-final':
            # Ban executed, disable buttons
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
            embed = await self._refresh_embed()
            embed.color = discord.Color.red()
            embed.title = "✅ Ban Approved"
            await interaction.response.edit_message(embed=embed, view=self)
            return
        # Partial approval (first)
        embed = await self._refresh_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Decline', style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = self.cog._decline_pending(self.guild_id, self.user_id, interaction.user.id)
        if result == 'not-pending':
            await interaction.response.send_message("⚠️ This pending ban no longer exists.", ephemeral=True)
            self.stop()
            return
        if result == 'declined':
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
            embed = await self._refresh_embed()
            embed.title = "❎ Ban Declined"
            embed.color = discord.Color.green()
            await interaction.response.edit_message(embed=embed, view=self)

class PointModeration(commands.Cog):
    """Moderation points system with two-step ban approval."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._ensure_schema()

    # ---------- Database Schema ----------
    def _connect(self):
        return sqlite3.connect(DB_PATH)

    def _ensure_schema(self):
        con = self._connect()
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS mod_points(
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            points INTEGER NOT NULL DEFAULT 0,
            period TEXT NOT NULL,
            last_updated TIMESTAMP NOT NULL,
            PRIMARY KEY (guild_id, user_id)
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS mod_point_bans(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL,
            reason TEXT,
            points_at_creation INTEGER NOT NULL,
            status TEXT NOT NULL,
            approver_one INTEGER,
            approver_two INTEGER,
            finalized_at TIMESTAMP
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS mod_point_config(
            guild_id INTEGER PRIMARY KEY,
            fallback_points INTEGER NOT NULL DEFAULT 80
        )""")
        con.commit()
        con.close()

    # ---------- Helpers ----------
    def _current_period(self) -> str:
        return datetime.now(timezone.utc).strftime(PERIOD_FORMAT)

    def _get_points_row(self, guild_id: int, user_id: int):
        con = self._connect(); cur = con.cursor()
        cur.execute("SELECT points, period FROM mod_points WHERE guild_id=? AND user_id=?", (guild_id, user_id))
        row = cur.fetchone()
        con.close()
        return row

    def _reset_if_needed(self, guild_id: int, user_id: int):
        period_now = self._current_period()
        row = self._get_points_row(guild_id, user_id)
        if row is None:
            # Insert new
            con = self._connect(); cur = con.cursor()
            cur.execute("INSERT INTO mod_points(guild_id, user_id, points, period, last_updated) VALUES (?,?,?,?,?)",
                        (guild_id, user_id, 0, period_now, datetime.now(timezone.utc)))
            con.commit(); con.close()
            return 0
        points, period = row
        if period != period_now:
            con = self._connect(); cur = con.cursor()
            cur.execute("UPDATE mod_points SET points=0, period=?, last_updated=? WHERE guild_id=? AND user_id=?",
                        (period_now, datetime.now(timezone.utc), guild_id, user_id))
            con.commit(); con.close()
            return 0
        return points

    def _update_points(self, guild_id: int, user_id: int, new_points: int):
        con = self._connect(); cur = con.cursor()
        cur.execute("UPDATE mod_points SET points=?, last_updated=? WHERE guild_id=? AND user_id=?",
                    (new_points, datetime.now(timezone.utc), guild_id, user_id))
        con.commit(); con.close()

    def _get_config(self, guild_id: int) -> int:
        con = self._connect(); cur = con.cursor()
        cur.execute("SELECT fallback_points FROM mod_point_config WHERE guild_id=?", (guild_id,))
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO mod_point_config(guild_id, fallback_points) VALUES (?,?)", (guild_id, DEFAULT_FALLBACK))
            con.commit(); con.close()
            return DEFAULT_FALLBACK
        con.close()
        return row[0]

    def _get_pending(self, guild_id: int, user_id: int):
        con = self._connect(); cur = con.cursor()
        cur.execute("""SELECT id, guild_id, user_id, reason, points_at_creation, status, approver_one, approver_two
                    FROM mod_point_bans WHERE guild_id=? AND user_id=? AND status='PENDING' ORDER BY id DESC LIMIT 1""",
                    (guild_id, user_id))
        row = cur.fetchone(); con.close()
        if row:
            return {
                'id': row[0], 'guild_id': row[1], 'user_id': row[2], 'reason': row[3],
                'points_at_creation': row[4], 'status': row[5], 'approver_one': row[6], 'approver_two': row[7]
            }
        return None

    def _create_pending(self, guild_id: int, user_id: int, reason: str, points: int):
        con = self._connect(); cur = con.cursor()
        cur.execute("INSERT INTO mod_point_bans(guild_id, user_id, created_at, reason, points_at_creation, status) VALUES (?,?,?,?,?, 'PENDING')",
                    (guild_id, user_id, datetime.now(timezone.utc), reason, points))
        con.commit(); con.close()

    def _decline_pending(self, guild_id: int, user_id: int, moderator_id: int):
        pending = self._get_pending(guild_id, user_id)
        if not pending:
            return 'not-pending'
        # Set status cancelled and reduce points
        fallback = self._get_config(guild_id)
        con = self._connect(); cur = con.cursor()
        cur.execute("UPDATE mod_point_bans SET status='CANCELLED', finalized_at=? WHERE id=?",
                    (datetime.now(timezone.utc), pending['id']))
        cur.execute("UPDATE mod_points SET points=?, last_updated=? WHERE guild_id=? AND user_id=?",
                    (fallback, datetime.now(timezone.utc), guild_id, user_id))
        con.commit(); con.close()
        self._log_case(guild_id, user_id, moderator_id, 'POINTBAN-CANCEL', f"Declined pending ban; points set to {fallback}")
        return 'declined'

    async def _add_approval(self, guild_id: int, user_id: int, moderator_id: int):
        pending = self._get_pending(guild_id, user_id)
        if not pending:
            return 'not-pending'
        if pending['approver_one'] == moderator_id or pending['approver_two'] == moderator_id:
            return 'already-approved'
        con = self._connect(); cur = con.cursor()
        # Add first approver
        if pending['approver_one'] is None:
            cur.execute("UPDATE mod_point_bans SET approver_one=? WHERE id=?", (moderator_id, pending['id']))
            con.commit(); con.close()
            return 'partial'
        # Add second approver -> finalize
        if pending['approver_two'] is None:
            cur.execute("UPDATE mod_point_bans SET approver_two=?, status='APPROVED', finalized_at=? WHERE id=?",
                        (moderator_id, datetime.now(timezone.utc), pending['id']))
            con.commit(); con.close()
            # Execute ban
            guild = self.bot.get_guild(guild_id)
            if guild:
                member = guild.get_member(user_id)
                reason = f"Point threshold exceeded ({POINT_CAP})"
                try:
                    if member:
                        try:
                            await member.send(f"You have been banned from {guild.name} for accumulating {POINT_CAP} moderation points.")
                        except Exception:
                            pass
                        await member.ban(reason=reason)
                except Exception:
                    pass
            self._log_case(guild_id, user_id, moderator_id, 'POINTBAN', f"Ban approved via point system ({POINT_CAP} points)")
            return 'approved-final'
        con.close()
        return 'partial'

    # ---------- Logging Helper ----------
    def _log_case(self, guild_id: int, user_id: int, mod_id: int, action: str, reason: str = "No reason provided"):
        try:
            con = self._connect(); cur = con.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS mod_cases(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                reason TEXT,
                created_at TIMESTAMP NOT NULL
            )""")
            cur.execute("INSERT INTO mod_cases(guild_id, user_id, moderator_id, action, reason, created_at) VALUES (?,?,?,?,?,?)",
                        (guild_id, user_id, mod_id, action, reason, datetime.now(timezone.utc)))
            con.commit(); con.close()
        except Exception:
            pass

    # ---------- Public API ----------
    def _add_points_internal(self, guild_id: int, user_id: int, moderator_id: int, amount: int, reason: str) -> tuple[int, bool, bool]:
        # returns (new_points, reached_cap, created_pending)
        current = self._reset_if_needed(guild_id, user_id)
        if amount <= 0:
            return current, False, False
        new_points = current + amount
        created_pending = False
        if new_points >= POINT_CAP:
            new_points = POINT_CAP
        self._update_points(guild_id, user_id, new_points)
        self._log_case(guild_id, user_id, moderator_id, 'POINTS', f"+{amount} -> {new_points} | {reason}")
        reached_cap = new_points >= POINT_CAP
        if reached_cap:
            # Create pending if doesn't exist
            if not self._get_pending(guild_id, user_id):
                self._create_pending(guild_id, user_id, reason, new_points)
                created_pending = True
        return new_points, reached_cap, created_pending

    def _get_points(self, guild_id: int, user_id: int) -> int:
        current = self._reset_if_needed(guild_id, user_id)
        return current

    # ---------- Commands ----------
    @commands.hybrid_command(name='addpoints', help='Add moderation points to a user')
    @app_commands.describe(user='User to add points to', amount='Amount of points to add', reason='Reason for the points')
    @commands.has_permissions(moderate_members=True)
    async def addpoints(self, ctx: commands.Context, user: discord.Member, amount: int, *, reason: str = 'No reason provided'):
        if ctx.guild is None:
            return await ctx.send('Guild only command.')
        new_points, cap, created_pending = self._add_points_internal(ctx.guild.id, user.id, ctx.author.id, amount, reason)
        if amount <= 0:
            return await ctx.send('⚠️ Amount must be positive.')
        if not cap:
            await ctx.send(f"✅ Added {amount} points to {user.mention}. Total: {new_points}/100")
        else:
            if created_pending:
                # Attempt DM
                try:
                    await user.send(f"You have reached {POINT_CAP} moderation points in {ctx.guild.name}. A ban is pending staff review.")
                except Exception:
                    pass
                view = PointApprovalView(self, ctx.guild.id, user.id)
                embed = await view._refresh_embed()
                await ctx.send(f"🚨 {user.mention} reached the point cap! Ban requires approval.", embed=embed, view=view)
            else:
                await ctx.send(f"⚠️ {user.mention} is already at the cap with a pending ban.")

    @commands.hybrid_command(name='points', help='Show moderation points for a user (or yourself)')
    @app_commands.describe(user='User to view points for (optional)')
    async def points(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        if ctx.guild is None:
            return await ctx.send('Guild only command.')
        target = user or ctx.author
        pts = self._get_points(ctx.guild.id, target.id)
        pending = self._get_pending(ctx.guild.id, target.id)
        status = '⚠️ Pending Ban' if pending else 'Active'
        embed = discord.Embed(title='Moderation Points', color=discord.Color.blue())
        embed.add_field(name='User', value=target.mention, inline=True)
        embed.add_field(name='Points', value=f"{pts}/{POINT_CAP}", inline=True)
        embed.add_field(name='Status', value=status, inline=True)
        if pending:
            approvals = []
            if pending['approver_one']:
                approvals.append(f"<@{pending['approver_one']}> ✔")
            if pending['approver_two']:
                approvals.append(f"<@{pending['approver_two']}> ✔")
            if not approvals:
                approvals.append('No approvals yet')
            embed.add_field(name='Pending Reason', value=pending['reason'] or 'No reason', inline=False)
            embed.add_field(name='Approvals', value='\n'.join(approvals), inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='pendingbans', help='List users with pending point-based bans')
    @commands.has_permissions(moderate_members=True)
    async def pendingbans(self, ctx: commands.Context):
        if ctx.guild is None:
            return await ctx.send('Guild only command.')
        con = self._connect(); cur = con.cursor()
        cur.execute("SELECT user_id, reason, points_at_creation, approver_one, approver_two FROM mod_point_bans WHERE guild_id=? AND status='PENDING' ORDER BY id DESC", (ctx.guild.id,))
        rows = cur.fetchall(); con.close()
        if not rows:
            return await ctx.send('✅ No pending point bans.')
        desc_lines = []
        for r in rows:
            user_id, reason, pts, a1, a2 = r
            approvals = [f"<@{a1}>" if a1 else '—', f"<@{a2}>" if a2 else '—']
            desc_lines.append(f"<@{user_id}> - {pts} pts | Approvals: {approvals[0]}, {approvals[1]} | {reason or 'No reason'}")
        embed = discord.Embed(title='Pending Point Bans', description='\n'.join(desc_lines)[:4000], color=discord.Color.orange())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='approveban', help='Approve a pending point-based ban')
    @commands.has_permissions(ban_members=True)
    async def approveban(self, ctx: commands.Context, user: discord.Member):
        if ctx.guild is None:
            return await ctx.send('Guild only command.')
        result = await self._add_approval(ctx.guild.id, user.id, ctx.author.id)
        if result == 'not-pending':
            return await ctx.send('⚠️ No pending ban for that user.')
        if result == 'already-approved':
            return await ctx.send('⚠️ You already approved this ban.')
        if result == 'approved-final':
            return await ctx.send(f'✅ Ban finalized for {user.mention}.')
        return await ctx.send(f'✅ Your approval has been recorded for {user.mention}.')

    @commands.hybrid_command(name='declineban', help='Decline a pending point-based ban')
    @commands.has_permissions(ban_members=True)
    async def declineban(self, ctx: commands.Context, user: discord.Member):
        if ctx.guild is None:
            return await ctx.send('Guild only command.')
        result = self._decline_pending(ctx.guild.id, user.id, ctx.author.id)
        if result == 'not-pending':
            return await ctx.send('⚠️ No pending ban for that user.')
        return await ctx.send(f'❎ Ban declined for {user.mention}. Points lowered.')

async def setup(bot: commands.Bot):
    await bot.add_cog(PointModeration(bot))
