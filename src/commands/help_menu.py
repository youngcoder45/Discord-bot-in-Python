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
# Maps cog class names -> display label. Commands from any cog not listed
# here are grouped under a "Miscellaneous" category automatically.
COG_CATEGORIES: dict[str, str] = {
    "Core": "Core",
    "Diagnostics": "Diagnostics",
    # Moderation is a single broad section: basic moderation (ModCog),
    # advanced moderation tools and the SAM warnings system.
    "ModCog": "Moderation",
    "AdvancedModeration": "Moderation",
    "Warnings": "Moderation",
    # AutoMod & Protection covers the anti-abuse systems.
    "Protection": "AutoMod & Protection",
    "SpamCatch": "AutoMod & Protection",
    "Appeals": "Appeals",
    "Tickets": "Tickets",
    "ReactionRoles": "Reaction Roles",
    "PermitSystem": "Permits",
    "LoggingCog": "Logging",
    # Utilities is the general-purpose section: embed builder plus the
    # smaller helper systems (sticky messages, rules, threads, help threads).
    "EmbedBuilder": "Utilities",
    "StickyMessage": "Utilities",
    "RulesCog": "Utilities",
    "ThreadCloser": "Utilities",
    "HelpThreadNotification": "Utilities",
    "MessageHandler": "Miscellaneous",
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


def _is_visible_command(cmd, is_owner: bool) -> bool:
    """Decide whether a command should appear in the help menu.

    Works for both prefix/hybrid commands (commands.Command) and slash-only
    commands (app_commands.Command / our _SlashCommandInfo wrapper).

    - Explicit system commands (sync/load/introreact) are always hidden.
    - Owner-only commands are always decorated hidden=True by convention
      (commands.is_owner is a function, not a class, so it cannot be used
      with isinstance) — they are excluded via the hidden filter below.
    - Other hidden commands are hidden unless whitelisted for users.
    - Regular commands are always visible.
    """
    name = getattr(cmd, "name", "")
    if name in _SYSTEM_COMMANDS:
        return False
    hidden = getattr(cmd, "hidden", False) or bool(getattr(cmd, "extras", {}).get("hidden", False))
    if hidden:
        return name in _USER_HIDDEN_COMMANDS
    return True


# ---------------------------------------------------------------------------
# Command type detection (Slash / Hybrid / Prefix)
# ---------------------------------------------------------------------------
def command_type(cmd) -> str:
    """Classify a command as "slash", "hybrid" or "prefix".

    - Hybrid: commands.HybridCommand / commands.HybridGroup (have an
      app_command attached AND live in the prefix command list).
    - Slash: app_commands.Command / Group (slash-only, from the command tree).
    - Prefix: commands.Command with no slash counterpart.
    """
    if isinstance(cmd, _SlashCommandInfo):
        return "slash"
    if isinstance(cmd, (commands.HybridCommand, commands.HybridGroup)):
        return "hybrid"
    if isinstance(cmd, (app_commands.Command, app_commands.Group)):
        return "slash"
    if getattr(cmd, "app_command", None) is not None:
        return "hybrid"
    return "prefix"


def _cog_category(cog_name: Optional[str]) -> str:
    """Return the display label for a cog's commands."""
    if cog_name:
        label = COG_CATEGORIES.get(cog_name)
        if label:
            return label
    return "Miscellaneous"


class _SlashCommandInfo:
    """Lightweight display wrapper for slash-only commands from the tree.

    app_commands.Command objects lack help/short_doc/cog_name, so we project
    them onto a uniform shape that the embed builders and visibility filter
    already understand. The owning cog is derived from cog attributes via
    _slash_command_cogs(); .extras carries the command's hidden flag.
    """

    def __init__(self, app_cmd, qualified_name: str, label: str):
        self.app_command = app_cmd
        self.name = app_cmd.name
        self.qualified_name = qualified_name
        self.label = label
        self.aliases: list[str] = []
        self.hidden = False
        self.extras: dict = dict(getattr(app_cmd, "extras", {}) or {})
        self.cog_name = label

    @property
    def help(self):
        return self.app_command.description or None

    @property
    def short_doc(self):
        return self.app_command.description or None

    @property
    def checks(self):
        return []


def _tree_commands(bot: commands.Bot) -> dict[str, app_commands.Command]:
    """Flatten the app command tree into {qualified_name: command}."""
    result: dict[str, app_commands.Command] = {}
    for cmd in bot.tree.walk_commands():  # type: ignore[attr-defined]
        result.setdefault(cmd.qualified_name, cmd)
    return result


def _slash_command_cogs(bot: commands.Bot) -> dict[str, str]:
    """Map every slash command's qualified name to its defining cog class name.

    app_commands.Command/Group objects do not carry a reference to the cog
    that defined them (extras is empty, no binding attr in this discord.py
    version), so we discover them by scanning each loaded cog's class
    attributes for Command/Group instances.
    """
    result: dict[str, str] = {}
    for cog in bot.cogs.values():
        for attr_name in dir(cog):
            if attr_name.startswith("_"):
                continue
            attr = getattr(cog, attr_name, None)
            if isinstance(attr, (app_commands.Command, app_commands.Group)):
                result.setdefault(attr.qualified_name, cog.__class__.__name__)
                # Direct subcommands of a group belong to the same cog.
                if isinstance(attr, app_commands.Group):
                    for sub in attr.commands:
                        result.setdefault(sub.qualified_name, cog.__class__.__name__)
    return result


def build_categories(bot: commands.Bot, ctx) -> dict[str, list]:
    """Group every visible command into its display category.

    Returns an ordered dict of {category_label: [commands]} where each entry
    is either a commands.Command (prefix/hybrid) or a _SlashCommandInfo
    (slash-only). Every command appears exactly once.
    """
    is_owner = _is_owner(ctx)
    categories: dict[str, list] = defaultdict(list)

    # Prefix + hybrid commands (hybrids carry .app_command and live here).
    tree = _tree_commands(bot)
    registered_prefix_names: set[str] = set()
    for cmd in bot.commands:
        if not _is_visible_command(cmd, is_owner):
            continue
        # Hybrid commands are also present in the tree; register by qualified
        # name so slash-only commands from the tree don't duplicate them.
        qname = cmd.qualified_name
        label = _cog_category(cmd.cog_name)
        categories[label].append((qname, cmd))
        tree.pop(qname, None)
        registered_prefix_names.add(cmd.name)

    # Slash-only commands from the tree (hybrids were already popped above).
    # Subcommands of groups are skipped here — they are listed inside the
    # group's detailed help instead, keeping each category list tidy.
    slash_cogs = _slash_command_cogs(bot)
    for qname, app_cmd in tree.items():
        if getattr(app_cmd, "parent", None) is not None:
            continue  # subcommand of a group (shown via detail view)
        # A command registered as a plain prefix command AND as a slash command
        # (e.g. getuserid in protection.py) is shown once under its prefix form.
        if app_cmd.name in registered_prefix_names:
            continue
        if not _is_visible_command(app_cmd, is_owner):
            continue
        label = _cog_category(slash_cogs.get(qname))
        categories[label].append((qname, _SlashCommandInfo(app_cmd, qname, label)))

    result: dict[str, list] = {}
    for label, entries in categories.items():
        entries.sort(key=lambda e: e[0])
        result[label] = [cmd for _, cmd in entries]
    return dict(sorted(result.items()))


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
    embed.add_field(name="Quick Stats", value="\n".join(stats), inline=False)

    overview = "\n".join(
        f"**{label}** — {len(cmds)} command{'s' if len(cmds) != 1 else ''}"
        for label, cmds in categories.items()
    )
    embed.add_field(name="Categories", value=overview or "No commands available.", inline=False)

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
    """Extract human-readable permission requirements from command checks.

    Note: owner-only commands are excluded from the help menu upstream
    (commands.is_owner is a function, not a class, so it cannot be used
    with isinstance).
    """
    perms: list[str] = []
    for check in getattr(cmd, "checks", []) or []:
        kw = getattr(check, "kwargs", None)
        if not kw:
            continue
        for perm, value in kw.items():
            if isinstance(value, bool) and value:
                perms.append(_perm_label(perm))
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


def _display_name(cmd) -> str:
    """Name shown in list views: uses /-form for slash commands, prefix form otherwise."""
    if command_type(cmd) == "slash":
        return f"/{cmd.qualified_name}"
    return cmd.qualified_name


def _display_usage(cmd, prefix: str) -> str:
    """Build the usage line(s) for a command of any type."""
    ctype = command_type(cmd)
    if ctype == "slash":
        return f"`/{cmd.qualified_name}`"
    if ctype == "hybrid":
        sig = getattr(cmd, "signature", "") or ""
        sig = " " + sig if sig else sig
        return f"`{prefix}{cmd.qualified_name}{sig}` / `{cmd.qualified_name}{sig}`"
    sig = getattr(cmd, "signature", "") or ""
    sig = " " + sig if sig else sig
    return f"`{prefix}{cmd.qualified_name}{sig}`"


def _normalize_command_name(name: str) -> str:
    """Normalize user input like '/verify', '?ban' or 'ls role' to a lookup key."""
    name = name.strip().lstrip("/").lstrip("?")
    return name.replace(" ", ".")


def _total_visible_count(bot: commands.Bot) -> int:
    """Count of commands shown in the menu (top-level visible commands)."""
    seen: set[str] = set()
    for c in bot.commands:
        if not _is_visible_command(c, False):
            continue
        seen.add(c.qualified_name)
    for app_cmd in _tree_commands(bot).values():
        if getattr(app_cmd, "parent", None) is not None:
            continue
        if app_cmd.name in {c.name for c in bot.commands}:
            continue
        if not _is_visible_command(app_cmd, False):
            continue
        seen.add(app_cmd.qualified_name)
    return len(seen)


def _find_command(bot: commands.Bot, name: str):
    """Find a command by (possibly qualified) name across prefix + slash."""
    name = _normalize_command_name(name)
    # Try dotted form first (tree-style keys), then the space form (the
    # natural prefix syntax, e.g. 'ls role' resolves via bot.get_command).
    for key in (name, name.replace(".", " ")):
        cmd = bot.get_command(key)
        if cmd is not None:
            return cmd
        for app_cmd in _tree_commands(bot).values():
            if app_cmd.qualified_name == key:
                label = _cog_category(_slash_command_cogs(bot).get(key))
                return _SlashCommandInfo(app_cmd, key, label)
    return None


def build_command_embed(
    bot: commands.Bot,
    cmd,
    prefix: str,
    is_owner: bool,
) -> discord.Embed:
    """Detailed embed for a single command (any type)."""
    embed = discord.Embed(
        title=f"`{cmd.qualified_name}`",
        description=(cmd.help or cmd.short_doc or "No description provided."),
        color=0x2B2D31,
        timestamp=datetime.now(timezone.utc),
    )

    embed.add_field(name="Category", value=_cog_category(getattr(cmd, "cog_name", None)), inline=True)
    embed.add_field(name="Type", value=_type_label(cmd), inline=True)

    aliases = _get_aliases(cmd)
    if aliases:
        embed.add_field(
            name="Aliases",
            value=", ".join(f"`{a}`" for a in aliases[:8]),
            inline=True,
        )

    embed.add_field(name="Usage", value=_display_usage(cmd, prefix), inline=False)

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
    elif isinstance(cmd, _SlashCommandInfo) and isinstance(cmd.app_command, app_commands.Group):
        subs = [s for s in cmd.app_command.commands if _is_visible_command(s, is_owner)]
        if subs:
            lines = [f"`{s.name}` — {s.description or 'No description'}" for s in subs]
            embed.add_field(name="Subcommands", value="\n".join(lines), inline=False)

    embed.set_footer(text=f"CodeVerse Bot • {_total_visible_count(bot)} total commands")
    return embed


# ---------------------------------------------------------------------------
# Category page rendering (with pagination)
# ---------------------------------------------------------------------------
_COMMANDS_PER_FIELD = 12
_FIELDS_PER_PAGE = 2


def _chunk_commands(cmds: list, size: int) -> list[list]:
    return [cmds[i : i + size] for i in range(0, len(cmds), size)]


def _total_pages(cmds: list) -> int:
    """Number of pages for a category given the per-page chunking."""
    return max(1, len(_chunk_commands(cmds, _COMMANDS_PER_FIELD * _FIELDS_PER_PAGE)))


def _section_lines(cmds: list, prefix: str) -> list[str]:
    """Format command lines (without a section heading)."""
    lines = []
    for cmd in cmds:
        summary = (cmd.short_doc or cmd.help or "No description").strip().replace("\n", " ")
        if len(summary) > 70:
            summary = summary[:67] + "…"
        lines.append(f"`{_display_name(cmd)}` — {summary}")
    return lines


def _group_by_type(cmds: list) -> dict[str, list]:
    """Split commands into slash/hybrid/prefix buckets."""
    buckets: dict[str, list] = {"slash": [], "hybrid": [], "prefix": []}
    for cmd in cmds:
        buckets[command_type(cmd)].append(cmd)
    return buckets


_SECTION_TITLES = {"slash": "Slash Commands", "hybrid": "Hybrid Commands", "prefix": "Prefix Commands"}


def build_category_embed(
    bot: commands.Bot,
    label: str,
    cmds: list,
    prefix: str,
    page: int = 0,
) -> discord.Embed:
    """Embed for one category page, grouped into command-type sections.

    Sections are shown in the order Slash -> Hybrid -> Prefix, and empty
    sections are omitted entirely.
    """
    page_size = _COMMANDS_PER_FIELD * _FIELDS_PER_PAGE
    total_pages = max(1, len(_chunk_commands(cmds, page_size)))
    page = max(0, min(page, total_pages - 1))
    page_cmds = cmds[page * page_size : (page + 1) * page_size]

    embed = discord.Embed(
        title=f"{label} Commands",
        description=f"{len(cmds)} command{'s' if len(cmds) != 1 else ''} • `?help <command>` or `/help <command>` for details",
        color=0x2B2D31,
        timestamp=datetime.now(timezone.utc),
    )

    buckets = _group_by_type(page_cmds)
    for ctype in ("slash", "hybrid", "prefix"):
        group = buckets[ctype]
        if not group:
            continue
        # If a section spills onto the next page, mark it so users know it
        # continues (headers are never orphaned on their own page).
        title = _SECTION_TITLES[ctype]
        if page > 0 and command_type(cmds[page * page_size - 1]) == ctype:
            title += " (cont.)"
        for chunk in _chunk_commands(group, _COMMANDS_PER_FIELD):
            lines = _section_lines(chunk, prefix)
            embed.add_field(name=title, value="\n".join(lines), inline=False)

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
            custom_id="help:home",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.view.home_embed, view=self.view)  # type: ignore[attr-defined]


class _PageButton(discord.ui.Button):
    def __init__(self, label: str, custom_id: str, direction: int):
        super().__init__(label=label, style=discord.ButtonStyle.primary, custom_id=custom_id)
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
        self.add_item(_PageButton("◀", "help:prev", -1))
        self.add_item(_PageButton("▶", "help:next", 1))

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
        cmd = _find_command(bot, command_name.lower())
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
