import discord
from discord.ext import commands
import sqlite3
from utils.database import DATABASE_NAME
from utils.embeds import create_error_embed, create_success_embed, create_info_embed
from config import MODERATION_ROLE_ID

class Appeals(commands.Cog):
    """Unban appeal system"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle DM appeals"""
        # Only process DMs to the bot
        if not isinstance(message.channel, discord.DMChannel) or message.author.bot:
            return
        
        # Check if message contains appeal keywords
        content_lower = message.content.lower()
        appeal_keywords = ['unban', 'appeal', 'banned', 'sorry', 'apologize', 'mistake']
        
        if any(keyword in content_lower for keyword in appeal_keywords):
            # Store the appeal in database
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            
            # Check if user already has a pending appeal
            cursor.execute('SELECT id FROM unban_requests WHERE user_id = ? AND status = "pending"', (message.author.id,))
            existing = cursor.fetchone()
            
            if existing:
                embed = discord.Embed(
                    title="Appeal Already Submitted",
                    description="You already have a pending appeal. Please wait for staff to review it.",
                    color=0xf39c12
                )
                embed.set_footer(text="Professional Moderation System")
                await message.author.send(embed=embed)
                conn.close()
                return
            
            # Insert new appeal
            cursor.execute('''
                INSERT INTO unban_requests (user_id, reason)
                VALUES (?, ?)
            ''', (message.author.id, message.content))
            conn.commit()
            appeal_id = cursor.lastrowid
            conn.close()
            
            # Send confirmation to user
            embed = discord.Embed(
                title="Appeal Received",
                description="Your unban appeal has been submitted and will be reviewed by staff.",
                color=0x3498db
            )
            embed.add_field(name="Appeal ID", value=f"#{appeal_id}", inline=True)
            embed.add_field(name="Status", value="Pending Review", inline=True)
            embed.add_field(name="Next Steps", value="Staff will review your appeal and respond within 24-48 hours.", inline=False)
            embed.set_footer(text="Professional Moderation System")
            await message.author.send(embed=embed)
            
            # Notify staff in appeals channel
            for guild in self.bot.guilds:
                staff_role = guild.get_role(MODERATION_ROLE_ID)
                if staff_role:
                    for channel in guild.text_channels:
                        if 'appeal' in channel.name.lower() or 'staff' in channel.name.lower():
                            embed_staff = discord.Embed(
                                title="New Appeal Submitted",
                                description=f"Appeal #{appeal_id} from {message.author}",
                                color=0x3498db
                            )
                            embed_staff.add_field(name="User", value=f"{message.author} ({message.author.id})", inline=True)
                            embed_staff.add_field(name="Appeal Content", value=message.content[:500] + "..." if len(message.content) > 500 else message.content, inline=False)
                            embed_staff.add_field(name="Review Commands", value="`!appeals` to view all\n`!approve <id>` to approve\n`!deny <id> <reason>` to deny", inline=False)
                            await channel.send(embed=embed_staff)
                            break

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def appeals(self, ctx, status: str = "pending"):
        """View appeal requests"""
        valid_statuses = ["pending", "approved", "denied", "all"]
        if status not in valid_statuses:
            embed = create_error_embed("Invalid Status", f"Valid statuses: {', '.join(valid_statuses)}")
            await ctx.send(embed=embed)
            return
        
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        if status == "all":
            cursor.execute('SELECT id, user_id, reason, status, timestamp FROM unban_requests ORDER BY timestamp DESC LIMIT 20')
        else:
            cursor.execute('SELECT id, user_id, reason, status, timestamp FROM unban_requests WHERE status = ? ORDER BY timestamp DESC LIMIT 20', (status,))
        
        appeals = cursor.fetchall()
        conn.close()
        
        if not appeals:
            embed = create_info_embed("No Appeals", f"No {status} appeals found.")
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(title=f'{status.title()} Appeals', color=0x3498db)
        
        for appeal in appeals:
            appeal_id, user_id, reason, appeal_status, timestamp = appeal
            try:
                user = await self.bot.fetch_user(user_id)
                user_name = f"{user} ({user_id})"
            except:
                user_name = f"Unknown ({user_id})"
            
            status_emoji = {"pending": "🟡", "approved": "🟢", "denied": "🔴"}.get(appeal_status, "⚪")
            
            embed.add_field(
                name=f'{status_emoji} Appeal #{appeal_id}', 
                value=f'**User:** {user_name}\n**Status:** {appeal_status.title()}\n**Reason:** {reason[:100]}{"..." if len(reason) > 100 else ""}\n**Time:** {timestamp}', 
                inline=False
            )
        
        embed.set_footer(text=f"Use !approve <id> or !deny <id> <reason> to process appeals")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def approve(self, ctx, appeal_id: int, *, reason: str = "Appeal approved"):
        """Approve an unban appeal"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM unban_requests WHERE id = ? AND status = "pending"', (appeal_id,))
        result = cursor.fetchone()
        
        if not result:
            embed = create_error_embed("Appeal Not Found", "Appeal not found or already processed.")
            await ctx.send(embed=embed)
            conn.close()
            return
        
        user_id = result[0]
        cursor.execute('UPDATE unban_requests SET status = "approved" WHERE id = ?', (appeal_id,))
        conn.commit()
        conn.close()
        
        # Unban the user
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f'Appeal #{appeal_id} approved by {ctx.author}')
            
            # Clear points for unbanned user
            from utils.database import clear_user_points
            clear_user_points(user_id)
            
            embed = discord.Embed(title='Appeal Approved', color=0x2ecc71)
            embed.add_field(name='Appeal ID', value=f"#{appeal_id}", inline=True)
            embed.add_field(name='User', value=f'{user} ({user_id})', inline=True)
            embed.add_field(name='Approved By', value=ctx.author.mention, inline=True)
            embed.add_field(name='Reason', value=reason, inline=False)
            await ctx.send(embed=embed)
            
            # Send DM to user
            try:
                embed_dm = discord.Embed(
                    title="Appeal Approved",
                    description=f"Your appeal has been approved! You have been unbanned from **{ctx.guild.name}**.",
                    color=0x2ecc71
                )
                embed_dm.add_field(name="Appeal ID", value=f"#{appeal_id}", inline=True)
                embed_dm.add_field(name="Approved By", value=str(ctx.author), inline=True)
                embed_dm.add_field(name="Reason", value=reason, inline=False)
                embed_dm.add_field(name="Welcome Back", value="Please make sure to follow our community guidelines.", inline=False)
                embed_dm.set_footer(text="Professional Moderation System")
                await user.send(embed=embed_dm)
            except:
                pass
                
        except discord.NotFound:
            embed = create_error_embed("User Not Found", "User not found or not banned.")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = create_error_embed("Permission Error", "I don't have permission to unban this user.")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = create_error_embed("Error", f"Error processing appeal: {str(e)}")
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def deny(self, ctx, appeal_id: int, *, reason: str = "Appeal denied"):
        """Deny an unban appeal"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM unban_requests WHERE id = ? AND status = "pending"', (appeal_id,))
        result = cursor.fetchone()
        
        if not result:
            embed = create_error_embed("Appeal Not Found", "Appeal not found or already processed.")
            await ctx.send(embed=embed)
            conn.close()
            return
        
        user_id = result[0]
        cursor.execute('UPDATE unban_requests SET status = "denied" WHERE id = ?', (appeal_id,))
        conn.commit()
        conn.close()
        
        embed = discord.Embed(title='Appeal Denied', color=0xe74c3c)
        embed.add_field(name='Appeal ID', value=f"#{appeal_id}", inline=True)
        embed.add_field(name='User ID', value=str(user_id), inline=True)
        embed.add_field(name='Denied By', value=ctx.author.mention, inline=True)
        embed.add_field(name='Reason', value=reason, inline=False)
        await ctx.send(embed=embed)
        
        # Send DM to user
        try:
            user = await self.bot.fetch_user(user_id)
            embed_dm = discord.Embed(
                title="Appeal Denied",
                description=f"Your appeal has been denied for **{ctx.guild.name}**.",
                color=0xe74c3c
            )
            embed_dm.add_field(name="Appeal ID", value=f"#{appeal_id}", inline=True)
            embed_dm.add_field(name="Denied By", value=str(ctx.author), inline=True)
            embed_dm.add_field(name="Reason", value=reason, inline=False)
            embed_dm.add_field(name="Future Appeals", value="You may submit another appeal after reflecting on the reason for denial.", inline=False)
            embed_dm.set_footer(text="Professional Moderation System")
            await user.send(embed=embed_dm)
        except:
            pass

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def appealinfo(self, ctx, appeal_id: int):
        """Get detailed information about an appeal"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, reason, status, timestamp FROM unban_requests WHERE id = ?', (appeal_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            embed = create_error_embed("Appeal Not Found", f"No appeal found with ID #{appeal_id}")
            await ctx.send(embed=embed)
            return
        
        user_id, reason, status, timestamp = result
        
        try:
            user = await self.bot.fetch_user(user_id)
            user_info = f"{user} ({user.id})"
            account_created = user.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            user_info = f"Unknown User ({user_id})"
            account_created = "Unknown"
        
        status_emoji = {"pending": "🟡", "approved": "🟢", "denied": "🔴"}.get(status, "⚪")
        
        embed = discord.Embed(title=f'{status_emoji} Appeal #{appeal_id} Details', color=0x3498db)
        embed.add_field(name="User", value=user_info, inline=True)
        embed.add_field(name="Status", value=status.title(), inline=True)
        embed.add_field(name="Submitted", value=timestamp, inline=True)
        embed.add_field(name="Account Created", value=account_created, inline=True)
        embed.add_field(name="Appeal Content", value=reason[:1000] + "..." if len(reason) > 1000 else reason, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Appeals(bot))