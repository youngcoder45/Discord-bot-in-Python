import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import logging
from typing import List, Optional

from config import DATABASE_NAME
from utils.embeds import create_info_embed, create_success_embed, create_error_embed
from utils.helpers import safe_interaction_reply

logger = logging.getLogger(__name__)

class PermissionSelect(discord.ui.Select):
    def __init__(self, role_name: str):
        self.role_name = role_name
        options = [
            discord.SelectOption(label="Kick Members", value="kick_members", description="Allow kicking members"),
            discord.SelectOption(label="Ban Members", value="ban_members", description="Allow banning members"),
            discord.SelectOption(label="Timeout/Mute", value="moderate_members", description="Allow timing out members"),
            discord.SelectOption(label="Manage Messages", value="manage_messages", description="Allow purging/deleting messages"),
            discord.SelectOption(label="Manage Nicknames", value="manage_nicknames", description="Allow changing nicknames"),
            discord.SelectOption(label="Warn Members", value="warn_members", description="Allow warning members")
        ]
        super().__init__(placeholder="Select permissions...", min_values=1, max_values=len(options), options=options)

    async def callback(self, interaction: discord.Interaction):
        # Save to DB
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            
            # Create role
            cursor.execute("INSERT OR REPLACE INTO permit_roles (name, guild_id) VALUES (?, ?)", (self.role_name, interaction.guild_id))
            
            # Add permissions
            cursor.execute("DELETE FROM permit_permissions WHERE role_name = ? AND guild_id = ?", (self.role_name, interaction.guild_id))
            for perm in self.values:
                cursor.execute("INSERT INTO permit_permissions (role_name, guild_id, permission) VALUES (?, ?, ?)", (self.role_name, interaction.guild_id, perm))
            
            conn.commit()
            conn.close()
            
            embed = create_success_embed("Role Created", f"Permit role **{self.role_name}** created with permissions: {', '.join(self.values)}")
            await safe_interaction_reply(interaction, embed=embed)
            
            # Disable view
            if self.view:
                self.view.stop()
        except Exception as e:
            logger.error(f"Error creating permit role: {e}")
            embed = create_error_embed("Creation Failed", f"Database error: {e}")
            await safe_interaction_reply(interaction, embed=embed, ephemeral=True)

class PermitView(discord.ui.View):
    def __init__(self, role_name: str):
        super().__init__()
        self.add_item(PermissionSelect(role_name))

class PermitDeleteConfirmView(discord.ui.View):
    """Confirmation prompt before permanently deleting a permit role."""

    def __init__(self, role_name: str, guild_id: int):
        super().__init__(timeout=60)
        self.role_name = role_name
        self.guild_id = guild_id

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def confirm_delete(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # Only administrators (the same group that can invoke the command) may confirm.
        perms = getattr(interaction.user, "guild_permissions", None)
        if perms is None or not perms.administrator:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "No Permission", "Only administrators can confirm this action."
                ),
                ephemeral=True,
            )
            return

        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM permit_permissions WHERE role_name = ? AND guild_id = ?",
                (self.role_name, self.guild_id),
            )
            cursor.execute(
                "DELETE FROM permit_assignments WHERE role_name = ? AND guild_id = ?",
                (self.role_name, self.guild_id),
            )
            cursor.execute(
                "DELETE FROM permit_roles WHERE name = ? AND guild_id = ?",
                (self.role_name, self.guild_id),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error deleting permit role: {e}")
            embed = create_error_embed("Deletion Failed", f"Database error: {e}")
            self.stop()
            await safe_interaction_reply(interaction, embed=embed, ephemeral=True)
            return

        embed = create_success_embed(
            "Permit Role Deleted",
            f"Permit role **{self.role_name}** and all of its assignments were deleted.",
        )
        try:
            await interaction.response.edit_message(embed=embed, view=None)
        except (discord.NotFound, discord.HTTPException) as e:
            logger.warning(f"Could not edit permit delete confirmation: {e}")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_delete(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = create_info_embed(
            "Cancelled", f"Permit role **{self.role_name}** was not deleted."
        )
        try:
            await interaction.response.edit_message(embed=embed, view=None)
        except (discord.NotFound, discord.HTTPException) as e:
            logger.warning(f"Could not edit permit cancel confirmation: {e}")

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        message = getattr(self, "message", None)
        if message is not None:
            try:
                await message.edit(view=self)
            except Exception:
                pass

class PermitListPaginator(discord.ui.View):
    """Paginated view for the `/permit check-all` output."""

    def __init__(self, embeds: list[discord.Embed]):
        super().__init__(timeout=180)
        self.embeds = embeds
        self.page = 0

    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary)
    async def prev_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.page = (self.page - 1) % len(self.embeds)
        try:
            await interaction.response.edit_message(
                embed=self.embeds[self.page], view=self
            )
        except (discord.NotFound, discord.HTTPException) as e:
            logger.warning(f"Could not edit permit list page: {e}")

    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary)
    async def next_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.page = (self.page + 1) % len(self.embeds)
        try:
            await interaction.response.edit_message(
                embed=self.embeds[self.page], view=self
            )
        except (discord.NotFound, discord.HTTPException) as e:
            logger.warning(f"Could not edit permit list page: {e}")

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        message = getattr(self, "message", None)
        if message is not None:
            try:
                await message.edit(view=self)
            except Exception:
                pass

class PermitSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permit_roles (
                name TEXT,
                guild_id INTEGER,
                PRIMARY KEY (name, guild_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permit_permissions (
                role_name TEXT,
                guild_id INTEGER,
                permission TEXT,
                FOREIGN KEY (role_name, guild_id) REFERENCES permit_roles(name, guild_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permit_assignments (
                user_id INTEGER,
                role_name TEXT,
                guild_id INTEGER,
                PRIMARY KEY (user_id, role_name, guild_id)
            )
        ''')
        conn.commit()
        conn.close()

    permit_group = app_commands.Group(name="permit", description="Manage bot permission groups")

    @permit_group.command(name="new")
    @app_commands.describe(name="Name of the new permit role (e.g. 'mod')")
    @commands.has_permissions(administrator=True)
    async def permit_new(self, interaction: discord.Interaction, name: str):
        """Create a new permit role and select permissions"""
        view = PermitView(name)
        embed = discord.Embed(title="Create Permit Role", description=f"Select permissions for **{name}** below:", color=0x00aaff)
        await interaction.response.send_message(embed=embed, view=view)

    @permit_group.command(name="add")
    @app_commands.describe(member="Member to assign the permit role to", role_name="Name of the permit role")
    @commands.has_permissions(administrator=True)
    async def permit_add(self, interaction: discord.Interaction, member: discord.Member, role_name: str):
        """Assign a permit role to a user"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Check if role exists
        cursor.execute("SELECT 1 FROM permit_roles WHERE name = ? AND guild_id = ?", (role_name, interaction.guild_id))
        if not cursor.fetchone():
            conn.close()
            embed = create_error_embed("Role Not Found", f"Permit role **{role_name}** does not exist.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        cursor.execute("INSERT OR IGNORE INTO permit_assignments (user_id, role_name, guild_id) VALUES (?, ?, ?)", 
                       (member.id, role_name, interaction.guild_id))
        conn.commit()
        conn.close()
        
        embed = create_success_embed("Permit Added", f"Added **{role_name}** permit to {member.mention}.")
        await interaction.response.send_message(embed=embed)

    @permit_group.command(name="list")
    async def permit_list(self, interaction: discord.Interaction):
        """List all permit roles"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM permit_roles WHERE guild_id = ?", (interaction.guild_id,))
        roles = cursor.fetchall()
        conn.close()
        
        if not roles:
            await interaction.response.send_message("No permit roles found.", ephemeral=True)
            return

        role_list = "\n".join([r[0] for r in roles])
        embed = discord.Embed(title="Permit Roles", description=role_list, color=0x00aaff)
        await interaction.response.send_message(embed=embed)

    @permit_group.command(name="check")
    @app_commands.describe(member="Member to check")
    async def permit_check(self, interaction: discord.Interaction, member: discord.Member):
        """Check what permits a user has"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pa.role_name, pp.permission 
            FROM permit_assignments pa
            JOIN permit_permissions pp ON pa.role_name = pp.role_name AND pa.guild_id = pp.guild_id
            WHERE pa.user_id = ? AND pa.guild_id = ?
        """, (member.id, interaction.guild_id))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            await interaction.response.send_message("User has no permits.", ephemeral=True)
            return
            
        perm_map = {}
        for role, perm in results:
            if role not in perm_map:
                perm_map[role] = []
            perm_map[role].append(perm)
            
        desc = ""
        for role, perms in perm_map.items():
            desc += f"**{role}**: {', '.join(perms)}\n"
            
        embed = discord.Embed(title=f"Permits for {member.display_name}", description=desc, color=0x00aaff)
        await interaction.response.send_message(embed=embed)

    async def _permit_role_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for permit role names in the current guild."""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM permit_roles WHERE guild_id = ?", (interaction.guild_id,)
        )
        roles = [row[0] for row in cursor.fetchall()]
        conn.close()
        return [
            app_commands.Choice(name=role, value=role)
            for role in roles
            if current.lower() in role.lower()
        ][:25]

    @permit_group.command(name="delete")
    @app_commands.describe(role_name="Name of the permit role to delete")
    @app_commands.autocomplete(role_name=_permit_role_autocomplete)
    @commands.has_permissions(administrator=True)
    async def permit_delete(self, interaction: discord.Interaction, role_name: str):
        """Delete a permit role and all of its assignments"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM permit_roles WHERE name = ? AND guild_id = ?",
            (role_name, interaction.guild_id),
        )
        if not cursor.fetchone():
            conn.close()
            embed = create_error_embed(
                "Role Not Found", f"Permit role **{role_name}** does not exist."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        cursor.execute(
            "SELECT COUNT(*) FROM permit_assignments WHERE role_name = ? AND guild_id = ?",
            (role_name, interaction.guild_id),
        )
        assigned = cursor.fetchone()[0]
        conn.close()

        description = f"Are you sure you want to permanently delete permit role **{role_name}**?"
        if assigned:
            description += (
                f"\n\n**{assigned} user{'s' if assigned != 1 else ''}** "
                f"currently hold{'s' if assigned == 1 else ''} this permit "
                "and will lose access to it."
            )

        view = PermitDeleteConfirmView(role_name, interaction.guild_id)
        embed = create_info_embed("Confirm Deletion", description)
        message = await interaction.response.send_message(embed=embed, view=view)
        view.message = message

    @permit_group.command(name="rename")
    @app_commands.describe(
        role_name="Current name of the permit role",
        new_name="New name for the permit role",
    )
    @app_commands.autocomplete(role_name=_permit_role_autocomplete)
    @commands.has_permissions(administrator=True)
    async def permit_rename(
        self, interaction: discord.Interaction, role_name: str, new_name: str
    ):
        """Rename a permit role (applies to every user assigned to it)"""
        new_name = new_name.strip()
        if not new_name:
            embed = create_error_embed(
                "Invalid Name", "The new name cannot be empty."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if new_name.lower() == role_name.lower():
            embed = create_error_embed(
                "Nothing to Rename", f"**{role_name}** already has that name."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM permit_roles WHERE name = ? AND guild_id = ?",
            (role_name, interaction.guild_id),
        )
        if not cursor.fetchone():
            conn.close()
            embed = create_error_embed(
                "Role Not Found", f"Permit role **{role_name}** does not exist."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Case-insensitive collision check (SQLite compares TEXT case-sensitively,
        # so renaming 'mod' -> 'Mod' would otherwise slip through).
        cursor.execute(
            "SELECT name FROM permit_roles WHERE guild_id = ?", (interaction.guild_id,)
        )
        existing_names = [row[0] for row in cursor.fetchall()]
        if any(n != role_name and n.lower() == new_name.lower() for n in existing_names):
            conn.close()
            embed = create_error_embed(
                "Name Taken",
                f"A permit role named **{new_name}** already exists in this server.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            # Disable foreign keys for the swap so the rename stays safe even
            # if FK enforcement is ever enabled (children reference the parent
            # by the (name, guild_id) composite key).
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.execute(
                "UPDATE permit_permissions SET role_name = ? WHERE role_name = ? AND guild_id = ?",
                (new_name, role_name, interaction.guild_id),
            )
            cursor.execute(
                "UPDATE permit_assignments SET role_name = ? WHERE role_name = ? AND guild_id = ?",
                (new_name, role_name, interaction.guild_id),
            )
            cursor.execute(
                "UPDATE permit_roles SET name = ? WHERE name = ? AND guild_id = ?",
                (new_name, role_name, interaction.guild_id),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            conn.close()
            logger.error(f"Error renaming permit role: {e}")
            embed = create_error_embed("Rename Failed", f"Database error: {e}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = create_success_embed(
            "Permit Role Renamed",
            f"Permit role **{role_name}** renamed to **{new_name}**.",
        )
        await interaction.response.send_message(embed=embed)

    @permit_group.command(name="check-all")
    async def permit_check_all(self, interaction: discord.Interaction):
        """Check all users with permits and what they can do"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT pa.user_id, pa.role_name, pp.permission
            FROM permit_assignments pa
            LEFT JOIN permit_permissions pp
                ON pa.role_name = pp.role_name AND pa.guild_id = pp.guild_id
            WHERE pa.guild_id = ?
            ORDER BY pa.user_id, pa.role_name
            """,
            (interaction.guild_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            embed = create_info_embed(
                "No Permits", "No users have any permits in this server yet."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Group per user: user_id -> {role_name: [permissions]}
        users: dict[int, dict[str, list[str]]] = {}
        for user_id, role, perm in rows:
            users.setdefault(user_id, {}).setdefault(role, [])
            if perm:
                users[user_id][role].append(perm)

        guild = interaction.guild
        user_entries: list[tuple[str, str]] = []  # (label, body)
        for user_id, roles in users.items():
            member = guild.get_member(user_id) if guild else None
            label = member.mention if member else f"<@{user_id}>"
            body_parts = []
            for role, perms in sorted(roles.items()):
                if perms:
                    perms_text = ", ".join(f"`{p}`" for p in perms)
                    body_parts.append(f"**{role}** → {perms_text}")
                else:
                    body_parts.append(f"**{role}** → *no permissions set*")
            user_entries.append((label, "\n".join(body_parts)))

        # Build pages of up to 6 users each
        per_page = 6
        embeds: list[discord.Embed] = []
        for page_index in range(0, len(user_entries), per_page):
            page_entries = user_entries[page_index : page_index + per_page]
            embed = discord.Embed(
                title="Permit Holders",
                description=(
                    f"All **{len(user_entries)}** "
                    f"user{'s' if len(user_entries) != 1 else ''} with permits."
                ),
                color=0x00aaff,
            )
            for label, body in page_entries:
                embed.add_field(name=label, value=body, inline=False)
            embed.set_footer(
                text=f"Page {page_index // per_page + 1}/"
                f"{(len(user_entries) + per_page - 1) // per_page}"
            )
            embeds.append(embed)

        if len(embeds) == 1:
            await interaction.response.send_message(embed=embeds[0])
            return

        view = PermitListPaginator(embeds)
        message = await interaction.response.send_message(embed=embeds[0], view=view)
        view.message = message

    def check_permit(self, user_id: int, guild_id: int, permission: str) -> bool:
        """Helper to check if a user has a specific permit permission"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 
            FROM permit_assignments pa
            JOIN permit_permissions pp ON pa.role_name = pp.role_name AND pa.guild_id = pp.guild_id
            WHERE pa.user_id = ? AND pa.guild_id = ? AND pp.permission = ?
        """, (user_id, guild_id, permission))
        result = cursor.fetchone()
        conn.close()
        return bool(result)

async def setup(bot):
    await bot.add_cog(PermitSystem(bot))
