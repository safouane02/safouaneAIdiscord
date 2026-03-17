import time
import hashlib
from collections import OrderedDict

# Simple LRU cache with TTL
# key: hash(question) → value: (answer, timestamp)

_cache: OrderedDict[str, tuple[str, float]] = OrderedDict()

MAX_SIZE = 500       # max cached answers
TTL = 60 * 60 * 6   # 6 hours


def _hash(text: str) -> str:
    normalized = " ".join(text.lower().split())
    return hashlib.md5(normalized.encode()).hexdigest()


def get(question: str) -> str | None:
    key = _hash(question)
    entry = _cache.get(key)

    if not entry:
        return None

    answer, timestamp = entry
    if time.time() - timestamp > TTL:
        _cache.pop(key, None)
        return None

    # move to end (LRU)
    _cache.move_to_end(key)
    return answer


def set(question: str, answer: str):
    key = _hash(question)

    if key in _cache:
        _cache.move_to_end(key)
    elif len(_cache) >= MAX_SIZE:
        _cache.popitem(last=False)  # remove oldest

    _cache[key] = (answer, time.time())


def stats() -> dict:
    return {"size": len(_cache), "max": MAX_SIZE, "ttl_hours": TTL // 3600}
