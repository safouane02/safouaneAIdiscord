# safouane02.github

import asyncio
import discord
from datetime import timedelta
from discord.ext import commands

from src.services.moderation import detect_moderation_intent, parse_duration, VALID_ACTIONS
from src.services.mod_logger import add_case, get_user_history, get_warnings
from src.services.snipe_store import get_deleted, get_edited, store_deleted, store_edited
from src.services.logger import get_logger

log = get_logger("mod_commands")

_pending: dict[int, dict] = {}


def mod_embed(title: str, member, reason: str, color: int, case_id: int = None) -> discord.Embed:
    embed = discord.Embed(title=title, color=color)
    if member:
        embed.add_field(name="User", value=f"{member.mention} (`{member.id}`)", inline=True)
    embed.add_field(name="Reason", value=reason or "No reason provided", inline=True)
    if case_id:
        embed.set_footer(text=f"Case #{case_id} • github.com/safouane02")
    else:
        embed.set_footer(text="github.com/safouane02")
    return embed


class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def process_ai_mod(self, message: discord.Message):
        intent = await detect_moderation_intent(message.content)

        if not intent.get("action") or intent["action"] not in VALID_ACTIONS:
            return

        action = intent["action"]
        reason = intent.get("reason") or "AI moderation"
        duration = intent.get("duration")

        target = None
        if intent.get("target_id"):
            try:
                target = message.guild.get_member(int(intent["target_id"]))
            except (ValueError, TypeError):
                pass

        if not target and action not in ("clear", "lock", "unlock", "nuke"):
            await message.reply("⚠️ Could not identify the target user.", mention_author=False)
            return

        duration_text = f" for **{duration}**" if duration else ""
        target_text = target.mention if target else "this channel"

        confirm = await message.reply(
            f"⚡ AI detected intent: **{action}** on {target_text}{duration_text}\n"
            f"Reason: *{reason}*\n\n"
            f"Reply **yes** to confirm or **no** to cancel.",
            mention_author=False,
        )

        _pending[confirm.id] = {
            "action": action,
            "target": target,
            "reason": reason,
            "duration": duration,
            "channel": message.channel,
            "guild": message.guild,
            "requester": message.author,
        }

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if not message.reference:
            return

        ref_id = message.reference.message_id
        if ref_id not in _pending:
            return

        pending = _pending.pop(ref_id)

        if message.author != pending["requester"]:
            _pending[ref_id] = pending
            return

        if message.content.lower().strip() in ("yes", "y", "نعم", "أيوه"):
            await _execute_mod_action(message, pending)
        else:
            await message.reply("❌ Action cancelled.", mention_author=False)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        await member.ban(reason=reason)
        case_id = add_case(ctx.guild.id, member.id, ctx.author.id, "ban", reason)
        await ctx.send(embed=mod_embed("🔨 Banned", member, reason, 0xED4245, case_id))

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason: str = "No reason provided"):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            case_id = add_case(ctx.guild.id, user_id, ctx.author.id, "unban", reason)
            await ctx.send(embed=mod_embed("✅ Unbanned", user, reason, 0x57F287, case_id))
        except discord.NotFound:
            await ctx.send("⚠️ User not found or not banned.")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        await member.kick(reason=reason)
        case_id = add_case(ctx.guild.id, member.id, ctx.author.id, "kick", reason)
        await ctx.send(embed=mod_embed("👢 Kicked", member, reason, 0xFEE75C, case_id))

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def softban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        await member.ban(reason=f"[Softban] {reason}", delete_message_days=7)
        await ctx.guild.unban(member, reason="Softban — unban after message deletion")
        case_id = add_case(ctx.guild.id, member.id, ctx.author.id, "softban", reason)
        await ctx.send(embed=mod_embed("🧹 Softbanned", member, reason, 0xFF7043, case_id))

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def massban(self, ctx, *members: discord.Member):
        if not members:
            await ctx.send("Usage: `!massban @user1 @user2 ...`")
            return
        banned = []
        for member in members:
            try:
                await member.ban(reason=f"Massban by {ctx.author}")
                add_case(ctx.guild.id, member.id, ctx.author.id, "ban", "Massban")
                banned.append(str(member))
            except Exception:
                pass
        await ctx.send(f"🔨 Massbanned **{len(banned)}** users: {', '.join(banned)}")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: str = "10m", *, reason: str = "No reason provided"):
        seconds = parse_duration(duration)
        if seconds <= 0:
            await ctx.send("⚠️ Invalid duration. Use formats like `10m`, `1h`, `1d`.")
            return
        until = discord.utils.utcnow() + timedelta(seconds=seconds)
        await member.timeout(until, reason=reason)
        case_id = add_case(ctx.guild.id, member.id, ctx.author.id, "timeout", reason)
        await ctx.send(embed=mod_embed(f"⏱️ Timed Out ({duration})", member, reason, 0x5865F2, case_id))

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member):
        await member.timeout(None)
        add_case(ctx.guild.id, member.id, ctx.author.id, "untimeout", "Manual untimeout")
        await ctx.send(f"✅ Removed timeout from {member.mention}")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        case_id = add_case(ctx.guild.id, member.id, ctx.author.id, "warn", reason)
        warns = get_warnings(ctx.guild.id, member.id)
        await ctx.send(embed=mod_embed(f"⚠️ Warning (#{len(warns)} total)", member, reason, 0xFFA500, case_id))
        try:
            await member.send(f"⚠️ You were warned in **{ctx.guild.name}**\nReason: {reason}")
        except discord.Forbidden:
            pass

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, member: discord.Member):
        warns = get_warnings(ctx.guild.id, member.id)
        if not warns:
            await ctx.send(f"✅ {member.mention} has no warnings.")
            return
        lines = [f"**#{w['id']}** — {w['reason']} *(by <@{w['moderator_id']}>)*" for w in warns]
        embed = discord.Embed(title=f"⚠️ Warnings for {member}", description="\n".join(lines), color=0xFFA500)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def history(self, ctx, member: discord.Member):
        cases = get_user_history(ctx.guild.id, member.id)
        if not cases:
            await ctx.send(f"✅ No moderation history for {member.mention}.")
            return
        lines = [f"**#{c['id']}** `{c['action']}` — {c['reason']} *(by <@{c['moderator_id']}>)*" for c in cases[-10:]]
        embed = discord.Embed(title=f"📋 History for {member}", description="\n".join(lines), color=0x5865F2)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 10):
        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=amount)
        msg = await ctx.send(f"🗑️ Deleted **{len(deleted)}** messages.")
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def nuke(self, ctx):
        confirm = await ctx.send(
            f"⚠️ Are you sure you want to nuke **#{ctx.channel.name}**? Reply **yes** to confirm."
        )
        _pending[confirm.id] = {
            "action": "nuke",
            "channel": ctx.channel,
            "guild": ctx.guild,
            "requester": ctx.author,
            "target": None,
            "reason": "Nuke",
            "duration": None,
        }

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Channel locked.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
        await ctx.send("🔓 Channel unlocked.")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            role = await ctx.guild.create_role(name="Muted")
            for ch in ctx.guild.channels:
                await ch.set_permissions(role, send_messages=False, speak=False)
        await member.add_roles(role, reason=reason)
        case_id = add_case(ctx.guild.id, member.id, ctx.author.id, "mute", reason)
        await ctx.send(embed=mod_embed("🔇 Muted", member, reason, 0x5865F2, case_id))

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if role and role in member.roles:
            await member.remove_roles(role)
            await ctx.send(f"🔊 {member.mention} unmuted.")
        else:
            await ctx.send(f"⚠️ {member.mention} is not muted.")

    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx, member: discord.Member, *, nickname: str):
        await member.edit(nick=nickname)
        await ctx.send(f"✏️ Changed {member.mention}'s nickname to **{nickname}**")

    @commands.command()
    @commands.has_permissions(move_members=True)
    async def move(self, ctx, member: discord.Member, channel: discord.VoiceChannel):
        await member.move_to(channel)
        await ctx.send(f"➡️ Moved {member.mention} to **{channel.name}**")

    @commands.command()
    @commands.has_permissions(move_members=True)
    async def disconnect(self, ctx, member: discord.Member):
        await member.move_to(None)
        await ctx.send(f"🔌 Disconnected {member.mention} from voice.")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def role_add(self, ctx, member: discord.Member, role: discord.Role):
        await member.add_roles(role)
        await ctx.send(f"✅ Added **{role.name}** to {member.mention}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def role_remove(self, ctx, member: discord.Member, role: discord.Role):
        await member.remove_roles(role)
        await ctx.send(f"✅ Removed **{role.name}** from {member.mention}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def announce(self, ctx, channel: discord.TextChannel, *, message: str):
        embed = discord.Embed(description=message, color=0x5865F2)
        embed.set_footer(text=f"Announced by {ctx.author}")
        await channel.send(embed=embed)
        await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, *, message: str):
        await ctx.message.delete()
        await ctx.send(message)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def snipe(self, ctx):
        data = get_deleted(ctx.channel.id)
        if not data:
            await ctx.send("Nothing to snipe.")
            return
        embed = discord.Embed(description=data["content"], color=0xED4245)
        embed.set_author(name=data["author"], icon_url=data["avatar"])
        embed.set_footer(text="Deleted message")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def editsnipe(self, ctx):
        data = get_edited(ctx.channel.id)
        if not data:
            await ctx.send("Nothing to snipe.")
            return
        embed = discord.Embed(color=0xFEE75C)
        embed.set_author(name=data["author"], icon_url=data["avatar"])
        embed.add_field(name="Before", value=data["before"], inline=False)
        embed.add_field(name="After", value=data["after"], inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def embed_cmd(self, ctx, title: str, color: str = "5865F2", *, description: str):
        try:
            color_int = int(color.strip("#"), 16)
        except ValueError:
            color_int = 0x5865F2
        embed = discord.Embed(title=title, description=description, color=color_int)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_emojis=True)
    async def steal_emoji(self, ctx, emoji: discord.PartialEmoji, name: str = None):
        emoji_bytes = await emoji.read()
        new_emoji = await ctx.guild.create_custom_emoji(name=name or emoji.name, image=emoji_bytes)
        await ctx.send(f"✅ Added emoji {new_emoji} as `:{new_emoji.name}:`")


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def serverinfo(self, ctx):
        g = ctx.guild
        embed = discord.Embed(title=g.name, color=0x5865F2)
        embed.set_thumbnail(url=g.icon.url if g.icon else None)
        embed.add_field(name="Members", value=g.member_count, inline=True)
        embed.add_field(name="Channels", value=len(g.channels), inline=True)
        embed.add_field(name="Roles", value=len(g.roles), inline=True)
        embed.add_field(name="Owner", value=g.owner.mention if g.owner else "N/A", inline=True)
        embed.add_field(name="Created", value=g.created_at.strftime("%Y-%m-%d"), inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=str(member), color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        roles = [r.mention for r in member.roles[1:]]
        embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles) or "None", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def whois(self, ctx, member: discord.Member = None):
        await self.userinfo(ctx, member)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"{member}'s Avatar", color=0x5865F2)
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def banner(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = await self.bot.fetch_user(member.id)
        if not user.banner:
            await ctx.send(f"⚠️ {member.mention} has no banner.")
            return
        embed = discord.Embed(title=f"{member}'s Banner", color=0x5865F2)
        embed.set_image(url=user.banner.url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def servericon(self, ctx):
        if not ctx.guild.icon:
            await ctx.send("⚠️ This server has no icon.")
            return
        embed = discord.Embed(title=f"{ctx.guild.name}'s Icon", color=0x5865F2)
        embed.set_image(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def membercount(self, ctx):
        g = ctx.guild
        bots = sum(1 for m in g.members if m.bot)
        humans = g.member_count - bots
        embed = discord.Embed(title=f"👥 {g.name}", color=0x57F287)
        embed.add_field(name="Total", value=g.member_count, inline=True)
        embed.add_field(name="Humans", value=humans, inline=True)
        embed.add_field(name="Bots", value=bots, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def channelinfo(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        embed = discord.Embed(title=f"#{channel.name}", color=0x5865F2)
        embed.add_field(name="ID", value=channel.id, inline=True)
        embed.add_field(name="Category", value=channel.category or "None", inline=True)
        embed.add_field(name="Created", value=channel.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Topic", value=channel.topic or "None", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def invite(self, ctx):
        link = await ctx.channel.create_invite(max_age=3600)
        await ctx.send(f"🔗 Invite link (expires in 1h): {link}")


    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.author.bot and message.content:
            store_deleted(message.channel.id, message)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.author.bot and before.content != after.content:
            store_edited(before.channel.id, before, after)


    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("⛔ You don't have permission to use this.", mention_author=False)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.reply("⚠️ Member not found.", mention_author=False)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(f"⚠️ Missing: `{error.param.name}`", mention_author=False)
        elif isinstance(error, discord.Forbidden):
            await ctx.reply("⛔ I don't have permission to do that.", mention_author=False)
        else:
            log.error(f"Mod error in {ctx.command}: {error}")


async def _execute_mod_action(message: discord.Message, pending: dict):
    action = pending["action"]
    target: discord.Member = pending.get("target")
    reason = pending["reason"]
    duration = pending.get("duration")
    guild = pending["guild"]

    try:
        if action == "nuke":
            channel = pending["channel"]
            new_channel = await channel.clone(reason="Nuked")
            await new_channel.send("💥 Channel has been nuked.")
            await channel.delete()
            return

        if action == "ban" and target:
            await target.ban(reason=reason)
            case_id = add_case(guild.id, target.id, pending["requester"].id, "ban", reason)
            await message.reply(embed=mod_embed("🔨 Banned", target, reason, 0xED4245, case_id), mention_author=False)

        elif action == "kick" and target:
            await target.kick(reason=reason)
            case_id = add_case(guild.id, target.id, pending["requester"].id, "kick", reason)
            await message.reply(embed=mod_embed("👢 Kicked", target, reason, 0xFEE75C, case_id), mention_author=False)

        elif action == "softban" and target:
            await target.ban(reason=f"[Softban] {reason}", delete_message_days=7)
            await guild.unban(target)
            case_id = add_case(guild.id, target.id, pending["requester"].id, "softban", reason)
            await message.reply(embed=mod_embed("🧹 Softbanned", target, reason, 0xFF7043, case_id), mention_author=False)

        elif action == "timeout" and target:
            seconds = parse_duration(duration or "10m")
            until = discord.utils.utcnow() + timedelta(seconds=seconds)
            await target.timeout(until, reason=reason)
            case_id = add_case(guild.id, target.id, pending["requester"].id, "timeout", reason)
            await message.reply(embed=mod_embed(f"⏱️ Timed Out ({duration or '10m'})", target, reason, 0x5865F2, case_id), mention_author=False)

        elif action == "warn" and target:
            case_id = add_case(guild.id, target.id, pending["requester"].id, "warn", reason)
            await message.reply(embed=mod_embed("⚠️ Warning", target, reason, 0xFFA500, case_id), mention_author=False)
            try:
                await target.send(f"⚠️ You were warned in **{guild.name}**\nReason: {reason}")
            except discord.Forbidden:
                pass

        elif action == "mute" and target:
            role = discord.utils.get(guild.roles, name="Muted")
            if not role:
                role = await guild.create_role(name="Muted")
                for ch in guild.channels:
                    await ch.set_permissions(role, send_messages=False, speak=False)
            await target.add_roles(role, reason=reason)
            case_id = add_case(guild.id, target.id, pending["requester"].id, "mute", reason)
            await message.reply(embed=mod_embed("🔇 Muted", target, reason, 0x5865F2, case_id), mention_author=False)

        elif action == "lock":
            await pending["channel"].set_permissions(guild.default_role, send_messages=False)
            await message.reply("🔒 Channel locked.", mention_author=False)

        elif action == "unlock":
            await pending["channel"].set_permissions(guild.default_role, send_messages=None)
            await message.reply("🔓 Channel unlocked.", mention_author=False)

        elif action == "clear":
            amount = pending.get("amount") or 10
            await pending["channel"].purge(limit=int(amount))
            await message.reply(f"🗑️ Cleared {amount} messages.", mention_author=False)

        else:
            await message.reply("⚠️ Couldn't execute that action.", mention_author=False)

    except discord.Forbidden:
        await message.reply("⛔ I don't have permission to do that.", mention_author=False)
    except Exception as e:
        log.error(f"AI mod execution error: {e}")
        await message.reply("⚠️ Something went wrong.", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
