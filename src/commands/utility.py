import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import json
import re

class EmbedBuilder(commands.Cog):
    """Advanced embed creation and management commands"""
    
    def __init__(self, bot):
        self.bot = bot
        # Store some preset colors for easy access
        self.colors = {
            "red": discord.Color.red(),
            "blue": discord.Color.blue(),
            "green": discord.Color.green(),
            "gold": discord.Color.gold(),
            "purple": discord.Color.purple(),
            "orange": discord.Color.orange(),
            "teal": discord.Color.teal(),
            "magenta": discord.Color.magenta(),
        }

    @app_commands.command(
        name="embed",
        description="Create a beautiful embed message with customization options"
    )
    @app_commands.describe(
        title="The title of the embed",
        description="The main description/content of the embed",
        color="Color of the embed (e.g., red, blue, green, #FF0000)",
        thumbnail="URL for the thumbnail image (optional)",
        image="URL for the main image (optional)",
        footer="Footer text (optional)",
        timestamp="Add current timestamp? (yes/no)",
    )
    async def create_embed(
        self, 
        interaction: discord.Interaction,
        title: str,
        description: str,
        color: str = "blue",
        thumbnail: Optional[str] = None,
        image: Optional[str] = None,
        footer: Optional[str] = None,
        timestamp: Optional[str] = "no"
    ):
        """Create a beautiful customized embed message"""
        try:
            print(f"DEBUG: /embed called by {interaction.user} (ID: {interaction.user.id})")
            print(f"DEBUG: Guild: {interaction.guild.name if interaction.guild else 'DM'}")
            
            # Create base embed with proper spacing
            embed = discord.Embed(title=title, color=discord.Color.blue())
            
            # Handle description with proper formatting and spacing
            # Format: {field|name|value|inline}
            field_pattern = r'\{field\|(.*?)\|(.*?)(?:\|(true|false))?\}'
            
            # Extract and remove field definitions from description
            fields = list(re.finditer(field_pattern, description))
            clean_description = re.sub(field_pattern, '', description).strip()
            
            # Add proper spacing to description
            if clean_description:
                # Replace \n with actual newlines and add extra spacing
                formatted_description = clean_description.replace('\\n', '\n').replace('\n', '\n\n')
                embed.description = f"\n{formatted_description}\n"
            
            # Set color first (before fields)
            if color.startswith('#'):
                try:
                    color_int = int(color[1:], 16)
                    embed.color = discord.Color(color_int)
                except ValueError:
                    embed.color = discord.Color.blue()
            else:
                embed.color = self.colors.get(color.lower(), discord.Color.blue())
            
            # Add any fields found in the description with proper spacing
            for i, match in enumerate(fields):
                name = match.group(1).strip()
                value = match.group(2).strip()
                inline = match.group(3) != "false" if match.group(3) else True
                
                # Add spacing to field values
                formatted_value = f"\n{value}\n" if not inline else value
                embed.add_field(name=f"**{name}**", value=formatted_value, inline=inline)
                
                # Add spacing between fields (invisible field)
                if not inline and i < len(fields) - 1:
                    embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            # Add thumbnail if provided
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
            
            # Add image if provided
            if image:
                embed.set_image(url=image)
            
            # Add footer if provided
            if footer:
                embed.set_footer(text=footer)
            
            # Add timestamp if requested
            if timestamp and timestamp.lower() in ['yes', 'true', 'y']:
                embed.timestamp = discord.utils.utcnow()
            
            # Send the embed
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Embed Creation Failed",
                description=f"Error: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(
        name="embedrules",
        description="Create a pre-formatted rules embed"
    )
    @app_commands.describe(
        rules="The rules text, one rule per line starting with a number and dot (e.g., 1. Be respectful)",
        title="Custom title for the rules embed",
        color="Color of the embed (e.g., red, blue, green, #FF0000)",
        footer="Optional footer text",
    )
    async def create_rules_embed(
        self,
        interaction: discord.Interaction,
        rules: str,
        title: str = "📜 Server Rules",
        color: str = "blue",
        footer: Optional[str] = None
    ):
        """Create a beautifully formatted rules embed"""
        try:
            # Create the embed with proper spacing
            embed = discord.Embed(title=title)
            
            # Process rules text with beautiful formatting
            rule_lines = rules.replace('\\n', '\n').split('\n')
            formatted_rules = []
            
            for i, line in enumerate(rule_lines):
                line = line.strip()
                if line:
                    # Add emoji based on rule number with proper spacing
                    if re.match(r'^\d+\.', line):
                        rule_num = int(line.split('.')[0])
                        # Use different emojis for better visual appeal
                        if rule_num <= 10:
                            emoji = f"{rule_num}\u20e3"  # Number emoji
                        else:
                            emoji = "📋"  # Generic rule emoji
                        formatted_rules.append(f"\n{emoji} **{line}**\n")
                    else:
                        formatted_rules.append(f"\n🔸 **{line}**\n")
            
            # Join rules with extra spacing
            embed.description = "\n".join(formatted_rules)
            
            # Set color
            if color.startswith('#'):
                try:
                    embed.color = discord.Color(int(color[1:], 16))
                except ValueError:
                    embed.color = discord.Color.blue()
            else:
                embed.color = self.colors.get(color.lower(), discord.Color.blue())
            
            # Add a nice separator field for visual appeal
            embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", inline=False)
            
            # Add footer with proper styling
            if footer:
                embed.set_footer(text=f"📜 {footer}", icon_url="https://cdn.discordapp.com/emojis/741205308478832650.png")
            else:
                embed.set_footer(text="📜 Please read and follow all rules to maintain a positive community!", 
                               icon_url="https://cdn.discordapp.com/emojis/741205308478832650.png")
            
            # Add timestamp for professionalism
            embed.timestamp = discord.utils.utcnow()
            
            # Send the embed
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Rules Embed Creation Failed",
                description=f"Error: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(
        name="embedhelp",
        description="Get help with creating embeds"
    )
    async def embed_help(self, interaction: discord.Interaction):
        """Show help information for creating embeds"""
        help_embed = discord.Embed(
            title="🎨 **Dyno-Style Embed Creator**",
            description="\n*Create beautiful, professional embeds with proper spacing and formatting*\n",
            color=discord.Color.gold()
        )
        
        # Basic usage with better formatting
        help_embed.add_field(
            name="🔧 **Basic Usage**",
            value="\n**Use `/embed` to create custom embeds:**\n"
                  "• `title` - The embed title\n"
                  "• `description` - Main content (supports \\n for new lines)\n"
                  "• `color` - Color name or hex (blue, red, #FF0000)\n"
                  "• `thumbnail` - Small image URL\n"
                  "• `image` - Large image URL\n"
                  "• `footer` - Footer text\n"
                  "• `timestamp` - Add current time (yes/no)\n",
            inline=False
        )
        
        # Separator
        help_embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", inline=False)
        
        # Field syntax
        help_embed.add_field(
            name="📋 **Adding Fields**",
            value="\n**Add fields in description using:**\n"
                  "`{field|Field Name|Field Value|true}`\n"
                  "*The last 'true/false' controls if fields are inline*\n",
            inline=False
        )
        
        # Rules embed
        help_embed.add_field(
            name="📜 **Creating Rules**",
            value="\n**Use `/embedrules` for formatted rules:**\n"
                  "• Enter rules as numbered lines\n"
                  "• Example: `1. Be respectful\\n2. No spam`\n"
                  "• Automatically adds numbering emojis\n"
                  "• Beautiful spacing and formatting\n",
            inline=False
        )
        
        # Separator
        help_embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", inline=False)
        
        # Colors
        help_embed.add_field(
            name="🎨 **Available Colors**",
            value="\n**Basic:** red, blue, green, gold, purple\n"
                  "**Extra:** orange, teal, magenta\n"
                  "**Custom:** Use hex codes like #FF0000\n",
            inline=True
        )
        
        # Examples
        help_embed.add_field(
            name="💡 **Example Commands**",
            value="\n**Basic embed:**\n"
                  "```/embed title:Welcome! description:Hello everyone!\\n\\nEnjoy your stay! color:blue```\n"
                  "\n**Rules embed:**\n"
                  "```/embedrules rules:1. Be respectful\\n2. No spam\\n3. Stay on topic```\n",
            inline=True
        )
        
        help_embed.set_footer(text="🌟 Professional embeds made easy!", icon_url="https://cdn.discordapp.com/emojis/741205308478832650.png")
        help_embed.timestamp = discord.utils.utcnow()
        
        await interaction.response.send_message(embed=help_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))
