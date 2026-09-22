from typing import Dict, Any, Optional, List
from app.memory.qdrant_client import qdrant_store

class MemoryWriter:
    def write_memory(
        self,
        collection_name: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        mission_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return qdrant_store.write_memory(
            collection_name=collection_name,
            content=content,
            metadata=metadata,
            mission_id=mission_id,
            agent_id=agent_id,
            organization_id=organization_id
        )

    def record_decision(
        self,
        mission_id: str,
        strategy_name: str,
        content: str,
        confidence: float,
        domain: str = "GENERAL",
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return qdrant_store.write_memory(
            collection_name="decision_memory",
            content=content,
            metadata={"title": f"Decision: {strategy_name}", "confidence": confidence, "outcome": "successful", "domain": domain, "organization_id": organization_id},
            mission_id=mission_id,
            organization_id=organization_id
        )

    def record_reflection(
        self,
        mission_id: str,
        lesson_text: str,
        tags: List[str],
        domain: str = "GENERAL",
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return qdrant_store.write_memory(
            collection_name="reflection_memory",
            content=lesson_text,
            metadata={"title": "Reflection Lesson", "tags": tags, "confidence": 0.95, "domain": domain, "organization_id": organization_id},
            mission_id=mission_id,
            organization_id=organization_id
        )

memory_writer = MemoryWriter()
