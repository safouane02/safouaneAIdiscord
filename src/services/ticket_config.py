import json
from pathlib import Path

_FILE = Path("data/ticket_config.json")
_FILE.parent.mkdir(exist_ok=True)

_DEFAULT_PANEL = {
    "title": "🎫 Support Tickets",
    "description": (
        "Need help? Click the button below to open a ticket.\n\n"
        "Our AI support will assist you immediately.\n"
        "If needed, **{support_role}** staff will be notified."
    ),
    "footer": "github.com/safouane02",
    "color": 0x5865F2,
}

_DEFAULT_TICKET = {
    "title": "🎫 Support Ticket",
    "description": (
        "Welcome {user}! 👋\n\n"
        "Please describe your issue and our AI will assist you.\n"
        "Reply to the bot's message to continue the conversation.\n\n"
        "**Commands:**\n"
        "`!close` — Close this ticket\n"
        "`!transcript` — Download transcript\n"
        "`!tadd @user` — Add someone\n"
        "`!claim` — Claim *(staff only)*"
    ),
    "color": 0x5865F2,
}


def _load() -> dict:
    if not _FILE.exists():
        return {}
    try:
        return json.loads(_FILE.read_text())
    except Exception:
        return {}


def _save(data: dict):
    _FILE.write_text(json.dumps(data, indent=2))


def get_panel_message(guild_id: int) -> dict:
    data = _load()
    return data.get(str(guild_id), {}).get("panel", _DEFAULT_PANEL.copy())


def get_ticket_message(guild_id: int) -> dict:
    data = _load()
    return data.get(str(guild_id), {}).get("ticket", _DEFAULT_TICKET.copy())


def set_panel_message(guild_id: int, **kwargs):
    data = _load()
    key = str(guild_id)
    if key not in data:
        data[key] = {}
    current = data[key].get("panel", _DEFAULT_PANEL.copy())
    current.update({k: v for k, v in kwargs.items() if v is not None})
    data[key]["panel"] = current
    _save(data)


def set_ticket_message(guild_id: int, **kwargs):
    data = _load()
    key = str(guild_id)
    if key not in data:
        data[key] = {}
    current = data[key].get("ticket", _DEFAULT_TICKET.copy())
    current.update({k: v for k, v in kwargs.items() if v is not None})
    data[key]["ticket"] = current
    _save(data)


def reset_panel_message(guild_id: int):
    data = _load()
    if str(guild_id) in data:
        data[str(guild_id)].pop("panel", None)
        _save(data)


def reset_ticket_message(guild_id: int):
    data = _load()
    if str(guild_id) in data:
        data[str(guild_id)].pop("ticket", None)
        _save(data)