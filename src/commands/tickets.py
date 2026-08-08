import asyncio
import io
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils.database import DATABASE_NAME
from utils.embeds import create_error_embed, create_info_embed, create_success_embed
from utils.helpers import safe_interaction_reply

logger = logging.getLogger("codeverse.tickets")

# Named colors accepted by the ticket panel command. Each maps to a hex value;
# users can also pass any raw hex code like #00ff00 or 00ff00.
TICKET_NAMED_COLORS: dict[str, int] = {
    "blue": 0x0000FF,
    "red": 0xFF0000,
    "green": 0x00FF00,
    "yellow": 0xFFFF00,
    "orange": 0xFFA500,
    "purple": 0x800080,
    "pink": 0xFF69B4,
    "blurple": 0x5865F2,
    "black": 0x000000,
    "white": 0xFFFFFF,
    "gray": 0x808080,
    "grey": 0x808080,
    "gold": 0xFFD700,
    "cyan": 0x00FFFF,
    "magenta": 0xFF00FF,
    "lime": 0x32CD32,
    "brown": 0xA52A2A,
    "navy": 0x000080,
    "teal": 0x008080,
    "crimson": 0xDC143C,
}


def parse_ticket_color(value: str) -> int | None:
    """Parse a user-supplied color into an integer hex value.

    Accepts either a named color ("blue", "red", ...) or a hex code
    ("#00ff00", "00ff00"). Returns None when the value is invalid.
    """
    if not value:
        return None
    cleaned = value.strip().lstrip("#").lower()
    if cleaned in TICKET_NAMED_COLORS:
        return TICKET_NAMED_COLORS[cleaned]
    try:
        if len(cleaned) == 6:
            return int(cleaned, 16)
    except ValueError:
        pass
    return None


class TicketCategoryView(discord.ui.View):
    """View for selecting ticket category"""

    def __init__(self, cog: "Tickets"):
        super().__init__(timeout=180)
        self.cog = cog

    @discord.ui.select(
        placeholder="Choose a category...",
        options=[
            discord.SelectOption(label="Partnership", value="partnership"),
            discord.SelectOption(label="General Support", value="support"),
            discord.SelectOption(label="Role Issues", value="role_issue"),
            discord.SelectOption(label="Reports", value="report"),
            discord.SelectOption(label="Warn Appeals", value="warn_appeal"),
            discord.SelectOption(label="Other Issues", value="other"),
        ],
    )
    async def category_select(self, interaction: discord.Interaction, select):
        category = select.values[0]
        await self.cog.show_ticket_info(interaction, category)


class TicketConfirmationView(discord.ui.View):
    """View for confirming ticket creation after seeing info"""

    def __init__(self, cog: "Tickets", category: str):
        super().__init__(timeout=120)
        self.cog = cog
        self.category = category

    @discord.ui.button(label="Create This Ticket", style=discord.ButtonStyle.grey)
    async def create_ticket_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.cog.create_ticket(interaction, self.category)

    @discord.ui.button(label="Back to Categories", style=discord.ButtonStyle.grey)
    async def back_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        view = TicketCategoryView(self.cog)
        embed = discord.Embed(
            title="Create a New Ticket",
            description="Please select the category that best describes your issue:",
            color=0x5865F2,
        )
        embed.add_field(
            name="Available Categories",
            value=(
                "**Partnership** - Business partnerships and collaborations\n"
                "**General Support** - Get help with using our services\n"
                "**Role Issues** - Issues related to roles and permissions\n"
                "**Reports** - Report inappropriate behavior\n"
                "**Warn Appeals** - Appeal warnings or moderation actions\n"
                "**Other Issues** - Anything else that needs attention"
            ),
            inline=False,
        )
        embed.set_footer(text="Select a category from the dropdown menu below")
        await interaction.response.edit_message(embed=embed, view=view)


class TicketControlView(discord.ui.View):
    """Persistent view with ticket control buttons"""

    def __init__(self, cog: "Tickets" = None):
        super().__init__(timeout=None)
        self.cog = cog

    async def _get_cog(self) -> Optional["Tickets"]:
        if self.cog is not None:
            return self.cog
        return None

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.grey,
        custom_id="ticket_close_button",
    )
    async def close_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cog = await self._get_cog()
        if cog is None:
            await interaction.response.send_message("Ticket system unavailable.", ephemeral=True)
            return
        await cog.handle_close_ticket(interaction)

    @discord.ui.button(
        label="Claim Ticket",
        style=discord.ButtonStyle.grey,
        custom_id="ticket_claim_button",
    )
    async def claim_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cog = await self._get_cog()
        if cog is None:
            await interaction.response.send_message("Ticket system unavailable.", ephemeral=True)
            return
        await cog.handle_claim_ticket(interaction)


class TicketPanelView(discord.ui.View):
    """Persistent view for the ticket panel"""

    def __init__(self, cog: "Tickets"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Create Ticket",
        style=discord.ButtonStyle.grey,
        custom_id="persistent_ticket_create_button",
    )
    async def create_ticket_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT ticket_channel_id FROM tickets WHERE user_id = ? AND status = "open"',
            (interaction.user.id,),
        )
        existing = cursor.fetchone()
        conn.close()

        if existing:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Ticket Already Open",
                    f"You already have an open ticket: <#{existing[0]}>",
                ),
                ephemeral=True,
            )
            return

        view = TicketCategoryView(self.cog)
        embed = discord.Embed(
            title="Select Ticket Category",
            description="Please choose the category that best describes your issue:",
            color=0x5865F2,
        )
        embed.add_field(
            name="Available Categories",
            value=(
                "**Partnership** - Business partnerships and collaborations\n"
                "**General Support** - Get help with using our services\n"
                "**Role Issues** - Issues related to roles and permissions\n"
                "**Reports** - Report inappropriate behavior\n"
                "**Warn Appeals** - Appeal warnings or moderation actions\n"
                "**Other Issues** - Anything else that needs attention"
            ),
            inline=False,
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class Tickets(commands.Cog):
    """Advanced ticket system using private text channels (one per ticket)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._pending_deletion_tasks: dict[int, asyncio.Task] = {}
        self._init_database()

        # Configuration
        self.ticket_channel_id: Optional[int] = (
            None  # Panel channel id (where the panel lives)
        )
        self.staff_role_id: int = 1417900662053671073
        self.admin_bypass_role_id: int = 1403059755001577543

        self.ticket_counter = self._get_ticket_counter()

        self.bot.loop.create_task(self._restore_persistent_views())
        self.bot.loop.create_task(self._restore_pending_ticket_deletions())

    def cog_unload(self):
        for task in self._pending_deletion_tasks.values():
            if not task.done():
                task.cancel()
        self._pending_deletion_tasks.clear()

    async def _restore_persistent_views(self):
        await self.bot.wait_until_ready()

        await self._restore_ticket_control_views()

        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT guild_id, channel_id, message_id, color FROM ticket_panels")
            panels = cursor.fetchall()
            conn.close()

            for guild_id, channel_id, message_id, panel_color in panels:
                try:
                    guild = self.bot.get_guild(guild_id)
                    if not guild:
                        continue

                    channel = guild.get_channel(channel_id)
                    if not channel or not isinstance(channel, discord.TextChannel):
                        continue

                    try:
                        _message = await channel.fetch_message(message_id)
                        view = TicketPanelView(self)
                        self.bot.add_view(view, message_id=message_id)
                        # Re-apply the stored panel color to the embed after a
                        # restart, since the DB is the source of truth.
                        # Note: check ``is not None`` so black (0x000000) restores too.
                        if panel_color is not None and _message.embeds:
                            embed = _message.embeds[0]
                            if embed.color.value != panel_color:
                                embed.color = discord.Color(panel_color)
                                await _message.edit(embed=embed)
                        logger.info(
                            f"Restored ticket panel view for message {message_id} in guild {guild_id}"
                        )
                    except discord.NotFound:
                        conn2 = sqlite3.connect(DATABASE_NAME)
                        cursor2 = conn2.cursor()
                        cursor2.execute(
                            "DELETE FROM ticket_panels WHERE message_id = ?",
                            (message_id,),
                        )
                        conn2.commit()
                        conn2.close()
                        logger.warning(
                            f"Ticket panel message {message_id} not found, removed from database"
                        )
                    except Exception as e:
                        logger.error(
                            f"Error fetching ticket panel message {message_id}: {e}"
                        )

                except Exception as e:
                    logger.error(
                        f"Error restoring ticket panel for guild {guild_id}: {e}"
                    )

            logger.info(f"Restored {len(panels)} ticket panel views")

        except Exception as e:
            logger.error(f"Error restoring persistent ticket views: {e}")

    async def _restore_pending_ticket_deletions(self):
        """Restore delayed deletions for closed tickets after restarts."""
        await self.bot.wait_until_ready()

        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ticket_id, ticket_channel_id, delete_at
                FROM tickets
                WHERE status = 'closed' AND ticket_channel_id IS NOT NULL AND delete_at IS NOT NULL
                """
            )
            rows = cursor.fetchall()
            conn.close()

            restored = 0
            for ticket_id, channel_id, delete_at in rows:
                delete_at_dt = self._parse_db_timestamp(delete_at)
                if delete_at_dt is None:
                    continue

                channel = self.bot.get_channel(channel_id)
                if channel is None or not isinstance(channel, discord.TextChannel):
                    self._update_ticket_deletion_state(
                        ticket_id, delete_at=None, deleted_at=True
                    )
                    continue

                restored += 1
                self._schedule_ticket_channel_deletion(
                    ticket_id=ticket_id,
                    channel=channel,
                    delete_at=delete_at_dt,
                )

            if restored:
                logger.info(f"Restored {restored} delayed ticket deletions")
        except Exception as e:
            logger.error(f"Error restoring delayed ticket deletions: {e}")

    async def _restore_ticket_control_views(self):
        """Restore TicketControlView for all open tickets so close/claim buttons survive restarts."""
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT ticket_channel_id, welcome_message_id FROM tickets WHERE status = "open" AND ticket_channel_id IS NOT NULL AND welcome_message_id IS NOT NULL'
            )
            tickets = cursor.fetchall()
            conn.close()

            restored = 0
            for channel_id, msg_id in tickets:
                channel = self.bot.get_channel(channel_id)
                if channel is None or not isinstance(channel, discord.TextChannel):
                    continue
                try:
                    await channel.fetch_message(msg_id)
                    view = TicketControlView(self)
                    self.bot.add_view(view, message_id=msg_id)
                    restored += 1
                except discord.NotFound:
                    # Welcome message deleted, skip
                    continue
                except Exception as e:
                    logger.error(f"Error restoring control view for ticket channel {channel_id}: {e}")

            if restored:
                logger.info(f"Restored {restored} ticket control views")
        except Exception as e:
            logger.error(f"Error restoring ticket control views: {e}")

    def _init_database(self):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_channel_id INTEGER,
                ticket_thread_id INTEGER,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                claimed_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                close_reason TEXT
            )
            """
        )

        # Panels
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_panels (
                panel_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                color INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER NOT NULL,
                UNIQUE(guild_id, channel_id, message_id)
            )
            """
        )
        # Migrate pre-existing databases that predate the color column.
        try:
            cursor.execute("ALTER TABLE ticket_panels ADD COLUMN color INTEGER")
        except sqlite3.OperationalError:
            pass  # column already exists

        # Custom log channels
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_log_channels (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                set_by INTEGER NOT NULL,
                set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Roles
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_support_roles (
                guild_id INTEGER PRIMARY KEY,
                role_id INTEGER NOT NULL,
                set_by INTEGER NOT NULL,
                set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_report_roles (
                guild_id INTEGER PRIMARY KEY,
                role_id INTEGER NOT NULL,
                set_by INTEGER NOT NULL,
                set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_partner_roles (
                guild_id INTEGER PRIMARY KEY,
                role_id INTEGER NOT NULL,
                set_by INTEGER NOT NULL,
                set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Ticket category channel for creating tickets
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_category_channels (
                guild_id INTEGER PRIMARY KEY,
                category_id INTEGER NOT NULL,
                set_by INTEGER NOT NULL,
                set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Migration: add welcome_message_id column if missing
        try:
            cursor.execute("PRAGMA table_info(tickets)")
            cols = [row[1] for row in cursor.fetchall()]
            if "welcome_message_id" not in cols:
                cursor.execute("ALTER TABLE tickets ADD COLUMN welcome_message_id INTEGER")
            if "delete_at" not in cols:
                cursor.execute("ALTER TABLE tickets ADD COLUMN delete_at TIMESTAMP")
            if "deleted_at" not in cols:
                cursor.execute("ALTER TABLE tickets ADD COLUMN deleted_at TIMESTAMP")
        except Exception as e:
            print(f"[Tickets] Migration for welcome_message_id failed: {e}")

        # Migration: copy legacy ticket_thread_id into ticket_channel_id if needed
        try:
            cursor.execute("PRAGMA table_info(tickets)")
            cols = [row[1] for row in cursor.fetchall()]
            if "ticket_channel_id" not in cols:
                cursor.execute(
                    "ALTER TABLE tickets ADD COLUMN ticket_channel_id INTEGER"
                )
            if "ticket_thread_id" in cols:
                cursor.execute(
                    "UPDATE tickets SET ticket_channel_id = COALESCE(ticket_channel_id, ticket_thread_id)"
                )
        except Exception as e:
            print(f"[Tickets] Migration check failed: {e}")

        conn.commit()
        conn.close()

    def _get_ticket_counter(self) -> int:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tickets")
        count = cursor.fetchone()[0]
        conn.close()
        return count + 1

    def _get_ticket_log_channel(
        self, guild: discord.Guild
    ) -> Optional[discord.TextChannel]:
        # Your existing hardcoded fallback
        TICKET_LOGS_CHANNEL = 1438487366305190018
        channel = guild.get_channel(TICKET_LOGS_CHANNEL)
        if channel and isinstance(channel, discord.TextChannel):
            return channel

        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT channel_id FROM ticket_log_channels WHERE guild_id = ?",
                (guild.id,),
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                ch = guild.get_channel(result[0])
                if ch and isinstance(ch, discord.TextChannel):
                    return ch
        except Exception as e:
            print(f"[Tickets] Error checking custom log channel: {e}")

        for ch in guild.text_channels:
            if ch.name.lower() in [
                "ticketlog",
                "ticket-log",
                "ticketlogs",
                "ticket-logs",
            ]:
                return ch
        return None

    def _get_support_team_role(self, guild: discord.Guild) -> Optional[discord.Role]:
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role_id FROM ticket_support_roles WHERE guild_id = ?",
                (guild.id,),
            )
            result = cursor.fetchone()
            conn.close()
            if result:
                role = guild.get_role(result[0])
                if role:
                    return role
        except Exception as e:
            print(f"[Tickets] Error checking custom support role: {e}")

        return guild.get_role(self.staff_role_id)

    def _get_report_team_role(self, guild: discord.Guild) -> Optional[discord.Role]:
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role_id FROM ticket_report_roles WHERE guild_id = ?",
                (guild.id,),
            )
            result = cursor.fetchone()
            conn.close()
            if result:
                role = guild.get_role(result[0])
                if role:
                    return role
        except Exception as e:
            print(f"[Tickets] Error checking report team role: {e}")

        return self._get_support_team_role(guild)

    def _get_partner_team_role(self, guild: discord.Guild) -> Optional[discord.Role]:
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role_id FROM ticket_partner_roles WHERE guild_id = ?",
                (guild.id,),
            )
            result = cursor.fetchone()
            conn.close()
            if result:
                role = guild.get_role(result[0])
                if role:
                    return role
        except Exception as e:
            print(f"[Tickets] Error checking partner team role: {e}")

        return self._get_support_team_role(guild)

    def _get_ticket_category_channel(
        self, guild: discord.Guild
    ) -> Optional[discord.CategoryChannel]:
        """Get the configured ticket category channel for a guild."""
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT category_id FROM ticket_category_channels WHERE guild_id = ?",
                (guild.id,),
            )
            result = cursor.fetchone()
            conn.close()
            if result:
                category = guild.get_channel(result[0])
                if category and isinstance(category, discord.CategoryChannel):
                    return category
        except Exception as e:
            print(f"[Tickets] Error checking ticket category channel: {e}")
        return None

    async def show_ticket_info(self, interaction: discord.Interaction, category: str):
        category_info = {
            "partnership": {
                "name": "Partnership",
                "description": "We value building a strong, engaging community and have established clear criteria for our partnership program",
                "guidelines": (
                    "**Server Requirements:**\n"
                    "100+ active members with 1/9 online during peak hours\n"
                    "350+ daily messages in active channels\n"
                    "SFW content and family-friendly environment\n"
                    "Tech/IT focus but different from CodeVerse specialization\n"
                    "Active, reliable moderation team\n\n"
                    "**Partnership Benefits:**\n"
                    "Custom advertisement channels\n"
                    "Cross-community engagement opportunities\n"
                    "Collaborative events and knowledge sharing\n\n"
                    "**Partnership Terms:**\n"
                    "Partnership may be removed if requirements are no longer met, channels are deleted, or community guidelines are violated.\n\n"
                    "**Ready to apply?** Click 'Create This Ticket' to begin the partnership application process."
                ),
                "examples": "Discord server partnerships, tech community collaborations, educational alliances",
                "color": 0x5865F2,
            },
            "support": {
                "name": "General Support",
                "description": "Get help with using our services, platforms, or community features",
                "guidelines": (
                    "**Be specific about your question** - What do you need help with?\n"
                    "**Mention what you've tried** - What steps have you already taken?\n"
                    "**Provide context** - What are you trying to accomplish?\n"
                    "**Include relevant details** - Account info, error messages, etc.\n"
                    "**Be patient** - Our team will help you as soon as possible"
                ),
                "examples": "How to use features, account questions, general guidance",
                "color": 0x5865F2,
            },
            "role_issue": {
                "name": "Role Issues",
                "description": "Report issues related to roles, permissions, or access",
                "guidelines": (
                    "**Missing roles** - Which roles are you missing?\n"
                    "**Permission errors** - What are you trying to do?\n"
                    "**Role color/icon** - Issues with role appearance\n"
                    "**Self-assignable roles** - Problems with reaction roles or commands"
                ),
                "examples": "Didn't get level up role, can't access channel, role color wrong",
                "color": 0x5865F2,
            },
            "report": {
                "name": "Reports",
                "description": "Report inappropriate behavior, rule violations, or misconduct",
                "guidelines": (
                    "**User information** - Who are you reporting? (ID, username)\n"
                    "**Detailed description** - What did they do wrong?\n"
                    "**Evidence** - Screenshots, message links, timestamps\n"
                    "**Rule violations** - Which rules were broken? (optional)\n"
                    "**Your involvement** - Were you directly affected?"
                ),
                "examples": "Harassment, spam, rule breaking, inappropriate content",
                "color": 0x5865F2,
            },
            "warn_appeal": {
                "name": "Warn Appeals",
                "description": "Appeal a warning or moderation action taken against you",
                "guidelines": (
                    "**Case ID** - The ID of the warning (if known)\n"
                    "**Reason for appeal** - Why do you think the warning was unjust?\n"
                    "**Evidence** - Any proof to support your claim\n"
                    "**Honesty** - Be honest about the situation"
                ),
                "examples": "Unjust warning, misunderstanding, incorrect punishment",
                "color": 0x5865F2,
            },
            "other": {
                "name": "Other Issues",
                "description": "Anything else that doesn't fit the above categories",
                "guidelines": (
                    "**Clear subject line** - Summarize your issue in one sentence\n"
                    "**Detailed explanation** - Provide all relevant information\n"
                    "**Urgency level** - Is this time-sensitive?\n"
                    "**Preferred contact method** - How should we follow up?\n"
                    "**Additional context** - Any other details that might help"
                ),
                "examples": "Feedback, suggestions, questions not covered by other categories",
                "color": 0x5865F2,
            },
        }

        info = category_info.get(category, category_info["other"])

        embed = discord.Embed(
            title=info["name"],
            description=info["description"],
            color=info["color"],
        )
        embed.add_field(
            name="Guidelines for this ticket type:",
            value=info["guidelines"],
            inline=False,
        )
        embed.add_field(name="Examples:", value=info["examples"], inline=False)
        embed.add_field(
            name="What happens next?",
            value=(
                "Your ticket will be created as a private channel\n"
                "Our support team will be notified automatically\n"
                "You'll receive help from qualified staff members\n"
                "The ticket will remain open until your issue is resolved"
            ),
            inline=False,
        )
        embed.set_footer(
            text="Click 'Create This Ticket' if you're ready to proceed, or go back to choose a different category."
        )

        view = TicketConfirmationView(self, category)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def create_ticket(self, interaction: discord.Interaction, category: str):
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            return

        guild = interaction.guild
        user = interaction.user

        category_info = {
            "partnership": ("", "Partnership"),
            "support": ("", "General Support"),
            "role_issue": ("", "Role Issues"),
            "report": ("", "Reports"),
            "warn_appeal": ("", "Warn Appeals"),
            "other": ("", "Other Issues"),
        }
        _emoji, category_name = category_info.get(category, ("", "Ticket"))

        panel_channel_id = self.ticket_channel_id or interaction.channel_id
        if panel_channel_id is None:
            await interaction.followup.send(
                embed=create_error_embed(
                    "Configuration Error", "No ticket panel channel configured."
                ),
                ephemeral=True,
            )
            return

        panel_channel = guild.get_channel(panel_channel_id)
        if not panel_channel or not isinstance(panel_channel, discord.TextChannel):
            await interaction.followup.send(
                embed=create_error_embed(
                    "Configuration Error",
                    "Ticket panel channel not properly configured.",
                ),
                ephemeral=True,
            )
            return

        # Create ticket channel under the same category as the panel channel
        ticket_number = self.ticket_counter
        self.ticket_counter += 1

        channel_name = (
            f"ticket-{ticket_number:04d}-{category_name.lower().replace(' ', '-')}"
        )
        # Use configured ticket category, or fall back to panel channel's category
        parent_category = self._get_ticket_category_channel(guild)
        if not parent_category:
            parent_category = panel_channel.category

        staff_role = None
        if category in ("report", "warn_appeal"):
            staff_role = self._get_report_team_role(guild)
        elif category == "partnership":
            staff_role = self._get_partner_team_role(guild)
        else:
            staff_role = self._get_support_team_role(guild)

        overwrites: dict[discord.abc.Snowflake, discord.PermissionOverwrite] = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
                add_reactions=True,
            ),
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
                attach_files=True,
                embed_links=True,
                add_reactions=True,
            )

        if guild.me:
            overwrites[guild.me] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
                manage_messages=True,
            )

        try:
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=parent_category,
                overwrites=overwrites,
                topic=f"Ticket #{ticket_number} | {category_name} | User: {user} ({user.id})",
            )
        except Exception as e:
            await interaction.followup.send(
                embed=create_error_embed("Failed to Create Ticket", f"Error: {str(e)}"),
                ephemeral=True,
            )
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tickets (ticket_channel_id, ticket_thread_id, user_id, category) VALUES (?, ?, ?, ?)",
            (ticket_channel.id, ticket_channel.id, user.id, category),
        )
        ticket_id = cursor.lastrowid
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title=f"Ticket #{ticket_number} - {category_name}",
            description=(
                f"Welcome {user.mention}! Thank you for creating a ticket.\n\n"
                "Please describe your issue in detail, and our staff team will assist you shortly."
            ),
            color=0x00FF00,
        )
        embed.add_field(
            name="Ticket Information",
            value=(
                f"**Category:** {category_name}\n"
                f"**Created:** <t:{int(datetime.now(timezone.utc).timestamp())}:R>\n"
                f"**Status:** Open"
            ),
            inline=False,
        )
        embed.add_field(
            name="Ticket Controls",
            value=("• Close - Close this ticket\n• Claim - Claim this ticket (Staff)"),
            inline=False,
        )
        embed.set_footer(text=f"Ticket ID: {ticket_id} | CodeVerse Support")

        view = TicketControlView(self)
        staff_mention = staff_role.mention if staff_role else "@Staff"
        welcome_msg = await ticket_channel.send(
            content=f"{user.mention} | Staff: {staff_mention}",
            embed=embed,
            view=view,
        )

        # Store welcome_message_id for persistent view restoration
        try:
            conn2 = sqlite3.connect(DATABASE_NAME)
            cur2 = conn2.cursor()
            cur2.execute(
                "UPDATE tickets SET welcome_message_id = ? WHERE ticket_id = ?",
                (welcome_msg.id, ticket_id),
            )
            conn2.commit()
            conn2.close()
        except Exception as e:
            print(f"[Tickets] Failed to store welcome_message_id: {e}")

        await interaction.followup.send(
            embed=create_success_embed(
                "Ticket Created",
                f"Your ticket has been created: {ticket_channel.mention}",
            ),
            ephemeral=True,
        )

        await self._log_ticket_action(
            "CREATED",
            ticket_id,
            ticket_channel,
            user,
            category_name,
        )

    async def handle_close_ticket(self, interaction: discord.Interaction):
        # Acknowledge immediately: the DB reads and API calls below can exceed
        # Discord's 3-second window for button interactions (10062).
        try:
            await interaction.response.defer(ephemeral=True)
        except (discord.NotFound, discord.HTTPException):
            logger.warning(
                "Ticket close interaction expired before ack (user %s).",
                getattr(interaction.user, "id", None),
            )
            return

        if (
            not isinstance(interaction.channel, discord.TextChannel)
            or not interaction.guild
        ):
            await interaction.followup.send(
                embed=create_error_embed(
                    "Not a Ticket", "This command can only be used in ticket channels."
                ),
                ephemeral=True,
            )
            return

        channel = interaction.channel

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT ticket_id, user_id, category FROM tickets WHERE ticket_channel_id = ? AND status = "open"',
            (channel.id,),
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            await interaction.followup.send(
                embed=create_error_embed(
                    "Not a Ticket", "This is not an open ticket channel."
                ),
                ephemeral=True,
            )
            return

        ticket_id, user_id, category = result

        has_permission = self._is_staff_or_owner(interaction, user_id)

        if not has_permission:
            conn.close()
            await interaction.followup.send(
                embed=create_error_embed(
                    "No Permission",
                    "Only the ticket owner or staff can close this ticket.",
                ),
                ephemeral=True,
            )
            return

        cursor.execute(
            'UPDATE tickets SET status = "closed", closed_at = CURRENT_TIMESTAMP, close_reason = ?, delete_at = datetime(CURRENT_TIMESTAMP, "+24 hours"), deleted_at = NULL WHERE ticket_id = ?',
            (f"Closed by {interaction.user}", ticket_id),
        )
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="Ticket Closed",
            description=f"This ticket has been closed by {interaction.user.mention}",
            color=0xFF0000,
        )
        embed.add_field(
            name="Next Steps",
            value=(
                "A transcript has been saved.\n"
                "This channel will remain available for 24 hours so staff can review it before it is deleted."
            ),
            inline=False,
        )
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.followup.send(embed=embed)

        await self._generate_transcript(channel, ticket_id, save_to_log=True)

        self._schedule_ticket_channel_deletion(
            ticket_id=ticket_id,
            channel=channel,
            delete_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )

        await self._log_ticket_action(
            "CLOSED",
            ticket_id,
            channel,
            interaction.user,
            category,
            f"Closed by {interaction.user.name} | Transcript saved; channel deletes in 24 hours",
        )

    def _is_staff_or_owner(
        self, interaction: discord.Interaction, user_id: int
    ) -> bool:
        """Check if the user is the ticket owner or has a staff/admin role."""
        if isinstance(interaction.user, discord.Member):
            if interaction.user.id == user_id:
                return True
            guild = interaction.guild
            allowed_roles = {self.staff_role_id, self.admin_bypass_role_id}
            # Also check dynamically configured support/report/partner roles
            for role_getter in (
                self._get_support_team_role,
                self._get_report_team_role,
                self._get_partner_team_role,
            ):
                try:
                    role = role_getter(guild)
                    if role:
                        allowed_roles.add(role.id)
                except Exception:
                    pass
            return (
                any(r.id in allowed_roles for r in interaction.user.roles)
                or interaction.user.guild_permissions.administrator
            )
        return interaction.user.id == user_id

    def _is_staff(self, interaction: discord.Interaction) -> bool:
        """Check if the user has a staff/admin role."""
        if isinstance(interaction.user, discord.Member):
            guild = interaction.guild
            allowed_roles = {self.staff_role_id, self.admin_bypass_role_id}
            for role_getter in (
                self._get_support_team_role,
                self._get_report_team_role,
                self._get_partner_team_role,
            ):
                try:
                    role = role_getter(guild)
                    if role:
                        allowed_roles.add(role.id)
                except Exception:
                    pass
            return (
                any(r.id in allowed_roles for r in interaction.user.roles)
                or interaction.user.guild_permissions.administrator
            )
        return False

    async def handle_claim_ticket(self, interaction: discord.Interaction):
        # Acknowledge immediately: the DB reads and the fetch_user API call
        # below can exceed Discord's 3-second window for button interactions.
        try:
            await interaction.response.defer(ephemeral=True)
        except (discord.NotFound, discord.HTTPException):
            logger.warning(
                "Ticket claim interaction expired before ack (user %s).",
                getattr(interaction.user, "id", None),
            )
            return

        if (
            not isinstance(interaction.channel, discord.TextChannel)
            or not interaction.guild
        ):
            await interaction.followup.send(
                embed=create_error_embed(
                    "Not a Ticket", "This command can only be used in ticket channels."
                ),
                ephemeral=True,
            )
            return

        channel = interaction.channel

        if not self._is_staff(interaction):
            await interaction.followup.send(
                embed=create_error_embed(
                    "No Permission", "Only staff members can claim tickets."
                ),
                ephemeral=True,
            )
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT ticket_id, user_id, claimed_by FROM tickets WHERE ticket_channel_id = ? AND status = "open"',
            (channel.id,),
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            await interaction.followup.send(
                embed=create_error_embed(
                    "Not a Ticket", "This is not an open ticket channel."
                ),
                ephemeral=True,
            )
            return

        ticket_id, _user_id, claimed_by = result

        if claimed_by:
            try:
                claimer = await self.bot.fetch_user(claimed_by)
                msg = f"This ticket is already claimed by {claimer.mention}"
            except Exception:
                msg = "This ticket is already claimed by someone."
            conn.close()
            await interaction.followup.send(
                embed=create_info_embed("Already Claimed", msg),
                ephemeral=True,
            )
            return

        cursor.execute(
            "UPDATE tickets SET claimed_by = ? WHERE ticket_id = ?",
            (interaction.user.id, ticket_id),
        )
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="Ticket Claimed",
            description=f"{interaction.user.mention} is now handling this ticket.",
            color=0x0000FF,
        )
        embed.timestamp = datetime.now(timezone.utc)
        await interaction.followup.send(embed=embed)

        await self._log_ticket_action(
            "CLAIMED",
            ticket_id,
            channel,
            interaction.user,
        )

    async def _generate_transcript(
        self,
        channel: discord.TextChannel,
        ticket_id: int,
        save_to_log: bool = False,
    ) -> Optional[str]:
        try:
            messages: list[str] = []
            async for message in channel.history(limit=500, oldest_first=True):
                timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                author = f"{message.author.display_name}"
                content = message.content or "[No text content]"

                if message.attachments:
                    for attachment in message.attachments:
                        content += f"\n[Attachment: {attachment.url}]"

                messages.append(f"[{timestamp}] {author}: {content}")

            transcript = (
                f"Ticket #{ticket_id} Transcript\n"
                f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                + ("=" * 80)
                + "\n\n"
                + "\n".join(messages)
            )

            if save_to_log and channel.guild:
                log_channel = self._get_ticket_log_channel(channel.guild)
                if log_channel:
                    file = discord.File(
                        io.BytesIO(transcript.encode("utf-8")),
                        filename=f"ticket-{ticket_id}-transcript.txt",
                    )
                    embed = discord.Embed(
                        title=f"Ticket #{ticket_id} Transcript",
                        description="Transcript saved for closed ticket.",
                        color=0x95A5A6,
                    )
                    embed.timestamp = datetime.now(timezone.utc)
                    await log_channel.send(embed=embed, file=file)

            return transcript
        except Exception as e:
            print(f"[Tickets] Failed to generate transcript: {e}")
            return None

    def _parse_db_timestamp(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None

        try:
            parsed = datetime.fromisoformat(str(value))
        except ValueError:
            try:
                parsed = datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _update_ticket_deletion_state(
        self, ticket_id: int, *, delete_at: Optional[datetime], deleted_at: bool = False
    ) -> None:
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tickets
                SET delete_at = ?, deleted_at = ?
                WHERE ticket_id = ?
                """,
                (
                    delete_at.strftime("%Y-%m-%d %H:%M:%S")
                    if delete_at is not None
                    else None,
                    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    if deleted_at
                    else None,
                    ticket_id,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Tickets] Failed to update deletion state for ticket #{ticket_id}: {e}")

    async def _delete_ticket_channel_later(
        self, ticket_id: int, channel: discord.TextChannel, delete_at: datetime
    ):
        try:
            delay = (delete_at - datetime.now(timezone.utc)).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)

            if channel.guild is None:
                return
            fresh_channel = channel.guild.get_channel(channel.id)
            if fresh_channel is None:
                self._update_ticket_deletion_state(ticket_id, delete_at=None, deleted_at=True)
                return

            await fresh_channel.delete(
                reason=f"Ticket #{ticket_id} deleted 24 hours after closure"
            )
            self._update_ticket_deletion_state(ticket_id, delete_at=None, deleted_at=True)
        except asyncio.CancelledError:
            raise
        except discord.NotFound:
            self._update_ticket_deletion_state(ticket_id, delete_at=None, deleted_at=True)
        except Exception as e:
            print(f"[Tickets] Failed to delete ticket channel #{ticket_id}: {e}")

    def _schedule_ticket_channel_deletion(
        self, ticket_id: int, channel: discord.TextChannel, delete_at: datetime
    ) -> None:
        existing_task = self._pending_deletion_tasks.pop(ticket_id, None)
        if existing_task and not existing_task.done():
            existing_task.cancel()

        self._update_ticket_deletion_state(ticket_id, delete_at=delete_at)
        task = self.bot.loop.create_task(
            self._delete_ticket_channel_later(ticket_id, channel, delete_at)
        )

        def _cleanup(done_task: asyncio.Task, *, _ticket_id: int = ticket_id):
            current = self._pending_deletion_tasks.get(_ticket_id)
            if current is done_task:
                self._pending_deletion_tasks.pop(_ticket_id, None)

        task.add_done_callback(_cleanup)
        self._pending_deletion_tasks[ticket_id] = task

    async def _log_ticket_action(
        self,
        action: str,
        ticket_id: int,
        channel: discord.abc.GuildChannel,
        user: discord.User | discord.Member,
        category: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        if not channel.guild:
            return

        log_channel = self._get_ticket_log_channel(channel.guild)
        if not log_channel:
            return

        colors = {"CREATED": 0x00FF00, "CLOSED": 0xFF0000, "CLAIMED": 0x0000FF}
        titles = {
            "CREATED": "Ticket Created",
            "CLOSED": "Ticket Closed",
            "CLAIMED": "Ticket Claimed",
        }

        embed = discord.Embed(
            title=titles.get(action, f"Ticket {action}"),
            color=colors.get(action, 0x95A5A6),
        )
        embed.add_field(name="Ticket ID", value=f"#{ticket_id}", inline=True)
        embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=True)
        embed.add_field(name="Channel", value=channel.mention, inline=True)

        if category:
            embed.add_field(name="Category", value=str(category), inline=True)
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)

        embed.timestamp = datetime.now(timezone.utc)
        embed.set_footer(text="Ticket System")

        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            print(f"[Tickets] Failed to send log: {e}")

    @commands.hybrid_group(name="ticket", description="Manage tickets, panels, and ticket settings.")
    async def ticket_group(self, ctx: commands.Context):
        """Ticket system commands. Use `?help ticket` for the subcommands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @ticket_group.command(name="panel")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        channel="Channel to send the ticket panel to",
        support_role="Role to use for support tickets (optional)",
        report_role="Role to use for report tickets (optional)",
        partner_role="Role to use for partnership tickets (optional)",
        color="Panel color: hex code (#00ff00) or name (blue, red, green, ...)",
    )
    async def ticket_panel(
        self,
        ctx,
        channel: Optional[discord.TextChannel] = None,
        support_role: Optional[discord.Role] = None,
        report_role: Optional[discord.Role] = None,
        partner_role: Optional[discord.Role] = None,
        color: Optional[str] = None,
    ):
        """Create a persistent ticket panel"""
        # Defer the response to prevent timeout issues
        await ctx.defer(ephemeral=True)
        
        target_channel = channel or ctx.channel

        if not isinstance(target_channel, discord.TextChannel):
            await ctx.followup.send(
                embed=create_error_embed(
                    "Invalid Channel", "Please provide a valid text channel."
                ),
                ephemeral=True,
            )
            return

        panel_color = parse_ticket_color(color) if color else 0x5865F2
        if panel_color is None:
            named = ", ".join(sorted(TICKET_NAMED_COLORS))
            await ctx.followup.send(
                embed=create_error_embed(
                    "Invalid Color",
                    f"Could not parse `{color}`. Use a hex code like `#00ff00` "
                    f"or a named color: `{named}`.",
                ),
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="Support Tickets",
            description=(
                "Need help? Click **Create Ticket** below to get started!\n"
                "Select a category and confirm to create a private ticket channel.\n\n"
                "**Available Categories:**\n"
                "• General Support\n"
                "• Role Issues\n"
                "• Warn Appeals\n"
                "• Partnership\n"
                "• Reports\n"
                "• Other Issues\n\n"
                "> Note:- Creating tickets for fun or spam may lead to disciplinary action."
            ),
            color=panel_color,
        )

        view = TicketPanelView(self)
        panel_message = await target_channel.send(embed=embed, view=view)

        if ctx.guild:
            try:
                conn = sqlite3.connect(DATABASE_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO ticket_panels (guild_id, channel_id, message_id, color, created_by)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (ctx.guild.id, target_channel.id, panel_message.id, panel_color, ctx.author.id),
                )

                if support_role:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO ticket_support_roles (guild_id, role_id, set_by, set_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (ctx.guild.id, support_role.id, ctx.author.id),
                    )
                if report_role:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO ticket_report_roles (guild_id, role_id, set_by, set_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (ctx.guild.id, report_role.id, ctx.author.id),
                    )
                if partner_role:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO ticket_partner_roles (guild_id, role_id, set_by, set_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (ctx.guild.id, partner_role.id, ctx.author.id),
                    )

                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Error saving ticket panel/roles to database: {e}")

        self.ticket_channel_id = target_channel.id

        await ctx.followup.send(
            embed=create_success_embed(
                "Panel Created", f"Ticket panel created in {target_channel.mention}."
            ),
            ephemeral=True,
        )

    @ticket_group.command(name="log")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        channel="The channel to use for ticket logs (leave empty to view current setting)"
    )
    async def ticket_log_setup(
        self, ctx, channel: Optional[discord.TextChannel] = None
    ):
        if not ctx.guild:
            await ctx.send(
                embed=create_error_embed(
                    "Error", "This command can only be used in servers."
                ),
                ephemeral=True,
            )
            return

        if channel is None:
            current_log_channel = self._get_ticket_log_channel(ctx.guild)
            if current_log_channel:
                await ctx.send(
                    embed=create_info_embed(
                        "Ticket Log Channel",
                        f"Current ticket log channel: {current_log_channel.mention}",
                    ),
                    ephemeral=True,
                )
            else:
                await ctx.send(
                    embed=create_info_embed(
                        "Ticket Log Channel", "No ticket log channel is currently set."
                    ),
                    ephemeral=True,
                )
            return

        try:
            test_msg = await channel.send(
                embed=discord.Embed(title="Test", description="Ticket logging enabled.")
            )
            await test_msg.delete()

            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO ticket_log_channels (guild_id, channel_id, set_by, set_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (ctx.guild.id, channel.id, ctx.author.id),
            )
            conn.commit()
            conn.close()

            await ctx.send(
                embed=create_success_embed(
                    "Ticket Log Channel Set",
                    f"Ticket logs will be sent to {channel.mention}",
                ),
                ephemeral=True,
            )
        except discord.Forbidden:
            await ctx.send(
                embed=create_error_embed(
                    "Permission Error", f"I cannot send messages in {channel.mention}"
                ),
                ephemeral=True,
            )
        except Exception as e:
            await ctx.send(
                embed=create_error_embed("Setup Error", str(e)), ephemeral=True
            )

    @ticket_group.command(name="log-disable")
    @commands.has_permissions(administrator=True)
    async def ticket_log_disable(self, ctx):
        if not ctx.guild:
            await ctx.send(
                embed=create_error_embed(
                    "Error", "This command can only be used in servers."
                ),
                ephemeral=True,
            )
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM ticket_log_channels WHERE guild_id = ?", (ctx.guild.id,)
        )
        conn.commit()
        conn.close()

        await ctx.send(
            embed=create_success_embed(
                "Ticket Logging", "Custom ticket log channel setting removed."
            ),
            ephemeral=True,
        )

    @ticket_group.command(name="support")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(role="Support role (leave empty to view current setting)")
    async def ticket_support_role(self, ctx, role: Optional[discord.Role] = None):
        if not ctx.guild:
            await ctx.send(
                embed=create_error_embed(
                    "Error", "This command can only be used in servers."
                ),
                ephemeral=True,
            )
            return

        if role is None:
            current = self._get_support_team_role(ctx.guild)
            await ctx.send(
                embed=create_info_embed(
                    "Support Role",
                    f"Current: {current.mention if current else 'Not set'}",
                ),
                ephemeral=True,
            )
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO ticket_support_roles (guild_id, role_id, set_by, set_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (ctx.guild.id, role.id, ctx.author.id),
        )
        conn.commit()
        conn.close()
        await ctx.send(
            embed=create_success_embed(
                "Support Role Set", f"Support role set to {role.mention}"
            ),
            ephemeral=True,
        )

    @ticket_group.command(name="support-disable")
    @commands.has_permissions(administrator=True)
    async def ticket_support_role_disable(self, ctx):
        if not ctx.guild:
            await ctx.send(
                embed=create_error_embed(
                    "Error", "This command can only be used in servers."
                ),
                ephemeral=True,
            )
            return
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM ticket_support_roles WHERE guild_id = ?", (ctx.guild.id,)
        )
        conn.commit()
        conn.close()
        await ctx.send(
            embed=create_success_embed("Support Role", "Support role setting removed."),
            ephemeral=True,
        )

    @ticket_group.command(name="report")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(role="Report role (leave empty to view current setting)")
    async def ticket_report_role(self, ctx, role: Optional[discord.Role] = None):
        if not ctx.guild:
            await ctx.send(
                embed=create_error_embed(
                    "Error", "This command can only be used in servers."
                ),
                ephemeral=True,
            )
            return

        if role is None:
            current = self._get_report_team_role(ctx.guild)
            await ctx.send(
                embed=create_info_embed(
                    "Report Role",
                    f"Current: {current.mention if current else 'Not set'}",
                ),
                ephemeral=True,
            )
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO ticket_report_roles (guild_id, role_id, set_by, set_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (ctx.guild.id, role.id, ctx.author.id),
        )
        conn.commit()
        conn.close()
        await ctx.send(
            embed=create_success_embed(
                "Report Role Set", f"Report role set to {role.mention}"
            ),
            ephemeral=True,
        )

    @ticket_group.command(name="report-disable")
    @commands.has_permissions(administrator=True)
    async def ticket_report_role_disable(self, ctx):
        if not ctx.guild:
            await ctx.send(
                embed=create_error_embed(
                    "Error", "This command can only be used in servers."
                ),
                ephemeral=True,
            )
            return
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM ticket_report_roles WHERE guild_id = ?", (ctx.guild.id,)
        )
        conn.commit()
        conn.close()
        await ctx.send(
            embed=create_success_embed("Report Role", "Report role setting removed."),
            ephemeral=True,
        )

    @ticket_group.command(name="partner")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(role="Partner role (leave empty to view current setting)")
    async def ticket_partner_role(self, ctx, role: Optional[discord.Role] = None):
        if not ctx.guild:
            await ctx.send(
                embed=create_error_embed(
                    "Error", "This command can only be used in servers."
                ),
                ephemeral=True,
            )
            return

        if role is None:
            current = self._get_partner_team_role(ctx.guild)
            await ctx.send(
                embed=create_info_embed(
                    "Partner Role",
                    f"Current: {current.mention if current else 'Not set'}",
                ),
                ephemeral=True,
            )
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO ticket_partner_roles (guild_id, role_id, set_by, set_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (ctx.guild.id, role.id, ctx.author.id),
        )
        conn.commit()
        conn.close()
        await ctx.send(
            embed=create_success_embed(
                "Partner Role Set", f"Partner role set to {role.mention}"
            ),
            ephemeral=True,
        )

    @ticket_group.command(name="partner-disable")
    @commands.has_permissions(administrator=True)
    async def ticket_partner_role_disable(self, ctx):
        if not ctx.guild:
            await ctx.send(
                embed=create_error_embed(
                    "Error", "This command can only be used in servers."
                ),
                ephemeral=True,
            )
            return
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM ticket_partner_roles WHERE guild_id = ?", (ctx.guild.id,)
        )
        conn.commit()
        conn.close()
        await ctx.send(
            embed=create_success_embed("Partner Role", "Partner role setting removed."),
            ephemeral=True,
        )

    @ticket_group.command(name="category")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        category="The category channel for tickets (leave empty to view current setting)"
    )
    async def ticket_category_setup(
        self, ctx, category: Optional[discord.CategoryChannel] = None
    ):
        """Set or view the category channel where tickets will be created."""
        if not ctx.guild:
            await ctx.send(
                embed=create_error_embed(
                    "Error", "This command can only be used in servers."
                ),
                ephemeral=True,
            )
            return

        if category is None:
            current_category = self._get_ticket_category_channel(ctx.guild)
            if current_category:
                await ctx.send(
                    embed=create_info_embed(
                        "Ticket Category Channel",
                        f"Current ticket category: {current_category.mention}",
                    ),
                    ephemeral=True,
                )
            else:
                await ctx.send(
                    embed=create_info_embed(
                        "Ticket Category Channel",
                        "No ticket category channel is currently set. Tickets will be created in the panel channel's category.",
                    ),
                    ephemeral=True,
                )
            return

        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO ticket_category_channels (guild_id, category_id, set_by, set_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (ctx.guild.id, category.id, ctx.author.id),
            )
            conn.commit()
            conn.close()

            await ctx.send(
                embed=create_success_embed(
                    "Ticket Category Channel Set",
                    f"Tickets will now be created in {category.mention}",
                ),
                ephemeral=True,
            )
        except Exception as e:
            await ctx.send(
                embed=create_error_embed("Setup Error", str(e)), ephemeral=True
            )

    @ticket_group.command(name="category-disable")
    @commands.has_permissions(administrator=True)
    async def ticket_category_disable(self, ctx):
        """Remove the ticket category channel setting."""
        if not ctx.guild:
            await ctx.send(
                embed=create_error_embed(
                    "Error", "This command can only be used in servers."
                ),
                ephemeral=True,
            )
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM ticket_category_channels WHERE guild_id = ?", (ctx.guild.id,)
        )
        conn.commit()
        conn.close()

        await ctx.send(
            embed=create_success_embed(
                "Ticket Category Channel",
                "Ticket category setting removed. Tickets will be created in the panel channel's category.",
            ),
            ephemeral=True,
        )

    @ticket_group.command(name="list")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        status="Filter tickets by status (open, closed, all)",
        user="Filter tickets by user",
    )
    async def tickets_list(
        self, ctx, status: str = "open", user: Optional[discord.User] = None
    ):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        query = "SELECT ticket_id, ticket_channel_id, user_id, category, status, claimed_by, created_at FROM tickets"
        params = []

        if status != "all":
            query += " WHERE status = ?"
            params.append(status)

        if user:
            query += " AND user_id = ?" if params else " WHERE user_id = ?"
            params.append(user.id)

        query += " ORDER BY created_at DESC LIMIT 20"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            await ctx.send(
                embed=create_info_embed("No Tickets", f"No {status} tickets found."),
                ephemeral=True,
            )
            return

        embed = discord.Embed(title=f"{status.title()} Tickets", color=0x5865F2)

        for row in rows[:10]:
            (
                ticket_id,
                channel_id,
                user_id,
                category,
                ticket_status,
                claimed_by,
                created_at,
            ) = row
            embed.add_field(
                name=f"Ticket #{ticket_id} ({ticket_status})",
                value=(
                    f"**User:** <@{user_id}>\n"
                    f"**Category:** {str(category).title()}\n"
                    f"**Channel:** <#{channel_id}>\n"
                    f"**Created:** {created_at}"
                ),
                inline=False,
            )

        await ctx.send(embed=embed)

    @ticket_group.command(name="stats")
    @commands.has_permissions(manage_messages=True)
    async def ticket_stats(self, ctx):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tickets")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'open'")
        open_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'closed'")
        closed_count = cursor.fetchone()[0]
        conn.close()

        embed = discord.Embed(title="Ticket Statistics", color=0x5865F2)
        embed.add_field(name="Total", value=str(total), inline=True)
        embed.add_field(name="Open", value=str(open_count), inline=True)
        embed.add_field(name="Closed", value=str(closed_count), inline=True)
        await ctx.send(embed=embed)

    async def force_close_ticket(
        self,
        ctx,
        ticket_id: int,
        *,
        reason: str = "Force closed by staff",
        announce_in_channel: bool = True,
        announce_in_ticket: bool = True,
    ):
        """Force close a ticket by ID. Can be called internally or as a command."""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT ticket_channel_id, user_id, category FROM tickets WHERE ticket_id = ? AND status = "open"',
            (ticket_id,),
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            if hasattr(ctx, "send"):
                await ctx.send(
                    embed=create_error_embed(
                        "Ticket Not Found", f"No open ticket found with ID #{ticket_id}"
                    ),
                    ephemeral=True,
                )
            return

        channel_id, user_id, category = row

        cursor.execute(
            'UPDATE tickets SET status = "closed", closed_at = CURRENT_TIMESTAMP, close_reason = ?, delete_at = datetime(CURRENT_TIMESTAMP, "+24 hours"), deleted_at = NULL WHERE ticket_id = ?',
            (f"Force closed by {ctx.author}: {reason}", ticket_id),
        )
        conn.commit()
        conn.close()

        ticket_channel = None
        if ctx.guild and channel_id:
            ticket_channel = ctx.guild.get_channel(channel_id)
            if ticket_channel is None:
                try:
                    ticket_channel = await ctx.guild.fetch_channel(channel_id)
                except Exception:
                    ticket_channel = None

        if announce_in_channel and hasattr(ctx, "send"):
            embed = discord.Embed(
                title="Ticket Force Closed",
                description=(
                    f"Ticket #{ticket_id} has been force closed.\n"
                    "A transcript has been saved and the channel will remain available for 24 hours."
                ),
                color=0xFF0000,
            )
            embed.add_field(
                name="Ticket Owner", value=f"<@{user_id}> ({user_id})", inline=True
            )
            embed.add_field(name="Closed By", value=ctx.author.mention, inline=True)
            embed.add_field(name="Category", value=str(category).title(), inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            if ticket_channel:
                embed.add_field(
                    name="Channel", value=ticket_channel.mention, inline=True
                )
            await ctx.send(embed=embed)

        if ticket_channel and isinstance(ticket_channel, discord.TextChannel):
            if announce_in_ticket:
                await ticket_channel.send(
                    embed=discord.Embed(
                        title="Ticket Force Closed",
                        description=(
                            f"This ticket has been force closed by {ctx.author.mention}.\n"
                            "A transcript has been saved and this channel will stay visible for 24 hours before deletion."
                        ),
                        color=0xFF0000,
                    )
                )

            await self._generate_transcript(
                ticket_channel, int(ticket_id), save_to_log=True
            )
            self._schedule_ticket_channel_deletion(
                ticket_id=int(ticket_id),
                channel=ticket_channel,
                delete_at=datetime.now(timezone.utc) + timedelta(hours=24),
            )

            await self._log_ticket_action(
                "CLOSED",
                int(ticket_id),
                ticket_channel,
                ctx.author,
                category,
                f"Force closed by {ctx.author.name}: {reason} | Transcript saved; channel deletes in 24 hours",
            )

    @ticket_group.command(name="forceclose")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        ticket_id="The ID of the ticket to force close (from embed footer)",
        channel="The ticket channel to force close (alternative to ticket_id)",
        reason="Reason for force closing",
    )
    async def forceclose_command(
        self,
        ctx,
        ticket_id: Optional[int] = None,
        *,
        channel: Optional[discord.TextChannel] = None,
        reason: str = "Force closed by staff",
    ):
        """Force close a ticket by ID or channel.

        Provide either **ticket_id** (from the embed footer) or a **channel** mention/link.
        """
        if ticket_id is None and channel is None:
            await ctx.send(
                embed=create_error_embed(
                    "Missing Argument",
                    "You must provide either a **ticket ID** (from the embed footer) or a **ticket channel**.",
                ),
                ephemeral=True,
            )
            return

        # If channel was provided instead of ticket_id, look it up
        if ticket_id is None and channel is not None:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT ticket_id FROM tickets WHERE ticket_channel_id = ? AND status = "open"',
                (channel.id,),
            )
            row = cursor.fetchone()
            conn.close()
            if not row:
                await ctx.send(
                    embed=create_error_embed(
                        "Ticket Not Found",
                        f"No open ticket found for channel {channel.mention}.",
                    ),
                    ephemeral=True,
                )
                return
            ticket_id = row[0]

        await self.force_close_ticket(
            ctx,
            ticket_id,
            reason=reason,
            announce_in_channel=True,
            announce_in_ticket=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
