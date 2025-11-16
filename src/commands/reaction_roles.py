import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import json
import os
from datetime import datetime, timezone

class ReactionRoles(commands.Cog):
    """Reaction role system for automatic role assignment"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/reaction_roles.json"
        self.reaction_roles = self.load_reaction_roles()
    
    def load_reaction_roles(self):
        """Load reaction role data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading reaction roles: {e}")
            return {}
    
    def save_reaction_roles(self):
        """Save reaction role data to file"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump(self.reaction_roles, f, indent=2)
        except Exception as e:
            print(f"Error saving reaction roles: {e}")
    
    @app_commands.command(
        name="rr",
        description="Create a reaction role message with up to 10 role assignments"
    )
    @app_commands.describe(
        title="Title for the reaction role embed",
        channel="Channel to send the reaction role message to",
        description="Description for the reaction role embed",
        emoji1="First emoji", role1="First role",
        emoji2="Second emoji (optional)", role2="Second role (optional)",
        emoji3="Third emoji (optional)", role3="Third role (optional)",
        emoji4="Fourth emoji (optional)", role4="Fourth role (optional)",
        emoji5="Fifth emoji (optional)", role5="Fifth role (optional)",
        emoji6="Sixth emoji (optional)", role6="Sixth role (optional)",
        emoji7="Seventh emoji (optional)", role7="Seventh role (optional)",
        emoji8="Eighth emoji (optional)", role8="Eighth role (optional)",
        emoji9="Ninth emoji (optional)", role9="Ninth role (optional)",
        emoji10="Tenth emoji (optional)", role10="Tenth role (optional)"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def create_reaction_role(
        self,
        interaction: discord.Interaction,
        title: str,
        channel: discord.TextChannel,
        description: str,
        emoji1: str, role1: discord.Role,
        emoji2: Optional[str] = None, role2: Optional[discord.Role] = None,
        emoji3: Optional[str] = None, role3: Optional[discord.Role] = None,
        emoji4: Optional[str] = None, role4: Optional[discord.Role] = None,
        emoji5: Optional[str] = None, role5: Optional[discord.Role] = None,
        emoji6: Optional[str] = None, role6: Optional[discord.Role] = None,
        emoji7: Optional[str] = None, role7: Optional[discord.Role] = None,
        emoji8: Optional[str] = None, role8: Optional[discord.Role] = None,
        emoji9: Optional[str] = None, role9: Optional[discord.Role] = None,
        emoji10: Optional[str] = None, role10: Optional[discord.Role] = None
    ):
        """Create a reaction role message"""
        try:
            # Check if we're in a guild
            if not interaction.guild:
                await interaction.response.send_message(
                    "❌ This command can only be used in a server!", 
                    ephemeral=True
                )
                return
            
            # Check bot permissions
            bot_member = channel.guild.get_member(self.bot.user.id)
            if not bot_member:
                await interaction.response.send_message(
                    "❌ I'm not a member of this server!", 
                    ephemeral=True
                )
                return
                
            if not channel.permissions_for(bot_member).manage_roles:
                await interaction.response.send_message(
                    "❌ I need `Manage Roles` permission to create reaction roles!", 
                    ephemeral=True
                )
                return
            
            if not channel.permissions_for(bot_member).add_reactions:
                await interaction.response.send_message(
                    "❌ I need `Add Reactions` permission in that channel!", 
                    ephemeral=True
                )
                return
            
            # Collect emoji-role pairs
            role_pairs = []
            emojis = [emoji1, emoji2, emoji3, emoji4, emoji5, emoji6, emoji7, emoji8, emoji9, emoji10]
            roles = [role1, role2, role3, role4, role5, role6, role7, role8, role9, role10]
            
            for i in range(10):
                if emojis[i] and roles[i]:
                    # Check if bot can assign this role
                    if roles[i].position >= bot_member.top_role.position:
                        await interaction.response.send_message(
                            f"❌ I cannot assign the role {roles[i].mention} because it's higher than my highest role!", 
                            ephemeral=True
                        )
                        return
                    
                    role_pairs.append((emojis[i], roles[i]))
            
            if not role_pairs:
                await interaction.response.send_message(
                    "❌ You must provide at least one emoji-role pair!", 
                    ephemeral=True
                )
                return
            
            # Create the embed (compatible with /editembed)
            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Add role information to embed description
            role_list = "\n".join([f"{emoji} {role.mention}" for emoji, role in role_pairs])
            embed.description = f"{description}\n\n**React to get roles:**\n{role_list}"
            
            embed.set_footer(text="React with the emojis below to get/remove roles!")
            
            # Send the message
            message = await channel.send(embed=embed)
            
            # Add reactions
            for emoji, role in role_pairs:
                try:
                    await message.add_reaction(emoji)
                except discord.HTTPException:
                    # If emoji fails, try to continue with others
                    continue
            
            # Store reaction role data
            message_data = {
                "channel_id": channel.id,
                "guild_id": interaction.guild.id,  # Already checked above
                "roles": {}
            }
            
            for emoji, role in role_pairs:
                message_data["roles"][str(emoji)] = role.id
            
            self.reaction_roles[str(message.id)] = message_data
            self.save_reaction_roles()
            
            # Success message
            success_embed = discord.Embed(
                title="✅ Reaction Role Created",
                description=f"Reaction role message created in {channel.mention}!\n"
                           f"[Jump to message]({message.jump_url})\n\n"
                           f"**Added {len(role_pairs)} role(s):**\n" +
                           "\n".join([f"{emoji} {role.mention}" for emoji, role in role_pairs]),
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to send messages in that channel!", 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error creating reaction role: {str(e)}", 
                ephemeral=True
            )
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle reaction additions for role assignment"""
        # Ignore bot reactions
        if payload.user_id == self.bot.user.id:
            return
        
        message_id = str(payload.message_id)
        if message_id not in self.reaction_roles:
            return
        
        data = self.reaction_roles[message_id]
        emoji_str = str(payload.emoji)
        
        if emoji_str not in data["roles"]:
            return
        
        try:
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return
            
            member = guild.get_member(payload.user_id)
            if not member:
                return
            
            role_id = data["roles"][emoji_str]
            role = guild.get_role(role_id)
            if not role:
                return
            
            # Check if member already has the role
            if role not in member.roles:
                await member.add_roles(role, reason="Reaction role assignment")
                
        except discord.Forbidden:
            # Bot doesn't have permission to assign roles
            pass
        except Exception as e:
            print(f"Error adding reaction role: {e}")
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handle reaction removals for role removal"""
        # Ignore bot reactions
        if payload.user_id == self.bot.user.id:
            return
        
        message_id = str(payload.message_id)
        if message_id not in self.reaction_roles:
            return
        
        data = self.reaction_roles[message_id]
        emoji_str = str(payload.emoji)
        
        if emoji_str not in data["roles"]:
            return
        
        try:
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return
            
            member = guild.get_member(payload.user_id)
            if not member:
                return
            
            role_id = data["roles"][emoji_str]
            role = guild.get_role(role_id)
            if not role:
                return
            
            # Check if member has the role
            if role in member.roles:
                await member.remove_roles(role, reason="Reaction role removal")
                
        except discord.Forbidden:
            # Bot doesn't have permission to remove roles
            pass
        except Exception as e:
            print(f"Error removing reaction role: {e}")
    
    @app_commands.command(
        name="rrlist",
        description="List all active reaction role messages in this server"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def list_reaction_roles(self, interaction: discord.Interaction):
        """List all reaction role messages in the current server"""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server!", 
                ephemeral=True
            )
            return
            
        guild_rr = []
        
        for message_id, data in self.reaction_roles.items():
            if data["guild_id"] == interaction.guild.id:
                channel = interaction.guild.get_channel(data["channel_id"])
                if channel:
                    role_count = len(data["roles"])
                    guild_rr.append(f"• **Message ID:** `{message_id}`\n"
                                  f"  **Channel:** {channel.mention}\n"
                                  f"  **Roles:** {role_count}")
        
        if not guild_rr:
            embed = discord.Embed(
                title="📝 Reaction Roles",
                description="No reaction role messages found in this server.",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="📝 Active Reaction Roles",
                description="\n\n".join(guild_rr),
                color=discord.Color.blue()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(
        name="rrremove",
        description="Remove a reaction role message (stops tracking reactions)"
    )
    @app_commands.describe(
        message_id="The ID of the reaction role message to remove"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def remove_reaction_role(self, interaction: discord.Interaction, message_id: str):
        """Remove a reaction role message from tracking"""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server!", 
                ephemeral=True
            )
            return
            
        if message_id not in self.reaction_roles:
            await interaction.response.send_message(
                "❌ No reaction role found with that message ID!", 
                ephemeral=True
            )
            return
        
        data = self.reaction_roles[message_id]
        if data["guild_id"] != interaction.guild.id:
            await interaction.response.send_message(
                "❌ That reaction role message is not in this server!", 
                ephemeral=True
            )
            return
        
        # Remove from tracking
        del self.reaction_roles[message_id]
        self.save_reaction_roles()
        
        embed = discord.Embed(
            title="✅ Reaction Role Removed",
            description=f"Reaction role message `{message_id}` has been removed from tracking.\n"
                       f"The message itself is still in the channel but reactions won't assign roles anymore.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))