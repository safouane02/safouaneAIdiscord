import discord
from src.services.level_service import get_user, get_rank


async def build_server_context(message: discord.Message) -> str:
    """Build dynamic context about the current server and user for the AI."""
    guild = message.guild
    author = message.author

    if not guild:
        return ""

    # user level data
    try:
        level_data = await get_user(guild.id, author.id)
        rank = await get_rank(guild.id, author.id)
        level_info = (
            f"- Level: {level_data['level']} | "
            f"XP: {level_data['xp']:,} | "
            f"Rank: #{rank} | "
            f"Messages: {level_data['messages']:,}"
        )
    except Exception:
        level_info = "- Level data not available"

    # user roles
    roles = [r.name for r in author.roles[1:]]
    is_admin = author.guild_permissions.administrator
    is_mod = author.guild_permissions.kick_members

    context = f"""
## Current Discord Context
### Server: {guild.name}
- Members: {guild.member_count:,}
- Channels: {len(guild.channels)}
- Roles: {len(guild.roles)}

### User: {author.display_name} ({author.name})
- ID: {author.id}
- Roles: {', '.join(roles) if roles else 'None'}
- Permissions: {'Administrator' if is_admin else 'Moderator' if is_mod else 'Member'}
{level_info}

### Current Channel: #{message.channel.name}
"""
    return context.strip()
