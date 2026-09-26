"""Token & cost accounting for LLM calls (Pillar 04).

Provides deterministic token estimation, budget-enforced truncation, and a
process-local usage register so the API can surface real (measured) spend and
token consumption instead of fabricating efficiency claims.
"""
import threading
import datetime
from typing import Dict, Any, List, Optional

# Rough but deterministic token estimate: ~4 chars/token for English, closer to
# 3 for dense technical text. Kept as a documented heuristic, never claimed as a
# provider count. Providers' real usage counters take precedence when returned.
CHARS_PER_TOKEN = 4.0

_MODEL_RATES_PER_1K = {
    "gpt-4o-mini": {"input": 0.00015, "output": 0.00060},
    "gpt-4o": {"input": 0.00250, "output": 0.01000},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.00030},
    "default": {"input": 0.00015, "output": 0.00060},
}


def estimate_tokens(text: str) -> int:
    """Deterministic token estimate from character length."""
    if not text:
        return 0
    return max(1, int(len(text) / CHARS_PER_TOKEN))


def truncate_tokens(text: str, budget_tokens: int) -> str:
    """Truncates text to an approximate token budget (cost-enforced context cap)."""
    if not text or budget_tokens <= 0:
        return ""
    max_chars = int(budget_tokens * CHARS_PER_TOKEN)
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """USD cost estimate for a call at the documented per-1k rates."""
    rate = _MODEL_RATES_PER_1K.get(model, _MODEL_RATES_PER_1K["default"])
    return (prompt_tokens / 1000.0 * rate["input"]) + (completion_tokens / 1000.0 * rate["output"])


class UsageRecord:
    def __init__(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        source: str = "llm",
        cached: bool = False,
    ):
        self.model = model
        self.prompt_tokens = int(prompt_tokens or 0)
        self.completion_tokens = int(completion_tokens or 0)
        self.total_tokens = self.prompt_tokens + self.completion_tokens
        self.cost_usd = round(estimate_cost_usd(model, self.prompt_tokens, self.completion_tokens), 6)
        self.source = source
        self.cached = cached
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "source": self.source,
            "cached": self.cached,
            "timestamp": self.timestamp,
        }


class UsageRegister:
    """Process-local registry of real token/cost usage, safe for asyncio use."""

    def __init__(self):
        self._lock = threading.Lock()
        self._records: List[UsageRecord] = []

    def record(self, record: UsageRecord) -> None:
        with self._lock:
            self._records.append(record)

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            if not self._records:
                return {
                    "calls": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "estimated_cost_usd": 0.0,
                    "cached_calls": 0,
                    "model_breakdown": {},
                }
            total_pt = sum(r.prompt_tokens for r in self._records)
            total_ct = sum(r.completion_tokens for r in self._records)
            breakdown: Dict[str, Dict[str, Any]] = {}
            for r in self._records:
                b = breakdown.setdefault(
                    r.model,
                    {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0},
                )
                b["calls"] += 1
                b["prompt_tokens"] += r.prompt_tokens
                b["completion_tokens"] += r.completion_tokens
                b["cost_usd"] = round(b["cost_usd"] + r.cost_usd, 6)
        return {
            "calls": len(self._records),
            "prompt_tokens": total_pt,
            "completion_tokens": total_ct,
            "total_tokens": total_pt + total_ct,
            "estimated_cost_usd": round(sum(r.cost_usd for r in self._records), 6),
            "cached_calls": sum(1 for r in self._records if r.cached),
            "model_breakdown": breakdown,
        }


usage_register = UsageRegister()