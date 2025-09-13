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

    async def check_embed_perms(self, interaction: discord.Interaction) -> bool:
        """Check if user has permission to use embed commands"""
        if interaction.guild is None:
            return False
        
        # Get member from the interaction
        member = interaction.guild.get_member(interaction.user.id)
        if member is None:
            member = await interaction.guild.fetch_member(interaction.user.id)
        if member is None:
            return False
            
        # Always allow server owner
        if member.id == interaction.guild.owner_id:
            return True
            
        # Allow users with administrator permission
        if member.guild_permissions.administrator:
            return True
            
        # Allow users with manage messages permission
        if member.guild_permissions.manage_messages:
            return True
            
        return False

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
            # Create base embed
            embed = discord.Embed(title=title)
            
            # Handle description with optional field parsing
            # Format: {field|name|value|inline}
            field_pattern = r'\{field\|(.*?)\|(.*?)(?:\|(true|false))?\}'
            
            # Extract and remove field definitions from description
            fields = re.finditer(field_pattern, description)
            clean_description = re.sub(field_pattern, '', description).strip()
            
            if clean_description:
                embed.description = clean_description
            
            # Add any fields found in the description
            for match in fields:
                name = match.group(1)
                value = match.group(2)
                inline = match.group(3) != "false" if match.group(3) else True
                embed.add_field(name=name, value=value, inline=inline)
            
            # Set color
            if color.startswith('#'):
                # Convert hex color to int
                color_int = int(color[1:], 16)
                embed.color = discord.Color(color_int)
            else:
                # Use preset color or default to blue
                embed.color = self.colors.get(color.lower(), discord.Color.blue())
            
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
            # Create the embed
            embed = discord.Embed(title=title)
            
            # Process rules text
            rule_lines = rules.replace('\\n', '\n').split('\n')  # Handle both literal \n and actual newlines
            formatted_rules = []
            
            for line in rule_lines:
                line = line.strip()
                if line:
                    # Add emoji based on rule number
                    if re.match(r'^\d+\.', line):
                        rule_num = int(line.split('.')[0])
                        emoji = f"{rule_num}\u20e3"  # Convert number to keycap emoji
                        formatted_rules.append(f"{emoji} {line}")
                    else:
                        formatted_rules.append(f"• {line}")
            
            embed.description = "\n".join(formatted_rules)
            
            # Set color
            if color.startswith('#'):
                embed.color = discord.Color(int(color[1:], 16))
            else:
                embed.color = self.colors.get(color.lower(), discord.Color.blue())
            
            # Add footer if provided
            if footer:
                embed.set_footer(text=footer)
            else:
                embed.set_footer(text="Please read and follow all rules to maintain a positive community!")
            
            # Add timestamp
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
            title="📝 Embed Creation Guide",
            color=discord.Color.blue()
        )
        
        # Basic usage
        help_embed.add_field(
            name="Basic Usage",
            value="Use `/embed` to create a custom embed with various options:\n"
                  "• title: The embed title\n"
                  "• description: Main content\n"
                  "• color: Color name or hex (e.g., blue, #FF0000)\n"
                  "• thumbnail: Small image URL\n"
                  "• image: Large image URL\n"
                  "• footer: Footer text\n"
                  "• timestamp: Add current time (yes/no)",
            inline=False
        )
        
        # Field syntax
        help_embed.add_field(
            name="Adding Fields",
            value="Add fields in the description using this syntax:\n"
                  "`{field|Field Name|Field Value|true}`\n"
                  "The last 'true/false' controls if fields are inline.",
            inline=False
        )
        
        # Rules embed
        help_embed.add_field(
            name="Creating Rules",
            value="Use `/embedrules` for a formatted rules embed:\n"
                  "• Enter rules as numbered lines: '1. Be respectful'\n"
                  "• Use \\n for new lines\n"
                  "• Automatically adds numbering emojis",
            inline=False
        )
        
        # Colors
        help_embed.add_field(
            name="Available Colors",
            value="• Basic: red, blue, green, gold\n"
                  "• Extra: purple, orange, teal, magenta\n"
                  "• Custom: Use hex codes like #FF0000",
            inline=False
        )
        
        # Examples
        help_embed.add_field(
            name="Example Commands",
            value="Basic embed:\n"
                  "```/embed title:Welcome! description:Hello everyone! color:blue```\n"
                  "Rules embed:\n"
                  "```/embedrules rules:1. Be respectful\n2. No spam\n3. Stay on topic```\n"
                  "With custom title and color:\n"
                  "```/embedrules rules:1. Be kind\n2. Have fun title:Community Guidelines color:#FF0000```",
            inline=False
        )
        
        await interaction.response.send_message(embed=help_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))
