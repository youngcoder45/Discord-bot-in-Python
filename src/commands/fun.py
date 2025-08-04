import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import json
from datetime import datetime
from utils.database import db
from utils.helpers import create_success_embed, create_error_embed, create_info_embed

class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    @app_commands.describe(question="Your yes/no question")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        """Magic 8-ball command"""
        responses = [
            "🎱 It is certain", "🎱 Without a doubt", "🎱 Yes definitely",
            "🎱 You may rely on it", "🎱 As I see it, yes", "🎱 Most likely",
            "🎱 Outlook good", "🎱 Yes", "🎱 Signs point to yes",
            "🎱 Reply hazy, try again", "🎱 Ask again later", "🎱 Better not tell you now",
            "🎱 Cannot predict now", "🎱 Concentrate and ask again",
            "🎱 Don't count on it", "🎱 My reply is no", "🎱 My sources say no",
            "🎱 Outlook not so good", "🎱 Very doubtful"
        ]
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=random.choice(responses), inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="poll", description="Create a poll with custom options")
    @app_commands.describe(
        question="The poll question",
        option1="First option",
        option2="Second option", 
        option3="Third option (optional)",
        option4="Fourth option (optional)"
    )
    async def poll(self, interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
        """Create a poll with reactions"""
        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)
        
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        
        embed = discord.Embed(
            title="📊 Poll",
            description=question,
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        for i, option in enumerate(options):
            embed.add_field(
                name=f"{emojis[i]} Option {i+1}",
                value=option,
                inline=False
            )
        
        embed.set_footer(text=f"Poll by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        for i in range(len(options)):
            await message.add_reaction(emojis[i])
    
    @app_commands.command(name="guess", description="Start a number guessing game")
    @app_commands.describe(max_number="Maximum number to guess (default: 100)")
    async def guess_game(self, interaction: discord.Interaction, max_number: int = 100):
        """Number guessing game"""
        if max_number < 2 or max_number > 1000:
            await interaction.response.send_message("❌ Please choose a number between 2 and 1000!", ephemeral=True)
            return
            
        number = random.randint(1, max_number)
        attempts = 0
        max_attempts = min(10, max(3, max_number // 10))
        
        embed = discord.Embed(
            title="🎯 Number Guessing Game",
            description=f"I'm thinking of a number between 1 and {max_number}!\nYou have {max_attempts} attempts to guess it.",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)
        
        def check(message):
            return message.author == interaction.user and message.channel == interaction.channel
        
        while attempts < max_attempts:
            try:
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                attempts += 1
                
                try:
                    guess = int(msg.content)
                except ValueError:
                    await msg.reply("Please enter a valid number!")
                    continue
                
                if guess == number:
                    await msg.reply(f"🎉 Congratulations! You guessed it in {attempts} attempts! The number was {number}.")
                    # Give XP for winning
                    await db.update_user_activity(interaction.user.id, str(interaction.user), 15)
                    return
                elif guess < number:
                    remaining = max_attempts - attempts
                    if remaining > 0:
                        await msg.reply(f"📈 Too low! {remaining} attempts remaining.")
                    else:
                        await msg.reply(f"📈 Too low! Game over! The number was {number}.")
                else:
                    remaining = max_attempts - attempts
                    if remaining > 0:
                        await msg.reply(f"📉 Too high! {remaining} attempts remaining.")
                    else:
                        await msg.reply(f"📉 Too high! Game over! The number was {number}.")
                        
            except asyncio.TimeoutError:
                await interaction.followup.send(f"⏰ Time's up! The number was {number}.")
                return
        
        await interaction.followup.send(f"💔 Game over! The number was {number}. Better luck next time!")

async def setup(bot):
    await bot.add_cog(FunCommands(bot))
