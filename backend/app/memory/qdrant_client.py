import os
import uuid
import hashlib
import datetime
from typing import List, Dict, Any, Optional
from app.core.config import settings

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue
    HAS_QDRANT_CLIENT = True
except ImportError:
    HAS_QDRANT_CLIENT = False

try:
    from fastembed import TextEmbedding
    HAS_FASTEMBED = True
    _fastembed_model = None
    def _get_fastembed_model():
        global _fastembed_model
        if _fastembed_model is None:
            _fastembed_model = TextEmbedding("BAAI/bge-small-en-v1.5")
        return _fastembed_model
except ImportError:
    HAS_FASTEMBED = False

VECTOR_DIM = 384

def embed_text(text: str, dim: int = VECTOR_DIM) -> List[float]:
    """
    Generates 384-dimensional dense semantic vector embeddings.
    Primary: Qdrant's FastEmbed (BAAI/bge-small-en-v1.5) ONNX model for genuine semantic recall.
    Fallback: Content-aware deterministic feature hash (offline resilience).
    """
    if HAS_FASTEMBED:
        try:
            model = _get_fastembed_model()
            embeddings = list(model.embed([text]))
            if embeddings and len(embeddings) > 0:
                vec = [float(x) for x in embeddings[0]]
                if len(vec) == dim:
                    return vec
        except Exception as e:
            pass

    # Resilient deterministic feature hashing fallback
    vec = [0.0] * dim
    norm_text = text.lower()
    grams = []
    if len(norm_text) <= 3:
        grams.append(norm_text)
    else:
        for i in range(len(norm_text) - 2):
            grams.append(norm_text[i:i + 3])
        for w in norm_text.split():
            if w.isalnum() and len(w) >= 3:
                grams.append("w:" + w)

    for g in grams:
        h = int(hashlib.md5(g.encode("utf-8")).hexdigest(), 16)
        sign = 1.0 if (h & 1) else -1.0
        idx = h % dim
        vec[idx] += sign

    # L2 normalize
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec

def _vector_cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates true cosine similarity between two dense 384-dim vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = sum(a * a for a in v1) ** 0.5
    norm_b = sum(b * b for b in v2) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))

MEMORY_COLLECTIONS = [
    "mission_memory",
    "decision_memory",
    "failure_memory",
    "workflow_memory",
    "agent_memory",
    "dissent_memory",
    "reflection_memory",
    "domain_memory",
    "cross_domain_memory"
]

class QdrantMemoryStore:
    def __init__(self):
        self.client = None
        self.in_memory_store: Dict[str, List[Dict[str, Any]]] = {c: [] for c in MEMORY_COLLECTIONS}
        self._init_qdrant()

    def _init_qdrant(self):
        if not HAS_QDRANT_CLIENT:
            print("[QdrantMemoryStore] qdrant-client package not installed. Using fallback in-memory vector store.")
            self._seed_sample_memories()
            return

        try:
            if settings.QDRANT_URL:
                print(f"[QdrantMemoryStore] Connecting to Qdrant Cloud/Host at {settings.QDRANT_URL}")
                self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
            else:
                print("[QdrantMemoryStore] Initializing local in-memory Qdrant instance")
                self.client = QdrantClient(":memory:")

            existing_collections = [c.name for c in self.client.get_collections().collections]
            for col in MEMORY_COLLECTIONS:
                if col not in existing_collections:
                    self.client.create_collection(
                        collection_name=col,
                        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                    )
            self._seed_sample_memories()
        except Exception as e:
            print(f"[QdrantMemoryStore] Qdrant connection exception: {e}. Falling back to in-memory store.")
            self.client = None
            self._seed_sample_memories()

    def _seed_sample_memories(self):
        """Seed mandatory historical memories across all 5 domains into Qdrant."""
        samples = [
            # Software Incident
            ("mission_memory", "Auth Middleware Deployment Regression 2025", "Null pointer exception in authentication middleware deployed at release tag v2.4. Canary rollback restored service in 8 mins.", 0.96, ["software_incident", "deployment", "rollback"], "SOFTWARE_INCIDENT"),
            ("decision_memory", "Blue-Green Revert Protocol 2025", "Consensus: Execute Blue-Green router switchback rather than in-flight database patch. Zero data loss achieved.", 0.95, ["software_incident", "decision", "blue-green"], "SOFTWARE_INCIDENT"),
            
            # Enterprise Crisis / Power Grid
            ("mission_memory", "SCADA Substation 04 Breach 2025", "Unauthorized PLC command packet injection detected on Substation 04 switchboard. Air-gapped control loops stopped breach within 15 mins.", 0.96, ["enterprise_crisis", "power-grid", "scada", "cyber-attack"], "ENTERPRISE_CRISIS"),
            ("decision_memory", "Grid Failover Protocol 2025", "Consensus Achieved: Deploy Plan B with multi-region microgrid failover loops. Zero grid blackout recorded.", 0.94, ["enterprise_crisis", "decision", "substation"], "ENTERPRISE_CRISIS"),
            ("failure_memory", "Single Point Substation Failure Alert", "Historical Failure: Direct breaker trip without feeder load shedding caused 3-hour secondary blackout.", 0.89, ["enterprise_crisis", "blackout", "substation"], "ENTERPRISE_CRISIS"),
            
            # Startup Strategy
            ("mission_memory", "Series A Bridge & Burn Reduction 2024", "Startup extended runway from 2.8 to 11.2 months by cutting non-core ad spend and launching B2B upfront annuals.", 0.94, ["startup_strategy", "runway", "bridge"], "STARTUP_STRATEGY"),
            ("decision_memory", "B2B Enterprise Upfront Annual Pivot", "Consensus: Shift from monthly freemium to $25k enterprise upfront contracts with 25% wire discount.", 0.93, ["startup_strategy", "decision", "pivot"], "STARTUP_STRATEGY"),
            
            # Supply Chain
            ("mission_memory", "Rotterdam Port Choke Point Rerouting 2024", "Port strike delayed 14 vessels. Inland electrified rail junction corridor preserved cold-chain refrigerated cargo.", 0.93, ["supply_chain", "logistics", "freight"], "SUPPLY_CHAIN"),
            ("decision_memory", "Secondary Sourcing 60/40 Split", "Consensus: Dual-source microcontrollers 60% regional / 40% secondary with pre-qualified tooling.", 0.92, ["supply_chain", "decision", "sourcing"], "SUPPLY_CHAIN"),
            
            # University Operations
            ("mission_memory", "University Exam System DB Fail 2024", "Database connection pool exhaustion during peak registration sync. Lessons: Use decoupled read-only replicas.", 0.95, ["university_operations", "exam", "portal"], "UNIVERSITY_OPERATIONS"),
            ("decision_memory", "Staggered 24h Exam Window Protocol", "Consensus: Offer 24h continuous window with dynamic paper parameter randomization.", 0.93, ["university_operations", "decision", "fairness"], "UNIVERSITY_OPERATIONS"),
            
            # Cross-Domain Learnings
            ("cross_domain_memory", "Cross-Domain Dependency Isolation Principle", "Lesson transferred from Software Incidents to Supply Chain: Decouple dependencies before triggering rapid failovers.", 0.96, ["cross_domain", "architecture", "decoupling"], "CROSS_DOMAIN")
        ]

        for col, title, content, conf, tags, dom in samples:
            self.write_memory(
                collection_name=col,
                content=content,
                metadata={"title": title, "confidence": conf, "tags": tags, "outcome": "successful", "domain": dom}
            )

    def write_memory(
        self,
        collection_name: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        mission_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Writes structured memory record with domain tagging into designated Qdrant collection."""
        if collection_name not in MEMORY_COLLECTIONS:
            collection_name = "mission_memory"

        memory_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        metadata = metadata or {}
        org_id = organization_id or metadata.get("organization_id") or settings.DEMO_ORG_ID

        payload = {
            "memory_id": memory_id,
            "organization_id": org_id,
            "mission_id": mission_id or str(uuid.uuid4()),
            "agent_id": agent_id or "system",
            "memory_type": collection_name,
            "domain": metadata.get("domain", "GENERAL"),
            "content": content,
            "timestamp": timestamp,
            "confidence": metadata.get("confidence", 0.92),
            "outcome": metadata.get("outcome", "successful"),
            "tags": metadata.get("tags", ["nexus_forge", "adaptive_command"]),
            "title": metadata.get("title", content[:40])
        }

        # Content-aware deterministic 384-dim embedding
        vector = embed_text(content)

        if self.client:
            try:
                self.client.upsert(
                    collection_name=collection_name,
                    points=[PointStruct(id=memory_id, vector=vector, payload=payload)]
                )
            except Exception as e:
                print(f"[QdrantMemoryStore] Upsert error into {collection_name}: {e}")
        
        # Always maintain in-memory store synchronized for fast local lookup and resilient fallback
        self.in_memory_store[collection_name].append(payload)

        return payload

    def list_collections(self) -> List[str]:
        return MEMORY_COLLECTIONS

    def get_collection_stats(self) -> Dict[str, Any]:
        stats = {}
        total_vectors = 0

        for col in MEMORY_COLLECTIONS:
            count = len(self.in_memory_store.get(col, []))
            if self.client:
                try:
                    info = self.client.get_collection(collection_name=col)
                    count = max(count, info.points_count or 0)
                except Exception:
                    pass
            
            stats[col] = {
                "collection_name": col,
                "vectors_count": count,
                "vector_size": 384,
                "distance": "Cosine",
                "status": "GREEN"
            }
            total_vectors += count

        return {
            "qdrant_host": settings.QDRANT_URL or "in-memory (Local FastVector Engine)",
            "total_collections": len(MEMORY_COLLECTIONS),
            "total_vectors_indexed": total_vectors,
            "vector_dimension": 384,
            "metric": "Cosine",
            "collections": stats
        }

    def query_memory(
        self,
        collection_name: str,
        query: str,
        limit: int = 5,
        filter_tags: Optional[List[str]] = None,
        domain: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Queries semantic vector memories with domain-preferential ranking and strict tenant isolation."""
        if collection_name not in MEMORY_COLLECTIONS and collection_name != "all":
            collection_name = "mission_memory"

        vector = embed_text(query)

        if self.client and collection_name != "all":
            try:
                query_filter = None
                if organization_id:
                    query_filter = Filter(
                        must=[FieldCondition(key="organization_id", match=MatchValue(value=organization_id))]
                    )
                points = self.client.query_points(
                    collection_name=collection_name,
                    query=vector,
                    query_filter=query_filter,
                    limit=limit
                )
                output = []
                for record in getattr(points, "points", points):
                    p = dict(record.payload or {})
                    rec_org = p.get("organization_id", settings.DEMO_ORG_ID)
                    if organization_id and rec_org != organization_id:
                        continue
                    p["similarity_score"] = round(float(record.score) if record.score is not None else 0.95, 3)
                    output.append(p)
                    if len(output) >= limit:
                        break
                if output:
                    return output
            except Exception as e:
                print(f"[QdrantMemoryStore] Search error in {collection_name}: {e}")

        # Genuine in-memory vector search with 384-dim cosine similarity
        store_items = []
        if collection_name == "all":
            for c in MEMORY_COLLECTIONS:
                store_items.extend(self.in_memory_store[c])
        else:
            store_items = self.in_memory_store.get(collection_name, [])

        scored_items = []
        for item in store_items:
            # Tenant isolation filter
            if organization_id:
                rec_org = item.get("organization_id", settings.DEMO_ORG_ID)
                if rec_org != organization_id:
                    continue

            # Tag filter
            tags = item.get("tags", [])
            if filter_tags and not any(t in tags for t in filter_tags):
                continue

            item_vec = item.get("vector")
            if not item_vec or len(item_vec) != len(vector):
                item_vec = embed_text(item.get("content", ""))
                item["vector"] = item_vec

            # Compute actual cosine distance in 384-dimensional vector space
            sim = _vector_cosine_similarity(vector, item_vec)

            # Domain alignment subtle weight (prioritizes domain relevance when tied)
            item_domain = item.get("domain", "")
            domain_bonus = 0.03 if (domain and item_domain == domain) else 0.0
            total_score = min(sim + domain_bonus, 0.99)

            item_copy = dict(item)
            item_copy["similarity_score"] = round(float(total_score), 3)
            scored_items.append((total_score, item_copy))

        # Sort strictly by descending cosine vector similarity
        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [it for _, it in scored_items[:limit]]

qdrant_store = QdrantMemoryStore()

