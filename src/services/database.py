# safouane02.github

import aiosqlite
from pathlib import Path

DB_PATH = Path("data/bot.db")
DB_PATH.parent.mkdir(exist_ok=True)
DB_PATH_STR = str(DB_PATH)


async def init_db():
    async with aiosqlite.connect(DB_PATH_STR) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS levels (
                guild_id    INTEGER NOT NULL,
                user_id     INTEGER NOT NULL,
                xp          INTEGER DEFAULT 0,
                level       INTEGER DEFAULT 0,
                messages    INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS level_roles (
                guild_id    INTEGER NOT NULL,
                level       INTEGER NOT NULL,
                role_id     INTEGER NOT NULL,
                PRIMARY KEY (guild_id, level)
            );

            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id        INTEGER PRIMARY KEY,
                xp_per_msg      INTEGER DEFAULT 15,
                xp_cooldown     INTEGER DEFAULT 60,
                xp_boost        REAL    DEFAULT 1.0,
                level_channel   INTEGER DEFAULT NULL,
                level_up_msg    TEXT    DEFAULT NULL,
                log_channel_id  INTEGER DEFAULT NULL
            );

            CREATE TABLE IF NOT EXISTS automod_settings (
                guild_id        INTEGER PRIMARY KEY,
                enabled         INTEGER DEFAULT 0,
                banned_words    TEXT    DEFAULT '[]',
                spam_enabled    INTEGER DEFAULT 1,
                invite_filter   INTEGER DEFAULT 1,
                caps_filter     INTEGER DEFAULT 1
            );
        """)

        migrations = [
            "ALTER TABLE guild_settings ADD COLUMN xp_boost REAL DEFAULT 1.0",
            "ALTER TABLE guild_settings ADD COLUMN level_up_msg TEXT DEFAULT NULL",
            "ALTER TABLE guild_settings ADD COLUMN log_channel_id INTEGER DEFAULT NULL",
        ]
        for sql in migrations:
            try:
                await db.execute(sql)
            except Exception:
                pass

        await db.commit()
