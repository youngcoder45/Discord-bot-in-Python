"""Dynamic, self-maintaining help menu for CodeVerse Bot.

The help menu is built entirely from the bot's loaded command tree at
render time, so new commands appear automatically once their cog is loaded.
There is no manual command list to keep in sync.
"""
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Category configuration
# ---------------------------------------------------------------------------
# Maps cog class names -> (display label, emoji). Commands from any cog not
# listed here are grouped under a "Miscellaneous" category automatically.
COG_CATEGORIES: dict[str, tuple[str, str]] = {
    "Core": ("Core", "🛠️"),
    "Diagnostics": ("Diagnostics", "🔍"),
    "ModCog": ("Moderation", "🛡️"),
    "AdvancedModeration": ("Advanced Moderation", "⚙️"),
    "Protection": ("AutoMod & Protection", "🤖"),
    "Appeals": ("Appeals", "📨"),
    "SpamCatch": ("Spam Prevention", "🧹"),
    "Tickets": ("Tickets", "🎫"),
    "StickyMessage": ("Sticky Messages", "📌"),
    "ReactionRoles": ("Reaction Roles", "🎭"),
    "PermitSystem": ("Permits", "🗝️"),
    "EmbedBuilder": ("Utilities", "🧰"),
    "RulesCog": ("Rules", "📜"),
    "ThreadCloser": ("Threads", "🧵"),
    "HelpThreadNotification": ("Help Threads", "🆘"),
    "Warnings": ("Warnings", "⚠️"),
    "MemberEvents": ("Member Events", "👋"),
    "MessageHandler": ("Miscellaneous", "📁"),
}

# Cog classes that are purely automated (no user-invocable commands).
_AUTOMATED_COGS = {"LoggingCog", "MemberEvents"}

# Hidden commands that are still intended for regular users.
_USER_HIDDEN_COMMANDS = {"needhelp"}

# Commands that should never surface in the help menu at all.
_SYSTEM_COMMANDS = {"introreact", "sync", "load"}

DEFAULT_PREFIX = "?"


# ---------------------------------------------------------------------------
# Command discovery / categorization
# ---------------------------------------------------------------------------
def _is_owner(ctx: commands.Context) -> bool:
    """Return whether the invoking user is the bot owner (sync check)."""
    author = getattr(ctx, "author", None)
    if author is None:
        return False
    owner_ids = set(getattr(ctx.bot, "owner_ids", None) or ())
    if getattr(ctx.bot, "owner_id", None):
        owner_ids.add(ctx.bot.owner_id)
    if getattr(ctx.bot, "user", None):
        owner_ids.add(ctx.bot.user.id)
    return author.id in owner_ids


def _is_visible_command(cmd: commands.Command, is_owner: bool) -> bool:
    """Decide whether a command should appear in the help menu.

    - Explicit system commands are always hidden.
    - Owner-only commands are visible only to the bot owner.
    - Other hidden commands are hidden unless whitelisted for users.
    - Regular commands are always visible.
    """
    if cmd.name in _SYSTEM_COMMANDS:
        return False
    if any(isinstance(c, commands.is_owner) for c in getattr(cmd, "checks", []) or []):
        return is_owner
    if cmd.hidden:
        return cmd.name in _USER_HIDDEN_COMMANDS
    return True


def _cog_category(cog_name: Optional[str]) -> tuple[str, str]:
    """Return the (label, emoji) for a cog's commands."""
    if cog_name:
        category = COG_CATEGORIES.get(cog_name)
        if category:
            return category
    return "Miscellaneous", "📁"


def build_categories(bot: commands.Bot, ctx) -> dict[str, list[commands.Command]]:
    """Group every visible top-level command into its display category.

    Returns an ordered dict of {category_label: [commands]}, sorted by
    label and with each category's commands sorted by name.
    """
    is_owner = _is_owner(ctx)
    categories: dict[str, list[commands.Command]] = defaultdict(list)

    for cmd in bot.commands:
        if not _is_visible_command(cmd, is_owner):
            continue
        label, _ = _cog_category(cmd.cog_name)
        categories[label].append(cmd)

    for cmds in categories.values():
        cmds.sort(key=lambda c: c.name)
    return dict(sorted(categories.items()))


def build_home_embed(bot: commands.Bot, categories: dict[str, list[commands.Command]], prefix: str) -> discord.Embed:
    """Main help page with bot info, quick stats and category overview."""
    total = sum(len(cmds) for cmds in categories.values())
    uptime = _format_uptime(bot)

    embed = discord.Embed(
        title="CodeVerse Bot — Help Center",
        description=(
            "Welcome to **CodeVerse Bot**! Pick a category from the dropdown "
            "below to explore its commands.\n\n"
            f"**Prefix:** `{prefix}` (e.g. `{prefix}ping`)\n"
            "**Slash:** `/` (e.g. `/ping`)\n"
            "Use `/help <command>` or `?help <command>` for detailed info on a specific command."
        ),
        color=0x2B2D31,
        timestamp=datetime.now(timezone.utc),
    )

    stats = [
        f"• **Commands:** {total}",
        f"• **Categories:** {len(categories)}",
        f"• **Uptime:** {uptime}",
    ]
    embed.add_field(name="📊 Quick Stats", value="\n".join(stats), inline=False)

    overview = "\n".join(
        f"{emoji} **{label}** — {len(cmds)} command{'s' if len(cmds) != 1 else ''}"
        for label, cmds in categories.items()
    )
    embed.add_field(name="🗂️ Categories", value=overview or "No commands available.", inline=False)

    if bot.user and bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
    embed.set_footer(text=f"{total} total commands • Use the dropdown to browse categories")
    return embed


def _format_uptime(bot: commands.Bot) -> str:
    try:
        start_time = getattr(bot, "start_time", datetime.now(timezone.utc))
        uptime = datetime.now(timezone.utc) - start_time
        return str(uptime).split(".")[0]
    except Exception:
        return "Unknown"


def _format_usage(bot: commands.Bot, cmd: commands.Command, prefix: str) -> str:
    """Build `prefix cmd sig` / `/cmd sig` usage lines for a command."""
    sig = getattr(cmd, "signature", "") or ""
    if sig:
        sig = " " + sig
    lines = [f"`{prefix}{cmd.qualified_name}{sig}`"]
    if getattr(cmd, "app_command", None) is not None:
        lines.append(f"`/{cmd.qualified_name}{sig}`")
    return "\n".join(lines)


def _format_permissions(cmd: commands.Command) -> str:
    """Extract human-readable permission requirements from command checks."""
    perms: list[str] = []
    owner_only = False
    for check in getattr(cmd, "checks", []) or []:
        if isinstance(check, commands.is_owner):
            owner_only = True
            continue
        kw = getattr(check, "kwargs", None)
        if not kw:
            continue
        for perm, value in kw.items():
            if isinstance(value, bool) and value:
                perms.append(_perm_label(perm))
    if owner_only:
        return "Bot Owner only"
    return ", ".join(perms) if perms else "Everyone"


def _perm_label(perm: str) -> str:
    """Convert a discord.Permissions attribute to a friendly label."""
    labels = {
        "administrator": "Administrator",
        "ban_members": "Ban Members",
        "kick_members": "Kick Members",
        "manage_messages": "Manage Messages",
        "manage_roles": "Manage Roles",
        "manage_channels": "Manage Channels",
        "manage_guild": "Manage Server",
        "manage_threads": "Manage Threads",
        "moderate_members": "Moderate Members",
        "manage_webhooks": "Manage Webhooks",
        "manage_events": "Manage Events",
        "manage_nicknames": "Manage Nicknames",
        "send_messages": "Send Messages",
        "embed_links": "Embed Links",
        "mute_members": "Mute Members",
        "move_members": "Move Members",
        "deafen_members": "Deafen Members",
        "view_audit_log": "View Audit Log",
        "manage_expressions": "Manage Expressions",
        "mention_everyone": "Mention Everyone",
        "attach_files": "Attach Files",
    }
    return labels.get(perm, perm.replace("_", " ").title())


def _format_cooldown(cmd: commands.Command) -> Optional[str]:
    """Return a short cooldown description if the command defines one."""
    for check in getattr(cmd, "checks", []) or []:
        if isinstance(check, commands.Cooldown):
            per = check.per
            unit = "second"
            if per >= 3600:
                per, unit = per / 3600, "hour"
            elif per >= 60:
                per, unit = per / 60, "minute"
            return f"{check.rate} use{'s' if check.rate != 1 else ''}/{int(per)} {unit}{'s' if int(per) != 1 else ''}"
    return None


def _type_label(cmd: commands.Command) -> str:
    """Classify a command as Slash, Prefix or Hybrid."""
    has_app = getattr(cmd, "app_command", None) is not None
    is_prefix = True  # registered via @commands.command / hybrid_command
    if has_app and is_prefix:
        return "Hybrid"
    if has_app:
        return "Slash"
    return "Prefix"


def _get_aliases(cmd: commands.Command) -> list[str]:
    """Return the effective alias list (excluding slash command names)."""
    aliases = [a for a in getattr(cmd, "aliases", []) or []]
    app_cmd = getattr(cmd, "app_command", None)
    if app_cmd is not None:
        app_name = getattr(app_cmd, "name", None)
        if app_name:
            aliases = [a for a in aliases if a != app_name]
    return aliases


def build_command_embed(
    bot: commands.Bot,
    cmd: commands.Command,
    prefix: str,
    is_owner: bool,
) -> discord.Embed:
    """Detailed embed for a single command."""
    embed = discord.Embed(
        title=f"`{cmd.qualified_name}`",
        description=(cmd.help or cmd.short_doc or "No description provided."),
        color=0x2B2D31,
        timestamp=datetime.now(timezone.utc),
    )

    label, emoji = _cog_category(cmd.cog_name)
    embed.add_field(name="Category", value=f"{emoji} {label}", inline=True)
    embed.add_field(name="Type", value=_type_label(cmd), inline=True)

    aliases = _get_aliases(cmd)
    if aliases:
        embed.add_field(
            name="Aliases",
            value=", ".join(f"`{a}`" for a in aliases[:8]),
            inline=True,
        )

    embed.add_field(name="Usage", value=_format_usage(bot, cmd, prefix), inline=False)

    perms = _format_permissions(cmd)
    if perms:
        embed.add_field(name="Required Permissions", value=perms, inline=True)

    cooldown = _format_cooldown(cmd)
    if cooldown:
        embed.add_field(name="Cooldown", value=cooldown, inline=True)

    if isinstance(cmd, commands.Group):
        subs = [s for s in cmd.commands if _is_visible_command(s, is_owner)]
        if subs:
            lines = [f"`{s.name}` — {s.short_doc or 'No description'}" for s in subs]
            embed.add_field(name="Subcommands", value="\n".join(lines), inline=False)

    total = sum(
        1 for c in bot.commands if _is_visible_command(c, is_owner)
    )
    embed.set_footer(text=f"CodeVerse Bot • {total} total commands")
    return embed


# ---------------------------------------------------------------------------
# Category page rendering (with pagination)
# ---------------------------------------------------------------------------
_COMMANDS_PER_FIELD = 12
_FIELDS_PER_PAGE = 2


def _chunk_commands(cmds: list[commands.Command], size: int) -> list[list[commands.Command]]:
    return [cmds[i : i + size] for i in range(0, len(cmds), size)]


def _category_emoji(label: str) -> str:
    """Return the emoji for a display label (reverse lookup of COG_CATEGORIES)."""
    for _, (cat_label, emoji) in COG_CATEGORIES.items():
        if cat_label == label:
            return emoji
    return "📁"


def _total_pages(cmds: list[commands.Command]) -> int:
    """Number of pages for a category given the per-page chunking."""
    return max(1, len(_chunk_commands(cmds, _COMMANDS_PER_FIELD * _FIELDS_PER_PAGE)))


def build_category_embed(
    bot: commands.Bot,
    label: str,
    cmds: list[commands.Command],
    prefix: str,
    page: int = 0,
) -> discord.Embed:
    """Embed for one category page. Returns a single page of commands."""
    emoji = _category_emoji(label)

    page_size = _COMMANDS_PER_FIELD * _FIELDS_PER_PAGE
    total_pages = max(1, len(_chunk_commands(cmds, page_size)))
    page = max(0, min(page, total_pages - 1))
    page_fields = _chunk_commands(cmds[page * page_size : (page + 1) * page_size], _COMMANDS_PER_FIELD)

    embed = discord.Embed(
        title=f"{emoji} {label} Commands",
        description=f"{len(cmds)} command{'s' if len(cmds) != 1 else ''} • `?help <command>` or `/help <command>` for details",
        color=0x2B2D31,
        timestamp=datetime.now(timezone.utc),
    )

    for chunk in page_fields:
        lines = []
        for cmd in chunk:
            summary = (cmd.short_doc or cmd.help or "No description").strip().replace("\n", " ")
            if len(summary) > 70:
                summary = summary[:67] + "…"
            lines.append(f"`{prefix}{cmd.name}` — {summary}")
        embed.add_field(name="Commands", value="\n".join(lines), inline=False)

    if total_pages > 1:
        embed.set_footer(
            text=f"Page {page + 1}/{total_pages} • Use the buttons to navigate • {len(cmds)} commands"
        )
    else:
        embed.set_footer(text=f"{len(cmds)} commands • Select another category from the dropdown")
    return embed


# ---------------------------------------------------------------------------
# Interactive view
# ---------------------------------------------------------------------------
class _HomeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Home",
            style=discord.ButtonStyle.secondary,
            emoji="🏠",
            custom_id="help:home",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.view.home_embed, view=self.view)  # type: ignore[attr-defined]


class _PageButton(discord.ui.Button):
    def __init__(self, label: str, emoji: Optional[str], custom_id: str, direction: int):
        super().__init__(
            label=label, style=discord.ButtonStyle.primary, emoji=emoji or None, custom_id=custom_id
        )
        self.direction = direction

    async def callback(self, interaction: discord.Interaction):
        view: HelpMenuView = self.view  # type: ignore[assignment]
        page = view.current_page + self.direction
        view.current_page = max(0, min(page, view.total_pages - 1))
        embed = build_category_embed(
            view.bot, view.current_label, view.current_cmds, view.prefix, view.current_page
        )
        await interaction.response.edit_message(embed=embed, view=view)


class _CategorySelect(discord.ui.Select):
    def __init__(self, categories: dict[str, list[commands.Command]]):
        options = [
            discord.SelectOption(
                label=label,
                description=f"{len(cmds)} command{'s' if len(cmds) != 1 else ''}",
                value=label,
            )
            for label, cmds in categories.items()
        ]
        super().__init__(
            placeholder="Choose a category to explore…",
            min_values=1,
            max_values=1,
            options=options[:25],
            custom_id="help:category",
        )

    async def callback(self, interaction: discord.Interaction):
        view: HelpMenuView = self.view  # type: ignore[assignment]
        label = self.values[0]
        view.current_label = label
        view.current_cmds = view.categories[label]
        view.current_page = 0
        view.total_pages = _total_pages(view.current_cmds)
        embed = build_category_embed(view.bot, label, view.current_cmds, view.prefix, 0)
        await interaction.response.edit_message(embed=embed, view=view)


class HelpMenuView(discord.ui.View):
    """Dropdown + paginated help menu."""

    def __init__(
        self,
        bot: commands.Bot,
        categories: dict[str, list[commands.Command]],
        home_embed: discord.Embed,
        prefix: str,
    ):
        super().__init__(timeout=180)
        self.bot = bot
        self.categories = categories
        self.home_embed = home_embed
        self.prefix = prefix
        self.current_label: Optional[str] = None
        self.current_cmds: list[commands.Command] = []
        self.current_page = 0
        self.total_pages = 1

        self.add_item(_CategorySelect(categories))
        self.add_item(_HomeButton())
        self.add_item(_PageButton("◀", None, "help:prev", -1))
        self.add_item(_PageButton("▶", None, "help:next", 1))

    async def on_timeout(self) -> None:
        """Clean up the menu by disabling it when it times out."""
        try:
            for item in self.children:
                item.disabled = True
            await self.message.edit(view=self)  # type: ignore[union-attr]
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Entry point used by the help command
# ---------------------------------------------------------------------------
async def send_help_menu(ctx: commands.Context, command_name: Optional[str] = None) -> None:
    """Render and send the interactive help menu.

    Works for both slash and prefix invocations via hybrid commands.
    """
    bot = ctx.bot
    prefix = getattr(ctx, "clean_prefix", DEFAULT_PREFIX) or DEFAULT_PREFIX
    is_owner = _is_owner(ctx)

    # Detailed help for a specific command
    if command_name:
        cmd = bot.get_command(command_name.lower())
        if not cmd or not _is_visible_command(cmd, is_owner):
            await _reply(ctx, f"Command `{command_name}` not found.")
            return
        embed = build_command_embed(bot, cmd, prefix, is_owner)
        await _reply(ctx, embed=embed)
        return

    # Interactive menu
    categories = build_categories(bot, ctx)
    home_embed = build_home_embed(bot, categories, prefix)
    view = HelpMenuView(bot, categories, home_embed, prefix)
    if ctx.interaction:
        await ctx.interaction.response.send_message(embed=home_embed, view=view)
    else:
        message = await ctx.send(embed=home_embed, view=view)
        view.message = message


async def _reply(ctx, content: str | None = None, embed: discord.Embed | None = None) -> None:
    """Reply through either the interaction or a plain context."""
    if ctx.interaction:
        if not ctx.interaction.response.is_done():
            if embed is not None:
                await ctx.interaction.response.send_message(content=content or "", embed=embed, ephemeral=True)
            else:
                await ctx.interaction.response.send_message(content=content or "", ephemeral=True)
        else:
            if embed is not None:
                await ctx.interaction.followup.send(content=content or "", embed=embed, ephemeral=True)
            else:
                await ctx.interaction.followup.send(content=content or "", ephemeral=True)
    else:
        if embed is not None:
            await ctx.send(content=content or "", embed=embed)
        else:
            await ctx.send(content=content or "")
