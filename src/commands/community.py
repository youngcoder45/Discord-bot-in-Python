"""Community engagement prefix commands (simplified).

Provides quote, question, meme and suggestion commands. Persistence for
suggestions/challenges/QOTD removed per simplification request.
"""

import discord
from discord.ext import commands
import json
from datetime import datetime, timezone
from utils.helpers import (
    create_success_embed,
    create_error_embed,
    get_random_quote,
    get_random_question,
    fetch_programming_meme,
    sanitize_input
)


class CommunityCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.load_data()

    def load_data(self):
        try:
            with open('src/data/questions.json', 'r', encoding='utf-8') as f:
                self.questions = json.load(f)
        except FileNotFoundError:
            self.questions = []
        try:
            with open('src/data/quotes.json', 'r', encoding='utf-8') as f:
                self.quotes = json.load(f)
        except FileNotFoundError:
            self.quotes = []

    @commands.command(name='quote', help='Get a random motivational/programming quote')
    async def quote(self, ctx: commands.Context):
        if not self.quotes:
            await ctx.send(embed=create_error_embed('No Quotes', 'No quotes available.'))
            return
        text = get_random_quote(self.quotes)
        embed = discord.Embed(title='💡 Inspiration', description=f"*{text}*", color=discord.Color.gold(), timestamp=datetime.now(tz=timezone.utc))
        embed.set_footer(text='Stay motivated! 🚀')
        await ctx.send(embed=embed)

    @commands.command(name='question', help='Get a random programming question')
    async def question(self, ctx: commands.Context):
        if not self.questions:
            await ctx.send(embed=create_error_embed('No Questions', 'No questions available.'))
            return
        q = get_random_question(self.questions)
        embed = discord.Embed(title='🧠 Programming Question', color=discord.Color.blue(), timestamp=datetime.now(tz=timezone.utc))
        if isinstance(q, dict):
            embed.add_field(name='Question', value=q.get('question', 'N/A'), inline=False)
            if 'difficulty' in q:
                embed.add_field(name='Difficulty', value=q['difficulty'], inline=True)
            if 'category' in q:
                embed.add_field(name='Category', value=q['category'], inline=True)
        else:
            embed.add_field(name='Question', value=str(q), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='meme', help='Get a random programming meme')
    async def meme(self, ctx: commands.Context):
        async with ctx.typing():
            meme = await fetch_programming_meme()
        if meme.startswith('http'):
            embed = discord.Embed(title='😄 Programming Meme', color=discord.Color.orange(), timestamp=datetime.now(tz=timezone.utc))
            embed.set_image(url=meme)
        else:
            embed = discord.Embed(title='😄 Programming Meme', description=meme, color=discord.Color.orange(), timestamp=datetime.now(tz=timezone.utc))
        embed.set_footer(text='Hope this made you smile! 😊')
        await ctx.send(embed=embed)

    @commands.command(name='suggest', help='Submit a suggestion (ephemeral – not stored)')
    async def suggest(self, ctx: commands.Context, *, suggestion: str):
        suggestion = sanitize_input(suggestion, 1000)
        if len(suggestion.strip()) < 10:
            await ctx.send(embed=create_error_embed('Suggestion Too Short', 'Minimum 10 characters.'))
            return
        embed = create_success_embed(
            '💡 Suggestion Received!',
                        f"(Not persisted in this simplified build)\n\n**Your suggestion:** {suggestion[:200]}{'...' if len(suggestion) > 200 else ''}"
        )
        await ctx.send(embed=embed)

    @commands.command(name='reload-data', help='Reload quotes & questions (Admin only)')
    @commands.has_permissions(administrator=True)
    async def reload_data(self, ctx: commands.Context):
        try:
            self.load_data()
            await ctx.send(embed=create_success_embed('🔄 Data Reloaded', f"Loaded {len(self.questions)} questions, {len(self.quotes)} quotes."))
        except Exception as e:
            await ctx.send(embed=create_error_embed('Reload Failed', str(e)))


async def setup(bot: commands.Bot):
    await bot.add_cog(CommunityCommands(bot))