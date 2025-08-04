import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import numpy as np
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
from collections import defaultdict
from utils.database import db
from utils.helpers import create_success_embed, create_error_embed, create_info_embed

class AnalyticsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="stats", description="Get server activity statistics")
    @app_commands.describe(timeframe="Time period (day, week, month)")
    async def server_stats(self, interaction: discord.Interaction, timeframe: str = "week"):
        """Display server statistics"""
        if timeframe not in ["day", "week", "month"]:
            await interaction.response.send_message("❌ Invalid timeframe! Use: day, week, or month", ephemeral=True)
            return
        
        # Calculate time range
        now = datetime.utcnow()
        if timeframe == "day":
            start_time = now - timedelta(days=1)
            title = "📊 Last 24 Hours"
        elif timeframe == "week":
            start_time = now - timedelta(weeks=1)
            title = "📊 Last 7 Days"
        else:  # month
            start_time = now - timedelta(days=30)
            title = "📊 Last 30 Days"
        
        embed = discord.Embed(
            title=f"{title} - Server Statistics",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        # Get basic stats
        guild = interaction.guild
        
        # Member activity (simplified - you'd expand this with database queries)
        total_members = guild.member_count
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        
        embed.add_field(name="👥 Total Members", value=total_members, inline=True)
        embed.add_field(name="🟢 Online Now", value=online_members, inline=True)
        embed.add_field(name="📈 Activity Rate", value=f"{(online_members/total_members*100):.1f}%", inline=True)
        
        # Channel activity
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        
        embed.add_field(name="💬 Text Channels", value=text_channels, inline=True)
        embed.add_field(name="🔊 Voice Channels", value=voice_channels, inline=True)
        embed.add_field(name="📁 Categories", value=len(guild.categories), inline=True)
        
        # XP and engagement stats (from your database)
        try:
            # These would be actual database queries
            embed.add_field(name="🎯 Total XP Gained", value="Coming Soon", inline=True)
            embed.add_field(name="🏆 New Level Ups", value="Coming Soon", inline=True)
            embed.add_field(name="💭 QOTD Submissions", value="Coming Soon", inline=True)
        except:
            pass
        
        embed.set_footer(text=f"Statistics for {guild.name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="activity-graph", description="Generate activity graph for the server")
    @app_commands.describe(days="Number of days to analyze (1-30)")
    async def activity_graph(self, interaction: discord.Interaction, days: int = 7):
        """Generate and send activity graph"""
        if days < 1 or days > 30:
            await interaction.response.send_message("❌ Days must be between 1 and 30!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # Generate sample data (you'd replace with real database queries)
            dates = [(datetime.utcnow() - timedelta(days=i)).strftime("%m/%d") for i in range(days-1, -1, -1)]
            
            # Sample activity data - replace with real data from your database
            messages = [random.randint(50, 200) for _ in range(days)]
            new_members = [random.randint(0, 5) for _ in range(days)]
            xp_gained = [random.randint(100, 500) for _ in range(days)]
            
            # Create the graph
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
            fig.suptitle(f'Server Activity - Last {days} Days', fontsize=16, fontweight='bold')
            
            # Messages chart
            ax1.plot(dates, messages, color='#7289da', marker='o', linewidth=2, markersize=4)
            ax1.set_title('Messages Sent', fontweight='bold')
            ax1.set_ylabel('Messages')
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # New members chart
            ax2.bar(dates, new_members, color='#43b581', alpha=0.8)
            ax2.set_title('New Members', fontweight='bold')
            ax2.set_ylabel('New Members')
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
            
            # XP gained chart
            ax3.plot(dates, xp_gained, color='#faa61a', marker='s', linewidth=2, markersize=4)
            ax3.set_title('XP Gained', fontweight='bold')
            ax3.set_ylabel('XP Points')
            ax3.set_xlabel('Date')
            ax3.grid(True, alpha=0.3)
            ax3.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Save to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            # Send the graph
            file = discord.File(buffer, filename='activity_graph.png')
            
            embed = discord.Embed(
                title="📈 Server Activity Graph",
                description=f"Activity analysis for the last {days} days",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.set_image(url="attachment://activity_graph.png")
            
            await interaction.followup.send(embed=embed, file=file)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error generating graph: {str(e)}")

    @app_commands.command(name="leaderboard-chart", description="Generate XP leaderboard chart")
    async def leaderboard_chart(self, interaction: discord.Interaction):
        """Generate visual leaderboard chart"""
        await interaction.response.defer()
        
        try:
            # Get top 10 users from database (simplified)
            # In real implementation, you'd query your database
            sample_data = [
                ("User1", 2500),
                ("User2", 2200),
                ("User3", 1800),
                ("User4", 1500),
                ("User5", 1200),
                ("User6", 1000),
                ("User7", 800),
                ("User8", 600),
                ("User9", 400),
                ("User10", 200)
            ]
            
            usernames = [data[0] for data in sample_data]
            xp_values = [data[1] for data in sample_data]
            
            # Create horizontal bar chart
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Create color gradient
            colors = plt.cm.viridis(np.linspace(0, 1, len(usernames)))
            
            bars = ax.barh(usernames, xp_values, color=colors)
            
            # Customize the chart
            ax.set_xlabel('XP Points', fontweight='bold')
            ax.set_title('🏆 Top 10 XP Leaderboard', fontsize=16, fontweight='bold', pad=20)
            
            # Add value labels on bars
            for i, (bar, value) in enumerate(zip(bars, xp_values)):
                ax.text(bar.get_width() + 25, bar.get_y() + bar.get_height()/2, 
                       f'{value} XP', va='center', fontweight='bold')
            
            # Add rank numbers
            for i, (bar, username) in enumerate(zip(bars, usernames)):
                ax.text(bar.get_width()/2, bar.get_y() + bar.get_height()/2, 
                       f'#{i+1}', va='center', ha='center', fontweight='bold', 
                       color='white', fontsize=10)
            
            ax.grid(True, axis='x', alpha=0.3)
            plt.tight_layout()
            
            # Save to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            # Send the chart
            file = discord.File(buffer, filename='leaderboard_chart.png')
            
            embed = discord.Embed(
                title="🏆 XP Leaderboard Chart",
                description="Visual representation of top server members",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            embed.set_image(url="attachment://leaderboard_chart.png")
            
            await interaction.followup.send(embed=embed, file=file)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error generating chart: {str(e)}")

    @commands.command(name='channel-stats', help='Get statistics for a specific channel')
    @commands.has_permissions(manage_messages=True)
    async def channel_stats(self, ctx, channel: discord.TextChannel = None):
        """Get detailed channel statistics"""
        if channel is None:
            channel = ctx.channel
        
        embed = discord.Embed(
            title=f"📊 {channel.name} Statistics",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Basic channel info
        embed.add_field(name="📁 Category", value=channel.category.name if channel.category else "None", inline=True)
        embed.add_field(name="📅 Created", value=channel.created_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="🔒 NSFW", value="Yes" if channel.is_nsfw() else "No", inline=True)
        
        # Message analysis (simplified - would need message history scan)
        embed.add_field(name="💬 Recent Activity", value="Analyzing...", inline=True)
        embed.add_field(name="👥 Active Users", value="Coming Soon", inline=True)
        embed.add_field(name="📈 Daily Average", value="Coming Soon", inline=True)
        
        if channel.topic:
            embed.add_field(name="📝 Topic", value=channel.topic[:100] + "..." if len(channel.topic) > 100 else channel.topic, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AnalyticsCommands(bot))
