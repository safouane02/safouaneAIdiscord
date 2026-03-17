import math
import random
import time
import aiosqlite
from src.services.database import DB_PATH_STR

_cooldowns: dict[tuple, float] = {}


def xp_for_level(level: int) -> int:
    return math.floor(100 * (level ** 1.5))


def level_from_xp(xp: int) -> int:
    level = 0
    while xp >= xp_for_level(level + 1):
        xp -= xp_for_level(level + 1)
        level += 1
    return level


async def get_user(guild_id: int, user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH_STR) as db:
        async with db.execute(
            "SELECT xp, level, messages FROM levels WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        ) as cur:
            row = await cur.fetchone()
    if row:
        return {"xp": row[0], "level": row[1], "messages": row[2]}
    return {"xp": 0, "level": 0, "messages": 0}


async def get_settings(guild_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH_STR) as db:
        async with db.execute(
            "SELECT xp_per_msg, xp_cooldown, level_channel, xp_boost, level_up_msg FROM guild_settings WHERE guild_id=?",
            (guild_id,),
        ) as cur:
            row = await cur.fetchone()
    if row:
        return {
            "xp_per_msg": row[0],
            "xp_cooldown": row[1],
            "level_channel": row[2],
            "xp_boost": row[3] or 1.0,
            "level_up_msg": row[4],
        }
    return {"xp_per_msg": 15, "xp_cooldown": 60, "level_channel": None, "xp_boost": 1.0, "level_up_msg": None}


async def add_xp(guild_id: int, user_id: int) -> tuple[bool, int, int]:
    key = (guild_id, user_id)
    settings = await get_settings(guild_id)
    now = time.time()

    if now - _cooldowns.get(key, 0) < settings["xp_cooldown"]:
        return False, 0, 0

    _cooldowns[key] = now
    xp_gain = random.randint(
        max(1, settings["xp_per_msg"] - 5),
        settings["xp_per_msg"] + 5,
    )

    async with aiosqlite.connect(DB_PATH_STR) as db:
        await db.execute(
            """
            INSERT INTO levels (guild_id, user_id, xp, level, messages)
            VALUES (?, ?, ?, 0, 1)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                xp = xp + ?,
                messages = messages + 1
            """,
            (guild_id, user_id, xp_gain, xp_gain),
        )
        await db.commit()

        async with db.execute(
            "SELECT xp, level FROM levels WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        ) as cur:
            row = await cur.fetchone()
        current_xp, old_level = row

    new_level = level_from_xp(current_xp)

    if new_level > old_level:
        async with aiosqlite.connect(DB_PATH_STR) as db:
            await db.execute(
                "UPDATE levels SET level=? WHERE guild_id=? AND user_id=?",
                (new_level, guild_id, user_id),
            )
            await db.commit()
        return True, old_level, new_level

    return False, old_level, old_level


async def get_leaderboard(guild_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH_STR) as db:
        async with db.execute(
            "SELECT user_id, xp, level, messages FROM levels WHERE guild_id=? ORDER BY xp DESC LIMIT ?",
            (guild_id, limit),
        ) as cur:
            rows = await cur.fetchall()
    return [{"user_id": r[0], "xp": r[1], "level": r[2], "messages": r[3]} for r in rows]


async def get_rank(guild_id: int, user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH_STR) as db:
        async with db.execute(
            """
            SELECT COUNT(*) FROM levels
            WHERE guild_id=? AND xp > (
                SELECT COALESCE(xp, 0) FROM levels WHERE guild_id=? AND user_id=?
            )
            """,
            (guild_id, guild_id, user_id),
        ) as cur:
            row = await cur.fetchone()
    return (row[0] + 1) if row else 1


async def set_level_role(guild_id: int, level: int, role_id: int):
    async with aiosqlite.connect(DB_PATH_STR) as db:
        await db.execute(
            "INSERT OR REPLACE INTO level_roles (guild_id, level, role_id) VALUES (?, ?, ?)",
            (guild_id, level, role_id),
        )
        await db.commit()


async def remove_level_role(guild_id: int, level: int):
    async with aiosqlite.connect(DB_PATH_STR) as db:
        await db.execute(
            "DELETE FROM level_roles WHERE guild_id=? AND level=?",
            (guild_id, level),
        )
        await db.commit()


async def get_level_roles(guild_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH_STR) as db:
        async with db.execute(
            "SELECT level, role_id FROM level_roles WHERE guild_id=? ORDER BY level",
            (guild_id,),
        ) as cur:
            rows = await cur.fetchall()
    return [{"level": r[0], "role_id": r[1]} for r in rows]


async def get_role_for_level(guild_id: int, level: int) -> int | None:
    async with aiosqlite.connect(DB_PATH_STR) as db:
        async with db.execute(
            "SELECT role_id FROM level_roles WHERE guild_id=? AND level=?",
            (guild_id, level),
        ) as cur:
            row = await cur.fetchone()
    return row[0] if row else None


async def update_settings(guild_id: int, **kwargs):
    async with aiosqlite.connect(DB_PATH_STR) as db:
        await db.execute(
            """
            INSERT INTO guild_settings (guild_id, xp_per_msg, xp_cooldown, level_channel)
            VALUES (?, 15, 60, NULL)
            ON CONFLICT(guild_id) DO NOTHING
            """,
            (guild_id,),
        )
        for key, value in kwargs.items():
            await db.execute(
                f"UPDATE guild_settings SET {key}=? WHERE guild_id=?",
                (value, guild_id),
            )
        await db.commit()


async def set_user_xp(guild_id: int, user_id: int, xp: int):
    new_level = level_from_xp(xp)
    async with aiosqlite.connect(DB_PATH_STR) as db:
        await db.execute(
            """
            INSERT INTO levels (guild_id, user_id, xp, level, messages)
            VALUES (?, ?, ?, ?, 0)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET xp=?, level=?
            """,
            (guild_id, user_id, xp, new_level, xp, new_level),
        )
        await db.commit()


async def reset_user_xp(guild_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH_STR) as db:
        await db.execute(
            "DELETE FROM levels WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        await db.commit()