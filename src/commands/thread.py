# Cog to manage threads and posts in a Discord server
import discord
from discord.ext import commands
from typing import Optional
import asyncio


class ThreadCloser(commands.Cog):
    """Cog to manage threads and posts in a Discord server."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_thread(self, channel) -> Optional[discord.Thread]:
        """Helper to check if channel is a thread."""
        return channel if isinstance(channel, discord.Thread) else None

    async def _resolve_thread(self, ctx: commands.Context, thread_id: Optional[int] = None) -> Optional[discord.Thread]:
        """Resolve a thread from current channel or by ID."""
        if thread_id is None:
            thread = self._get_thread(ctx.channel)
            if thread is None:
                await ctx.reply("Please provide a thread ID or run this command inside a thread.")
            return thread
        else:
            thread = None
            if ctx.guild is not None:
                try:
                    thread = getattr(ctx.guild, 'get_thread', lambda _id: None)(thread_id)
                except Exception:
                    thread = None
            if thread is None:
                thread = self.bot.get_channel(thread_id)
            if thread is None or not isinstance(thread, discord.Thread):
                await ctx.reply("Thread not found or invalid ID.")
                return None
            return thread

    @commands.command(name="close", aliases=["close_thread", "archive"], help="Close (archive) a thread.")
    async def close_thread(self, ctx: commands.Context, thread_id: Optional[int] = None):
        """Close (archive) a thread by ID or in current thread. Only mods and original poster can close."""
        thread = await self._resolve_thread(ctx, thread_id)
        if thread is None:
            return
        
        # Check permissions: only mods (manage_threads) or original poster can close
        is_mod = False
        if isinstance(ctx.author, discord.Member):
            is_mod = ctx.author.guild_permissions.manage_threads
        
        is_original_poster = thread.owner_id == ctx.author.id
        
        if not (is_mod or is_original_poster):
            await ctx.reply("❌ Only moderators or the thread creator can close this thread.")
            return
        
        try:
            # Create embed for close message
            embed = discord.Embed(
                title="🔒 Thread Closed",
                description=f"This thread has been closed and archived.",
                color=discord.Color.red()
            )
            embed.add_field(name="Thread Name", value=thread.name, inline=False)
            embed.add_field(name="Closed By", value=ctx.author.mention, inline=True)
            embed.set_footer(text=f"Closed at {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            # Send close message first
            await ctx.send(embed=embed)
            
            # Small delay to ensure message is sent before archiving
            await asyncio.sleep(0.5)
            
            # Then archive the thread (so bot message doesn't reopen it)
            await thread.edit(archived=True)
            print(f"[Thread] Archived '{thread.name}' (ID: {thread.id}) by {ctx.author}")
        except discord.Forbidden:
            await ctx.reply("❌ I do not have permission to archive this thread.")
        except Exception as e:
            await ctx.reply(f"❌ Error archiving thread: {e}")
            print(f"[Thread] Error archiving {thread.id}: {e}")

    @commands.command(name="pin", help="Pin a message in thread/post or current channel.")
    @commands.has_permissions(manage_messages=True)
    async def pin_message(self, ctx: commands.Context, message_id: Optional[int] = None):
        """Pin a message by ID or reply to message. If message_id not provided, reply to a message to pin it."""
        try:
            message = None
            if message_id is not None:
                try:
                    message = await ctx.channel.fetch_message(message_id)
                except discord.NotFound:
                    await ctx.reply(f" Message with ID {message_id} not found.")
                    return
            elif ctx.message.reference is not None:
                try:
                    ref_msg_id = ctx.message.reference.message_id
                    if ref_msg_id:
                        message = await ctx.channel.fetch_message(ref_msg_id)
                except discord.NotFound:
                    await ctx.reply(" Referenced message not found.")
                    return
            else:
                await ctx.reply(" Please provide a message ID or reply to a message to pin.")
                return
            if message is None:
                await ctx.reply(" Message could not be resolved.")
                return
            await message.pin()
            channel_str = getattr(ctx.channel, 'mention', f"#{getattr(ctx.channel, 'name', 'unknown')}")
            await ctx.reply(f" Message pinned in {channel_str}.")
            channel_name = getattr(ctx.channel, 'name', 'unknown')
            if message:
                print(f"[Thread] Pinned message {message.id} in {channel_name} by {ctx.author}")
        except discord.Forbidden:
            await ctx.reply(" I do not have permission to pin messages in this channel.")
        except Exception as e:
            await ctx.reply(f" Error pinning message: {e}")

    @commands.command(name="unpin", help="Unpin a message in thread/post or current channel.")
    @commands.has_permissions(manage_messages=True)
    async def unpin_message(self, ctx: commands.Context, message_id: Optional[int] = None):
        """Unpin a message by ID or reply to message. If message_id not provided, reply to a pinned message to unpin it."""
        try:
            message = None
            if message_id is not None:
                try:
                    message = await ctx.channel.fetch_message(message_id)
                except discord.NotFound:
                    await ctx.reply(f" Message with ID {message_id} not found.")
                    return
            elif ctx.message.reference is not None:
                try:
                    ref_msg_id = ctx.message.reference.message_id
                    if ref_msg_id:
                        message = await ctx.channel.fetch_message(ref_msg_id)
                except discord.NotFound:
                    await ctx.reply(" Referenced message not found.")
                    return
            else:
                await ctx.reply(" Please provide a message ID or reply to a message to unpin.")
                return
            if message is None:
                await ctx.reply(" Message could not be resolved.")
                return
            await message.unpin()
            channel_str = getattr(ctx.channel, 'mention', f"#{getattr(ctx.channel, 'name', 'unknown')}")
            await ctx.reply(f" Message unpinned from {channel_str}.")
            channel_name = getattr(ctx.channel, 'name', 'unknown')
            if message:
                print(f"[Thread] Unpinned message {message.id} in {channel_name} by {ctx.author}")
        except discord.Forbidden:
            await ctx.reply(" I do not have permission to unpin messages in this channel.")
        except Exception as e:
            await ctx.reply(f"❌ Error unpinning message: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ThreadCloser(bot))