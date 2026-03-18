import re
import time
from collections import defaultdict
from src.services.database import DB_PATH_STR
import aiosqlite

# spam tracking: { (guild_id, user_id): [timestamps] }
_msg_timestamps: dict[tuple, list] = defaultdict(list)

# duplicate message tracking: { (guild_id, user_id): last_message }
_last_messages: dict[tuple, str] = {}

DEFAULT_BANNED_WORDS: list[str] = []

SPAM_THRESHOLD = 5       # messages
SPAM_WINDOW = 5          # seconds
DUPLICATE_THRESHOLD = 3  # same message count


async def get_automod_settings(guild_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH_STR) as db:
        async with db.execute(
            "SELECT enabled, banned_words, spam_enabled, invite_filter, caps_filter FROM automod_settings WHERE guild_id=?",
            (guild_id,),
        ) as cur:
            row = await cur.fetchone()
    if row:
        import json
        return {
            "enabled": bool(row[0]),
            "banned_words": json.loads(row[1]) if row[1] else [],
            "spam_enabled": bool(row[2]),
            "invite_filter": bool(row[3]),
            "caps_filter": bool(row[4]),
        }
    return {
        "enabled": False,
        "banned_words": [],
        "spam_enabled": True,
        "invite_filter": True,
        "caps_filter": True,
    }


async def save_automod_settings(guild_id: int, **kwargs):
    import json
    async with aiosqlite.connect(DB_PATH_STR) as db:
        await db.execute(
            """
            INSERT INTO automod_settings (guild_id, enabled, banned_words, spam_enabled, invite_filter, caps_filter)
            VALUES (?, 0, '[]', 1, 1, 1)
            ON CONFLICT(guild_id) DO NOTHING
            """,
            (guild_id,),
        )
        for key, value in kwargs.items():
            if key == "banned_words":
                value = json.dumps(value)
            await db.execute(
                f"UPDATE automod_settings SET {key}=? WHERE guild_id=?",
                (value, guild_id),
            )
        await db.commit()


def check_spam(guild_id: int, user_id: int) -> bool:
    key = (guild_id, user_id)
    now = time.time()
    timestamps = _msg_timestamps[key]

    timestamps = [t for t in timestamps if now - t < SPAM_WINDOW]
    timestamps.append(now)
    _msg_timestamps[key] = timestamps

    return len(timestamps) >= SPAM_THRESHOLD


def check_duplicate(guild_id: int, user_id: int, content: str) -> bool:
    key = (guild_id, user_id)
    last = _last_messages.get(key, "")
    _last_messages[key] = content
    return content.lower() == last.lower() and len(content) > 10


def check_banned_words(content: str, banned_words: list[str]) -> str | None:
    content_lower = content.lower()
    for word in banned_words:
        if word.lower() in content_lower:
            return word
    return None


def check_invite_link(content: str) -> bool:
    return bool(re.search(r"discord\.gg/\w+|discord\.com/invite/\w+", content, re.IGNORECASE))


def check_caps(content: str) -> bool:
    letters = [c for c in content if c.isalpha()]
    if len(letters) < 10:
        return False
    caps_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    return caps_ratio > 0.7
