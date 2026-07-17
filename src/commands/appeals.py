import asyncio
import math
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal, Optional

import discord  # type: ignore[import-not-found]
from discord import app_commands  # type: ignore[import-not-found]
from discord.ext import commands  # type: ignore[import-not-found]

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import MODERATION_ROLE_ID
from utils.database import DATABASE_NAME, init_db
from utils.embeds import (
    create_error_embed as _base_create_error_embed,
)
from utils.embeds import (
    create_info_embed as _base_create_info_embed,
)
from utils.embeds import (
    create_success_embed as _base_create_success_embed,
)


def _appeals_footer_text(guild_name: str | None = None) -> str:
    return f"{guild_name} • Appeals" if guild_name else "Appeals"


APPEALS_PANEL_COLOR = 0x0A0A0A
APPEALS_ACCEPT_COLOR = 0x00FF00
APPEALS_REJECT_COLOR = 0xFF0000
APPEALS_TIMEOUT_END_COLOR = 0xF9F504


def create_error_embed(
    title: str, description: str, guild_name: str | None = None
) -> discord.Embed:
    embed = _base_create_error_embed(title, description)
    embed.color = APPEALS_PANEL_COLOR
    embed.set_footer(text=_appeals_footer_text(guild_name))
    embed.timestamp = datetime.now(timezone.utc)
    return embed


def create_success_embed(
    title: str, description: str, guild_name: str | None = None
) -> discord.Embed:
    embed = _base_create_success_embed(title, description)
    embed.color = APPEALS_PANEL_COLOR
    embed.set_footer(text=_appeals_footer_text(guild_name))
    embed.timestamp = datetime.now(timezone.utc)
    return embed


def create_info_embed(
    title: str, description: str, guild_name: str | None = None
) -> discord.Embed:
    embed = _base_create_info_embed(title, description)
    embed.color = APPEALS_PANEL_COLOR
    embed.set_footer(text=_appeals_footer_text(guild_name))
    embed.timestamp = datetime.now(timezone.utc)
    return embed


async def _safe_ctx_send(
    ctx: commands.Context,
    *,
    content: str | None = None,
    embed: discord.Embed | None = None,
    view: discord.ui.View | None = None,
    ephemeral: bool = False,
):
    send_kwargs: dict[str, Any] = {}
    if content is not None:
        send_kwargs["content"] = content
    if embed is not None:
        send_kwargs["embed"] = embed
    if view is not None:
        send_kwargs["view"] = view

    interaction = getattr(ctx, "interaction", None)
    if ephemeral and interaction is not None:
        try:
            return await interaction.response.send_message(
                **send_kwargs, ephemeral=True
            )
        except discord.InteractionResponded:
            return await interaction.followup.send(**send_kwargs, ephemeral=True)
    return await ctx.send(**send_kwargs)


def _format_relative(dt: Optional[datetime]) -> str:
    if dt is None:
        return "Unknown"
    return f"<t:{int(dt.timestamp())}:R> (<t:{int(dt.timestamp())}:F>)"


def _truncate(text: str, limit: int = 900) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _clean_reason(text: Optional[str]) -> str:
    if not text:
        return "No reason provided"
    text = str(text).strip()
    return text or "No reason provided"


@dataclass(slots=True)
class AppealRecord:
    appeal_id: int
    guild_id: int
    guild_name: str
    user_id: int
    username: str
    punishment_type: str
    punishment_reason: str
    timeout_issued_at: Optional[datetime]
    timeout_expires_at: Optional[datetime]
    appeal_reason: str
    should_remove: str
    appeal_learned: str
    appeal_extra: Optional[str]
    submitted_at: datetime
    status: str = "pending"
    review_channel_id: Optional[int] = None
    review_message_id: Optional[int] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_reason: Optional[str] = None
    jump_url: Optional[str] = None


class AppealSubmissionDashboard(discord.ui.LayoutView):
    """Components V2 DM card shown to a punished user."""

    def __init__(
        self,
        cog: "Appeals",
        record: AppealRecord,
        *,
        can_submit: bool,
        disabled_reason: Optional[str] = None,
    ):
        super().__init__(timeout=None)
        self.cog = cog
        self.record = record
        self.can_submit = can_submit
        self.disabled_reason = disabled_reason
        self._render()

    def _icon_url(self) -> str:
        guild = self.cog.bot.get_guild(self.record.guild_id)
        if guild and guild.icon:
            return guild.icon.url
        if self.cog.bot.user:
            return self.cog.bot.user.display_avatar.url
        return "https://cdn.discordapp.com/embed/avatars/0.png"

    def _render(self) -> None:
        self.clear_items()

        container = discord.ui.Container(
            accent_color=discord.Color(APPEALS_PANEL_COLOR)
        )
        container.add_item(
            discord.ui.TextDisplay(
                "## Moderation Appeal System\n"
                f"You are currently timed out from **{self.record.guild_name}**.\n"
                "We understand mistakes happen.\n"
                "If you believe your timeout was unfair or you would like another chance, "
                "you may submit an appeal."
            )
        )
        container.add_item(discord.ui.Separator())
        container.add_item(
            discord.ui.Section(
                discord.ui.TextDisplay(
                    "### Current Punishment\n"
                    f"• `{self.record.punishment_type.title()}`\n"
                    f"**Reason**\n"
                    f"• {self.record.punishment_reason}\n"
                    f"**Issued**\n"
                    f"• {_format_relative(self.record.timeout_issued_at)}\n"
                    f"**Expires**\n"
                    f"• {_format_relative(self.record.timeout_expires_at)}"
                ),
                accessory=discord.ui.Thumbnail(
                    self._icon_url(),
                    description=f"{self.record.guild_name} moderation appeal",
                ),
            )
        )
        container.add_item(discord.ui.Separator())
        container.add_item(
            discord.ui.TextDisplay(
                "### Appeal Requirements\n"
                "- Be honest\n"
                "- Explain what happened\n"
                "- Explain what you learned\n"
                "- Tell us why your punishment should be reduced or removed"
            )
        )
        container.add_item(discord.ui.Separator())
        container.add_item(
            discord.ui.TextDisplay("### Average Review Time\n5 minutes to 5 hours")
        )
        if self.disabled_reason:
            container.add_item(discord.ui.Separator())
            container.add_item(
                discord.ui.TextDisplay(f"**Status:** {self.disabled_reason}")
            )

        self.add_item(container)

        row = discord.ui.ActionRow()
        submit = discord.ui.Button(
            label="Submit Appeal",
            style=discord.ButtonStyle.secondary,
            disabled=not self.can_submit,
            custom_id=f"appeal:submit:{self.record.guild_id}:{self.record.user_id}",
        )
        submit.callback = self.submit_appeal  # type: ignore[assignment]
        row.add_item(submit)
        self.add_item(row)

    async def submit_appeal(self, interaction: discord.Interaction):
        if interaction.user.id != self.record.user_id:
            await interaction.response.send_message(
                "This appeal card is not for you.", ephemeral=True
            )
            return

        if not self.can_submit:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Appeal Unavailable",
                    self.disabled_reason or "This appeal is not available right now.",
                    guild_name=self.record.guild_name,
                ),
                ephemeral=True,
            )
            return

        modal = AppealSubmissionModal(
            self.cog, self.record, source_message=interaction.message
        )
        await interaction.response.send_modal(modal)


class AppealSubmissionModal(discord.ui.Modal):
    """Collects the four required timeout appeal answers."""

    def __init__(
        self,
        cog: "Appeals",
        record: AppealRecord,
        *,
        source_message: Optional[discord.Message] = None,
    ):
        super().__init__(title="Submit Appeal", timeout=300)
        self.cog = cog
        self.record = record
        self.source_message = source_message

        self.what_happened = discord.ui.TextInput(
            label="Why were you timed out?",
            placeholder="Explain the situation clearly and honestly.",
            style=discord.TextStyle.paragraph,
            max_length=1200,
            required=True,
        )
        self.should_remove = discord.ui.TextInput(
            label="Why should we remove the timeout?",
            placeholder="Tell us why the timeout should be reduced or removed.",
            style=discord.TextStyle.paragraph,
            max_length=1200,
            required=True,
        )
        self.extra = discord.ui.TextInput(
            label="Anything else?",
            placeholder="Optional additional context for the moderation team.",
            style=discord.TextStyle.paragraph,
            max_length=1200,
            required=False,
        )

        self.add_item(self.what_happened)
        self.add_item(self.should_remove)
        self.add_item(self.extra)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.process_appeal_submission(
            interaction,
            self.record,
            what_happened=self.what_happened.value,
            should_remove=self.should_remove.value,
            extra=self.extra.value if self.extra.value else None,
            source_message=self.source_message,
        )


class AppealDecisionConfirmView(discord.ui.View):
    """Small confirmation dialog for staff decisions."""

    def __init__(
        self,
        cog: "Appeals",
        record: AppealRecord,
        action: Literal["approved", "denied"],
    ):
        super().__init__(timeout=90)
        self.cog = cog
        self.record = record
        self.action = action

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.cog.finalize_appeal_decision(interaction, self.record, self.action)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="Decision cancelled.", view=None
        )


class AppealExtendTimeoutModal(discord.ui.Modal):
    """Extend a timeout from the review dashboard."""

    def __init__(self, cog: "Appeals", record: AppealRecord):
        super().__init__(title=f"Extend Timeout #{record.appeal_id}", timeout=300)
        self.cog = cog
        self.record = record

        self.duration = discord.ui.TextInput(
            label="Duration",
            placeholder="Examples: 1d 2h, 12h, 45m",
            max_length=30,
            required=True,
        )
        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="Explain why the timeout is being extended.",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True,
        )

        self.add_item(self.duration)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.extend_timeout_for_appeal(
            interaction,
            self.record,
            duration_text=self.duration.value,
            reason=self.reason.value,
        )


class AppealReviewDashboard(discord.ui.LayoutView):
    """Components V2 moderation dashboard for reviewing appeals."""

    def __init__(
        self,
        cog: "Appeals",
        record: AppealRecord,
        *,
        decision: Optional[str] = None,
        decision_reason: Optional[str] = None,
        moderator: Optional[discord.Member | discord.User] = None,
        alert_text: Optional[str] = None,
    ):
        super().__init__(timeout=None)
        self.cog = cog
        self.record = record
        self.decision = decision
        self.decision_reason = decision_reason
        self.moderator = moderator
        self.alert_text = alert_text
        self._render()

    def _render(self) -> None:
        self.clear_items()

        color_map = {
            None: discord.Color(APPEALS_PANEL_COLOR),
            "approved": discord.Color(APPEALS_ACCEPT_COLOR),
            "denied": discord.Color(APPEALS_REJECT_COLOR),
            "extended": discord.Color(APPEALS_PANEL_COLOR),
            "auto_resolved": discord.Color(APPEALS_PANEL_COLOR),
        }
        container = discord.ui.Container(
            accent_color=color_map.get(
                self.decision, discord.Color(APPEALS_PANEL_COLOR)
            )
        )
        avatar = self._user_avatar()

        status_line = "Pending review"
        if self.decision == "approved":
            status_line = "Approved"
        elif self.decision == "denied":
            status_line = "Rejected"
        elif self.decision == "extended":
            status_line = "Timeout extended"
        elif self.decision == "auto_resolved":
            status_line = "Auto-resolved"

        header = (
            "## Moderation Appeal Review Dashboard\n"
            f"### Appeal #{self.record.appeal_id}\n"
            f"Status: **{status_line}**"
        )
        container.add_item(discord.ui.TextDisplay(header))
        container.add_item(discord.ui.Separator())

        if self.alert_text:
            container.add_item(discord.ui.TextDisplay(f"**{self.alert_text}**"))
            container.add_item(discord.ui.Separator())

        meta_section = discord.ui.Section(
            discord.ui.TextDisplay(
                "### Appeal Snapshot\n"
                f"**User**\n• {self.record.username} (<@{self.record.user_id}>)\n"
                f"**User ID**\n• `{self.record.user_id}`\n"
                f"**Account Created**\n• {_format_relative(self._account_created)}\n"
                f"**Joined Server**\n• {_format_relative(self._joined_at)}\n"
                f"**Timeout Ends**\n• {_format_relative(self.record.timeout_expires_at)}\n"
                f"**Reason**\n• {_clean_reason(self.record.punishment_reason)}\n"
                f"**Appeal Time**\n• {_format_relative(self.record.submitted_at)}"
            ),
            accessory=discord.ui.Thumbnail(
                avatar,
                description=f"{self.record.username} profile",
            ),
        )
        container.add_item(meta_section)
        container.add_item(discord.ui.Separator())

        answers = discord.ui.TextDisplay(
            "### All Appeal Answers\n"
            f"**1. Why were you timed out?**\n{_truncate(self.record.appeal_reason, 1200)}\n"
            f"**2. Why should we remove the timeout?**\n{_truncate(self.record.should_remove, 1200)}\n"
            f"**3. Anything else?**\n{_truncate(self.record.appeal_extra or 'Not provided.', 1200)}"
        )
        container.add_item(answers)

        if self.decision_reason:
            container.add_item(discord.ui.Separator())
            container.add_item(
                discord.ui.TextDisplay(
                    f"### Decision Note\n{_truncate(self.decision_reason, 1200)}"
                )
            )

        self.add_item(container)

        row = discord.ui.ActionRow()
        for button in self._build_buttons():
            row.add_item(button)
        self.add_item(row)

    @property
    def _account_created(self) -> Optional[datetime]:
        member = self.cog._resolve_member(self.record.guild_id, self.record.user_id)
        if member and hasattr(member, "created_at"):
            return member.created_at
        return None

    @property
    def _joined_at(self) -> Optional[datetime]:
        member = self.cog._resolve_member(self.record.guild_id, self.record.user_id)
        if member and hasattr(member, "joined_at"):
            return member.joined_at
        return None

    def _user_avatar(self) -> str:
        member = self.cog._resolve_member(self.record.guild_id, self.record.user_id)
        if member and getattr(member, "display_avatar", None):
            return member.display_avatar.url
        if self.cog.bot.user:
            return self.cog.bot.user.display_avatar.url
        return "https://cdn.discordapp.com/embed/avatars/0.png"

    def _build_buttons(self) -> list[discord.ui.Button]:
        resolved = self.decision is not None
        buttons: list[discord.ui.Button] = []

        accept = discord.ui.Button(
            label="Accept",
            style=discord.ButtonStyle.success,
            disabled=resolved,
            custom_id=f"appeal:{self.record.appeal_id}:accept",
        )
        accept.callback = self.accept  # type: ignore[assignment]
        buttons.append(accept)

        reject = discord.ui.Button(
            label="Reject",
            style=discord.ButtonStyle.danger,
            disabled=resolved,
            custom_id=f"appeal:{self.record.appeal_id}:reject",
        )
        reject.callback = self.reject  # type: ignore[assignment]
        buttons.append(reject)

        extend = discord.ui.Button(
            label="Extend Timeout",
            style=discord.ButtonStyle.secondary,
            disabled=resolved,
            custom_id=f"appeal:{self.record.appeal_id}:extend",
        )
        extend.callback = self.extend_timeout  # type: ignore[assignment]
        buttons.append(extend)

        view_user = discord.ui.Button(
            label="View User",
            style=discord.ButtonStyle.secondary,
            disabled=False,
            custom_id=f"appeal:{self.record.appeal_id}:user",
        )
        view_user.callback = self.view_user  # type: ignore[assignment]
        buttons.append(view_user)

        view_history = discord.ui.Button(
            label="View History",
            style=discord.ButtonStyle.secondary,
            disabled=False,
            custom_id=f"appeal:{self.record.appeal_id}:history",
        )
        view_history.callback = self.view_history  # type: ignore[assignment]
        buttons.append(view_history)

        return buttons

    async def _must_be_moderator(self, interaction: discord.Interaction) -> bool:
        if not self.cog._is_moderator(interaction):
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Permission Denied",
                    "You don't have permission to review appeals.",
                    guild_name=interaction.guild.name if interaction.guild else None,
                ),
                ephemeral=True,
            )
            return False
        return True

    async def accept(self, interaction: discord.Interaction):
        if not await self._must_be_moderator(interaction):
            return
        if self.decision is not None:
            await interaction.response.send_message(
                "This appeal has already been processed.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            view=AppealDecisionConfirmView(self.cog, self.record, "approved"),
            ephemeral=True,
        )

    async def reject(self, interaction: discord.Interaction):
        if not await self._must_be_moderator(interaction):
            return
        if self.decision is not None:
            await interaction.response.send_message(
                "This appeal has already been processed.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            view=AppealDecisionConfirmView(self.cog, self.record, "denied"),
            ephemeral=True,
        )

    async def extend_timeout(self, interaction: discord.Interaction):
        if not await self._must_be_moderator(interaction):
            return
        if self.decision is not None:
            await interaction.response.send_message(
                "This appeal has already been processed.", ephemeral=True
            )
            return
        await interaction.response.send_modal(
            AppealExtendTimeoutModal(self.cog, self.record)
        )

    async def view_user(self, interaction: discord.Interaction):
        if not await self._must_be_moderator(interaction):
            return
        dashboard = await self.cog.build_user_profile_dashboard(self.record)
        await interaction.response.send_message(view=dashboard, ephemeral=True)

    async def view_history(self, interaction: discord.Interaction):
        if not await self._must_be_moderator(interaction):
            return
        dashboard = await self.cog.build_history_dashboard(self.record)
        await interaction.response.send_message(view=dashboard, ephemeral=True)


class Appeals(commands.Cog):
    """Unban appeal system with auto-DM for moderation actions"""

    def __init__(self, bot):
        self.bot = bot
        init_db()
        self._timeout_dedupe_cache = {}  # {(user_id, guild_id, action): timestamp} - prevents double DM
        self._ban_event_handled = (
            set()
        )  # Track recently handled ban events to prevent duplicates
        self._ensure_appeal_schema()
        self.bot.loop.create_task(self._restore_review_dashboards())

    def _ensure_appeal_schema(self):
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            for column_sql in (
                "ALTER TABLE unban_requests ADD COLUMN punishment_type TEXT",
                "ALTER TABLE unban_requests ADD COLUMN punishment_reason TEXT",
                "ALTER TABLE unban_requests ADD COLUMN appeal_reason TEXT",
                "ALTER TABLE unban_requests ADD COLUMN should_remove TEXT",
                "ALTER TABLE unban_requests ADD COLUMN appeal_learned TEXT",
                "ALTER TABLE unban_requests ADD COLUMN appeal_extra TEXT",
                "ALTER TABLE unban_requests ADD COLUMN timeout_issued_at DATETIME",
                "ALTER TABLE unban_requests ADD COLUMN timeout_expires_at DATETIME",
                "ALTER TABLE unban_requests ADD COLUMN appeal_message_id INTEGER",
                "ALTER TABLE unban_requests ADD COLUMN review_channel_id INTEGER",
                "ALTER TABLE unban_requests ADD COLUMN review_message_id INTEGER",
                "ALTER TABLE unban_requests ADD COLUMN reviewed_by INTEGER",
                "ALTER TABLE unban_requests ADD COLUMN reviewed_at DATETIME",
                "ALTER TABLE unban_requests ADD COLUMN review_reason TEXT",
                "ALTER TABLE unban_requests ADD COLUMN jump_url TEXT",
            ):
                try:
                    cursor.execute(column_sql)
                except sqlite3.OperationalError:
                    pass

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS appeal_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appeal_id INTEGER NOT NULL,
                    guild_id INTEGER,
                    action TEXT NOT NULL,
                    actor_id INTEGER,
                    reason TEXT,
                    jump_url TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        finally:
            try:
                conn.close()
            except Exception:
                pass

    async def _restore_review_dashboards(self):
        await self.bot.wait_until_ready()
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, guild_id, reason, status, timestamp, punishment_type, punishment_reason,
                       appeal_reason, should_remove, appeal_learned, appeal_extra, timeout_issued_at,
                       timeout_expires_at, appeal_message_id, review_channel_id, review_message_id,
                       reviewed_by, reviewed_at, review_reason, jump_url
                FROM unban_requests
                WHERE status = 'pending' AND review_channel_id IS NOT NULL AND review_message_id IS NOT NULL
                """
            )
            rows = cursor.fetchall()
            conn.close()
            restored = 0
            for row in rows:
                record = self._build_appeal_record_from_row(row)
                channel = self.bot.get_channel(record.review_channel_id)
                if channel is None:
                    continue
                try:
                    await channel.fetch_message(record.review_message_id)
                    self.bot.add_view(
                        AppealReviewDashboard(self, record),
                        message_id=record.review_message_id,
                    )
                    restored += 1
                except Exception:
                    continue
            if restored:
                print(f"[Appeals] Restored {restored} appeal review dashboards")
        except Exception as e:
            print(f"[Appeals] Error restoring appeal review dashboards: {e}")

    def _resolve_member(self, guild_id: int, user_id: int) -> Optional[discord.Member]:
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return None
        member = guild.get_member(user_id)
        return member if isinstance(member, discord.Member) else None

    def _is_moderator(self, interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            return False
        allowed = {1403059755001577543}
        if interaction.guild:
            role = interaction.guild.get_role(MODERATION_ROLE_ID)
            if role:
                allowed.add(role.id)
        return (
            any(role.id in allowed for role in interaction.user.roles)
            or interaction.user.guild_permissions.manage_messages
            or interaction.user.guild_permissions.administrator
        )

    def _parse_timestamp(self, value: Any) -> Optional[datetime]:
        if not value:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
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

    def _format_roles(self, member: Optional[discord.Member]) -> str:
        if not member:
            return "Unavailable"
        roles = [role.mention for role in member.roles if not role.is_default()]
        if not roles:
            return "None"
        return ", ".join(roles[:8]) + ("..." if len(roles) > 8 else "")

    def _parse_duration(self, text: str) -> Optional[timedelta]:
        text = text.strip().lower().replace(",", " ")
        match = re.fullmatch(
            r"(?:(\d+)\s*d)?\s*(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?",
            text,
        )
        if not match:
            return None
        days, hours, minutes, seconds = (
            int(part) if part else 0 for part in match.groups()
        )
        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        return delta if delta.total_seconds() > 0 else None

    def _build_appeal_record_from_row(self, row: tuple) -> AppealRecord:
        (
            appeal_id,
            user_id,
            guild_id,
            reason,
            status,
            timestamp,
            punishment_type,
            punishment_reason,
            appeal_reason,
            should_remove,
            appeal_learned,
            appeal_extra,
            timeout_issued_at,
            timeout_expires_at,
            appeal_message_id,
            review_channel_id,
            review_message_id,
            reviewed_by,
            reviewed_at,
            review_reason,
            jump_url,
        ) = row
        guild = self.bot.get_guild(guild_id) if guild_id else None
        member = self._resolve_member(guild_id, user_id) if guild_id else None
        return AppealRecord(
            appeal_id=appeal_id,
            guild_id=guild_id,
            guild_name=guild.name if guild else "the server",
            user_id=user_id,
            username=str(member) if member else f"User {user_id}",
            punishment_type=punishment_type or "timeout",
            punishment_reason=punishment_reason or "No reason provided",
            timeout_issued_at=self._parse_timestamp(timeout_issued_at),
            timeout_expires_at=self._parse_timestamp(timeout_expires_at),
            appeal_reason=appeal_reason or "No answer provided.",
            should_remove=should_remove or "No answer provided.",
            appeal_learned=appeal_learned or "No answer provided.",
            appeal_extra=appeal_extra,
            submitted_at=self._parse_timestamp(timestamp) or datetime.now(timezone.utc),
            status=status or "pending",
            review_channel_id=review_channel_id,
            review_message_id=review_message_id,
            reviewed_by=reviewed_by,
            reviewed_at=self._parse_timestamp(reviewed_at),
            review_reason=review_reason,
            jump_url=jump_url,
        )

    async def _log_appeal_event(
        self,
        event_type: str,
        record: AppealRecord,
        *,
        moderator: Optional[discord.Member | discord.User] = None,
        reason: Optional[str] = None,
        jump_url: Optional[str] = None,
    ) -> None:
        logging_cog = self.bot.get_cog("LoggingCog")
        if not logging_cog or not hasattr(logging_cog, "log_event"):
            return
        details = reason or record.review_reason or record.punishment_reason
        await logging_cog.log_event(
            event_type,
            user_id=record.user_id,
            guild_id=record.guild_id,
            moderator_id=getattr(moderator, "id", None),
            details=details,
            title=f"Appeal {event_type.replace('APPEAL_', '').title()}",
            description=details,
            fields=[
                {"name": "Appeal ID", "value": f"#{record.appeal_id}", "inline": True},
                {
                    "name": "User",
                    "value": f"<@{record.user_id}> ({record.user_id})",
                    "inline": True,
                },
                {
                    "name": "Decision",
                    "value": event_type.replace("APPEAL_", "").title(),
                    "inline": True,
                },
                {"name": "Reason", "value": _truncate(details, 900), "inline": False},
                {
                    "name": "Timestamp",
                    "value": f"<t:{int(datetime.now(timezone.utc).timestamp())}:F>",
                    "inline": True,
                },
                {
                    "name": "Jump URL",
                    "value": jump_url or record.jump_url or "Unavailable",
                    "inline": False,
                },
            ],
            color={
                "APPEAL_SUBMITTED": APPEALS_PANEL_COLOR,
                "APPEAL_APPROVED": APPEALS_ACCEPT_COLOR,
                "APPEAL_DENIED": APPEALS_REJECT_COLOR,
                "APPEAL_EXTENDED": APPEALS_PANEL_COLOR,
            }.get(event_type, APPEALS_PANEL_COLOR),
            jump_url=jump_url or record.jump_url,
        )

    async def _get_timeout_history(
        self, user_id: int, guild_id: int
    ) -> list[dict[str, Any]]:
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, action, reason
                FROM moderation_log
                WHERE user_id = ? AND guild_id = ? AND (action LIKE 'Timeout%' OR action LIKE 'timeout%')
                ORDER BY timestamp DESC LIMIT 10
                """,
                (user_id, guild_id),
            )
            rows = cursor.fetchall()
            conn.close()
            return [
                {
                    "timestamp": row[0],
                    "action": row[1],
                    "reason": row[2] or "No reason provided",
                }
                for row in rows
            ]
        except Exception:
            return []

    async def _get_appeal_history(
        self, user_id: int, guild_id: int
    ) -> list[dict[str, Any]]:
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, status, timestamp
                FROM unban_requests
                WHERE user_id = ? AND guild_id = ?
                ORDER BY timestamp DESC LIMIT 10
                """,
                (user_id, guild_id),
            )
            rows = cursor.fetchall()
            conn.close()
            return [
                {"id": row[0], "status": row[1], "timestamp": row[2]} for row in rows
            ]
        except Exception:
            return []

    async def _get_notes_history(
        self, user_id: int, guild_id: int
    ) -> list[dict[str, Any]]:
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, action, reason
                FROM moderation_log
                WHERE user_id = ? AND guild_id = ? AND action LIKE '%note%'
                ORDER BY timestamp DESC LIMIT 10
                """,
                (user_id, guild_id),
            )
            rows = cursor.fetchall()
            conn.close()
            return [
                {
                    "timestamp": row[0],
                    "action": row[1],
                    "details": row[2] or "No details",
                }
                for row in rows
            ]
        except Exception:
            return []

    async def _get_message_count(self, guild_id: int, user_id: int) -> str:
        return "Unavailable"

    async def build_user_profile_dashboard(
        self, record: AppealRecord
    ) -> discord.ui.LayoutView:
        member = self._resolve_member(record.guild_id, record.user_id)
        try:
            from utils.json_store import get_warnings

            warnings = await get_warnings(record.user_id)
        except Exception:
            warnings = []
        timeouts = await self._get_timeout_history(record.user_id, record.guild_id)
        appeals = await self._get_appeal_history(record.user_id, record.guild_id)

        view = discord.ui.LayoutView(timeout=120)
        container = discord.ui.Container(
            accent_color=discord.Color(APPEALS_PANEL_COLOR)
        )
        container.add_item(
            discord.ui.TextDisplay(
                "## User Profile\n"
                f"**User**: {record.username}\n"
                f"**User ID**: `{record.user_id}`\n"
                f"**Roles**: {self._format_roles(member)}\n"
                f"**Joined Server**: {_format_relative(member.joined_at if member and member.joined_at else None)}\n"
                f"**Account Created**: {_format_relative(member.created_at if member and member.created_at else None)}\n"
                f"**Warnings**: {len(warnings)}\n"
                f"**Timeouts**: {len(timeouts)}\n"
                f"**Appeals**: {len(appeals)}\n"
                f"**Message Count**: Unavailable"
            )
        )
        view.add_item(container)
        return view

    async def build_history_dashboard(
        self, record: AppealRecord
    ) -> discord.ui.LayoutView:
        try:
            from utils.json_store import get_warnings

            warnings = await get_warnings(record.user_id)
        except Exception:
            warnings = []
        timeouts = await self._get_timeout_history(record.user_id, record.guild_id)
        appeals = await self._get_appeal_history(record.user_id, record.guild_id)
        notes = await self._get_notes_history(record.user_id, record.guild_id)

        view = discord.ui.LayoutView(timeout=120)
        container = discord.ui.Container(
            accent_color=discord.Color(APPEALS_PANEL_COLOR)
        )
        container.add_item(
            discord.ui.TextDisplay(
                "## History\n"
                f"**Warnings**: {len(warnings)}\n"
                f"**Timeouts**: {len(timeouts)}\n"
                f"**Appeals**: {len(appeals)}\n"
                f"**Notes**: {len(notes)}"
            )
        )
        if warnings:
            warning_lines = "\n".join(
                f"• {item.get('ts', 'Unknown')} - {item.get('reason', 'No reason')}"
                for item in warnings[:5]
            )
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(f"### Warnings\n{warning_lines}"))
        if timeouts:
            timeout_lines = "\n".join(
                f"• {item['timestamp']} - {item['reason']}" for item in timeouts[:5]
            )
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(f"### Timeouts\n{timeout_lines}"))
        if appeals:
            appeal_lines = "\n".join(
                f"• #{item['id']} - {item['status']} ({item['timestamp']})"
                for item in appeals[:5]
            )
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(f"### Appeals\n{appeal_lines}"))
        if notes:
            note_lines = "\n".join(
                f"• {item['timestamp']} - {item['details']}" for item in notes[:5]
            )
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(f"### Notes\n{note_lines}"))
        view.add_item(container)
        return view

    async def process_appeal_submission(
        self,
        interaction: discord.Interaction,
        record: AppealRecord,
        *,
        what_happened: str,
        should_remove: str,
        extra: Optional[str] = None,
        source_message: Optional[discord.Message] = None,
    ) -> None:
        if interaction.user.id != record.user_id:
            await interaction.response.send_message(
                "This appeal form is not for you.", ephemeral=True
            )
            return

        existing = await self._get_pending_appeal(record.user_id, record.guild_id)
        if existing and existing.appeal_id != record.appeal_id:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Appeal Already Submitted",
                    f"You already have a pending appeal (#{existing.appeal_id}).",
                    guild_name=record.guild_name,
                ),
                ephemeral=True,
            )
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO unban_requests (
                user_id, guild_id, reason, status, punishment_type, punishment_reason,
                appeal_reason, should_remove, appeal_learned, appeal_extra,
                timeout_issued_at, timeout_expires_at, jump_url
            ) VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.user_id,
                record.guild_id,
                "\n".join(
                    [
                        f"**Why I was timed out:** {what_happened}",
                        f"**Why it should be removed:** {should_remove}",
                        f"**Anything else:** {extra or 'Not provided.'}",
                    ]
                ),
                record.punishment_type,
                record.punishment_reason,
                what_happened,
                should_remove,
                None,
                extra,
                record.timeout_issued_at.strftime("%Y-%m-%d %H:%M:%S")
                if record.timeout_issued_at
                else None,
                record.timeout_expires_at.strftime("%Y-%m-%d %H:%M:%S")
                if record.timeout_expires_at
                else None,
                interaction.message.jump_url if interaction.message else None,
            ),
        )
        appeal_id = cursor.lastrowid
        conn.commit()
        conn.close()

        updated_record = await self._fetch_appeal_record(appeal_id)
        if updated_record is None:
            await interaction.response.send_message(
                "Failed to persist the appeal.", ephemeral=True
            )
            return

        await self._log_appeal_event(
            "APPEAL_SUBMITTED",
            updated_record,
            moderator=None,
            reason="User submitted a timeout appeal.",
            jump_url=interaction.message.jump_url if interaction.message else None,
        )

        review_view = AppealReviewDashboard(self, updated_record)
        review_channel = await self._resolve_review_channel(updated_record.guild_id)
        if review_channel:
            # Send @here mention first as a separate message (Components V2 views
            # cannot be sent with a content field in the same message)
            await review_channel.send(
                content="@here",
                allowed_mentions=discord.AllowedMentions(everyone=True),
            )
            staff_message = await review_channel.send(view=review_view)
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE unban_requests SET review_channel_id = ?, review_message_id = ?, jump_url = ? WHERE id = ?",
                (
                    review_channel.id,
                    staff_message.id,
                    staff_message.jump_url,
                    updated_record.appeal_id,
                ),
            )
            conn.commit()
            conn.close()

        await interaction.response.send_message(
            embed=create_success_embed(
                "Appeal Submitted",
                "Your appeal has been sent to the moderation team.",
                guild_name=record.guild_name,
            ),
            ephemeral=True,
        )

        disabled_view = AppealSubmissionDashboard(
            self,
            updated_record,
            can_submit=False,
            disabled_reason="Appeal already submitted and awaiting review.",
        )
        try:
            target_message = source_message or interaction.message
            if target_message is not None:
                await target_message.edit(view=disabled_view)
        except Exception:
            pass

    async def finalize_appeal_decision(
        self,
        interaction: discord.Interaction,
        record: AppealRecord,
        decision: Literal["approved", "denied"],
    ) -> None:
        if not self._is_moderator(interaction):
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Permission Denied", "You don't have permission to review appeals."
                ),
                ephemeral=True,
            )
            return

        updated_record = await self._fetch_appeal_record(record.appeal_id)
        if updated_record is None or updated_record.status != "pending":
            await interaction.response.send_message(
                "This appeal has already been processed.", ephemeral=True
            )
            return

        if decision == "approved":
            member = self._resolve_member(record.guild_id, record.user_id)
            if member is None:
                await interaction.response.send_message(
                    embed=create_error_embed(
                        "Member Not Found",
                        "The user is no longer in the server, so the timeout cannot be removed.",
                    ),
                    ephemeral=True,
                )
                return
            try:
                await member.timeout(
                    None,
                    reason=f"Appeal #{record.appeal_id} approved by {interaction.user}",
                )
            except Exception as e:
                await interaction.response.send_message(
                    embed=create_error_embed(
                        "Action Failed", f"Could not clear timeout: {e}"
                    ),
                    ephemeral=True,
                )
                return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE unban_requests
            SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP, review_reason = ?, jump_url = ?
            WHERE id = ?
            """,
            (
                decision,
                interaction.user.id,
                f"{decision.title()} by {interaction.user}",
                interaction.message.jump_url if interaction.message else None,
                record.appeal_id,
            ),
        )
        conn.commit()
        conn.close()

        decision_reason = f"{decision.title()} by {interaction.user.mention}"
        resolved_view = AppealReviewDashboard(
            self,
            updated_record,
            decision=decision,
            decision_reason=decision_reason,
            moderator=interaction.user,
        )

        if updated_record.review_channel_id and updated_record.review_message_id:
            try:
                channel = self.bot.get_channel(updated_record.review_channel_id)
                if channel is None:
                    channel = await self.bot.fetch_channel(
                        updated_record.review_channel_id
                    )
                if channel:
                    message = await channel.fetch_message(
                        updated_record.review_message_id
                    )
                    await message.edit(view=resolved_view)
            except Exception:
                pass

        decision_color = (
            APPEALS_ACCEPT_COLOR if decision == "approved" else APPEALS_REJECT_COLOR
        )
        decision_embed = discord.Embed(
            title=f"Appeal {decision.title()}",
            description=f"Appeal #{record.appeal_id} has been {decision}.",
            color=decision_color,
            timestamp=datetime.now(timezone.utc),
        )
        decision_embed.set_footer(text=_appeals_footer_text(record.guild_name))
        await interaction.response.send_message(
            embed=decision_embed,
            ephemeral=True,
        )

        await self._log_appeal_event(
            f"APPEAL_{decision.upper()}",
            updated_record,
            moderator=interaction.user,
            reason=decision_reason,
            jump_url=updated_record.jump_url,
        )

        await self._dm_decision(updated_record, decision, interaction.user)

    async def extend_timeout_for_appeal(
        self,
        interaction: discord.Interaction,
        record: AppealRecord,
        *,
        duration_text: str,
        reason: str,
    ) -> None:
        if not self._is_moderator(interaction):
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Permission Denied", "You don't have permission to extend timeouts."
                ),
                ephemeral=True,
            )
            return

        delta = self._parse_duration(duration_text)
        if delta is None:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Invalid Duration", "Use a format like `1d 2h`, `12h`, or `45m`."
                ),
                ephemeral=True,
            )
            return

        member = self._resolve_member(record.guild_id, record.user_id)
        if not member:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Member Not Found", "The user is no longer in the server."
                ),
                ephemeral=True,
            )
            return

        new_until = datetime.now(timezone.utc) + delta
        try:
            await member.timeout(new_until, reason=reason)
        except Exception as e:
            await interaction.response.send_message(
                embed=create_error_embed("Timeout Failed", str(e)),
                ephemeral=True,
            )
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE unban_requests SET timeout_expires_at = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP, review_reason = ? WHERE id = ?",
            (
                new_until.strftime("%Y-%m-%d %H:%M:%S"),
                interaction.user.id,
                reason,
                record.appeal_id,
            ),
        )
        conn.commit()
        conn.close()

        refreshed = await self._fetch_appeal_record(record.appeal_id)
        await self._log_appeal_event(
            "APPEAL_EXTENDED",
            refreshed or record,
            moderator=interaction.user,
            reason=reason,
            jump_url=(refreshed.jump_url if refreshed else record.jump_url),
        )
        await self._dm_extended_timeout(
            refreshed or record, interaction.user, new_until, reason
        )
        await interaction.response.send_message(
            embed=create_success_embed(
                "Timeout Extended",
                f"The timeout for {record.username} has been extended until {_format_relative(new_until)}.",
                guild_name=record.guild_name,
            ),
            ephemeral=True,
        )
        if refreshed and refreshed.review_channel_id and refreshed.review_message_id:
            try:
                channel = self.bot.get_channel(refreshed.review_channel_id)
                if channel is None:
                    channel = await self.bot.fetch_channel(refreshed.review_channel_id)
                if channel:
                    message = await channel.fetch_message(refreshed.review_message_id)
                    await message.edit(
                        view=AppealReviewDashboard(
                            self,
                            refreshed,
                            decision="extended",
                            decision_reason=reason,
                            moderator=interaction.user,
                            alert_text="Timeout extension applied.",
                        )
                    )
            except Exception:
                pass

    async def _get_pending_appeal(
        self, user_id: int, guild_id: int
    ) -> Optional[AppealRecord]:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, user_id, guild_id, reason, status, timestamp, punishment_type, punishment_reason,
                   appeal_reason, should_remove, appeal_learned, appeal_extra, timeout_issued_at,
                   timeout_expires_at, appeal_message_id, review_channel_id, review_message_id,
                   reviewed_by, reviewed_at, review_reason, jump_url
            FROM unban_requests
            WHERE user_id = ? AND guild_id = ? AND status = 'pending'
            ORDER BY timestamp DESC LIMIT 1
            """,
            (user_id, guild_id),
        )
        row = cursor.fetchone()
        conn.close()
        return self._build_appeal_record_from_row(row) if row else None

    async def _fetch_appeal_record(self, appeal_id: int) -> Optional[AppealRecord]:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, user_id, guild_id, reason, status, timestamp, punishment_type, punishment_reason,
                   appeal_reason, should_remove, appeal_learned, appeal_extra, timeout_issued_at,
                   timeout_expires_at, appeal_message_id, review_channel_id, review_message_id,
                   reviewed_by, reviewed_at, review_reason, jump_url
            FROM unban_requests
            WHERE id = ?
            """,
            (appeal_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return self._build_appeal_record_from_row(row) if row else None

    async def _resolve_review_channel(
        self, guild_id: int
    ) -> Optional[discord.TextChannel]:
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return None
        for channel in guild.text_channels:
            name = channel.name.lower()
            if "appeal" in name or "mod" in name or "staff" in name or "log" in name:
                return channel
        return guild.text_channels[0] if guild.text_channels else None

    async def _dm_decision(
        self,
        record: AppealRecord,
        decision: Literal["approved", "denied"],
        moderator: discord.Member | discord.User,
    ) -> None:
        try:
            user = await self.bot.fetch_user(record.user_id)
        except Exception:
            return
        guild = self.bot.get_guild(record.guild_id)
        if decision == "approved":
            text = (
                "## Your appeal has been reviewed and approved.\n"
                f"Your timeout in **{record.guild_name}** has been removed."
            )
            accent = discord.Color(APPEALS_ACCEPT_COLOR)
        else:
            text = (
                "## Your appeal has been reviewed and denied.\n"
                f"Your timeout in **{record.guild_name}** remains in place."
            )
            accent = discord.Color(APPEALS_REJECT_COLOR)

        view = discord.ui.LayoutView(timeout=None)
        container = discord.ui.Container(accent_color=accent)
        container.add_item(discord.ui.TextDisplay(text))
        if guild and guild.icon:
            container.add_item(discord.ui.Separator())
            container.add_item(
                discord.ui.TextDisplay(
                    f"**Reviewed By:** {moderator}\n**Appeal ID:** #{record.appeal_id}\n**Reason:** {record.review_reason or 'Reviewed by staff'}"
                )
            )
        view.add_item(container)
        try:
            await user.send(view=view)
        except Exception:
            pass

    async def _dm_extended_timeout(
        self,
        record: AppealRecord,
        moderator: discord.Member | discord.User,
        new_until: datetime,
        reason: str,
    ) -> None:
        try:
            user = await self.bot.fetch_user(record.user_id)
        except Exception:
            return
        view = discord.ui.LayoutView(timeout=None)
        container = discord.ui.Container(
            accent_color=discord.Color(APPEALS_PANEL_COLOR)
        )
        container.add_item(
            discord.ui.TextDisplay(
                "## Timeout Extended\n"
                f"Your timeout in **{record.guild_name}** has been extended until {_format_relative(new_until)}.\n"
                f"**Reason:** {reason}\n"
                f"**Reviewed By:** {moderator}"
            )
        )
        view.add_item(container)
        try:
            await user.send(view=view)
        except Exception:
            pass

    async def _disable_appeal_buttons_by_id(self, appeal_id: int, guild_id: int):
        """Find and disable appeal buttons in messages for a specific appeal ID"""
        try:
            record = await self._fetch_appeal_record(appeal_id)
            if not record:
                return
            if record.review_channel_id and record.review_message_id:
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    return
                channel = guild.get_channel(record.review_channel_id)
                if channel is None:
                    channel = await guild.fetch_channel(record.review_channel_id)
                if channel:
                    message = await channel.fetch_message(record.review_message_id)
                    await message.edit(
                        view=AppealReviewDashboard(
                            self,
                            record,
                            decision="auto_resolved",
                            decision_reason="The timeout expired or was removed while this appeal was pending.",
                            alert_text="This appeal has been automatically resolved.",
                        )
                    )
                    print(
                        f"[Appeals] Disabled buttons for appeal #{appeal_id} in review dashboard"
                    )
                    return
        except Exception as e:
            print(f"[Appeals] Error disabling buttons for appeal #{appeal_id}: {e}")

    async def _log_punishment_expiry(
        self, appeal_id: int, user_id: int, guild_id: int, status_message: str
    ):
        """Log punishment expiry to appeals channel"""
        try:
            print(
                f"[Appeals] Starting to log punishment expiry for appeal #{appeal_id}"
            )

            guild = self.bot.get_guild(guild_id)
            if not guild:
                print(
                    f"[Appeals] Could not find guild {guild_id} for logging appeal #{appeal_id}"
                )
                return

            # Find appeals channel
            appeals_channels = [
                channel
                for channel in guild.text_channels
                if "appeal" in channel.name.lower()
            ]
            if not appeals_channels:
                print(
                    f"[Appeals] No appeals channel found in {guild.name} for logging punishment expiry"
                )
                # Try to find any channel with "appeal" in the name or description
                all_channels = [ch.name for ch in guild.text_channels]
                print(
                    f"[Appeals] Available channels in {guild.name}: {', '.join(all_channels)}"
                )
                return

            print(
                f"[Appeals] Found appeals channel: {appeals_channels[0].name} in {guild.name}"
            )

            user = self.bot.get_user(user_id) or f"<@{user_id}>"

            # Determine the type of expiry for better messaging
            is_natural_expiry = "naturally expired" in status_message.lower()
            is_ban_removal = "no longer banned" in status_message.lower()

            if is_natural_expiry:
                title = "Appeal Auto-Resolved - Timeout Naturally Expired"
                color = APPEALS_TIMEOUT_END_COLOR
                description = f"Appeal #{appeal_id} has been automatically resolved because the timeout naturally expired."
            elif is_ban_removal:
                title = "Appeal Auto-Resolved - Ban Removed"
                color = APPEALS_TIMEOUT_END_COLOR
                description = f"Appeal #{appeal_id} has been automatically resolved because the ban was removed."
            else:
                title = "Appeal Auto-Resolved - Punishment Invalid"
                color = APPEALS_TIMEOUT_END_COLOR
                description = f"Appeal #{appeal_id} has been automatically resolved because the punishment is no longer valid."

            print(f"[Appeals] Creating log embed with title: {title}")

            # Create log embed
            log_embed = discord.Embed(
                title=title,
                description=description,
                color=color,
                timestamp=datetime.now(timezone.utc),
            )

            log_embed.add_field(name="User", value=str(user), inline=True)

            log_embed.add_field(name="Appeal ID", value=f"#{appeal_id}", inline=True)

            log_embed.add_field(name="Details", value=status_message, inline=False)

            log_embed.add_field(
                name="Action",
                value="Appeal buttons have been automatically disabled",
                inline=False,
            )

            log_embed.set_footer(
                text=f"Guild: {guild.name}",
                icon_url=guild.icon.url if guild.icon else None,
            )

            # Send to appeals channel
            print(f"[Appeals] Sending log embed to {appeals_channels[0].name}")
            await appeals_channels[0].send(embed=log_embed)
            print(
                f"[Appeals] Successfully logged punishment expiry for appeal #{appeal_id} to {appeals_channels[0].name}"
            )

        except Exception as e:
            print(
                f"[Appeals] Error logging punishment expiry for appeal #{appeal_id}: {e}"
            )
            import traceback

            traceback.print_exc()

    async def _send_appeal_form(
        self,
        user: discord.User | discord.Member,
        guild: discord.Guild,
        action_type: str,
        reason: str | None = None,
        *,
        issued_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
    ):
        """Send the timeout appeal dashboard to the user."""
        dm_success = False
        dm_error = None

        try:
            if user.bot or (self.bot.user and user.id == self.bot.user.id):
                return

            # Improved dedupe: use (user_id, guild_id, action_type) as key
            import time

            now = time.time()
            dedupe_key = (user.id, guild.id, action_type)
            last_sent = self._timeout_dedupe_cache.get(dedupe_key)

            # Prevent duplicate DMs within 30 seconds for same action
            if last_sent and (now - last_sent) < 30:
                print(
                    f"[Appeals] Skipped duplicate DM to {user} for {action_type} in {guild.name} (sent {now - last_sent:.1f}s ago)"
                )
                return

            self._timeout_dedupe_cache[dedupe_key] = now

            # Cleanup old cache entries (keep last 100)
            if len(self._timeout_dedupe_cache) > 200:
                oldest = sorted(self._timeout_dedupe_cache.items(), key=lambda x: x[1])[
                    :100
                ]
                for key, _ in oldest:
                    del self._timeout_dedupe_cache[key]

            timeout_member = guild.get_member(user.id)
            timeout_until = (
                getattr(timeout_member, "timed_out_until", None)
                if timeout_member
                else None
            )
            pending_record = await self._get_pending_appeal(user.id, guild.id)
            can_submit = (
                timeout_until is not None
                and timeout_until > datetime.now(timezone.utc)
                and pending_record is None
            )
            disabled_reason = None
            if pending_record is not None:
                disabled_reason = (
                    f"Appeal already submitted as #{pending_record.appeal_id}."
                )
            elif timeout_until is None or timeout_until <= datetime.now(timezone.utc):
                disabled_reason = "This timeout has already expired or was removed."

            temp_record = AppealRecord(
                appeal_id=0,
                guild_id=guild.id,
                guild_name=guild.name,
                user_id=user.id,
                username=str(user),
                punishment_type=action_type,
                punishment_reason=_clean_reason(reason),
                timeout_issued_at=issued_at,
                timeout_expires_at=expires_at
                or (timeout_until if isinstance(timeout_until, datetime) else None),
                appeal_reason="Not submitted yet.",
                should_remove="Not submitted yet.",
                appeal_learned="Not submitted yet.",
                appeal_extra=None,
                submitted_at=datetime.now(timezone.utc),
                status="pending",
            )
            view = AppealSubmissionDashboard(
                self,
                temp_record,
                can_submit=can_submit,
                disabled_reason=disabled_reason,
            )

            await user.send(view=view)
            dm_success = True
            print(
                f"[Appeals] Sent appeal dashboard to {user} ({user.id}) for {action_type} in {guild.name}"
            )

            # Log success to appeals channel
            await self._log_dm_success(
                user, guild, action_type, reason or "No reason provided"
            )
        except discord.Forbidden:
            dm_error = "DMs are closed or bot is blocked"
            print(f"[Appeals] Cannot DM {user} ({user.id}) - DMs closed or bot blocked")
        except Exception as e:
            dm_error = str(e)
            print(f"[Appeals] DM error to {user} ({user.id}): {e}")

        # Log DM failure to appeals channel
        if not dm_success and dm_error:
            await self._log_dm_failure(
                user, guild, action_type, reason or "No reason provided", dm_error
            )

    async def _log_dm_failure(
        self,
        user: discord.User | discord.Member,
        guild: discord.Guild,
        action_type: str,
        reason: str,
        error: str,
    ):
        """Log to appeals channel when DM fails"""
        for cid in (1423642446616592385, 1444013659134361703):
            ch = self.bot.get_channel(cid)
            if ch:
                embed = discord.Embed(
                    title="DM Delivery Failed",
                    description=f"**Could not send appeal form to {user.mention}**\nUser will NOT be able to submit an appeal via DM.",
                    color=APPEALS_REJECT_COLOR,
                )
                embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
                embed.add_field(name="Guild", value=guild.name, inline=True)
                embed.add_field(name="Action", value=action_type.title(), inline=True)
                embed.add_field(
                    name="Reason", value=reason or "No reason provided", inline=False
                )
                embed.add_field(name="Error", value=f"```{error}```", inline=False)
                embed.add_field(
                    name="Message Type",
                    value="Timeout Appeal Form",
                    inline=False,
                )
                embed.add_field(
                    name="Note",
                    value="This user's DMs are blocked. They cannot submit appeals through the bot. Consider alternative appeal methods or manual review.",
                    inline=False,
                )
                embed.timestamp = datetime.now(timezone.utc)
                embed.set_footer(text=_appeals_footer_text(guild.name))
                try:
                    await ch.send(embed=embed)
                    print(f"[Appeals] Logged DM failure to channel {cid}")
                except Exception as e:
                    print(
                        f"[Appeals] Failed to send DM failure log to channel {cid}: {e}"
                    )
                break

    async def _log_dm_success(
        self,
        user: discord.User | discord.Member,
        guild: discord.Guild,
        action_type: str,
        reason: str,
    ):
        """Log to appeals channel when DM is successfully sent"""
        for cid in (1423642446616592385, 1444013659134361703):
            ch = self.bot.get_channel(cid)
            if ch:
                embed = discord.Embed(
                    title="DM Delivered Successfully",
                    description=f"Successfully sent appeal form to {user.mention}",
                    color=APPEALS_ACCEPT_COLOR,
                )
                embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
                embed.add_field(name="Guild", value=guild.name, inline=True)
                embed.add_field(name="Action", value=action_type.title(), inline=True)
                embed.add_field(
                    name="Reason", value=reason or "No reason provided", inline=False
                )
                embed.add_field(
                    name="Message Type",
                    value="Timeout Appeal Form",
                    inline=False,
                )
                embed.timestamp = datetime.now(timezone.utc)
                embed.set_footer(text=_appeals_footer_text(guild.name))
                try:
                    await ch.send(embed=embed)
                except Exception as e:
                    print(
                        f"[Appeals] Failed to send DM success log to channel {cid}: {e}"
                    )
                break

    # ---------------- Listeners ----------------
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Handle ban events.

        CVH Policy: ban appeals are disabled, so we do NOT DM an appeal form on bans.
        """
        if user.bot or (self.bot.user and user.id == self.bot.user.id):
            return

        # Create unique event key to prevent duplicate processing
        import time

        event_key = (user.id, guild.id, "ban", int(time.time() / 5))  # 5-second window

        if event_key in self._ban_event_handled:
            print(f"[Appeals] Skipped duplicate ban event for {user} in {guild.name}")
            return

        self._ban_event_handled.add(event_key)

        # Clean up old entries (keep last 50)
        if len(self._ban_event_handled) > 100:
            # Remove all entries, will be recreated as needed
            self._ban_event_handled.clear()

        # Get reason from audit logs with retry
        reason = "No reason provided"
        try:
            await asyncio.sleep(1.5)  # Longer wait for audit log to be created

            # Check multiple entries to find the right one
            async for entry in guild.audit_logs(
                action=discord.AuditLogAction.ban, limit=10
            ):
                if entry.target and entry.target.id == user.id:
                    # Check if this is recent (within last 10 seconds)
                    if entry.created_at:
                        time_diff = (
                            datetime.now(timezone.utc) - entry.created_at
                        ).total_seconds()
                        if time_diff < 10:
                            if entry.reason:
                                reason = entry.reason
                            print(f"[Appeals] Found ban audit log for {user}: {reason}")
                            break
        except Exception as e:
            print(f"[Appeals] Error fetching ban audit logs: {e}")

        print(
            f"[Appeals] Ban detected for {user} ({user.id}) in {guild.name}: {reason}"
        )
        # Intentionally no DM appeal form for bans.

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Handle timeout changes - improved to prevent double DMs and log manual removals"""
        if after.bot:
            return

        before_timeout = before.timed_out_until
        after_timeout = after.timed_out_until

        # Check if timeout was manually removed OR naturally expired
        if (
            before_timeout
            and before_timeout > datetime.now(timezone.utc)
            and (not after_timeout or after_timeout <= datetime.now(timezone.utc))
        ):
            # Determine if this was manual removal or natural expiration
            current_time = datetime.now(timezone.utc)
            was_natural_expiry = False

            # If the before_timeout was very close to current time (within 30 seconds),
            # it's likely natural expiration
            if (
                before_timeout
                and (current_time - before_timeout).total_seconds() >= -30
            ):
                was_natural_expiry = True

            # Check if there are pending appeals for this user
            try:
                conn = sqlite3.connect(DATABASE_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT id FROM unban_requests WHERE user_id = ? AND status = "pending" ORDER BY id DESC LIMIT 1',
                    (after.id,),
                )
                appeal = cursor.fetchone()
                conn.close()

                if appeal:
                    if was_natural_expiry:
                        print(
                            f"[Appeals] Natural timeout expiry detected for user {after.id} with pending appeal #{appeal[0]}"
                        )
                        action_text = "Natural timeout expiry"
                        log_title = "Natural Timeout Expiry Detected"
                        log_description = f"User {after.mention} (`{after.id}`) had their timeout naturally expire while having a pending appeal."
                        color = APPEALS_TIMEOUT_END_COLOR
                    else:
                        print(
                            f"[Appeals] Manual timeout removal detected for user {after.id} with pending appeal #{appeal[0]}"
                        )
                        action_text = "Manual timeout removal"
                        log_title = "Manual Timeout Removal Detected"
                        log_description = f"User {after.mention} (`{after.id}`) had their timeout manually removed while having a pending appeal."
                        color = APPEALS_TIMEOUT_END_COLOR

                    # IMMEDIATELY mark as auto-resolved and disable buttons
                    try:
                        conn = sqlite3.connect(DATABASE_NAME)
                        cursor = conn.cursor()
                        cursor.execute(
                            'UPDATE unban_requests SET status = "auto_resolved" WHERE id = ?',
                            (appeal[0],),
                        )
                        conn.commit()
                        conn.close()

                        # Disable buttons immediately
                        await self._disable_appeal_buttons_by_id(
                            appeal[0], after.guild.id
                        )
                        print(
                            f"[Appeals] Auto-resolved appeal #{appeal[0]} and disabled buttons due to {action_text}"
                        )
                    except Exception as e:
                        print(
                            f"[Appeals] Error auto-resolving appeal #{appeal[0]}: {e}"
                        )

                    # Create log message
                    log_embed = discord.Embed(
                        title=log_title, description=log_description, color=color
                    )
                    log_embed.add_field(
                        name="Appeal ID", value=f"#{appeal[0]}", inline=True
                    )
                    log_embed.add_field(
                        name="Previous Timeout",
                        value=f"Until <t:{int(before_timeout.timestamp())}:F>",
                        inline=True,
                    )
                    log_embed.add_field(
                        name="Action",
                        value="Appeal automatically resolved and buttons disabled",
                        inline=False,
                    )
                    log_embed.set_footer(text=f"User: {after.name}")

                    # Try to send to appeals channel or log it
                    appeals_channels = [
                        channel
                        for channel in after.guild.text_channels
                        if "appeal" in channel.name.lower()
                    ]
                    if appeals_channels:
                        await appeals_channels[0].send(embed=log_embed)
                    else:
                        print(f"[Appeals] {log_embed.description}")

            except Exception as e:
                print(
                    f"[Appeals] Error checking for appeals during timeout removal: {e}"
                )

        # Only send appeal form when timeout is APPLIED (not removed)
        if before_timeout is None and after_timeout is not None:
            reason = "Timeout applied"
            try:
                # Wait for audit log
                await asyncio.sleep(1.5)
                async for entry in after.guild.audit_logs(
                    action=discord.AuditLogAction.member_update, limit=10
                ):
                    if entry.target and entry.target.id == after.id:
                        # Check if this is recent
                        if entry.created_at:
                            time_diff = (
                                datetime.now(timezone.utc) - entry.created_at
                            ).total_seconds()
                            if time_diff < 10:
                                audit_reason = entry.reason or reason
                                # Skip if audit reason contains appeal-related keywords
                                if audit_reason and not any(
                                    keyword in audit_reason.lower()
                                    for keyword in [
                                        "appeal",
                                        "approved",
                                        "unbanned",
                                        "untimeout",
                                    ]
                                ):
                                    reason = audit_reason
                                break
            except Exception as e:
                print(f"[Appeals] Error fetching timeout audit logs: {e}")

            print(
                f"[Appeals] Timeout APPLIED to {after} ({after.id}): before={before_timeout}, after={after_timeout}, reason={reason}"
            )

            # Send appeal form (logs will be sent by _send_appeal_form)
            await self._send_appeal_form(
                after,
                after.guild,
                "timed out",
                reason,
                issued_at=entry.created_at
                if "entry" in locals() and entry.created_at
                else None,
                expires_at=after_timeout,
            )

        # Check if timeout was REMOVED before expiry (manual untimeout/appeal approved)
        elif before_timeout is not None and after_timeout is None:
            # Auto-approve any pending appeals for this user in this guild
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id FROM unban_requests WHERE user_id = ? AND status = "pending"',
                (after.id,),
            )
            appeals = cursor.fetchall()

            if appeals:
                for (appeal_id,) in appeals:
                    cursor.execute(
                        'UPDATE unban_requests SET status = "approved" WHERE id = ?',
                        (appeal_id,),
                    )
                    print(
                        f"[Appeals] Auto-approved appeal #{appeal_id} - timeout removed for {after} ({after.id})"
                    )

                conn.commit()

                # Try to DM the user about approval
                try:
                    dm = create_success_embed(
                        "Appeal Automatically Approved",
                        f"## Your appeal has been automatically approved\nYour timeout in **{after.guild.name}** has been removed.",
                        guild_name=after.guild.name,
                    )
                    dm.add_field(
                        name="Result", value="**Timeout removed**", inline=True
                    )
                    await after.send(embed=dm)
                except Exception:
                    pass
            conn.close()

    @commands.hybrid_command(name="appeals")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        status="Filter appeals by status: pending, approved, denied, or all"
    )
    async def appeals(self, ctx, status: str = "pending"):
        """View appeal requests"""
        valid_statuses = ["pending", "approved", "denied", "all"]
        if status not in valid_statuses:
            embed = create_error_embed(
                "Invalid Status", f"Valid statuses: {', '.join(valid_statuses)}"
            )
            await ctx.send(embed=embed)
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        if status == "all":
            cursor.execute(
                "SELECT id, user_id, reason, status, timestamp FROM unban_requests ORDER BY timestamp DESC LIMIT 20"
            )
        else:
            cursor.execute(
                "SELECT id, user_id, reason, status, timestamp FROM unban_requests WHERE status = ? ORDER BY timestamp DESC LIMIT 20",
                (status,),
            )

        appeals = cursor.fetchall()
        conn.close()

        if not appeals:
            embed = create_info_embed("No Appeals", f"No {status} appeals found.")
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"{status.title()} Appeals", color=APPEALS_PANEL_COLOR
        )

        for appeal in appeals:
            appeal_id, user_id, reason, appeal_status, timestamp = appeal
            try:
                user = await self.bot.fetch_user(user_id)
                user_name = f"{user} ({user_id})"
            except:
                user_name = f"Unknown ({user_id})"

            embed.add_field(
                name=f"Appeal #{appeal_id}",
                value=f"**User:** {user_name}\n**Status:** {appeal_status.title()}\n**Reason:** {reason[:100]}{'...' if len(reason) > 100 else ''}\n**Time:** {timestamp}",
                inline=False,
            )

        embed.set_footer(
            text=f"Appeals are processed using interactive buttons in staff notifications"
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="appealinfo")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(appeal_id="The ID of the appeal to get information about")
    async def appealinfo(self, ctx, appeal_id: int):
        """Get detailed information about an appeal"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, reason, status, timestamp FROM unban_requests WHERE id = ?",
            (appeal_id,),
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            embed = create_error_embed(
                "Appeal Not Found", f"No appeal found with ID #{appeal_id}"
            )
            await ctx.send(embed=embed)
            return

        user_id, reason, status, timestamp = result

        try:
            user = await self.bot.fetch_user(user_id)
            user_info = f"{user} ({user.id})"
            account_created = user.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            user_info = f"Unknown User ({user_id})"
            account_created = "Unknown"

        embed = discord.Embed(
            title=f"Appeal #{appeal_id} Details", color=APPEALS_PANEL_COLOR
        )
        embed.add_field(name="User", value=user_info, inline=True)
        embed.add_field(name="Status", value=status.title(), inline=True)
        embed.add_field(name="Submitted", value=timestamp, inline=True)
        embed.add_field(name="Account Created", value=account_created, inline=True)
        embed.add_field(
            name="Appeal Content",
            value=reason[:1000] + "..." if len(reason) > 1000 else reason,
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="appealcancel")
    @app_commands.describe()
    async def appeal_cancel(self, ctx):
        """Cancel your own pending appeal (users can use this, staff can add @user to cancel another's appeal)"""
        # Check if user has a pending appeal
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id FROM unban_requests WHERE user_id = ? AND status = "pending"',
            (ctx.author.id,),
        )
        result = cursor.fetchone()

        if not result:
            embed = create_error_embed(
                "No Pending Appeal", "You don't have any pending appeals to cancel."
            )
            await _safe_ctx_send(ctx, embed=embed, ephemeral=True)
            conn.close()
            return

        appeal_id = result[0]

        # Ask for confirmation
        confirm_embed = discord.Embed(
            title="Cancel Appeal?",
            description=f"Are you sure you want to cancel appeal **#{appeal_id}**?\nYou can submit a new appeal after this is cancelled.",
            color=APPEALS_PANEL_COLOR,
        )

        class CancelConfirmView(discord.ui.View):
            def __init__(
                self,
                cog_ref: "Appeals",
                appeal_id_val: int,
                user_id: int,
                author_id: int,
            ):
                super().__init__(timeout=60)
                self.confirmed = False
                self.cog_ref = cog_ref
                self.appeal_id_val = appeal_id_val
                self.user_id_val = user_id
                self.author_id = author_id

            @discord.ui.button(label="Yes, Cancel", style=discord.ButtonStyle.red)
            async def confirm(
                self, button_interaction: discord.Interaction, button: discord.ui.Button
            ):
                if button_interaction.user.id != self.author_id:
                    await button_interaction.response.send_message(
                        "This button is not for you.", ephemeral=True
                    )
                    return

                self.confirmed = True

                # Delete the appeal from database
                conn = sqlite3.connect(DATABASE_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM unban_requests WHERE id = ?", (self.appeal_id_val,)
                )
                conn.commit()
                conn.close()

                result_embed = discord.Embed(
                    title="Appeal Cancelled",
                    description=f"Your appeal **#{self.appeal_id_val}** has been cancelled successfully.\nYou can submit a new appeal at any time.",
                    color=APPEALS_PANEL_COLOR,
                )
                result_embed.set_footer(
                    text=_appeals_footer_text(
                        button_interaction.guild.name
                        if button_interaction.guild
                        else None
                    )
                )
                result_embed.timestamp = datetime.now(timezone.utc)
                await button_interaction.response.send_message(
                    embed=result_embed, ephemeral=True
                )

                print(
                    f"[Appeals] Appeal #{self.appeal_id_val} cancelled by {button_interaction.user} ({self.author_id})"
                )

            @discord.ui.button(label="No, Keep It", style=discord.ButtonStyle.green)
            async def cancel(
                self, button_interaction: discord.Interaction, button: discord.ui.Button
            ):
                if button_interaction.user.id != self.author_id:
                    await button_interaction.response.send_message(
                        "This button is not for you.", ephemeral=True
                    )
                    return

                result_embed = discord.Embed(
                    title="Cancelled",
                    description="Your appeal was not cancelled.",
                    color=APPEALS_PANEL_COLOR,
                )
                result_embed.set_footer(
                    text=_appeals_footer_text(
                        button_interaction.guild.name
                        if button_interaction.guild
                        else None
                    )
                )
                result_embed.timestamp = datetime.now(timezone.utc)
                await button_interaction.response.send_message(
                    embed=result_embed, ephemeral=True
                )

        view = CancelConfirmView(self, appeal_id, ctx.author.id, ctx.author.id)
        await _safe_ctx_send(ctx, embed=confirm_embed, view=view, ephemeral=True)

    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        self._timeout_dedupe_cache.clear()
        self._ban_event_handled.clear()

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Log when a user is manually unbanned"""
        try:
            # Check if there are pending appeals for this user
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id FROM unban_requests WHERE user_id = ? AND status = "pending" ORDER BY id DESC LIMIT 1',
                (user.id,),
            )
            appeal = cursor.fetchone()
            conn.close()

            if appeal:
                print(
                    f"[Appeals] Manual unban detected for user {user.id} with pending appeal #{appeal[0]}"
                )

                # IMMEDIATELY mark as auto-resolved and disable buttons
                try:
                    conn = sqlite3.connect(DATABASE_NAME)
                    cursor = conn.cursor()
                    cursor.execute(
                        'UPDATE unban_requests SET status = "auto_resolved" WHERE id = ?',
                        (appeal[0],),
                    )
                    conn.commit()
                    conn.close()

                    # Disable buttons immediately
                    await self._disable_appeal_buttons_by_id(appeal[0], guild.id)
                    print(
                        f"[Appeals] Auto-resolved appeal #{appeal[0]} and disabled buttons due to manual unban"
                    )
                except Exception as e:
                    print(f"[Appeals] Error auto-resolving appeal #{appeal[0]}: {e}")

                # Get audit log entry to see who unbanned the user
                try:
                    async for entry in guild.audit_logs(
                        action=discord.AuditLogAction.unban, limit=5
                    ):
                        if entry.target and entry.target.id == user.id:
                            # Create log message
                            log_embed = discord.Embed(
                                title="Manual Unban Detected",
                                description=f"User {user.mention} (`{user.id}`) was manually unbanned while having a pending appeal.",
                                color=APPEALS_TIMEOUT_END_COLOR,
                            )
                            log_embed.add_field(
                                name="Unbanned By",
                                value=f"{entry.user.mention}"
                                if entry.user
                                else "Unknown",
                                inline=True,
                            )
                            log_embed.add_field(
                                name="Appeal ID", value=f"#{appeal[0]}", inline=True
                            )
                            log_embed.add_field(
                                name="Action",
                                value="Appeal automatically resolved and buttons disabled",
                                inline=False,
                            )
                            log_embed.set_footer(
                                text=f"{_appeals_footer_text(guild.name)} • User: {user.name}"
                            )
                            log_embed.timestamp = datetime.now(timezone.utc)

                            # Try to send to appeals channel or log it
                            appeals_channels = [
                                channel
                                for channel in guild.text_channels
                                if "appeal" in channel.name.lower()
                            ]
                            if appeals_channels:
                                await appeals_channels[0].send(embed=log_embed)
                            else:
                                print(f"[Appeals] {log_embed.description}")
                            break
                except Exception as e:
                    print(f"[Appeals] Error checking audit log for unban: {e}")

        except Exception as e:
            print(f"[Appeals] Error in on_member_unban: {e}")

    @commands.hybrid_command(
        name="check_appeals",
        description="Check for appeals that may no longer be valid due to expired/removed punishments",
    )
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def check_appeals(self, ctx: commands.Context):
        """Check all pending appeals for validity"""
        try:
            # Send initial processing message
            processing_msg = await ctx.send("Checking pending appeals...")

            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, user_id, reason FROM unban_requests WHERE status = "pending"'
            )
            pending_appeals = cursor.fetchall()
            conn.close()

            if not pending_appeals:
                embed = create_success_embed(
                    "Appeal Check Complete",
                    "No pending appeals found.",
                    guild_name=ctx.guild.name if ctx.guild else None,
                )
                await processing_msg.edit(content=None, embed=embed)
                return

            invalid_appeals = []
            valid_appeals = []

            for appeal_id, user_id, reason in pending_appeals:
                # Check ban status
                try:
                    if ctx.guild:
                        await ctx.guild.fetch_ban(discord.Object(id=user_id))
                        valid_appeals.append((appeal_id, user_id, "Still banned"))
                        continue
                except discord.NotFound:
                    invalid_appeals.append((appeal_id, user_id, "No longer banned"))
                    continue
                except discord.Forbidden:
                    valid_appeals.append(
                        (appeal_id, user_id, "Cannot check ban status")
                    )
                    continue

                # Check timeout status
                if ctx.guild:
                    member = ctx.guild.get_member(user_id)
                    if member:
                        timeout_until = getattr(member, "timed_out_until", None)
                        if timeout_until and timeout_until > datetime.now(timezone.utc):
                            valid_appeals.append(
                                (
                                    appeal_id,
                                    user_id,
                                    f"Still timed out until <t:{int(timeout_until.timestamp())}:F>",
                                )
                            )
                        else:
                            invalid_appeals.append(
                                (appeal_id, user_id, "Timeout expired or removed")
                            )
                    else:
                        invalid_appeals.append(
                            (appeal_id, user_id, "User left the server")
                        )

            embed = create_info_embed(
                "Appeal Validity Check",
                f"Found {len(pending_appeals)} pending appeals",
                guild_name=ctx.guild.name if ctx.guild else None,
            )

            if valid_appeals:
                valid_text = "\\n".join(
                    [
                        f"#{aid}: <@{uid}> - {status}"
                        for aid, uid, status in valid_appeals[:10]
                    ]
                )
                embed.add_field(
                    name=f"Valid Appeals ({len(valid_appeals)})",
                    value=valid_text,
                    inline=False,
                )

            if invalid_appeals:
                invalid_text = "\\n".join(
                    [
                        f"#{aid}: <@{uid}> - {status}"
                        for aid, uid, status in invalid_appeals[:10]
                    ]
                )
                embed.add_field(
                    name=f"Invalid Appeals ({len(invalid_appeals)})",
                    value=invalid_text,
                    inline=False,
                )

                # Auto-resolve invalid appeals
                conn = sqlite3.connect(DATABASE_NAME)
                cursor = conn.cursor()
                for appeal_id, user_id, status in invalid_appeals:
                    cursor.execute(
                        'UPDATE unban_requests SET status = "auto_resolved" WHERE id = ?',
                        (appeal_id,),
                    )
                    print(f"[Appeals] Auto-resolved appeal #{appeal_id} - {status}")
                conn.commit()
                conn.close()

                embed.add_field(
                    name="Action Taken",
                    value="Invalid appeals have been automatically resolved",
                    inline=False,
                )

            if len(valid_appeals) > 10 or len(invalid_appeals) > 10:
                embed.set_footer(
                    text=f"{_appeals_footer_text(ctx.guild.name if ctx.guild else None)} • Showing first 10 of each category"
                )

            await processing_msg.edit(content=None, embed=embed)

        except Exception as e:
            print(f"[Appeals] Error in check_appeals: {e}")
            error_embed = create_error_embed("Error", f"Failed to check appeals: {e}")
            if "processing_msg" in locals():
                await processing_msg.edit(content=None, embed=error_embed)
            else:
                await ctx.send(embed=error_embed)


async def setup(bot):
    await bot.add_cog(Appeals(bot))
