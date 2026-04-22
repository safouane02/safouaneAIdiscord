import json
from pathlib import Path
from datetime import datetime

_FILE = Path("data/tickets.json")
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


def create_ticket(guild_id: int, ticket_id: int, user_id: int, channel_id: int) -> dict:
    data = _load()
    key = str(guild_id)
    if key not in data:
        data[key] = {"tickets": {}, "counter": 0, "stats": {"total": 0, "closed": 0}}

    ticket = {
        "id": ticket_id,
        "user_id": user_id,
        "channel_id": channel_id,
        "last_bot_msg_id": None,
        "claimed_by": None,
        "status": "open",
        "opened_at": datetime.utcnow().isoformat(),
        "closed_at": None,
        "rating": None,
        "messages": [],
    }
    data[key]["tickets"][str(channel_id)] = ticket
    data[key]["stats"]["total"] += 1
    _save(data)
    return ticket


def get_ticket(guild_id: int, channel_id: int) -> dict | None:
    data = _load()
    return data.get(str(guild_id), {}).get("tickets", {}).get(str(channel_id))


def update_ticket(guild_id: int, channel_id: int, **kwargs):
    data = _load()
    ticket = data.get(str(guild_id), {}).get("tickets", {}).get(str(channel_id))
    if ticket:
        ticket.update(kwargs)
        _save(data)


def close_ticket(guild_id: int, channel_id: int, transcript: str = None):
    data = _load()
    ticket = data.get(str(guild_id), {}).get("tickets", {}).get(str(channel_id))
    if ticket:
        ticket["status"] = "closed"
        ticket["closed_at"] = datetime.utcnow().isoformat()
        if transcript:
            ticket["transcript"] = transcript
        data[str(guild_id)]["stats"]["closed"] += 1
        _save(data)


def next_ticket_id(guild_id: int) -> int:
    data = _load()
    key = str(guild_id)
    if key not in data:
        data[key] = {"tickets": {}, "counter": 1, "stats": {"total": 0, "closed": 0}}
    data[key]["counter"] += 1
    _save(data)
    return data[key]["counter"]


def get_stats(guild_id: int) -> dict:
    data = _load()
    return data.get(str(guild_id), {}).get("stats", {"total": 0, "closed": 0})


def set_rating(guild_id: int, channel_id: int, rating: int):
    data = _load()
    ticket = data.get(str(guild_id), {}).get("tickets", {}).get(str(channel_id))
    if ticket:
        ticket["rating"] = rating
        _save(data)
