import discord
from discord.ext import commands
import asyncio
import random
import os
from datetime import datetime
from utils.database import db
from utils.helpers import get_level_role, create_success_embed

class MessageHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.level_up_messages = [
            "🎉 Congratulations! You've leveled up!",
            "🚀 Level up! You're climbing the ranks!",
            "⭐ Amazing! You've reached a new level!",
            "🔥 Level up! Keep up the great work!",
            "🎊 Fantastic! You've advanced to the next level!"
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle incoming messages for XP tracking"""
        # Ignore bot messages
        if message.author.bot:
            return

        # Ignore DMs
        if not isinstance(message.channel, discord.TextChannel):
            return

        # Check AFK system
        await self.handle_afk_system(message)

        # Ignore commands (they're handled separately)
        if message.content.startswith(('!', '/', '.', '?', '-')):
            await self.bot.process_commands(message)
            return

        # Check if user is muted
        if await db.is_user_muted(message.author.id):
            try:
                await message.delete()
                return
            except discord.Forbidden:
                pass

        # Track user activity and give XP
        await self.handle_user_activity(message)

        # Process commands
        await self.bot.process_commands(message)

    async def handle_user_activity(self, message):
        """Handle user activity tracking and XP rewards"""
        user = message.author
        
        # Ensure user exists in database
        await db.add_user(user.id, str(user))
        
        # Get current user stats before XP gain
        old_stats = await db.get_user_stats(user.id)
        old_level = old_stats['level'] if old_stats else 1
        
        # Calculate XP based on message content
        base_xp = 5
        bonus_xp = 0
        
        # Bonus XP for longer messages
        if len(message.content) > 50:
            bonus_xp += 2
        if len(message.content) > 100:
            bonus_xp += 3
        
        # Bonus XP for helpful keywords
        helpful_keywords = [
            'help', 'tutorial', 'guide', 'explain', 'documentation',
            'debug', 'error', 'solution', 'fix', 'problem', 'question'
        ]
        
        message_lower = message.content.lower()
        for keyword in helpful_keywords:
            if keyword in message_lower:
                bonus_xp += 2
                break
        
        # Random bonus (10% chance for 2-5 extra XP)
        if random.random() < 0.1:
            bonus_xp += random.randint(2, 5)
        
        total_xp = base_xp + bonus_xp
        
        # Update user activity with XP
        await db.update_user_activity(user.id, str(user), total_xp)
        
        # Get new stats to check for level up
        new_stats = await db.get_user_stats(user.id)
        new_level = new_stats['level'] if new_stats else 1
        
        # Check for level up
        if new_level > old_level:
            await self.handle_level_up(message, user, old_level, new_level)

    async def handle_level_up(self, message, user, old_level, new_level):
        """Handle level up events"""
        # Create level up embed
        level_up_msg = random.choice(self.level_up_messages)
        role_name = get_level_role(new_level)
        
        embed = create_success_embed(
            f"🎉 Level Up!",
            f"{user.mention} {level_up_msg}\n\n"
            f"**Old Level:** {old_level}\n"
            f"**New Level:** {new_level}\n"
            f"**Role Tier:** {role_name}"
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Send level up message
        level_up_notification = await message.channel.send(embed=embed)
        
        # Delete after 10 seconds to avoid spam
        await asyncio.sleep(10)
        try:
            await level_up_notification.delete()
        except discord.NotFound:
            pass
        
        # Try to assign appropriate role
        await self.assign_level_role(message.guild, user, new_level)
        
        # DM user about level up
        try:
            dm_embed = create_success_embed(
                "🎉 Level Up!",
                f"Congratulations! You've reached **Level {new_level}** in **{message.guild.name}**!\n\n"
                f"**Role Tier:** {role_name}\n"
                f"Keep being active to unlock more rewards! 🚀"
            )
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass

    async def assign_level_role(self, guild, user, level):
        """Assign appropriate level-based role to user"""
        role_mapping = {
            5: "Active",
            15: "Very Active", 
            30: "Ultra Active",
            50: "Elite Member"
        }
        
        # Find the highest role the user qualifies for
        target_role_name = None
        for required_level in sorted(role_mapping.keys(), reverse=True):
            if level >= required_level:
                target_role_name = role_mapping[required_level]
                break
        
        if not target_role_name:
            return
        
        try:
            # Get the target role
            target_role = discord.utils.get(guild.roles, name=target_role_name)
            
            if target_role and target_role not in user.roles:
                # Remove old level roles
                old_roles_to_remove = []
                for role_name in role_mapping.values():
                    if role_name != target_role_name:
                        old_role = discord.utils.get(guild.roles, name=role_name)
                        if old_role and old_role in user.roles:
                            old_roles_to_remove.append(old_role)
                
                # Remove old roles
                if old_roles_to_remove:
                    await user.remove_roles(*old_roles_to_remove, reason="Level role update")
                
                # Add new role
                await user.add_roles(target_role, reason=f"Reached level {level}")
                
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error assigning role: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Handle new member joins"""
        # Add user to database
        await db.add_user(member.id, str(member))
        
        # Send welcome message to joins-n-leaves channel if configured
        joins_channel_id = int(os.getenv('JOINS_LEAVES_CHANNEL_ID', 0))
        if joins_channel_id:
            channel = self.bot.get_channel(joins_channel_id)
            if channel:
                embed = discord.Embed(
                    title="👋 Welcome to The CodeVerse Hub!",
                    description=f"Welcome {member.mention}! We're glad to have you here.\n\n"
                               f"🔹 Make sure to read the rules in <#rules-channel>\n"
                               f"🔹 Introduce yourself in <#lobby>\n"
                               f"🔹 Start chatting to earn XP and level up!\n\n"
                               f"**Member #{len(member.guild.members)}**",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text="Enjoy your stay! 🚀")
                
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Handle member leaves"""
        # Send goodbye message to joins-n-leaves channel if configured
        joins_channel_id = int(os.getenv('JOINS_LEAVES_CHANNEL_ID', 0))
        if joins_channel_id:
            channel = self.bot.get_channel(joins_channel_id)
            if channel:
                embed = discord.Embed(
                    title="👋 Member Left",
                    description=f"**{member.display_name}** has left the server.\n"
                               f"We'll miss you! 😢",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Global command error handler"""
        # Don't handle errors that are already handled by command-specific handlers
        if hasattr(ctx.command, 'on_error'):
            return
        
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You don't have permission to use this command!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
        
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Argument",
                description=f"Missing required argument: `{error.param}`\n"
                           f"Use `!help {ctx.command}` for usage information.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=15)
        
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Invalid Argument", 
                description="Invalid argument provided!\n"
                           f"Use `!help {ctx.command}` for usage information.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=15)
        
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Command on Cooldown",
                description=f"This command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed, delete_after=10)
        
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="❌ Member Not Found",
                description="Could not find the specified member!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
        
        else:
            # Log unexpected errors
            print(f"Unhandled error in command {ctx.command}: {error}")
            
            embed = discord.Embed(
                title="❌ An Error Occurred",
                description="An unexpected error occurred while processing your command.\n"
                           "Please try again later or contact an administrator.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=15)
    
    async def handle_afk_system(self, message):
        """Handle AFK system - check mentions and remove AFK status"""
        # Remove AFK status if user sends a message
        afk_data = await db.get_user_afk(message.author.id)
        if afk_data:
            await db.remove_user_afk(message.author.id)
            
            embed = discord.Embed(
                title="👋 Welcome Back!",
                description=f"**{message.author.display_name}**, you're no longer AFK!",
                color=discord.Color.green()
            )
            
            welcome_msg = await message.channel.send(embed=embed)
            await asyncio.sleep(5)
            await welcome_msg.delete()
        
        # Check for AFK mentions
        for mention in message.mentions:
            if mention.bot:
                continue
                
            afk_data = await db.get_user_afk(mention.id)
            if afk_data:
                reason, afk_since = afk_data
                afk_time = datetime.fromisoformat(afk_since)
                time_diff = datetime.utcnow() - afk_time
                
                # Format time difference
                if time_diff.days > 0:
                    time_str = f"{time_diff.days} day(s) ago"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    time_str = f"{hours} hour(s) ago"
                elif time_diff.seconds > 60:
                    minutes = time_diff.seconds // 60
                    time_str = f"{minutes} minute(s) ago"
                else:
                    time_str = "just now"
                
                embed = discord.Embed(
                    title="😴 AFK User",
                    description=f"**{mention.display_name}** is currently AFK\n"
                              f"**Reason:** {reason}\n"
                              f"**Since:** {time_str}",
                    color=discord.Color.orange()
                )
                
                afk_msg = await message.channel.send(embed=embed)
                await asyncio.sleep(10)
                await afk_msg.delete()

async def setup(bot):
    await bot.add_cog(MessageHandler(bot))