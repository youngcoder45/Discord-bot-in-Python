import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import json
import re
from datetime import datetime, timezone

class EmbedEditModal(discord.ui.Modal, title='Edit Existing Embed'):
    """Interactive modal for editing existing embeds"""
    
    def __init__(self, cog, original_message, original_embed, webhook=None):
        super().__init__()
        self.cog = cog
        self.original_message = original_message
        self.original_embed = original_embed
        self.webhook = webhook
        
        # Pre-populate fields with existing embed data
        self.embed_title.default = original_embed.title or ""
        self.embed_description.default = original_embed.description or ""
        self.embed_footer.default = original_embed.footer.text if original_embed.footer else ""
        
        # Pre-populate content if message works
        self.embed_premessage.default = original_message.content or ""
        
        # Extract color as hex
        if original_embed.color:
            self.embed_color.default = f"#{original_embed.color.value:06x}"
        else:
            self.embed_color.default = "blue"
    
    # Input fields for the modal
    embed_title = discord.ui.TextInput(
        label='Embed Title',
        placeholder='Enter the title for your embed...',
        required=True,
        max_length=256
    )
    
    embed_description = discord.ui.TextInput(
        label='Description',
        placeholder='Enter the main content of your embed...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000
    )
    
    embed_color = discord.ui.TextInput(
        label='Color (optional)',
        placeholder='red, blue, green, gold, purple, orange, teal, #FF0000',
        required=False,
        max_length=50,
        default='blue'
    )
    
    embed_footer = discord.ui.TextInput(
        label='Footer Text (optional)',
        placeholder='Enter footer text...',
        required=False,
        max_length=2048
    )
    
    embed_premessage = discord.ui.TextInput(
        label='Pre-Message (optional)',
        placeholder='Write a plain message to send before the embed (you can @mention people or roles)...',
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=2000
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle the form submission and edit the embed"""
        try:
            # Create the updated embed
            embed = discord.Embed(
                title=self.embed_title.value,
                description=self.embed_description.value
            )
            
            # Set color
            color_value = self.embed_color.value.strip().lower() if self.embed_color.value else 'blue'
            if color_value.startswith('#'):
                try:
                    color_int = int(color_value[1:], 16)
                    embed.color = discord.Color(color_int)
                except ValueError:
                    embed.color = discord.Color.blue()
            else:
                embed.color = self.cog.colors.get(color_value, discord.Color.blue())
            
            # Add footer if provided
            if self.embed_footer.value:
                embed.set_footer(text=self.embed_footer.value)
            
            # Preserve original image if it exists
            if self.original_embed.image:
                embed.set_image(url=self.original_embed.image.url)

            # Preserve thumbnail if it exists
            if self.original_embed.thumbnail:
                embed.set_thumbnail(url=self.original_embed.thumbnail.url)
            
            # Edit the original message with the new embed
            new_content = self.embed_premessage.value
            
            if self.webhook:
                await self.webhook.edit_message(self.original_message.id, content=new_content, embed=embed)
            else:
                await self.original_message.edit(content=new_content, embed=embed)
            
            # Send ephemeral confirmation
            success_embed = discord.Embed(
                title="✅ Embed Updated",
                description=f"The embed has been updated!\n[Jump to message]({self.original_message.jump_url})",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to edit that message. Make sure I sent the original message.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
        except discord.NotFound:
            error_embed = discord.Embed(
                title="❌ Message Not Found",
                description="The message could not be found. It may have been deleted.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Embed Edit Failed",
                description=f"Error: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

class EmbedCreatorModal(discord.ui.Modal, title='Create Beautiful Embed'):
    """Interactive modal for creating embeds"""
    
    def __init__(self, cog):
        super().__init__()
        self.cog = cog
    
    # Input fields for the modal
    embed_title = discord.ui.TextInput(
        label='Embed Title',
        placeholder='Enter the title for your embed...',
        required=True,
        max_length=256
    )
    
    embed_description = discord.ui.TextInput(
        label='Description',
        placeholder='Enter the main content of your embed...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000
    )
    
    embed_color = discord.ui.TextInput(
        label='Color (optional)',
        placeholder='red, blue, green, gold, purple, orange, teal, #FF0000',
        required=False,
        max_length=50,
        default='blue'
    )
    
    embed_footer = discord.ui.TextInput(
        label='Footer Text (optional)',
        placeholder='Enter footer text...',
        required=False,
        max_length=2048
    )
    
    # Optional pre-message (plain text sent BEFORE the embed; useful for mentions)
    embed_premessage = discord.ui.TextInput(
        label='Pre-Message (optional)',
        placeholder='Write a plain message to send before the embed (you can @mention people or roles)...',
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=2000,
        default=''
    )
    # end of create modal fields

    async def on_submit(self, interaction: discord.Interaction):
        """Handle the form submission and create the embed"""
        try:
            # Create the embed with the provided data
            embed = discord.Embed(
                title=self.embed_title.value,
                description=self.embed_description.value
            )
            
            # Set color
            color_value = self.embed_color.value.strip().lower() if self.embed_color.value else 'blue'
            if color_value.startswith('#'):
                try:
                    color_int = int(color_value[1:], 16)
                    embed.color = discord.Color(color_int)
                except ValueError:
                    embed.color = discord.Color.blue()
            else:
                embed.color = self.cog.colors.get(color_value, discord.Color.blue())
            
            # Add footer if provided
            if self.embed_footer.value:
                embed.set_footer(text=self.embed_footer.value)
            
            # Use Webhook to send ephemeral-style user impersonated message
            target_channel = interaction.channel
            webhook_sent = False
            
            # Check if we can use webhooks (TextChannels only usually)
            if isinstance(target_channel, discord.TextChannel) and interaction.guild and target_channel.permissions_for(interaction.guild.me).manage_webhooks:
                try:
                    # Find or create webhook
                    webhooks = await target_channel.webhooks()
                    webhook = next((w for w in webhooks if w.user and w.user.id == self.cog.bot.user.id), None)
                    
                    if not webhook:
                        webhook = await target_channel.create_webhook(name="Embed Bot helper")
                    
                    # Send via webhook with 'The Codeverse Hub' identity
                    content = self.embed_premessage.value if self.embed_premessage.value else discord.utils.MISSING
                    
                    await webhook.send(
                        content=content,
                        embed=embed,
                        username="The Codeverse Hub",
                        avatar_url=self.cog.bot.user.display_avatar.url
                    )
                    webhook_sent = True
                    
                except Exception as e:
                    # Fallback to normal send if webhook fails
                    webhook_sent = False
            
            if not webhook_sent:
                # Fallback: Send plain message first if provided, then embedding as bot
                if isinstance(target_channel, (discord.TextChannel, discord.Thread)):
                    if self.embed_premessage.value:
                        try:
                            # Send content and embed in same message if possible, or separate
                            # User asked for "part of embed text message", so use content=
                            await target_channel.send(content=self.embed_premessage.value, embed=embed)
                        except Exception:
                             # Try sending separate if failed (e.g. content too long?)
                             await target_channel.send(self.embed_premessage.value)
                             await target_channel.send(embed=embed)
                    else:
                        await target_channel.send(embed=embed)
                else:
                    # Fallback for other channel types
                    await interaction.response.send_message(content=self.embed_premessage.value, embed=embed)
                    return

            # Send ephemeral confirmation to the user
            success_embed = discord.Embed(
                title="✅ Embed Sent",
                description="Your embed has been sent to this channel!",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Embed Creation Failed",
                description=f"Error: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

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
        description="Create a beautiful embed with an interactive form"
    )
    async def create_embed_interactive(self, interaction: discord.Interaction):
        """Create a beautiful embed using an interactive modal form"""
        try:
            # Show the modal form to the user
            modal = EmbedCreatorModal(self)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error Opening Embed Creator",
                description=f"Error: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(
        name="editembed",
        description="Edit an existing embed made by the bot"
    )
    @app_commands.describe(
        message_id="The ID of the message containing the embed to edit",
        message_url="Alternative: Paste the message URL instead of ID"
    )
    async def edit_embed(
        self, 
        interaction: discord.Interaction,
        message_id: Optional[str] = None,
        message_url: Optional[str] = None
    ):
        """Edit an existing embed using a pre-populated modal form"""
        try:
            # Extract message ID from URL if provided
            target_message_id = None
            target_channel_id = None
            
            if message_url:
                # Parse Discord message URL: https://discord.com/channels/guild_id/channel_id/message_id
                import re
                url_pattern = r'https://discord\.com/channels/(\d+)/(\d+)/(\d+)'
                match = re.match(url_pattern, message_url.strip())
                if match:
                    guild_id, channel_id, msg_id = match.groups()
                    target_message_id = int(msg_id)
                    target_channel_id = int(channel_id)
                else:
                    raise ValueError("Invalid message URL format")
            elif message_id:
                try:
                    target_message_id = int(message_id.strip())
                    target_channel_id = interaction.channel_id
                except ValueError:
                    raise ValueError("Invalid message ID format")
            else:
                raise ValueError("Please provide either message_id or message_url")
            
            # Get the channel and message
            if target_channel_id and target_channel_id != interaction.channel_id:
                # Message is in a different channel
                if not interaction.guild:
                    raise ValueError("This command can only be used in a server")
                target_channel = interaction.guild.get_channel(target_channel_id)
                if not target_channel:
                    raise ValueError("Channel not found or not accessible")
                if not isinstance(target_channel, (discord.TextChannel, discord.Thread)):
                    raise ValueError("Can only edit embeds in text channels or threads")
            else:
                target_channel = interaction.channel
                if not isinstance(target_channel, (discord.TextChannel, discord.Thread)):
                    raise ValueError("Can only edit embeds in text channels or threads")
            
            if not target_message_id:
                raise ValueError("Message ID is required")
            
            # Fetch the message
            try:
                target_message = await target_channel.fetch_message(target_message_id)
            except discord.NotFound:
                raise ValueError("Message not found")
            except discord.Forbidden:
                raise ValueError("No permission to access that message")
            
            # Check if the message was sent by the bot (id) or by a webhook (no user id checks for webhooks)
            # Fetch webhook if it's a webhook message
            is_webhook = bool(target_message.webhook_id)
            webhook = None
            
            if is_webhook:
                if isinstance(target_channel, discord.TextChannel) and interaction.guild and target_channel.permissions_for(interaction.guild.me).manage_webhooks:
                     webhooks = await target_channel.webhooks()
                     # Check if we own the webhook (it's one of ours)
                     webhook = next((w for w in webhooks if w.id == target_message.webhook_id and (w.user and w.user.id == interaction.client.user.id)), None) if interaction.client.user else None

            if not is_webhook and (not interaction.client.user or target_message.author.id != interaction.client.user.id):
                error_embed = discord.Embed(
                    title="❌ Cannot Edit Message",
                    description="I can only edit messages that I sent myself.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return
            
            if is_webhook and not webhook:
                 error_embed = discord.Embed(
                    title="❌ Cannot Edit Message",
                    description="This webhook message doesn't seem to belong to me or I don't have access to it.",
                    color=discord.Color.red()
                )
                 await interaction.response.send_message(embed=error_embed, ephemeral=True)
                 return

            # Check if the message has an embed
            if not target_message.embeds:
                error_embed = discord.Embed(
                    title="❌ No Embed Found",
                    description="The specified message doesn't contain any embeds to edit.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return
            
            # Get the first embed from the message
            original_embed = target_message.embeds[0]
            
            # Show the pre-populated modal form
            modal = EmbedEditModal(self, target_message, original_embed, webhook)
            await interaction.response.send_modal(modal)
            
        except ValueError as e:
            error_embed = discord.Embed(
                title="❌ Invalid Input",
                description=f"Error: {str(e)}\n\n**Usage Examples:**\n"
                           f"• `/editembed message_id:123456789`\n"
                           f"• `/editembed message_url:https://discord.com/channels/.../.../.../`\n"
                           f"• Right-click message → Copy Message Link",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error Opening Embed Editor",
                description=f"Error: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(
        name="embedquick",
        description="Create a quick embed with command parameters (legacy method)"
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
    async def create_embed_quick(
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
        """Create a beautiful customized embed message (quick method with parameters)"""
        try:
            print(f"DEBUG: /embedquick called by {interaction.user} (ID: {interaction.user.id})")
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
            
            # Send the embed to the channel (not as a reply)
            if isinstance(interaction.channel, (discord.TextChannel, discord.Thread)):
                await interaction.channel.send(embed=embed)
                
                # Send ephemeral confirmation to the user
                success_embed = discord.Embed(
                    title="✅ Embed Sent",
                    description="Your embed has been sent to this channel!",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=success_embed, ephemeral=True)
            else:
                # Fallback if not in a proper channel
                await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Embed Creation Failed",
                description=f"Error: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    # embedrules command has been removed

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
        
        help_embed.add_field(
            name="🔧 **Interactive Embed Creator**",
            value="\n**Use `/embed` for an interactive form:**\n"
                  "• Opens a popup form with input fields\n"
                  "• Fill in title, description, color, footer, and image\n"
                  "• Creates beautiful, professional embeds\n"
                  "• Easy to use - just type `/embed` and fill the form!\n",
            inline=False
        )
        
        help_embed.add_field(
            name="✏️ **Edit Existing Embeds**",
            value="\n**Use `/editembed` to modify bot embeds:**\n"
                  "• Edit any embed previously created by the bot\n"
                  "• Pre-populated form with existing content\n"
                  "• Use message ID or right-click → Copy Message Link\n"
                  "• Works across channels in the same server\n",
            inline=False
        )
        
        help_embed.add_field(
            name="⚡ **Quick Embed Creator**",
            value="\n**Use `/embedquick` for command-line style:**\n"
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
        
        # Field syntax (for embedquick)
        help_embed.add_field(
            name="📋 **Adding Fields (embedquick only)**",
            value="\n**Add fields in description using:**\n"
                  "`{field|Field Name|Field Value|true}`\n"
                  "*The last 'true/false' controls if fields are inline*\n",
            inline=False
        )
        
        # Rules embed section removed
        
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
            value="\n**Interactive embed:**\n"
                  "```/embed```\n"
                  "*Then fill out the popup form!*\n"
                  "\n**Edit existing embed:**\n"
                  "```/editembed message_id:123456789```\n"
                  "```/editembed message_url:https://discord.com/channels/.../.../.../```\n"
                  "\n**Quick embed:**\n"
                  "```/embedquick title:Welcome! description:Hello everyone!\\n\\nEnjoy your stay! color:blue```\n",
            inline=True
        )
        
        help_embed.set_footer(text="🌟 Professional embeds made easy!", icon_url="https://cdn.discordapp.com/emojis/741205308478832650.png")
        help_embed.timestamp = discord.utils.utcnow()
        
        await interaction.response.send_message(embed=help_embed, ephemeral=True)

    @commands.group(name="ls", invoke_without_command=True)
    async def ls_command(self, ctx):
        """List utilities for the server"""
        embed = discord.Embed(
            title="Server Listing Utilities",
            description="Inspect roles, channels, and permissions on this server.",
            color=0x000000
        )
        embed.add_field(name="?ls channels", value="List all channels (categories, text, voice)", inline=False)
        embed.add_field(name="?ls channels ?w <Target> <Perm>", value="Find channels where User/Role has Permission", inline=False)
        embed.add_field(name="?ls categories [?w ...]", value="List categories (optional: filter by permission)", inline=False)
        embed.add_field(name="?ls role <role>", value="View full details and permissions of a role", inline=False)
        embed.add_field(name="?ls members <role>", value="List members who have a specific role", inline=False)
        embed.add_field(name="?ls perm <permission>", value="See which roles have a specific permission", inline=False)
        embed.add_field(name="?ls bots", value="List all bots in the server", inline=False)
        embed.add_field(name="?ls boosters", value="List server boosters", inline=False)
        embed.add_field(name="?ls perms", value="List roles that have permissions", inline=False)
        embed.add_field(name="?ls noperms", value="List cosmetic roles (no permissions)", inline=False)
        
        embed.set_footer(text="Tip: Use Role ID with ?ls role <id> to avoid pinging members!")
        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @ls_command.command(name="role")
    async def ls_role(self, ctx, role: discord.Role):
        """View full details and permissions of a specific role"""
        perms = role.permissions

        # Key Permissions to highlight
        key_perms = []
        if perms.administrator: key_perms.append("Administrator")
        if perms.manage_guild: key_perms.append("Manage Server")
        if perms.manage_roles: key_perms.append("Manage Roles")
        if perms.manage_channels: key_perms.append("Manage Channels")
        if perms.ban_members: key_perms.append("Ban Members")
        if perms.kick_members: key_perms.append("Kick Members")
        if perms.manage_messages: key_perms.append("Manage Messages")
        if perms.mention_everyone: key_perms.append("Mention Everyone")
        if perms.view_audit_log: key_perms.append("View Audit Log")

        # Create list of enabled permissions
        enabled_perms = [p[0].replace('_', ' ').title() for p in perms if p[1]]
        
        embed = discord.Embed(title=f"Role: {role.name}", color=0x000000)
        embed.add_field(name="ID", value=str(role.id), inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        embed.add_field(name="Position", value=str(role.position), inline=True)
        embed.add_field(name="Integrated", value=str(role.is_integration()), inline=True)
        embed.add_field(name="Hoisted", value=str(role.hoist), inline=True)
        embed.add_field(name="Mentionable", value=str(role.mentionable), inline=True)
        
        embed.add_field(name="Members", value=f"{len(role.members)} members", inline=True)
        embed.add_field(name="Created", value=f"<t:{int(role.created_at.timestamp())}:R>", inline=True)
        
        if perms.administrator:
            embed.add_field(name="Fatal Permission", value="**ADMINISTRATOR** (Bypasses all other permissions)", inline=False)
        
        if key_perms and not perms.administrator:
            embed.add_field(name="Key Permissions", value=", ".join(key_perms), inline=False)

        # Truncate full list if too long
        perm_list_str = ", ".join(enabled_perms)
        if len(perm_list_str) > 1000:
            perm_list_str = perm_list_str[:1000] + "..."
        
        if not enabled_perms:
            perm_list_str = "None (Cosmetic Role)"

        embed.add_field(name="All Permissions", value=perm_list_str, inline=False)
        
        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @ls_command.command(name="members")
    async def ls_members(self, ctx, *, role: discord.Role):
        """Show how many people have a specific role and list them if < 20"""
        count = len(role.members)
        
        embed = discord.Embed(
            title=f"Members in Role: {role.name}",
            color=role.color
        )
        embed.add_field(name="Total Members", value=str(count), inline=False)
        embed.add_field(name="Role ID", value=str(role.id), inline=False)
        
        if count == 0:
            embed.description = "No members have this role."
        elif count < 20:
            member_mentions = [member.mention for member in role.members]
            # Join with a nice separator
            embed.description = "\n".join(member_mentions)
        else:
            embed.description = f"There are {count} members with this role. (List only shown if < 20)"
            
        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @ls_command.command(name="perm")
    async def ls_perm(self, ctx, *, perm_query: str):
        """List roles that have a specific permission"""
        # Normalize query
        query = perm_query.lower().replace(" ", "_")
        
        # Valid permissions map
        valid_perms = dir(discord.Permissions.none())
        
        # Find match
        matched_perm = None
        for p in valid_perms:
            if p.startswith("_") or callable(getattr(discord.Permissions, p, None)):
                continue
            if p == query or p.replace("_", "") == query.replace("_", ""):
                matched_perm = p
                break
        
        if not matched_perm:
            # Fuzzy-ish fallback
            matches = [p for p in valid_perms if not p.startswith("_") and query in p]
            if matches:
                 await ctx.send(f"Permission `{perm_query}` not found. Did you mean: {', '.join(matches[:5])}?")
            else:
                 await ctx.send(f"Permission `{perm_query}` not found.")
            return

        # Find roles
        roles_with_perm = []
        for role in ctx.guild.roles:
            if role.is_default(): continue
            # Administrator implies all permissions
            if role.permissions.administrator or getattr(role.permissions, matched_perm):
                roles_with_perm.append(role)
        
        roles_with_perm.sort(key=lambda r: r.position, reverse=True)
        
        embed = discord.Embed(
            title=f"Roles with '{matched_perm.replace('_', ' ').title()}'",
            description=f"Found {len(roles_with_perm)} roles.",
            color=0x000000
        )
        
        chunk = ""
        for role in roles_with_perm:
            # Mark if it's via admin or direct
            note = " (Admin)" if role.permissions.administrator and matched_perm != "administrator" else ""
            line = f"{role.mention}{note}\n"
            
            if len(chunk) + len(line) > 4000:
                embed.description = chunk
                await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                chunk = line
                embed = discord.Embed(title="Continued...", color=0x000000)
            else:
                chunk += line
                
        if chunk:
            embed.description = chunk
            await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        elif not roles_with_perm:
            await ctx.send(f"No roles found with `{matched_perm}`.")

    @ls_command.command(name="noperms")
    async def ls_noperms(self, ctx):
        """List cosmetic roles (no permissions at all)"""
        roles = []
        for role in ctx.guild.roles:
            if role.is_default(): continue # Skip @everyone
            # Check if role has NO permissions
            if role.permissions.value == 0:
                roles.append(role)
        
        # Sort by position (reverse = highest first)
        roles.sort(key=lambda r: r.position, reverse=True)
        
        if not roles:
            await ctx.send("No cosmetic-only roles found.")
            return

        # Create embed
        embed = discord.Embed(
            title="Cosmetic Roles (No Permissions)",
            description="These roles have 0 permission value.",
            color=0x000000
        )
        
        # Chunking for description limit
        chunk = ""
        count = 0
        for role in roles:
            line = f"{role.mention} (Pos: {role.position})\n"
            if len(chunk) + len(line) > 4000:
                embed.description = chunk
                await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                chunk = line
                embed = discord.Embed(title="Continued...", color=0x000000)
            else:
                chunk += line
            count += 1
            
        if chunk:
            embed.description = chunk
            embed.set_footer(text=f"Total: {count} roles")
            await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @ls_command.command(name="perms")
    async def ls_perms(self, ctx, *, role: discord.Role = None):
        """List roles that have at least one permission or permissions for a specific role"""
        
        if role:
            # List permissions for the specific role
            perms = []
            for perm, value in role.permissions:
                if value:
                    perms.append(perm.replace('_', ' ').title())
            
            if not perms:
                await ctx.send(f"{role.mention} has no active permissions.", allowed_mentions=discord.AllowedMentions.none())
                return
            
            perms.sort()
            
            perms_chunked = [perms[i:i + 20] for i in range(0, len(perms), 20)]

            for i, chunk in enumerate(perms_chunked):
                embed = discord.Embed(
                    title=f"Permissions for {role.name}" if i == 0 else f"Permissions for {role.name} (Continued)",
                    description="\n".join(f"• {p}" for p in chunk),
                    color=role.color if role.color.value != 0 else 0x000000
                )
                if i == len(perms_chunked) - 1:
                    embed.set_footer(text=f"Total: {len(perms)} permissions")
                await ctx.send(embed=embed)
            return

        # List all roles with permissions
        roles = []
        for r in ctx.guild.roles:
            if r.is_default(): continue
            if r.permissions.value != 0:
                roles.append(r)
        
        roles.sort(key=lambda r: r.position, reverse=True)
        
        if not roles:
            await ctx.send("No roles with permissions found (unlikely).")
            return

        embed = discord.Embed(
            title="Functional Roles (With Permissions)",
            description="These roles have at least one permission enabled.",
            color=0x000000
        )
        
        chunk = ""
        count = 0
        
        for r in roles:
            line = f"{r.mention} (Pos: {r.position})\n"
            if len(chunk) + len(line) > 4000:
                embed.description = chunk
                await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                chunk = line
                embed = discord.Embed(title="Continued...", color=0x000000)
            else:
                chunk += line
            count += 1
            
        if chunk:
            embed.description = chunk
            embed.set_footer(text=f"Total: {count} roles")
            await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @ls_command.command(name="channels")
    async def ls_channels(self, ctx, *args):
        """List channels. Usage: ?ls channels [?w <Role/User> <Permission>]"""
        
        # Check for ?w argument for filtering
        full_args = " ".join(args)
        if "?w" in full_args:
            # Parse usage: ?ls channels ?w <Target> <Permission>
            try:
                # Split everything after ?w
                params = full_args.split("?w", 1)[1].strip()
                if not params:
                    raise ValueError("Missing arguments after ?w")
                
                # We expect the last word to be the permission, and everything before it to be the target
                # This allows targets with spaces in names if distinct enough, though mentions/IDs are safer.
                match_parts = params.rsplit(" ", 1)
                if len(match_parts) < 2:
                    raise ValueError("Please provide a Target and a Permission (e.g., Everyone SendMessage)")
                
                target_str = match_parts[0].strip()
                perm_str = match_parts[1].strip()
                
                # Resolve Target
                target = None
                if target_str.lower() in ["everyone", "@everyone", "here", "@here"]:
                    target = ctx.guild.default_role
                else:
                    # Try converting to Role first, then Member
                    try:
                        target = await commands.RoleConverter().convert(ctx, target_str)
                    except commands.BadArgument:
                        try:
                            target = await commands.MemberConverter().convert(ctx, target_str)
                        except commands.BadArgument:
                            await ctx.send(f"❌ Could not find Role or Member named `{target_str}`.")
                            return
                
                # Resolve Permission
                # Map common aliases
                perm_map = {
                    'sendmessage': 'send_messages',
                    'sendmessages': 'send_messages',
                    'sendingmessages': 'send_messages',
                    'send': 'send_messages',
                    'view': 'view_channel',
                    'viewchannel': 'view_channel',
                    'viewchannels': 'view_channel',
                    'read': 'view_channel',
                    'readmessage': 'view_channel',
                    'readmessages': 'view_channel',
                    'connect': 'connect',
                    'speak': 'speak',
                    'manage': 'manage_channels',
                    'admin': 'administrator',
                    'embed': 'embed_links',
                    'embeds': 'embed_links',
                    'embedlink': 'embed_links',
                    'attach': 'attach_files',
                    'files': 'attach_files',
                    'file': 'attach_files',
                    'image': 'attach_files',
                    'addreaction': 'add_reactions',
                    'addreactions': 'add_reactions',
                    'reaction': 'add_reactions',
                    'history': 'read_message_history',
                    'managemessage': 'manage_messages',
                    'managemessages': 'manage_messages'
                }
                
                # Normalize input
                clean_input = perm_str.lower().replace(" ", "").replace("_", "")
                
                # Get all real permissions using standard iteration
                valid_perms = [name for name, value in discord.Permissions()]
                
                perm_attr = None
                
                # 1. Map Check (Trust the map)
                if clean_input in perm_map:
                    perm_attr = perm_map[clean_input]
                
                # 2. Direct name check (snake case normalized)
                # This covers "manage_channels" -> "manage_channels"
                if not perm_attr:
                     snake_input = perm_str.lower().replace(" ", "_")
                     if snake_input in valid_perms:
                         perm_attr = snake_input

                # 3. Stripped check (ignore underscores in real permissions)
                # This covers "managechannels" -> matches "manage_channels"
                if not perm_attr:
                    for vp in valid_perms:
                        if vp.replace("_", "") == clean_input:
                            perm_attr = vp
                            break
                            
                # 4. Fuzzy / Substring match (DANGEROUS but helpful)
                if not perm_attr:
                    # Finds "manage" -> "manage_channels" (first match)
                    # Use a priority list if multiple match?
                    matches = [p for p in valid_perms if clean_input in p.replace("_", "")]
                    if matches:
                        # Prefer shorter matches or exact start matches
                        # e.g. "ban" matches "ban_members"
                        perm_attr = matches[0] 
                    else:
                        await ctx.send(f"❌ Invalid permission `{perm_str}`.")
                        return

                # Filter Channels
                matched = []
                for channel in ctx.guild.channels:
                    # Exclude categories
                    if isinstance(channel, discord.CategoryChannel):
                        continue
                        
                    # channel.permissions_for handles overwrites, roles, admin implications
                    perms = channel.permissions_for(target)
                    if getattr(perms, perm_attr, False):
                        matched.append(channel)
                
                matched.sort(key=lambda c: c.position)
                
                if not matched:
                    await ctx.send(f"🚫 No channels found where {target.mention} has `{perm_attr}` permission.")
                    return
                
                # Build Embed
                embed = discord.Embed(
                    title=f"Channel Audit: {perm_attr}",
                    description=f"Showing channels where **{target.mention}** can `{perm_attr}`.",
                    color=0x000000
                )
                
                # Build list text
                lines = [f"{c.mention} (`{c.id}`)" for c in matched]
                full_text = "\n".join(lines)
                
                # Handle large output
                if len(full_text) > 4000:
                    chunks = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
                    embed.description = chunks[0] + "..."
                    await ctx.send(embed=embed)
                    if len(chunks) > 1:
                        await ctx.send(f"... {len(matched) - len(chunks[0].splitlines())} more channels omitted.")
                else:
                    embed.description = full_text
                    await ctx.send(embed=embed)
                    
            except Exception as e:
                await ctx.send(f"Error parsing arguments: {str(e)}\nUsage: `?ls channels ?w Everyone SendMessage`")
            return

        # Default: List all channels grouped by category
        channels = sorted(ctx.guild.channels, key=lambda c: c.position)
        
        categories = {}
        no_category = []
        
        for c in channels:
            if c.category:
                if c.category not in categories:
                    categories[c.category] = []
                categories[c.category].append(c)
            elif isinstance(c, discord.CategoryChannel):
                # We can list categories separately or as headers. 
                # Let's verify if 'categories' dict keys cover this.
                if c not in categories:
                    categories[c] = [] # Ensure category exists even if empty
            else:
                no_category.append(c)
                
        embed = discord.Embed(title=f"Channels in {ctx.guild.name}", color=0x000000)
        
        description = ""
        
        # List non-categorized first
        if no_category:
            description += "**Uncategorized**\n"
            for c in no_category:
                description += f"{c.mention}\n"
            description += "\n"
            
        # Sort categories by position
        sorted_cats = sorted(categories.keys(), key=lambda x: x.position)
        
        for cat in sorted_cats:
            chans = categories[cat]
            description += f"**{cat.name.upper()}**\n"
            for c in chans:
                description += f"  └ {c.mention}\n"
            description += "\n"
            
        if len(description) > 4000:
            description = description[:4000] + "\n...(truncated)"
            
        embed.description = description
        await ctx.send(embed=embed)

    @ls_command.command(name="categories", aliases=["category"])
    async def ls_categories(self, ctx, *args):
        """List categories. Usage: ?ls categories [?w <Role/User> <Permission>]"""
        
        # Check for ?w argument for filtering
        full_args = " ".join(args)
        if "?w" in full_args:
            # Parse usage: ?ls categories ?w <Target> <Permission>
            try:
                # Split everything after ?w
                params = full_args.split("?w", 1)[1].strip()
                if not params:
                    raise ValueError("Missing arguments after ?w")
                
                match_parts = params.rsplit(" ", 1)
                if len(match_parts) < 2:
                    raise ValueError("Please provide a Target and a Permission")
                
                target_str = match_parts[0].strip()
                perm_str = match_parts[1].strip()
                
                # Resolve Target
                target = None
                if target_str.lower() in ["everyone", "@everyone", "here", "@here"]:
                    target = ctx.guild.default_role
                else:
                    try:
                        target = await commands.RoleConverter().convert(ctx, target_str)
                    except commands.BadArgument:
                        try:
                            target = await commands.MemberConverter().convert(ctx, target_str)
                        except commands.BadArgument:
                            await ctx.send(f"❌ Could not find Role or Member named `{target_str}`.")
                            return
                
                # Resolve Permission
                perm_map = {
                    'sendmessage': 'send_messages',
                    'sendmessages': 'send_messages',
                    'sendingmessages': 'send_messages',
                    'send': 'send_messages',
                    'view': 'view_channel',
                    'viewchannel': 'view_channel',
                    'viewchannels': 'view_channel',
                    'read': 'view_channel',
                    'readmessage': 'view_channel',
                    'readmessages': 'view_channel',
                    'connect': 'connect',
                    'speak': 'speak',
                    'manage': 'manage_channels',
                    'admin': 'administrator',
                    'embed': 'embed_links',
                    'embeds': 'embed_links',
                    'embedlink': 'embed_links',
                    'attach': 'attach_files',
                    'files': 'attach_files',
                    'file': 'attach_files',
                    'image': 'attach_files',
                    'addreaction': 'add_reactions',
                    'addreactions': 'add_reactions',
                    'reaction': 'add_reactions',
                    'history': 'read_message_history',
                    'managemessage': 'manage_messages',
                    'managemessages': 'manage_messages'
                }
                
                clean_input = perm_str.lower().replace(" ", "").replace("_", "")
                valid_perms = [name for name, value in discord.Permissions()]
                
                perm_attr = None
                if clean_input in perm_map:
                    perm_attr = perm_map[clean_input]
                
                if not perm_attr:
                     snake_input = perm_str.lower().replace(" ", "_")
                     if snake_input in valid_perms:
                         perm_attr = snake_input

                if not perm_attr:
                    for vp in valid_perms:
                        if vp.replace("_", "") == clean_input:
                            perm_attr = vp
                            break
                            
                if not perm_attr:
                    matches = [p for p in valid_perms if clean_input in p.replace("_", "")]
                    if matches:
                        perm_attr = matches[0] 
                    else:
                        await ctx.send(f"❌ Invalid permission `{perm_str}`.")
                        return

                # Filter Categories
                matched = []
                for channel in ctx.guild.categories:
                    perms = channel.permissions_for(target)
                    if getattr(perms, perm_attr, False):
                        matched.append(channel)
                
                matched.sort(key=lambda c: c.position)
                
                if not matched:
                    await ctx.send(f"🚫 No categories found where {target.mention} has `{perm_attr}` permission.")
                    return
                
                embed = discord.Embed(
                    title=f"Category Audit: {perm_attr}",
                    description=f"Showing categories where **{target.mention}** can `{perm_attr}`.",
                    color=0x000000
                )
                
                lines = [f"{c.name.upper()} (`{c.id}`)" for c in matched]
                full_text = "\n".join(lines)
                
                if len(full_text) > 4000:
                    chunks = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
                    embed.description = chunks[0] + "..."
                    await ctx.send(embed=embed)
                else:
                    embed.description = full_text
                    await ctx.send(embed=embed)
                    
            except Exception as e:
                await ctx.send(f"Error parsing arguments: {str(e)}")
            return

        # Default: List all categories
        categories = sorted(ctx.guild.categories, key=lambda c: c.position)
        
        embed = discord.Embed(title=f"Categories in {ctx.guild.name}", color=0x000000)
        
        lines = [f"{c.name} (`{c.id}`)" for c in categories]
        full_text = "\n".join(lines)
        
        if len(full_text) > 4000:
             embed.description = full_text[:4000] + "\n...(truncated)"
        else:
             embed.description = full_text or "No categories found."
             
        await ctx.send(embed=embed)

    @ls_command.command(name="bots")
    async def ls_bots(self, ctx):
        """List all bots in the server"""
        bots = [m for m in ctx.guild.members if m.bot]
        
        embed = discord.Embed(
            title=f"Bots in {ctx.guild.name} ({len(bots)})",
            color=0x000000
        )
        
        description = ""
        for bot in bots:
            description += f"{bot.mention} {bot.top_role.mention if bot.top_role else ''}\n"
            
        if len(description) > 4000:
             description = description[:4000] + "..."
             
        embed.description = description
        await ctx.send(embed=embed)

    @ls_command.command(name="boosters")
    async def ls_boosters(self, ctx):
        """List current server boosters"""
        boosters = ctx.guild.premium_subscribers
        
        if not boosters:
             embed = discord.Embed(
                title=f"Server Boosters (Tier {ctx.guild.premium_tier})",
                description="This server has no boosters yet!",
                color=0x000000
             )
             await ctx.send(embed=embed)
             return

        embed = discord.Embed(
            title=f"Server Boosters ({ctx.guild.premium_subscription_count} boosts)",
            description=f"Current Level: **Tier {ctx.guild.premium_tier}**",
            color=0x000000
        )
        
        lines = []
        for member in boosters:
            # Format time since boost
            if member.premium_since:
                timestamp = f"<t:{int(member.premium_since.timestamp())}:R>"
            else:
                timestamp = "Unknown time"
            lines.append(f"• {member.mention} - {timestamp}")
            
        embed.add_field(name="Current Boosters", value="\n".join(lines) or "None", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))
