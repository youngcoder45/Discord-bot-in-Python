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

    # ============== RANKS COMMAND GROUP ==============
    @commands.hybrid_group(name="ranks", description="Manage and use joinable ranks")
    @commands.guild_only()
    async def ranks_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `/ranks list` to see available ranks or `/ranks join <name>` to join one")

    @ranks_group.command(name="add", description="Add a new joinable rank (role)")
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
        await ctx.reply(f"✅ Added joinable rank {role.mention}.")

    @ranks_group.command(name="del", description="Delete an existing joinable rank")
    @app_commands.describe(name="Exact name of the rank to delete")
    @commands.has_permissions(manage_roles=True)
    async def ranks_del(self, ctx: commands.Context, *, name: str):
        if not ctx.guild:
            return
        role = discord.utils.get(ctx.guild.roles, name=name)
        if not role:
            return await ctx.reply("❌ Role not found.")
        try:
            await role.delete(reason=f"Joinable rank removed by {ctx.author}")
        except discord.Forbidden:
            return await ctx.reply("❌ I do not have permission to delete that role.")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM joinable_roles WHERE guild_id = ? AND role_id = ?", (ctx.guild.id, role.id))
            await db.commit()
        await ctx.reply(f"✅ Deleted rank '{name}'.")

    @ranks_group.command(name="list", description="List all joinable ranks")
    async def ranks_list(self, ctx: commands.Context):
        if not ctx.guild:
            return
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT role_id FROM joinable_roles WHERE guild_id = ?", (ctx.guild.id,))
            rows = list(await cursor.fetchall())
        if not rows:
            return await ctx.reply("📋 No joinable ranks configured.")
        roles_display = []
        for (role_id,) in rows[:50]:
            role = ctx.guild.get_role(role_id)
            if role:
                roles_display.append(role.mention)
        
        embed = discord.Embed(
            title="📋 Joinable Ranks",
            description=" ".join(roles_display),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Use /ranks join <name> to join a rank")
        await ctx.reply(embed=embed)

    @ranks_group.command(name="join", description="Join a joinable rank")
    @app_commands.describe(name="Name of the rank to join")
    async def ranks_join(self, ctx: commands.Context, *, name: str):
        if not ctx.guild:
            return
        # Ensure we're working with a Member object
        member = ctx.guild.get_member(ctx.author.id)
        if not member:
            return await ctx.reply("❌ Could not retrieve your member information.")
            
        role = discord.utils.get(ctx.guild.roles, name=name)
        if not role:
            return await ctx.reply("❌ Role not found.")
        
        # Check if joinable
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT 1 FROM joinable_roles WHERE guild_id = ? AND role_id = ?", (ctx.guild.id, role.id))
            exists = await cursor.fetchone()
        
        if not exists:
            return await ctx.reply("❌ That role is not a joinable rank.")
        
        if role in member.roles:
            return await ctx.reply(f"⚠️ You already have {role.mention}.")
        
        await member.add_roles(role, reason="Rank join")
        await ctx.reply(f"✅ Added {role.mention} to your roles.")

    @ranks_group.command(name="leave", description="Leave a joinable rank")
    @app_commands.describe(name="Name of the rank to leave")
    async def ranks_leave(self, ctx: commands.Context, *, name: str):
        if not ctx.guild:
            return
        # Ensure we're working with a Member object
        member = ctx.guild.get_member(ctx.author.id)
        if not member:
            return await ctx.reply("❌ Could not retrieve your member information.")
            
        role = discord.utils.get(ctx.guild.roles, name=name)
        if not role:
            return await ctx.reply("❌ Role not found.")
        
        # Check if joinable
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT 1 FROM joinable_roles WHERE guild_id = ? AND role_id = ?", (ctx.guild.id, role.id))
            exists = await cursor.fetchone()
        
        if not exists:
            return await ctx.reply("❌ That role is not a joinable rank.")
        
        if role not in member.roles:
            return await ctx.reply(f"⚠️ You don't have {role.mention}.")
        
        await member.remove_roles(role, reason="Rank leave")
        await ctx.reply(f"✅ Removed {role.mention} from your roles.")

    # ============== ROLELIST COMMAND GROUP ==============
    @commands.hybrid_group(name="rolelist", description="List and search server roles")
    @commands.guild_only()
    async def rolelist_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `/rolelist all` to see all roles or `/rolelist search <text>` to search")

    @rolelist_group.command(name="all", description="List all server roles")
    @app_commands.describe(search="Optional search text")
    async def rolelist_all(self, ctx: commands.Context, search: Optional[str] = None):
        if not ctx.guild:
            return await ctx.reply("❌ This command can only be used in a server.")
            
        roles = ctx.guild.roles[1:]  # exclude @everyone
        if search:
            search_lower = search.lower()
            roles = [r for r in roles if search_lower in r.name.lower()]
            if not roles:
                return await ctx.reply(f"❌ No roles match '{search}'.")
        
        roles_display = ", ".join(r.name for r in roles[:100])
        
        embed = discord.Embed(
            title=f"📋 Server Roles ({len(roles)})",
            description=roles_display,
            color=discord.Color.blue()
        )
        if search:
            embed.set_footer(text=f"Filtered by: {search}")
        await ctx.reply(embed=embed)

    # ============== ROLEINFO COMMAND GROUP ==============
    @commands.hybrid_group(name="roleinfo", description="View role information")
    @commands.guild_only()
    async def roleinfo_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `/roleinfo view <role>` to see role details")

    @roleinfo_group.command(name="view", description="View detailed role information")
    @app_commands.describe(role="Role to inspect")
    async def roleinfo_view(self, ctx: commands.Context, role: discord.Role):
        """Detailed role metadata."""
        embed = discord.Embed(title=f"Role: {role.name}", color=role.color or discord.Color.blue())
        embed.add_field(name="ID", value=f"`{role.id}`", inline=True)
        embed.add_field(name="Members", value=str(len(role.members)), inline=True)
        embed.add_field(name="Color", value=f"`#{role.color.value:06X}`", inline=True)
        embed.add_field(name="Mentionable", value="✅ Yes" if role.mentionable else "❌ No", inline=True)
        embed.add_field(name="Hoisted", value="✅ Yes" if role.hoist else "❌ No", inline=True)
        embed.add_field(name="Position", value=str(role.position), inline=True)
        embed.add_field(name="Created", value=f"<t:{int(role.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Managed", value="✅ Yes" if role.managed else "❌ No", inline=True)
        
        # Show permissions count
        perms = [perm for perm, value in role.permissions if value]
        embed.add_field(name="Permissions", value=f"{len(perms)} granted", inline=True)
        
        await ctx.reply(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))
