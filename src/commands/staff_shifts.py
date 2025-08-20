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
        return cls(*row)

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
                s = Shift.from_row(row)
                s.start = datetime.fromisoformat(s.start) if not isinstance(s.start, datetime) else s.start
                s.end = datetime.fromisoformat(s.end) if not isinstance(s.end, datetime) and s.end else s.end
                return s
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
        return any(role.id in settings.staff_role_ids for role in ctx.author.roles)

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
        if not (await self.is_staff(ctx)):
            await ctx.send("You are not a staff member.")
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
            await ctx.send("You are not a staff member.")
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
            await ctx.send("You are not a staff member.")
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
