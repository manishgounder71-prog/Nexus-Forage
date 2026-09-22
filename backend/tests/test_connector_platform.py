"""
Tests for the Organization Connector Platform: connector SDK normalization,
correlation pipeline (multi-signal crisis correlation), and the REST API flow.
These are hermetic — they run in-process against the SQLite DB and do not hit
live external integrations.
"""
import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.connectors.registry import connector_registry
from app.pipeline.correlator import correlation_engine
from app.pipeline.ingestion import event_ingestion_pipeline, incident_store


# ── Connector SDK ────────────────────────────────────────────────
@pytest.mark.parametrize("ctype", ["github", "slack", "monitoring", "webhook", "custom_api", "support"])
@pytest.mark.asyncio
async def test_all_connectors_registered(ctype):
    assert connector_registry.validate_type(ctype)
    config = {"connector_id": f"c_{ctype}", "secret": "s"}
    if ctype == "custom_api":
        config["base_url"] = "https://example.invalid"
    if ctype == "slack":
        config = {"connector_id": f"c_{ctype}", "token": "xoxb-test"}
    conn = await connector_registry.create_connector(ctype, config)
    # validate_credentials must be structurally sound.
    res = await conn.validate_credentials()
    assert res.valid is True


@pytest.mark.asyncio
async def test_connector_catalog_complete():
    catalog = connector_registry.catalog()
    types = {c["type"] for c in catalog}
    assert types == {"github", "slack", "monitoring", "webhook", "custom_api", "support"}


@pytest.mark.asyncio
async def test_monitoring_normalize_critical():
    conn = await connector_registry.create_connector("monitoring", {"connector_id": "c_mon", "secret": "s"})
    evt = conn.normalize_event({
        "resource": "payment-api", "summary": "Payment API error rate at 47%",
        "severity": "critical", "metrics": {"error_rate": "47%"}, "source_event_id": "pay_1",
        "deployment_recent": True, "related_services": ["payment-api"]})
    assert evt.severity == "critical"
    assert evt.event_type == "metric_alert"
    assert evt.deployment_recent is True
    assert evt.error_rate == "47%"


@pytest.mark.asyncio
async def test_github_normalize_deployment():
    conn = await connector_registry.create_connector("github", {"connector_id": "c_gh", "secret": "s"})
    evt = conn.normalize_event({
        "repository": {"full_name": "payment-service"},
        "deployment_status": {"state": "success"},
        "deployment": {"ref": "main", "id": "dep-1"},
        "id": "dep_1", "related_services": ["payment-api"]})
    assert evt.event_type == "deployment"
    assert evt.deployment_recent is True
    assert "payment-api" in evt.related_services


@pytest.mark.asyncio
async def test_custom_api_rejects_bad_base_url():
    conn = await connector_registry.create_connector("custom_api", {"connector_id": "c_api"})
    res = await conn.validate_credentials()
    assert res.valid is False


# ── Correlation pipeline ─────────────────────────────────────────
@pytest.fixture(autouse=True)
def _reset_pipeline_state():
    correlation_engine._clusters.clear()
    incident_store.incidents.clear()
    incident_store.crises.clear()
    yield
    correlation_engine._clusters.clear()
    incident_store.incidents.clear()
    incident_store.crises.clear()


@pytest.mark.asyncio
async def test_multi_signal_crisis_correlation():
    captured = []
    correlation_engine.on_incident(lambda inc: captured.append(inc))
    org = f"org_test_{uuid.uuid4().hex[:6]}"

    # Feed events directly to the correlator (hermetic, no event-bus timing).
    async def feed(et, res, sev, related, recent=False):
        await correlation_engine._on_event({
            "topic": f"org.{org}.events",
            "message": {"org_id": org, "event_type": et, "resource": res, "severity": sev,
                        "related_services": related, "dedupe_hash": uuid.uuid4().hex,
                        "source_event_id": uuid.uuid4().hex[:6], "deployment_recent": recent,
                        "connector_type": "x"}})

    # Fire all four concurrently (matching the event bus) so they correlate together.
    await asyncio.gather(
        feed("error_rate_spike", "payment-api", "critical", ["payment-api"], recent=True),
        feed("deployment", "payment-service@main", "info", ["payment-service", "payment-api"], recent=True),
        feed("latency_spike", "database-primary", "medium", ["payment-api"]),
        feed("support_complaint", "payment-api", "medium", ["payment-api"]),
    )

    assert len(captured) == 1
    incident = captured[0]
    assert incident["severity"] == "critical"
    assert set(incident["event_types"]) == {"error_rate_spike", "deployment", "latency_spike", "support_complaint"}
    assert incident["confidence"] >= 0.7
    assert incident["meta"]["deployment_recent"] is True


# ── Ingestion + dedupe + incident store ─────────────────────────
@pytest.mark.asyncio
async def test_ingestion_persists_and_incident_created():
    from app.api.demo_seed import seed_demo_organization
    await seed_demo_organization()
    org = "org_acme_digital"

    res = await event_ingestion_pipeline.ingest(
        org, "conn_test", "monitoring",
        {"resource": "api", "summary": "error spike 10%", "severity": "high",
         "source_event_id": f"t_{uuid.uuid4().hex[:8]}", "metrics": {"error_rate": "10%"}},
        {}, None)
    assert res["status"] == "ingested"
    assert res["event"]["severity"] == "high"
    assert res["event"]["error_rate"] == "10%"  # type: ignore

    # Deduplicate: same source_event_id + same connector_id should be rejected
    res2 = await event_ingestion_pipeline.ingest(
        org, "conn_test", "monitoring",
        {"resource": "api", "summary": "error spike 10%", "severity": "high",
         "source_event_id": res["event"]["source_event_id"],
         "metrics": {"error_rate": "10%"}}, {}, None)
    assert res2["status"] == "duplicate"


# ── Agent tools ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_agent_tool_execute_requires_approval():
    from app.connectors.agent_tools import connector_tool_registry
    r = await connector_tool_registry.invoke(
        "org_acme_digital", "conn_mon", "connector_execute_change", {"action": "rollback"})
    assert r["ok"] is False
    assert r["needs_approval"] is True
    ref = r["approval_ref"]
    assert connector_tool_registry.approve(ref)["ok"] is True
    r2 = await connector_tool_registry.invoke(
        "org_acme_digital", "conn_mon", "connector_execute_change",
        {"action": "rollback"}, approval=True)
    assert r2["ok"] is True
    assert r2["result"]["status"] == "executed"


@pytest.mark.asyncio
async def test_agent_tool_low_risk_auto_runs():
    from app.connectors.agent_tools import connector_tool_registry
    r = await connector_tool_registry.invoke(
        "org_acme_digital", "conn_mon", "connector_propose_change",
        {"action": "investigate", "target": "payment-api"})
    assert r["ok"] is True
    assert r["result"]["proposal"]["action"] == "investigate"


@pytest.mark.asyncio
async def test_agent_tool_role_denied():
    from app.connectors.agent_tools import connector_tool_registry
    r = await connector_tool_registry.invoke(
        "org_acme_digital", "conn_mon", "connector_execute_change",
        {"action": "rollback"}, role="VIEWER")
    assert r["ok"] is False
    assert "lacks permission" in r["error"]


# ── REST API ─────────────────────────────────────────────────────
@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_api_demo_crisis_flow():
    from app.main import app
    from app.api.demo_seed import seed_demo_organization
    from app.pipeline.event_bus import event_bus
    await event_bus.start()
    await seed_demo_organization()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/platform/catalog")
        assert r.status_code == 200
        assert r.json()["count"] == 6

        r = await client.get("/api/v1/platform/orgs/org_acme_digital/connectors")
        assert r.status_code == 200

        r = await client.post("/api/v1/platform/demo/crisis",
                              json={"org_id": "org_acme_digital"})
        assert r.status_code == 200
        body = r.json()
        assert all(out["status"] == "ingested" for out in body["results"])

        # Verify the ingestion webhook path works end-to-end (status + raw persistence).
        conn_row = (await client.get("/api/v1/platform/orgs/org_acme_digital/connectors")).json()["connectors"][0]
        wh = await client.post(
            f"/api/v1/platform/orgs/org_acme_digital/connectors/{conn_row['id']}/webhook",
            json={"payload": {"resource": "checkout", "summary": "checkout errors", "severity": "medium",
                              "source_event_id": f"w_{uuid.uuid4().hex[:8]}"}})
        assert wh.status_code == 200
        assert wh.json()["status"] == "ingested"

        await asyncio.sleep(4)
        r = await client.get("/api/v1/platform/orgs/org_acme_digital/incidents")
        assert r.status_code == 200
        assert isinstance(r.json()["incidents"], list)
    await event_bus.stop()


@pytest.mark.asyncio
async def test_event_bus_dispatches_coroutine_handler_exactly_once():
    """Guards against the leaked/doubled coroutine handling bug where async
    subscribers were called twice (leaking an un-awaited coroutine)."""
    from app.pipeline.event_bus import event_bus
    from app.core.config import settings

    await event_bus.start()
    calls = []

    async def handler(item):
        calls.append(item["message"]["n"])
        # small delay to prove the dispatched coroutine is actually awaited
        await asyncio.sleep(0.05)

    event_bus.subscribe("*", handler)
    try:
        await event_bus.publish("test.topic", {"n": 1})
        await event_bus.publish("test.topic", {"n": 2})
        await asyncio.sleep(0.4)  # give the dispatch loop + scheduled coroutines time
    finally:
        event_bus.unsubscribe("*", handler)
        await event_bus.stop()

    assert sorted(calls) == [1, 2], f"expected exactly-once [1,2], got {calls}"