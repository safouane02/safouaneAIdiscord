# safouane02.github

"""
Agent Handler — ينفذ الأوامر التي يكتشفها bot_agent.
يُستدعى من reply_handler عند الرد على رسالة البوت.
"""

import discord
from datetime import timedelta
from discord.ext import commands

from src.services.bot_agent import detect_intent
from src.services.mod_logger import add_case, get_warnings
from src.services.level_service import get_user, get_rank, xp_for_level, get_leaderboard
from src.services.premium import get_premium_info, PLANS, WEBSITE_URL
from src.services.moderation import parse_duration
from src.services.logger import get_logger

log = get_logger("agent_handler")


async def handle_agent(message: discord.Message, bot: discord.Client) -> bool:
    """
    Try to handle message as an agent command.
    Returns True if handled, False if should fall through to normal AI.
    """
    guild = message.guild
    author = message.author

    mentions = [
        {"id": str(m.id), "name": m.display_name, "mention": m.mention}
        for m in message.mentions
        if not m.bot and m.id != bot.user.id
    ]

    perms = author.guild_permissions if guild else None
    user_permissions = {
        "administrator": bool(perms and perms.administrator),
        "ban_members": bool(perms and perms.ban_members),
        "kick_members": bool(perms and perms.kick_members),
        "manage_messages": bool(perms and perms.manage_messages),
        "manage_channels": bool(perms and perms.manage_channels),
        "moderate_members": bool(perms and perms.moderate_members),
    }

    server_ctx = ""
    if guild:
        server_ctx = f"Server: {guild.name} | Members: {guild.member_count}"

    intent = await detect_intent(
        message=message.content,
        mentions=mentions,
        user_permissions=user_permissions,
        server_context=server_ctx,
    )

    action = intent.get("action", "chat_response")
    response_msg = intent.get("message", "")
    target_id = intent.get("target_id")
    reason = intent.get("reason") or "No reason provided"
    duration = intent.get("duration")
    amount = intent.get("amount")

    log.info(f"Agent action: {action} | User: {author} | Target: {target_id}")

    if action == "chat_response":
        if response_msg:
            await message.reply(response_msg, mention_author=False)
            return True
        return False

    target = guild.get_member(int(target_id)) if target_id and guild else None

    if action in ("ban_member", "kick_member", "timeout_member", "warn_member", "mute_member", "unmute_member"):
        if not target:
            await message.reply("⚠️ لم أتمكن من إيجاد المستخدم المذكور.", mention_author=False)
            return True

        async with message.channel.typing():
            try:
                if action == "ban_member":
                    if not user_permissions["ban_members"]:
                        await message.reply("⛔ ليس لديك صلاحية الحظر.", mention_author=False)
                        return True
                    await target.ban(reason=f"[AI] {reason}")
                    add_case(guild.id, target.id, author.id, "ban", f"[AI] {reason}")
                    embed = _mod_embed("🔨 تم الحظر", target, reason, 0xED4245)
                    await message.reply(embed=embed, mention_author=False)

                elif action == "kick_member":
                    if not user_permissions["kick_members"]:
                        await message.reply("⛔ ليس لديك صلاحية الطرد.", mention_author=False)
                        return True
                    await target.kick(reason=f"[AI] {reason}")
                    add_case(guild.id, target.id, author.id, "kick", f"[AI] {reason}")
                    embed = _mod_embed("👢 تم الطرد", target, reason, 0xFEE75C)
                    await message.reply(embed=embed, mention_author=False)

                elif action == "timeout_member":
                    if not user_permissions["moderate_members"]:
                        await message.reply("⛔ ليس لديك هذه الصلاحية.", mention_author=False)
                        return True
                    seconds = parse_duration(duration or "10m")
                    until = discord.utils.utcnow() + timedelta(seconds=seconds)
                    await target.timeout(until, reason=f"[AI] {reason}")
                    add_case(guild.id, target.id, author.id, "timeout", f"[AI] {reason}")
                    embed = _mod_embed(f"⏱️ تم التقييد ({duration or '10m'})", target, reason, 0x5865F2)
                    await message.reply(embed=embed, mention_author=False)

                elif action == "warn_member":
                    if not user_permissions["kick_members"]:
                        await message.reply("⛔ ليس لديك صلاحية التحذير.", mention_author=False)
                        return True
                    add_case(guild.id, target.id, author.id, "warn", f"[AI] {reason}")
                    warns = get_warnings(guild.id, target.id)
                    embed = _mod_embed(f"⚠️ تحذير (#{len(warns)})", target, reason, 0xFFA500)
                    await message.reply(embed=embed, mention_author=False)
                    try:
                        await target.send(f"⚠️ تلقيت تحذيراً في **{guild.name}**\nالسبب: {reason}")
                    except discord.Forbidden:
                        pass

                elif action == "mute_member":
                    if not user_permissions["moderate_members"]:
                        await message.reply("⛔ ليس لديك هذه الصلاحية.", mention_author=False)
                        return True
                    role = discord.utils.get(guild.roles, name="Muted")
                    if not role:
                        role = await guild.create_role(name="Muted")
                        for ch in guild.channels:
                            await ch.set_permissions(role, send_messages=False, speak=False)
                    await target.add_roles(role, reason=f"[AI] {reason}")
                    add_case(guild.id, target.id, author.id, "mute", f"[AI] {reason}")
                    embed = _mod_embed("🔇 تم الكتم", target, reason, 0x5865F2)
                    await message.reply(embed=embed, mention_author=False)

                elif action == "unmute_member":
                    role = discord.utils.get(guild.roles, name="Muted")
                    if role and role in target.roles:
                        await target.remove_roles(role)
                        await message.reply(f"🔊 تم رفع الكتم عن {target.mention}", mention_author=False)
                    else:
                        await message.reply(f"⚠️ {target.mention} غير مكتوم.", mention_author=False)

            except discord.Forbidden:
                await message.reply("⛔ لا أملك الصلاحية لتنفيذ هذا.", mention_author=False)
            except Exception as e:
                log.error(f"Agent mod error: {e}")
                await message.reply("⚠️ حدث خطأ أثناء التنفيذ.", mention_author=False)

        return True

    elif action == "clear_messages":
        if not user_permissions["manage_messages"]:
            await message.reply("⛔ ليس لديك صلاحية حذف الرسائل.", mention_author=False)
            return True
        count = int(amount) if amount else 10
        await message.channel.purge(limit=count)
        msg = await message.channel.send(f"🗑️ تم حذف **{count}** رسالة.")
        import asyncio
        await asyncio.sleep(3)
        await msg.delete()
        return True

    elif action == "lock_channel":
        if not user_permissions["manage_channels"]:
            await message.reply("⛔ ليس لديك الصلاحية.", mention_author=False)
            return True
        await message.channel.set_permissions(guild.default_role, send_messages=False)
        await message.reply("🔒 تم قفل القناة.", mention_author=False)
        return True

    elif action == "unlock_channel":
        if not user_permissions["manage_channels"]:
            await message.reply("⛔ ليس لديك الصلاحية.", mention_author=False)
            return True
        await message.channel.set_permissions(guild.default_role, send_messages=None)
        await message.reply("🔓 تم فتح القناة.", mention_author=False)
        return True

    elif action == "show_rank":
        check_user = target or author
        data = await get_user(guild.id, check_user.id)
        rank_pos = await get_rank(guild.id, check_user.id)
        xp_needed = xp_for_level(data["level"] + 1)
        progress = min(data["xp"] / max(xp_needed, 1), 1.0)
        bar = "█" * int(progress * 20) + "░" * (20 - int(progress * 20))

        embed = discord.Embed(title=f"📊 {check_user.display_name}", color=0x5865F2)
        embed.set_thumbnail(url=check_user.display_avatar.url)
        embed.add_field(name="الترتيب", value=f"#{rank_pos}", inline=True)
        embed.add_field(name="المستوى", value=str(data["level"]), inline=True)
        embed.add_field(name="XP", value=f"{data['xp']:,} / {xp_needed:,}", inline=True)
        embed.add_field(name="التقدم", value=f"`{bar}` {int(progress * 100)}%", inline=False)
        await message.reply(embed=embed, mention_author=False)
        return True

    elif action == "show_leaderboard":
        rows = await get_leaderboard(guild.id, limit=10)
        if not rows:
            await message.reply("لا توجد بيانات بعد. ابدأ بالتحدث لكسب XP!", mention_author=False)
            return True
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for i, row in enumerate(rows, 1):
            m = guild.get_member(row["user_id"])
            name = m.display_name if m else "Unknown"
            medal = medals.get(i, f"`#{i}`")
            lines.append(f"{medal} **{name}** — Level {row['level']} • {row['xp']:,} XP")
        embed = discord.Embed(
            title=f"🏆 {guild.name} Leaderboard",
            description="\n".join(lines),
            color=0xFFD700,
        )
        await message.reply(embed=embed, mention_author=False)
        return True

    elif action == "show_premium":
        info = await get_premium_info(guild.id)
        plan = info["plan"]
        used = info["tokens_used_today"]
        limit = plan["daily_tokens"]

        if limit < 999999:
            progress = min(used / limit, 1.0)
            bar = "█" * int(progress * 20) + "░" * (20 - int(progress * 20))
            usage = f"`{bar}` {used:,} / {limit:,}"
        else:
            usage = f"{used:,} / ∞"

        embed = discord.Embed(
            title=f"{plan['emoji']} {plan['name']} Plan",
            color=plan["color"],
        )
        embed.add_field(name="التوكنز اليوم", value=usage, inline=False)
        embed.add_field(name="AI Model", value=plan["ai_model"], inline=True)
        embed.add_field(name="XP Boost", value=f"x{plan['xp_boost']}", inline=True)

        if info["tier"] == "free":
            embed.add_field(
                name="⬆️ ترقية",
                value=f"[اشترِ من الموقع]({WEBSITE_URL})",
                inline=False,
            )
        await message.reply(embed=embed, mention_author=False)
        return True

    elif action == "show_plans":
        embed = discord.Embed(
            title="💎 الخطط المتاحة",
            description=f"[🛒 اشترِ الآن]({WEBSITE_URL})",
            color=0x5865F2,
        )
        for tier, plan in PLANS.items():
            tokens = str(plan["daily_tokens"]) if plan["daily_tokens"] < 999999 else "∞"
            embed.add_field(
                name=f"{plan['emoji']} {plan['name']} — {plan['price']}",
                value=f"📊 {tokens} token/يوم | 🤖 {plan['ai_model']} | ⭐ x{plan['xp_boost']} XP",
                inline=False,
            )
        await message.reply(embed=embed, mention_author=False)
        return True

    elif action == "show_serverinfo":
        embed = discord.Embed(title=guild.name, color=0x5865F2)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="الأعضاء", value=guild.member_count, inline=True)
        embed.add_field(name="القنوات", value=len(guild.channels), inline=True)
        embed.add_field(name="الرتب", value=len(guild.roles), inline=True)
        embed.add_field(name="المالك", value=guild.owner.mention if guild.owner else "N/A", inline=True)
        await message.reply(embed=embed, mention_author=False)
        return True

    elif action == "show_userinfo":
        check_user = target or author
        embed = discord.Embed(title=str(check_user), color=check_user.color)
        embed.set_thumbnail(url=check_user.display_avatar.url)
        embed.add_field(name="ID", value=check_user.id, inline=True)
        embed.add_field(name="انضم", value=check_user.joined_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="أُنشئ", value=check_user.created_at.strftime("%Y-%m-%d"), inline=True)
        roles = [r.mention for r in check_user.roles[1:]]
        embed.add_field(name=f"الرتب ({len(roles)})", value=" ".join(roles[:8]) or "None", inline=False)
        await message.reply(embed=embed, mention_author=False)
        return True

    elif action == "how_to_ticket":
        from src.services.premium import WEBSITE_URL
        embed = discord.Embed(
            title="🎫 كيف تفتح تذكرة دعم؟",
            color=0x5865F2,
        )
        embed.add_field(
            name="الطريقة 1 — زر في القناة",
            value="اذهب لقناة `#open-ticket` واضغط زر **Open Ticket** 🎫",
            inline=False,
        )
        embed.add_field(
            name="الطريقة 2 — أمر مباشر",
            value="اكتب `/ticket` أو `!ticket` في أي قناة",
            inline=False,
        )
        after_text = "AI replies automatically. Press Call Staff for staff, Close Ticket to close."
        embed.add_field(name="After Opening", value=after_text, inline=False)
        await message.reply(embed=embed, mention_author=False)
        return True

    return False


def _mod_embed(title: str, member: discord.Member, reason: str, color: int) -> discord.Embed:
    embed = discord.Embed(title=title, color=color)
    embed.add_field(name="المستخدم", value=f"{member.mention} (`{member.id}`)", inline=True)
    embed.add_field(name="السبب", value=reason, inline=True)
    embed.set_footer(text="github.com/safouane02")
    return embed
