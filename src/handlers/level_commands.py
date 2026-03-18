import discord
from discord.ext import commands
from src.services.level_service import (
    get_user, get_rank, get_leaderboard, xp_for_level,
    set_level_role, remove_level_role, get_level_roles,
    update_settings, get_settings, add_xp, get_role_for_level,
    set_user_xp, reset_user_xp,
)
from src.services.logger import get_logger

log = get_logger("levels")


class LevelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── !rank ──────────────────────────────────────────────
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        data = await get_user(ctx.guild.id, member.id)
        rank = await get_rank(ctx.guild.id, member.id)
        current_level = data["level"]
        xp_needed = xp_for_level(current_level + 1)

        embed = discord.Embed(title=f"📊 {member.display_name}", color=member.color or 0x5865F2)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Rank", value=f"#{rank}", inline=True)
        embed.add_field(name="Level", value=str(current_level), inline=True)
        embed.add_field(name="XP", value=f"{data['xp']:,} / {xp_needed:,}", inline=True)
        embed.add_field(name="Messages", value=f"{data['messages']:,}", inline=True)

        progress = min(data["xp"] / max(xp_needed, 1), 1.0)
        bar_filled = int(progress * 20)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        embed.add_field(name="Progress", value=f"`{bar}` {int(progress * 100)}%", inline=False)
        embed.set_footer(text="github.com/safouane02")
        await ctx.reply(embed=embed, mention_author=False)

    # ── !leaderboard ───────────────────────────────────────
    @commands.command(aliases=["lb", "top"])
    async def leaderboard(self, ctx):
        rows = await get_leaderboard(ctx.guild.id, limit=10)
        if not rows:
            await ctx.reply("No data yet. Start chatting to earn XP!", mention_author=False)
            return

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for i, row in enumerate(rows, 1):
            user = ctx.guild.get_member(row["user_id"])
            name = user.display_name if user else f"Unknown ({row['user_id']})"
            medal = medals.get(i, f"`#{i}`")
            lines.append(f"{medal} **{name}** — Level {row['level']} • {row['xp']:,} XP")

        embed = discord.Embed(
            title=f"🏆 {ctx.guild.name} Leaderboard",
            description="\n".join(lines),
            color=0xFFD700,
        )
        embed.set_footer(text="github.com/safouane02")
        await ctx.reply(embed=embed, mention_author=False)

    # ── !setlevelrole ──────────────────────────────────────
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def setlevelrole(self, ctx, level: int, role: discord.Role):
        await set_level_role(ctx.guild.id, level, role.id)
        await ctx.reply(
            f"✅ Members who reach **Level {level}** will receive **{role.name}**",
            mention_author=False,
        )

    # ── !removelevelrole ───────────────────────────────────
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def removelevelrole(self, ctx, level: int):
        await remove_level_role(ctx.guild.id, level)
        await ctx.reply(f"✅ Removed level role for Level {level}.", mention_author=False)

    # ── !levelroles ────────────────────────────────────────
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def levelroles(self, ctx):
        roles = await get_level_roles(ctx.guild.id)
        if not roles:
            await ctx.reply(
                "No level roles set.\nUse `!setlevelrole <level> @role` to add one.",
                mention_author=False,
            )
            return

        lines = []
        for r in roles:
            role = ctx.guild.get_role(r["role_id"])
            role_text = role.mention if role else f"Deleted role ({r['role_id']})"
            lines.append(f"Level **{r['level']}** → {role_text}")

        embed = discord.Embed(
            title="🎖️ Level Roles",
            description="\n".join(lines),
            color=0x5865F2,
        )
        await ctx.reply(embed=embed, mention_author=False)

    # ── !levelsettings ─────────────────────────────────────
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def levelsettings(self, ctx):
        s = await get_settings(ctx.guild.id)
        channel = ctx.guild.get_channel(s["level_channel"]) if s["level_channel"] else "Not set"
        boost = s.get("xp_boost", 1.0)

        embed = discord.Embed(title="⚙️ Level Settings", color=0x5865F2)
        embed.add_field(name="XP per message", value=str(s["xp_per_msg"]), inline=True)
        embed.add_field(name="Cooldown", value=f"{s['xp_cooldown']}s", inline=True)
        embed.add_field(name="XP Boost", value=f"x{boost}", inline=True)
        embed.add_field(name="Level-up channel", value=str(channel), inline=False)
        embed.set_footer(text=(
            "!setlevelupchannel #ch | !setxpboost 2.0 | "
            "!xpsettings xp_per_msg 20 | !xpsettings xp_cooldown 30"
        ))
        await ctx.reply(embed=embed, mention_author=False)

    # ── !setlevelupchannel ─────────────────────────────────
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlevelupchannel(self, ctx, channel: discord.TextChannel = None):
        if not channel:
            await update_settings(ctx.guild.id, level_channel=None)
            await ctx.reply("✅ Level-up announcements will be sent in the same channel as the message.", mention_author=False)
            return
        await update_settings(ctx.guild.id, level_channel=channel.id)
        await ctx.reply(f"✅ Level-up announcements will be sent to {channel.mention}", mention_author=False)

    # ── !setlevelupmsg ─────────────────────────────────────
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlevelupmsg(self, ctx, *, message: str = None):
        """
        Placeholders: {user} {level} {old_level}
        Example: !setlevelupmsg {user} وصل للفل {level} 🎉
        """
        if not message:
            await ctx.reply(
                "Usage: `!setlevelupmsg <message>`\n"
                "Placeholders: `{user}` `{level}` `{old_level}`\n"
                "Example: `!setlevelupmsg {user} وصل للفل {level} 🎉`",
                mention_author=False,
            )
            return
        await update_settings(ctx.guild.id, level_up_msg=message)
        preview = message.replace("{user}", ctx.author.mention).replace("{level}", "5").replace("{old_level}", "4")
        await ctx.reply(f"✅ Level-up message set!\nPreview: {preview}", mention_author=False)

    # ── !setxpboost ────────────────────────────────────────
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setxpboost(self, ctx, multiplier: float):
        if not 0.1 <= multiplier <= 10.0:
            await ctx.reply("⚠️ Boost must be between `0.1` and `10.0`", mention_author=False)
            return
        await update_settings(ctx.guild.id, xp_boost=multiplier)
        await ctx.reply(f"✅ XP boost set to **x{multiplier}** — all members earn {multiplier}x XP now.", mention_author=False)

    # ── !xpsettings ────────────────────────────────────────
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def xpsettings(self, ctx, setting: str = None, value: str = None):
        """
        !xpsettings                      → show all settings
        !xpsettings xp_per_msg 20
        !xpsettings xp_cooldown 30
        """
        if not setting:
            await self.levelsettings(ctx)
            return

        if setting == "xp_per_msg":
            await update_settings(ctx.guild.id, xp_per_msg=int(value))
            await ctx.reply(f"✅ XP per message set to **{value}**", mention_author=False)
        elif setting == "xp_cooldown":
            await update_settings(ctx.guild.id, xp_cooldown=int(value))
            await ctx.reply(f"✅ Cooldown set to **{value}s**", mention_author=False)
        else:
            await ctx.reply("⚠️ Unknown setting. Use: `xp_per_msg` or `xp_cooldown`", mention_author=False)

    # ── !setxp ─────────────────────────────────────────────
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setxp(self, ctx, member: discord.Member, xp: int):
        if xp < 0:
            await ctx.reply("⚠️ XP cannot be negative. Use `!resetxp` to reset.", mention_author=False)
            return
        await set_user_xp(ctx.guild.id, member.id, xp)
        await ctx.reply(f"✅ Set **{member.display_name}**'s XP to **{xp:,}**", mention_author=False)

    # ── !resetxp ───────────────────────────────────────────
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def resetxp(self, ctx, member: discord.Member):
        await reset_user_xp(ctx.guild.id, member.id)
        await ctx.reply(f"✅ Reset **{member.display_name}**'s XP and level to 0.", mention_author=False)

    # ── XP listener ────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if message.content.startswith("!"):
            return

        leveled_up, old_level, new_level = await add_xp(message.guild.id, message.author.id)
        if not leveled_up:
            return

        role_id = await get_role_for_level(message.guild.id, new_level)
        if role_id:
            role = message.guild.get_role(role_id)
            if role:
                try:
                    await message.author.add_roles(role, reason=f"Reached Level {new_level}")
                except discord.Forbidden:
                    pass

        settings = await get_settings(message.guild.id)
        channel_id = settings.get("level_channel")
        channel = message.guild.get_channel(channel_id) if channel_id else message.channel

        # use custom message if set
        custom_msg = settings.get("level_up_msg")
        if custom_msg:
            text = (
                custom_msg
                .replace("{user}", message.author.mention)
                .replace("{level}", str(new_level))
                .replace("{old_level}", str(old_level))
            )
            try:
                await channel.send(text)
            except discord.Forbidden:
                pass
            return

        embed = discord.Embed(
            title="⬆️ Level Up!",
            description=f"**{message.author.mention}** reached **Level {new_level}**! 🎉",
            color=0xFFD700,
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)
        if role_id:
            role = message.guild.get_role(role_id)
            if role:
                embed.add_field(name="🎖️ New Role", value=role.mention, inline=False)

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

        log.info(f"{message.author} leveled up to {new_level} in {message.guild.name}")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("⛔ You don't have permission.", mention_author=False)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.reply("⚠️ Member not found.", mention_author=False)
        elif isinstance(error, (commands.BadArgument, ValueError)):
            await ctx.reply("⚠️ Invalid value.", mention_author=False)
        else:
            log.error(f"Level error in {ctx.command}: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(LevelCog(bot))