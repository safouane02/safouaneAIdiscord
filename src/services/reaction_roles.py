# safouane02.github

import json
import aiosqlite
from src.services.database import DB_PATH_STR


async def init_reaction_roles_table():
    async with aiosqlite.connect(DB_PATH_STR) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reaction_roles (
                guild_id    INTEGER NOT NULL,
                message_id  INTEGER NOT NULL,
                emoji       TEXT NOT NULL,
                role_id     INTEGER NOT NULL,
                PRIMARY KEY (guild_id, message_id, emoji)
            )
        """)
        await db.commit()


async def add_reaction_role(guild_id: int, message_id: int, emoji: str, role_id: int):
    async with aiosqlite.connect(DB_PATH_STR) as db:
        await db.execute(
            "INSERT OR REPLACE INTO reaction_roles VALUES (?, ?, ?, ?)",
            (guild_id, message_id, emoji, role_id),
        )
        await db.commit()


async def remove_reaction_role(guild_id: int, message_id: int, emoji: str):
    async with aiosqlite.connect(DB_PATH_STR) as db:
        await db.execute(
            "DELETE FROM reaction_roles WHERE guild_id=? AND message_id=? AND emoji=?",
            (guild_id, message_id, emoji),
        )
        await db.commit()


async def get_role_for_reaction(guild_id: int, message_id: int, emoji: str) -> int | None:
    async with aiosqlite.connect(DB_PATH_STR) as db:
        async with db.execute(
            "SELECT role_id FROM reaction_roles WHERE guild_id=? AND message_id=? AND emoji=?",
            (guild_id, message_id, emoji),
        ) as cur:
            row = await cur.fetchone()
    return row[0] if row else None


async def get_all_reaction_roles(guild_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH_STR) as db:
        async with db.execute(
            "SELECT message_id, emoji, role_id FROM reaction_roles WHERE guild_id=? ORDER BY message_id",
            (guild_id,),
        ) as cur:
            rows = await cur.fetchall()
    return [{"message_id": r[0], "emoji": r[1], "role_id": r[2]} for r in rows]
