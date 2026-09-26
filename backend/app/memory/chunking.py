"""Text chunking for retrieval-quality ingestion (Pillar 03).

Splits long memory/doc content into overlapping passages so semantic retrieval
hits granular, self-contained chunks instead of the whole document. Pure,
dependency-light logic (unit-testable without heavy imports).
"""
import re
from typing import List, Dict, Any


def split_sentences(text: str) -> List[str]:
    cleaned = re.sub(r"\s+", " ", text.strip())
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [p for p in parts if p]


def chunk_text(
    text: str,
    chunk_size: int = 600,
    overlap: int = 80,
) -> List[Dict[str, Any]]:
    """Splits `text` into overlapping chunks bounded near sentence boundaries.

    Returns list of {"chunk_index", "start_char", "end_char", "content"}.
    Chunking is deterministic and preserves provenance (span info) so retrieval
    can attribute each hit to a specific passage.
    """
    if not text:
        return []
    if len(text) <= chunk_size:
        return [{"chunk_index": 0, "start_char": 0, "end_char": len(text), "content": text}]

    sentences = split_sentences(text)
    chunks: List[Dict[str, Any]] = []
    current = ""
    start_char = 0

    def flush(c: str, st: int) -> None:
        nonlocal chunks
        chunks.append({
            "chunk_index": len(chunks),
            "start_char": st,
            "end_char": st + len(c),
            "content": c[:chunk_size],
        })

    for sent in sentences:
        if not current:
            current = sent
            start_char = 0
        elif len(current) + len(sent) + 1 <= chunk_size:
            current += " " + sent
        else:
            flush(current, start_char)
            # Carry trailing overlap tokens from previous chunk for boundary recall.
            overlap_seed = current[-overlap:] if len(current) > overlap else current
            current = overlap_seed + " " + sent
            start_char = max(0, (start_char + len(overlap_seed) - overlap))
    if current:
        flush(current, start_char)

    return chunks