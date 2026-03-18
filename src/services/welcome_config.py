import json
from pathlib import Path

_FILE = Path("data/welcome_config.json")
_FILE.parent.mkdir(exist_ok=True)

_DEFAULT = {
    "enabled": False,
    "channel_id": None,
    "message": "Welcome {user} to **{server}**! 🎉\nYou are member **#{count}**.",
    "background_color": "#2b2d31",
    "text_color": "#ffffff",
    "show_avatar": True,
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


def get_config(guild_id: int) -> dict:
    return _load().get(str(guild_id), _DEFAULT.copy())


def update_config(guild_id: int, **kwargs):
    data = _load()
    current = data.get(str(guild_id), _DEFAULT.copy())
    current.update({k: v for k, v in kwargs.items() if v is not None})
    data[str(guild_id)] = current
    _save(data)
