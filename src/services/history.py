# safouane02.github

from collections import defaultdict
from src.config import config as _config, PERSONALITIES

_store: dict[int, list[dict]] = defaultdict(list)

_personalities: dict[int, str] = {}


def get_history(user_id: int) -> list[dict]:
    return _store[user_id].copy()


def add_message(user_id: int, role: str, content: str):
    _store[user_id].append({"role": role, "content": content})

    if len(_store[user_id]) > _config.max_history * 2:
        _store[user_id] = _store[user_id][2:]


def clear_history(user_id: int):
    _store.pop(user_id, None)


def get_personality(user_id: int) -> str:
    name = _personalities.get(user_id, "default")
    return PERSONALITIES[name]


def set_personality(user_id: int, name: str) -> bool:
    if name not in PERSONALITIES:
        return False
    _personalities[user_id] = name
    clear_history(user_id)
    return True


def get_personality_name(user_id: int) -> str:
    return _personalities.get(user_id, "default")
