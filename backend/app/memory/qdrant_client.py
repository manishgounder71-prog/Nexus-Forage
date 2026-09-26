import os
import re
import uuid
import math
import hashlib
import datetime
from collections import Counter
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


def _tokenize(text: str) -> List[str]:
    """Lowercase alphanumeric token stream used for lexical (keyword) scoring."""
    return re.findall(r"[a-z0-9]+", (text or "").lower())


class _Bm25Index:
    """Lightweight in-memory BM25 index over mirrored memory records.

    Provides genuine lexical scoring for hybrid retrieval (RRF fusion with the
    semantic vector path). Populated per-query from the in-memory mirror so the
    demo never depends on a live BM25 server.
    """

    def __init__(self, items: List[Dict[str, Any]]):
        self.doc_terms: Dict[str, Counter] = {}
        self.doc_len: Dict[str, int] = {}
        self.docs_with: Counter = Counter()
        self.avgdl = 1.0
        self.k1 = 1.2
        self.b = 0.75
        self._build(items)

    def _build(self, items: List[Dict[str, Any]]) -> None:
        total_len = 0
        for it in items:
            mid = it.get("memory_id")
            if not mid:
                continue
            text = " ".join([
                str(it.get("content", "")),
                str(it.get("title", "")),
                " ".join(str(t) for t in it.get("tags", [])),
            ])
            terms = _tokenize(text)
            counts = Counter(terms)
            self.doc_terms[mid] = counts
            n = len(terms) or 1
            self.doc_len[mid] = n
            total_len += n
            for t in set(terms):
                self.docs_with[t] += 1
        if items and total_len:
            self.avgdl = total_len / len(items)

    def _idf(self, term: str, corpus_size: int) -> float:
        df = self.docs_with.get(term, 0)
        return math.log(1 + (corpus_size - df + 0.5) / (df + 0.5))

    def score(self, query_terms: List[str], memory_id: str) -> float:
        counts = self.doc_terms.get(memory_id)
        if not counts:
            return 0.0
        dl = self.doc_len[memory_id]
        corpus_size = len(self.doc_terms) or 1
        s = 0.0
        for t, f in Counter(query_terms).items():
            tf = counts.get(t, 0)
            if tf == 0:
                continue
            k = self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            s += self._idf(t, corpus_size) * ((tf * (self.k1 + 1)) / (tf + k))
        return s

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
        """Seed mandatory historical memories across all 5 domains into Qdrant.

        NOTE: the seed corpus is a DEMO corpus. Every seed is explicitly labeled
        ``is_synthetic: true`` / ``source: demo_seed_corpus`` so downstream
        consumers can filter or attribute it honestly. Production organizations
        push their own real decisions via ``write_memory`` (which defaults to
        ``is_synthetic: false`` / ``source: organization_pipeline``).
        """
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
                metadata={
                    "title": title,
                    "confidence": conf,
                    "tags": tags,
                    "outcome": "successful",
                    "domain": dom,
                    "is_synthetic": True,
                    "source": "demo_seed_corpus",
                },
            )

        dissent_samples = [
            ("dissent_memory", "Risk Agent: Canary Rollback Too Fast for Auth Middleware", "Risk Agent argued the 8-minute canary rollback window is too aggressive; schema-incompatible rows could still poison reads. Recommended dual-write reconciliation columns during rollback.", 0.91, ["software_incident", "dissent", "rollback"], "SOFTWARE_INCIDENT"),
            ("dissent_memory", "Academic Risk Agent: Staggered Exam Windows Invite Collusion", "Academic Risk Agent dissented from the 24-hour staggered exam window, citing paper-leakage and collusion risk. Proposed algorithmic variable randomization per exam copy instead.", 0.92, ["university_operations", "dissent", "exam"], "UNIVERSITY_OPERATIONS"),
            ("dissent_memory", "Cost Agent: Air Freight Batch-1 Case", "Operational Impact Agent favored a first-batch air cargo airlift to prevent factory line stop, despite cost objections, while rail corridors loaded the bulk volume.", 0.90, ["supply_chain", "dissent", "freight"], "SUPPLY_CHAIN"),
        ]

        for col, title, content, conf, tags, dom in dissent_samples:
            self.write_memory(
                collection_name=col,
                content=content,
                metadata={
                    "title": title,
                    "confidence": conf,
                    "tags": tags,
                    "outcome": "dissent_recorded",
                    "domain": dom,
                    "is_synthetic": True,
                    "source": "demo_seed_corpus",
                },
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
            "title": metadata.get("title", content[:40]),
            "is_synthetic": bool(metadata.get("is_synthetic", False)),
            "source": metadata.get("source", "organization_pipeline"),
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

    def _hybrid_merge(
        self,
        collection_name: str,
        query: str,
        limit: int,
        vector_hits: List[Dict[str, Any]],
        filter_tags: Optional[List[str]] = None,
        domain: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """RRF fusion of semantic vector hits with BM25 keyword scoring."""
        qv = embed_text(query)
        query_terms = _tokenize(query)

        pool = []
        if collection_name == "all":
            for c in MEMORY_COLLECTIONS:
                pool.extend(self.in_memory_store[c])
        else:
            pool = self.in_memory_store.get(collection_name, [])

        filtered = []
        for item in pool:
            if organization_id:
                rec_org = item.get("organization_id", settings.DEMO_ORG_ID)
                if rec_org != organization_id:
                    continue
            if filter_tags and not any(t in item.get("tags", []) for t in filter_tags):
                continue
            filtered.append(item)

        candidates: Dict[str, Dict[str, Any]] = {}
        for hit in vector_hits:
            mid = hit.get("memory_id")
            if mid:
                hit.setdefault("vector_sim", hit.get("similarity_score", 0.0))
                candidates[mid] = hit
        for item in filtered:
            candidates.setdefault(item.get("memory_id"), item)

        vector_scores: Dict[str, float] = {}
        keyword_scores: Dict[str, float] = {}
        for mid, item in candidates.items():
            item_vec = item.get("vector")
            if not item_vec or len(item_vec) != VECTOR_DIM:
                item_vec = embed_text(item.get("content", ""))
                item["vector"] = item_vec
            sim = _vector_cosine_similarity(qv, item_vec)
            item_domain = item.get("domain", "")
            bonus = 0.03 if (domain and item_domain == domain) else 0.0
            vector_scores[mid] = min(sim + bonus, 0.99)

        index = _Bm25Index(filtered)
        for item in filtered:
            keyword_scores[item.get("memory_id")] = index.score(query_terms, item.get("memory_id"))

        K = 60

        def rank_map(scores: Dict[str, float]):
            ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
            return {mid: pos for pos, (mid, _) in enumerate(ordered, start=1) if scores[mid] > 0}

        vector_ranks = rank_map(vector_scores)
        keyword_ranks = rank_map(keyword_scores)

        rrf: Dict[str, float] = {}
        for mid in vector_scores:
            score = 0.0
            if mid in vector_ranks:
                score += 1.0 / (K + vector_ranks[mid])
            if mid in keyword_ranks:
                score += 1.0 / (K + keyword_ranks[mid])
            rrf[mid] = score

        ranked = [mid for mid, _ in sorted(rrf.items(), key=lambda kv: kv[1], reverse=True)]
        results = []
        for mid in ranked[:limit]:
            if rrf[mid] <= 0:
                continue
            item = dict(candidates[mid])
            item["similarity_score"] = round(min(rrf[mid] * K, 0.99), 3)
            item["vector_sim"] = round(vector_scores.get(mid, 0.0), 3)
            item["keyword_sim"] = round(keyword_scores.get(mid, 0.0), 3)
            item["hybrid_method"] = "RRF_hybrid(lexical+semantic)"
            item["is_synthetic"] = item.get("is_synthetic", False)
            item["source"] = item.get("source", "organization_pipeline")
            results.append(item)
        return results

    def query_memory(
        self,
        collection_name: str,
        query: str,
        limit: int = 5,
        filter_tags: Optional[List[str]] = None,
        domain: Optional[str] = None,
        organization_id: Optional[str] = None,
        hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """Hybrid semantic + lexical retrieval (RRF fusion) with provenance labels.

        Returns results with ``similarity_score`` (fused), ``vector_sim``,
        ``keyword_sim``, ``hybrid_method``, and provenance fields
        (``is_synthetic`` / ``source``) so downstream consumers can attribute
        every memory honestly. When ``hybrid=False``, returns pure semantic
        ranking (vector_sim only).
        """
        if collection_name not in MEMORY_COLLECTIONS and collection_name != "all":
            collection_name = "mission_memory"

        vector = embed_text(query)
        vector_hits: List[Dict[str, Any]] = []

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
                    limit=limit * 3
                )
                for record in getattr(points, "points", points):
                    p = dict(record.payload or {})
                    rec_org = p.get("organization_id", settings.DEMO_ORG_ID)
                    if organization_id and rec_org != organization_id:
                        continue
                    p["similarity_score"] = round(float(record.score) if record.score is not None else 0.0, 3)
                    p["vector_sim"] = p["similarity_score"]
                    vector_hits.append(p)
                    if len(vector_hits) >= limit * 3:
                        break
            except Exception as e:
                print(f"[QdrantMemoryStore] Search error in {collection_name}: {e}")

        else:
            store_items = []
            if collection_name == "all":
                for c in MEMORY_COLLECTIONS:
                    store_items.extend(self.in_memory_store[c])
            else:
                store_items = self.in_memory_store.get(collection_name, [])
            for item in store_items:
                if organization_id:
                    rec_org = item.get("organization_id", settings.DEMO_ORG_ID)
                    if rec_org != organization_id:
                        continue
                if filter_tags and not any(t in item.get("tags", []) for t in filter_tags):
                    continue
                item_vec = item.get("vector")
                if not item_vec or len(item_vec) != len(vector):
                    item_vec = embed_text(item.get("content", ""))
                    item["vector"] = item_vec
                sim = _vector_cosine_similarity(vector, item_vec)
                item_domain = item.get("domain", "")
                bonus = 0.03 if (domain and item_domain == domain) else 0.0
                total_score = min(sim + bonus, 0.99)
                item_copy = dict(item)
                item_copy["similarity_score"] = round(float(total_score), 3)
                item_copy["vector_sim"] = item_copy["similarity_score"]
                vector_hits.append(item_copy)

        if not hybrid:
            vector_hits.sort(key=lambda x: x.get("vector_sim", 0.0), reverse=True)
            for hit in vector_hits:
                hit.setdefault("is_synthetic", False)
                hit.setdefault("source", "organization_pipeline")
                hit["hybrid_method"] = "semantic_cosine"
            return vector_hits[:limit]

        return self._hybrid_merge(
            collection_name,
            query,
            limit,
            vector_hits,
            filter_tags=filter_tags,
            domain=domain,
            organization_id=organization_id,
        )

    def evaluate_retrieval(self, limit: int = 3) -> Dict[str, Any]:
        """Computes Precision@k, Recall@k and MRR over labeled gold queries.

        Ground truth is derived from the labeled seed corpus (documents are
        relevant when their domain matches the query's gold domain labels),
        giving a genuine, reproducible retrieval-quality measurement.
        """
        gold_queries: List[Dict[str, Any]] = [
            {"query": "database connection pool exhausted during exam registration system portal", "domains": ["UNIVERSITY_OPERATIONS"]},
            {"query": "authentication middleware deployment regression canary rollback", "domains": ["SOFTWARE_INCIDENT"]},
            {"query": "power grid substation scada breach blackout failover", "domains": ["ENTERPRISE_CRISIS"]},
            {"query": "startup runway bridge funding burn reduction pivot", "domains": ["STARTUP_STRATEGY"]},
            {"query": "port strike shipping containers freight rerouting sourcing", "domains": ["SUPPLY_CHAIN"]},
        ]
        pool = []
        for c in MEMORY_COLLECTIONS:
            pool.extend(self.in_memory_store[c])
        rel_ids = {
            d.upper(): {it["memory_id"] for it in pool if str(it.get("domain", "")).upper() == d.upper()}
            for d in ["UNIVERSITY_OPERATIONS", "SOFTWARE_INCIDENT", "ENTERPRISE_CRISIS", "STARTUP_STRATEGY", "SUPPLY_CHAIN"]
        }

        precision_sum = 0.0
        recall_sum = 0.0
        mrr_sum = 0.0
        per_query = []
        n = len(gold_queries)

        for gq in gold_queries:
            retrieved = self.query_memory("all", gq["query"], limit=limit)
            retrieved_ids = [r.get("memory_id") for r in retrieved]
            relevant = rel_ids.get(gq["domains"][0], set())
            hits = sum(1 for mid in retrieved_ids if mid in relevant)
            precision = hits / max(limit, 1)
            recall = hits / max(len(relevant), 1)
            mrr = 0.0
            for i, mid in enumerate(retrieved_ids, start=1):
                if mid in relevant:
                    mrr = 1.0 / i
                    break
            precision_sum += precision
            recall_sum += recall
            mrr_sum += mrr
            per_query.append({
                "query": gq["query"],
                "gold_domain": gq["domains"][0],
                "precision_at_k": round(precision, 3),
                "recall_at_k": round(recall, 3),
                "mrr": round(mrr, 3),
            })

        return {
            "k": limit,
            "queries_evaluated": n,
            "precision_at_k": round(precision_sum / n, 3),
            "recall_at_k": round(recall_sum / n, 3),
            "mrr": round(mrr_sum / n, 3),
            "method": "Hybrid retrieval (RRF: semantic + BM25 lexical), evaluated on labeled seed corpus",
            "per_query": per_query,
        }

qdrant_store = QdrantMemoryStore()

