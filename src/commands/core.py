import discord
import os
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

class Core(commands.Cog):
    """Core hybrid commands: ping, info, help menu."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = getattr(bot, 'start_time', datetime.now(timezone.utc))

    @commands.hybrid_command(name="ping", help="Check if the bot is responsive")
    async def ping(self, ctx: commands.Context):
        """Latency check."""
        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="Connection Status", 
            description=f"WebSocket Latency: {latency_ms}ms",
            color=0x2ECC71
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="info", help="Get bot information")
    async def info(self, ctx: commands.Context):
        uptime = datetime.now(timezone.utc) - self.start_time
        embed = discord.Embed(
            title="CodeVerse Bot Information", 
            description="A professional Discord bot for programming communities",
            color=0x3498DB,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Uptime", value=str(uptime).split('.')[0], inline=True)
        embed.add_field(name="Command Prefix", value=str(self.bot.command_prefix), inline=True)
        instance_id = os.getenv('INSTANCE_ID', 'production')
        embed.add_field(name="Instance ID", value=instance_id, inline=True)
        embed.set_footer(text=f"Instance: {instance_id}")
        await ctx.reply(embed=embed, mention_author=False)



    @commands.hybrid_command(name="help", aliases=["helpmenu"], help="Open the interactive dropdown help center")
    @app_commands.describe(command="Optional command name to get detailed help about")
    async def helpmenu(self, ctx: commands.Context, command: str | None = None):
        """Interactive categorized help with dropdown menu."""
        
        # If a specific command is requested, show detailed info inline
        if command:
            cmd = self.bot.get_command(command.lower())
            if not cmd or cmd.hidden:
                await ctx.reply(f"❌ Command `{command}` not found.", mention_author=False)
                return
            embed = discord.Embed(
                title=f"Help: {cmd.qualified_name}",
                color=discord.Color.blurple()
            )
            # Basic description
            desc = cmd.help or "No description provided."
            if cmd.brief:
                desc = f"{cmd.brief}\n\n{desc}" if cmd.brief not in desc else desc
            embed.description = desc

            # Usage (build from signature if available)
            signature = getattr(cmd, 'signature', '')
            if signature:
                embed.add_field(name="Usage", value=f"`?{cmd.qualified_name} {signature}`", inline=False)
            else:
                embed.add_field(name="Usage", value=f"`?{cmd.qualified_name}`", inline=False)

            # Cog / category
            if cmd.cog_name:
                embed.add_field(name="Category", value=cmd.cog_name, inline=True)

            # Slash compatibility
            embed.add_field(name="Slash", value=f"`/{cmd.qualified_name}`", inline=True)

            # Aliases
            if getattr(cmd, 'aliases', None):
                embed.add_field(name="Aliases", value=", ".join(f"`{a}`" for a in cmd.aliases), inline=False)
        
            embed.set_footer(text="Use ?help for the full interactive help menu")
            await ctx.reply(embed=embed, mention_author=False)
            return
            
        # No specific command: show interactive help menu
        view = HelpView(self.bot)
        embed = await view.get_main_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @commands.hybrid_command(name="bothelp", help="Show all bot commands organized by category (legacy)")
    async def help_cmd_legacy(self, ctx: commands.Context):
        """Dynamic help system that auto-discovers cogs/commands.

        Behaviour:
        - Builds a categorized list of all visible commands grouped by their Cog name.
        - If the combined content is short enough it sends a single embed.
        - If too long, sends a summary embed with interactive buttons to browse categories.
        - Falls back gracefully if components cannot be sent.
        """
        from collections import defaultdict

        # Aggregate commands by cog
        categories: dict[str, list[commands.Command]] = defaultdict(list)
        for cmd in sorted(self.bot.commands, key=lambda c: c.name):
            if cmd.hidden:
                continue
            categories[cmd.cog_name or "Misc"].append(cmd)

        # Friendly / emoji name mapping (extend as needed)
        emoji_map = {
            "Core": "🏠",
            "AFK": "😴",
            "Afk": "😴",
            "Community": "🎪",
            "Fun": "🎮",
            "Utility": "💻",
            "Programming": "💻",
            "Moderation": "🛡️",
            "ModerationExtended": "🛡️",
            "Roles": "🎭",
            "Tags": "🏷️",
            "Highlights": "🔔",
            "Staff": "⭐",
            "Diagnostics": "🔧",
            "Database": "🗄️",
            "Misc": "📦"
        }

        # Helper to format command line
        def format_cmd(c: commands.Command) -> str:
            summary = (c.brief or c.help or "").strip().replace('\n', ' ')
            if len(summary) > 80:
                summary = summary[:77] + '…'
            return f"**`{c.name}`** - {summary if summary else 'No description'}"

        # Build the big description preview & measure size
        total_chars = 0
        preview_fields = []
        for cat_name, cmd_list in categories.items():
            lines = [format_cmd(c) for c in cmd_list]
            field_value = "\n".join(lines) if lines else "No commands"
            total_chars += len(field_value)
            preview_fields.append((cat_name, field_value))

        interactive_needed = total_chars > 3800 or len(preview_fields) > 10

        if not interactive_needed:
            # Single embed variant
            embed = discord.Embed(
                title="CodeVerse Bot - Command Reference",
                description="All commands support both prefix `?` and slash `/`.",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )
            for cat_name, value in preview_fields:
                emoji = emoji_map.get(cat_name, "📁")
                embed.add_field(name=f"{emoji} {cat_name}", value=value[:1024] or "No commands", inline=False)
            embed.set_footer(text=f"Total: {sum(len(v) for v in categories.values())} commands • Use ?help <command> for details")
            embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user and self.bot.user.avatar else None)
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Interactive view
        view = BotHelpView(self.bot, categories, emoji_map)
        summary_embed = discord.Embed(
            title="CodeVerse Bot - Command Directory",
            description=(
                "The command list is large, so use the buttons below to browse by category.\n"
                "All commands work with both prefix `?` and slash `/`.\n"
                "Use `?help <command>` for detailed usage."
            ),
            color=0x3498DB,
            timestamp=datetime.now(timezone.utc)
        )
        summary_embed.add_field(
            name="Categories",
            value=" • ".join(f"{emoji_map.get(n,'📁')} {n}" for n in categories.keys()),
            inline=False
        )
        summary_embed.set_footer(text=f"{sum(len(v) for v in categories.values())} commands across {len(categories)} categories")
        summary_embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user and self.bot.user.avatar else None)

        try:
            await ctx.reply(embed=summary_embed, view=view, mention_author=False)
        except Exception:
            # Fallback compact text
            compact = []
            for name, cmds_in_cat in categories.items():
                compact.append(f"**{name}**: " + ", ".join(f"`{c.name}`" for c in cmds_in_cat))
            chunks = []
            current = ""
            for line in compact:
                if len(current) + len(line) + 1 > 1900:
                    chunks.append(current)
                    current = line + "\n"
                else:
                    current += line + "\n"
            if current:
                chunks.append(current)
            for i, chunk in enumerate(chunks):
                await ctx.reply(chunk, mention_author=False, ephemeral=False if i == 0 else True)

class BotHelpView(discord.ui.View):
    """Interactive button view for dynamic bothelp categories."""
    def __init__(self, bot: commands.Bot, categories: dict[str, list[commands.Command]], emoji_map: dict[str, str]):
        super().__init__(timeout=180)
        self.bot = bot
        self.categories = categories
        self.emoji_map = emoji_map
        # Create a button per category (Discord max 25 components total; assume safe)
        for cat_name in list(categories.keys())[:25]:
            emoji = self.emoji_map.get(cat_name, '📁')
            self.add_item(CategoryButton(cat_name, emoji, categories))

class CategoryButton(discord.ui.Button):
    def __init__(self, category: str, emoji: str, categories: dict[str, list[commands.Command]]):
        super().__init__(label=category, style=discord.ButtonStyle.primary, emoji=emoji, custom_id=f"bothelp:{category}")
        self.category = category
        self.categories = categories

    async def callback(self, interaction: discord.Interaction):  # type: ignore
        # Build embed for this category
        embed = discord.Embed(
            title=f"{self.emoji} {self.category} Commands" if self.emoji else f"{self.category} Commands",
            color=0x3498DB,
            timestamp=datetime.now(timezone.utc)
        )
        cmds = self.categories.get(self.category, [])
        if not cmds:
            embed.description = "No commands in this category."
        else:
            lines = []
            for c in cmds:
                summary = (c.brief or c.help or "No description").split('\n')[0][:90]
                lines.append(f"`{c.name}` - {summary}")
            # Split if exceeds field limits
            chunk = []
            acc = 0
            for line in lines:
                if acc + len(line) + 1 > 1000:
                    embed.add_field(name="Commands", value="\n".join(chunk), inline=False)
                    chunk = [line]
                    acc = len(line)
                else:
                    chunk.append(line)
                    acc += len(line) + 1
            if chunk:
                embed.add_field(name="Commands", value="\n".join(chunk), inline=False)
        embed.set_footer(text="Use ?help <command> for detailed usage • Buttons timeout in 3 minutes")
        try:
            await interaction.response.edit_message(embed=embed, view=self.view)
        except discord.NotFound:
            pass


class HelpView(discord.ui.View):
    """Interactive help system with dropdown menus"""
    
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=180)
        self.bot = bot
        
        # Add dropdown for category selection
        self.add_item(HelpDropdown(self.bot))
    
    async def get_main_embed(self):
        """Get the main help embed"""
        embed = discord.Embed(
            title="📚 CodeVerse Bot - Help Center",
            description=(
                "**Welcome to CodeVerse Bot!**\n\n"
                "🔹 **Prefix Commands:** Use `?` before command names (e.g., `?ping`)\n"
                "🔹 **Slash Commands:** Use `/` before command names (e.g., `/ping`)\n"
                "🔹 **Both work:** Every command supports both methods!\n\n"
                "**Use the dropdown below to explore command categories**"
            ),
            color=0x5865F2
        )
        
        # Quick stats
        total_commands = len([cmd for cmd in self.bot.commands if not cmd.hidden])
        embed.add_field(
            name="📊 Quick Stats",
            value=(
                f"**Total Commands:** {total_commands}\n"
                f"**Categories:** 6\n"
                f"**Server Exclusive:** Professional moderation\n"
                f"**Uptime:** {self.get_uptime()}"
            ),
            inline=True
        )
        
        # Most popular commands
        embed.add_field(
            name="⭐ Most Popular",
            value=(
                "• `/help` - This help menu\n"
                "• `/ping` - Check bot status\n"
                "• `/afk` - Set away message\n"
                "• `/serverinfo` - Server details\n"
                "• `/warnings` - Warning system"
            ),
            inline=True
        )
        
        # Quick links
        embed.add_field(
            name="🔗 Quick Links",
            value=(
                "• [Bot Features](https://github.com/youngcoder45/Discord-bot-in-Python)\n"
                "• [Support Server](https://discord.gg/codeverse)\n"
                "• [Documentation](https://github.com/youngcoder45/Discord-bot-in-Python/blob/master/README.md)"
            ),
            inline=False
        )
        
        embed.set_footer(text="Select a category from the dropdown below to see detailed commands")
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user and self.bot.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        return embed
    
    def get_uptime(self):
        """Get formatted uptime"""
        try:
            start_time = getattr(self.bot, 'start_time', datetime.now(timezone.utc))
            uptime = datetime.now(timezone.utc) - start_time
            return str(uptime).split('.')[0]
        except:
            return "Unknown"


class HelpDropdown(discord.ui.Select):
    """Dropdown menu for help categories"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        options = [
            discord.SelectOption(
                label="🏠 Core Commands",
                description="Essential bot commands (ping, info, help)",
                value="core",
                emoji="🏠"
            ),
            discord.SelectOption(
                label="😴 AFK System",
                description="Away from keyboard status management",
                value="afk",
                emoji="😴"
            ),
            discord.SelectOption(
                label="🛡️ ModCog",
                description="Merged moderation system with warnings",
                value="moderation",
                emoji="🛡️"
            ),
            discord.SelectOption(
                label="🔒 Advanced Moderation",
                description="Extended moderation and protection tools",
                value="advanced_moderation",
                emoji="🔒"
            ),
            discord.SelectOption(
                label="⭐ Staff Systems",
                description="Points, shifts, and staff management",
                value="staff",
                emoji="⭐"
            ),
            discord.SelectOption(
                label="🎨 Embed Tools",
                description="Create and edit server announcements",
                value="embeds",
                emoji="🎨"
            ),
            discord.SelectOption(
                label="📊 Data Management",
                description="Backup, restore, and data operations",
                value="data",
                emoji="📊"
            ),
            discord.SelectOption(
                label="🔧 Diagnostics",
                description="Bot health, testing, and troubleshooting",
                value="diagnostics",
                emoji="🔧"
            )
        ]
        
        super().__init__(
            placeholder="📂 Choose a command category to explore...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Handle dropdown selection"""
        category = self.values[0]
        embed = await self.get_category_embed(category)
        await interaction.response.edit_message(embed=embed, view=self.view)
    
    async def get_category_embed(self, category: str):
        """Get embed for specific category"""
        embeds = {
            "core": self.get_core_embed(),
            "afk": self.get_afk_embed(),
            "moderation": self.get_moderation_embed(),
            "advanced_moderation": self.get_advanced_moderation_embed(),
            "staff": self.get_staff_embed(),
            "embeds": self.get_embeds_embed(),
            "data": self.get_data_embed(),
            "diagnostics": self.get_diagnostics_embed()
        }
        return embeds.get(category, self.get_core_embed())
    
    def get_core_embed(self):
        """Core commands embed"""
        embed = discord.Embed(
            title="🏠 Core Commands",
            description="Essential bot functionality and information",
            color=0x2ECC71
        )
        
        commands = [
            ("**`/ping`**", "Check bot latency and responsiveness"),
            ("**`/info`**", "View bot information, uptime, and instance details"),
            ("**`/help`**", "Show this interactive help menu"),
            ("**`/diag`**", "Get comprehensive bot diagnostics")
        ]
        
        for cmd, desc in commands:
            embed.add_field(name=cmd, value=desc, inline=False)
            
        embed.set_footer(text="These commands work with both ? and / prefixes")
        return embed
    
    def get_afk_embed(self):
        """AFK system commands embed"""
        embed = discord.Embed(
            title="😴 AFK System",
            description="Away from keyboard status management with automatic responses",
            color=0xF39C12
        )
        
        embed.add_field(
            name="**`/afk [reason]`**",
            value="Set yourself as AFK with an optional reason. Others will see this when they mention you.",
            inline=False
        )
        
        embed.add_field(
            name="**`/unafk`** | **`/back`** | **`/return`**",
            value="Manually remove your AFK status. You'll also auto-return when you send any message.",
            inline=False
        )
        
        embed.add_field(
            name="**`/afklist`** | **`/afkstatus`** | **`/whoafk`**",
            value="List all currently AFK users in the server with their reasons and durations.",
            inline=False
        )
        
        embed.add_field(
            name="🔧 How it works",
            value=(
                "• Set AFK with custom reason\n"
                "• Bot responds to mentions automatically\n"
                "• Tracks mention count and duration\n"
                "• Auto-return when you send a message\n"
                "• Per-server AFK status"
            ),
            inline=False
        )
        
        embed.set_footer(text="AFK status persists across bot restarts")
        return embed
    
    def get_moderation_embed(self):
        """Moderation commands embed"""
        embed = discord.Embed(
            title="🛡️ ModCog - Combined Moderation System",
            description="Unified moderation system with integrated warnings",
            color=0xE74C3C
        )
        
        embed.add_field(
            name="🔨 Basic Moderation",
            value=(
                "**`/purge <amount>`** - Delete messages *(Manage Messages)*\n"
                "**`/kick <member> [reason]`** - Kick member *(Kick Members)*\n"
                "**`/ban <member> [reason]`** - Ban member *(Ban Members)*\n"
                "**`/unban <user_id>`** - Unban user *(Ban Members)*\n"
                "**`/softban <user> [reason]`** - Kick and delete messages *(Ban Members)*\n"
                "**`/clean [count]`** - Delete bot messages *(Manage Messages)*\n"
                "**`/role <user> <role_name>`** - Toggle role for user *(Manage Roles)*"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 Server Information",
            value=(
                "**`/serverinfo`** - Detailed server information\n"
                "**`/userinfo [@user]`** - Detailed user information"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Warning System",
            value=(
                "**`/warnings add <@user> [reason]`** - Issue warning to user\n"
                "**`/warnings remove <@user> <case_id> [reason]`** - Revoke specific warning\n"
                "**`/warnings list <@user>`** - List all warnings for user\n"
                "**`/warnings clear <@user> [reason]`** - Clear all warnings for user\n"
                "**`/warnings view <case_id>`** - View details about specific warning"
            ),
            inline=False
        )
        
        embed.add_field(
            name="� Appeal System",
            value=(
                "**`/appeals [status]`** - View appeal requests *(Admin)*\n"
                "**`/approve <id> [reason]`** - Approve unban appeal *(Admin)*\n"
                "**`/deny <id> <reason>`** - Deny unban appeal *(Admin)*\n"
                "**`/appealinfo <id>`** - Get detailed appeal info *(Admin)*\n"
                "**Auto-DM:** Appeals sent automatically on kick/ban/timeout"
            ),
            inline=False
        )
        
        embed.set_footer(text="All moderation actions are logged automatically")
        return embed
    
    def get_staff_embed(self):
        """Staff systems embed"""
        embed = discord.Embed(
            title="⭐ Staff Management Systems",
            description="Comprehensive staff tools and recognition systems",
            color=0xF1C40F
        )
        
        embed.add_field(
            name="🏆 Aura (Points) System",
            value=(
                "**`/aura check [@user]`** - Check aura balance\n"
                "**`/aura leaderboard`** - View staff rankings\n"
                "**`/aura top`** - Quick top 3 view\n"
                "**`/aura add <@user> <amount> [reason]`** - Award aura *(Admin)*\n"
                "**`/aura stats [@user]`** - Detailed statistics"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⏰ Shift Tracking",
            value=(
                "**`/shift start [note]`** - Start staff shift *(Staff)*\n"
                "**`/shift end [note]`** - End staff shift *(Staff)*\n"
                "**`/shift admin active`** - View active shifts *(Admin)*\n"
                "**`/shift admin stats [user]`** - View statistics *(Admin)*"
            ),
            inline=False
        )
        
        embed.set_footer(text="Staff systems include automatic recognition and logging")
        return embed
    
    def get_embeds_embed(self):
        """Embed tools embed"""
        embed = discord.Embed(
            title="🎨 Embed Creation Tools",
            description="Professional embed creation for server announcements",
            color=0x17A2B8
        )
        
        commands = [
            ("**`/embed`**", "Interactive embed creator with popup form"),
            ("**`/editembed <message_id>`**", "Edit existing embeds made by the bot"),
            ("**`/embedquick <title> <description> [color]`**", "Quick embed creation"),
            ("**`/embedhelp`**", "Get help with embed creation")
        ]
        
        for cmd, desc in commands:
            embed.add_field(name=cmd, value=desc, inline=False)
            
        embed.add_field(
            name="✨ Features",
            value=(
                "• Interactive popup forms\n"
                "• Color customization\n"
                "• Professional formatting\n"
                "• Server announcements\n"
                "• Staff communication"
            ),
            inline=False
        )
        
        embed.set_footer(text="Create professional embeds for server announcements")
        return embed
    
    def get_data_embed(self):
        """Data management embed"""
        embed = discord.Embed(
            title="📊 Data Management",
            description="Backup, restore, and data operation commands",
            color=0x6C757D
        )
        
        commands = [
            ("**`/data backup`**", "Create immediate backup of all bot data *(Admin)*"),
            ("**`/data restore`**", "Restore data from backup (DANGEROUS) *(Admin)*"),
            ("**`/data status`**", "Show backup and persistence status"),
            ("**`/data export`**", "Export data as downloadable file *(Admin)*")
        ]
        
        for cmd, desc in commands:
            embed.add_field(name=cmd, value=desc, inline=False)
            
        embed.add_field(
            name="🔄 Automatic Backups",
            value=(
                "• Every 6 hours automatically\n"
                "• On bot startup\n"
                "• GitHub integration\n"
                "• Local file storage\n"
                "• Database persistence"
            ),
            inline=False
        )
        
        embed.set_footer(text="Data safety is our top priority")
        return embed
    
    def get_advanced_moderation_embed(self):
        """Advanced moderation commands embed"""
        embed = discord.Embed(
            title="🔒 Advanced Moderation",
            description="Extended moderation and protection tools",
            color=0x9B59B6
        )
        
        embed.add_field(
            name="🚨 Protection Systems",
            value=(
                "**`/automod`** - Configure automatic moderation settings\n"
                "**`/automodstatus`** - View current automod configuration\n"
                "**`/antispam`** - Anti-spam protection settings\n"
                "**`/antiraid`** - Configure anti-raid protection\n"
                "**`/antinuke`** - Server anti-nuke protection"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔍 Information Commands",
            value=(
                "**`/serverinfo`** - Detailed server statistics\n"
                "**`/userinfo [@user]`** - Member information and history\n"
                "**`/roleinfo <role>`** - Detailed role information\n"
                "**`/channelinfo [#channel]`** - Channel configuration details"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚔️ Advanced Actions",
            value=(
                "**`/lockdown [#channel] [reason]`** - Restrict channel access\n"
                "**`/unlock [#channel]`** - Remove channel restrictions\n"
                "**`/slowmode <seconds> [#channel]`** - Set channel slowmode\n"
                "**`/massban <user_ids> [reason]`** - Ban multiple users at once\n"
                "**`/nuke [#channel] [reason]`** - Clone and replace channel"
            ),
            inline=False
        )
        
        embed.set_footer(text="These commands require appropriate moderator permissions")
        return embed
    
    # Removed point_moderation_embed and warnings_embed as they're now part of ModCog
    
    def get_diagnostics_embed(self):
        """Diagnostics embed"""
        embed = discord.Embed(
            title="🔧 Diagnostics & Testing",
            description="Bot health monitoring and troubleshooting tools",
            color=0x28A745
        )
        
        commands = [
            ("**`/diag`**", "Comprehensive bot diagnostics and health check"),
            ("**`/ping`**", "Check bot latency and connection status"),
            ("**`/info`**", "Bot information, uptime, and version details")
        ]
        
        for cmd, desc in commands:
            embed.add_field(name=cmd, value=desc, inline=False)
            
        embed.add_field(
            name="🩺 Health Monitoring",
            value=(
                "• Database connectivity\n"
                "• File system checks\n"
                "• Environment validation\n"
                "• Permission verification\n"
                "• Performance metrics"
            ),
            inline=False
        )
        
        embed.set_footer(text="Use these tools to troubleshoot any issues")
        return embed


async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
