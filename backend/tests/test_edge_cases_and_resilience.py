import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.domain_packs.detector import domain_detector
from app.memory.retriever import memory_retriever
from app.services.omi_service import omi_service

@pytest.mark.asyncio
async def test_domain_detector_unknown_fallback():
    """Verify domain detector handles ambiguous or gibberish input cleanly."""
    res = domain_detector.detect_domain("asdkfjhasdfkjhasdf random noise")
    assert res is not None
    assert "primary_domain" in res
    assert res["confidence"] >= 0.0

@pytest.mark.asyncio
async def test_omi_voice_ambient_empty_stream():
    """Verify Omi ambient stream parser handles empty or non-crisis chunks without crashing."""
    res = omi_service.parse_ambient_stream_chunk("chk_empty", "")
    assert res["is_crisis_trigger"] is False
    assert res["chunk_id"] == "chk_empty"

@pytest.mark.asyncio
async def test_memory_retriever_graceful_on_empty():
    """Verify vector memory retrieval functions safely even on novel domains."""
    memories = memory_retriever.retrieve_context_for_mission(
        query="Non-existent legacy incident 99999",
        limit=3
    )
    assert isinstance(memories, dict)
    assert "total_context_nodes" in memories

@pytest.mark.asyncio
async def test_invalid_mission_create_payload():
    """Verify mission creation with missing required fields returns 422 Unprocessable Entity."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/missions", json={})
        assert resp.status_code == 422

@pytest.mark.asyncio
async def test_nonexistent_mission_events_empty_list():
    """Verify requesting events for a nonexistent mission returns empty list rather than 500."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/missions/msn_does_not_exist_404/events")
        assert resp.status_code == 200
        assert resp.json() == []
