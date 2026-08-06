import asyncio
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
import logging

import discord  # type: ignore[import-not-found]
from discord.ext import commands  # type: ignore[import-not-found]

logger = logging.getLogger("codeverse.helpers")

async def log_action(action: str, user_id: int, details: str = "", **extra):
    """Log moderation actions via logging module (centralized LoggingCog handles Discord output)."""
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    logger.info("[%s] %s - User: %s - %s", timestamp, action, user_id, details)


def parse_duration(text: str) -> Optional[timedelta]:
    """Parse a duration string like '1d 2h 30m' into a timedelta.
    
    Supports: d (days), h (hours), m (minutes), s (seconds).
    Returns None if the format is invalid.
    """
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


def find_channel_by_name(guild: discord.Guild, *keywords: str) -> Optional[discord.TextChannel]:
    """Find the first text channel whose name contains any of the given keywords.
    
    Example: find_channel_by_name(guild, "appeal", "mod", "staff")
    """
    for channel in guild.text_channels:
        name = channel.name.lower()
        if any(kw.lower() in name for kw in keywords):
            return channel
    return None


async def safe_interaction_reply(
    interaction: discord.Interaction,
    *,
    content: str | None = None,
    embed: discord.Embed | None = None,
    embeds: list[discord.Embed] | None = None,
    view: discord.ui.View | None = None,
    ephemeral: bool = False,
) -> Optional[discord.Message]:
    """Reply to a Discord interaction without ever crashing on `10062`.

    Automatically picks the correct API based on the interaction's state:
    - Not yet acknowledged -> ``interaction.response.send_message``
    - Already deferred/responded -> ``interaction.followup.send``

    Handles (logs, never re-raises):
    - ``discord.NotFound`` (10062 Unknown interaction - token expired)
    - ``discord.InteractionResponded`` (race between check and send)
    - ``discord.HTTPException`` (rate limits / transient API failures)

    Returns the sent message or ``None`` if the reply could not be delivered.
    """
    send_kwargs: dict[str, Any] = {}
    if content is not None:
        send_kwargs["content"] = content
    if embed is not None:
        send_kwargs["embed"] = embed
    if embeds is not None:
        send_kwargs["embeds"] = embeds
    if view is not None:
        send_kwargs["view"] = view
    if ephemeral:
        send_kwargs["ephemeral"] = True

    try:
        if not interaction.response.is_done():
            return await interaction.response.send_message(**send_kwargs)
        return await interaction.followup.send(**send_kwargs)
    except discord.NotFound:
        # The interaction token expired before we could respond (error 10062).
        logger.warning(
            "Interaction %s expired before a reply could be sent (error 10062).",
            interaction.id,
        )
    except discord.InteractionResponded:
        # Race: the interaction was acknowledged between our check and the send.
        try:
            return await interaction.followup.send(**send_kwargs)
        except discord.NotFound:
            logger.warning(
                "Interaction %s expired before a followup could be sent (error 10062).",
                interaction.id,
            )
        except discord.HTTPException as e:
            logger.error("safe_interaction_reply followup failed: %s", e)
    except discord.HTTPException as e:
        logger.error(
            "safe_interaction_reply failed for interaction %s: %s",
            interaction.id,
            e,
        )
    return None


async def safe_send(
    ctx_or_interaction: commands.Context | discord.Interaction,
    *,
    content: str | None = None,
    embed: discord.Embed | None = None,
    view: discord.ui.View | None = None,
    ephemeral: bool = False,
) -> Optional[discord.Message]:
    """Unified reply helper for hybrid commands.

    Works with both prefix (ctx.send) and slash (interaction response/followup) flows.
    Interaction flows are routed through :func:`safe_interaction_reply`, so an
    expired interaction (10062) can never raise.
    """
    send_kwargs: dict[str, Any] = {}
    if content is not None:
        send_kwargs["content"] = content
    if embed is not None:
        send_kwargs["embed"] = embed
    if view is not None:
        send_kwargs["view"] = view

    interaction = getattr(ctx_or_interaction, "interaction", ctx_or_interaction)
    if isinstance(interaction, discord.Interaction):
        # Interaction-based reply (slash / hybrid invoked via slash).
        message = await safe_interaction_reply(
            interaction, **send_kwargs, ephemeral=ephemeral
        )
        if message is not None:
            return message

    if isinstance(ctx_or_interaction, commands.Context):
        try:
            return await ctx_or_interaction.send(**send_kwargs)
        except Exception as e:
            logger.warning("safe_send ctx.send failed: %s", e)
    return None


def is_moderator(
    user: discord.Member | discord.User,
    guild: discord.Guild,
    *,
    mod_role_id: Optional[int] = None,
    additional_user_ids: Optional[set[int]] = None,
) -> bool:
    """Check if a user has moderator permissions.
    
    Returns True if the user:
    - Has a role matching mod_role_id, OR
    - Is in additional_user_ids, OR
    - Has MANAGE_MESSAGES or ADMINISTRATOR permissions.
    """
    if not isinstance(user, discord.Member):
        return False
    
    allowed: set[int] = set(additional_user_ids or ())
    if mod_role_id:
        role = guild.get_role(mod_role_id)
        if role:
            allowed.add(role.id)
    
    return (
        any(r.id in allowed for r in user.roles)
        or user.guild_permissions.manage_messages
        or user.guild_permissions.administrator
    )


def register_mod_action(bot, guild_id: int, user_id: int, moderator_id: int, reason: str, action_type: str, source=None):
    """Tell the LoggingCog who really performed a moderation action.

    Called by moderation commands BEFORE the Discord API call so the logging
    event listener attributes the log entry to the actual command invoker
    instead of the bot (Discord audit logs show the bot application for
    API-performed actions). `source` is an optional context flag (e.g. "appeal")
    describing how the action happened.
    """
    logging_cog = bot.get_cog("LoggingCog")
    if logging_cog and hasattr(logging_cog, "register_command_action"):
        logging_cog.register_command_action(guild_id, user_id, moderator_id, reason, action_type, source=source)


def discard_mod_action(bot, guild_id: int, user_id: int, action_type: str):
    """Remove a pending moderation action (e.g. after the API call failed)."""
    logging_cog = bot.get_cog("LoggingCog")
    if logging_cog and hasattr(logging_cog, "discard_command_action"):
        logging_cog.discard_command_action(guild_id, user_id, action_type)