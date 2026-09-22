from typing import List, Dict, Any, Optional
from app.memory.qdrant_client import qdrant_store

class MemoryRetriever:
    def retrieve_context_for_mission(
        self,
        query: str,
        limit: int = 5,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves relevant historical context across Qdrant collections:
        mission_memory, failure_memory, decision_memory, and dissent_memory,
        with strict tenant boundary filtering by organization_id.
        """
        missions = qdrant_store.query_memory("mission_memory", query, limit=3, organization_id=organization_id)
        failures = qdrant_store.query_memory("failure_memory", query, limit=2, organization_id=organization_id)
        decisions = qdrant_store.query_memory("decision_memory", query, limit=2, organization_id=organization_id)
        dissents = qdrant_store.query_memory("dissent_memory", query, limit=2, organization_id=organization_id)

        return {
            "query": query,
            "organization_id": organization_id,
            "relevant_missions": missions,
            "historical_failures": failures,
            "past_decisions": decisions,
            "dissent_warnings": dissents,
            "total_context_nodes": len(missions) + len(failures) + len(decisions) + len(dissents)
        }

memory_retriever = MemoryRetriever()
