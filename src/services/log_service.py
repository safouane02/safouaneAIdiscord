import discord
import aiosqlite
from datetime import datetime
from src.services.database import DB_PATH_STR


async def get_log_channel(guild_id: int) -> int | None:
    async with aiosqlite.connect(DB_PATH_STR) as db:
        async with db.execute(
            "SELECT log_channel_id FROM guild_settings WHERE guild_id=?",
            (guild_id,),
        ) as cur:
            row = await cur.fetchone()
    return row[0] if row and row[0] else None


async def set_log_channel(guild_id: int, channel_id: int):
    async with aiosqlite.connect(DB_PATH_STR) as db:
        await db.execute(
            """
            INSERT INTO guild_settings (guild_id, log_channel_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET log_channel_id=?
            """,
            (guild_id, channel_id, channel_id),
        )
        await db.commit()


async def send_log(guild: discord.Guild, bot: discord.Client, embed: discord.Embed):
    channel_id = await get_log_channel(guild.id)
    if not channel_id:
        return
    channel = guild.get_channel(channel_id)
    if channel:
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass


def mod_log_embed(action: str, target: discord.Member, moderator: discord.Member,
                  reason: str, color: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"🔨 {action}",
        color=color,
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="User", value=f"{target.mention} (`{target.id}`)", inline=True)
    embed.add_field(name="Moderator", value=moderator.mention, inline=True)
    embed.add_field(name="Reason", value=reason or "No reason", inline=False)
    embed.set_footer(text=f"User ID: {target.id}")
    return embed


def automod_log_embed(reason: str, member: discord.Member,
                      content: str, action: str) -> discord.Embed:
    embed = discord.Embed(
        title=f"🛡️ AutoMod — {reason}",
        color=0xFF6B35,
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="User", value=f"{member.mention} (`{member.id}`)", inline=True)
    embed.add_field(name="Action", value=action, inline=True)
    embed.add_field(name="Message", value=f"```{content[:200]}```", inline=False)
    embed.set_footer(text=f"Channel: #{member.guild.name}")
    return embed


def join_log_embed(member: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title="👋 Member Joined",
        description=f"{member.mention} joined the server",
        color=0x57F287,
        timestamp=datetime.utcnow(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Member Count", value=str(member.guild.member_count), inline=True)
    embed.set_footer(text=f"ID: {member.id}")
    return embed


def leave_log_embed(member: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title="👋 Member Left",
        description=f"**{member}** left the server",
        color=0xED4245,
        timestamp=datetime.utcnow(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"ID: {member.id}")
    return embed


def message_delete_embed(message: discord.Message) -> discord.Embed:
    embed = discord.Embed(
        title="🗑️ Message Deleted",
        color=0xFEE75C,
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="Author", value=message.author.mention, inline=True)
    embed.add_field(name="Channel", value=message.channel.mention, inline=True)
    embed.add_field(name="Content", value=f"```{message.content[:300] or 'No text'}```", inline=False)
    embed.set_footer(text=f"User ID: {message.author.id}")
    return embed


def message_edit_embed(before: discord.Message, after: discord.Message) -> discord.Embed:
    embed = discord.Embed(
        title="✏️ Message Edited",
        color=0x5865F2,
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="Author", value=before.author.mention, inline=True)
    embed.add_field(name="Channel", value=before.channel.mention, inline=True)
    embed.add_field(name="Before", value=f"```{before.content[:200] or 'Empty'}```", inline=False)
    embed.add_field(name="After", value=f"```{after.content[:200] or 'Empty'}```", inline=False)
    embed.set_footer(text=f"User ID: {before.author.id}")
    return embed
