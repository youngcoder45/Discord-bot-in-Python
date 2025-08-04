import discord
import json
import random
from datetime import datetime, timedelta
from utils.helpers import create_info_embed, create_success_embed

async def announce_weekly_challenge(bot, channel_id):
    """Announce the weekly coding challenge"""
    if not channel_id:
        print("Weekly challenge channel not configured")
        return
    
    channel = bot.get_channel(channel_id)
    if not channel:
        print(f"Weekly challenge channel {channel_id} not found")
        return
    
    # Load challenges
    try:
        with open('src/data/challenges.json', 'r', encoding='utf-8') as f:
            challenges = json.load(f)
    except FileNotFoundError:
        print("Challenges file not found")
        return
    except json.JSONDecodeError:
        print("Error reading challenges file")
        return
    
    if not challenges:
        print("No challenges available")
        return
    
    # Get a random challenge
    challenge_data = random.choice(challenges)
    
    # Generate challenge ID for tracking
    week_number = datetime.utcnow().isocalendar()[1]
    year = datetime.utcnow().year
    challenge_id = f"challenge_{year}_W{week_number:02d}"
    
    # Calculate deadline (next Sunday 11:59 PM UTC)
    today = datetime.utcnow()
    days_until_sunday = (6 - today.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7  # If today is Sunday, set deadline to next Sunday
    deadline = today + timedelta(days=days_until_sunday)
    deadline = deadline.replace(hour=23, minute=59, second=59, microsecond=0)
    
    # Create embed for staff channel
    embed = discord.Embed(
        title="📋 Weekly Challenge - Staff Review",
        description="A new weekly coding challenge is ready to be announced!",
        color=discord.Color.orange(),
        timestamp=datetime.utcnow()
    )
    
    if isinstance(challenge_data, dict):
        embed.add_field(
            name="🎯 Challenge Title",
            value=challenge_data.get('title', 'Untitled Challenge'),
            inline=False
        )
        
        embed.add_field(
            name="📝 Description",
            value=challenge_data.get('description', 'No description available')[:500] + 
                  ("..." if len(challenge_data.get('description', '')) > 500 else ""),
            inline=False
        )
        
        if 'difficulty' in challenge_data:
            embed.add_field(
                name="🎚️ Difficulty",
                value=challenge_data['difficulty'],
                inline=True
            )
        
        if 'estimated_time' in challenge_data:
            embed.add_field(
                name="⏱️ Estimated Time",
                value=challenge_data['estimated_time'],
                inline=True
            )
        
        if 'category' in challenge_data:
            embed.add_field(
                name="📂 Category",
                value=challenge_data['category'],
                inline=True
            )
        
        if 'requirements' in challenge_data:
            requirements = challenge_data['requirements']
            if isinstance(requirements, list):
                requirements_text = "\n".join([f"• {req}" for req in requirements[:5]])
                if len(requirements) > 5:
                    requirements_text += f"\n• ... and {len(requirements) - 5} more"
            else:
                requirements_text = str(requirements)[:200]
            
            embed.add_field(
                name="📋 Requirements",
                value=requirements_text,
                inline=False
            )
        
        if 'bonus_features' in challenge_data:
            bonus = challenge_data['bonus_features']
            if isinstance(bonus, list):
                bonus_text = "\n".join([f"• {feat}" for feat in bonus[:3]])
                if len(bonus) > 3:
                    bonus_text += f"\n• ... and {len(bonus) - 3} more"
            else:
                bonus_text = str(bonus)[:200]
            
            embed.add_field(
                name="🌟 Bonus Features",
                value=bonus_text,
                inline=False
            )
    else:
        embed.add_field(
            name="📝 Challenge",
            value=str(challenge_data)[:1000] + ("..." if len(str(challenge_data)) > 1000 else ""),
            inline=False
        )
    
    embed.add_field(
        name="📅 Timeline",
        value=f"**Challenge ID:** `{challenge_id}`\n"
              f"**Starts:** {today.strftime('%B %d, %Y at %H:%M UTC')}\n"
              f"**Deadline:** {deadline.strftime('%B %d, %Y at %H:%M UTC')}\n"
              f"**Duration:** {(deadline - today).days} days",
        inline=False
    )
    
    embed.add_field(
        name="🎮 Staff Actions",
        value="• Review the challenge details above\n"
              "• Decide if any modifications are needed\n"
              "• Post the challenge in #coding-challenges when ready\n"
              "• Use `!post-challenge` to announce to the community",
        inline=False
    )
    
    embed.set_footer(
        text=f"Week {week_number} of {year} • Challenge ready for review",
        icon_url=bot.user.display_avatar.url if bot.user else None
    )
    
    try:
        await channel.send(embed=embed)
        print(f"Weekly challenge announced for staff review in {channel.name}")
        
    except discord.Forbidden:
        print(f"No permission to send messages in {channel.name}")
    except discord.HTTPException as e:
        print(f"Error posting weekly challenge: {e}")
    except Exception as e:
        print(f"Unexpected error posting weekly challenge: {e}")

async def post_challenge_to_community(bot, challenge_data, coding_challenges_channel_id):
    """Post the approved challenge to the community coding challenges channel"""
    if not coding_challenges_channel_id:
        print("Coding challenges channel not configured")
        return
    
    channel = bot.get_channel(coding_challenges_channel_id)
    if not channel:
        print(f"Coding challenges channel {coding_challenges_channel_id} not found")
        return
    
    # Generate challenge info
    week_number = datetime.utcnow().isocalendar()[1]
    year = datetime.utcnow().year
    challenge_id = f"challenge_{year}_W{week_number:02d}"
    
    # Calculate deadline
    today = datetime.utcnow()
    days_until_sunday = (6 - today.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7
    deadline = today + timedelta(days=days_until_sunday)
    deadline = deadline.replace(hour=23, minute=59, second=59, microsecond=0)
    
    # Create community announcement embed
    embed = discord.Embed(
        title="🚀 Weekly Coding Challenge",
        description="Time for this week's coding challenge! Show off your skills and compete with the community!",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    if isinstance(challenge_data, dict):
        embed.add_field(
            name="🎯 Challenge",
            value=challenge_data.get('title', 'Weekly Coding Challenge'),
            inline=False
        )
        
        embed.add_field(
            name="📝 Description",
            value=challenge_data.get('description', 'No description available'),
            inline=False
        )
        
        if 'difficulty' in challenge_data:
            embed.add_field(
                name="🎚️ Difficulty",
                value=challenge_data['difficulty'],
                inline=True
            )
        
        if 'estimated_time' in challenge_data:
            embed.add_field(
                name="⏱️ Est. Time",
                value=challenge_data['estimated_time'],
                inline=True
            )
        
        if 'category' in challenge_data:
            embed.add_field(
                name="📂 Category",
                value=challenge_data['category'],
                inline=True
            )
    else:
        embed.add_field(
            name="📝 Challenge",
            value=str(challenge_data),
            inline=False
        )
    
    embed.add_field(
        name="📅 Important Dates",
        value=f"**Deadline:** {deadline.strftime('%B %d, %Y at %H:%M UTC')}\n"
              f"**Time Remaining:** {(deadline - today).days} days",
        inline=False
    )
    
    embed.add_field(
        name="🎯 How to Submit",
        value="• Work on your solution\n"
              "• Upload to GitHub/GitLab or coding platform\n"
              "• Use `!submit-challenge <link>` to submit\n"
              "• Submit in this thread for discussion\n"
              "• Get feedback from the community!",
        inline=False
    )
    
    embed.add_field(
        name="🏆 Rewards",
        value="• **Winner:** 100 bonus XP + recognition\n"
              "• **Participants:** 25 bonus XP\n"
              "• **Best Solution:** Special mention in announcements\n"
              "• **Creative Solutions:** Extra recognition!",
        inline=False
    )
    
    embed.set_footer(
        text=f"Challenge #{week_number} • Good luck, coders! 🍀",
        icon_url=bot.user.display_avatar.url if bot.user else None
    )
    
    try:
        # Send the challenge message
        challenge_message = await channel.send(embed=embed)
        
        # Create a thread for submissions and discussions
        thread = await challenge_message.create_thread(
            name=f"Week {week_number} Challenge - Submissions & Discussion",
            auto_archive_duration=10080  # 7 days
        )
        
        # Send instructions in the thread
        thread_embed = create_info_embed(
            "💻 Challenge Discussion Thread",
            "Welcome to this week's coding challenge discussion!\n\n"
            "🔹 Share your solutions and approaches here\n"
            "🔹 Ask questions and get help from the community\n"
            "🔹 Provide feedback on others' solutions\n"
            "🔹 Use `!submit-challenge <link>` for official submission\n"
            "🔹 Remember: learning is more important than winning!"
        )
        
        await thread.send(embed=thread_embed)
        
        # Add reactions for engagement
        await challenge_message.add_reaction("💻")  # Computer
        await challenge_message.add_reaction("🚀")  # Rocket
        await challenge_message.add_reaction("🔥")  # Fire
        await challenge_message.add_reaction("❤️")  # Love
        
        print(f"Weekly challenge posted to community in {channel.name}")
        return challenge_message
        
    except discord.Forbidden:
        print(f"No permission to send messages in {channel.name}")
    except discord.HTTPException as e:
        print(f"Error posting community challenge: {e}")
    except Exception as e:
        print(f"Unexpected error posting community challenge: {e}")
    
    return None

def load_challenges():
    """Load challenges from the JSON file"""
    try:
        with open('src/data/challenges.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Usage example (to be placed in your bot initialization code):
# challenge_bot = WeeklyChallenge(bot, CHANNEL_ID)
# challenge_bot.start()