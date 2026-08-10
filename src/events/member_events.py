import discord
from discord.ext import commands

from config import (
    INTRODUCTION_CHANNEL_ID,
    WELCOME_ROLES_CHANNEL_ID,
    WELCOME_GENERAL_CHANNEL_ID,
    WELCOME_IDEAS_CHANNEL_ID,
    HELP_FORUM_ID,
    WELCOME_TICKET_CHANNEL_ID,
)

class MemberEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle member join: track user and send welcome DM."""
        # Send welcome DM
        try:
            # Create a personalized welcome message (channels configured in .env)
            welcome_text = (
                f" Welcome {member.mention} to The CodeVerse Hub! \n"
                f"We're glad to have you join our **growing** community of developers, techies, and curious minds from around the world.\n\n"
                f" **Start your journey:**\n"
                f"• <#{INTRODUCTION_CHANNEL_ID}> – Start By Introducing Yourself Here !!!\n"
                f"• <#{WELCOME_ROLES_CHANNEL_ID}> – Get all Your Roles here!\n"
                f"• <#{WELCOME_GENERAL_CHANNEL_ID}> – Say Hi to everyone!\n"
                f"• <#{WELCOME_IDEAS_CHANNEL_ID}> – Share ideas, ask questions\n"
                f"• <#{HELP_FORUM_ID}> – Feel Free to ask for help here, our team or any other expert member may help you as soon as possible\n"
                f"If u have any query feel free to create a ticket in <#{WELCOME_TICKET_CHANNEL_ID}>\n\n"
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
        
async def setup(bot):
    await bot.add_cog(MemberEvents(bot))