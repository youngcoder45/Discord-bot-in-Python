"""
Data Management Commands - Manual backup, restore, and data management
"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import logging
from utils.helpers import create_success_embed, create_error_embed, create_warning_embed

logger = logging.getLogger("codeverse.data_management")

class DataManagement(commands.Cog):
    """Data backup and management commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.hybrid_group(name="data", description="Data management and backup commands")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def data(self, ctx: commands.Context):
        """Data management command group"""
        if ctx.invoked_subcommand is None:
            await self.show_data_status(ctx)
    
    @data.command(name="backup", description="Create an immediate backup of all bot data")
    @commands.has_permissions(administrator=True)
    async def manual_backup(self, ctx: commands.Context):
        """Create an immediate backup of all bot data"""
        embed = discord.Embed(
            title="🔄 Creating Data Backup",
            description="Starting backup process...",
            color=0x0000ff
        )
        embed.add_field(name="Status", value="⏳ In Progress", inline=False)
        
        message = await ctx.reply(embed=embed)
        
        try:
            from utils.data_persistence import backup_data
            await backup_data()
            
            embed = create_success_embed(
                "Backup Completed",
                "All bot data has been successfully backed up!"
            )
            embed.add_field(name="Backup Includes", value="• Staff shift data\n• Staff points data\n• Election data\n• Configuration settings\n• JSON data files", inline=False)
            embed.add_field(name="Backup Locations", value="• GitHub repository (if token configured)\n• Local backup files", inline=False)
            embed.set_footer(text=f"Backup completed at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            await message.edit(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Backup Failed",
                f"An error occurred during backup: {str(e)[:500]}..."
            )
            await message.edit(embed=embed)
            logger.error(f"Manual backup failed: {e}")
    
    @data.command(name="restore", description="Restore data from backup (DANGEROUS)")
    @commands.has_permissions(administrator=True)
    async def manual_restore(self, ctx: commands.Context):
        """Restore data from backup with confirmation"""
        embed = create_warning_embed(
            "⚠️ Data Restore Confirmation",
            "**WARNING: This will OVERWRITE all current data!**\n\n"
            "This action will:\n"
            "• Replace all current staff shift data\n"
            "• Replace all staff points data\n"
            "• Replace all election data\n"
            "• Replace configuration settings\n\n"
            "**This action cannot be undone!**\n\n"
            "Are you absolutely sure you want to proceed?"
        )
        
        view = ConfirmRestoreView()
        message = await ctx.reply(embed=embed, view=view)
        
        await view.wait()
        
        if view.value:
            # Proceed with restore
            embed = discord.Embed(
                title="🔄 Restoring Data",
                description="Starting restore process...",
                color=0xff0000
            )
            embed.add_field(name="Status", value="⏳ In Progress", inline=False)
            embed.add_field(name="Warning", value="⚠️ Do not restart the bot during this process!", inline=False)
            
            await message.edit(embed=embed, view=None)
            
            try:
                from utils.data_persistence import startup_restore
                await startup_restore()
                
                embed = create_success_embed(
                    "Restore Completed",
                    "All bot data has been successfully restored from backup!"
                )
                embed.add_field(name="Restored Data", value="• Staff shift data\n• Staff points data\n• Election data\n• Configuration settings\n• JSON data files", inline=False)
                embed.add_field(name="Next Steps", value="• Restart the bot to ensure all data is loaded properly\n• Verify that all systems are working correctly", inline=False)
                embed.set_footer(text=f"Restore completed at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
                
                await message.edit(embed=embed)
                
            except Exception as e:
                embed = create_error_embed(
                    "❌ Restore Failed",
                    f"An error occurred during restore: {str(e)[:500]}..."
                )
                await message.edit(embed=embed)
                logger.error(f"Manual restore failed: {e}")
        else:
            embed = create_success_embed(
                "✅ Restore Cancelled",
                "Data restore has been cancelled. No changes were made."
            )
            await message.edit(embed=embed, view=None)
    
    @data.command(name="status", description="Show data backup and persistence status")
    async def data_status(self, ctx: commands.Context):
        """Show data backup and persistence status"""
        await self.show_data_status(ctx)
    
    async def show_data_status(self, ctx: commands.Context):
        """Show comprehensive data status"""
        embed = discord.Embed(
            title="📊 Data Management Status",
            description="Current status of bot data and backups",
            color=0x0000ff
        )
        
        # Check GitHub configuration
        import os
        github_token = os.getenv('GITHUB_TOKEN')
        github_repo = os.getenv('GITHUB_REPO', 'youngcoder45/Discord-bot-in-Python')
        
        if github_token:
            github_status = "✅ Configured"
            github_details = f"Repository: `{github_repo}`\nBranch: `bot-data-backup`"
        else:
            github_status = "❌ Not Configured"
            github_details = "Set `GITHUB_TOKEN` environment variable to enable"
        
        embed.add_field(
            name="🔗 GitHub Backup",
            value=f"**Status:** {github_status}\n{github_details}",
            inline=False
        )
        
        # Check local backup files
        from pathlib import Path
        backup_dir = Path("backup")
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("bot_data_backup_*.json"))
            local_status = f"✅ {len(backup_files)} local backup(s) found"
        else:
            local_status = "❌ No local backups found"
        
        embed.add_field(
            name="💾 Local Backups",
            value=f"**Status:** {local_status}\nLocation: `backup/`",
            inline=False
        )
        
        # Check database files
        import os
        db_files = [
            "data/staff_shifts.db",
            "data/staff_points.db", 
            "data/codeverse_bot.db"
        ]
        
        db_status = []
        for db_path in db_files:
            if os.path.exists(db_path):
                size = os.path.getsize(db_path)
                db_status.append(f"✅ `{os.path.basename(db_path)}` ({size} bytes)")
            else:
                db_status.append(f"❌ `{os.path.basename(db_path)}` (missing)")
        
        embed.add_field(
            name="🗄️ Database Files",
            value="\n".join(db_status),
            inline=False
        )
        
        # Backup schedule info
        embed.add_field(
            name="⏰ Automatic Backups",
            value="**Schedule:** Every 6 hours\n**Triggers:** Bot startup, periodic timer\n**Storage:** GitHub + Local files",
            inline=False
        )
        
        # Configuration help
        embed.add_field(
            name="⚙️ Configuration",
            value="**Environment Variables:**\n"
                  "`GITHUB_TOKEN` - GitHub personal access token\n"
                  "`GITHUB_REPO` - Repository for backups (optional)\n"
                  "`BACKUP_BRANCH` - Branch for backups (optional)",
            inline=False
        )
        
        embed.set_footer(text="Use /data backup to create an immediate backup")
        
        await ctx.reply(embed=embed)
    
    @data.command(name="export", description="Export data as downloadable file")
    @commands.has_permissions(administrator=True)
    async def export_data(self, ctx: commands.Context):
        """Export data as downloadable JSON file"""
        try:
            from utils.data_persistence import persistence_manager
            
            # Create backup data
            backup_data = await persistence_manager.collect_all_data()
            
            # Save to temporary file
            import json
            import io
            
            json_content = json.dumps(backup_data, indent=2, ensure_ascii=False)
            file_buffer = io.BytesIO(json_content.encode('utf-8'))
            
            filename = f"codeverse_bot_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            embed = create_success_embed(
                "📤 Data Export Ready",
                "Your bot data has been exported to a downloadable file."
            )
            embed.add_field(name="File Size", value=f"{len(json_content)} characters", inline=True)
            embed.add_field(name="Export Time", value=f"<t:{int(datetime.now().timestamp())}:F>", inline=True)
            
            await ctx.reply(
                embed=embed,
                file=discord.File(file_buffer, filename=filename)
            )
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Export Failed",
                f"Failed to export data: {str(e)[:500]}..."
            )
            await ctx.reply(embed=embed)


class ConfirmRestoreView(discord.ui.View):
    """Confirmation view for data restore"""
    
    def __init__(self):
        super().__init__(timeout=60)
        self.value = None
    
    @discord.ui.button(label="YES, RESTORE DATA", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def confirm_restore(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_restore(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.defer()


async def setup(bot: commands.Bot):
    await bot.add_cog(DataManagement(bot))
