import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
from datetime import datetime
from utils.database import db
from utils.helpers import (
    create_success_embed,
    create_error_embed,
    create_info_embed,
    get_random_quote,
    get_random_question,
    fetch_programming_meme,
    is_valid_url,
    sanitize_input
)

async def respond_to_user(ctx, embed):
    """Helper function to respond to both slash commands and regular commands"""
    if hasattr(ctx, 'response'):
        # It's an interaction (slash command)
        await ctx.response.send_message(embed=embed)
    else:
        # It's a regular command
        await ctx.send(embed=embed)

class CommunityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_data()

    def load_data(self):
        """Load data from JSON files"""
        try:
            with open('src/data/questions.json', 'r', encoding='utf-8') as f:
                self.questions = json.load(f)
        except FileNotFoundError:
            self.questions = []
            
        try:
            with open('src/data/challenges.json', 'r', encoding='utf-8') as f:
                self.challenges = json.load(f)
        except FileNotFoundError:
            self.challenges = []
            
        try:
            with open('src/data/quotes.json', 'r', encoding='utf-8') as f:
                self.quotes = json.load(f)
        except FileNotFoundError:
            self.quotes = []

    @commands.hybrid_command(name='quote', description='Get a random motivational/programming quote')
    async def quote(self, ctx):
        """Send a random motivational or programming quote"""
        if not self.quotes:
            embed = create_error_embed("No Quotes", "No quotes available at the moment!")
            await respond_to_user(ctx, embed)
            return
        
        quote_text = get_random_quote(self.quotes)
        
        embed = discord.Embed(
            title="💡 Daily Inspiration",
            description=f"*{quote_text}*",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Stay motivated, keep coding! 🚀")
        
        await respond_to_user(ctx, embed)

    @commands.command(name='question', help='Get a random programming question')
    async def question(self, ctx):
        """Get a random programming question"""
        if not self.questions:
            embed = create_error_embed("No Questions", "No questions available at the moment!")
            await ctx.send(embed=embed)
            return
        
        question_data = get_random_question(self.questions)
        
        embed = discord.Embed(
            title="🧠 Random Programming Question",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        if isinstance(question_data, dict):
            embed.add_field(
                name="Question",
                value=question_data.get('question', 'No question available'),
                inline=False
            )
            if 'difficulty' in question_data:
                embed.add_field(
                    name="Difficulty",
                    value=question_data['difficulty'],
                    inline=True
                )
            if 'category' in question_data:
                embed.add_field(
                    name="Category",
                    value=question_data['category'],
                    inline=True
                )
        else:
            embed.add_field(
                name="Question",
                value=str(question_data),
                inline=False
            )
        
        embed.set_footer(text="Think you know the answer? Share it in the thread! 💭")
        
        await ctx.send(embed=embed)

    @commands.command(name='meme', help='Get a random programming meme')
    async def meme(self, ctx):
        """Get a random programming meme"""
        async with ctx.typing():
            meme = await fetch_programming_meme()
        
        if meme.startswith('http'):
            # It's an image URL
            embed = discord.Embed(
                title="😄 Programming Meme",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.set_image(url=meme)
            embed.set_footer(text="Hope this made you smile! 😊")
        else:
            # It's a text meme
            embed = discord.Embed(
                title="😄 Programming Meme",
                description=meme,
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="Hope this made you smile! 😊")
        
        await ctx.send(embed=embed)

    @commands.command(name='submit-challenge', aliases=['submit'], help='Submit a link for the current coding challenge')
    async def submit_challenge(self, ctx, *, submission_link: str):
        """Submit a link for the coding challenge"""
        if not is_valid_url(submission_link):
            embed = create_error_embed(
                "Invalid URL", 
                "Please provide a valid URL for your submission!"
            )
            await ctx.send(embed=embed)
            return
        
        # Get current challenge ID (you might want to implement a way to track current challenge)
        current_challenge_id = f"challenge_{datetime.utcnow().strftime('%Y_%W')}"  # Weekly challenge ID
        
        # Add submission to database
        await db.add_challenge_submission(ctx.author.id, current_challenge_id, submission_link)
        
        # Create success embed
        embed = create_success_embed(
            "🎯 Challenge Submission Received!",
            f"**Participant:** {ctx.author.mention}\n"
            f"**Submission:** [View Submission]({submission_link})\n"
            f"**Submitted:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        
        await ctx.send(embed=embed)
        
        # Also send to mod-tools channel if configured
        mod_tools_channel_id = int(os.getenv('MOD_TOOLS_CHANNEL_ID', 0))
        if mod_tools_channel_id:
            mod_channel = self.bot.get_channel(mod_tools_channel_id)
            if mod_channel:
                mod_embed = create_info_embed(
                    "📝 New Challenge Submission",
                    f"**Participant:** {ctx.author} ({ctx.author.id})\n"
                    f"**Channel:** {ctx.channel.mention}\n"
                    f"**Submission:** [View Submission]({submission_link})"
                )
                await mod_channel.send(embed=mod_embed)
        
        # Give XP for submission
        await db.update_user_activity(ctx.author.id, str(ctx.author), 25)  # Bonus XP for submissions

    @commands.command(name='suggest', help='Submit a suggestion for the server')
    async def suggest(self, ctx, *, suggestion: str):
        """Submit a suggestion for the server"""
        # Sanitize input
        suggestion = sanitize_input(suggestion, 1000)
        
        if len(suggestion.strip()) < 10:
            embed = create_error_embed(
                "Suggestion Too Short",
                "Please provide a suggestion with at least 10 characters!"
            )
            await ctx.send(embed=embed)
            return
        
        # Add to database
        await db.add_suggestion(ctx.author.id, suggestion)
        
        # Create embed for user confirmation
        embed = create_success_embed(
            "💡 Suggestion Submitted!",
            f"Your suggestion has been submitted and will be reviewed by the staff.\n\n"
            f"**Your suggestion:** {suggestion[:200]}{'...' if len(suggestion) > 200 else ''}"
        )
        
        await ctx.send(embed=embed)
        
        # Send to suggestions channel
        suggestions_channel_id = int(os.getenv('SUGGESTIONS_CHANNEL_ID', 0))
        if suggestions_channel_id:
            suggestions_channel = self.bot.get_channel(suggestions_channel_id)
            if suggestions_channel:
                suggestion_embed = discord.Embed(
                    title="💡 New Suggestion",
                    description=suggestion,
                    color=discord.Color.purple(),
                    timestamp=datetime.utcnow()
                )
                suggestion_embed.set_author(
                    name=f"{ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url
                )
                suggestion_embed.set_footer(text=f"User ID: {ctx.author.id}")
                
                suggestion_msg = await suggestions_channel.send(embed=suggestion_embed)
                
                # Add reaction options
                await suggestion_msg.add_reaction("👍")
                await suggestion_msg.add_reaction("👎")
                await suggestion_msg.add_reaction("🤔")

    @commands.command(name='qotd-answer', aliases=['qotd-submit'], help='Submit an answer to the current QOTD')
    async def qotd_answer(self, ctx, *, answer: str):
        """Submit an answer to the current Question of the Day"""
        answer = sanitize_input(answer, 500)
        
        if len(answer.strip()) < 5:
            embed = create_error_embed(
                "Answer Too Short",
                "Please provide an answer with at least 5 characters!"
            )
            await ctx.send(embed=embed)
            return
        
        # Get current QOTD ID (daily)
        current_qotd_id = f"qotd_{datetime.utcnow().strftime('%Y_%m_%d')}"
        
        # Add answer to database
        await db.add_qotd_submission(ctx.author.id, current_qotd_id, answer)
        
        embed = create_success_embed(
            "🧠 QOTD Answer Submitted!",
            f"Your answer has been recorded! Good luck!\n\n"
            f"**Your answer:** {answer[:150]}{'...' if len(answer) > 150 else ''}"
        )
        
        await ctx.send(embed=embed)
        
        # Give XP for participation
        await db.update_user_activity(ctx.author.id, str(ctx.author), 15)  # Bonus XP for QOTD

    @commands.command(name='challenge-submissions', help='View submissions for current challenge (Mod only)')
    @commands.has_permissions(manage_messages=True)
    async def challenge_submissions(self, ctx):
        """View submissions for the current challenge (Moderator only)"""
        current_challenge_id = f"challenge_{datetime.utcnow().strftime('%Y_%W')}"
        submissions = await db.get_challenge_submissions(current_challenge_id)
        
        if not submissions:
            embed = create_info_embed(
                "No Submissions",
                "No submissions found for the current challenge."
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="📋 Current Challenge Submissions",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        for i, (user_id, link, date, status) in enumerate(submissions[:10], 1):
            user = self.bot.get_user(user_id)
            username = user.display_name if user else f"Unknown User ({user_id})"
            submit_date = datetime.fromisoformat(date).strftime("%m/%d %H:%M")
            
            embed.add_field(
                name=f"#{i} - {username}",
                value=f"[View Submission]({link})\n**Submitted:** {submit_date}\n**Status:** {status.title()}",
                inline=False
            )
        
        if len(submissions) > 10:
            embed.set_footer(text=f"Showing 10 of {len(submissions)} submissions")
        
        await ctx.send(embed=embed)

    @commands.command(name='qotd-winner', help='Set QOTD winner (Mod only)')
    @commands.has_permissions(manage_messages=True)
    async def set_qotd_winner(self, ctx, member: discord.Member):
        """Set the QOTD winner (Moderator only)"""
        current_qotd_id = f"qotd_{datetime.utcnow().strftime('%Y_%m_%d')}"
        
        await db.set_qotd_winner(member.id, current_qotd_id)
        
        embed = create_success_embed(
            "🏆 QOTD Winner Announced!",
            f"Congratulations {member.mention} for winning today's QOTD!\n\n"
            f"🎉 You've earned the **Code Master** role and bonus XP!"
        )
        
        await ctx.send(embed=embed)
        
        # Give bonus XP to winner
        await db.update_user_activity(member.id, str(member), 100)  # Big bonus for winning
        
        # Try to assign Code Master role
        try:
            code_master_role = discord.utils.get(ctx.guild.roles, name="Code Master")
            if code_master_role:
                await member.add_roles(code_master_role, reason="QOTD Winner")
        except discord.Forbidden:
            pass

    @commands.command(name='reload-data', help='Reload questions, challenges, and quotes (Admin only)')
    @commands.has_permissions(administrator=True)
    async def reload_data(self, ctx):
        """Reload data files (Admin only)"""
        try:
            self.load_data()
            embed = create_success_embed(
                "🔄 Data Reloaded",
                f"Successfully reloaded:\n"
                f"• {len(self.questions)} questions\n"
                f"• {len(self.challenges)} challenges\n"
                f"• {len(self.quotes)} quotes"
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = create_error_embed(
                "Reload Failed",
                f"Failed to reload data: {str(e)}"
            )
            await ctx.send(embed=embed)

    # Slash Commands
    @app_commands.command(name="quote", description="Get a random motivational/programming quote")
    async def slash_quote(self, interaction: discord.Interaction):
        """Slash command version of quote"""
        if not self.quotes:
            embed = create_error_embed("No Quotes", "No quotes available at the moment!")
            await interaction.response.send_message(embed=embed)
            return
        
        quote_text = get_random_quote(self.quotes)
        
        embed = discord.Embed(
            title="💡 Daily Inspiration",
            description=f"*{quote_text}*",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Stay motivated, keep coding! 🚀")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="question", description="Get a random programming question")
    async def slash_question(self, interaction: discord.Interaction):
        """Slash command version of question"""
        if not self.questions:
            embed = create_error_embed("No Questions", "No questions available at the moment!")
            await interaction.response.send_message(embed=embed)
            return
        
        question_data = get_random_question(self.questions)
        
        embed = discord.Embed(
            title="🧠 Random Programming Question",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        if isinstance(question_data, dict):
            embed.add_field(
                name="Question",
                value=question_data.get('question', 'No question available'),
                inline=False
            )
            if 'difficulty' in question_data:
                embed.add_field(
                    name="Difficulty",
                    value=question_data['difficulty'],
                    inline=True
                )
            if 'category' in question_data:
                embed.add_field(
                    name="Category",
                    value=question_data['category'],
                    inline=True
                )
        else:
            embed.add_field(
                name="Question",
                value=str(question_data),
                inline=False
            )
        
        embed.set_footer(text="Think you know the answer? Share it in the thread! 💭")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="meme", description="Get a random programming meme")
    async def slash_meme(self, interaction: discord.Interaction):
        """Slash command version of meme"""
        await interaction.response.defer()
        
        meme = await fetch_programming_meme()
        
        if meme.startswith('http'):
            # It's an image URL
            embed = discord.Embed(
                title="😄 Programming Meme",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.set_image(url=meme)
            embed.set_footer(text="Hope this made you smile! 😊")
        else:
            # It's a text meme
            embed = discord.Embed(
                title="😄 Programming Meme",
                description=meme,
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="Hope this made you smile! 😊")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="suggest", description="Submit a suggestion for the server")
    @app_commands.describe(suggestion="Your suggestion for improving the server")
    async def slash_suggest(self, interaction: discord.Interaction, suggestion: str):
        """Slash command version of suggest"""
        # Sanitize input
        suggestion = sanitize_input(suggestion, 1000)
        
        if len(suggestion.strip()) < 10:
            embed = create_error_embed(
                "Suggestion Too Short",
                "Please provide a suggestion with at least 10 characters!"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Add to database
        await db.add_suggestion(interaction.user.id, suggestion)
        
        # Create embed for user confirmation
        embed = create_success_embed(
            "💡 Suggestion Submitted!",
            f"Your suggestion has been submitted and will be reviewed by the staff.\n\n"
            f"**Your suggestion:** {suggestion[:200]}{'...' if len(suggestion) > 200 else ''}"
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Send to suggestions channel
        suggestions_channel_id = int(os.getenv('SUGGESTIONS_CHANNEL_ID', 0))
        if suggestions_channel_id:
            suggestions_channel = self.bot.get_channel(suggestions_channel_id)
            if suggestions_channel:
                suggestion_embed = discord.Embed(
                    title="💡 New Suggestion",
                    description=suggestion,
                    color=discord.Color.purple(),
                    timestamp=datetime.utcnow()
                )
                suggestion_embed.set_author(
                    name=f"{interaction.user.display_name}",
                    icon_url=interaction.user.display_avatar.url
                )
                suggestion_embed.set_footer(text=f"User ID: {interaction.user.id}")
                
                suggestion_msg = await suggestions_channel.send(embed=suggestion_embed)
                
                # Add reaction options
                await suggestion_msg.add_reaction("👍")
                await suggestion_msg.add_reaction("👎")
                await suggestion_msg.add_reaction("🤔")

    @app_commands.command(name="submit-challenge", description="Submit a link for the current coding challenge")
    @app_commands.describe(link="URL to your challenge solution")
    async def slash_submit_challenge(self, interaction: discord.Interaction, link: str):
        """Slash command version of submit-challenge"""
        if not is_valid_url(link):
            embed = create_error_embed(
                "Invalid URL", 
                "Please provide a valid URL for your submission!"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get current challenge ID
        current_challenge_id = f"challenge_{datetime.utcnow().strftime('%Y_%W')}"
        
        # Add submission to database
        await db.add_challenge_submission(interaction.user.id, current_challenge_id, link)
        
        # Create success embed
        embed = create_success_embed(
            "🎯 Challenge Submission Received!",
            f"**Participant:** {interaction.user.mention}\n"
            f"**Submission:** [View Submission]({link})\n"
            f"**Submitted:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Also send to mod-tools channel if configured
        mod_tools_channel_id = int(os.getenv('MOD_TOOLS_CHANNEL_ID', 0))
        if mod_tools_channel_id:
            mod_channel = self.bot.get_channel(mod_tools_channel_id)
            if mod_channel:
                mod_embed = create_info_embed(
                    "📝 New Challenge Submission",
                    f"**Participant:** {interaction.user} ({interaction.user.id})\n"
                    f"**Submission:** [View Submission]({link})"
                )
                await mod_channel.send(embed=mod_embed)
        
        # Give XP for submission
        await db.update_user_activity(interaction.user.id, str(interaction.user), 25)

async def setup(bot):
    await bot.add_cog(CommunityCommands(bot))