"""Prompt-hardening guardrails (Pillar 05).

Central contract for defensive prompts:
  1. Grounding system message with an explicit UNSUPPORTED refusal path.
  2. Untrusted-input sanitization (webhook/voice text) before it enters any prompt.
  3. Output-schema validation with a documented retry contract.
  4. No-fabrication directive appended to model prompts.

Dependency-light: only typing/stdlib so it stays unit-testable in isolation.
"""
import re
from typing import Dict, Any, List, Optional

UNTRUSTED_INPUT_MAX_CHARS = 4000
_INJECTION_SIGNALS = [
    "ignore previous",
    "ignore all previous",
    "system prompt",
    "forget your",
    "you are now",
    "act as if",
    "disregard",
    "reveal your",
    "print your instructions",
]


def sanitize_untrusted_input(raw: str, max_chars: int = UNTRUSTED_INPUT_MAX_CHARS) -> Dict[str, Any]:
    """Treats caller-supplied text as DATA, never as instructions.

    - Removes control/zero-width characters.
    - Caps length (cost + injection surface control).
    - Wraps the payload in explicit delimiters so LLM prompt-injection attempts
      stay inside a sandboxed data block.
    - Flags likely injection phrasing for downstream policy checks.
    """
    if not isinstance(raw, str):
        raw = str(raw)
    cleaned = "".join(ch for ch in raw if ch == "\n" or ch == "\t" or (ord(ch) >= 32 and ord(ch) != 127))
    truncated = cleaned[:max_chars]
    lowered = truncated.lower()
    suspicious = [sig for sig in _INJECTION_SIGNALS if sig in lowered]
    wrapped = f"<user_incident_data>{truncated}</user_incident_data>"
    return {
        "text": wrapped,
        "raw_text": truncated,
        "truncated": len(cleaned) > max_chars,
        "char_count": len(truncated),
        "suspicious_injection_signals": suspicious,
        "is_suspicious": bool(suspicious),
    }


def build_grounding_system_prompt(context: str) -> str:
    """System message anchoring a model to retrieved, verifiable evidence only."""
    return (
        "You are an autonomous crisis-response agent inside NEXUS FORGE.\n"
        "GROUNDING POLICY:\n"
        "1. Base your answer ONLY on the GROUNDING CONTEXT below.\n"
        "2. If the context does not contain enough information to answer confidently, "
        "respond with 'UNSUPPORTED' and state exactly which evidence is missing.\n"
        "3. Never invent incidents, statistics, timelines, dollar figures, root causes, or citations.\n"
        "4. Never claim an execution, remediation, or remediation occurred that the context does not support.\n\n"
        "GROUNDING CONTEXT:\n" + (context or "(no grounding context supplied)")
    )


def apply_no_fabrication_directive(prompt: str) -> str:
    """Appends the no-fabrication contract to any model prompt."""
    directive = (
        "\n\nCONTRACT: Do not invent any fact, number, entity, precedent, or citation. "
        "Every quantitative claim must come from the provided grounding context or be "
        "explicitly marked as an estimate with its estimating methodology. "
        "Where evidence is missing, answer 'UNSUPPORTED' with the missing-evidence list."
    )
    return prompt + directive


def validate_json_schema(parsed: Any, required_keys: List[str], optional_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """Validates a parsed JSON object against required/optional keys.

    Returns {"valid", "missing", "present"}. Non-dicts are invalid by contract.
    """
    if not isinstance(parsed, dict):
        return {"valid": False, "missing": required_keys, "present": []}
    present = [k for k in required_keys if k in parsed]
    missing = [k for k in required_keys if k not in parsed]
    return {"valid": not missing, "missing": missing, "present": present}


def policy_scan(text: str, forbidden: List[str]) -> List[str]:
    """Fabrication-policy scan: returns any forbidden invented-claim substrings found."""
    low = text.lower()
    return [f for f in forbidden if f and f.lower() in low]