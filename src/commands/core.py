import discord
import os
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

class Core(commands.Cog):
    """Core hybrid commands: ping, info, help."""
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

    @commands.hybrid_command(name="help", help="Show all bot commands organized by category")
    async def help_cmd(self, ctx: commands.Context):
        """Enhanced interactive help command with organized categories."""
        view = HelpView(self.bot)
        embed = await view.get_main_embed()
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="bothelp", help="Show all bot commands organized by category (legacy)")
    async def help_cmd_legacy(self, ctx: commands.Context):
        """Enhanced help command with organized categories (legacy version)."""
        embed = discord.Embed(
            title="CodeVerse Bot - Command Reference",
            description="All commands work with both prefix `?` and slash `/` notation\nExample: `?ping` or `/ping`",
            color=0x3498DB,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Core Commands
        core_commands = [
            "**ping** - Check bot latency and responsiveness",
            "**info** - View bot information and uptime",
            "**diag** - Get bot diagnostics and health status",
            "**help** - Show this interactive command reference"
        ]
        embed.add_field(
            name="🏠 Core Commands",
            value="\n".join(core_commands),
            inline=False
        )
        
        # AFK System Commands
        afk_commands = [
            "**`afk [reason]`** - Set yourself as AFK with optional reason",
            "**`unafk`** / **`back`** / **`return`** - Remove your AFK status",
            "**`afklist`** / **`afkstatus`** / **`whoafk`** - List all AFK users in server"
        ]
        embed.add_field(
            name="😴 AFK System",
            value="\n".join(afk_commands),
            inline=False
        )
        
        # Community Commands
        community_commands = [
            "**`quote`** - Get inspirational programming quotes",
            "**`question`** - Random programming questions for learning",
            "**`meme`** - Programming memes and humor",
            "**`suggest <text>`** - Submit suggestions to bot developers"
        ]
        embed.add_field(
            name="🎪 Community & Learning",
            value="\n".join(community_commands),
            inline=False
        )
        
        # Fun & Games Commands
        fun_commands = [
            "**`compliment [@user]`** - Send a random compliment",
            "**`dadjoke`** - Get a dad joke",
            "**`fortune`** - Programming fortune cookie",
            "**`joke`** - Programming jokes",
            "**`flip`** - Flip a coin",
            "**`8ball <question>`** - Magic 8-ball answers",
            "**`roll [NdN]`** - Roll dice (e.g., 2d6)",
            "**`rps <choice>`** - Rock Paper Scissors",
            "**`wyr`** - Would you rather questions",
            "**`hangman`** - Programming-themed hangman",
            "**`riddle`** - Interactive riddles",
            "**`trivia`** - Programming trivia questions",
            "**`kill <@user>`** - Playfully 'eliminate' a user"
        ]
        embed.add_field(
            name="🎮 Fun & Games",
            value="\n".join(fun_commands),
            inline=False
        )
        
        # Programming Utilities
        programming_commands = [
            "**`snippet <lang> <algo>`** - Code snippets (Python, JS, Java, C++)",
            "**`regex [pattern]`** - Common regex patterns (email, phone, etc.)",
            "**`bigO [complexity]`** - Big O notation explanations",
            "**`http [code]`** - HTTP status code lookup",
            "**`git [command]`** - Git command reference",
            "**`encode <format> <text>`** - Encode text (base64, url, hex, binary)",
            "**`decode <format> <text>`** - Decode text (base64, url, hex)",
            "**`hash <algo> <text>`** - Generate hashes (md5, sha1, sha256, sha512)",
            "**`json <text>`** - Format and validate JSON",
            "**`color <value>`** - Convert color formats (hex, rgb, names)",
            "**`uuid [version]`** - Generate UUIDs (v1, v4)",
            "**`timestamp [time] [format]`** - Convert timestamps"
        ]
        embed.add_field(
            name="💻 Programming Utilities",
            value="\n".join(programming_commands),
            inline=False
        )
        
        # Staff Points System
        points_commands = [
            "**`points check [@user]`** - Check points balance",
            "**`points leaderboard`** - View top staff members",
            "**`points top`** - Quick top 3 view",
            "**`points stats [@user]`** - Detailed statistics",
            "**`points history [@user]`** - Points activity log *(Mod)*",
            "**`points add <@user> <amount> [reason]`** - Award points *(Admin)*",
            "**`points remove <@user> <amount> [reason]`** - Remove points *(Admin)*",
            "**`points set <@user> <amount> [reason]`** - Set exact points *(Admin)*",
            "**`points reset <@user> [reason]`** - Reset to zero *(Admin)*",
            "**`points config <action> [value]`** - Configure system *(Admin)*"
        ]
        embed.add_field(
            name="⭐ Staff Points (Aura) System",
            value="\n".join(points_commands),
            inline=False
        )
        
        # Staff Reminder Commands (Admin only)
        reminder_commands = [
            "**`reminder-status`** - Check staff reminder status *(Admin)*",
            "**`remind-now`** - Send manual reminder to staff *(Admin)*",
            "**`staff-channel [#channel]`** - Set staff reminder channel *(Admin)*"
        ]
        embed.add_field(
            name="🔔 Staff Reminder (Admin Only)",
            value="\n".join(reminder_commands),
            inline=False
        )
        
        # Staff Shift Commands
        shift_commands = [
            "**`shift start [note]`** - Start your staff shift *(Staff)*",
            "**`shift end [note]`** - End your staff shift *(Staff)*",
            "**`shift discard`** - Discard current shift *(Staff)*",
            "**`shift admin active`** - View active shifts *(Admin)*",
            "**`shift admin history [user] [days]`** - View shift history *(Admin)*",
            "**`shift admin end <user> [reason]`** - Force end shift *(Admin)*",
            "**`shift admin stats [user] [days]`** - View shift statistics *(Admin)*",
            "**`shift admin summary [days]`** - Staff activity summary *(Admin)*",
            "**`shift settings logs [#channel]`** - Set shift log channel *(Admin)*",
            "**`shift settings addrole <role>`** - Add staff role *(Admin)*",
            "**`shift settings removerole <role>`** - Remove staff role *(Admin)*",
            "**`shift settings clearroles`** - Clear all staff roles *(Admin)*",
            "**`shift settings listroles`** - List staff roles"
        ]
        embed.add_field(
            name="⏰ Staff Shift Tracking",
            value="\n".join(shift_commands),
            inline=False
        )
        
        # Moderation Commands (Admin only)
        moderation_commands = [
            "**`purge <amount> [@user]`** - Delete messages *(Manage Messages)*",
            "**`kick <member> [reason]`** - Kick a member *(Kick Members)*",
            "**`ban <member> [days] [reason]`** - Ban a member *(Ban Members)*",
            "**`unban <user> [reason]`** - Unban a user *(Ban Members)*",
            "**`timeout <member> <minutes> [reason]`** - Timeout a member *(Moderate Members)*",
            "**`untimeout <member> [reason]`** - Remove timeout *(Moderate Members)*",
            "**`warn <member> [reason]`** - Warn a member *(Manage Messages)*",
            "**`slowmode <seconds> [#channel]`** - Set channel slowmode *(Manage Channels)*",
            "**`nick <member> [nickname]`** - Change nickname *(Manage Nicknames)*"
        ]
        embed.add_field(
            name="🛡️ Basic Moderation (Admin Only)",
            value="\n".join(moderation_commands),
            inline=False
        )
        
        # Advanced Moderation Commands
        advanced_mod_commands = [
            "**`serverinfo`** - Detailed server information",
            "**`userinfo [@user]`** - Detailed user information", 
            "**`roleinfo <role>`** - Detailed role information",
            "**`channelinfo [#channel]`** - Detailed channel information",
            "**`lockdown [#channel] [reason]`** - Lock channel *(Manage Channels)*",
            "**`unlock [#channel] [reason]`** - Unlock channel *(Manage Channels)*",
            "**`nuke [#channel] [reason]`** - Delete and recreate channel *(Manage Channels)*",
            "**`massban <user_ids> [days] [reason]`** - Mass ban users *(Ban Members)*",
            "**`listbans`** - List all banned users *(Ban Members)*",
            "**`addrole <@user> <role> [reason]`** - Add role to user *(Manage Roles)*",
            "**`removerole <@user> <role> [reason]`** - Remove role from user *(Manage Roles)*"
        ]
        embed.add_field(
            name="⚔️ Advanced Moderation (Admin Only)",
            value="\n".join(advanced_mod_commands),
            inline=False
        )
        
        # Footer with usage info
        embed.add_field(
            name="💡 Usage Tips",
            value="• Use `?command` or `/command` - both work!\n• Some commands need parameters (shown in `<>` or `[]`)\n• Admin commands require Manage Server permission\n• Staff reminders sent every 2 hours to #staff-chat (ToS compliant)\n• Staff shifts track on-duty time with database logging",
            inline=False
        )
        
        embed.set_footer(text=f"CodeVerse Bot • {len([cmd for cmd in self.bot.commands if not cmd.hidden])} commands available")
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user and self.bot.user.avatar else None)
        
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="commands", help="Quick list of all available commands")
    async def commands_list(self, ctx: commands.Context):
        """Simple command list for quick reference."""
        embed = discord.Embed(
            title="⚡ Quick Command List",
            description="Use `?help` or `/help` for detailed descriptions",
            color=discord.Color.green()
        )
        
        # Get all non-hidden commands
        all_commands = []
        for cmd in sorted(self.bot.commands, key=lambda c: c.name):
            if not cmd.hidden:
                all_commands.append(f"`{cmd.name}`")
        
        # Split into chunks for better display
        chunk_size = 10
        command_chunks = [all_commands[i:i + chunk_size] for i in range(0, len(all_commands), chunk_size)]
        
        for i, chunk in enumerate(command_chunks):
            field_name = f"Commands ({i*chunk_size + 1}-{min((i+1)*chunk_size, len(all_commands))})"
            embed.add_field(
                name=field_name,
                value=" • ".join(chunk),
                inline=False
            )
        
        embed.add_field(
            name="💡 Remember",
            value="All commands work with both `?` and `/` prefixes!\nUse `?help` for full descriptions and examples.",
            inline=False
        )
        
        embed.set_footer(text=f"Total: {len(all_commands)} commands available")
        await ctx.reply(embed=embed, mention_author=False)


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
                f"**Categories:** 10+\n"
                f"**Server Exclusive:** Professional features\n"
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
                "• `/quote` - Programming quotes\n"
                "• `/joke` - Programming humor"
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
                label="🎪 Community & Learning", 
                description="Quotes, questions, memes, and suggestions",
                value="community",
                emoji="🎪"
            ),
            discord.SelectOption(
                label="🎮 Fun & Games",
                description="Entertainment commands and mini-games",
                value="fun",
                emoji="🎮"
            ),
            discord.SelectOption(
                label="💻 Programming Utilities",
                description="Code snippets, regex, encoding, and more",
                value="programming",
                emoji="💻"
            ),
            discord.SelectOption(
                label="🛡️ Moderation",
                description="Basic and advanced moderation tools",
                value="moderation",
                emoji="🛡️"
            ),
            discord.SelectOption(
                label="⭐ Staff Systems",
                description="Points, shifts, elections, and management",
                value="staff",
                emoji="⭐"
            ),
            discord.SelectOption(
                label="🎨 Embed Tools",
                description="Create and edit beautiful embeds",
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
            "community": self.get_community_embed(),
            "fun": self.get_fun_embed(),
            "programming": self.get_programming_embed(),
            "moderation": self.get_moderation_embed(),
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
            ("**`/diag`**", "Get comprehensive bot diagnostics"),
            ("**`/commands`**", "Quick list of all available commands")
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
    
    def get_community_embed(self):
        """Community commands embed"""
        embed = discord.Embed(
            title="🎪 Community & Learning",
            description="Educational content and community interaction",
            color=0x9B59B6
        )
        
        commands = [
            ("**`/quote`**", "Get inspirational programming quotes and wisdom"),
            ("**`/question`**", "Random programming questions for learning and practice"),
            ("**`/meme`**", "Programming memes and humor for the community"),
            ("**`/suggest <text>`**", "Submit suggestions to bot developers (ephemeral)")
        ]
        
        for cmd, desc in commands:
            embed.add_field(name=cmd, value=desc, inline=False)
            
        embed.set_footer(text="Content refreshes from curated databases")
        return embed
    
    def get_fun_embed(self):
        """Fun commands embed"""
        embed = discord.Embed(
            title="🎮 Fun & Games",
            description="Entertainment and interactive mini-games",
            color=0xE91E63
        )
        
        commands = [
            ("**`/flip`**", "Flip a virtual coin (heads or tails)"),
            ("**`/roll [sides]`**", "Roll dice with specified sides (default: 6)"),
            ("**`/8ball <question>`**", "Ask the magic 8-ball a question"),
            ("**`/choose <choices>`**", "Randomly choose from comma-separated options"),
            ("**`/compliment [@user]`**", "Send a random compliment to someone"),
            ("**`/joke`**", "Get programming jokes and humor"),
            ("**`/dadjoke`**", "Classic dad jokes for the community"),
            ("**`/fortune`**", "Programming fortune cookies")
        ]
        
        for cmd, desc in commands:
            embed.add_field(name=cmd, value=desc, inline=False)
            
        embed.set_footer(text="All games are family-friendly and professional")
        return embed
    
    def get_programming_embed(self):
        """Programming utilities embed"""
        embed = discord.Embed(
            title="💻 Programming Utilities",
            description="Developer tools and programming helpers",
            color=0x3498DB
        )
        
        commands = [
            ("**`/snippet <lang> <algo>`**", "Code snippets (Python, JS, Java, C++)"),
            ("**`/encode <format> <text>`**", "Encode text (base64, url, hex, binary)"),
            ("**`/decode <format> <text>`**", "Decode text (base64, url, hex)"),
            ("**`/hash <algo> <text>`**", "Generate hashes (md5, sha1, sha256, sha512)"),
            ("**`/json <text>`**", "Format and validate JSON"),
            ("**`/regex [pattern]`**", "Common regex patterns (email, phone, etc.)"),
            ("**`/color <value>`**", "Convert color formats (hex, rgb, names)"),
            ("**`/uuid [version]`**", "Generate UUIDs (v1, v4)"),
            ("**`/http [code]`**", "HTTP status code lookup"),
            ("**`/git [command]`**", "Git command reference")
        ]
        
        for cmd, desc in commands:
            embed.add_field(name=cmd, value=desc, inline=False)
            
        embed.set_footer(text="Perfect for coding assistance and learning")
        return embed
    
    def get_moderation_embed(self):
        """Moderation commands embed"""
        embed = discord.Embed(
            title="🛡️ Moderation Tools",
            description="Basic and advanced server management commands",
            color=0xE74C3C
        )
        
        embed.add_field(
            name="🔨 Basic Moderation",
            value=(
                "**`/purge <amount> [@user]`** - Delete messages *(Manage Messages)*\n"
                "**`/kick <member> [reason]`** - Kick member *(Kick Members)*\n"
                "**`/ban <member> [days] [reason]`** - Ban member *(Ban Members)*\n"
                "**`/unban <user> [reason]`** - Unban user *(Ban Members)*\n"
                "**`/timeout <member> <minutes> [reason]`** - Timeout member *(Moderate Members)*\n"
                "**`/warn <member> [reason]`** - Warn member *(Manage Messages)*\n"
                "**`/slowmode <seconds> [#channel]`** - Set slowmode *(Manage Channels)*"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚔️ Advanced Moderation",
            value=(
                "**`/serverinfo`** - Detailed server information\n"
                "**`/userinfo [@user]`** - Detailed user information\n"
                "**`/lockdown [#channel] [reason]`** - Lock channel *(Manage Channels)*\n"
                "**`/unlock [#channel] [reason]`** - Unlock channel *(Manage Channels)*\n"
                "**`/nuke [#channel] [reason]`** - Delete and recreate channel *(Manage Channels)*\n"
                "**`/massban <user_ids> [reason]`** - Mass ban users *(Ban Members)*\n"
                "**`/listbans`** - List banned users *(Ban Members)*"
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
        
        embed.add_field(
            name="🗳️ Elections",
            value=(
                "**`/election create <title> <candidates> [duration]`** - Create election *(Mod)*\n"
                "**`/election results`** - View current results\n"
                "**`/election end`** - Force end election *(Mod)*"
            ),
            inline=False
        )
        
        embed.set_footer(text="Staff systems include automatic recognition and logging")
        return embed
    
    def get_embeds_embed(self):
        """Embed tools embed"""
        embed = discord.Embed(
            title="🎨 Embed Creation Tools",
            description="Professional embed creation and editing tools",
            color=0x17A2B8
        )
        
        commands = [
            ("**`/embed`**", "Interactive embed creator with popup form"),
            ("**`/editembed <message_id>`**", "Edit existing embeds made by the bot"),
            ("**`/embedquick <title> <description> [color]`**", "Quick embed creation"),
            ("**`/embedrules <rules> [title]`**", "Pre-formatted rules embed"),
            ("**`/embedhelp`**", "Detailed help for embed creation")
        ]
        
        for cmd, desc in commands:
            embed.add_field(name=cmd, value=desc, inline=False)
            
        embed.add_field(
            name="✨ Features",
            value=(
                "• Interactive popup forms\n"
                "• Color customization\n"
                "• Image and thumbnail support\n"
                "• Footer and timestamp options\n"
                "• Professional formatting"
            ),
            inline=False
        )
        
        embed.set_footer(text="Create beautiful, professional embeds with ease")
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
