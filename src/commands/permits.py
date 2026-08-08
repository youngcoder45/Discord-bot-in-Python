import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import logging
from typing import List, Optional

from config import DATABASE_NAME
from utils.embeds import create_success_embed, create_error_embed
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
