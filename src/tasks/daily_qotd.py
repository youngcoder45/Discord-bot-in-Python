import discord
import random
import json
import os
from datetime import datetime
from utils.helpers import get_random_question, create_info_embed

async def post_daily_qotd(bot, channel_id):
    """Post the daily Question of the Day"""
    if not channel_id:
        print("QOTD channel not configured")
        return
    
    channel = bot.get_channel(channel_id)
    if not channel:
        print(f"QOTD channel {channel_id} not found")
        return
    
    # Load questions
    try:
        with open('src/data/questions.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)
    except FileNotFoundError:
        print("Questions file not found")
        return
    except json.JSONDecodeError:
        print("Error reading questions file")
        return
    
    if not questions:
        print("No questions available")
        return
    
    # Get a random question
    question_data = get_random_question(questions)
    
    # Generate QOTD ID for tracking
    qotd_id = f"qotd_{datetime.utcnow().strftime('%Y_%m_%d')}"
    
    # Create embed
    embed = discord.Embed(
        title="🧠 Question of the Day",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    if isinstance(question_data, dict):
        embed.add_field(
            name="Today's Question",
            value=question_data.get('question', 'No question available'),
            inline=False
        )
        
        if 'difficulty' in question_data:
            embed.add_field(
                name="🎯 Difficulty",
                value=question_data['difficulty'],
                inline=True
            )
        
        if 'category' in question_data:
            embed.add_field(
                name="📂 Category",
                value=question_data['category'],
                inline=True
            )
        
        if 'hint' in question_data:
            embed.add_field(
                name="💡 Hint",
                value=question_data['hint'],
                inline=False
            )
    else:
        embed.add_field(
            name="Today's Question",
            value=str(question_data),
            inline=False
        )
    
    embed.add_field(
        name="🎁 How to Participate",
      value="• Answer in this thread to submit your response\n"
          "• Use `?qotd-answer <your answer>` for recorded submission\n"
          "• Winners get community recognition!\n"
              "• Best answer will be selected by staff",
        inline=False
    )
    
    embed.set_footer(
        text=f"QOTD #{datetime.utcnow().strftime('%j')} • Good luck! 🍀",
        icon_url=bot.user.display_avatar.url if bot.user else None
    )
    
    try:
        # Send the QOTD message
        qotd_message = await channel.send(embed=embed)
        
        # Create a thread for discussions
        thread = await qotd_message.create_thread(
            name=f"QOTD Discussion - {datetime.utcnow().strftime('%B %d, %Y')}",
            auto_archive_duration=1440  # 24 hours
        )
        
        # Send instructions in the thread
        thread_embed = create_info_embed(
            "💬 Discussion Thread",
            "Welcome to today's QOTD discussion!\n\n"
            "🔹 Share your thoughts and solutions here\n"
            "🔹 Help others understand concepts\n"
            "🔹 Learn from different approaches\n"
            "🔹 Use `?qotd-answer` in the main channel for official submission"
        )
        
        await thread.send(embed=thread_embed)
        
        # Add reactions for quick feedback
        await qotd_message.add_reaction("🧠")  # Thinking
        await qotd_message.add_reaction("❤️")  # Love it
        await qotd_message.add_reaction("🔥")  # Fire/Awesome
        
        print(f"Daily QOTD posted successfully in {channel.name}")
        
    except discord.Forbidden:
        print(f"No permission to send messages in {channel.name}")
    except discord.HTTPException as e:
        print(f"Error posting QOTD: {e}")
    except Exception as e:
        print(f"Unexpected error posting QOTD: {e}")

async def announce_qotd_winner(bot, channel_id, winner_user, question_text):
    """Announce the QOTD winner"""
    if not channel_id:
        return
    
    channel = bot.get_channel(channel_id)
    if not channel:
        return
    
    embed = discord.Embed(
        title="🏆 QOTD Winner Announcement!",
        description=f"Congratulations to {winner_user.mention} for the best answer to today's QOTD!",
        color=discord.Color.gold(),
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(
        name="🧠 Question",
        value=question_text[:200] + "..." if len(question_text) > 200 else question_text,
        inline=False
    )
    
    embed.add_field(
        name="🎁 Rewards",
        value="• **100 Bonus XP**\n• **Code Master** role\n• Recognition in the community!",
        inline=False
    )
    
    embed.set_thumbnail(url=winner_user.display_avatar.url)
    embed.set_footer(text="Great job! Keep participating in our daily QOTDs! 🚀")
    
    try:
        await channel.send(embed=embed)
        print(f"QOTD winner announced: {winner_user}")
    except Exception as e:
        print(f"Error announcing QOTD winner: {e}")

def load_questions():
    """Load questions from the JSON file"""
    try:
        with open('src/data/questions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    def stop(self):
        self.post_qotd.stop()