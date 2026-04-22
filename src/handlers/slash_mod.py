# safouane02.github

import discord
from datetime import timedelta
from discord import app_commands
from discord.ext import commands

from src.services.mod_logger import add_case, get_user_history, get_warnings
from src.services.log_service import send_log, mod_log_embed
from src.services.logger import get_logger
from src.services.moderation import parse_duration

log = get_logger("slash_mod")


class SlashModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="banner", description="Show a member's banner [Basic+]")
    @app_commands.describe(member="Member to check")
    async def banner(self, interaction: discord.Interaction, member: discord.Member = None):
        from src.services.plan_guard import require_plan
        if not await require_plan(interaction, "banner"):
            return
        member = member or interaction.user
        user = await self.bot.fetch_user(member.id)
        if not user.banner:
            await interaction.response.send_message(f"⚠️ {member.mention} has no banner.", ephemeral=True)
            return
        embed = discord.Embed(title=f"{member}'s Banner", color=0x5865F2)
        embed.set_image(url=user.banner.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="Member to ban", reason="Reason for ban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.ban(reason=reason)
        case_id = add_case(interaction.guild.id, member.id, interaction.user.id, "ban", reason)
        embed = mod_log_embed("Ban", member, interaction.user, reason, 0xED4245)
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, self.bot, embed)
        log.info(f"/ban {member} by {interaction.user} — {reason}")

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="Member to kick", reason="Reason for kick")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.kick(reason=reason)
        add_case(interaction.guild.id, member.id, interaction.user.id, "kick", reason)
        embed = mod_log_embed("Kick", member, interaction.user, reason, 0xFEE75C)
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, self.bot, embed)

    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.describe(member="Member to timeout", duration="Duration: 10m, 1h, 1d", reason="Reason")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member,
                      duration: str = "10m", reason: str = "No reason provided"):
        seconds = parse_duration(duration)
        if seconds <= 0:
            await interaction.response.send_message("⚠️ Invalid duration. Use: `10m`, `1h`, `1d`", ephemeral=True)
            return
        until = discord.utils.utcnow() + timedelta(seconds=seconds)
        await member.timeout(until, reason=reason)
        add_case(interaction.guild.id, member.id, interaction.user.id, "timeout", reason)
        embed = mod_log_embed(f"Timeout ({duration})", member, interaction.user, reason, 0x5865F2)
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, self.bot, embed)

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(member="Member to warn", reason="Reason for warning")
    @app_commands.checks.has_permissions(kick_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        add_case(interaction.guild.id, member.id, interaction.user.id, "warn", reason)
        warns = get_warnings(interaction.guild.id, member.id)
        embed = mod_log_embed(f"Warning (#{len(warns)} total)", member, interaction.user, reason, 0xFFA500)
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, self.bot, embed)
        try:
            await member.send(f"⚠️ You were warned in **{interaction.guild.name}**\nReason: {reason}")
        except discord.Forbidden:
            pass

    @app_commands.command(name="mute", description="Mute a member")
    @app_commands.describe(member="Member to mute", reason="Reason")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        role = discord.utils.get(interaction.guild.roles, name="Muted")
        if not role:
            role = await interaction.guild.create_role(name="Muted")
            for ch in interaction.guild.channels:
                await ch.set_permissions(role, send_messages=False, speak=False)
        await member.add_roles(role, reason=reason)
        add_case(interaction.guild.id, member.id, interaction.user.id, "mute", reason)
        embed = mod_log_embed("Mute", member, interaction.user, reason, 0x5865F2)
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, self.bot, embed)

    @app_commands.command(name="unmute", description="Unmute a member")
    @app_commands.describe(member="Member to unmute")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        role = discord.utils.get(interaction.guild.roles, name="Muted")
        if role and role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(f"🔊 {member.mention} has been unmuted.")
        else:
            await interaction.response.send_message(f"⚠️ {member.mention} is not muted.", ephemeral=True)

    @app_commands.command(name="warnings", description="View a member's warnings")
    @app_commands.describe(member="Member to check")
    @app_commands.checks.has_permissions(kick_members=True)
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        warns = get_warnings(interaction.guild.id, member.id)
        if not warns:
            await interaction.response.send_message(f"✅ {member.mention} has no warnings.", ephemeral=True)
            return
        lines = [f"**#{w['id']}** — {w['reason']}" for w in warns]
        embed = discord.Embed(title=f"⚠️ Warnings for {member}", description="\n".join(lines), color=0xFFA500)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="history", description="View a member's moderation history")
    @app_commands.describe(member="Member to check")
    @app_commands.checks.has_permissions(kick_members=True)
    async def history(self, interaction: discord.Interaction, member: discord.Member):
        cases = get_user_history(interaction.guild.id, member.id)
        if not cases:
            await interaction.response.send_message(f"✅ No history for {member.mention}.", ephemeral=True)
            return
        lines = [f"**#{c['id']}** `{c['action']}` — {c['reason']}" for c in cases[-10:]]
        embed = discord.Embed(title=f"📋 History for {member}", description="\n".join(lines), color=0x5865F2)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="rank", description="Check your or someone's rank")
    @app_commands.describe(member="Member to check (optional)")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        from src.services.level_service import get_user, get_rank, xp_for_level
        member = member or interaction.user
        data = await get_user(interaction.guild.id, member.id)
        rank_pos = await get_rank(interaction.guild.id, member.id)
        xp_needed = xp_for_level(data["level"] + 1)
        progress = min(data["xp"] / max(xp_needed, 1), 1.0)
        bar = "█" * int(progress * 20) + "░" * (20 - int(progress * 20))

        embed = discord.Embed(title=f"📊 {member.display_name}", color=member.color or 0x5865F2)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Rank", value=f"#{rank_pos}", inline=True)
        embed.add_field(name="Level", value=str(data["level"]), inline=True)
        embed.add_field(name="XP", value=f"{data['xp']:,} / {xp_needed:,}", inline=True)
        embed.add_field(name="Progress", value=f"`{bar}` {int(progress * 100)}%", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Get info about a member")
    @app_commands.describe(member="Member to check")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(title=str(member), color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        roles = [r.mention for r in member.roles[1:]]
        embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles[:10]) or "None", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Get info about the server")
    async def serverinfo(self, interaction: discord.Interaction):
        g = interaction.guild
        embed = discord.Embed(title=g.name, color=0x5865F2)
        embed.set_thumbnail(url=g.icon.url if g.icon else None)
        embed.add_field(name="Members", value=g.member_count, inline=True)
        embed.add_field(name="Channels", value=len(g.channels), inline=True)
        embed.add_field(name="Roles", value=len(g.roles), inline=True)
        embed.add_field(name="Owner", value=g.owner.mention if g.owner else "N/A", inline=True)
        embed.add_field(name="Created", value=g.created_at.strftime("%Y-%m-%d"), inline=True)
        await interaction.response.send_message(embed=embed)

    async def cog_app_command_error(self, interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("⛔ You don't have permission.", ephemeral=True)
        elif isinstance(error, app_commands.BotMissingPermissions):
            await interaction.response.send_message("⛔ I don't have permission to do that.", ephemeral=True)
        else:
            log.error(f"Slash error: {error}")
            if not interaction.response.is_done():
                await interaction.response.send_message("⚠️ Something went wrong.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SlashModCog(bot))
