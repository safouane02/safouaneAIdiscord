import os
from itertools import cycle


def _load_keys() -> list[str]:
    keys = []

    # support GROQ_API_KEY, GROQ_API_KEY_2, GROQ_API_KEY_3 ...
    primary = os.getenv("GROQ_API_KEY")
    if primary:
        keys.append(primary)

    i = 2
    while True:
        key = os.getenv(f"GROQ_API_KEY_{i}")
        if not key:
            break
        keys.append(key)
        i += 1

    return keys


class KeyPool:
    def __init__(self):
        self._keys = _load_keys()
        self._cycle = cycle(self._keys) if self._keys else None
        self._current_index = 0

    def next_key(self) -> str:
        if not self._keys:
            raise RuntimeError("No GROQ_API_KEY found in .env")
        key = next(self._cycle)
        self._current_index = (self._current_index + 1) % len(self._keys)
        return key

    @property
    def count(self) -> int:
        return len(self._keys)


pool = KeyPool()
