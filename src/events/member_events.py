import discord
from discord.ext import commands

class MemberEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle member join: track user and send welcome DM."""
        # Send welcome DM
        try:
            # Create a personalized welcome message
            welcome_text = (
                f" Welcome {member.mention} to The CodeVerse Hub! \n"
                f"We're glad to have you join our **growing** community of developers, techies, and curious minds from around the world.\n\n"
                f" **Start your journey:**\n"
                f"• <#1263070188589547541> – Start By Introducing Yourself Here !!!\n"
                f"• <#1263070845098655744> – Get all Your Roles here!\n"
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
        
async def setup(bot):
    await bot.add_cog(MemberEvents(bot))