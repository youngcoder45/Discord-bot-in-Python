import discord
from discord.ext import commands
from utils.json_store import add_or_update_user

class MemberEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle member join: track user and send welcome DM."""
        await add_or_update_user(member.id, str(member))
        
        # Send welcome DM
        try:
            # Create a personalized welcome message
            welcome_text = (
                f"👋 Welcome {member.mention} to The CodeVerse Hub! 🎉\n"
                f"We're glad to have you join our **growing** community of developers, techies, and curious minds from around the world.\n\n"
                f"🚀 **Start your journey:**\n"
                f"• <#1263070188589547541> – Start By Introducing Yourself Here !!!\n"
                f"• <#1263070845098655744> – Learn what we're all about\n"
                f"• <#1263067254803796030> – Say Hi to everyone!\n"
                f"• <#1347581046753067050> – Share ideas, ask questions\n"
                f"• <#1388169643234955354> – Feel Free to ask for help here, our team or any other expert member may help you as soon as possible\n"
                f"If u have any query feel free to create a ticket in <#1410169473180241971>\n\n"
                f"You are our member number **{member.guild.member_count}**\n"
                f"Let’s build, learn, and grow together!!! Happy To See You OnBoard!"
            )
            
            # Send as an embed for better presentation
            embed = discord.Embed(
                description=welcome_text,
                color=discord.Color.from_rgb(0, 122, 255)  # A nice CodeVerse blue
            )
            
            if member.guild.icon:
                embed.set_thumbnail(url=member.guild.icon.url)
                
            await member.send(embed=embed)
            
        except discord.Forbidden:
            # User has DMs disabled
            pass
        except Exception as e:
            print(f"Error sending welcome DM: {e}")
        
        # Logging now handled by centralized logging system

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Handle member leaving the guild (logging only)."""
        # Logging now handled by centralized logging system
        pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Handle member updates (role changes, nickname changes, etc.)"""
        # Nothing to do here - role changes now handled by the centralized logging system
        # This method is kept for future compatibility
        pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Handle member ban events"""
        # Logging now handled by centralized logging system
        pass

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Handle member unban events"""
        # Logging now handled by centralized logging system
        pass

async def setup(bot):
    await bot.add_cog(MemberEvents(bot))