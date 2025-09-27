import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from pathlib import Path
from typing import Optional, List

DB_PATH = Path("data/roles.db")

class Roles(commands.Cog):
    """Joinable rank (role) management and role info listing."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        await self.init_db()

    async def init_db(self):
        DB_PATH.parent.mkdir(exist_ok=True)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS joinable_roles (
                    guild_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    hoist INTEGER NOT NULL DEFAULT 0,
                    color INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(guild_id, role_id)
                )
            """)
            await db.commit()

    # ============== COMMAND GROUP ==============
    @commands.hybrid_group(name="ranks", description="Manage view or manage joinable ranks.")
    @commands.guild_only()
    async def ranks_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send("Use /ranks list or /ranks add")

    @ranks_group.command(name="add", description="Add a new joinable rank (role).")
    @app_commands.describe(name="Name of the rank", color="Hex color like #FF0000 (optional)", hoist="Display separately")
    @commands.has_permissions(manage_roles=True)
    async def ranks_add(self, ctx: commands.Context, name: str, color: Optional[str] = None, hoist: bool = False):
        if not ctx.guild:
            return
        # Create role
        discord_color = None
        if color:
            hex_clean = color.lstrip('#')
            try:
                value = int(hex_clean, 16)
                discord_color = discord.Color(value)
            except ValueError:
                return await ctx.reply("Invalid color hex.")
        role = await ctx.guild.create_role(name=name, colour=discord_color or discord.Color.default(), hoist=hoist, mentionable=True, reason=f"Joinable rank created by {ctx.author}")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO joinable_roles (guild_id, role_id, name, hoist, color) VALUES (?, ?, ?, ?, ?)",
                             (ctx.guild.id, role.id, role.name, int(hoist), role.colour.value))
            await db.commit()
        await ctx.reply(f"Added joinable rank {role.mention}.")

    @ranks_group.command(name="del", description="Delete an existing joinable rank.")
    @app_commands.describe(name="Exact name of the rank to delete")
    @commands.has_permissions(manage_roles=True)
    async def ranks_del(self, ctx: commands.Context, *, name: str):
        if not ctx.guild:
            return
        role = discord.utils.get(ctx.guild.roles, name=name)
        if not role:
            return await ctx.reply("Role not found.")
        try:
            await role.delete(reason=f"Joinable rank removed by {ctx.author}")
        except discord.Forbidden:
            return await ctx.reply("I do not have permission to delete that role.")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM joinable_roles WHERE guild_id = ? AND role_id = ?", (ctx.guild.id, role.id))
            await db.commit()
        await ctx.reply(f"Deleted rank '{name}'.")

    @ranks_group.command(name="list", description="List all joinable ranks.")
    async def ranks_list(self, ctx: commands.Context):
        if not ctx.guild:
            return
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT role_id FROM joinable_roles WHERE guild_id = ?", (ctx.guild.id,))
            rows = list(await cursor.fetchall())
        if not rows:
            return await ctx.reply("No joinable ranks configured.")
        roles_display = []
        for (role_id,) in rows[:50]:
            role = ctx.guild.get_role(role_id)
            if role:
                roles_display.append(role.mention)
        await ctx.reply("Joinable Ranks:\n" + " ".join(roles_display))

    @commands.hybrid_command(name="rank", help="Join or leave a joinable rank.")
    @app_commands.describe(name="Name of the rank to toggle")
    @commands.guild_only()
    async def rank(self, ctx: commands.Context, *, name: str):
        if not ctx.guild:
            return
        # Ensure we're working with a Member object
        member = ctx.guild.get_member(ctx.author.id)
        if not member:
            return await ctx.reply("Could not retrieve your member information.")
            
        role = discord.utils.get(ctx.guild.roles, name=name)
        if not role:
            return await ctx.reply("Role not found.")
        # Check if joinable
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT 1 FROM joinable_roles WHERE guild_id = ? AND role_id = ?", (ctx.guild.id, role.id))
            exists = await cursor.fetchone()
        if not exists:
            return await ctx.reply("That role is not a joinable rank.")
        if role in member.roles:
            await member.remove_roles(role, reason="Rank toggle remove")
            await ctx.reply(f"Removed {role.mention}.")
        else:
            await member.add_roles(role, reason="Rank toggle add")
            await ctx.reply(f"Added {role.mention}.")

    @commands.hybrid_command(name="roles", help="List all server roles (optional search)")
    @app_commands.describe(search="Optional search text")
    @commands.guild_only()
    async def roles(self, ctx: commands.Context, *, search: Optional[str] = None):
        if not ctx.guild:
            return await ctx.reply("This command can only be used in a server.")
            
        roles = ctx.guild.roles[1:]  # exclude @everyone
        if search:
            search_lower = search.lower()
            roles = [r for r in roles if search_lower in r.name.lower()]
            if not roles:
                return await ctx.reply("No roles match that search.")
        roles_display = ", ".join(r.name for r in roles[:100])
        await ctx.reply(f"Roles ({len(roles)}): {roles_display}")

    @commands.hybrid_command(name="rolemeta", help="Basic role metadata (simple version). For advanced use /roleinfo")
    @app_commands.describe(role="Role to inspect")
    @commands.guild_only()
    async def rolemeta(self, ctx: commands.Context, role: discord.Role):
        """Simplified role metadata (kept separate from advanced /roleinfo)."""
        embed = discord.Embed(title=f"Role: {role.name}", color=role.color or discord.Color.blue())
        embed.add_field(name="ID", value=str(role.id), inline=True)
        embed.add_field(name="Members", value=str(len(role.members)), inline=True)
        embed.add_field(name="Color", value=f"#{role.color.value:06X}", inline=True)
        embed.add_field(name="Mentionable", value=str(role.mentionable), inline=True)
        embed.add_field(name="Hoisted", value=str(role.hoist), inline=True)
        embed.add_field(name="Created", value=f"<t:{int(role.created_at.timestamp())}:R>", inline=True)
        await ctx.reply(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))
