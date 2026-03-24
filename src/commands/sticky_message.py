import discord  # type: ignore[import-not-found]
from discord.ext import commands  # type: ignore[import-not-found]
from discord import app_commands  # type: ignore[import-not-found]
import sqlite3
import asyncio
from typing import Optional

DATABASE_NAME = "data/codeverse_bot.db"

def init_sticky_db():
    """Initialize the sticky messages database table"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sticky_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_content TEXT NOT NULL,
            message_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(guild_id, channel_id)
        )
    ''')
    conn.commit()
    conn.close()

class StickyMessageModal(discord.ui.Modal):
    """Modal for creating sticky messages with markdown support"""
    
    def __init__(self, cog, channel: discord.TextChannel):
        super().__init__(title="Create Sticky Message")
        self.cog = cog
        self.channel = channel
    
    content = discord.ui.TextInput(
        label="Sticky Message Content",
        placeholder="Enter your sticky message content here (supports markdown)",
        style=discord.TextStyle.long,
        max_length=2000,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission"""
        try:
            if not interaction.guild:
                await interaction.response.send_message("❌ This command can only be used in servers.", ephemeral=True)
                return
                
            text = self.content.value
            
            # Create the sticky message content
            sticky_content = f"__**Sticky Message**__\n\n{text}"
            
            # Send the sticky message
            sticky_msg = await self.channel.send(sticky_content)
            
            # Store in database
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO sticky_messages 
                (guild_id, channel_id, message_content, message_id)
                VALUES (?, ?, ?, ?)
            ''', (interaction.guild.id, self.channel.id, text, sticky_msg.id))
            conn.commit()
            conn.close()
            
            # Update cache
            self.cog._message_cache[self.channel.id] = {
                'content': text,
                'message_id': sticky_msg.id,
                'last_repost': asyncio.get_event_loop().time()
            }
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ Sticky Message Created",
                description=f"Sticky message has been set in {self.channel.mention}",
                color=0x00ff00
            )
            
            # Show preview (truncated if too long)
            preview = text[:500] + "..." if len(text) > 500 else text
            embed.add_field(name="Content Preview", value=preview, inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description=f"I don't have permission to send messages in {self.channel.mention}.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to create sticky message: {str(e)}",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class StickyMessage(commands.Cog):
    """Sticky message system that reposts messages when new messages are sent"""

    def __init__(self, bot):
        self.bot = bot
        init_sticky_db()
        self._message_cache = {}  # Cache to prevent spam
        self._cooldowns = {}  # Per-channel cooldowns
        
        # Load all sticky messages on startup
        self.bot.loop.create_task(self._load_sticky_messages())
    
    async def _load_sticky_messages(self):
        """Load all sticky messages from database into cache on bot startup"""
        await self.bot.wait_until_ready()
        
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT channel_id, message_content, message_id
                FROM sticky_messages
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            for channel_id, content, message_id in results:
                self._message_cache[channel_id] = {
                    'content': content,
                    'message_id': message_id,
                    'last_repost': 0
                }
            
            print(f"[StickyMessage] Loaded {len(results)} sticky messages into cache")
            
        except Exception as e:
            print(f"[StickyMessage] Error loading sticky messages: {e}")

    @commands.hybrid_command(name="stickymessage")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    @app_commands.describe(
        channel="The channel where the sticky message should be posted (defaults to current channel)"
    )
    async def sticky_message(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Create or update a sticky message in a channel using a modal"""

        guild = ctx.guild
        if guild is None:
            await ctx.send("❌ This command can only be used in servers.")
            return

        target_channel = channel if isinstance(channel, discord.TextChannel) else (ctx.channel if isinstance(ctx.channel, discord.TextChannel) else None)
        if target_channel is None:
            embed = discord.Embed(
                title="❌ Invalid Channel",
                description="This command can only be used in text channels.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        if not isinstance(ctx.author, discord.Member):
            await ctx.send("❌ This command can only be used by server members.")
            return
        
        # Check if user has permissions in the target channel
        if not target_channel.permissions_for(ctx.author).manage_messages:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description=f"You don't have `Manage Messages` permission in {target_channel.mention}.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        # Check if bot has permissions in the target channel
        bot_member = guild.me
        if bot_member is None or not target_channel.permissions_for(bot_member).send_messages:
            embed = discord.Embed(
                title="❌ Bot Permission Error",
                description=f"I don't have permission to send messages in {target_channel.mention}.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        # Open the modal for creating sticky message
        if ctx.interaction is None:
            await ctx.send("❌ Please use the slash version of this command to open the modal.")
            return

        modal = StickyMessageModal(self, target_channel)
        await ctx.interaction.response.send_modal(modal)

    @commands.hybrid_command(name="removesticky")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    @app_commands.describe(
        channel="The channel to remove sticky message from (defaults to current channel)"
    )
    async def remove_sticky(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Remove a sticky message from a channel"""

        guild = ctx.guild
        if guild is None:
            await ctx.send("❌ This command can only be used in servers.")
            return

        target_channel = channel if isinstance(channel, discord.TextChannel) else (ctx.channel if isinstance(ctx.channel, discord.TextChannel) else None)
        if target_channel is None:
            embed = discord.Embed(
                title="❌ Invalid Channel",
                description="This command can only be used in text channels.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        if not isinstance(ctx.author, discord.Member):
            await ctx.send("❌ This command can only be used by server members.")
            return
        
        # Check if user has permissions in the target channel
        if not target_channel.permissions_for(ctx.author).manage_messages:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description=f"You don't have `Manage Messages` permission in {target_channel.mention}.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Get sticky message from database
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('SELECT message_id FROM sticky_messages WHERE guild_id = ? AND channel_id = ?',
                         (guild.id, target_channel.id))
            result = cursor.fetchone()
            
            if not result:
                embed = discord.Embed(
                    title="❌ No Sticky Message",
                    description=f"No sticky message found in {target_channel.mention}.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                conn.close()
                return
            
            message_id = result[0]
            
            # Delete from database
            cursor.execute('DELETE FROM sticky_messages WHERE guild_id = ? AND channel_id = ?',
                         (guild.id, target_channel.id))
            conn.commit()
            conn.close()
            
            # Remove from cache
            if target_channel.id in self._message_cache:
                del self._message_cache[target_channel.id]
            
            # Try to delete the actual message
            try:
                if message_id:
                    message = await target_channel.fetch_message(message_id)
                    await message.delete()
            except (discord.NotFound, discord.Forbidden):
                pass  # Message might already be deleted or we don't have permission
            
            embed = discord.Embed(
                title="✅ Sticky Message Removed",
                description=f"Sticky message has been removed from {target_channel.mention}.",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to remove sticky message: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="liststicky")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def list_sticky(self, ctx):
        """List all sticky messages in the current server"""
        
        try:
            if ctx.guild is None:
                await ctx.send("❌ This command can only be used in servers.")
                return

            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT channel_id, message_content, created_at 
                FROM sticky_messages 
                WHERE guild_id = ? 
                ORDER BY created_at DESC
            ''', (ctx.guild.id,))
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                embed = discord.Embed(
                    title="📝 Sticky Messages",
                    description="No sticky messages found in this server.",
                    color=0x0000ff
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="📝 Sticky Messages",
                description=f"Found {len(results)} sticky message(s) in this server:",
                color=0x0000ff
            )
            
            for channel_id, content, created_at in results[:10]:  # Limit to 10 for embed limits
                channel = self.bot.get_channel(channel_id)
                channel_name = channel.mention if channel else f"<#{channel_id}> (deleted)"
                
                # Truncate content for display
                display_content = content[:100] + "..." if len(content) > 100 else content
                
                embed.add_field(
                    name=f"🔗 {channel_name}",
                    value=f"```{display_content}```",
                    inline=False
                )
            
            if len(results) > 10:
                embed.set_footer(text=f"Showing first 10 of {len(results)} sticky messages")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to list sticky messages: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle message events to repost sticky messages"""
        
        # Ignore bot messages and DMs
        if message.author.bot or not message.guild:
            return
        
        # Check if this channel has a sticky message
        channel_id = message.channel.id
        
        # Check cache first
        if channel_id not in self._message_cache:
            # Load from database
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT message_content, message_id 
                FROM sticky_messages 
                WHERE guild_id = ? AND channel_id = ?
            ''', (message.guild.id, channel_id))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return
            
            # Cache the result
            self._message_cache[channel_id] = {
                'content': result[0],
                'message_id': result[1],
                'last_repost': 0
            }
        
        sticky_data = self._message_cache[channel_id]
        
        # Don't repost if this message IS the sticky message
        if message.id == sticky_data['message_id']:
            return
        
        # Reduced cooldown - only 1 second to prevent spam but still be responsive
        current_time = asyncio.get_event_loop().time()
        if current_time - sticky_data['last_repost'] < 1:  # 1 second cooldown
            return
        
        try:
            # Small delay to let the user's message fully appear first
            await asyncio.sleep(0.5)
            
            # Delete old sticky message if it exists
            if sticky_data['message_id']:
                try:
                    old_message = await message.channel.fetch_message(sticky_data['message_id'])
                    await old_message.delete()
                except (discord.NotFound, discord.Forbidden):
                    pass  # Message already deleted or no permission
            
            # Small delay before reposting to ensure proper order
            await asyncio.sleep(0.2)
            
            # Send new sticky message
            sticky_content = f"__**Sticky Message**__\n\n{sticky_data['content']}"
            new_sticky = await message.channel.send(sticky_content)
            
            # Update message ID in database and cache
            sticky_data['message_id'] = new_sticky.id
            sticky_data['last_repost'] = current_time
            
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE sticky_messages 
                SET message_id = ? 
                WHERE guild_id = ? AND channel_id = ?
            ''', (new_sticky.id, message.guild.id, channel_id))
            conn.commit()
            conn.close()
            
        except discord.Forbidden:
            # Bot doesn't have permission to send messages
            pass
        except Exception as e:
            print(f"[StickyMessage] Error reposting sticky message: {e}")

    async def cog_unload(self):
        """Clean up when cog is unloaded"""
        self._message_cache.clear()
        self._cooldowns.clear()

async def setup(bot):
    await bot.add_cog(StickyMessage(bot))