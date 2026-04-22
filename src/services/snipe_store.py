# safouane02.github

from collections import defaultdict

_deleted: dict[int, dict] = {}
_edited: dict[int, dict] = defaultdict(dict)


def store_deleted(channel_id: int, message):
    _deleted[channel_id] = {
        "content": message.content,
        "author": str(message.author),
        "avatar": str(message.author.display_avatar.url),
        "timestamp": message.created_at,
    }


def store_edited(channel_id: int, before, after):
    _edited[channel_id] = {
        "before": before.content,
        "after": after.content,
        "author": str(before.author),
        "avatar": str(before.author.display_avatar.url),
        "timestamp": before.created_at,
    }


def get_deleted(channel_id: int) -> dict | None:
    return _deleted.get(channel_id)


def get_edited(channel_id: int) -> dict | None:
    return _edited.get(channel_id)
