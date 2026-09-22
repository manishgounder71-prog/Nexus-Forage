import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_analytics_overview_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analytics/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert data["summary"]["agent_swarm_size"] > 0
        assert "memory_subsystem" in data
        assert data["memory_subsystem"]["search_dimension"] == 384
        assert "domain_distribution" in data
        assert "sponsor_integrations" in data
        assert data["sponsor_integrations"]["qdrant_vector"]["status"] == "ACTIVE"

@pytest.mark.asyncio
async def test_system_status_readiness_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/system/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "OPERATIONAL"
        assert "components" in data
        comps = data["components"]
        assert "qdrant_vector_memory" in comps
        assert "lyzr_agent_orchestrator" in comps
        assert "omi_voice_pipeline" in comps
        assert "connector_event_bus" in comps

@pytest.mark.asyncio
async def test_audit_logs_query_and_filtering():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Default query
        resp = await client.get("/api/v1/audit/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_records" in data
        assert len(data["records"]) > 0

        # Filter by severity
        info_resp = await client.get("/api/v1/audit/logs?severity=INFO")
        assert info_resp.status_code == 200
        info_data = info_resp.json()
        for rec in info_data["records"]:
            assert rec["severity"] == "INFO"

@pytest.mark.asyncio
async def test_mission_dossier_export():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a mission or test with existing id
        test_id = "msn_test_exp_01"
        resp = await client.get(f"/api/v1/missions/{test_id}/export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["mission_id"] == test_id
        assert "incident_overview" in data
        assert "deliberation_summary" in data
        assert "tasks_executed" in data
        assert "qdrant_memory_citations" in data
        assert "compliance_signoff" in data
        assert data["compliance_signoff"]["regulatory_ready"] is True

@pytest.mark.asyncio
async def test_mission_pause_and_resume():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        mid = "msn_pause_test_01"
        pause_resp = await client.post(f"/api/v1/missions/{mid}/pause")
        assert pause_resp.status_code == 200
        assert pause_resp.json()["status"] == "PAUSED"

        resume_resp = await client.post(f"/api/v1/missions/{mid}/resume")
        assert resume_resp.status_code == 200
        assert resume_resp.json()["status"] == "EXECUTING"

@pytest.mark.asyncio
async def test_connector_simulate_burst():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "event_count": 3,
            "severity": "critical",
            "source": "monitoring"
        }
        resp = await client.post("/api/v1/platform/simulate-burst", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "BURST_INJECTION_COMPLETED"
        assert data["events_injected"] == 3
