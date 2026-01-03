"""
Staff Points (Aura) System - Track and reward staff performance
Only members with the staff role can receive aura.
Only admins can award aura by saying "thanks".
"""
import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import traceback
from datetime import datetime, timezone, timedelta
from typing import Optional
from utils.helpers import create_success_embed, create_error_embed, create_warning_embed

# Staff role ID - only members with this role can get aura
STAFF_ROLE_ID = 1403059755001577543

class StaffPoints(commands.Cog):
    """Staff Points (Aura) System for tracking and rewarding staff performance"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_path = "data/staff_points.db"
        
    async def cog_load(self):
        """Initialize the database when the cog loads"""
        await self.init_database()
    
    async def init_database(self):
        """Initialize the staff points database - preserves existing data"""
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
            
            await db.commit()
            
            # Clean up duplicate entries (merge them into single entries per user)
            await self.cleanup_duplicates(db)
            
            # Ensure unique constraint exists via index (for older databases)
            # This must run AFTER cleanup_duplicates to avoid errors
            await db.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_staff_points_guild_user 
                ON staff_points(guild_id, user_id)
            """)
            await db.commit()
    
    async def cleanup_duplicates(self, db):
        """Clean up duplicate entries in the database by merging them - keeps the MAXIMUM aura value"""
        try:
            # Find duplicates
            async with db.execute("""
                SELECT guild_id, user_id, COUNT(*) as count
                FROM staff_points
                GROUP BY guild_id, user_id
                HAVING count > 1
            """) as cursor:
                duplicates = await cursor.fetchall()
            
            if not duplicates:
                return  # No duplicates found
            
            print(f"🔍 Found {len(duplicates)} users with duplicate entries, merging...")
            
            for guild_id, user_id, count in duplicates:
                # Get the MAXIMUM values from all duplicate entries (preserves highest aura)
                async with db.execute("""
                    SELECT MAX(points), MAX(total_earned), MAX(total_spent), MAX(last_updated)
                    FROM staff_points
                    WHERE guild_id = ? AND user_id = ?
                """, (guild_id, user_id)) as cursor:
                    result = await cursor.fetchone()
                    max_points, max_earned, max_spent, last_updated = result
                
                print(f"  Merging user {user_id}: keeping max {max_points} aura (from {count} entries)")
                
                # Delete all entries for this user
                await db.execute("""
                    DELETE FROM staff_points
                    WHERE guild_id = ? AND user_id = ?
                """, (guild_id, user_id))
                
                # Insert single merged entry with MAXIMUM values
                await db.execute("""
                    INSERT INTO staff_points (guild_id, user_id, points, total_earned, total_spent, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (guild_id, user_id, max_points or 0, max_earned or 0, max_spent or 0, last_updated))
            
            await db.commit()
            print(f"✅ Cleaned up {len(duplicates)} duplicate staff entries")
        except Exception as e:
            print(f"⚠️ Error during duplicate cleanup: {e}")
            traceback.print_exc()

    async def is_staff_member(self, member: discord.Member) -> bool:
        """Check if a member has the staff role"""
        return any(role.id == STAFF_ROLE_ID for role in member.roles)
    
    async def is_admin(self, member: discord.Member) -> bool:
        """Check if a member is an admin"""
        return member.guild_permissions.administrator or member.id == member.guild.owner_id

    @commands.hybrid_group(name="aura", description="Staff aura management system")
    @commands.guild_only()
    async def aura(self, ctx: commands.Context):
        """Main aura command group"""
        if not ctx.guild:
            await ctx.send(embed=create_error_embed("Error", "This command can only be used in a server."), ephemeral=True)
            return
        if ctx.invoked_subcommand is None:
            # Show user's own aura
            if not isinstance(ctx.author, discord.Member):
                await ctx.send("❌ This command can only be used by server members!", ephemeral=True)
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
        """Add aura to a staff member - Admin only"""
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return
            
        if amount <= 0 or amount > 1000:
            await ctx.send("❌ Aura amount must be between 1 and 1000!", ephemeral=True)
            return
            
        # Check if target is staff
        if not await self.is_staff_member(member):
            await ctx.send(f"❌ {member.mention} doesn't have the staff role! Only staff members can receive aura.", ephemeral=True)
            return

        await self.modify_points(ctx.guild.id, member.id, amount, ctx.author.id, reason, "add")
        
        embed = create_success_embed(
            "✨ Aura Added!",
            f"**{member.display_name}** received **{amount}** aura!\n\n**Reason:** {reason}"
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Get new total
        total = await self.get_user_points(ctx.guild.id, member.id)
        embed.add_field(name="New Total", value=f"{total} aura", inline=True)
        embed.add_field(name="Awarded by", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

    @aura.command(name="remove", description="Remove aura from a staff member")
    @app_commands.describe(
        member="The staff member to remove aura from",
        amount="Number of aura to remove (1-1000)",
        reason="Reason for removing aura"
    )
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def remove_points(self, ctx: commands.Context, member: discord.Member, amount: int, *, reason: str = "No reason provided"):
        """Remove aura from a staff member - Admin only"""
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return
            
        if amount <= 0 or amount > 1000:
            await ctx.send("❌ Aura amount must be between 1 and 1000!", ephemeral=True)
            return
            
        # Check if target is staff
        if not await self.is_staff_member(member):
            await ctx.send(f"❌ {member.mention} doesn't have the staff role!", ephemeral=True)
            return
        
        current_points = await self.get_user_points(ctx.guild.id, member.id)
        if amount > current_points:
            await ctx.send(f"❌ {member.display_name} only has {current_points} aura available!", ephemeral=True)
            return
        
        await self.modify_points(ctx.guild.id, member.id, -amount, ctx.author.id, reason, "remove")
        
        embed = create_warning_embed(
            "⚠️ Aura Removed",
            f"**{member.display_name}** lost **{amount}** aura.\n\n**Reason:** {reason}"
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Get new total
        total = await self.get_user_points(ctx.guild.id, member.id)
        embed.add_field(name="New Total", value=f"{total} aura", inline=True)
        embed.add_field(name="Removed by", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

    @aura.command(name="set", description="Set a staff member's aura to a specific amount")
    @app_commands.describe(
        member="The staff member to set aura for",
        amount="Number of aura to set (0-10000)",
        reason="Reason for setting aura"
    )
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def set_points(self, ctx: commands.Context, member: discord.Member, amount: int, *, reason: str = "Aura adjustment"):
        """Set a staff member's aura to a specific amount - Admin only"""
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return
        
        if amount < 0 or amount > 10000:
            await ctx.send("❌ Aura amount must be between 0 and 10000!", ephemeral=True)
            return
            
        # Check if target is staff
        if not await self.is_staff_member(member):
            await ctx.send(f"❌ {member.mention} doesn't have the staff role!", ephemeral=True)
            return
        
        current_points = await self.get_user_points(ctx.guild.id, member.id)
        difference = amount - current_points
        
        await self.set_user_points(ctx.guild.id, member.id, amount, ctx.author.id, reason)
        
        embed = discord.Embed(
            title="🔧 Aura Set",
            description=f"**{member.display_name}**'s aura has been set to **{amount}**.\n\n**Reason:** {reason}",
            color=0x3498db
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Previous Total", value=f"{current_points} aura", inline=True)
        embed.add_field(name="New Total", value=f"{amount} aura", inline=True)
        embed.add_field(name="Change", value=f"{'+' if difference >= 0 else ''}{difference} aura", inline=True)
        embed.add_field(name="Set by", value=ctx.author.mention, inline=False)
        
        await ctx.send(embed=embed)

    @aura.command(name="check", description="Check a staff member's aura")
    @app_commands.describe(member="The staff member to check aura for")
    async def check_points(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Check a staff member's aura"""
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return
            
        if member is None:
            member = ctx.author
            
        await self.show_user_points(ctx, member)

    @aura.command(name="history", description="View aura history for a staff member")
    @app_commands.describe(
        member="The staff member to check history for",
        limit="Number of recent entries to show (default: 10, max: 50)"
    )
    @commands.has_permissions(manage_messages=True)
    async def points_history(self, ctx: commands.Context, member: Optional[discord.Member] = None, limit: int = 10):
        """View aura history for a staff member"""
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return
            
        if member is None:
            member = ctx.author
            
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
            await ctx.send(f"❌ No aura history found for {member.display_name}.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"📜 Aura History - {member.display_name}",
            color=0x3498db
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        current_points = await self.get_user_points(ctx.guild.id, member.id)
        embed.add_field(name="Current Aura", value=f"⭐ {current_points} aura", inline=True)
        
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
            emoji = "✨" if points_change > 0 else "⚠️"
            
            history_text += f"{emoji} **{sign}{points_change}** aura - {reason}\n"
            history_text += f"   *by {mod_name} • {time_str}*\n\n"
        
        if len(history_text) > 1024:
            history_text = history_text[:1021] + "..."
            
        embed.add_field(name="Recent Activity", value=history_text or "No activity", inline=False)
        embed.set_footer(text=f"Showing last {len(history_rows)} entries")
        
        await ctx.send(embed=embed)

    @aura.command(name="leaderboard", description="Show all staff members with aura")
    async def leaderboard(self, ctx: commands.Context):
        """Show all staff members with aura"""
        if not ctx.guild:
            return
            
        # Get all members with the staff role
        staff_role = ctx.guild.get_role(STAFF_ROLE_ID)
        if not staff_role:
            await ctx.send("❌ Staff role not found!", ephemeral=True)
            return
        
        # Count actual staff members
        staff_members = [m for m in staff_role.members if not m.bot]
        staff_count = len(staff_members)
        staff_ids = {m.id for m in staff_members}
        
        async with aiosqlite.connect(self.db_path) as db:
            # Get staff points - no GROUP BY needed since UNIQUE constraint prevents duplicates
            async with db.execute("""
                SELECT user_id, points, total_earned
                FROM staff_points 
                WHERE guild_id = ?
                ORDER BY points DESC, total_earned DESC
            """, (ctx.guild.id,)) as cursor:
                leaderboard_rows = await cursor.fetchall()
        
        # Filter to only show staff members with the role
        filtered_leaderboard = []
        seen_users = set()
        for user_id, user_points, user_earned in leaderboard_rows:
            if user_id in staff_ids and user_id not in seen_users:
                filtered_leaderboard.append((user_id, user_points, user_earned))
                seen_users.add(user_id)
        
        # Calculate real stats first
        total_points = sum(pts for _, pts, _ in filtered_leaderboard)
        total_earned = sum(earned for _, _, earned in filtered_leaderboard)
        
        embed = discord.Embed(
            title="🏆 Staff Aura Leaderboard",
            color=0xf1c40f
        )
        
        if filtered_leaderboard:
            leaderboard_text = ""
            for rank, (user_id, points, total_earned) in enumerate(filtered_leaderboard, 1):
                user = self.bot.get_user(user_id)
                if user:
                    # Medal emojis for top 3
                    medal = ""
                    if rank == 1:
                        medal = "🥇 "
                    elif rank == 2:
                        medal = "🥈 "
                    elif rank == 3:
                        medal = "🥉 "
                    
                    leaderboard_text += f"{rank}. {medal}**{user.name}** - {points} aura\n"
            
            # Discord embed limits: description max 4096, field value max 1024
            # Split into description (first 4000 chars) and fields (1000 chars each for safety)
            if len(leaderboard_text) <= 4000:
                embed.description = leaderboard_text
            else:
                # Put first part in description
                embed.description = leaderboard_text[:4000]
                remaining = leaderboard_text[4000:]
                
                # Split remaining into field chunks of max 1000 chars (safe margin under 1024 limit)
                field_count = 1
                while remaining:
                    chunk = remaining[:1000]
                    # Try to split at a newline to avoid cutting mid-line
                    if len(remaining) > 1000:
                        last_newline = chunk.rfind('\n')
                        if last_newline > 800:  # Only if we find a newline reasonably far
                            chunk = chunk[:last_newline + 1]
                    
                    embed.add_field(
                        name=f"Rankings (continued {field_count})" if field_count > 1 else "Rankings (continued)",
                        value=chunk,
                        inline=False
                    )
                    remaining = remaining[len(chunk):]
                    field_count += 1
        else:
            embed.description = "No staff members with aura yet!"
        
        # Add stats field
        embed.add_field(
            name="📊 Server Stats",
            value=f"**Staff Members:** {staff_count}\n**Total Points:** {total_points}\n",
            inline=True
        )
        
        embed.set_footer(text=f"Showing {len(filtered_leaderboard)} staff members with aura")
        embed.timestamp = datetime.now(timezone.utc)
        
        await ctx.send(embed=embed)

    @aura.command(name="cleanup", description="Clean up duplicate aura entries in database")
    @commands.has_permissions(administrator=True)
    async def cleanup_command(self, ctx: commands.Context):
        """Manually clean up duplicate entries - Admin only"""
        if not ctx.guild:
            return
        
        await ctx.send("🔄 Checking for duplicate entries...", ephemeral=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Count duplicates before cleanup
            async with db.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT guild_id, user_id
                    FROM staff_points
                    GROUP BY guild_id, user_id
                    HAVING COUNT(*) > 1
                )
            """) as cursor:
                result = await cursor.fetchone()
                dup_count_before = result[0] if result else 0
            
            if dup_count_before == 0:
                await ctx.send("✅ No duplicate entries found! Database is clean.", ephemeral=True)
                return
            
            # Run cleanup
            await self.cleanup_duplicates(db)
            
            # Count after
            async with db.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT guild_id, user_id
                    FROM staff_points
                    GROUP BY guild_id, user_id
                    HAVING COUNT(*) > 1
                )
            """) as cursor:
                result = await cursor.fetchone()
                dup_count_after = result[0] if result else 0
        
        embed = create_success_embed(
            "🧹 Database Cleanup Complete",
            f"Merged duplicate entries!\n\n"
            f"**Before:** {dup_count_before} users with duplicates\n"
            f"**After:** {dup_count_after} users with duplicates\n\n"
            f"✅ All duplicate entries have been merged keeping the maximum aura values."
        )
        await ctx.send(embed=embed)

    @aura.command(name="reset", description="Reset a staff member's aura")
    @app_commands.describe(
        member="The staff member to reset aura for",
        reason="Reason for resetting aura"
    )
    @commands.has_permissions(administrator=True)
    async def reset_points(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Aura reset"):
        """Reset a staff member's aura to zero - Admin only"""
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return
            
        current_points = await self.get_user_points(ctx.guild.id, member.id)
        
        if current_points == 0:
            await ctx.send(f"❌ {member.display_name} already has 0 aura!", ephemeral=True)
            return
        
        # Set points to 0
        await self.set_user_points(ctx.guild.id, member.id, 0, ctx.author.id, reason)
        
        embed = create_warning_embed(
            "🔄 Aura Reset",
            f"**{member.display_name}**'s aura has been reset to 0.\n\n**Reason:** {reason}"
        )
        embed.add_field(name="Previous Aura", value=f"{current_points} aura", inline=True)
        embed.add_field(name="Reset by", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

    # Helper methods
    async def init_user(self, guild_id: int, user_id: int):
        """Initialize a user in the aura system"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO staff_points (guild_id, user_id, points, total_earned, total_spent)
                VALUES (?, ?, 0, 0, 0)
            """, (guild_id, user_id))
            await db.commit()

    async def get_user_points(self, guild_id: int, user_id: int) -> int:
        """Get a user's current aura"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT points FROM staff_points 
                WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def modify_points(self, guild_id: int, user_id: int, points_change: int, moderator_id: int, reason: str, action_type: str):
        """Modify a user's aura and log the change"""
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
        """Set a user's aura to a specific amount"""
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

    async def show_user_points(self, ctx: commands.Context, member: discord.Member):
        """Show a user's aura information"""
        if not ctx.guild:
            return
            
        points = await self.get_user_points(ctx.guild.id, member.id)
        
        # Check if they're staff
        is_staff = await self.is_staff_member(member)
        
        if not is_staff:
            await ctx.send(f"❌ {member.mention} is not a staff member and cannot receive aura.", ephemeral=True)
            return
        
        # Get rank among current staff members only (not all database users)
        staff_role = ctx.guild.get_role(STAFF_ROLE_ID)
        if not staff_role:
            rank = 1
        else:
            # Get set of current staff IDs for O(1) lookup
            staff_ids = {m.id for m in staff_role.members if not m.bot}
            
            # Get all staff members' points from database
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT user_id, points
                    FROM staff_points 
                    WHERE guild_id = ?
                    ORDER BY points DESC
                """, (ctx.guild.id,)) as cursor:
                    all_points = await cursor.fetchall()
            
            # Filter to only current staff members and calculate rank
            rank = 1
            for user_id, user_points in all_points:
                if user_id in staff_ids:
                    if user_points > points:
                        rank += 1
                    else:
                        # Since sorted DESC, once we hit <= points, we can stop
                        break
        
        embed = discord.Embed(
            title=f"⭐ {member.display_name}'s Aura",
            color=0xf1c40f
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Current Aura", value=f"**{points}** aura", inline=True)
        embed.add_field(name="Leaderboard Rank", value=f"**#{rank}**", inline=True)
        
        if member == ctx.author:
            embed.set_footer(text="Keep up the great work! 💪")
        
        await ctx.send(embed=embed)

    async def auto_give_point(self, member: discord.Member, reason: str = "Thanks received") -> bool:
        """Automatically give 1 aura to a staff member when thanked"""
        # Only give aura to staff members
        if not await self.is_staff_member(member):
            return False
        
        if not self.bot.user:
            return False
        
        # Add 1 aura
        await self.init_user(member.guild.id, member.id)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE staff_points 
                SET points = points + 1, total_earned = total_earned + 1, last_updated = CURRENT_TIMESTAMP
                WHERE guild_id = ? AND user_id = ?
            """, (member.guild.id, member.id))
            
            # Log the transaction
            await db.execute("""
                INSERT INTO points_history (guild_id, user_id, moderator_id, points_change, reason, action_type)
                VALUES (?, ?, ?, 1, ?, 'auto_add')
            """, (member.guild.id, member.id, self.bot.user.id, reason))
            
            await db.commit()
        
        return True


async def setup(bot: commands.Bot):
    await bot.add_cog(StaffPoints(bot))
