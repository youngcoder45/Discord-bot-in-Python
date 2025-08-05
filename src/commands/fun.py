import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import json
import re
import typing
from datetime import datetime, timedelta
from utils.database import db
from utils.helpers import create_success_embed, create_error_embed, create_info_embed

class Fun(commands.Cog):
    """Fun commands for entertainment and engagement"""
    
    def __init__(self, bot):
        self.bot = bot
        self.hangman_games = {}
        self.would_you_rather_cooldowns = {}
        self.active_games = {}

    @commands.hybrid_command(name="compliment", description="Get a random compliment")
    async def compliment(self, ctx, member: discord.Member = None):
        """Send a random compliment to yourself or another member"""
        target = member or ctx.author
        compliment = random.choice(COMPLIMENTS)
        embed = discord.Embed(
            title="💝 Compliment!",
            description=f"{target.mention}, {compliment}",
            color=discord.Color.pink()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="dadjoke", description="Get a random dad joke")
    async def dadjoke(self, ctx):
        """Get a random dad joke"""
        joke = random.choice(DAD_JOKES)
        embed = discord.Embed(
            title="👨 Dad Joke!",
            description=joke,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="fortune", description="Get your programming fortune")
    async def fortune(self, ctx):
        """Get a programming-themed fortune cookie message"""
        fortune = random.choice(FORTUNE_COOKIES)
        embed = discord.Embed(
            title="🥠 Your Programming Fortune",
            description=fortune,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="wyr", description="Would you rather...?")
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def would_you_rather(self, ctx):
        """Start a would you rather game"""
        question = random.choice(WOULD_YOU_RATHER)
        embed = discord.Embed(
            title="🤔 Would You Rather...",
            color=discord.Color.blue()
        )
        embed.add_field(name="1️⃣", value=question["option1"], inline=False)
        embed.add_field(name="2️⃣", value=question["option2"], inline=False)
        message = await ctx.send(embed=embed)
        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")

    @commands.hybrid_command(name="hangman", description="Play hangman with programming words")
    async def hangman(self, ctx):
        """Start a game of hangman"""
        if ctx.channel.id in self.hangman_games:
            await ctx.send("A game is already in progress in this channel!")
            return

        word = random.choice(HANGMAN_WORDS).upper()
        guessed = set()
        tries = 6
        
        self.hangman_games[ctx.channel.id] = {
            "word": word,
            "guessed": guessed,
            "tries": tries
        }

        def get_display_word():
            return " ".join(letter if letter in guessed else "_" for letter in word)

        embed = discord.Embed(
            title="🎯 Hangman - Programming Edition",
            description=f"```\n{get_display_word()}\n```\nTries left: {tries}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle hangman game responses"""
        if message.author.bot:
            return

        if message.channel.id in self.hangman_games:
            game = self.hangman_games[message.channel.id]
            
            content = message.content.upper()
            if len(content) == 1 and content.isalpha():
                if content in game["guessed"]:
                    await message.channel.send("You already guessed that letter!")
                    return

                game["guessed"].add(content)
                
                if content not in game["word"]:
                    game["tries"] -= 1

                word = game["word"]
                guessed = game["guessed"]
                tries = game["tries"]

                display = " ".join(letter if letter in guessed else "_" for letter in word)
                
                if tries == 0:
                    await message.channel.send(f"Game Over! The word was: {word}")
                    del self.hangman_games[message.channel.id]
                elif "_" not in display.replace(" ", ""):
                    await message.channel.send(f"🎉 Congratulations! You got it: {word}")
                    await db.update_user_activity(message.author.id, str(message.author), 20)
                    del self.hangman_games[message.channel.id]
                else:
                    embed = discord.Embed(
                        title="🎯 Hangman - Programming Edition",
                        description=f"```\n{display}\n```\nTries left: {tries}",
                        color=discord.Color.green()
                    )
                    await message.channel.send(embed=embed)

COMPLIMENTS = [
    "You're coding like a pro! 🚀",
    "Your problem-solving skills are impressive! 🧠",
    "You're crushing it today! 💪",
    "You make debugging look easy! 🔍",
    "Your code is cleaner than my cache! ✨",
    "You're the exception to null pointer errors! ⭐",
    "You're the semicolon to my statement! 😊",
]

DAD_JOKES = [
    "Why don't programmers like nature? It has too many bugs!",
    "What do you call a bear with no teeth? A gummy bear!",
    "Why don't skeletons fight each other? They don't have the guts!",
    "What do you call a fake noodle? An impasta!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
]

FORTUNE_COOKIES = [
    "A beautiful, smart, and loving person will be coming into your code base.",
    "Your commit will bring you good luck.",
    "Now is the time to try something new with your code.",
    "The bug you're looking for is in another file.",
    "You will soon be the center of a git merge conflict.",
    "Your code will compile on the first try today.",
    "A mysterious pull request will bring unexpected joy.",
    "Don't worry about the bugs of tomorrow, deal with the exceptions of today.",
]

WOULD_YOU_RATHER = [
    {"option1": "Only be able to write Python", "option2": "Only be able to write JavaScript"},
    {"option1": "Have perfect code but no comments", "option2": "Buggy code with perfect documentation"},
    {"option1": "Be able to predict all runtime errors", "option2": "Be able to predict all compilation errors"},
    {"option1": "Always have to code in light mode", "option2": "Always have to code without auto-complete"},
    {"option1": "Write code that no one can understand but works perfectly", "option2": "Write code everyone understands but takes twice as long to run"},
]

HANGMAN_WORDS = [
    "python", "javascript", "programming", "database", "algorithm",
    "function", "variable", "debugging", "framework", "developer",
    "compiler", "frontend", "backend", "fullstack", "docker",
    "github", "linux", "server", "cloud", "agile"
]

PROGRAMMING_JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "Why did the programmer quit his job? Because he didn't get arrays!",
    "What's a programmer's favorite hangout spot? The Foo Bar!",
    "Why do programmers always mix up Christmas and Halloween? Because Oct 31 == Dec 25!",
    "Why do Java developers wear glasses? Because they don't C#",
    "Why did the developer go broke? Because he used up all his cache!",
    "What do you call a programmer from Finland? Nerdic!",
    "Why was the JavaScript developer sad? Because he didn't Node how to Express himself!",
    "What's a pirate's favorite programming language? R!",
    "Why do programmers hate nature? It has too many bugs!",
    "What's a programmer's favorite place in New York? Boolean Manhattan!",
]

RIDDLES = [
    {"question": "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?", "answer": "an echo"},
    {"question": "What has keys, but no locks; space, but no room; and you can enter, but not go in?", "answer": "a keyboard"},
    {"question": "What gets bigger when more is taken away?", "answer": "a hole"},
    {"question": "I am taken from a mine and shut up in a wooden case, from which I am never released, and yet I am used by everyone. What am I?", "answer": "a pencil lead"},
    {"question": "What kind of tree can you carry in your hand?", "answer": "a palm"},
    {"question": "I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. I have roads, but no cars. What am I?", "answer": "a map"},
    {"question": "The more you code, the more of me there is. I may be gone for now but you can't get rid of me forever. What am I?", "answer": "a bug"},
]

COMPLIMENTS = [
    "You're coding like a pro! 🚀",
    "Your problem-solving skills are impressive! 🧠",
    "You're crushing it today! 💪",
    "You make debugging look easy! 🔍",
    "Your code is cleaner than my cache! ✨",
    "You're the exception to null pointer errors! ⭐",
    "You're the semicolon to my statement! 😊",
]

DAD_JOKES = [
    "Why don't programmers like nature? It has too many bugs!",
    "What do you call a bear with no teeth? A gummy bear!",
    "Why don't skeletons fight each other? They don't have the guts!",
    "What do you call a fake noodle? An impasta!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
]

FORTUNE_COOKIES = [
    "A beautiful, smart, and loving person will be coming into your code base.",
    "Your commit will bring you good luck.",
    "Now is the time to try something new with your code.",
    "The bug you're looking for is in another file.",
    "You will soon be the center of a git merge conflict.",
    "Your code will compile on the first try today.",
    "A mysterious pull request will bring unexpected joy.",
    "Don't worry about the bugs of tomorrow, deal with the exceptions of today.",
]

WOULD_YOU_RATHER = [
    {"option1": "Only be able to write Python", "option2": "Only be able to write JavaScript"},
    {"option1": "Have perfect code but no comments", "option2": "Buggy code with perfect documentation"},
    {"option1": "Be able to predict all runtime errors", "option2": "Be able to predict all compilation errors"},
    {"option1": "Always have to code in light mode", "option2": "Always have to code without auto-complete"},
    {"option1": "Write code that no one can understand but works perfectly", "option2": "Write code everyone understands but takes twice as long to run"},
]

# Dictionary for hangman words related to programming
HANGMAN_WORDS = [
    "python", "javascript", "programming", "database", "algorithm",
    "function", "variable", "debugging", "framework", "developer",
    "compiler", "frontend", "backend", "fullstack", "docker",
    "github", "linux", "server", "cloud", "agile"
]

# Rock, Paper, Scissors responses
RPS_RESPONSES = {
    "win": [
        "Amazing victory! 🎉",
        "You're unbeatable! 🏆",
        "Skillful play! ⭐",
        "Champion move! 🌟",
    ],
    "lose": [
        "Better luck next time! 🎲",
        "Close game! 🎮",
        "Don't give up! 💫",
        "Practice makes perfect! 🎯",
    ],
    "tie": [
        "Great minds think alike! 🤝",
        "It's a tie! ⚖️",
        "Perfect balance! ☯️",
        "Let's go again! 🔄",
    ]
}

TRIVIA_QUESTIONS = [
    {
        "question": "What does API stand for?",
        "options": [
            "Application Programming Interface",
            "Advanced Programming Interface",
            "Automated Programming Interface",
            "Application Protocol Interface"
        ],
        "answer": "Application Programming Interface",
        "category": "basics"
    },
    {
        "question": "Which data structure uses LIFO?",
        "options": [
            "Queue",
            "Stack",
            "Tree",
            "Linked List"
        ],
        "answer": "Stack",
        "category": "data_structures"
    },
    {
        "question": "What is the time complexity of binary search?",
        "options": [
            "O(n)",
            "O(log n)",
            "O(n²)",
            "O(n log n)"
        ],
        "answer": "O(log n)",
        "answer": "O(log n)",
        "category": "algorithms"
    }
]

class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.hybrid_command(name="joke", description="Get a random programming joke")
    async def joke(self, ctx):
        """Get a random programming joke"""
        joke = random.choice(PROGRAMMING_JOKES)
        embed = discord.Embed(
            title="😄 Programming Joke",
            description=joke,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="riddle", description="Get a random riddle to solve")
    async def riddle(self, ctx):
        """Start a riddle game"""
        riddle = random.choice(RIDDLES)
        embed = discord.Embed(
            title="🤔 Riddle Time!",
            description=riddle["question"],
            color=discord.Color.purple()
        )
        embed.set_footer(text="Reply with your answer within 30 seconds!")
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            guess = await self.bot.wait_for('message', check=check, timeout=30.0)
            if guess.content.lower() == riddle["answer"]:
                await ctx.send(f"🎉 Correct, {ctx.author.mention}! Well done!")
                await db.update_user_activity(ctx.author.id, str(ctx.author), 10)
            else:
                await ctx.send(f"❌ Sorry, that's not correct. The answer was: {riddle['answer']}")
        except asyncio.TimeoutError:
            await ctx.send("⏰ Time's up! Better luck next time!")

    @commands.hybrid_command(name="trivia", description="Start a trivia question")
    async def trivia(self, ctx):
        """Start a trivia game"""
        question = random.choice(TRIVIA_QUESTIONS)
        options = question["options"]
        random.shuffle(options)

        # Create the question embed
        embed = discord.Embed(
            title="🎯 Programming Trivia",
            description=question["question"],
            color=discord.Color.gold()
        )
        for i, option in enumerate(options):
            embed.add_field(name=f"Option {i+1}", value=option, inline=True)
        embed.set_footer(text="Reply with the number of your answer (1-4) within 30 seconds!")
        
        await ctx.send(embed=embed)

        def check(m):
            return (m.author == ctx.author and 
                   m.channel == ctx.channel and 
                   m.content.isdigit() and 
                   1 <= int(m.content) <= 4)

        try:
            guess = await self.bot.wait_for('message', check=check, timeout=30.0)
            if options[int(guess.content)-1] == question["answer"]:
                await ctx.send(f"✨ Correct, {ctx.author.mention}! You're a genius!")
                await db.update_user_activity(ctx.author.id, str(ctx.author), 15)
            else:
                await ctx.send(f"❌ Not quite! The correct answer was: {question['answer']}")
        except asyncio.TimeoutError:
            await ctx.send("⏰ Time's up! The answer was: " + question["answer"])

    @commands.hybrid_command(name="rps", description="Play Rock, Paper, Scissors")
    @app_commands.describe(choice="Your choice: rock, paper, or scissors")
    async def rps(self, ctx, choice: str):
        """Play Rock, Paper, Scissors"""
        choice = choice.lower()
        choices = ["rock", "paper", "scissors"]
        
        if choice not in choices:
            await ctx.send("Please choose either rock, paper, or scissors!")
            return

        bot_choice = random.choice(choices)
        
        # Create result embed
        embed = discord.Embed(title="🎮 Rock, Paper, Scissors!", color=discord.Color.blue())
        embed.add_field(name="Your Choice", value=choice.capitalize(), inline=True)
        embed.add_field(name="Bot's Choice", value=bot_choice.capitalize(), inline=True)
        
        # Determine winner
        if choice == bot_choice:
            result = "It's a tie! 🤝"
        elif ((choice == "rock" and bot_choice == "scissors") or 
              (choice == "paper" and bot_choice == "rock") or 
              (choice == "scissors" and bot_choice == "paper")):
            result = f"You win! 🎉"
            await db.update_user_activity(ctx.author.id, str(ctx.author), 5)
        else:
            result = "Bot wins! 🤖"
        
        embed.add_field(name="Result", value=result, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="flip", description="Flip a coin")
    async def flip(self, ctx):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"The coin landed on: **{result}**!",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="roll", description="Roll some dice")
    @app_commands.describe(dice="The dice to roll (e.g., 2d6 for two six-sided dice)")
    async def roll(self, ctx, dice: str = "1d6"):
        """Roll dice in NdN format"""
        try:
            match = re.match(r"(\d+)d(\d+)", dice)
            if not match:
                await ctx.send("Format must be NdN (e.g., 2d6 for two six-sided dice)")
                return

            number, sides = map(int, match.groups())
            if number > 100:
                await ctx.send("Cannot roll more than 100 dice at once!")
                return
            if sides > 100:
                await ctx.send("Cannot roll dice with more than 100 sides!")
                return

            rolls = [random.randint(1, sides) for _ in range(number)]
            total = sum(rolls)
            
            embed = discord.Embed(
                title="🎲 Dice Roll",
                description=f"Rolling {dice}...",
                color=discord.Color.green()
            )
            embed.add_field(name="Rolls", value=", ".join(map(str, rolls)), inline=False)
            embed.add_field(name="Total", value=str(total), inline=False)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")

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
async def setup(bot):
    await bot.add_cog(Fun(bot))
    await bot.add_cog(FunCommands(bot))
