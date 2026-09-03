"""
In-memory sliding-window rate limiter keyed by org (or arbitrary scope key).

Used to protect webhook ingestion endpoints from abuse / event floods.
Windows are tracked per key with timestamps; requests exceeding the per-minute
allowance are rejected.
"""
import time
import threading
from collections import defaultdict, deque
from typing import Deque, Dict

from app.core.config import settings


class SlidingWindowRateLimiter:
    def __init__(self, rate_per_minute: int = 0):
        self._rate = rate_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self._windows: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, cost: int = 1) -> bool:
        """Returns True if `key` is within rate for the current window, and records the hit."""
        if self._rate <= 0:
            return True
        now = time.monotonic()
        window_start = now - 60.0
        allowed = False
        with self._lock:
            dq = self._windows[key]
            while dq and dq[0] < window_start:
                dq.popleft()
            if len(dq) + cost <= self._rate:
                dq.extend([now] * cost)
                allowed = True
        return allowed

    def remaining(self, key: str) -> int:
        now = time.monotonic()
        window_start = now - 60.0
        with self._lock:
            dq = self._windows[key]
            while dq and dq[0] < window_start:
                dq.popleft()
            return max(0, self._rate - len(dq))

    def reset(self, key: str) -> None:
        with self._lock:
            self._windows.pop(key, None)


org_rate_limiter = SlidingWindowRateLimiter()