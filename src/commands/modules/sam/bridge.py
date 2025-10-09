"""
SAM to CodeVerse Bot Bridge

This module acts as a bridge between the SAM module and the CodeVerse bot,
allowing SAM features to interact with the bot's core systems like logging.
"""
import discord
from discord.ext import commands
import os

from .public import logging_api

async def log_consumer(bot: commands.Bot, action: logging_api.LogAction):
    """
    Consumes a LogAction from the SAM logging_api and sends it to the
    CodeVerse bot's server log channel.
    """
    log_channel_id = os.getenv('SERVER_LOGS_CHANNEL_ID')
    if not log_channel_id:
        return

    try:
        log_channel = await bot.fetch_channel(int(log_channel_id))
    except (discord.NotFound, discord.Forbidden, ValueError):
        return

    embed = discord.Embed(
        title=action.title,
        description=action.description,
        color=discord.Color.blue(),
        timestamp=action.timestamp
    )

    for field in action.fields:
        embed.add_field(name=field.name, value=field.value, inline=field.inline)

    if isinstance(log_channel, discord.TextChannel):
        await log_channel.send(embed=embed)

def connect_log_consumer(bot: commands.Bot):
    """
    Connects the log consumer to the SAM logging API.
    """
    # We use a lambda to pass the bot instance to the consumer
    consumer_with_bot = lambda action: log_consumer(bot, action)
    
    # Store it on the function so we can disconnect it later if needed
    connect_log_consumer.consumer = consumer_with_bot
    
    logging_api.connect(consumer_with_bot)

def disconnect_log_consumer():
    """
    Disconnects the log consumer from the SAM logging API.
    """
    if hasattr(connect_log_consumer, "consumer"):
        logging_api.disconnect(connect_log_consumer.consumer)

