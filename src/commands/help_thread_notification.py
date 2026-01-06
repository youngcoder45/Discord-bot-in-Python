import discord
from discord.ext import commands
import logging
import asyncio

logger = logging.getLogger(__name__)

class HelpThreadNotification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.source_forum_id = 1388169643234955354
        self.target_channel_id = 1456979344504258570

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        """
        Listen for new threads in the specific help forum.
        When a new thread is created, send a notification embed to the target channel.
        """
        # Check if the thread is in the correct forum channel
        if thread.parent_id != self.source_forum_id:
            return

        # Slight delay to ensure message is fully committed/available via API
        await asyncio.sleep(1)

        try:
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
            
            if not starter_message:
                logger.warning(f"Could not retrieve starter message for thread {thread.id} in channel {thread.parent_id}")
                return

            # Get the description content
            description = starter_message.content
            if not description:
                description = "*No text content provided.*"
            
            # Create the embed
            # Color is black (0x000000)
            embed = discord.Embed(
                title=f"New Help Thread: {thread.name}",
                description=description,
                color=0x000000,
                url=thread.jump_url
            )

            # Set author
            embed.set_author(
                name=starter_message.author.display_name,
                icon_url=starter_message.author.display_avatar.url
            )
            
            # Handle attachments (images)
            # If there are attachments, use the first image found
            if starter_message.attachments:
                for attachment in starter_message.attachments:
                    if attachment.content_type and attachment.content_type.startswith('image/'):
                        embed.set_image(url=attachment.url)
                        break
            
            # Add tags if present
            if hasattr(thread, 'applied_tags') and thread.applied_tags:
                # applied_tags is a list of ForumTag objects
                tag_names = [tag.name for tag in thread.applied_tags]
                if tag_names:
                    embed.add_field(name="Tags", value=", ".join(tag_names), inline=False)

            # Add a field for the link, although the title is also a link
            embed.add_field(
                name="Go to Thread",  
                value=f"[Click here to help]({thread.jump_url})", 
                inline=False
            )
            

            # Get target channel
            target_channel = self.bot.get_channel(self.target_channel_id)
            if not target_channel:
                # Try fetching if not in cache
                try:
                    target_channel = await self.bot.fetch_channel(self.target_channel_id)
                except discord.NotFound:
                    logger.error(f"Target notification channel {self.target_channel_id} not found.")
                    return

            # Send the notification
            await target_channel.send(content="@here There's a New Help Forum(<#1388169643234955354>), Do check if u can help", embed=embed)
            logger.info(f"Sent help thread notification for thread {thread.id}")
            
            # Send confirmation message inside the thread
            await thread.send(
                "Thanks For Using our Help Forums." \
                "I have pinged help for you in <#1456979344504258570> ! Please wait a few minutes. "
                "Make sure to check <#1456009038344093766> to know more about how to ask good questions and get help easily."
            )

        except Exception as e:
            logger.error(f"Error in help thread notification for thread {thread.id}: {e}", exc_info=True)

async def setup(bot):
    await bot.add_cog(HelpThreadNotification(bot))
