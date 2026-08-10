import asyncio
import logging

import discord
from discord.ext import commands

from config import (
    HELP_FORUM_ID,
    HELP_NOTIFY_TARGET_CHANNEL_ID,
    HELP_MODERATOR_ROLE_ID,
    MAIN_GUILD_ID,
    HELP_GUIDE_CHANNEL_ID,
)

logger = logging.getLogger(__name__)


class HelpThreadNotification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.source_forum_id = HELP_FORUM_ID
        self.target_channel_id = HELP_NOTIFY_TARGET_CHANNEL_ID

        # Only members with this role can manually trigger notifications.
        self.moderator_role_id = HELP_MODERATOR_ROLE_ID

    async def _get_starter_message(self, thread: discord.Thread) -> discord.Message | None:
        # Slight delay to ensure message is fully committed/available via API
        await asyncio.sleep(1)

        starter_message = thread.starter_message

        # If not cached, try to fetch the starter message
        if not starter_message:
            try:
                # For forum channels, the starter message ID is usually the thread ID
                starter_message = await thread.fetch_message(thread.id)
            except discord.NotFound:
                # Fallback: fetch the first message in the thread
                async for msg in thread.history(limit=1, oldest_first=True):
                    starter_message = msg
                    break

        return starter_message

    def _build_notification_embed(
        self, thread: discord.Thread, starter_message: discord.Message
    ) -> discord.Embed:
        description = starter_message.content or "*No text content provided.*"

        embed = discord.Embed(
            title=f"New Help Thread: {thread.name}",
            description=description,
            color=0x5865F2,
            url=thread.jump_url,
        )

        embed.set_author(
            name=starter_message.author.display_name,
            icon_url=starter_message.author.display_avatar.url,
        )

        # Handle attachments (images)
        if starter_message.attachments:
            for attachment in starter_message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    embed.set_image(url=attachment.url)
                    break

        # Add tags if present
        if hasattr(thread, "applied_tags") and thread.applied_tags:
            tag_names = [tag.name for tag in thread.applied_tags]
            if tag_names:
                embed.add_field(name="Tags", value=", ".join(tag_names), inline=False)

        embed.add_field(
            name="Go to Thread",
            value=f"[Click here to help]({thread.jump_url})",
            inline=False,
        )

        return embed

    async def _get_target_channel(self) -> discord.abc.Messageable | None:
        target_channel = self.bot.get_channel(self.target_channel_id)
        if target_channel:
            return target_channel

        try:
            return await self.bot.fetch_channel(self.target_channel_id)
        except discord.NotFound:
            logger.error(
                f"Target notification channel {self.target_channel_id} not found."
            )
            return None

    def _has_moderator_role(self, member: discord.Member) -> bool:
        return any(role.id == self.moderator_role_id for role in member.roles)

    @commands.command(name="needhelp")
    @commands.guild_only()
    async def needhelp(self, ctx: commands.Context):
        """Manually ping the help channel with an embed of this forum post.

        This command is prefix-only and can only be used inside threads under the
        configured forum channel, by members with the configured moderator role.
        """

        if not isinstance(ctx.author, discord.Member) or not self._has_moderator_role(
            ctx.author
        ):
            await ctx.reply(
                "You don't have permission to use this command.",
                mention_author=False,
            )
            return

        if not isinstance(ctx.channel, discord.Thread):
            await ctx.reply(
                "Use this command inside a help forum post (thread).",
                mention_author=False,
            )
            return

        thread: discord.Thread = ctx.channel
        if thread.parent_id != self.source_forum_id:
            await ctx.reply(
                "This command can only be used in the configured help forum channel.",
                mention_author=False,
            )
            return

        try:
            starter_message = await self._get_starter_message(thread)
            if not starter_message:
                logger.warning(
                    f"Could not retrieve starter message for thread {thread.id} in channel {thread.parent_id}"
                )
                await ctx.reply(
                    "Couldn't find the starter message for this post.",
                    mention_author=False,
                )
                return

            embed = self._build_notification_embed(thread, starter_message)
            target_channel = await self._get_target_channel()
            if not target_channel:
                await ctx.reply(
                    "Configured help ping channel was not found.",
                    mention_author=False,
                )
                return

            await target_channel.send(
                content=(
                    f"@here There's a New Help Forum(<#{self.source_forum_id}>), Do check if u can help"
                ),
                embed=embed,
            )
            logger.info(
                f"Manual help thread notification sent for thread {thread.id} by {ctx.author.id}"
            )

            await thread.send(
                "Thanks For Using our Help Forums."
                f"I have pinged help for you in <#{self.target_channel_id}> ! Please wait a few minutes. "
                f"Make sure to check https://discord.com/channels/{MAIN_GUILD_ID}/{HELP_GUIDE_CHANNEL_ID} to know more about how to ask good questions and get help easily."
            )

        except Exception as e:
            logger.error(
                f"Error in manual help thread notification for thread {thread.id}: {e}",
                exc_info=True,
            )
            await ctx.reply(
                "Something went wrong while sending the notification.",
                mention_author=False,
            )

    # NOTE: Automatic pings on new forum posts have been intentionally removed
    # to prevent spam. Use the prefix command ?needhelp instead.


async def setup(bot):
    await bot.add_cog(HelpThreadNotification(bot))
