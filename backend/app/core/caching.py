"""Small TTL cache for LLM responses (Pillar 04).

Deterministic caching keyed by (model, normalized prompt/context) so identical
calls inside a mission window replay without recomputing, cutting spend and
latency. Cache is process-local and size-bounded.
"""
import threading
import time
import hashlib
from typing import Optional, Dict, Any


class TtlCache:
    def __init__(self, ttl_seconds: float = 600.0, max_entries: int = 256):
        self.ttl = ttl_seconds
        self.max_entries = max_entries
        self._lock = threading.Lock()
        self._store: Dict[str, Dict[str, Any]] = {}

    def _key(self, namespace: str, *parts: str) -> str:
        raw = "\x00".join([namespace] + [p or "" for p in parts])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, namespace: str, *parts: str) -> Optional[Any]:
        key = self._key(namespace, *parts)
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            if time.time() - entry["ts"] > self.ttl:
                self._store.pop(key, None)
                return None
            return entry["value"]

    def set(self, namespace: str, value: Any, *parts: str) -> None:
        key = self._key(namespace, *parts)
        with self._lock:
            if len(self._store) >= self.max_entries:
                # Evict oldest entry (first insertion order).
                oldest = min(self._store, key=lambda k: self._store[k]["ts"])
                self._store.pop(oldest, None)
            self._store[key] = {"value": value, "ts": time.time()}

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


llm_cache = TtlCache(ttl_seconds=600.0, max_entries=256)