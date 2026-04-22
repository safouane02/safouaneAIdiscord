# safouane02.github

import json
from pathlib import Path
from datetime import datetime
from src.services.logger import get_logger

log = get_logger("mod_logger")

_FILE = Path("data/mod_logs.json")
_FILE.parent.mkdir(exist_ok=True)


def _load() -> dict:
    if not _FILE.exists():
        return {}
    try:
        return json.loads(_FILE.read_text())
    except Exception:
        return {}


def _save(data: dict):
    _FILE.write_text(json.dumps(data, indent=2))


def add_case(guild_id: int, target_id: int, moderator_id: int, action: str, reason: str) -> int:
    data = _load()
    guild_key = str(guild_id)

    if guild_key not in data:
        data[guild_key] = {"cases": [], "next_id": 1}

    case_id = data[guild_key]["next_id"]
    data[guild_key]["cases"].append({
        "id": case_id,
        "action": action,
        "target_id": target_id,
        "moderator_id": moderator_id,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
    })
    data[guild_key]["next_id"] += 1
    _save(data)
    return case_id


def get_user_history(guild_id: int, target_id: int) -> list[dict]:
    data = _load()
    cases = data.get(str(guild_id), {}).get("cases", [])
    return [c for c in cases if c["target_id"] == target_id]


def get_all_cases(guild_id: int) -> list[dict]:
    data = _load()
    return data.get(str(guild_id), {}).get("cases", [])


def get_warnings(guild_id: int, target_id: int) -> list[dict]:
    return [c for c in get_user_history(guild_id, target_id) if c["action"] == "warn"]
