import pytest
import asyncio
from app.services.omi_service import omi_service
from app.memory.qdrant_client import qdrant_store
from app.agents.runtime import LyzrAgentRuntimeAdapter
from app.agents.registry import agent_registry

@pytest.mark.asyncio
async def test_omi_voice_transcription():
    sample_audio = b"\x00\x01\x02\x03" * 100
    # _force_local keeps the unit test hermetic (no writes to the live Omi account)
    res = await omi_service.transcribe_audio_bytes(sample_audio, content_type="audio/wav", _force_local=True)
    assert res["status"] == "success"
    assert "transcription" in res
    assert res["confidence"] >= 0.90
    assert "extracted_intent" in res
    assert res["extracted_intent"]["domain"] is not None

def test_omi_ambient_stream_parsing():
    chunk = omi_service.parse_ambient_stream_chunk("chk_01", "NEXUS, power grid cyber attack reported.")
    assert chunk["is_crisis_trigger"] is True
    assert chunk["extracted_intent"]["urgency"] == "CRITICAL"

def test_qdrant_collections_and_stats():
    stats = qdrant_store.get_collection_stats()
    assert stats["total_collections"] >= 7
    assert stats["vector_dimension"] == 384
    assert stats["metric"] == "Cosine"
    assert "mission_memory" in stats["collections"]

def test_qdrant_write_and_query_memory():
    # Insert new test vector
    inserted = qdrant_store.write_memory(
        collection_name="mission_memory",
        content="Testing SCADA Substation 04 emergency protocol injection.",
        metadata={"title": "SCADA Test Memory", "confidence": 0.98, "tags": ["scada", "test"]}
    )
    assert inserted["memory_id"] is not None
    assert inserted["memory_type"] == "mission_memory"

    # Query
    results = qdrant_store.query_memory("mission_memory", "SCADA emergency", limit=3)
    assert len(results) > 0
    assert any("scada" in r.get("content", "").lower() for r in results)

@pytest.mark.asyncio
async def test_lyzr_agent_runtime_execution():
    agent = LyzrAgentRuntimeAdapter(
        agent_id="test_lyzr_agent_01",
        name="Test Lyzr SCADA Specialist",
        division="Infrastructure Defense",
        specialization="SCADA Protocol Analysis",
        capabilities=["scada_isolation", "firmware_verification"]
    )
    # Force the deterministic offline runtime so this unit test is hermetic —
    # it must not depend on (or mutate) live Lyzr credentials/agents.
    res = await agent.execute_task(
        "SCADA Substation 04 Air-Gap Isolation",
        {"prompt": "Cyber attack on substation"},
        _force_local=True,
    )
    assert res["executed_by"] == "Test Lyzr SCADA Specialist"
    assert res["framework"] == "Lyzr Automata SDK (Solo Agent Runtime)"
    assert res["confidence"] >= 0.88
    assert len(res["tools_invoked"]) > 0
    assert len(res["thought_chain"]) == 4

def test_lyzr_agent_telemetry():
    agents = agent_registry.get_all_agents()
    assert len(agents) >= 6
    for a in agents:
        tel = a.get_telemetry()
        assert tel["framework"] == "Lyzr Automata Agent"
        assert tel["runtime_state"] == "READY"
