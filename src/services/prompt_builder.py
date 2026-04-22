# safouane02.github

from src.config import OWNER_INFO, BOT_COMMANDS_INFO

_SECTIONS = {
    "moderation": """
- !ban @user [reason]
- !unban <id> [reason]
- !kick @user [reason]
- !softban @user [reason]
- !massban @u1 @u2 ...
- !timeout @user <duration> [reason] — 10m, 1h, 1d
- !untimeout @user
- !mute / !unmute @user
- !warn @user [reason]
- !warnings @user
- !history @user
""",
    "management": """
- !clear <amount>
- !nuke
- !lock / !unlock
- !nick @user <name>
- !move @user #voice
- !disconnect @user
- !role_add / !role_remove @user @role
- !announce #channel <msg>
- !say <msg>
- !snipe / !editsnipe
""",
    "levels": """
- !rank [@user]
- !leaderboard
- !setlevelrole <level> @role
- !removelevelrole <level>
- !levelroles
- !levelsettings
- !setlevelupchannel [#ch]
- !setlevelupmsg <msg> — {user} {level} {old_level}
- !setxpboost <multiplier>
- !setxp @user <amount>
- !resetxp @user
""",
    "tickets": """
- !ticketsetup — setup the ticket system
- !ticketpanel — edit panel message
- !ticketmessage — edit ticket welcome message
- !ticket — open a ticket
- !close — close ticket
- !claim — claim ticket (staff)
- !tadd @user — add to ticket
- !transcript — download transcript
- !ticketstats
""",
    "ai": """
- !ask <question>
- !mode <default|sarcastic|teacher|developer>
- !clear_chat
- Reply to bot messages to continue conversation
- @Bot + @user mention → AI moderation
""",
    "info": """
- !serverinfo, !userinfo [@user], !whois [@user]
- !avatar [@user], !banner [@user]
- !servericon, !membercount, !channelinfo
- !invite
- !ping, !info
""",
    "broadcast": """
- !dm all <msg>
- !dm humans <msg>
- !dm @role <msg>
""",
}

_KEYWORDS = {
    "moderation": ["ban", "kick", "mute", "warn", "timeout", "طرد", "حظر", "كتم", "تحذير"],
    "management": ["clear", "nuke", "lock", "unlock", "nick", "move", "role", "announce", "قناة", "رتبة"],
    "levels": ["rank", "level", "xp", "leaderboard", "فل", "رتبة", "نقاط", "مستوى"],
    "tickets": ["ticket", "تكت", "support", "دعم", "close", "claim", "transcript"],
    "ai": ["personality", "mode", "chat", "شخصية", "محادثة", "ask"],
    "info": ["server", "user", "avatar", "banner", "info", "سيرفر", "معلومات"],
    "broadcast": ["dm", "broadcast", "message all", "رسالة", "جماعي"],
}

_BASE_PROMPT = (
    "You are a smart Discord bot assistant running inside a Discord server.\n"
    "You were built by Safouane Baadoud (صفوان باعود) from Algeria — github.com/safouane02\n"
    "Never mention Groq, Llama, or any AI model name — you are just 'the bot'.\n"
    "Respond in the same language the user uses.\n"
    "If someone asks you to perform an action, tell them the exact command to use.\n\n"
)


def build_prompt(user_message: str, personality_prompt: str = None) -> str:
    """
    Build a minimal but relevant system prompt based on what the user is asking about.
    Avoids sending ALL commands every time — only relevant sections.
    """
    msg = user_message.lower()

    relevant_sections = []
    for topic, keywords in _KEYWORDS.items():
        if any(k in msg for k in keywords):
            relevant_sections.append(_SECTIONS[topic])

    needs_owner = any(k in msg for k in [
        "who made", "who built", "developer", "creator", "من صنع", "من بناك", "صفوان"
    ])

    if not relevant_sections:
        prompt = _BASE_PROMPT
        if needs_owner:
            prompt += OWNER_INFO
        return prompt.strip()

    sections_text = "\n".join(relevant_sections)
    prompt = f"{_BASE_PROMPT}{sections_text}"

    if needs_owner:
        prompt += f"\n{OWNER_INFO}"

    return prompt.strip()
