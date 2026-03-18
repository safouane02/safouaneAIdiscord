import shutil
import asyncio
from pathlib import Path
from datetime import datetime
from src.services.logger import get_logger

log = get_logger("backup")

BACKUP_DIR = Path("data/backups")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
MAX_BACKUPS = 7  # keep last 7 days


def create_backup() -> Path:
    db_path = Path("data/bot.db")
    if not db_path.exists():
        return None

    timestamp = datetime.utcnow().strftime("%Y-%m-%d")
    backup_path = BACKUP_DIR / f"bot_{timestamp}.db"

    shutil.copy2(db_path, backup_path)

    # remove old backups beyond MAX_BACKUPS
    backups = sorted(BACKUP_DIR.glob("bot_*.db"))
    while len(backups) > MAX_BACKUPS:
        backups[0].unlink()
        backups = backups[1:]

    log.info(f"Backup created: {backup_path.name}")
    return backup_path


async def backup_loop():
    while True:
        await asyncio.sleep(86400)  # every 24 hours
        create_backup()
