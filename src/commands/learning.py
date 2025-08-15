import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import asyncio
from datetime import datetime, timedelta, timezone
from utils.database import db
from utils.helpers import create_success_embed, create_error_embed, create_info_embed

class LearningCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_learning_data()
        
    def load_learning_data(self):
        """Load learning resources"""
        try:
            with open('src/data/code_snippets.json', 'r', encoding='utf-8') as f:
                self.code_snippets = json.load(f)
        except FileNotFoundError:
            self.code_snippets = {}
            
        try:
            with open('src/data/tutorials.json', 'r', encoding='utf-8') as f:
                self.tutorials = json.load(f)
        except FileNotFoundError:
            self.tutorials = []

    @app_commands.command(name="code-snippet", description="Get a useful code snippet")
    @app_commands.describe(language="Programming language (python, javascript, java, etc.)")
    async def code_snippet(self, interaction: discord.Interaction, language: str = None):
        """Get random or language-specific code snippets"""
        if not self.code_snippets:
            await interaction.response.send_message("❌ No code snippets available!", ephemeral=True)
            return
            
        if language:
            language = language.lower()
            if language in self.code_snippets:
                snippet = random.choice(self.code_snippets[language])
            else:
                available = ", ".join(self.code_snippets.keys())
                await interaction.response.send_message(
                    f"❌ Language '{language}' not found. Available: {available}",
                    ephemeral=True
                )
                return
        else:
            # Random language
            language = random.choice(list(self.code_snippets.keys()))
            snippet = random.choice(self.code_snippets[language])
        
        embed = discord.Embed(
            title=f"💻 {language.title()} Code Snippet",
            description=snippet.get('description', 'Useful code snippet'),
            color=discord.Color.blue(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        if 'code' in snippet:
            embed.add_field(
                name="Code",
                value=f"```{language}\n{snippet['code']}\n```",
                inline=False
            )
        
        if 'explanation' in snippet:
            embed.add_field(
                name="Explanation",
                value=snippet['explanation'],
                inline=False
            )
            
        embed.set_footer(text="💡 Practice makes perfect!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="algorithm", description="Learn about algorithms with examples")
    @app_commands.describe(topic="Algorithm topic (sorting, searching, etc.)")
    async def algorithm(self, interaction: discord.Interaction, topic: str = None):
        """Educational algorithm explanations"""
        algorithms = {
            "bubble_sort": {
                "name": "Bubble Sort",
                "description": "Simple sorting algorithm that repeatedly steps through the list",
                "time_complexity": "O(n²)",
                "space_complexity": "O(1)",
                "code": """def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr""",
                "use_case": "Educational purposes, small datasets"
            },
            "binary_search": {
                "name": "Binary Search",
                "description": "Efficient search algorithm for sorted arrays",
                "time_complexity": "O(log n)",
                "space_complexity": "O(1)",
                "code": """def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1""",
                "use_case": "Searching in sorted data"
            },
            "fibonacci": {
                "name": "Fibonacci Sequence",
                "description": "Sequence where each number is sum of two preceding ones",
                "time_complexity": "O(n) with memoization",
                "space_complexity": "O(n)",
                "code": """def fibonacci(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 2:
        return 1
    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)
    return memo[n]""",
                "use_case": "Dynamic programming, mathematical sequences"
            }
        }
        
        if topic:
            topic = topic.lower().replace(" ", "_")
            if topic in algorithms:
                algo = algorithms[topic]
            else:
                available = ", ".join([k.replace("_", " ").title() for k in algorithms.keys()])
                await interaction.response.send_message(
                    f"❌ Algorithm '{topic}' not found. Available: {available}",
                    ephemeral=True
                )
                return
        else:
            topic, algo = random.choice(list(algorithms.items()))
        
        embed = discord.Embed(
            title=f"🧮 {algo['name']}",
            description=algo['description'],
            color=discord.Color.green(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        embed.add_field(
            name="⏱️ Time Complexity",
            value=algo['time_complexity'],
            inline=True
        )
        embed.add_field(
            name="💾 Space Complexity", 
            value=algo['space_complexity'],
            inline=True
        )
        embed.add_field(
            name="🎯 Use Case",
            value=algo['use_case'],
            inline=False
        )
        embed.add_field(
            name="Code Example",
            value=f"```python\n{algo['code']}\n```",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="quiz", description="Take a programming quiz")
    @app_commands.describe(topic="Quiz topic (python, javascript, general, etc.)")
    async def programming_quiz(self, interaction: discord.Interaction, topic: str = "general"):
        """Interactive programming quiz"""
        quizzes = {
            "python": [
                {
                    "question": "What is the output of: print(type([]))",
                    "options": ["<class 'list'>", "<class 'array'>", "<class 'tuple'>", "None"],
                    "answer": 0,
                    "explanation": "[] creates a list, so type([]) returns <class 'list'>"
                },
                {
                    "question": "Which keyword is used to define a function in Python?",
                    "options": ["function", "def", "func", "define"],
                    "answer": 1,
                    "explanation": "'def' is the keyword used to define functions in Python"
                }
            ],
            "javascript": [
                {
                    "question": "What does '===' operator do in JavaScript?",
                    "options": ["Assignment", "Equality with type coercion", "Strict equality", "Not equal"],
                    "answer": 2,
                    "explanation": "'===' checks for strict equality without type coercion"
                },
                {
                    "question": "How do you declare a variable in ES6?",
                    "options": ["var", "let or const", "variable", "declare"],
                    "answer": 1,
                    "explanation": "ES6 introduced 'let' and 'const' for better variable scoping"
                }
            ],
            "general": [
                {
                    "question": "What does OOP stand for?",
                    "options": ["Object Oriented Programming", "Only One Process", "Open Object Protocol", "Optimal Output Processing"],
                    "answer": 0,
                    "explanation": "OOP stands for Object Oriented Programming"
                },
                {
                    "question": "What is Big O notation used for?",
                    "options": ["Code formatting", "Algorithm complexity", "Variable naming", "File organization"],
                    "answer": 1,
                    "explanation": "Big O notation describes algorithm time/space complexity"
                }
            ]
        }
        
        if topic.lower() not in quizzes:
            available = ", ".join(quizzes.keys())
            await interaction.response.send_message(
                f"❌ Topic '{topic}' not available. Available topics: {available}",
                ephemeral=True
            )
            return
        
        quiz_questions = quizzes[topic.lower()]
        question = random.choice(quiz_questions)
        
        embed = discord.Embed(
            title=f"🧠 {topic.title()} Quiz",
            description=question["question"],
            color=discord.Color.orange(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(question["options"])])
        embed.add_field(name="Options", value=options_text, inline=False)
        embed.set_footer(text="React with 1️⃣, 2️⃣, 3️⃣, or 4️⃣ to answer!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        for reaction in reactions[:len(question["options"])]:
            await message.add_reaction(reaction)
        
        def check(reaction, user):
            return (user == interaction.user and 
                   str(reaction.emoji) in reactions and 
                   reaction.message.id == message.id)
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            user_answer = reactions.index(str(reaction.emoji))
            correct_answer = question["answer"]
            
            if user_answer == correct_answer:
                result_embed = create_success_embed(
                    "🎉 Correct!",
                    f"**Explanation:** {question['explanation']}"
                )
                # Give XP for correct answer
                await db.update_user_activity(interaction.user.id, str(interaction.user), 10)
            else:
                result_embed = create_error_embed(
                    "❌ Incorrect!",
                    f"**Correct answer:** {question['options'][correct_answer]}\n"
                    f"**Explanation:** {question['explanation']}"
                )
            
            await interaction.followup.send(embed=result_embed)
            
        except asyncio.TimeoutError:
            timeout_embed = create_info_embed(
                "⏰ Time's Up!",
                f"**Correct answer:** {question['options'][question['answer']]}\n"
                f"**Explanation:** {question['explanation']}"
            )
            await interaction.followup.send(embed=timeout_embed)

async def setup(bot):
    await bot.add_cog(LearningCommands(bot))
