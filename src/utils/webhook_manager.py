import discord
import logging
import asyncio
from typing import Optional, Dict

logger = logging.getLogger("codeverse.webhook_manager")

WEBHOOK_NAME = "CodeVerse Logger"

class WebhookManager:
    """
    Manages webhooks for logging channels to avoid rate limits and improve reliability.
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        # Cache mapping channel_id -> webhook_url
        self._webhook_cache: Dict[int, str] = {}
        # Lock to prevent race conditions during webhook creation per channel
        self._locks: Dict[int, asyncio.Lock] = {}

    def _get_lock(self, channel_id: int) -> asyncio.Lock:
        if channel_id not in self._locks:
            self._locks[channel_id] = asyncio.Lock()
        return self._locks[channel_id]

    async def get_webhook(self, channel: discord.TextChannel) -> Optional[discord.Webhook]:
        """
        Retrieves a webhook for the given channel. 
        Checks cache -> fetches existing -> creates new.
        """
        if self.bot.user is None:
            return None

        if channel.id in self._webhook_cache:
            return discord.Webhook.from_url(self._webhook_cache[channel.id], client=self.bot)

        async with self._get_lock(channel.id):
            # Double check cache after acquiring lock
            if channel.id in self._webhook_cache:
                return discord.Webhook.from_url(self._webhook_cache[channel.id], client=self.bot)

            try:
                # Fetch existing webhooks
                webhooks = await channel.webhooks()
                webhook = discord.utils.get(webhooks, name=WEBHOOK_NAME)

                if webhook:
                    self._webhook_cache[channel.id] = webhook.url
                    return webhook

                # Create new webhook if not found and we have permissions
                if channel.permissions_for(channel.guild.me).manage_webhooks:
                    # We can use the bot's avatar as the default webhook avatar
                    avatar = await self.bot.user.display_avatar.read()
                    webhook = await channel.create_webhook(
                        name=WEBHOOK_NAME, 
                        avatar=avatar,
                        reason="Logging system initialization"
                    )
                    self._webhook_cache[channel.id] = webhook.url
                    return webhook
                else:
                    logger.warning(f"Missing MANAGE_WEBHOOKS permission in {channel.name} ({channel.id})")
                    return None


            except discord.Forbidden:
                logger.warning(f"Forbidden: Cannot manage webhooks in {channel.name} ({channel.id})")
                return None
            except Exception as e:
                logger.error(f"Failed to get/create webhook for channel {channel.id}: {e}")
                return None

    async def send(self, channel: discord.TextChannel, embed: discord.Embed) -> bool:
        """
        Sends an embed via webhook. Falls back to channel.send on failure.
        Returns True if successful, False otherwise.
        """
        if self.bot.user is None:
            # Fallback if bot user info isn't available
            try:
                await channel.send(embed=embed)
                return True
            except Exception as e:
                logger.error(f"Fallback send failed for {channel.id}: {e}")
                return False

        webhook = await self.get_webhook(channel)
        
        if webhook:
            try:
                # wait=True to ensure we catch HTTP errors immediately
                await webhook.send(
                    embed=embed, 
                    username=self.bot.user.display_name, 
                    avatar_url=self.bot.user.display_avatar.url, 
                    wait=True
                )
                return True
            except discord.NotFound:
                # Webhook might have been deleted externally
                logger.info(f"Webhook not found for {channel.id}, invalidating cache.")
                if channel.id in self._webhook_cache:
                    del self._webhook_cache[channel.id]
                
                # Retry once after clearing cache
                webhook = await self.get_webhook(channel)
                if webhook:
                    try:
                        await webhook.send(
                            embed=embed, 
                            username=self.bot.user.display_name, 
                            avatar_url=self.bot.user.display_avatar.url, 
                            wait=True
                        )
                        return True
                    except Exception as e:
                        logger.error(f"Retry webhook send failed for {channel.id}: {e}")
            
            except discord.HTTPException as e:
                if e.status == 429: # Rate limit
                    logger.warning(f"Webhook rate limit hit for {channel.id}, falling back to bot send.")
                else:
                    logger.error(f"Webhook send failed for {channel.id}: {e}")
            except Exception as e:
                 logger.error(f"Webhook send failed for {channel.id}: {e}")
        
        # Fallback to direct bot message
        try:
            await channel.send(embed=embed)
            return True
        except Exception as e:
            logger.error(f"Fallback send failed for {channel.id}: {e}")
            return False
