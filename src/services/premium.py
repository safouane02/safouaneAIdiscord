import os
import aiosqlite
from datetime import datetime, timedelta
from src.services.database import DB_PATH_STR

WEBSITE_URL = os.getenv("WEBSITE_URL", "https://yourwebsite.com/premium")

PLANS = {
    "free": {
        "name": "Free",
        "emoji": "🆓",
        "color": 0x99aab5,
        "daily_tokens": 500,
        "ai_model": "fast",
        "xp_boost": 1.0,
        "max_level_roles": 3,
        "custom_welcome": False,
        "ticket_ai": True,
        "automod": False,
        "reaction_roles": 3,
        "price": "مجاني",
    },
    "basic": {
        "name": "Basic",
        "emoji": "⭐",
        "color": 0xFFD700,
        "daily_tokens": 2000,
        "ai_model": "balanced",
        "xp_boost": 1.5,
        "max_level_roles": 10,
        "custom_welcome": True,
        "ticket_ai": True,
        "automod": True,
        "reaction_roles": 15,
        "price": "4.99$/شهر",
    },
    "pro": {
        "name": "Pro",
        "emoji": "💎",
        "color": 0x00b0f4,
        "daily_tokens": 8000,
        "ai_model": "smart",
        "xp_boost": 2.0,
        "max_level_roles": 25,
        "custom_welcome": True,
        "ticket_ai": True,
        "automod": True,
        "reaction_roles": 50,
        "price": "9.99$/شهر",
    },
    "elite": {
        "name": "Elite",
        "emoji": "👑",
        "color": 0xFF6B35,
        "daily_tokens": 999999,
        "ai_model": "heavy",
        "xp_boost": 3.0,
        "max_level_roles": 999,
        "custom_welcome": True,
        "ticket_ai": True,
        "automod": True,
        "reaction_roles": 999,
        "price": "19.99$/شهر",
    },
}


async def init_premium_table():
    async with aiosqlite.connect(DB_PATH_STR) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS premium (
                guild_id    INTEGER PRIMARY KEY,
                tier        TEXT    DEFAULT 'free',
                expires_at  TEXT    DEFAULT NULL,
                granted_by  INTEGER DEFAULT NULL
            );

            CREATE TABLE IF NOT EXISTS token_usage (
                guild_id    INTEGER NOT NULL,
                date        TEXT    NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, date)
            );
        """)
        await db.commit()


async def get_tier(guild_id: int) -> str:
    async with aiosqlite.connect(DB_PATH_STR) as db:
        async with db.execute(
            "SELECT tier, expires_at FROM premium WHERE guild_id=?",
            (guild_id,),
        ) as cur:
            row = await cur.fetchone()

    if not row:
        return "free"

    tier, expires_at = row
    if expires_at:
        if datetime.utcnow() > datetime.fromisoformat(expires_at):
            await set_tier(guild_id, "free")
            return "free"

    return tier


async def get_plan(guild_id: int) -> dict:
    tier = await get_tier(guild_id)
    return PLANS[tier]


async def set_tier(guild_id: int, tier: str, days: int = None, granted_by: int = None):
    expires_at = None
    if days:
        expires_at = (datetime.utcnow() + timedelta(days=days)).isoformat()

    async with aiosqlite.connect(DB_PATH_STR) as db:
        await db.execute(
            """
            INSERT INTO premium (guild_id, tier, expires_at, granted_by)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET tier=?, expires_at=?, granted_by=?
            """,
            (guild_id, tier, expires_at, granted_by,
             tier, expires_at, granted_by),
        )
        await db.commit()


async def get_token_usage(guild_id: int) -> int:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH_STR) as db:
        async with db.execute(
            "SELECT tokens_used FROM token_usage WHERE guild_id=? AND date=?",
            (guild_id, today),
        ) as cur:
            row = await cur.fetchone()
    return row[0] if row else 0


async def add_token_usage(guild_id: int, tokens: int):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH_STR) as db:
        await db.execute(
            """
            INSERT INTO token_usage (guild_id, date, tokens_used)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, date) DO UPDATE SET tokens_used = tokens_used + ?
            """,
            (guild_id, today, tokens, tokens),
        )
        await db.commit()


async def check_token_limit(guild_id: int) -> tuple[bool, int, int]:
    """Returns (can_use, used, limit)"""
    plan = await get_plan(guild_id)
    daily_limit = plan["daily_tokens"]
    used = await get_token_usage(guild_id)
    return used < daily_limit, used, daily_limit


async def get_premium_info(guild_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH_STR) as db:
        async with db.execute(
            "SELECT tier, expires_at FROM premium WHERE guild_id=?",
            (guild_id,),
        ) as cur:
            row = await cur.fetchone()

    tier = row[0] if row else "free"
    expires_at = row[1] if row else None
    used = await get_token_usage(guild_id)

    return {
        "tier": tier,
        "plan": PLANS.get(tier, PLANS["free"]),
        "expires_at": expires_at,
        "tokens_used_today": used,
    }