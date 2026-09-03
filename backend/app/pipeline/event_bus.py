"""
In-process async event bus.

Middlewares/components (UI stream relay, correlator, analytics) subscribe to
canonical event topics and receive published events. Uses an asyncio queue so
publishers never block on slow consumers.
"""
import asyncio
from typing import Any, Callable, Dict, List

Handler = Callable[[Dict[str, Any]], Any]


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Handler]] = {}
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=2000)
        self._task: asyncio.Task | None = None
        self._running = False

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._subscribers.setdefault(topic, []).append(handler)

    def unsubscribe(self, topic: str, handler: Handler) -> None:
        if topic in self._subscribers:
            self._subscribers[topic] = [h for h in self._subscribers[topic] if h is not handler]

    async def publish(self, topic: str, message: Dict[str, Any]) -> None:
        """Publishes a message to a topic. Wraps with the topic field for consumers."""
        try:
            self._queue.put_nowait({"topic": topic, "message": message})
        except asyncio.QueueFull:
            # Drop oldest to keep the bus responsive under load.
            try:
                self._queue.get_nowait()
                self._queue.put_nowait({"topic": topic, "message": message})
            except Exception:
                pass

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._dispatch_loop())

    async def _dispatch_loop(self) -> None:
        while self._running:
            item = await self._queue.get()
            topic = item["topic"]
            message = item["message"]
            # Exact-topic handlers
            for handler in list(self._subscribers.get(topic, [])):
                await self._safe_call(handler, item)
            # Wildcard '*' handlers receive every message
            for handler in list(self._subscribers.get("*", [])):
                await self._safe_call(handler, item)

    async def _safe_call(self, handler: Handler, item: Dict) -> None:
        try:
            result = handler(item)
            if asyncio.iscoroutine(result):
                # Schedule the exact coroutine without blocking the dispatch loop so a
                # slow handler (e.g. correlator debounce) doesn't stall other subscribers.
                asyncio.create_task(self._run_async(result))
        except Exception:
            pass

    async def _run_async(self, coro) -> None:
        try:
            await coro
        except Exception:
            pass

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()


event_bus = EventBus()