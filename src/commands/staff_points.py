"""
Staff Points (Aura) System - Track and reward staff performance
"""
import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple, cast
from sqlite3 import Row
import discord.abc
import asyncio
from utils.helpers import create_success_embed, create_error_embed, create_warning_embed

class StaffPoints(commands.Cog):
    """Staff Points (Aura) System for tracking and rewarding staff performance"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_path = "data/staff_points.db"
        
    def check_guild_context(self, ctx: commands.Context) -> Tuple[discord.Guild, discord.Member]:
        """Validate guild context and return guild and author as Member"""
        if not ctx.guild:
            raise commands.NoPrivateMessage("This command cannot be used in DMs")
        if not isinstance(ctx.author, discord.Member):
            raise commands.CheckFailure("Command user must be a guild member")
        return ctx.guild, ctx.author
        
    async def cog_load(self):
        """Initialize the database when the cog loads"""
        await self.init_database()
    
    async def init_database(self):
        """Initialize the staff points database"""
        async with aiosqlite.connect(self.db_path) as db:
            # Staff points table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS staff_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    points INTEGER DEFAULT 0,
                    total_earned INTEGER DEFAULT 0,
                    total_spent INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, user_id)
                )
            """)
            
            # Points history table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS points_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    points_change INTEGER NOT NULL,
                    reason TEXT,
                    action_type TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Staff roles configuration
            await db.execute("""
                CREATE TABLE IF NOT EXISTS staff_config (
                    guild_id INTEGER PRIMARY KEY,
                    staff_role_ids TEXT,
                    points_channel_id INTEGER,
                    auto_rewards TEXT,
                    daily_bonus INTEGER DEFAULT 0,
                    weekly_bonus INTEGER DEFAULT 0
                )
            """)
            
            await db.commit()

    @commands.hybrid_group(name="aura", description="Staff aura management system")
    @commands.guild_only()
    async def aura(self, ctx: commands.Context):
        """Main aura command group"""
        if not ctx.guild:
            await ctx.send(embed=create_error_embed("Error", "This command can only be used in a server."), ephemeral=True)
            return
        if ctx.invoked_subcommand is None:
            # Show user's own aura
            if not ctx.guild or not isinstance(ctx.author, discord.Member):
                await ctx.send(" This command can only be used by server members!", ephemeral=True)
                return
            await self.show_user_points(ctx, ctx.author)

    @aura.command(name="add", description="Add aura to a staff member")
    @app_commands.describe(
        member="The staff member to give aura to",
        amount="Number of aura to add (1-1000)",
        reason="Reason for awarding aura"
    )
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def add_points(self, ctx: commands.Context, member: discord.Member, amount: int, *, reason: str = "No reason provided"):
        """Add aura to a staff member"""
        guild, author = self.check_guild_context(ctx)
        if amount <= 0 or amount > 1000:
            await ctx.reply(" Points amount must be between 1 and 1000!", ephemeral=True)
            return
            
        # Check if target is staff
        if not await self.is_staff_member(member):
            await ctx.reply(" You can only give points to staff members!", ephemeral=True)
            return

        await self.modify_points(guild.id, member.id, amount, author.id, reason, "add")
        
        embed = create_success_embed(
            "Points Added! ",
            f"**{member.display_name}** received **{amount}** points!\n\n**Reason:** {reason}"
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Get new total
        total = await self.get_user_points(guild.id, member.id)
        embed.add_field(name="New Total", value=f"{total} points", inline=True)
        embed.add_field(name="Awarded by", value=author.mention, inline=True)
        
        await ctx.reply(embed=embed)
        
        # Log to points channel if configured
        await self.log_points_change(guild, member, amount, author, reason, "add")

    @aura.command(name="remove", description="Remove aura from a staff member")
    @app_commands.describe(
        member="The staff member to remove aura from",
        amount="Number of aura to remove (1-1000)",
        reason="Reason for removing aura"
    )
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def remove_points(self, ctx: commands.Context, member: discord.Member, amount: int, *, reason: str = "No reason provided"):
        """Remove points from a staff member"""
        guild, author = self.check_guild_context(ctx)
        if amount <= 0 or amount > 1000:
            await ctx.reply(" Points amount must be between 1 and 1000!", ephemeral=True)
            return
            
        # Check if target is staff
        if not await self.is_staff_member(member):
            await ctx.reply(" You can only remove points from staff members!", ephemeral=True)
            return
        
        current_points = await self.get_user_points(guild.id, member.id)
        if amount > current_points:
            await ctx.reply(f" {member.display_name} only has {current_points} points available!", ephemeral=True)
            return
        
        await self.modify_points(guild.id, member.id, -amount, author.id, reason, "remove")
        
        embed = create_warning_embed(
            "Points Removed ",
            f"**{member.display_name}** lost **{amount}** points.\n\n**Reason:** {reason}"
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Get new total
        total = await self.get_user_points(guild.id, member.id)
        embed.add_field(name="New Total", value=f"{total} points", inline=True)
        embed.add_field(name="Removed by", value=author.mention, inline=True)
        
        await ctx.reply(embed=embed)
        
        # Log to points channel if configured
        await self.log_points_change(guild, member, -amount, author, reason, "remove")

    @aura.command(name="set", description="Set a staff member's aura to a specific amount")
    @app_commands.describe(
        member="The staff member to set aura for",
        amount="Number of aura to set (0-10000)",
        reason="Reason for setting aura"
    )
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def set_points(self, ctx: commands.Context, member: discord.Member, amount: int, *, reason: str = "Points adjustment"):
        """Set a staff member's points to a specific amount"""
        guild, author = self.check_guild_context(ctx)
        
        if amount < 0 or amount > 10000:
            await ctx.reply(" Points amount must be between 0 and 10000!", ephemeral=True)
            return
            
        # Check if target is staff
        if not await self.is_staff_member(member):
            await ctx.reply(" You can only set points for staff members!", ephemeral=True)
            return
        
        current_points = await self.get_user_points(guild.id, member.id)
        difference = amount - current_points
        
        await self.set_user_points(guild.id, member.id, amount, author.id, reason)
        
        embed = discord.Embed(
            title="Points Set ",
            description=f"**{member.display_name}**'s points have been set to **{amount}**.\n\n**Reason:** {reason}",
            color=0x3498DB
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Previous Total", value=f"{current_points} points", inline=True)
        embed.add_field(name="New Total", value=f"{amount} points", inline=True)
        embed.add_field(name="Change", value=f"{'+' if difference >= 0 else ''}{difference} points", inline=True)
        embed.add_field(name="Set by", value=author.mention, inline=False)
        
        await ctx.reply(embed=embed)

    @aura.command(name="check", description="Check a staff member's aura")
    @app_commands.describe(member="The staff member to check aura for")
    async def check_points(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Check a staff member's points"""
        assert ctx.guild is not None, "This command can only be used in a guild"
        assert isinstance(ctx.author, discord.Member), "Command user must be a guild member"
        if member is None:
            member = ctx.author  # type: ignore # we know author is Member because of guild_only
        assert isinstance(member, discord.Member), "Target must be a guild member"
            
        await self.show_user_points(ctx, member)

    @aura.command(name="history", description="View aura history for a staff member")
    @app_commands.describe(
        member="The staff member to check history for",
        limit="Number of recent entries to show (default: 10, max: 50)"
    )
    @commands.has_permissions(manage_messages=True)
    async def points_history(self, ctx: commands.Context, member: Optional[discord.Member] = None, limit: int = 10):
        """View points history for a staff member"""
        assert ctx.guild is not None, "This command can only be used in a guild"
        assert isinstance(ctx.author, discord.Member), "Command user must be a guild member"
        if member is None:
            member = ctx.author  # type: ignore # we know author is Member because of guild_only
        assert isinstance(member, discord.Member), "Target must be a guild member"
            
        if limit < 1 or limit > 50:
            limit = 10
            
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT points_change, reason, action_type, timestamp, moderator_id
                FROM points_history 
                WHERE guild_id = ? AND user_id = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (ctx.guild.id, member.id, limit)) as cursor:
                history_rows = list(await cursor.fetchall())
        
        if not history_rows:
            await ctx.reply(f" No points history found for {member.display_name}.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f" Points History - {member.display_name}",
            color=0x3498DB
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        current_points = await self.get_user_points(ctx.guild.id, member.id)
        embed.add_field(name="Current Points", value=f"{current_points} points", inline=True)
        
        history_text = ""
        for points_change, reason, action_type, timestamp, moderator_id in history_rows:
            moderator = self.bot.get_user(moderator_id)
            mod_name = moderator.display_name if moderator else "Unknown"
            
            # Parse timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = f"<t:{int(dt.timestamp())}:R>"
            except:
                time_str = "Unknown time"
            
            sign = "+" if points_change > 0 else ""
            emoji = "" if points_change > 0 else "" if action_type == "remove" else ""
            
            history_text += f"{emoji} **{sign}{points_change}** points - {reason}\n"
            history_text += f"   *by {mod_name} • {time_str}*\n\n"
        
        if len(history_text) > 1024:
            history_text = history_text[:1021] + "..."
            
        embed.add_field(name="Recent Activity", value=history_text or "No activity", inline=False)
        embed.set_footer(text=f"Showing last {len(history_rows)} entries")
        
        await ctx.reply(embed=embed)

    @aura.command(name="leaderboard", description="Show all staff members with aura")
    async def leaderboard(self, ctx: commands.Context):
        """Show all staff members with points"""
        assert ctx.guild is not None
            
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id, points, total_earned, last_updated
                FROM staff_points 
                WHERE guild_id = ? AND points > 0
                GROUP BY user_id
                ORDER BY points DESC, total_earned DESC
            """, (ctx.guild.id,)) as cursor:
                leaderboard_rows = list(await cursor.fetchall())
        
        if not leaderboard_rows:
            await ctx.reply(" No staff members with points found!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="Staff Aura Leaderboard",
            description="All staff members with aura",
            color=0x3498DB
        )
        
        leaderboard_text = ""
        seen_users = set()  # Track users we've already added to prevent duplicates
        rank = 1
        for user_id, points, total_earned, last_updated in leaderboard_rows:
            if user_id in seen_users:
                continue  # Skip duplicate entries
            seen_users.add(user_id)
            
            user = self.bot.get_user(user_id)
            if user:
                leaderboard_text += f"{rank}. **{user.name}** - {points} aura\n"
                rank += 1
        
        if leaderboard_text:
            # Split into chunks if too long
            if len(leaderboard_text) > 1024:
                chunks = [leaderboard_text[i:i+1024] for i in range(0, len(leaderboard_text), 1024)]
                for i, chunk in enumerate(chunks):
                    field_name = f"Rankings {i+1}" if i > 0 else "Rankings"
                    embed.add_field(name=field_name, value=chunk, inline=False)
            else:
                embed.add_field(name="Rankings", value=leaderboard_text, inline=False)
        
        # Add some stats
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT COUNT(*), SUM(points), SUM(total_earned)
                FROM staff_points 
                WHERE guild_id = ?
            """, (ctx.guild.id,)) as cursor:
                stats = await cursor.fetchone()
        
        if stats and stats[0]:
            total_staff, total_points, total_earned = stats
            embed.add_field(name="Server Stats", value=f"Staff Members: {total_staff}\nTotal Points: {total_points or 0}\nTotal Earned: {total_earned or 0}", inline=True)
        
        embed.set_footer(text=f"Showing top {len(leaderboard_rows)} staff members")
        embed.timestamp = datetime.now(timezone.utc)
        
        await ctx.reply(embed=embed)

    @aura.command(name="top", description="Show top 3 staff members")
    async def top_staff(self, ctx: commands.Context):
        """Show top 3 staff members"""
        assert ctx.guild is not None
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id, points, total_earned
                FROM staff_points 
                WHERE guild_id = ? AND points > 0
                ORDER BY points DESC, total_earned DESC
                LIMIT 3
            """, (ctx.guild.id,)) as cursor:
                top_staff = await cursor.fetchall()
        
        if not top_staff:
            await ctx.reply(" No staff members with points found!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=" Top 3 Staff Members",
            color=0xFFD700
        )
        
        medals = ["", "", ""]
        colors = [0xFFD700, 0xC0C0C0, 0xCD7F32]  # Gold, Silver, Bronze
        
        for i, (user_id, points, total_earned) in enumerate(top_staff):
            user = self.bot.get_user(user_id)
            if user:
                embed.add_field(
                    name=f"{medals[i]} {user.display_name}",
                    value=f"**{points}** points\n*Total earned: {total_earned}*",
                    inline=True
                )
        
        await ctx.reply(embed=embed)

    @aura.command(name="stats", description="Show detailed statistics for a staff member")
    @app_commands.describe(member="The staff member to show stats for")
    async def staff_stats(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Show detailed statistics for a staff member"""
        assert ctx.guild is not None
        assert isinstance(ctx.author, discord.Member)
        if member is None:
            member = ctx.author  # type: ignore
            
        if not await self.is_staff_member(member):
            await ctx.reply(" This command is only for staff members!", ephemeral=True)
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            # Get basic stats
            async with db.execute("""
                SELECT points, total_earned, total_spent, last_updated
                FROM staff_points 
                WHERE guild_id = ? AND user_id = ?
            """, (ctx.guild.id, member.id)) as cursor:
                basic_stats = await cursor.fetchone()
            
            # Get rank
            async with db.execute("""
                SELECT COUNT(*) + 1 as rank
                FROM staff_points 
                WHERE guild_id = ? AND points > (
                    SELECT COALESCE(points, 0) FROM staff_points 
                    WHERE guild_id = ? AND user_id = ?
                )
            """, (ctx.guild.id, ctx.guild.id, member.id)) as cursor:
                rank_data = await cursor.fetchone()
            
            # Get activity stats (last 30 days)
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            async with db.execute("""
                SELECT COUNT(*), SUM(points_change), action_type
                FROM points_history 
                WHERE guild_id = ? AND user_id = ? AND timestamp > ?
                GROUP BY action_type
            """, (ctx.guild.id, member.id, thirty_days_ago.isoformat())) as cursor:
                activity_stats = await cursor.fetchall()
        
        if not basic_stats:
            # Initialize user if not exists
            await self.init_user(ctx.guild.id, member.id)
            basic_stats = (0, 0, 0, datetime.now(timezone.utc).isoformat())
        
        points, total_earned, total_spent, last_updated = basic_stats
        rank = rank_data[0] if rank_data else 1
        
        embed = discord.Embed(
            title=f" Staff Statistics - {member.display_name}",
            color=0x3498DB
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Basic stats
        embed.add_field(name="Current Points", value=f" {points}", inline=True)
        embed.add_field(name="Leaderboard Rank", value=f" #{rank}", inline=True)
        embed.add_field(name="Total Earned", value=f" {total_earned}", inline=True)
        
        if total_spent > 0:
            embed.add_field(name="Total Spent", value=f" {total_spent}", inline=True)
        
        # Recent activity
        recent_earned = 0
        recent_lost = 0
        recent_actions = 0
        
        for count, points_sum, action_type in activity_stats:
            recent_actions += count
            if action_type == "add":
                recent_earned += points_sum
            elif action_type == "remove":
                recent_lost += abs(points_sum)
        
        if recent_actions > 0:
            embed.add_field(
                name="Last 30 Days",
                value=f" {recent_actions} actions\n {recent_earned} earned\n {recent_lost} lost",
                inline=True
            )
        
        # Performance metrics
        if total_earned > 0:
            retention_rate = ((total_earned - total_spent) / total_earned) * 100
            embed.add_field(
                name="Retention Rate",
                value=f" {retention_rate:.1f}%",
                inline=True
            )
        
        # Last activity
        try:
            dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            last_activity = f"<t:{int(dt.timestamp())}:R>"
        except:
            last_activity = "Unknown"
        
        embed.add_field(name="Last Updated", value=f" {last_activity}", inline=True)
        embed.set_footer(text="Use /points history for detailed activity log")
        
        await ctx.reply(embed=embed)

    @aura.command(name="reset", description="Reset a staff member's aura")
    @app_commands.describe(
        member="The staff member to reset aura for",
        reason="Reason for resetting aura"
    )
    @commands.has_permissions(administrator=True)
    async def reset_points(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Points reset"):
        """Reset a staff member's points to zero"""
        assert ctx.guild is not None and isinstance(ctx.author, discord.Member)
        current_points = await self.get_user_points(ctx.guild.id, member.id)
        
        if current_points == 0:
            await ctx.reply(f" {member.display_name} already has 0 points!", ephemeral=True)
            return
        
        # Confirm reset
        embed = create_warning_embed(
            "Confirm Points Reset ",
            f"Are you sure you want to reset **{member.display_name}**'s points?\n\n"
            f"**Current Points:** {current_points}\n"
            f"**Reason:** {reason}\n\n"
            f"*This action cannot be undone!*"
        )
        
        view = ConfirmView()
        
        # Send confirmation message
        if ctx.interaction:
            # For slash commands
            await ctx.reply(embed=embed, view=view, ephemeral=True)
            message = await ctx.interaction.original_response()
        else:
            # For text commands
            message = await ctx.send(embed=embed, view=view)
        
        # Wait for user response
        timed_out = await view.wait()
        
        if view.value is None or timed_out:
            # Timeout or no response
            embed = create_error_embed("Reset Timed Out", "Points reset confirmation timed out.")
            try:
                await message.edit(embed=embed, view=None)
            except:
                pass
            return
        
        if view.value:
            # Confirmed - reset points
            await self.set_user_points(ctx.guild.id, member.id, 0, ctx.author.id, reason)
            
            embed = create_success_embed(
                "Points Reset",
                f"**{member.display_name}**'s points have been reset to 0.\n\n**Reason:** {reason}"
            )
            embed.add_field(name="Previous Points", value=f"{current_points} points", inline=True)
            embed.add_field(name="Reset by", value=ctx.author.mention, inline=True)
            
            # Log the reset
            await self.log_points_change(ctx.guild, member, -current_points, ctx.author, reason, "reset")
            
            try:
                await message.edit(embed=embed, view=None)
            except Exception as e:
                # If edit fails, send new message
                await ctx.send(embed=embed)
        else:
            # Cancelled
            embed = create_error_embed("Reset Cancelled", "Points reset has been cancelled.")
            try:
                await message.edit(embed=embed, view=None)
            except:
                await ctx.send(embed=embed)

    @aura.command(name="config", description="Configure staff aura settings")
    @app_commands.describe(
        action="Configuration action",
        value="Configuration value"
    )
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def config_points(self, ctx: commands.Context, action: Optional[str] = None, *, value: Optional[str] = None):
        """Configure staff aura settings"""
        assert ctx.guild is not None
        if action is None:
            # Show current configuration
            await self.show_config(ctx)
            return
        
        action = action.lower()
        
        if action == "channel":
            if value is None:
                await ctx.reply(" Please specify a channel: `/points config channel #channel`", ephemeral=True)
                return
            
            # Parse channel mention or ID
            channel = None
            if value.startswith('<#') and value.endswith('>'):
                channel_id = int(value[2:-1])
                channel = ctx.guild.get_channel(channel_id)
            elif value.isdigit():
                channel = ctx.guild.get_channel(int(value))
            elif value.lower() in ["none", "disable", "off"]:
                await self.set_config(ctx.guild.id, "points_channel_id", None)
                await ctx.reply("Points logging channel disabled.", ephemeral=True)
                return
            
            if channel is None:
                await ctx.reply(" Channel not found!", ephemeral=True)
                return
            
            await self.set_config(ctx.guild.id, "points_channel_id", channel.id)
            await ctx.reply(f"Points logging channel set to {channel.mention}", ephemeral=True)
        
        elif action in ["addrole", "add_role", "role"]:
            if value is None:
                await ctx.reply(" Please specify a role: `/points config addrole @role`", ephemeral=True)
                return
            
            # Parse role mention or ID
            role = None
            if value.startswith('<@&') and value.endswith('>'):
                role_id = int(value[3:-1])
                role = ctx.guild.get_role(role_id)
            elif value.isdigit():
                role = ctx.guild.get_role(int(value))
            else:
                # Try to find by name
                role = discord.utils.get(ctx.guild.roles, name=value)
            
            if role is None:
                await ctx.reply(" Role not found!", ephemeral=True)
                return
            
            await self.add_staff_role(ctx.guild.id, role.id)
            await ctx.reply(f"Added {role.mention} as a staff role.", ephemeral=True)
        
        else:
            await ctx.reply(" Unknown configuration action. Use: `channel`, `addrole`", ephemeral=True)

    # Helper methods
    async def init_user(self, guild_id: int, user_id: int):
        """Initialize a user in the points system"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO staff_points (guild_id, user_id, points, total_earned, total_spent)
                VALUES (?, ?, 0, 0, 0)
            """, (guild_id, user_id))
            await db.commit()

    async def get_user_points(self, guild_id: int, user_id: int) -> int:
        """Get a user's current points"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT points FROM staff_points 
                WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def modify_points(self, guild_id: int, user_id: int, points_change: int, moderator_id: int, reason: str, action_type: str):
        """Modify a user's points and log the change"""
        await self.init_user(guild_id, user_id)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Update points
            if points_change > 0:
                await db.execute("""
                    UPDATE staff_points 
                    SET points = points + ?, total_earned = total_earned + ?, last_updated = CURRENT_TIMESTAMP
                    WHERE guild_id = ? AND user_id = ?
                """, (points_change, points_change, guild_id, user_id))
            else:
                abs_change = abs(points_change)
                await db.execute("""
                    UPDATE staff_points 
                    SET points = points + ?, total_spent = total_spent + ?, last_updated = CURRENT_TIMESTAMP
                    WHERE guild_id = ? AND user_id = ?
                """, (points_change, abs_change, guild_id, user_id))
            
            # Log the change
            await db.execute("""
                INSERT INTO points_history (guild_id, user_id, moderator_id, points_change, reason, action_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (guild_id, user_id, moderator_id, points_change, reason, action_type))
            
            await db.commit()

    async def set_user_points(self, guild_id: int, user_id: int, points: int, moderator_id: int, reason: str):
        """Set a user's points to a specific amount"""
        await self.init_user(guild_id, user_id)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Get current points to calculate the change
            async with db.execute("""
                SELECT points FROM staff_points 
                WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id)) as cursor:
                current = await cursor.fetchone()
                current_points = current[0] if current else 0
            
            points_change = points - current_points
            
            # Update points
            await db.execute("""
                UPDATE staff_points 
                SET points = ?, last_updated = CURRENT_TIMESTAMP
                WHERE guild_id = ? AND user_id = ?
            """, (points, guild_id, user_id))
            
            # Log the change
            await db.execute("""
                INSERT INTO points_history (guild_id, user_id, moderator_id, points_change, reason, action_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (guild_id, user_id, moderator_id, points_change, reason, "set"))
            
            await db.commit()

    async def is_staff_member(self, member: discord.Member) -> bool:
        """Check if a member is considered staff"""
        # Check if they have admin or manage server permissions
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            return True
        
        # Check configured staff roles
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT staff_role_ids FROM staff_config 
                WHERE guild_id = ?
            """, (member.guild.id,)) as cursor:
                result = await cursor.fetchone()
        
        if result and result[0]:
            staff_role_ids = [int(rid) for rid in result[0].split(',') if rid.isdigit()]
            return any(role.id in staff_role_ids for role in member.roles)
        
        return False

    async def show_user_points(self, ctx: commands.Context, member: discord.Member):
        """Show a user's points information"""
        assert ctx.guild is not None
        points = await self.get_user_points(ctx.guild.id, member.id)
        
        if points == 0 and member != ctx.author:
            await ctx.reply(f" {member.display_name} has no points recorded.", ephemeral=True)
            return
        
        # Get rank
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT COUNT(*) + 1 as rank
                FROM staff_points 
                WHERE guild_id = ? AND points > ?
            """, (ctx.guild.id, points)) as cursor:
                rank_data = await cursor.fetchone()
        
        rank = rank_data[0] if rank_data else 1
        
        embed = discord.Embed(
            title=f" {member.display_name}'s Points",
            color=0xFFD700
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Current Points", value=f"**{points}** points", inline=True)
        embed.add_field(name="Leaderboard Rank", value=f"**#{rank}**", inline=True)
        
        if member == ctx.author:
            embed.set_footer(text="Use /points stats for detailed statistics")
        
        await ctx.reply(embed=embed)

    async def log_points_change(self, guild: discord.Guild, member: discord.Member, points_change: int, moderator: discord.Member, reason: str, action_type: str):
        """Log points changes to the configured channel"""
        assert isinstance(moderator, discord.Member), "Moderator must be a guild member"
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT points_channel_id FROM staff_config 
                WHERE guild_id = ?
            """, (guild.id,)) as cursor:
                result = await cursor.fetchone()
        
        if not result or not result[0]:
            return
        
        channel = guild.get_channel(result[0])
        if not channel:
            return
        
        # Create log embed
        if points_change > 0:
            color = 0x00FF00  # Green
            emoji = ""
            action_text = "Points Added"
        elif action_type == "reset":
            color = 0xFF6600  # Orange
            emoji = ""
            action_text = "Points Reset"
        else:
            color = 0xFF0000  # Red
            emoji = ""
            action_text = "Points Removed"
        
        embed = discord.Embed(
            title=f"{emoji} {action_text}",
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name="Staff Member", value=member.mention, inline=True)
        embed.add_field(name="Moderator", value=moderator.mention, inline=True)
        embed.add_field(name="Points Change", value=f"{'+' if points_change > 0 else ''}{points_change}", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        # Get new total
        new_total = await self.get_user_points(guild.id, member.id)
        embed.add_field(name="New Total", value=f"{new_total} points", inline=True)
        
        try:
            if isinstance(channel, discord.TextChannel):
                await channel.send(embed=embed)
            elif isinstance(channel, discord.Thread):
                await channel.send(embed=embed)
            else:
                return
        except discord.errors.Forbidden:
            pass  # Channel not accessible

    async def show_config(self, ctx: commands.Context):
        """Show current configuration"""
        assert ctx.guild is not None
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT staff_role_ids, points_channel_id FROM staff_config 
                WHERE guild_id = ?
            """, (ctx.guild.id,)) as cursor:
                result = await cursor.fetchone()
        
        embed = discord.Embed(
            title=" Staff Points Configuration",
            color=0x3498DB
        )
        
        if result:
            staff_role_ids, points_channel_id = result
            
            # Staff roles
            if staff_role_ids:
                role_mentions = []
                for role_id in staff_role_ids.split(','):
                    if role_id.isdigit():
                        role = ctx.guild.get_role(int(role_id))
                        if role:
                            role_mentions.append(role.mention)
                
                embed.add_field(
                    name="Staff Roles",
                    value="\n".join(role_mentions) if role_mentions else "None configured",
                    inline=False
                )
            else:
                embed.add_field(name="Staff Roles", value="None configured", inline=False)
            
            # Points channel
            if points_channel_id:
                channel = ctx.guild.get_channel(points_channel_id)
                channel_text = channel.mention if channel else f"Invalid channel (ID: {points_channel_id})"
            else:
                channel_text = "Not configured"
            
            embed.add_field(name="Points Log Channel", value=channel_text, inline=False)
        else:
            embed.add_field(name="Status", value="Not configured", inline=False)
        
        embed.add_field(
            name="Configuration Commands",
            value="• `/points config channel #channel` - Set log channel\n• `/points config addrole @role` - Add staff role",
            inline=False
        )
        
        await ctx.reply(embed=embed)

    async def set_config(self, guild_id: int, key: str, value):
        """Set a configuration value"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"""
                INSERT OR REPLACE INTO staff_config (guild_id, {key})
                VALUES (?, ?)
            """, (guild_id, value))
            await db.commit()

    async def add_staff_role(self, guild_id: int, role_id: int):
        """Add a staff role to the configuration"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get current roles
            async with db.execute("""
                SELECT staff_role_ids FROM staff_config 
                WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                result = await cursor.fetchone()
            
            if result and result[0]:
                current_roles = result[0].split(',')
                if str(role_id) not in current_roles:
                    current_roles.append(str(role_id))
                    new_roles = ','.join(current_roles)
                else:
                    return  # Role already exists
            else:
                new_roles = str(role_id)
            
            await db.execute("""
                INSERT OR REPLACE INTO staff_config (guild_id, staff_role_ids)
                VALUES (?, ?)
            """, (guild_id, new_roles))
            await db.commit()



    async def auto_give_point(self, member: discord.Member, reason: str = "Thanks received"):
        """Automatically give an aura to a staff member"""
        if not await self.is_staff_member(member):
            return False
        if not self.bot.user:
            return False
        
        # Add point to database
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO staff_points (guild_id, user_id, points, total_earned, last_updated)
                VALUES (?, ?, 0, 0, datetime('now'))
            """, (member.guild.id, member.id))
            
            await db.execute("""
                UPDATE staff_points 
                SET points = points + 1, total_earned = total_earned + 1, last_updated = datetime('now')
                WHERE guild_id = ? AND user_id = ?
            """, (member.guild.id, member.id))
            
            # Log the transaction
            await db.execute("""
                INSERT INTO points_history (guild_id, user_id, moderator_id, points_change, reason, action_type)
                VALUES (?, ?, ?, 1, ?, 'auto_add')
            """, (member.guild.id, member.id, self.bot.user.id, reason))
            
            await db.commit()
        
        return True


class ConfirmView(discord.ui.View):
    """Confirmation view for dangerous operations"""
    
    def __init__(self):
        super().__init__(timeout=30)
        self.value = None
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
        except discord.errors.InteractionResponded:
            pass
        self.value = True
        self.stop()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
        except discord.errors.InteractionResponded:
            pass
        self.value = False
        self.stop()


async def setup(bot: commands.Bot):
    await bot.add_cog(StaffPoints(bot))
