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
from dataclasses import dataclass, field
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
    paused: bool = False
    pause_time: datetime | None = None
    pause_intervals: list[tuple[datetime, datetime]] = field(default_factory=list)
    
    @classmethod
    def new(cls, guild_id: int, user_id: int, start: datetime, start_note: str | None = None):
        return cls(None, guild_id, user_id, start, None, start_note, None, False, None, [])

    @classmethod
    def from_row(cls, row):
        shift_id, guild_id, user_id, start, end, start_note, end_note, paused, pause_time, pause_intervals = row
        
        # Convert string datetimes back to datetime objects if needed
        def parse_datetime(dt_value, default_time=None):
            """Helper function to safely parse datetime values"""
            if isinstance(dt_value, datetime):
                return dt_value
            elif isinstance(dt_value, str) and dt_value:
                try:
                    # Handle various datetime string formats from SQLite
                    dt_str = str(dt_value)
                    if dt_str.endswith('Z'):
                        dt_str = dt_str[:-1] + '+00:00'
                    
                    # Try fromisoformat first
                    try:
                        return datetime.fromisoformat(dt_str)
                    except ValueError:
                        pass
                    
                    # Try without timezone and add UTC
                    clean_str = dt_str.replace('+00:00', '').replace('Z', '')
                    if 'T' in clean_str:
                        return datetime.strptime(clean_str, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
                    else:
                        return datetime.strptime(clean_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                        
                except (ValueError, TypeError, AttributeError) as e:
                    print(f"Error parsing datetime '{dt_value}': {e}")
                    return default_time or datetime.now(timezone.utc)
            else:
                return default_time
        
        # Parse start time (required) - ensure it's never None
        start_dt = parse_datetime(start, datetime.now(timezone.utc))
        if start_dt is None:
            start_dt = datetime.now(timezone.utc)
        
        # Parse end time (optional)
        end_dt = parse_datetime(end, None) if end else None
        
        # Parse pause time (optional)
        pause_time_dt = parse_datetime(pause_time, None) if pause_time else None
        
        # Parse pause intervals
        intervals = []
        if pause_intervals:
            try:
                parsed_intervals = json.loads(pause_intervals)
                for start_interval, end_interval in parsed_intervals:
                    intervals.append((parse_datetime(start_interval), parse_datetime(end_interval)))
            except (json.JSONDecodeError, TypeError, ValueError):
                pass # Keep intervals empty if parsing fails
                
        return cls(shift_id, guild_id, user_id, start_dt, end_dt, start_note, end_note, bool(paused), pause_time_dt, intervals)

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
    
    def safe_timestamp(self, dt) -> int:
        """Safely get timestamp from datetime object or string"""
        try:
            # If it's already a datetime object, use it directly
            if isinstance(dt, datetime):
                return round(dt.timestamp())
            
            # If it's a string, try to parse it
            elif isinstance(dt, str):
                # Handle common datetime string formats
                dt_str = str(dt)  # Ensure it's a string
                
                # Replace Z with proper timezone offset
                if dt_str.endswith('Z'):
                    dt_str = dt_str[:-1] + '+00:00'
                
                # Try parsing with fromisoformat first (most common)
                try:
                    dt_parsed = datetime.fromisoformat(dt_str)
                    return round(dt_parsed.timestamp())
                except (ValueError, TypeError):
                    pass
                
                # Try parsing without timezone info and add UTC
                try:
                    # Remove any timezone suffix for basic parsing
                    clean_str = dt_str.replace('+00:00', '').replace('Z', '')
                    if 'T' in clean_str:
                        dt_parsed = datetime.strptime(clean_str, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
                    else:
                        dt_parsed = datetime.strptime(clean_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                    return round(dt_parsed.timestamp())
                except (ValueError, TypeError):
                    pass
                
                # If all parsing fails, return current time
                print(f"Warning: Could not parse datetime string: {dt_str}")
                return round(datetime.now(timezone.utc).timestamp())
            
            # For any other type (None, int, etc.), return current time
            else:
                print(f"Warning: Unexpected datetime type: {type(dt)} with value: {dt}")
                return round(datetime.now(timezone.utc).timestamp())
                
        except Exception as e:
            # Ultimate fallback - should never reach here
            print(f"Error in safe_timestamp: {e}, input: {dt}, type: {type(dt)}")
            return round(datetime.now(timezone.utc).timestamp())
    
    async def get_shift_start_embed(self, ctx: commands.Context, shift: Shift):
        embed=discord.Embed(title="Shift Started", description=f"{ctx.author.mention} has just started their shift.", color=0x00ff00)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="Start Time", value=f"<t:{self.safe_timestamp(shift.start)}:F>", inline=False)
        if shift.start_note is not None:
            embed.add_field(name="Start Note", value=f"```\n{shift.start_note}\n```", inline=False)
        return embed

    async def get_shift_end_embed(self, ctx: commands.Context, shift: Shift):
        embed=discord.Embed(title="Shift Ended", description=f"{ctx.author.mention} has just ended their shift.", color=0xff0000)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="Start Time", value=f"<t:{self.safe_timestamp(shift.start)}:F>", inline=True)
        if shift.end:
            embed.add_field(name="End Time", value=f"<t:{self.safe_timestamp(shift.end)}:F>", inline=True)
        if shift.start_note is not None:
            embed.add_field(name="Start Note", value=f"```\n{shift.start_note}\n```", inline=False)
        if shift.end_note is not None:
            embed.add_field(name="End Note", value=f"```\n{shift.end_note}\n```", inline=False)
        return embed
    
    async def get_shift_discard_embed(self, ctx: commands.Context, shift: Shift):
        embed=discord.Embed(title="Shift Discarded", description=f"{ctx.author.mention} has just discarded their shift.", color=0xFFFF00)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="Start Time", value=f"<t:{self.safe_timestamp(shift.start)}:F>", inline=True)
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
                    end_note TEXT DEFAULT NULL,
                    paused BOOLEAN DEFAULT 0,
                    pause_time DATETIME DEFAULT NULL,
                    pause_intervals TEXT DEFAULT '[]'
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
                "INSERT INTO shifts (guild_id, user_id, start, start_note, paused, pause_time, pause_intervals) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (shift.guild_id, shift.user_id, shift.start.isoformat(), shift.start_note, int(shift.paused), shift.pause_time.isoformat() if shift.pause_time else None, json.dumps(shift.pause_intervals or [])),
            )
            await db.commit()
    async def pause_shift(self, shift: Shift) -> None:
        """Pause a shift in the database"""
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                "UPDATE shifts SET paused = 1, pause_time = ? WHERE shift_id = ?",
                (datetime.now(timezone.utc).isoformat(), shift.shift_id),
            )
            await db.commit()

    async def resume_shift(self, shift: Shift) -> None:
        """Resume a paused shift, record interval"""
        async with aiosqlite.connect(self.database_path) as db:
            # Load previous intervals
            cursor = await db.execute("SELECT pause_intervals, pause_time FROM shifts WHERE shift_id = ?", (shift.shift_id,))
            row = await cursor.fetchone()
            if not row:
                # This case should ideally not be reached if the shift object is valid
                # but as a safeguard, we stop here.
                return
            intervals = json.loads(row[0]) if row[0] else []
            pause_start = row[1]
            if pause_start:
                intervals.append((pause_start, datetime.now(timezone.utc).isoformat()))
            await db.execute(
                "UPDATE shifts SET paused = 0, pause_time = NULL, pause_intervals = ? WHERE shift_id = ?",
                (json.dumps(intervals), shift.shift_id),
            )
            await db.commit()
    
    async def end_shift(self, shift: Shift) -> None:
        """Updates a shift in the database"""
        async with aiosqlite.connect(self.database_path) as db:
            end_time = shift.end.isoformat() if shift.end else None
            await db.execute(
                "UPDATE shifts SET end = ?, end_note = ? WHERE shift_id = ?",
                (end_time, shift.end_note, shift.shift_id),
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
        self.deprecation_message = "Shift commands are deprecated and disabled."

    async def _notify_deprecated(self, ctx: commands.Context):
        await ctx.send(self.deprecation_message)
    
    def safe_timestamp(self, dt) -> int:
        """Safely get timestamp from datetime object or string"""
        try:
            # If it's already a datetime object, use it directly
            if isinstance(dt, datetime):
                return round(dt.timestamp())
            
            # If it's a string, try to parse it
            elif isinstance(dt, str):
                # Handle common datetime string formats
                dt_str = str(dt)  # Ensure it's a string
                
                # Replace Z with proper timezone offset
                if dt_str.endswith('Z'):
                    dt_str = dt_str[:-1] + '+00:00'
                
                # Try parsing with fromisoformat first (most common)
                try:
                    dt_parsed = datetime.fromisoformat(dt_str)
                    return round(dt_parsed.timestamp())
                except (ValueError, TypeError):
                    pass
                
                # Try parsing without timezone info and add UTC
                try:
                    # Remove any timezone suffix for basic parsing
                    clean_str = dt_str.replace('+00:00', '').replace('Z', '')
                    if 'T' in clean_str:
                        dt_parsed = datetime.strptime(clean_str, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
                    else:
                        dt_parsed = datetime.strptime(clean_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                    return round(dt_parsed.timestamp())
                except (ValueError, TypeError):
                    pass
                
                # If all parsing fails, return current time
                print(f"Warning: Could not parse datetime string: {dt_str}")
                return round(datetime.now(timezone.utc).timestamp())
            
            # For any other type (None, int, etc.), return current time
            else:
                print(f"Warning: Unexpected datetime type: {type(dt)} with value: {dt}")
                return round(datetime.now(timezone.utc).timestamp())
                
        except Exception as e:
            # Ultimate fallback - should never reach here
            print(f"Error in safe_timestamp: {e}, input: {dt}, type: {type(dt)}")
            return round(datetime.now(timezone.utc).timestamp())

    async def cog_load(self) -> None:
        await self.service.init_db()
        self.ready.set()
    
    async def log_start(self, ctx: commands.Context, shift: Shift):
        return

    async def log_end(self, ctx: commands.Context, shift: Shift):
        return
    
    async def log_invalidate(self, ctx: commands.Context, shift: Shift):
        return
    
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
            await ctx.send("No staff roles are configured. An administrator must add at least one using `/shift settings addrole @Role`.")
        else:
            staff_role_mentions = []
            for role_id in settings.staff_role_ids:
                role = ctx.guild.get_role(role_id)
                if role:
                    staff_role_mentions.append(f"<@&{role_id}>")
            
            if staff_role_mentions:
                await ctx.send(f"You don't have permission to use shift commands. Required role(s): {', '.join(staff_role_mentions)}")
            else:
                await ctx.send("Configured staff roles are no longer valid. Please reconfigure with `/shift settings addrole @Role`.")

    @commands.group(
        name="shift",
        usage="shift <start | end> [reason/note]",
        description="Allows you to log your on-duty time.",
        invoke_without_command=True
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def shift(self, ctx: commands.Context):
        await self._notify_deprecated(ctx)
        return

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
        await self._notify_deprecated(ctx)
        return
    
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
        await self._notify_deprecated(ctx)
        return

    @shift.command(
        name="pause",
        usage="shift pause",
        description="Pause your current shift.",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def shift_pause(self, ctx: commands.Context):
        await self._notify_deprecated(ctx)
        return

    @shift.command(
        name="resume",
        usage="shift resume",
        description="Resume your paused shift.",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def shift_resume(self, ctx: commands.Context):
        await self._notify_deprecated(ctx)
        return

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
        await self._notify_deprecated(ctx)
        return
    
    @shift.group("admin")
    @commands.has_permissions(manage_guild=True)
    async def shift_admin(self, ctx: commands.Context):
        """Admin commands for managing staff shifts"""
        await self._notify_deprecated(ctx)
        return
    
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
        await self._notify_deprecated(ctx)
        return
    
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
        await self._notify_deprecated(ctx)
        return
    
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
        await self._notify_deprecated(ctx)
        return
    
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
        await self._notify_deprecated(ctx)
        return
    
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
        await self._notify_deprecated(ctx)
        return
    
    @shift.group("settings")
    async def shift_settings(self, ctx: commands.Context):
        await self._notify_deprecated(ctx)
        return
    
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
        await self._notify_deprecated(ctx)
        return
    
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
        await self._notify_deprecated(ctx)
        return

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
        await self._notify_deprecated(ctx)
        return
    
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
        await self._notify_deprecated(ctx)
        return
    
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
        await self._notify_deprecated(ctx)
        return


async def setup(bot: commands.Bot):
    await bot.add_cog(StaffShifts(bot))
