# safouane02.github

import time
from collections import defaultdict, deque
from src.config import config


_buckets: dict[int, deque] = defaultdict(deque)


def is_rate_limited(user_id: int) -> bool:
    now = time.time()
    window = 60.0
    bucket = _buckets[user_id]

    while bucket and now - bucket[0] > window:
        bucket.popleft()

    if len(bucket) >= config.rate_limit_per_minute:
        return True

    bucket.append(now)
    return False


def remaining_cooldown(user_id: int) -> int:
    bucket = _buckets[user_id]
    if not bucket:
        return 0
    oldest = bucket[0]
    wait = 60 - (time.time() - oldest)
    return max(0, int(wait))
