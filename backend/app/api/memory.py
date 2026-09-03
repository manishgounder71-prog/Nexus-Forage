from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Query, Body, HTTPException
from pydantic import BaseModel, Field
from app.memory.qdrant_client import qdrant_store

router = APIRouter(prefix="/memory", tags=["Memory"])

class MemoryInsertRequest(BaseModel):
    collection_name: str = Field(default="mission_memory", description="Target Qdrant collection")
    content: str = Field(description="Raw text content of the memory")
    title: Optional[str] = Field(default=None, description="Memory headline")
    tags: Optional[List[str]] = Field(default=["crisis_command", "manual_entry"])
    confidence: Optional[float] = Field(default=0.95, ge=0.0, le=1.0)
    mission_id: Optional[str] = Field(default=None)
    agent_id: Optional[str] = Field(default="operator")

@router.get("/stats", response_model=Dict[str, Any])
async def get_qdrant_stats():
    """Returns real-time indexing status, vector counts, and dimensions across all Qdrant collections."""
    return qdrant_store.get_collection_stats()

@router.get("/collections", response_model=List[str])
async def list_qdrant_collections():
    """Lists all configured Qdrant vector memory collections."""
    return qdrant_store.list_collections()

@router.get("/query", response_model=List[Dict[str, Any]])
async def query_vector_memories(
    collection: str = Query("all", description="Logical collection name or 'all'"),
    q: str = Query("system failure", description="Semantic query text"),
    limit: int = Query(5, ge=1, le=50)
):
    """Queries Qdrant vector memory collection for semantic context."""
    results = qdrant_store.query_memory(collection_name=collection, query=q, limit=limit)
    return results

@router.post("/insert", response_model=Dict[str, Any])
async def insert_vector_memory(request: MemoryInsertRequest):
    """Directly injects a new vector point into Qdrant memory with 384-dim embedding & payload metadata."""
    payload = qdrant_store.write_memory(
        collection_name=request.collection_name,
        content=request.content,
        metadata={
            "title": request.title or request.content[:40],
            "tags": request.tags,
            "confidence": request.confidence,
            "outcome": "stored"
        },
        mission_id=request.mission_id,
        agent_id=request.agent_id
    )
    return {
        "status": "SUCCESS",
        "message": f"Point inserted into Qdrant collection '{request.collection_name}'",
        "memory_point": payload
    }
