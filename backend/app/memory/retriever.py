from typing import List, Dict, Any, Optional
from app.memory.qdrant_client import qdrant_store


def _item_stats(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not items:
        return {"count": 0, "avg_similarity": 0.0, "synthetic": 0, "provenanced": 0}
    sims = [float(i.get("similarity_score") or 0.0) for i in items]
    return {
        "count": len(items),
        "avg_similarity": round(sum(sims) / len(sims), 3),
        "synthetic": sum(1 for i in items if i.get("is_synthetic")),
        "provenanced": sum(1 for i in items if i.get("source")),
    }


class MemoryRetriever:
    def retrieve_context_for_mission(
        self,
        query: str,
        limit: int = 5,
        organization_id: Optional[str] = None,
        hybrid: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieves relevant historical context across Qdrant collections:
        mission_memory, failure_memory, decision_memory, and dissent_memory,
        with strict tenant boundary filtering by organization_id.

        All hits carry provenance (``is_synthetic`` / ``source``) from the
        hybrid RRF retrieval path so grounded answers never conflate synthetic
        demo memories with real organizational evidence.
        """
        kw = {"organization_id": organization_id, "hybrid": hybrid}
        missions = qdrant_store.query_memory("mission_memory", query, limit=3, **kw)
        failures = qdrant_store.query_memory("failure_memory", query, limit=2, **kw)
        decisions = qdrant_store.query_memory("decision_memory", query, limit=2, **kw)
        dissents = qdrant_store.query_memory("dissent_memory", query, limit=2, **kw)

        all_hits = missions + failures + decisions + dissents

        def provenance_flag(item: Dict[str, Any]) -> bool:
            return bool(item.get("is_synthetic"))

        return {
            "query": query,
            "organization_id": organization_id,
            "retrieval_method": "RRF_hybrid(lexical+semantic)" if hybrid else "semantic_cosine",
            "relevant_missions": missions,
            "historical_failures": failures,
            "past_decisions": decisions,
            "dissent_warnings": dissents,
            "total_context_nodes": len(all_hits),
            "retrieval_stats": {
                "missions": _item_stats(missions),
                "failures": _item_stats(failures),
                "decisions": _item_stats(decisions),
                "dissents": _item_stats(dissents),
                "synthetic_documents": sum(1 for i in all_hits if provenance_flag(i)),
                "real_documents": sum(1 for i in all_hits if not provenance_flag(i)),
                "synthetic_ratio": round(
                    (sum(1 for i in all_hits if provenance_flag(i)) / len(all_hits)) if all_hits else 0.0, 3
                ),
            },
        }


memory_retriever = MemoryRetriever()
