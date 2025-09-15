"""
MIT License

Copyright (c) 2025 HyScript7 <mail: hyscript7@gmail.com> <discord: @hyscript7>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite
import discord
from discord.ext import commands
from discord import app_commands


@dataclass
class Settings:
    guild_id: int
    log_channel_id: Optional[int]
    staff_role_ids: list[int]

@dataclass
class Shift:
    shift_id: Optional[int]
    guild_id: int
    user_id: int
    start: datetime
    end: datetime | None = None
    start_note: str | None = None
    end_note: str | None = None
    
    @classmethod
    def new(cls, guild_id: int, user_id: int, start: datetime, start_note: str | None = None):
        return cls(None, guild_id, user_id, start, start_note=start_note)

    @classmethod
    def from_row(cls, row):
        shift_id, guild_id, user_id, start, end, start_note, end_note = row
        # Convert string datetimes back to datetime objects
        if isinstance(start, str):
            start = datetime.fromisoformat(start.replace('Z', '+00:00'))
        if end and isinstance(end, str):
            end = datetime.fromisoformat(end.replace('Z', '+00:00'))
        return cls(shift_id, guild_id, user_id, start, end, start_note, end_note)

class EmbedProvider(ABC):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @abstractmethod
    async def get_shift_start_embed(self, ctx: commands.Context, shift: Shift) -> discord.Embed:
        """
        Returns an embed containing information about the start of a shift.
        """
        ...
    
    @abstractmethod
    async def get_shift_end_embed(self, ctx: commands.Context, shift: Shift) -> discord.Embed:
        """
        Returns an embed containing information about the end of a shift.
        """
        ...

    @abstractmethod
    async def get_shift_discard_embed(self, ctx: commands.Context, shift: Shift) -> discord.Embed:
        """
        Returns an embed containing information about discarding a shift.
        """
        ...

class LogEmbedProvider(EmbedProvider):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
    
    async def get_shift_start_embed(self, ctx: commands.Context, shift: Shift):
        embed=discord.Embed(title="Shift Started", description=f"{ctx.author.mention} has just started their shift.", color=0x00ff00)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="Start Time", value=f"<t:{round(shift.start.timestamp())}:F>", inline=False)
        if shift.start_note is not None:
            embed.add_field(name="Start Note", value=f"```\n{shift.start_note}\n```", inline=False)
        return embed

    async def get_shift_end_embed(self, ctx: commands.Context, shift: Shift):
        embed=discord.Embed(title="Shift Ended", description=f"{ctx.author.mention} has just ended their shift.", color=0xff0000)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="Start Time", value=f"<t:{round(shift.start.timestamp())}:F>", inline=True)
        embed.add_field(name="End Time", value=f"<t:{round(shift.end.timestamp())}:F>", inline=True) # type: ignore
        if shift.start_note is not None:
            embed.add_field(name="Start Note", value=f"```\n{shift.start_note}\n```", inline=False)
        if shift.end_note is not None:
            embed.add_field(name="End Note", value=f"```\n{shift.end_note}\n```", inline=False)
        return embed
    
    async def get_shift_discard_embed(self, ctx: commands.Context, shift: Shift):
        embed=discord.Embed(title="Shift Discarded", description=f"{ctx.author.mention} has just discarded their shift.", color=0xFFFF00)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="Start Time", value=f"<t:{round(shift.start.timestamp())}:F>", inline=True)
        if shift.start_note is not None:
            embed.add_field(name="Start Note", value=f"```\n{shift.start_note}\n```", inline=False)
        return embed
 

class ShiftService:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        if not self.database_path.exists():
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            self.database_path.touch()

    async def init_db(self):
        """
        Initializes the database for this cog.
        """
        async with aiosqlite.connect(self.database_path) as db:
            # The order of rows in the table and fields in the Shift data class **must** match
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS shifts (
                    shift_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    start DATETIME NOT NULL,
                    end DATETIME DEFAULT NULL,
                    start_note TEXT DEFAULT NULL,
                    end_note TEXT DEFAULT NULL
                )
            """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS shift_settings (
                    guild_id INTEGER PRIMARY KEY,
                    log_channel_id INTEGER DEFAULT NULL,
                    staff_role_ids TEXT DEFAULT '[]'
                )
            """
            )
            await db.commit()

    async def drop_db(self):
        """
        Drops all tables owned by this cog.
        """
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("DROP TABLE IF EXISTS shifts")
            await db.execute("DROP TABLE IF EXISTS shift_settings")
            await db.commit()
    
    async def get_shift(self, guild_id: int, user_id: int) -> Shift | None:
        """Finds the last unfinished shift for a user (or returns None)"""
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(
                "SELECT * FROM shifts WHERE user_id = ? AND guild_id = ? AND end IS NULL",
                (user_id, guild_id),
            )
            row = await cursor.fetchone()
            if row:
                return Shift.from_row(row)
            return None
    
    async def start_shift(self, shift: Shift) -> None:
        """Adds a shift to the database"""
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                "INSERT INTO shifts (guild_id, user_id, start, start_note) VALUES (?, ?, ?, ?)",
                (shift.guild_id, shift.user_id, shift.start, shift.start_note),
            )
            await db.commit()
    
    async def end_shift(self, shift: Shift) -> None:
        """Updates a shift in the database"""
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                "UPDATE shifts SET end = ?, end_note = ? WHERE shift_id = ?",
                (shift.end, shift.end_note, shift.shift_id),
            )
            await db.commit()
    
    async def discard_shift(self, shift: Shift) -> None:
        """Removes a shift from the database"""
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("DELETE FROM shifts WHERE shift_id = ?", (shift.shift_id,))
            await db.commit()
    
    async def get_active_shifts(self, guild_id: int) -> list[Shift]:
        """Get all currently active shifts in the guild"""
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(
                "SELECT * FROM shifts WHERE guild_id = ? AND end IS NULL ORDER BY start DESC",
                (guild_id,)
            )
            rows = await cursor.fetchall()
            shifts = []
            for row in rows:
                shifts.append(Shift.from_row(row))
            return shifts
    
    async def get_shift_history(self, guild_id: int, user_id: Optional[int] = None, days: int = 30, limit: int = 50) -> list[Shift]:
        """Get shift history with optional filtering"""
        async with aiosqlite.connect(self.database_path) as db:
            if user_id:
                cursor = await db.execute(
                    """SELECT * FROM shifts WHERE guild_id = ? AND user_id = ? 
                       AND start >= datetime('now', '-{} days') 
                       ORDER BY start DESC LIMIT ?""".format(days),
                    (guild_id, user_id, limit)
                )
            else:
                cursor = await db.execute(
                    """SELECT * FROM shifts WHERE guild_id = ? 
                       AND start >= datetime('now', '-{} days') 
                       ORDER BY start DESC LIMIT ?""".format(days),
                    (guild_id, limit)
                )
            rows = await cursor.fetchall()
            shifts = []
            for row in rows:
                shifts.append(Shift.from_row(row))
            return shifts
    
    async def get_shift_stats(self, guild_id: int, user_id: Optional[int] = None, days: int = 30):
        """Get shift statistics"""
        async with aiosqlite.connect(self.database_path) as db:
            if user_id:
                # Individual user stats
                cursor = await db.execute(
                    """SELECT 
                        COUNT(*) as total_shifts,
                        COUNT(CASE WHEN end IS NOT NULL THEN 1 END) as completed_shifts,
                        COALESCE(SUM(
                            CASE WHEN end IS NOT NULL 
                            THEN (julianday(end) - julianday(start)) * 24 * 60 * 60 
                            END
                        ), 0) as total_seconds,
                        COALESCE(AVG(
                            CASE WHEN end IS NOT NULL 
                            THEN (julianday(end) - julianday(start)) * 24 * 60 * 60 
                            END
                        ), 0) as avg_seconds
                    FROM shifts 
                    WHERE guild_id = ? AND user_id = ? 
                    AND start >= datetime('now', '-{} days')""".format(days),
                    (guild_id, user_id)
                )
            else:
                # Server-wide stats
                cursor = await db.execute(
                    """SELECT 
                        COUNT(*) as total_shifts,
                        COUNT(CASE WHEN end IS NOT NULL THEN 1 END) as completed_shifts,
                        COUNT(DISTINCT user_id) as unique_staff,
                        COALESCE(SUM(
                            CASE WHEN end IS NOT NULL 
                            THEN (julianday(end) - julianday(start)) * 24 * 60 * 60 
                            END
                        ), 0) as total_seconds,
                        COALESCE(AVG(
                            CASE WHEN end IS NOT NULL 
                            THEN (julianday(end) - julianday(start)) * 24 * 60 * 60 
                            END
                        ), 0) as avg_seconds
                    FROM shifts 
                    WHERE guild_id = ? 
                    AND start >= datetime('now', '-{} days')""".format(days),
                    (guild_id,)
                )
            row = await cursor.fetchone()
            return row
    
    async def force_end_shift(self, guild_id: int, user_id: int, end_note: Optional[str] = None) -> Shift | None:
        """Force end a user's active shift (admin function)"""
        shift = await self.get_shift(guild_id, user_id)
        if shift:
            shift.end = datetime.now(timezone.utc)
            shift.end_note = end_note
            await self.end_shift(shift)
            return shift
        return None
    
    async def get_settings(self, guild_id: int) -> Settings:
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(
                "SELECT * FROM shift_settings WHERE guild_id = ?", (guild_id,)
            )
            row = await cursor.fetchone()
            if row:
                s = Settings(*row)
                s.staff_role_ids = json.loads(s.staff_role_ids or "[]") # type: ignore
                return s
            else:
                await self.create_default_settings(guild_id)
                return Settings(guild_id, None, [])
    
    async def create_default_settings(self, guild_id: int) -> None:
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                "INSERT INTO shift_settings (guild_id, log_channel_id, staff_role_ids) VALUES (?, ?, ?)", (guild_id, None, json.dumps([]))
            )
            await db.commit()
    
    async def update_settings(self, settings: Settings) -> None:
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                "UPDATE shift_settings SET log_channel_id = ?, staff_role_ids = ? WHERE guild_id = ?",
                (settings.log_channel_id, json.dumps(settings.staff_role_ids), settings.guild_id),
            )
            await db.commit()

class StaffShifts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_embed_provider = LogEmbedProvider(bot)
        self.service = ShiftService(Path("data/staff_shifts.db"))
        self.ready = asyncio.Event()
    
    async def cog_load(self) -> None:
        await self.service.init_db()
        self.ready.set()
    
    async def log_start(self, ctx: commands.Context, shift: Shift):
        assert ctx.guild is not None
        settings = await self.service.get_settings(ctx.guild.id)
        if settings.log_channel_id is None:
            return
        log_channel = self.bot.get_channel(settings.log_channel_id) or await self.bot.fetch_channel(settings.log_channel_id)
        if log_channel is None or not isinstance(log_channel, discord.TextChannel):
            print("Log channel not found")
            return
        await log_channel.send(
            embed=await self.log_embed_provider.get_shift_start_embed(ctx, shift)
        )

    async def log_end(self, ctx: commands.Context, shift: Shift):
        assert ctx.guild is not None
        settings = await self.service.get_settings(ctx.guild.id)
        if settings.log_channel_id is None:
            return
        log_channel = self.bot.get_channel(settings.log_channel_id) or await self.bot.fetch_channel(settings.log_channel_id)
        if log_channel is None or not isinstance(log_channel, discord.TextChannel):
            print("Log channel not found")
            return
        assert shift.end is not None
        await log_channel.send(
            embed=await self.log_embed_provider.get_shift_end_embed(ctx, shift)
        )
    
    async def log_invalidate(self, ctx: commands.Context, shift: Shift):
        assert ctx.guild is not None
        settings = await self.service.get_settings(ctx.guild.id)
        if settings.log_channel_id is None:
            return
        log_channel = self.bot.get_channel(settings.log_channel_id) or await self.bot.fetch_channel(settings.log_channel_id)
        if log_channel is None or not isinstance(log_channel, discord.TextChannel):
            print("Log channel not found")
            return
        await log_channel.send(
            embed=await self.log_embed_provider.get_shift_discard_embed(ctx, shift)
        )
    
    async def is_staff(self, ctx: commands.Context) -> bool:
        assert ctx.guild is not None
        if not isinstance(ctx.author, discord.Member):
            return False
        settings = await self.service.get_settings(ctx.guild.id)
        
        # Debug: Check if any roles are configured
        if not settings.staff_role_ids:
            return False
            
        # Check if user has any of the configured staff roles
        user_role_ids = [role.id for role in ctx.author.roles]
        return any(role_id in settings.staff_role_ids for role_id in user_role_ids)
    
    async def send_staff_error(self, ctx: commands.Context):
        """Send helpful error message when user is not staff"""
        if not ctx.guild:
            return
        settings = await self.service.get_settings(ctx.guild.id)
        if not settings.staff_role_ids:
            await ctx.send("❌ **No staff roles configured!**\n\nAn admin needs to add staff roles first using:\n`/shift settings addrole @YourModRole`")
        else:
            staff_role_mentions = []
            for role_id in settings.staff_role_ids:
                role = ctx.guild.get_role(role_id)
                if role:
                    staff_role_mentions.append(f"<@&{role_id}>")
            
            if staff_role_mentions:
                await ctx.send(f"❌ **You are not a staff member.**\n\nYou need one of these roles to use shift commands:\n{', '.join(staff_role_mentions)}")
            else:
                await ctx.send("❌ **No valid staff roles found.**\n\nAn admin needs to reconfigure staff roles using:\n`/shift settings addrole @YourModRole`")

    @commands.hybrid_group(
        name="shift",
        usage="shift <start | end> [reason/note]",
        description="Allows you to log your on-duty time.",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def shift(self, ctx: commands.Context):
        await self.ready.wait()
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @shift.command(
        name="start",
        usage="shift start [note]",
        description="Logs the start of your duty.",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def shift_start(
        self, ctx: commands.Context, note: str = None  # type: ignore
    ):
        assert ctx.guild is not None
        await self.ready.wait()
        
        # Check if user is staff
        if not (await self.is_staff(ctx)):
            await self.send_staff_error(ctx)
            return
        user_id = ctx.author.id
        existing_shift = await self.service.get_shift(ctx.guild.id, user_id)
        if existing_shift:
            await ctx.send(f"You already have a shift in progress since <t:{round(existing_shift.start.timestamp())}:F>. Use `{ctx.prefix}shift end` to end it now or `{ctx.prefix}shift discard` to discard it.")
            return
        start = datetime.now(timezone.utc)
        await self.service.start_shift(Shift.new(ctx.guild.id, user_id, start, note))
        await ctx.send(f"The start of your shift has been logged at <t:{round(start.timestamp())}:F>. Use `{ctx.prefix}shift end` to log its end.")
        await self.log_start(ctx, Shift.new(ctx.guild.id, user_id, start, note))
    
    @shift.command(
        name="discard",
        aliases=["invalidate"],
        usage="shift discard",
        description="Discards your current shift.",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def shift_invalidate(self, ctx: commands.Context):
        assert ctx.guild is not None
        await self.ready.wait()
        if not (await self.is_staff(ctx)):
            await self.send_staff_error(ctx)
            return
        user_id = ctx.author.id
        current_shift = await self.service.get_shift(ctx.guild.id, user_id)
        if not current_shift:
            await ctx.send("You don't have an active shift.")
            return
        await self.service.discard_shift(current_shift)
        await ctx.send("Your shift has been discarded. You can use `shift start` to start a new one.")
        await self.log_invalidate(ctx, current_shift)

    @shift.command(
        name="end",
        usage="shift end [reason/note]",
        description="Logs the end of your duty and for how long you were on.",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def shift_end(
        self, ctx: commands.Context, reason: str = None  # type: ignore
    ):
        assert ctx.guild is not None
        await self.ready.wait()
        if not (await self.is_staff(ctx)):
            await self.send_staff_error(ctx)
            return
        current_shift = await self.service.get_shift(ctx.guild.id, ctx.author.id)
        if not current_shift:
            await ctx.send("You don't have an active shift.")
            return
        current_shift.end = datetime.now(timezone.utc)
        current_shift.end_note = reason
        await self.service.end_shift(current_shift)
        await ctx.send(f"The end of your shift has been logged at <t:{round(current_shift.end.timestamp())}:F>.")
        await self.log_end(ctx, current_shift)
    
    @shift.group("admin")
    @commands.has_permissions(manage_guild=True)
    async def shift_admin(self, ctx: commands.Context):
        """Admin commands for managing staff shifts"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
    
    @shift_admin.command(
        name="active",
        usage="shift admin active",
        description="View all currently active shifts",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def shift_admin_active(self, ctx: commands.Context):
        """Show all currently active shifts"""
        assert ctx.guild is not None
        await self.ready.wait()
        
        active_shifts = await self.service.get_active_shifts(ctx.guild.id)
        
        if not active_shifts:
            embed = discord.Embed(
                title="📊 Active Shifts", 
                description="No staff members are currently on duty.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="📊 Active Shifts", 
            description=f"**{len(active_shifts)}** staff member(s) currently on duty",
            color=discord.Color.green()
        )
        
        for shift in active_shifts:
            user = ctx.guild.get_member(shift.user_id)
            if user:
                duration = datetime.now(timezone.utc) - shift.start
                hours, remainder = divmod(int(duration.total_seconds()), 3600)
                minutes = remainder // 60
                
                value = f"**Started:** <t:{round(shift.start.timestamp())}:R>\n"
                value += f"**Duration:** {hours}h {minutes}m"
                if shift.start_note:
                    value += f"\n**Note:** {shift.start_note[:100]}{'...' if len(shift.start_note) > 100 else ''}"
                
                embed.add_field(
                    name=f"👤 {user.display_name}",
                    value=value,
                    inline=True
                )
        
        await ctx.send(embed=embed)
    
    @shift_admin.command(
        name="history",
        usage="shift admin history [user] [days]",
        description="View shift history with optional filters",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def shift_admin_history(self, ctx: commands.Context, user: Optional[discord.Member] = None, days: int = 7):
        """Show shift history with optional user and day filters"""
        assert ctx.guild is not None
        await self.ready.wait()
        
        if days < 1 or days > 365:
            await ctx.send("❌ Days must be between 1 and 365.")
            return
        
        user_id = user.id if user else None
        shifts = await self.service.get_shift_history(ctx.guild.id, user_id, days, 20)
        
        if not shifts:
            target = f" for {user.display_name}" if user else ""
            embed = discord.Embed(
                title="📜 Shift History", 
                description=f"No shifts found{target} in the last {days} days.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        target = f" - {user.display_name}" if user else ""
        embed = discord.Embed(
            title=f"📜 Shift History{target}", 
            description=f"Last {len(shifts)} shifts from the past {days} days",
            color=discord.Color.blue()
        )
        
        for shift in shifts[:10]:  # Limit to 10 for embed space
            member = ctx.guild.get_member(shift.user_id)
            username = member.display_name if member else f"Unknown User ({shift.user_id})"
            
            if shift.end:
                duration = shift.end - shift.start
                hours, remainder = divmod(int(duration.total_seconds()), 3600)
                minutes = remainder // 60
                status = f"✅ {hours}h {minutes}m"
            else:
                status = "🔄 Ongoing"
            
            value = f"**Started:** <t:{round(shift.start.timestamp())}:R>\n**Status:** {status}"
            if shift.start_note:
                value += f"\n**Note:** {shift.start_note[:50]}{'...' if len(shift.start_note) > 50 else ''}"
            
            embed.add_field(
                name=f"👤 {username}",
                value=value,
                inline=True
            )
        
        if len(shifts) > 10:
            embed.set_footer(text=f"Showing 10 of {len(shifts)} shifts")
        
        await ctx.send(embed=embed)
    
    @shift_admin.command(
        name="end",
        usage="shift admin end <user> [reason]",
        description="Force end a user's active shift",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def shift_admin_end(self, ctx: commands.Context, user: discord.Member, *, reason: Optional[str] = None):
        """Force end a user's active shift"""
        assert ctx.guild is not None
        await self.ready.wait()
        
        current_shift = await self.service.get_shift(ctx.guild.id, user.id)
        if not current_shift:
            await ctx.send(f"❌ {user.display_name} doesn't have an active shift.")
            return
        
        # Add admin note to end reason
        admin_note = f"[Force ended by {ctx.author.display_name}]"
        if reason:
            end_note = f"{reason} {admin_note}"
        else:
            end_note = admin_note
        
        ended_shift = await self.service.force_end_shift(ctx.guild.id, user.id, end_note)
        if ended_shift and ended_shift.end:
            duration = ended_shift.end - ended_shift.start
            hours, remainder = divmod(int(duration.total_seconds()), 3600)
            minutes = remainder // 60
            
            embed = discord.Embed(
                title="⚠️ Shift Force Ended",
                description=f"Successfully ended {user.mention}'s shift.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Duration", value=f"{hours}h {minutes}m", inline=True)
            embed.add_field(name="Ended by", value=ctx.author.mention, inline=True)
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the forced end
            await self.log_end(ctx, ended_shift)
    
    @shift_admin.command(
        name="stats",
        usage="shift admin stats [user] [days]",
        description="View shift statistics",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def shift_admin_stats(self, ctx: commands.Context, user: Optional[discord.Member] = None, days: int = 30):
        """Show shift statistics"""
        assert ctx.guild is not None
        await self.ready.wait()
        
        if days < 1 or days > 365:
            await ctx.send("❌ Days must be between 1 and 365.")
            return
        
        user_id = user.id if user else None
        stats = await self.service.get_shift_stats(ctx.guild.id, user_id, days)
        
        if user:
            embed = discord.Embed(
                title=f"📊 Shift Statistics - {user.display_name}",
                description=f"Stats for the last {days} days",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
        else:
            embed = discord.Embed(
                title="📊 Server Shift Statistics",
                description=f"Stats for the last {days} days",
                color=discord.Color.blue()
            )
        
        total_shifts = stats[0] if stats else 0
        completed_shifts = stats[1] if stats else 0
        total_seconds = stats[3] if stats and len(stats) > 3 and stats[3] else 0
        avg_seconds = stats[4] if stats and len(stats) > 4 and stats[4] else 0
        
        # Convert seconds to human readable
        total_hours = int(total_seconds // 3600)
        avg_hours = int(avg_seconds // 3600)
        avg_minutes = int((avg_seconds % 3600) // 60)
        
        embed.add_field(name="Total Shifts", value=str(total_shifts), inline=True)
        embed.add_field(name="Completed Shifts", value=str(completed_shifts), inline=True)
        embed.add_field(name="Ongoing Shifts", value=str(total_shifts - completed_shifts), inline=True)
        embed.add_field(name="Total Hours", value=f"{total_hours}h", inline=True)
        
        if completed_shifts > 0:
            embed.add_field(name="Avg Shift Length", value=f"{avg_hours}h {avg_minutes}m", inline=True)
        
        if not user and stats and len(stats) > 2:
            unique_staff = stats[2]
            embed.add_field(name="Active Staff", value=str(unique_staff), inline=True)
        
        await ctx.send(embed=embed)
    
    @shift_admin.command(
        name="summary",
        usage="shift admin summary [days]",
        description="Staff activity summary",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def shift_admin_summary(self, ctx: commands.Context, days: int = 7):
        """Show staff activity summary"""
        assert ctx.guild is not None
        await self.ready.wait()
        
        if days < 1 or days > 365:
            await ctx.send("❌ Days must be between 1 and 365.")
            return
        
        # Get all shifts in the timeframe
        all_shifts = await self.service.get_shift_history(ctx.guild.id, None, days, 1000)
        
        # Get staff roles to identify all potential staff
        settings = await self.service.get_settings(ctx.guild.id)
        staff_members = set()
        for role_id in settings.staff_role_ids:
            role = ctx.guild.get_role(role_id)
            if role:
                staff_members.update(role.members)
        
        # Organize data by user
        user_data = {}
        for shift in all_shifts:
            if shift.user_id not in user_data:
                user_data[shift.user_id] = {'shifts': 0, 'hours': 0, 'ongoing': 0}
            
            user_data[shift.user_id]['shifts'] += 1
            if shift.end:
                duration = (shift.end - shift.start).total_seconds()
                user_data[shift.user_id]['hours'] += duration / 3600
            else:
                user_data[shift.user_id]['ongoing'] += 1
        
        embed = discord.Embed(
            title=f"📈 Staff Activity Summary",
            description=f"Activity report for the last {days} days",
            color=discord.Color.green()
        )
        
        # Active staff (those with shifts)
        active_staff = []
        for user_id, data in user_data.items():
            member = ctx.guild.get_member(user_id)
            if member:
                active_staff.append((member, data))
        
        # Sort by total hours
        active_staff.sort(key=lambda x: x[1]['hours'], reverse=True)
        
        if active_staff:
            top_staff = []
            for member, data in active_staff[:5]:  # Top 5
                hours = int(data['hours'])
                shifts = data['shifts']
                ongoing = data['ongoing']
                status = f" ({ongoing} ongoing)" if ongoing else ""
                top_staff.append(f"👤 **{member.display_name}**: {hours}h, {shifts} shifts{status}")
            
            embed.add_field(
                name="🏆 Most Active Staff",
                value="\n".join(top_staff) if top_staff else "None",
                inline=False
            )
        
        # Inactive staff (staff members with no shifts)
        inactive_staff = []
        for member in staff_members:
            if member.id not in user_data:
                inactive_staff.append(member.display_name)
        
        if inactive_staff:
            embed.add_field(
                name="😴 Inactive Staff",
                value="\n".join([f"👤 {name}" for name in inactive_staff[:10]]) if inactive_staff else "None",
                inline=False
            )
            if len(inactive_staff) > 10:
                embed.set_footer(text=f"Showing 10 of {len(inactive_staff)} inactive staff")
        
        # Overall stats
        total_shifts = sum(data['shifts'] for data in user_data.values())
        total_hours = sum(data['hours'] for data in user_data.values())
        active_count = len(active_staff)
        
        embed.add_field(name="Total Shifts", value=str(total_shifts), inline=True)
        embed.add_field(name="Total Hours", value=f"{int(total_hours)}h", inline=True)
        embed.add_field(name="Active Staff", value=f"{active_count}/{len(staff_members)}", inline=True)
        
        await ctx.send(embed=embed)
    
    @shift.group("settings")
    async def shift_settings(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
    
    @shift_settings.command(
        name="logs",
        usage="shift settings logs [channel]",
        description="Sets the channel for staff shift logs.",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def shift_settings_logs(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None
    ):
        assert ctx.guild is not None
        await self.ready.wait()
        settings = await self.service.get_settings(ctx.guild.id)
        settings.log_channel_id = channel.id if channel is not None else None
        await self.service.update_settings(settings)
        if channel is not None:
            await ctx.send(f"Shift logs will be sent to <#{channel.id}>.")
        else:
            await ctx.send("Shift logging will be disabled.")
    
    @shift_settings.command(
        name="addrole",
        usage="shift settings addrole [role]",
        description="Adds a role to the list of staff roles.",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def shift_settings_addrole(
        self, ctx: commands.Context, role: discord.Role
    ):
        assert ctx.guild is not None
        await self.ready.wait()
        settings = await self.service.get_settings(ctx.guild.id)
        if role.id in settings.staff_role_ids:
            await ctx.send(f"{role.mention} is already a staff role.")
            return
        settings.staff_role_ids.append(role.id)
        await self.service.update_settings(settings)
        await ctx.send(f"{role.mention} is now a staff role.")

    @shift_settings.command(
        name="removerole",
        usage="shift settings removerole [role]",
        description="Removes a role from the list of staff roles.",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def shift_settings_removerole(
        self, ctx: commands.Context, role: discord.Role
    ):
        assert ctx.guild is not None
        await self.ready.wait()
        settings = await self.service.get_settings(ctx.guild.id)
        if role.id not in settings.staff_role_ids:
            await ctx.send(f"{role.mention} is not a staff role.")
            return
        settings.staff_role_ids.remove(role.id)
        await self.service.update_settings(settings)
        await ctx.send(f"{role.mention} is no longer a staff role.")
    
    @shift_settings.command(
        name="clearroles",
        usage="shift settings clearroles",
        description="Clears the list of staff roles.",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def shift_settings_clearroles(
        self, ctx: commands.Context
    ):
        assert ctx.guild is not None
        await self.ready.wait()
        settings = await self.service.get_settings(ctx.guild.id)
        settings.staff_role_ids = []
        await self.service.update_settings(settings)
        await ctx.send("Cleared the list of staff roles.")
    
    @shift_settings.command(
        name="listroles",
        usage="shift settings listroles",
        description="Lists the list of staff roles.",
    )
    @commands.guild_only()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def shift_settings_listroles(
        self, ctx: commands.Context
    ):
        assert ctx.guild is not None
        await self.ready.wait()
        settings = await self.service.get_settings(ctx.guild.id)
        roles: list[discord.Role] = [ctx.guild.get_role(role_id) for role_id in settings.staff_role_ids if ctx.guild.get_role(role_id) is not None] # type: ignore
        await ctx.send(
            "The list of staff roles is: " + "\n -".join(["" if len(roles) > 0 else "None"] + [f"<@&{role.id}>" for role in roles])
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(StaffShifts(bot))
