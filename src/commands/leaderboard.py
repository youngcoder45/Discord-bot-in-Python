import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from utils.database import db
from utils.helpers import (
    create_info_embed,
    create_error_embed,
    create_success_embed,
    get_level_role,
    get_xp_for_next_level,
    create_progress_bar,
    get_relative_time
)

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='leaderboard', aliases=['lb', 'top'], help='Display the XP leaderboard')
    async def leaderboard(self, ctx, limit: int = 10):
        """Display the XP leaderboard"""
        if limit < 1 or limit > 25:
            embed = create_error_embed(
                "Invalid Limit",
                "Please provide a limit between 1 and 25!"
            )
            await ctx.send(embed=embed)
            return
        
        leaderboard_data = await db.get_leaderboard(limit)
        
        if not leaderboard_data:
            embed = create_info_embed(
                "Empty Leaderboard",
                "No users found in the leaderboard yet!"
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="🏆 The CodeVerse Hub Leaderboard",
            color=discord.Color.gold(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        medal_emojis = ["🥇", "🥈", "🥉"]
        leaderboard_text = ""
        
        for rank, (user_id, username, xp, level, message_count) in enumerate(leaderboard_data, 1):
            user = self.bot.get_user(user_id)
            display_name = user.display_name if user else username
            
            # Get medal emoji for top 3
            medal = medal_emojis[rank - 1] if rank <= 3 else f"**{rank}.**"
            
            # Create level role text
            role_name = get_level_role(level)
            
            leaderboard_text += f"{medal} **{display_name}** - Level {level}\n"
            leaderboard_text += f"   🔥 {xp:,} XP • 💬 {message_count:,} messages • {role_name}\n\n"
        
        embed.description = leaderboard_text
        embed.set_footer(text=f"Showing top {len(leaderboard_data)} members")
        
        # Add thumbnail
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        
        await ctx.send(embed=embed)

    @commands.command(name='rank', aliases=['level', 'stats'], help='Check your or someone\'s rank and stats')
    async def rank(self, ctx, member: discord.Member = None):
        """Check rank and stats for a user"""
        target = member or ctx.author
        
        # Get user stats
        stats = await db.get_user_stats(target.id)
        
        if not stats:
            if target == ctx.author:
                embed = create_info_embed(
                    "No Stats Yet",
                    "You haven't gained any XP yet! Start chatting to earn XP and climb the leaderboard!"
                )
            else:
                embed = create_info_embed(
                    "No Stats Found",
                    f"{target.display_name} hasn't gained any XP yet!"
                )
            await ctx.send(embed=embed)
            return
        
        xp = stats['xp']
        level = stats['level']
        message_count = stats['message_count']
        join_date = datetime.fromisoformat(stats['join_date']) if stats['join_date'] else None
        warnings = stats['total_warnings']
        
        # Calculate rank
        leaderboard_data = await db.get_leaderboard(1000)  # Get more users to find rank
        rank = None
        for i, (user_id, _, _, _, _) in enumerate(leaderboard_data, 1):
            if user_id == target.id:
                rank = i
                break
        
        # Calculate XP for next level
        xp_needed = get_xp_for_next_level(xp)
        current_level_xp = ((level - 1) ** 2) * 100
        xp_in_current_level = xp - current_level_xp
        xp_for_current_level = (level ** 2) * 100 - current_level_xp
        
        # Create embed
        embed = discord.Embed(
            title=f"📊 Stats for {target.display_name}",
            color=discord.Color.blue(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        # Set user avatar
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # Basic stats
        embed.add_field(
            name="🏆 Rank & Level",
            value=f"**Rank:** #{rank if rank else 'Unranked'}\n"
                  f"**Level:** {level}\n"
                  f"**Role:** {get_level_role(level)}",
            inline=True
        )
        
        embed.add_field(
            name="🔥 Experience",
            value=f"**Total XP:** {xp:,}\n"
                  f"**Messages:** {message_count:,}\n"
                  f"**Next Level:** {xp_needed:,} XP",
            inline=True
        )
        
        embed.add_field(
            name="⚠️ Moderation",
            value=f"**Warnings:** {warnings}",
            inline=True
        )
        
        # Progress bar for current level
        progress = create_progress_bar(xp_in_current_level, xp_for_current_level)
        embed.add_field(
            name=f"📈 Level {level} Progress",
            value=f"{progress}\n{xp_in_current_level:,}/{xp_for_current_level:,} XP",
            inline=False
        )
        
        # Join date if available
        if join_date:
            relative_time = get_relative_time(join_date)
            embed.add_field(
                name="📅 Member Since",
                value=f"{join_date.strftime('%B %d, %Y')} ({relative_time})",
                inline=False
            )
        
        embed.set_footer(text="Keep chatting to gain more XP! 🚀")
        
        await ctx.send(embed=embed)

    @commands.command(name='xp-leaderboard', aliases=['xplb'], help='XP-only leaderboard')
    async def xp_leaderboard(self, ctx, limit: int = 10):
        """Display a simple XP-only leaderboard"""
        if limit < 1 or limit > 25:
            embed = create_error_embed(
                "Invalid Limit",
                "Please provide a limit between 1 and 25!"
            )
            await ctx.send(embed=embed)
            return
        
        leaderboard_data = await db.get_leaderboard(limit)
        
        if not leaderboard_data:
            embed = create_info_embed(
                "Empty Leaderboard",
                "No users found in the leaderboard yet!"
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="🔥 XP Leaderboard",
            color=discord.Color.orange(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        leaderboard_text = ""
        
        for rank, (user_id, username, xp, level, message_count) in enumerate(leaderboard_data, 1):
            user = self.bot.get_user(user_id)
            display_name = user.display_name if user else username
            
            leaderboard_text += f"**{rank}.** {display_name} - **{xp:,}** XP\n"
        
        embed.description = leaderboard_text
        embed.set_footer(text=f"Showing top {len(leaderboard_data)} members by XP")
        
        await ctx.send(embed=embed)

    @commands.command(name='level-roles', aliases=['roles'], help='Show level-based roles')
    async def level_roles(self, ctx):
        """Show information about level-based roles"""
        embed = discord.Embed(
            title="🎭 Level-Based Roles",
            description="Here are the roles you can earn by being active in the server!",
            color=discord.Color.purple(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        roles_info = [
            ("Newcomer", "Level 1-4", "🆕", "Just getting started!"),
            ("Active", "Level 5-14", "🟢", "Regular community member"),
            ("Very Active", "Level 15-29", "🔥", "Highly engaged member"),
            ("Ultra Active", "Level 30-49", "⚡", "Super active contributor"),
            ("Elite Member", "Level 50+", "👑", "Legendary status!")
        ]
        
        for role_name, level_range, emoji, description in roles_info:
            embed.add_field(
                name=f"{emoji} {role_name}",
                value=f"**{level_range}**\n{description}",
                inline=True
            )
        
        embed.add_field(
            name="💡 How to Level Up",
            value="• Send messages (+5 XP per minute)\n"
                  "• Submit QOTD answers (+15 XP)\n"
                  "• Submit challenge solutions (+25 XP)\n"
                  "• Win QOTD/Challenges (+100 XP)",
            inline=False
        )
        
        embed.set_footer(text="Stay active and climb the ranks! 🚀")
        
        await ctx.send(embed=embed)

    @commands.command(name='give-xp', help='Give XP to a user (Admin only)')
    @commands.has_permissions(administrator=True)
    async def give_xp(self, ctx, member: discord.Member, amount: int):
        """Give XP to a user (Admin only)"""
        if amount <= 0:
            embed = create_error_embed(
                "Invalid Amount",
                "XP amount must be positive!"
            )
            await ctx.send(embed=embed)
            return
        
        if amount > 1000:
            embed = create_error_embed(
                "Amount Too Large",
                "Maximum XP amount is 1000 per command!"
            )
            await ctx.send(embed=embed)
            return
        
        # Add user if they don't exist
        await db.add_user(member.id, str(member))
        
        # Give XP
        await db.update_user_activity(member.id, str(member), amount)
        
        embed = create_success_embed(
            "🎁 XP Awarded",
            f"**{amount}** XP has been given to {member.mention}!\n"
            f"**Moderator:** {ctx.author.mention}"
        )
        
        await ctx.send(embed=embed)
        
        # Try to notify the user
        try:
            dm_embed = create_success_embed(
                "🎁 You Received XP!",
                f"You've been awarded **{amount}** XP in **{ctx.guild.name}**!\n"
                f"**Given by:** {ctx.author}"
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass

    @commands.command(name='reset-xp', help='Reset a user\'s XP (Admin only)')
    @commands.has_permissions(administrator=True)
    async def reset_xp(self, ctx, member: discord.Member):
        """Reset a user's XP (Admin only)"""
        # This would require a database method to reset XP
        # For now, we'll give them 0 XP (effectively resetting)
        await db.add_user(member.id, str(member))
        
        embed = create_success_embed(
            "🔄 XP Reset",
            f"XP has been reset for {member.mention}!\n"
            f"**Moderator:** {ctx.author.mention}"
        )
        
        await ctx.send(embed=embed)

    # Slash Commands
    @app_commands.command(name="rank", description="Check your current rank and XP")
    async def slash_rank(self, interaction: discord.Interaction, member: discord.Member = None):
        """Slash command version of rank"""
        target_member = member or interaction.user
        
        # Get user data
        user_data = await db.get_user_stats(target_member.id)
        
        if not user_data:
            embed = create_error_embed(
                "No Data Found",
                f"No activity data found for {target_member.mention}!"
            )
            await interaction.response.send_message(embed=embed)
            return
        
        xp = user_data['xp']
        level = user_data['level']
        messages = user_data['message_count']
        
        # Calculate rank
        all_users = await db.get_leaderboard(100)  # Get top 100 to find rank
        rank = None
        for i, user in enumerate(all_users, 1):
            # user is a tuple: (user_id, username, xp, level, message_count)
            if user[0] == target_member.id:
                rank = i
                break
        
        # XP for next level
        xp_for_next = get_xp_for_next_level(level + 1)
        xp_needed = xp_for_next - xp
        
        # Progress bar
        current_level_xp = get_xp_for_next_level(level)
        progress = (xp - current_level_xp) / (xp_for_next - current_level_xp)
        progress_bar = create_progress_bar(int((xp - current_level_xp)), int((xp_for_next - current_level_xp)))
        
        # Get role info
        role_name = get_level_role(level)
        
        embed = discord.Embed(
            title=f"📊 Rank & Stats - {target_member.display_name}",
            color=discord.Color.blue(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        embed.set_thumbnail(url=target_member.display_avatar.url)
        
        embed.add_field(
            name="🏆 Rank",
            value=f"#{rank}" if rank else "Not ranked",
            inline=True
        )
        embed.add_field(
            name="⭐ Level",
            value=str(level),
            inline=True
        )
        embed.add_field(
            name="✨ Total XP",
            value=f"{xp:,}",
            inline=True
        )
        embed.add_field(
            name="💬 Messages",
            value=f"{messages:,}",
            inline=True
        )
        embed.add_field(
            name="🎯 Next Level",
            value=f"{xp_needed:,} XP needed",
            inline=True
        )
        embed.add_field(
            name="🎭 Current Role",
            value=role_name,
            inline=True
        )
        embed.add_field(
            name="📈 Progress",
            value=f"{progress_bar}\n{int(progress * 100)}% to Level {level + 1}",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="View the server XP leaderboard")
    @app_commands.describe(page="Page number to view")
    async def slash_leaderboard(self, interaction: discord.Interaction, page: int = 1):
        """Slash command version of leaderboard"""
        page = max(1, page)  # Ensure page is at least 1
        
        # Get leaderboard data
        leaderboard = await db.get_leaderboard(100)  # Get top 100
        
        if not leaderboard:
            embed = create_error_embed(
                "No Data",
                "No leaderboard data available yet!"
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Pagination
        per_page = 10
        total_pages = (len(leaderboard) + per_page - 1) // per_page
        page = min(page, total_pages)
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_data = leaderboard[start_idx:end_idx]
        
        embed = discord.Embed(
            title="🏆 CodeVerse Hub Leaderboard",
            description=f"Top members by XP (Page {page}/{total_pages})",
            color=discord.Color.gold(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        leaderboard_text = ""
        for i, user_data in enumerate(page_data, start_idx + 1):
            # user_data is a tuple: (user_id, username, xp, level, message_count)
            user_id = user_data[0]
            username = user_data[1]
            xp = user_data[2]
            level = user_data[3]
            
            # Try to get current member for display name
            user = interaction.guild.get_member(user_id)
            display_name = user.display_name if user else username
            
            # Add medal emoji for top 3
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"**{i}.**"
            
            leaderboard_text += f"{medal} {display_name} - Level {level} ({xp:,} XP)\n"
        
        embed.add_field(
            name="Rankings",
            value=leaderboard_text or "No data available",
            inline=False
        )
        
        if total_pages > 1:
            embed.set_footer(text=f"Page {page}/{total_pages} • Use /leaderboard <page> to navigate")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="level", description="Check your level information")
    async def slash_level(self, interaction: discord.Interaction, member: discord.Member = None):
        """Slash command version of level"""
        target_member = member or interaction.user
        
        # Get user data
        user_data = await db.get_user_stats(target_member.id)
        
        if not user_data:
            embed = create_error_embed(
                "No Data Found",
                f"No activity data found for {target_member.mention}!"
            )
            await interaction.response.send_message(embed=embed)
            return
        
        xp = user_data['xp']
        level = user_data['level']
        
        # XP for next level
        xp_for_next = get_xp_for_next_level(level + 1)
        xp_needed = xp_for_next - xp
        
        # Progress calculation
        current_level_xp = get_xp_for_next_level(level)
        progress = (xp - current_level_xp) / (xp_for_next - current_level_xp)
        progress_bar = create_progress_bar(int((xp - current_level_xp)), int((xp_for_next - current_level_xp)))
        
        # Get role info
        role_name = get_level_role(level)
        next_role = get_level_role(level + 1)
        
        embed = discord.Embed(
            title=f"⭐ Level Information - {target_member.display_name}",
            color=discord.Color.purple(),
            timestamp=datetime.now(tz=timezone.utc)
        )
        
        embed.set_thumbnail(url=target_member.display_avatar.url)
        
        embed.add_field(
            name="🌟 Current Level",
            value=f"Level {level}",
            inline=True
        )
        embed.add_field(
            name="✨ Total XP",
            value=f"{xp:,}",
            inline=True
        )
        embed.add_field(
            name="🎯 XP Needed",
            value=f"{xp_needed:,}",
            inline=True
        )
        embed.add_field(
            name="🎭 Current Role",
            value=role_name,
            inline=True
        )
        embed.add_field(
            name="🚀 Next Role",
            value=next_role,
            inline=True
        )
        embed.add_field(
            name="📊 Progress",
            value=f"{progress_bar}\n{int(progress * 100)}% complete",
            inline=False
        )
        
        embed.set_footer(text="Keep being active to level up! 🌟")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))