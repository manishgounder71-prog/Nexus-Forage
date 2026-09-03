import pytest
import numpy as np
from app.memory.qdrant_client import embed_text, qdrant_store

def cosine_similarity(v1, v2):
    a = np.array(v1)
    b = np.array(v2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def test_fastembed_semantic_distinction():
    """
    Verifies that FastEmbed generates genuine dense semantic embeddings:
    Semantically close phrases ('substation power grid attack' & 'electrical blackout generator failure')
    have much higher cosine similarity than semantically distant phrases ('student exam grading system').
    """
    vec_grid_1 = embed_text("Substation 04 experiencing cyber-attack on SCADA transformer controllers")
    vec_grid_2 = embed_text("Electrical grid power transmission failure and blackout across regional feeders")
    vec_exam = embed_text("University student portal crashed during final semester exam submission")

    assert len(vec_grid_1) == 384
    assert len(vec_grid_2) == 384
    assert len(vec_exam) == 384

    sim_related = cosine_similarity(vec_grid_1, vec_grid_2)
    sim_unrelated = cosine_similarity(vec_grid_1, vec_exam)

    # Dense semantic embeddings must distinguish related from unrelated topics
    assert sim_related > sim_unrelated, f"Expected related ({sim_related:.3f}) > unrelated ({sim_unrelated:.3f})"
    assert sim_related >= 0.65, f"Related infrastructure topics should score >= 0.65, got {sim_related:.3f}"

def test_qdrant_semantic_recall_ranking():
    """Verifies that querying Qdrant memory returns the semantically aligned incident."""
    results = qdrant_store.query_memory(
        collection_name="mission_memory",
        query="High voltage transformer and SCADA PLC frequency anomaly",
        limit=3
    )
    assert len(results) > 0
    top_result = results[0]
    assert "similarity_score" in top_result
    assert top_result["similarity_score"] > 0.70
