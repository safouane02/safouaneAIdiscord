# safouane02.github

import os
import discord
from discord import app_commands
from discord.ext import commands

from src.services.premium import (
    get_tier, set_tier, get_plan, get_premium_info,
    get_token_usage, PLANS, WEBSITE_URL,
)
from src.services.logger import get_logger

log = get_logger("premium")


class PremiumCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _is_owner(self, user_id: int) -> bool:
        return user_id == int(os.getenv("OWNER_ID", "0"))

    @app_commands.command(name="premium", description="View your server's plan and token usage")
    async def premium(self, interaction: discord.Interaction):
        info = await get_premium_info(interaction.guild.id)
        tier = info["tier"]
        plan = info["plan"]
        used = info["tokens_used_today"]
        limit = plan["daily_tokens"]

        embed = discord.Embed(
            title=f"{plan['emoji']} {plan['name']} Plan",
            color=plan["color"],
        )

        if limit < 999999:
            progress = min(used / limit, 1.0)
            bar_filled = int(progress * 20)
            bar = "█" * bar_filled + "░" * (20 - bar_filled)
            usage_text = f"`{bar}` {used:,} / {limit:,}"
            if progress >= 0.9:
                usage_text += " ⚠️"
        else:
            usage_text = f"{used:,} / ∞"

        embed.add_field(name="📊 Daily Token Usage", value=usage_text, inline=False)
        embed.add_field(name="🤖 AI Model", value=plan["ai_model"].capitalize(), inline=True)
        embed.add_field(name="⭐ XP Boost", value=f"x{plan['xp_boost']}", inline=True)
        embed.add_field(name="🎭 Reaction Roles", value=str(plan["reaction_roles"]), inline=True)
        embed.add_field(name="🎖️ Level Roles", value=str(plan["max_level_roles"]), inline=True)
        embed.add_field(name="👋 Custom Welcome", value="✅" if plan["custom_welcome"] else "❌", inline=True)
        embed.add_field(name="🛡️ AutoMod", value="✅" if plan["automod"] else "❌", inline=True)

        if info["expires_at"]:
            embed.add_field(name="⏳ Expires", value=info["expires_at"][:10], inline=False)

        if tier == "free":
            embed.add_field(
                name="⬆️ ترقية خطتك",
                value=f"[اضغط هنا للاشتراك]({WEBSITE_URL})",
                inline=False,
            )
        else:
            embed.add_field(
                name="🔄 تجديد أو تغيير الخطة",
                value=f"[زيارة الموقع]({WEBSITE_URL})",
                inline=False,
            )

        embed.set_footer(text="github.com/safouane02")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="plans", description="Compare all available plans")
    async def plans(self, interaction: discord.Interaction):
        current_tier = await get_tier(interaction.guild.id)

        embed = discord.Embed(
            title="💎 Available Plans",
            description=f"Current plan: **{PLANS[current_tier]['emoji']} {PLANS[current_tier]['name']}**\n\n"
                        f"[🛒 اشترِ الآن من الموقع]({WEBSITE_URL})",
            color=0x5865F2,
        )

        for tier, plan in PLANS.items():
            is_current = "← خطتك الحالية" if tier == current_tier else ""
            value = (
                f"📊 **{plan['daily_tokens']:,}** token/يوم\n"
                f"🤖 AI: **{plan['ai_model']}**\n"
                f"⭐ XP Boost: **x{plan['xp_boost']}**\n"
                f"🎭 Reaction Roles: **{plan['reaction_roles']}**\n"
                f"💰 **{plan['price']}** {is_current}"
            )
            embed.add_field(
                name=f"{plan['emoji']} {plan['name']}",
                value=value,
                inline=True,
            )

        embed.set_footer(text=f"للشراء: {WEBSITE_URL}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setpremium", description="Set premium tier for a server (owner only)")
    @app_commands.describe(
        guild_id="Server ID",
        tier="Premium tier",
        days="Duration in days (0 = permanent)",
    )
    @app_commands.choices(tier=[
        app_commands.Choice(name="🆓 Free", value="free"),
        app_commands.Choice(name="⭐ Basic", value="basic"),
        app_commands.Choice(name="💎 Pro", value="pro"),
        app_commands.Choice(name="👑 Elite", value="elite"),
    ])
    async def setpremium(self, interaction: discord.Interaction, guild_id: str, tier: str, days: int = 30):
        if not self._is_owner(interaction.user.id):
            await interaction.response.send_message("⛔ Owner only.", ephemeral=True)
            return

        try:
            gid = int(guild_id)
        except ValueError:
            await interaction.response.send_message("⚠️ Invalid guild ID.", ephemeral=True)
            return

        duration = days if days > 0 else None
        await set_tier(gid, tier, duration, interaction.user.id)

        plan = PLANS[tier]
        await interaction.response.send_message(
            f"✅ Set **{plan['emoji']} {plan['name']}** for guild `{gid}`"
            + (f" for **{days} days**" if duration else " permanently"),
            ephemeral=True,
        )
        log.info(f"Premium set: guild {gid} → {tier} by {interaction.user}")

    @app_commands.command(name="premiumlist", description="List all premium servers (owner only)")
    async def premiumlist(self, interaction: discord.Interaction):
        if not self._is_owner(interaction.user.id):
            await interaction.response.send_message("⛔ Owner only.", ephemeral=True)
            return

        import aiosqlite
        from src.services.database import DB_PATH_STR

        async with aiosqlite.connect(DB_PATH_STR) as db:
            async with db.execute(
                "SELECT guild_id, tier, expires_at FROM premium WHERE tier != 'free' ORDER BY tier"
            ) as cur:
                rows = await cur.fetchall()

        if not rows:
            await interaction.response.send_message("No premium servers.", ephemeral=True)
            return

        lines = []
        for guild_id, tier, expires in rows:
            guild = self.bot.get_guild(int(guild_id))
            name = guild.name if guild else f"Unknown ({guild_id})"
            plan = PLANS.get(tier, PLANS["free"])
            exp = expires[:10] if expires else "Permanent"
            used = await get_token_usage(int(guild_id))
            lines.append(f"{plan['emoji']} **{name}** — {plan['name']} | Expires: {exp} | Today: {used:,} tokens")

        embed = discord.Embed(
            title="💎 Premium Servers",
            description="\n".join(lines),
            color=0xFFD700,
        )
        embed.set_footer(text=f"Total: {len(lines)} premium servers")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def cog_app_command_error(self, interaction, error):
        log.error(f"Premium error: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message("⚠️ Something went wrong.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(PremiumCog(bot))
