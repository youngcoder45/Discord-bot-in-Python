import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Dict, Tuple
import asyncio
from datetime import datetime, timedelta

class Election(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_elections = {}  # Support multiple elections

    @commands.hybrid_group(name="election", description="Conduct staff elections with weighted votes.")
    @commands.guild_only()
    async def election(self, ctx: commands.Context):
        """Election command group."""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="🗳️ Election System",
                description="**Available Commands:**\n`/election create` - Create a new election\n`/election results` - View current results\n`/election end` - Force end an election",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Vote Weights",
                value="- **Staff**: 2 votes\n- **Top Contributors**: 1 vote\n- **Members**: 0.5 vote",
                inline=False
            )
            await ctx.send(embed=embed)

    @election.command(name="create", description="Create a new staff election poll.")
    @app_commands.describe(
        title="Election title/question",
        candidates="Comma-separated candidate names (e.g. Alice,Bob,Charlie)",
        duration="Duration in minutes (1-1440, default: 60)"
    )
    @commands.has_permissions(manage_guild=True)
    async def create(self, ctx: commands.Context, title: str, candidates: str, duration: int = 60):
        """Create a new election poll."""
        # Validation
        if duration < 1 or duration > 1440:  # Max 24 hours
            await ctx.reply("Duration must be between 1 and 1440 minutes (24 hours).", ephemeral=True)
            return
            
        candidate_list = [c.strip() for c in candidates.split(",") if c.strip()]
        if len(candidate_list) < 2:
            await ctx.reply("❌ You must provide at least 2 candidates.", ephemeral=True)
            return
        if len(candidate_list) > 10:
            await ctx.reply("❌ Maximum 10 candidates allowed.", ephemeral=True)
            return

        # Check if election already exists
        if ctx.guild.id in self.active_elections:
            await ctx.reply("❌ An election is already running in this server. End it first.", ephemeral=True)
            return

        # Create election data
        results: Dict[str, List[Tuple[int, float]]] = {c: [] for c in candidate_list}
        end_time = datetime.utcnow() + timedelta(minutes=duration)
        
        # Create view with buttons
        view = ElectionView(self.bot, results, candidate_list, end_time, ctx.guild.id)
        
        # Create embed
        embed = discord.Embed(
            title=f"🗳️ {title}",
            description="**Vote for your preferred candidate below!**\n\n**Vote Weights:**\n🟦 **Staff**: 2 votes\n🟨 **Top Contributors**: 1 vote\n🟩 **Members**: 0.5 vote",
            color=0x5865F2
        )
        embed.add_field(
            name="📋 Candidates",
            value="\n".join([f"**{i+1}.** {c}" for i, c in enumerate(candidate_list)]),
            inline=False
        )
        embed.add_field(
            name="⏰ Duration",
            value=f"{duration} minutes",
            inline=True
        )
        embed.add_field(
            name="📊 Total Votes",
            value="0",
            inline=True
        )
        embed.set_footer(text="Click buttons below to vote • One vote per person")
        embed.timestamp = datetime.utcnow()

        msg = await ctx.send(embed=embed, view=view)
        
        # Store election data
        self.active_elections[ctx.guild.id] = {
            "message": msg,
            "results": results,
            "candidates": candidate_list,
            "end_time": end_time,
            "title": title,
            "creator": ctx.author.id
        }
        
        await ctx.reply(f"✅ Election started! Voting open for **{duration} minutes**.", ephemeral=True)
        
        # Schedule automatic end
        asyncio.create_task(self._auto_end_election(ctx.guild.id, duration * 60))

    @election.command(name="results", description="View current election results.")
    async def results(self, ctx: commands.Context):
        """Show current election results."""
        if ctx.guild.id not in self.active_elections:
            await ctx.reply("❌ No active election in this server.", ephemeral=True)
            return
            
        election_data = self.active_elections[ctx.guild.id]
        await self._show_results(ctx, election_data, final=False)

    @election.command(name="end", description="Force end the current election.")
    @commands.has_permissions(manage_guild=True)
    async def end(self, ctx: commands.Context):
        """Force end the current election."""
        if ctx.guild.id not in self.active_elections:
            await ctx.reply("❌ No active election in this server.", ephemeral=True)
            return
            
        election_data = self.active_elections[ctx.guild.id]
        await self._end_election(ctx.guild.id)
        await ctx.reply("✅ Election ended manually.")

    async def _auto_end_election(self, guild_id: int, delay: int):
        """Automatically end election after delay."""
        await asyncio.sleep(delay)
        if guild_id in self.active_elections:
            await self._end_election(guild_id)

    async def _end_election(self, guild_id: int):
        """End an election and show final results."""
        if guild_id not in self.active_elections:
            return
            
        election_data = self.active_elections[guild_id]
        msg = election_data["message"]
        
        # Disable view
        view = discord.ui.View()
        for item in msg.view.children:
            item.disabled = True
            view.add_item(item)
        
        # Show final results
        tally = {}
        total_votes = 0
        for candidate, votes in election_data["results"].items():
            candidate_total = sum(weight for _, weight in votes)
            tally[candidate] = candidate_total
            total_votes += candidate_total
        
        sorted_results = sorted(tally.items(), key=lambda x: x[1], reverse=True)
        
        # Create results embed
        embed = discord.Embed(
            title=f"🏆 Final Results: {election_data['title']}",
            description="**Election has ended!**",
            color=0x57F287 if sorted_results else 0xED4245
        )
        
        if sorted_results:
            winner = sorted_results[0]
            embed.add_field(
                name="🥇 Winner",
                value=f"**{winner[0]}** with {winner[1]} votes",
                inline=False
            )
            
            results_text = ""
            for i, (candidate, votes) in enumerate(sorted_results):
                emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else "📊"
                percentage = (votes / total_votes * 100) if total_votes > 0 else 0
                results_text += f"{emoji} **{candidate}**: {votes} votes ({percentage:.1f}%)\n"
            
            embed.add_field(name="📊 Full Results", value=results_text, inline=False)
        else:
            embed.add_field(name="📊 Results", value="No votes were cast.", inline=False)
        
        embed.add_field(name="📈 Total Votes", value=str(total_votes), inline=True)
        embed.add_field(name="👥 Voters", value=str(len(set(user_id for votes in election_data["results"].values() for user_id, _ in votes))), inline=True)
        embed.set_footer(text="Election completed")
        embed.timestamp = datetime.utcnow()
        
        await msg.edit(embed=embed, view=view)
        
        # Clean up
        del self.active_elections[guild_id]

    async def _show_results(self, ctx, election_data, final=False):
        """Show election results."""
        tally = {}
        total_votes = 0
        for candidate, votes in election_data["results"].items():
            candidate_total = sum(weight for _, weight in votes)
            tally[candidate] = candidate_total
            total_votes += candidate_total
        
        sorted_results = sorted(tally.items(), key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(
            title=f"📊 {'Final' if final else 'Current'} Results: {election_data['title']}",
            color=0x57F287 if final else 0xFEE75C
        )
        
        if sorted_results:
            results_text = ""
            for i, (candidate, votes) in enumerate(sorted_results):
                emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else "📊"
                percentage = (votes / total_votes * 100) if total_votes > 0 else 0
                results_text += f"{emoji} **{candidate}**: {votes} votes ({percentage:.1f}%)\n"
            
            embed.add_field(name="Results", value=results_text, inline=False)
        else:
            embed.add_field(name="Results", value="No votes cast yet.", inline=False)
        
        embed.add_field(name="Total Votes", value=str(total_votes), inline=True)
        embed.add_field(name="Voters", value=str(len(set(user_id for votes in election_data["results"].values() for user_id, _ in votes))), inline=True)
        
        if not final:
            time_left = election_data["end_time"] - datetime.utcnow()
            if time_left.total_seconds() > 0:
                embed.add_field(name="Time Remaining", value=f"{int(time_left.total_seconds() // 60)} minutes", inline=True)
        
        await ctx.send(embed=embed, ephemeral=True)

class ElectionView(discord.ui.View):
    def __init__(self, bot, results, candidates, end_time, guild_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.results = results
        self.candidates = candidates
        self.end_time = end_time
        self.guild_id = guild_id
        
        # Add buttons for each candidate
        for candidate in candidates:
            button = VoteButton(candidate, results)
            self.add_item(button)

class VoteButton(discord.ui.Button):
    def __init__(self, candidate: str, results):
        super().__init__(
            label=candidate,
            style=discord.ButtonStyle.primary,
            emoji="🗳️"
        )
        self.candidate = candidate
        self.results = results

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        member = interaction.guild.get_member(user.id)
        
        # Check if election is still active
        election_cog = interaction.client.get_cog("Election")
        if interaction.guild.id not in election_cog.active_elections:
            await interaction.response.send_message("❌ This election has ended.", ephemeral=True)
            return
        
        # Determine vote weight
        weight = 0.5  # Default for regular members
        weight_text = "Member (0.5 votes)"
        
        # Check for staff roles (from staff shift system)
        staff_roles = await self._get_staff_roles(interaction.guild, interaction.client)
        if any(role in member.roles for role in staff_roles):
            weight = 2.0
            weight_text = "Staff (2 votes)"
        else:
            # Check for Top Contributors role
            top_role = discord.utils.get(interaction.guild.roles, name="Top Contributors")
            if top_role and top_role in member.roles:
                weight = 1.0
                weight_text = "Top Contributor (1 vote)"
        
        # Remove previous vote from all candidates
        for candidate_name in self.results.keys():
            self.results[candidate_name] = [(uid, w) for uid, w in self.results[candidate_name] if uid != user.id]
        
        # Add new vote
        if user.id not in [uid for uid, _ in self.results[self.candidate]]:
            self.results[self.candidate].append((user.id, weight))
        
        await interaction.response.send_message(
            f"✅ Vote registered for **{self.candidate}**!\nYour vote weight: **{weight_text}**",
            ephemeral=True
        )

    async def _get_staff_roles(self, guild, bot):
        """Get staff roles from the staff shift system."""
        try:
            staff_cog = bot.get_cog("StaffShifts")
            if staff_cog and hasattr(staff_cog, "service"):
                settings = await staff_cog.service.get_settings(guild.id)
                if hasattr(settings, "staff_role_ids") and settings.staff_role_ids:
                    return [guild.get_role(role_id) for role_id in settings.staff_role_ids if guild.get_role(role_id)]
        except Exception:
            pass
        
        # Fallback: look for common staff role names
        staff_keywords = ["staff", "moderator", "admin", "mod"]
        return [role for role in guild.roles if any(keyword in role.name.lower() for keyword in staff_keywords)]

async def setup(bot: commands.Bot):
    await bot.add_cog(Election(bot))

    async def show_results(self, ctx, msg, results):
        tally = {c: sum(w for _, w in votes) for c, votes in results.items()}
        sorted_results = sorted(tally.items(), key=lambda x: x[1], reverse=True)
        result_str = "\n".join([f"**{c}**: {v} votes" for c, v in sorted_results])
        embed = discord.Embed(title="🗳️ Election Results", description=result_str, color=discord.Color.green())
        await msg.edit(embed=embed, view=None)
        await ctx.send("Election ended! Results above.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Election(bot))
