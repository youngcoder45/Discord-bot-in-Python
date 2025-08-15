import random
import re
import requests
import discord
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
import asyncio

def get_random_quote(quotes: List[str]) -> str:
    """Get a random motivational/programming quote"""
    return random.choice(quotes)

def get_random_question(questions: List[Dict]) -> Dict:
    """Get a random programming question"""
    return random.choice(questions)

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format"""
    if seconds <= 0:
        return "0 seconds"
    
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    
    return ", ".join(parts)

def parse_duration(duration_str: str) -> Optional[int]:
    """Parse duration string (e.g., '1h', '30m', '45s') to seconds"""
    pattern = r'(\d+)([hms])'
    matches = re.findall(pattern, duration_str.lower())
    
    total_seconds = 0
    for amount, unit in matches:
        amount = int(amount)
        if unit == 'h':
            total_seconds += amount * 3600
        elif unit == 'm':
            total_seconds += amount * 60
        elif unit == 's':
            total_seconds += amount
    
    return total_seconds if total_seconds > 0 else None

def extract_user_id_from_mention(mention: str) -> Optional[int]:
    """Extract user ID from mention string"""
    match = re.match(r'<@!?(\d+)>', mention)
    if match:
        return int(match.group(1))
    return None

def create_embed(title: str, description: str = "", color: discord.Color = discord.Color.blue()) -> discord.Embed:
    """Create a basic embed with consistent styling"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(tz=timezone.utc)
    )
    embed.set_footer(text="The CodeVerse Hub", icon_url="https://cdn.discordapp.com/icons/your-server-id/your-icon.png")
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

def get_level_role(level: int) -> str:
    """Get the appropriate role based on user level"""
    if level >= 50:
        return "Elite Member"
    elif level >= 30:
        return "Ultra Active"
    elif level >= 15:
        return "Very Active"
    elif level >= 5:
        return "Active"
    else:
        return "Newcomer"

def get_xp_for_next_level(current_xp: int) -> int:
    """Calculate XP needed for next level"""
    current_level = int((current_xp / 100) ** 0.5) + 1
    next_level_xp = ((current_level) ** 2) * 100
    return next_level_xp - current_xp

async def fetch_programming_meme() -> Optional[str]:
    """Fetch a random programming meme from an API"""
    try:
        # Using programminrmemes subreddit API
        response = requests.get(
            "https://meme-api.herokuapp.com/gimme/ProgrammerHumor",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('url')
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

def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

def paginate_text(text: str, max_length: int = 2000) -> List[str]:
    """Split long text into Discord-friendly chunks"""
    if len(text) <= max_length:
        return [text]
    
    pages = []
    lines = text.split('\n')
    current_page = ""
    
    for line in lines:
        if len(current_page + line + '\n') <= max_length:
            current_page += line + '\n'
        else:
            if current_page:
                pages.append(current_page.strip())
            current_page = line + '\n'
    
    if current_page:
        pages.append(current_page.strip())
    
    return pages

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent abuse"""
    # Remove potential mentions and excessive whitespace
    text = re.sub(r'@(everyone|here)', '[at]\\1', text)
    text = re.sub(r'<@[!&]?\d+>', '[mention]', text)
    text = ' '.join(text.split())  # Remove excessive whitespace
    
    return text[:max_length] if len(text) > max_length else text

async def log_action(action: str, user_id: int, details: str = ""):
    """Log moderation actions (placeholder for future logging system)"""
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {action} - User: {user_id} - {details}"
    print(log_entry)  # For now, just print. Later can be saved to file or database

def create_progress_bar(current: int, maximum: int, length: int = 10) -> str:
    """Create a text-based progress bar"""
    filled = int(length * current / maximum) if maximum > 0 else 0
    bar = "█" * filled + "░" * (length - filled)
    percentage = int(100 * current / maximum) if maximum > 0 else 0
    return f"{bar} {percentage}%"

def get_relative_time(timestamp: datetime) -> str:
    """Get relative time string (e.g., '2 hours ago')"""
    now = datetime.now(tz=timezone.utc)
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"