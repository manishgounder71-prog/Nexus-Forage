"""
retry.py — small async retry with exponential backoff + jitter for flaky
connector/integration calls (Lyzr inference, custom API polls, etc.).
"""
import asyncio
import random
from typing import Callable, Awaitable


async def retry_async(
    coro_factory: Callable[[], Awaitable],
    attempts: int = 3,
    base_delay: float = 0.3,
    backoff_factor: float = 2.0,
    jitter: float = 0.2,
    allowed_exceptions: tuple = (Exception,),
) -> object:
    last_exc = None
    delay = base_delay
    for attempt in range(1, attempts + 1):
        try:
            return await coro_factory()
        except allowed_exceptions as e:
            last_exc = e
            if attempt == attempts:
                break
            await asyncio.sleep(delay + random.uniform(0, jitter))
            delay *= backoff_factor
    raise last_exc