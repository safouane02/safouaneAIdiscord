import json
from pathlib import Path
from src.services.logger import get_logger

log = get_logger("whitelist")

_WHITELIST_FILE = Path("data/whitelist.json")
_WHITELIST_FILE.parent.mkdir(exist_ok=True)


def _load() -> set[int]:
    if not _WHITELIST_FILE.exists():
        return set()
    try:
        data = json.loads(_WHITELIST_FILE.read_text())
        return set(data)
    except Exception:
        return set()


def _save(users: set[int]):
    _WHITELIST_FILE.write_text(json.dumps(list(users)))


def is_allowed(user_id: int, owner_id: int) -> bool:
    if user_id == owner_id:
        return True
    return user_id in _load()


def add_user(user_id: int) -> bool:
    users = _load()
    if user_id in users:
        return False
    users.add(user_id)
    _save(users)
    log.info(f"Added user {user_id} to DM whitelist")
    return True


def remove_user(user_id: int) -> bool:
    users = _load()
    if user_id not in users:
        return False
    users.discard(user_id)
    _save(users)
    log.info(f"Removed user {user_id} from DM whitelist")
    return True


def list_users() -> list[int]:
    return list(_load())
