# Cog to manage threads and posts in a Discord server
import asyncio
import sqlite3
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands

from utils.database import DATABASE_NAME
from utils.embeds import create_error_embed, create_success_embed
from config import STAFF_ROLE_ID, ADMIN_BYPASS_ROLE_ID


class ThreadCloser(commands.Cog):
    """Cog to manage threads and posts in a Discord server.

    Extended: if used inside a ticket channel, it closes the ticket (transcript + delete).
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_thread(self, channel) -> Optional[discord.Thread]:
        """Helper to check if channel is a thread."""
        return channel if isinstance(channel, discord.Thread) else None

    async def _resolve_thread(
        self, ctx: commands.Context, thread_id: Optional[int] = None
    ) -> Optional[discord.Thread]:
        """Resolve a thread from current channel or by ID."""
        if thread_id is None:
            thread = self._get_thread(ctx.channel)
            if thread is None:
                await ctx.reply(
                    "❌ Please provide a thread ID or run this command inside a thread."
                )
                return None
            return thread
        else:
            thread = None
            if ctx.guild is not None:
                try:
                    thread = getattr(ctx.guild, "get_thread", lambda _id: None)(
                        thread_id
                    )
                except Exception:
                    thread = None
            if thread is None:
                thread = self.bot.get_channel(thread_id)
            if thread is None or not isinstance(thread, discord.Thread):
                await ctx.reply("❌ Thread not found or invalid ID.")
                return None
            return thread

    async def _is_ticket_thread(
        self, thread: discord.Thread
    ) -> tuple[bool, Optional[dict]]:
        """Check if thread is a ticket and return ticket info"""
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT ticket_id, user_id, category FROM tickets WHERE ticket_thread_id = ? AND status = "open"',
                (thread.id,),
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                ticket_id, user_id, category = result
                return True, {
                    "ticket_id": ticket_id,
                    "user_id": user_id,
                    "category": category,
                }
            return False, None
        except Exception:
            return False, None

    async def _close_ticket_thread(
        self, ctx: commands.Context, thread: discord.Thread, ticket_info: dict
    ):
        """Close a ticket thread"""
        ticket_id = ticket_info["ticket_id"]
        user_id = ticket_info["user_id"]
        category = ticket_info["category"]

        # Check permissions (ticket owner or staff)
        has_permission = False
        if isinstance(ctx.author, discord.Member):
            allowed_role_ids = {STAFF_ROLE_ID, ADMIN_BYPASS_ROLE_ID}
            tickets_cog = self.bot.get_cog("Tickets")
            if tickets_cog and ctx.guild:
                for role_getter in (
                    tickets_cog._get_support_team_role,
                    tickets_cog._get_report_team_role,
                    tickets_cog._get_partner_team_role,
                ):
                    try:
                        role = role_getter(ctx.guild)
                        if role:
                            allowed_role_ids.add(role.id)
                    except Exception:
                        pass
            has_permission = (
                ctx.author.id == user_id
                or any(r.id in allowed_role_ids for r in ctx.author.roles)
                or ctx.author.guild_permissions.administrator
            )
        elif ctx.author.id == user_id:
            has_permission = True

        if not has_permission:
            await ctx.reply("❌ Only the ticket owner or staff can close this ticket.")
            return

        # Delegate to ticket cog's full force-close flow when available so we get logs, transcript, and DM
        tickets_cog = self.bot.get_cog("Tickets")
        if tickets_cog:
            await tickets_cog.force_close_ticket(
                ctx,
                ticket_id,
                reason="Closed via ?close command",
                announce_in_channel=False,
            )
            return

        # Fallback: minimal close if ticket cog is unavailable
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE tickets SET status = "closed", closed_at = CURRENT_TIMESTAMP, close_reason = ? WHERE ticket_id = ?',
            (f"Closed by {ctx.author} (via ?close)", ticket_id),
        )
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="Ticket Closed",
            description=f"This ticket has been closed by {ctx.author.mention}",
            color=0xFF0000,
        )
        embed.add_field(
            name="Next Steps",
            value=(
                "A transcript has been saved.\n"
                "This thread will be archived and locked shortly."
            ),
            inline=False,
        )
        embed.set_footer(text=f"Ticket ID: {ticket_id} | Closed via ?close command")
        embed.timestamp = datetime.now(timezone.utc)

        await ctx.send(embed=embed)

        await asyncio.sleep(10)
        try:
            await thread.edit(archived=True, locked=True)
            print(
                f"[Thread] Closed ticket thread '{thread.name}' (ID: {thread.id}, Ticket: #{ticket_id}) by {ctx.author}"
            )
        except Exception as e:
            print(f"[Thread] Error closing ticket thread {thread.id}: {e}")

    async def _lookup_ticket_by_channel(self, channel_id: int) -> Optional[int]:
        """Look up an open ticket by channel ID (ticket_channel_id)."""
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT ticket_id, user_id FROM tickets WHERE ticket_channel_id = ? AND status = "open"',
                (channel_id,),
            )
            row = cursor.fetchone()
            conn.close()
            return row
        except Exception as e:
            print(f"[Thread] Error looking up ticket by channel: {e}")
            return None

    @commands.command(
        name="close",
        aliases=["close_thread", "archive"],
        help="Close (archive) a thread or close a ticket channel.",
    )
    async def close_thread(
        self, ctx: commands.Context, thread_id: Optional[int] = None
    ):
        """Close a thread (archive) or, if run in a ticket channel, close the ticket (transcript + delete)."""

        channel = ctx.channel

        # Ticket channels: allow ?close inside the ticket channel to close/delete it.
        if thread_id is None:
            # Check if this is a ticket text channel
            if isinstance(channel, discord.TextChannel):
                ticket_row = await self._lookup_ticket_by_channel(channel.id)
                if ticket_row:
                    ticket_id, user_id = ticket_row
                    tickets_cog = self.bot.get_cog("Tickets")
                    # Permission check: ticket owner, staff role, or admin
                    has_perm = False
                    if isinstance(ctx.author, discord.Member):
                        allowed_role_ids = {STAFF_ROLE_ID, ADMIN_BYPASS_ROLE_ID}
                        # Include configured roles from Tickets cog if available
                        if tickets_cog and ctx.guild:
                            for role_getter in (
                                tickets_cog._get_support_team_role,
                                tickets_cog._get_report_team_role,
                                tickets_cog._get_partner_team_role,
                            ):
                                try:
                                    role = role_getter(ctx.guild)
                                    if role:
                                        allowed_role_ids.add(role.id)
                                except Exception:
                                    pass
                        has_perm = (
                            ctx.author.id == user_id
                            or any(
                                r.id in allowed_role_ids
                                for r in ctx.author.roles
                            )
                            or ctx.author.guild_permissions.administrator
                        )
                    elif ctx.author.id == user_id:
                        has_perm = True
                    if not has_perm:
                        await ctx.reply("❌ Only the ticket owner or staff can close this ticket.")
                        return
                    if tickets_cog:
                        await tickets_cog.force_close_ticket(
                            ctx,
                            ticket_id,
                            reason="Closed via ?close command",
                            announce_in_channel=False,
                            announce_in_ticket=True,
                        )
                        return
                    await ctx.reply("❌ Ticket system is not available right now.")
                    return
            # Check if this is a ticket thread (legacy)
            elif isinstance(channel, discord.Thread):
                is_ticket, ticket_info = await self._is_ticket_thread(channel)
                if is_ticket and ticket_info:
                    await self._close_ticket_thread(ctx, channel, ticket_info)
                    return

        thread = await self._resolve_thread(ctx, thread_id)
        if thread is None:
            return

        # Check if this is a ticket thread (legacy)
        is_ticket, ticket_info = await self._is_ticket_thread(thread)
        if is_ticket and ticket_info:
            await self._close_ticket_thread(ctx, thread, ticket_info)
            return

        # Handle regular thread closure
        # Check permissions: only mods (manage_threads) or original poster can close
        is_mod = False
        if isinstance(ctx.author, discord.Member):
            is_mod = ctx.author.guild_permissions.manage_threads

        is_original_poster = thread.owner_id == ctx.author.id

        if not (is_mod or is_original_poster):
            await ctx.reply(
                "❌ Only moderators or the thread creator can close this thread."
            )
            return

        try:
            # Create embed for close message
            embed = discord.Embed(
                title="Thread Closed",
                description="This thread has been closed and archived.",
                color=discord.Color.red(),
            )
            embed.add_field(name="Thread Name", value=thread.name, inline=False)
            embed.add_field(name="Closed By", value=ctx.author.mention, inline=True)
            embed.set_footer(
                text=f"Closed at {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )

            # Send close message first
            await ctx.send(embed=embed)

            # Small delay to ensure message is sent before archiving
            await asyncio.sleep(0.5)

            # Then archive the thread (so bot message doesn't reopen it)
            await thread.edit(archived=True)
            print(
                f"[Thread] Archived '{thread.name}' (ID: {thread.id}) by {ctx.author}"
            )
        except discord.Forbidden:
            await ctx.reply("❌ I do not have permission to archive this thread.")
        except Exception as e:
            await ctx.reply(f"❌ Error archiving thread: {e}")
            print(f"[Thread] Error archiving {thread.id}: {e}")

    @commands.command(
        name="pin", help="Pin a message in thread/post or current channel."
    )
    @commands.has_permissions(manage_messages=True)
    async def pin_message(
        self, ctx: commands.Context, message_id: Optional[int] = None
    ):
        """Pin a message by ID or reply to message. If message_id not provided, reply to a message to pin it."""
        try:
            message = None
            if message_id is not None:
                try:
                    message = await ctx.channel.fetch_message(message_id)
                except discord.NotFound:
                    await ctx.reply(f"❌ Message with ID {message_id} not found.")
                    return
            elif ctx.message.reference is not None:
                try:
                    ref_msg_id = ctx.message.reference.message_id
                    if ref_msg_id:
                        message = await ctx.channel.fetch_message(ref_msg_id)
                except discord.NotFound:
                    await ctx.reply("❌ Referenced message not found.")
                    return
            else:
                await ctx.reply(
                    "❌ Please provide a message ID or reply to a message to pin."
                )
                return
            if message is None:
                await ctx.reply("❌ Message could not be resolved.")
                return
            await message.pin()
            channel_str = getattr(
                ctx.channel, "mention", f"#{getattr(ctx.channel, 'name', 'unknown')}"
            )
            await ctx.reply(f"📌 Message pinned in {channel_str}.")
            channel_name = getattr(ctx.channel, "name", "unknown")
            if message:
                print(
                    f"[Thread] Pinned message {message.id} in {channel_name} by {ctx.author}"
                )
        except discord.Forbidden:
            await ctx.reply(
                "❌ I do not have permission to pin messages in this channel."
            )
        except Exception as e:
            await ctx.reply(f"❌ Error pinning message: {e}")

    @commands.command(
        name="unpin", help="Unpin a message in thread/post or current channel."
    )
    @commands.has_permissions(manage_messages=True)
    async def unpin_message(
        self, ctx: commands.Context, message_id: Optional[int] = None
    ):
        """Unpin a message by ID or reply to message. If message_id not provided, reply to a pinned message to unpin it."""
        try:
            message = None
            if message_id is not None:
                try:
                    message = await ctx.channel.fetch_message(message_id)
                except discord.NotFound:
                    await ctx.reply(f"❌ Message with ID {message_id} not found.")
                    return
            elif ctx.message.reference is not None:
                try:
                    ref_msg_id = ctx.message.reference.message_id
                    if ref_msg_id:
                        message = await ctx.channel.fetch_message(ref_msg_id)
                except discord.NotFound:
                    await ctx.reply("❌ Referenced message not found.")
                    return
            else:
                await ctx.reply(
                    "❌ Please provide a message ID or reply to a message to unpin."
                )
                return
            if message is None:
                await ctx.reply("❌ Message could not be resolved.")
                return
            await message.unpin()
            channel_str = getattr(
                ctx.channel, "mention", f"#{getattr(ctx.channel, 'name', 'unknown')}"
            )
            await ctx.reply(f"📌 Message unpinned from {channel_str}.")
            channel_name = getattr(ctx.channel, "name", "unknown")
            if message:
                print(
                    f"[Thread] Unpinned message {message.id} in {channel_name} by {ctx.author}"
                )
        except discord.Forbidden:
            await ctx.reply(
                "❌ I do not have permission to unpin messages in this channel."
            )
        except Exception as e:
            await ctx.reply(f"❌ Error unpinning message: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ThreadCloser(bot))
