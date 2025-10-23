import random
import re
import requests
import discord
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict

def get_random_quote(quotes: List[str]) -> str:
    """Get a random motivational/programming quote"""
    return random.choice(quotes)

def get_random_question(questions: List[Dict]) -> Dict:
    """Get a random programming question"""
    return random.choice(questions)

def create_embed(title: str, description: str = "", color: discord.Color = discord.Color.blue()) -> discord.Embed:
    """Create a basic embed with consistent styling"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(tz=timezone.utc)
    )
    embed.set_footer(text="CodeVerse Bot")
    return embed

def create_success_embed(title: str, description: str = "") -> discord.Embed:
    """Create a success embed (green)"""
    return create_embed(title, description, discord.Color.green())

def create_error_embed(title: str, description: str = "") -> discord.Embed:
    """Create an error embed (red)"""
    return create_embed(title, description, discord.Color.red())

def create_warning_embed(title: str, description: str = "") -> discord.Embed:
    """Create a warning embed (yellow)"""
    return create_embed(title, description, discord.Color.yellow())

def create_info_embed(title: str, description: str = "") -> discord.Embed:
    """Create an info embed (blue)"""
    return create_embed(title, description, discord.Color.blue())

async def fetch_programming_meme() -> str:
    """Fetch a random programming meme from an API"""
    try:
        # Using programming memes subreddit API
        response = requests.get(
            "https://meme-api.herokuapp.com/gimme/ProgrammerHumor",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('url', '')
    except Exception:
        pass
    
    # Fallback memes if API fails
    fallback_memes = [
        "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
        "There are only 10 types of people in the world: those who understand binary and those who don't.",
        "99 little bugs in the code, 99 little bugs. Take one down, patch it around, 117 little bugs in the code.",
        "A SQL query goes into a bar, walks up to two tables and asks: 'Can I join you?'",
        "How many programmers does it take to change a light bulb? None, that's a hardware problem."
    ]
    return random.choice(fallback_memes)

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent abuse"""
    # Remove potential mentions and excessive whitespace
    text = re.sub(r'@(everyone|here)', '[at]\\1', text)
    text = re.sub(r'<@[!&]?\d+>', '[mention]', text)
    text = ' '.join(text.split())  # Remove excessive whitespace
    
    return text[:max_length] if len(text) > max_length else text

async def log_action(action: str, user_id: int, details: str = "", **extra):
    """Log moderation actions - redirects to LoggingCog if available"""
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {action} - User: {user_id} - {details}"
    print(log_entry)  # Fallback print if logging cog not available
    
    # Try to use LoggingCog if available
    import inspect
    current_frame = inspect.currentframe()
    try:
        # Find the bot instance to access the logging cog
        if current_frame and current_frame.f_back and hasattr(current_frame.f_back, 'f_locals'):
            # Look for the bot in the calling function's locals
            for key, value in current_frame.f_back.f_locals.items():
                if hasattr(value, 'get_cog'):
                    bot = value
                    # Try the new cog name first
                    logging_cog = bot.get_cog('LoggingCog')
                    if not logging_cog:
                        # Try legacy name if new name not found
                        logging_cog = bot.get_cog('LoggingCog')
                        
                    if logging_cog:
                        # Extract guild_id and moderator_id if available
                        guild_id = extra.get('guild_id', 0)
                        moderator_id = extra.get('moderator_id', 0)
                        asyncio.create_task(logging_cog.log_mod_action(
                            action_type=action,
                            user_id=user_id,
                            guild_id=guild_id,
                            moderator_id=moderator_id,
                            reason=details,
                            **extra
                        ))
                    break
    except Exception as e:
        print(f"Error redirecting to LoggingCog: {e}")
    finally:
        del current_frame  # Avoid reference cycles