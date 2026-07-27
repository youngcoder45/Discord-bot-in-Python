import asyncio
from datetime import datetime, timezone
import logging

logger = logging.getLogger("codeverse.helpers")

async def log_action(action: str, user_id: int, details: str = "", **extra):
    """Log moderation actions via logging module (centralized LoggingCog handles Discord output)."""
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    logger.info("[%s] %s - User: %s - %s", timestamp, action, user_id, details)