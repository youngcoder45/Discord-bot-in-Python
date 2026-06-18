import discord
from discord import app_commands
from discord.ext import commands


class RulesCog(commands.Cog):
    """Commands for displaying server rules."""

    def __init__(self, bot):
        self.bot = bot
        self.rules = {
            "r1": "**R1 ❯ Follow Discord Terms & Community Guidelines**\n\nAll members must follow Discord's Terms of Service and Community Guidelines. Server rules supplement Discord's rules. Approved client modifications such as Vencord or BetterDiscord are allowed if they comply with Discord ToS.",
            "r2": "**R2 ❯ Respect Everyone**\n\nTreat all members, staff, guests, and public figures with respect. Personal attacks, harassment, bullying, threats, intimidation, or hostile behavior are not allowed. This is NOT a Dating Server — being a creep, DMing random members, asking for pics/numbers is strictly NOT allowed!",
            "r3": "**R3 ❯ No Hate or Discrimination**\n\nRacism, casteism, sexism, religious hatred, xenophobia, homophobia, or discrimination of any kind is prohibited. Do not use someone's identity, background, or beliefs as an insult.",
            "r4": "**R4 ❯ Protect Privacy**\n\nSharing, leaking, or requesting personal information is prohibited. This includes names, phone numbers, addresses, IPs, IDs, social media accounts, and similar data. Doxxing, swatting, or related threats result in a permanent ban.",
            "r5": "**R5 ❯ No Scams, Malware, or Malicious Activity**\n\nScams, phishing, malware, viruses, IP grabbers, malicious links, and similar harmful content are prohibited. Cybersecurity discussions are allowed only in designated channels and must not promote abuse.",
            "r6": "**R6 ❯ Keep Content Appropriate**\n\nNSFW, pornographic, graphic, gore, shock, or illegal content is not allowed. Attempts to bypass this rule are also prohibited.",
            "r7": "**R7 ❯ No Extremism, Violence, or Criminal Advocacy**\n\nDo not promote or encourage violence, terrorism, criminal activity, or extremist ideologies. Threats, even as jokes, may result in immediate removal.",
            "r8": "**R8 ❯ No Spam or Advertising**\n\nDo not spam messages, reactions, sounds, mentions, emojis, or commands. Excessive pings, unsolicited promotions, advertisements, and invite links are prohibited — this includes DM advertisement. Violations will lead to unappealable permanent ban.",
            "r9": "**R9 ❯ Use Appropriate Channels**\n\nKeep discussions in relevant channels and follow channel topics. Staff may move, lock, mute, or redirect discussions to maintain order.",
            "r10": "**R10 ❯ Voice Channel Rules**\n\nEarrape, soundboard abuse, excessive noise, voice changer abuse, harassment, or disruption are prohibited. Do not record or share voice conversations without consent. Respect the purpose of each voice channel.",
            "r11": "**R11 ❯ Profiles Must Follow Server Rules**\n\nUsernames, nicknames, bios, avatars, statuses, banners, and profile content must comply with server rules and Discord ToS. Impersonation is prohibited.",
            "r12": "**R12 ❯ Respect Moderation & Use Common Sense**\n\nRespect moderation decisions and use proper appeal channels. Rules cannot cover every situation; exploiting loopholes or harming the community is not allowed. Use common sense.",
            "r34": "**R34 ❯ Heyy That's Not Allowed!**\n\nRule 34 content is strictly prohibited on this server.\nThis includes images, videos, text, or any other media depicting explicit content of fictional characters.\nViolations will result in immediate action.",
            "tldr": "**TL;DR**\nBe respectful. Protect privacy. No hate, scams, NSFW, spam, or malicious activity. Follow Discord ToS. Use common sense. Respect moderation.",
        }

    async def send_rule(self, ctx, rule_key):
        rule_content = self.rules.get(rule_key)
        if rule_content:
            embed = discord.Embed(description=rule_content, color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Rule `{rule_key}` not found.")

    @commands.command(name="r1", help="R1: Follow Discord Terms & Community Guidelines")
    async def rule1(self, ctx):
        await self.send_rule(ctx, "r1")

    @commands.command(name="r2", help="R2: Respect Everyone")
    async def rule2(self, ctx):
        await self.send_rule(ctx, "r2")

    @commands.command(name="r3", help="R3: No Hate or Discrimination")
    async def rule3(self, ctx):
        await self.send_rule(ctx, "r3")

    @commands.command(name="r4", help="R4: Protect Privacy")
    async def rule4(self, ctx):
        await self.send_rule(ctx, "r4")

    @commands.command(name="r5", help="R5: No Scams, Malware, or Malicious Activity")
    async def rule5(self, ctx):
        await self.send_rule(ctx, "r5")

    @commands.command(name="r6", help="R6: Keep Content Appropriate")
    async def rule6(self, ctx):
        await self.send_rule(ctx, "r6")

    @commands.command(
        name="r7", help="R7: No Extremism, Violence, or Criminal Advocacy"
    )
    async def rule7(self, ctx):
        await self.send_rule(ctx, "r7")

    @commands.command(name="r8", help="R8: No Spam or Advertising")
    async def rule8(self, ctx):
        await self.send_rule(ctx, "r8")

    @commands.command(name="r9", help="R9: Use Appropriate Channels")
    async def rule9(self, ctx):
        await self.send_rule(ctx, "r9")

    @commands.command(name="r10", help="R10: Voice Channel Rules")
    async def rule10(self, ctx):
        await self.send_rule(ctx, "r10")

    @commands.command(name="r11", help="R11: Profiles Must Follow Server Rules")
    async def rule11(self, ctx):
        await self.send_rule(ctx, "r11")

    @commands.command(name="r12", help="R12: Respect Moderation & Use Common Sense")
    async def rule12(self, ctx):
        await self.send_rule(ctx, "r12")

    @commands.command(name="r34", help="R34: Heyy That's Not Allowed!")
    async def rule34(self, ctx):
        await self.send_rule(ctx, "r34")

    @commands.command(name="tldr", help="TL;DR of the rules")
    async def tldr_rule(self, ctx):
        await self.send_rule(ctx, "tldr")


async def setup(bot):
    await bot.add_cog(RulesCog(bot))
