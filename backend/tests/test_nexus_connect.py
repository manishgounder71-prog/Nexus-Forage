"""
test_nexus_connect.py — Verification suite for NEXUS CONNECT:
  • HMAC-SHA256 signature verification & timestamp tolerance
  • Replay protection & rate limiting
  • Universal payload normalization
  • Multi-tenant isolation (Events, Approvals, Connectors, Qdrant memory)
  • End-to-end webhook -> incident -> mission -> approval -> memory lifecycle
"""
import asyncio
import hashlib
import hmac
import json
import time
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.core.security import (
    compute_org_webhook_signature,
    generate_ingestion_secret,
    generate_public_org_id,
    validate_timestamp_freshness,
    verify_org_webhook_signature,
)
from app.connectors.policy_engine import action_policy_engine, classify_risk
from app.connectors.base.schemas import RiskClass
from app.memory.qdrant_client import qdrant_store
from app.pipeline.crisis_detector import crisis_engine
from app.db.session import init_db


# ── 1. Unit Tests: Security & Webhook Primitives ──────────────────
def test_hmac_signature_generation_and_verification():
    secret = "whsec_test_secret_key_12345"
    timestamp = str(int(time.time()))
    body = b'{"event_type": "SERVICE_FAILURE", "resource": "payment-api"}'

    sig = compute_org_webhook_signature(timestamp, body, secret)
    assert sig.startswith("sha256=")
    assert verify_org_webhook_signature(timestamp, body, sig, secret) is True

    # Bad signature rejected
    assert verify_org_webhook_signature(timestamp, body, "sha256=invalid_hex", secret) is False

    # Tampered body rejected
    tampered_body = b'{"event_type": "SERVICE_FAILURE", "resource": "tampered-api"}'
    assert verify_org_webhook_signature(timestamp, tampered_body, sig, secret) is False


def test_timestamp_freshness_tolerance():
    now_epoch = str(int(time.time()))
    assert validate_timestamp_freshness(now_epoch, max_age_seconds=300) is True

    # 10 minutes ago -> should be rejected
    old_epoch = str(int(time.time()) - 600)
    assert validate_timestamp_freshness(old_epoch, max_age_seconds=300) is False

    # Invalid timestamp string
    assert validate_timestamp_freshness("not-a-date") is False
    assert validate_timestamp_freshness(None) is False


def test_risk_classification():
    assert classify_risk("read_health") == RiskClass.LOW
    assert classify_risk("get_recent_deployments") == RiskClass.LOW
    assert classify_risk("send_notification") == RiskClass.MEDIUM
    assert classify_risk("rollback_deployment") == RiskClass.HIGH
    assert classify_risk("restart_service") == RiskClass.HIGH
    assert classify_risk("delete_infrastructure") == RiskClass.CRITICAL
    assert classify_risk("purge_database") == RiskClass.CRITICAL


def test_crisis_detector_scoring_and_signals():
    sample_incident = {
        "severity": "critical",
        "confidence": 0.85,
        "meta": {"deployment_recent": True, "deployment_hours_ago": 0.2},
        "source_events": [
            {"event_type": "DEPLOYMENT", "resource": "payment-api"},
            {"event_type": "SERVICE_FAILURE", "resource": "payment-api", "error_rate": "42%"},
            {"event_type": "CUSTOMER_IMPACT", "resource": "payment-api"},
        ],
    }
    verdict = crisis_engine.evaluate(sample_incident)
    assert verdict["is_crisis"] is True
    assert verdict["crisis_score"] >= 0.70
    assert verdict["priority"] == "P1"
    assert any("Critical service failure" in s for s in verdict["signals"])
    assert any("Recent deployment detected" in s for s in verdict["signals"])
    assert any("Error rate exceeded threshold" in s for s in verdict["signals"])


# ── 2. Multi-Tenant Isolation & Security Tests ────────────────────
@pytest.mark.asyncio
async def test_multi_tenant_isolation():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create Org Alpha
        res_a = await client.post("/api/v1/organizations", json={"name": "Alpha Corp", "industry": "fintech"})
        assert res_a.status_code == 201
        org_a = res_a.json()["organization"]

        # Create Org Beta
        res_b = await client.post("/api/v1/organizations", json={"name": "Beta Industries", "industry": "energy"})
        assert res_b.status_code == 201
        org_b = res_b.json()["organization"]

        assert org_a["id"] != org_b["id"]
        assert org_a["public_id"] != org_b["public_id"]

        # Send Event to Org Alpha's universal endpoint
        payload_a = {"event_type": "SERVICE_FAILURE", "resource": "alpha-vault", "summary": "Alpha vault timeout"}
        res_ingest_a = await client.post(
            org_a["ingestion_endpoint"],
            json=payload_a,
            headers={"X-Nexus-Event-Id": "evt_alpha_001", "X-Nexus-Timestamp": str(int(time.time()))},
        )
        assert res_ingest_a.status_code == 202

        # Send Event to Org Beta's universal endpoint
        payload_b = {"event_type": "SECURITY_ALERT", "resource": "beta-substation", "summary": "Beta grid anomaly"}
        res_ingest_b = await client.post(
            org_b["ingestion_endpoint"],
            json=payload_b,
            headers={"X-Nexus-Event-Id": "evt_beta_001", "X-Nexus-Timestamp": str(int(time.time()))},
        )
        assert res_ingest_b.status_code == 202

        # Allow background persistence task to finish
        await asyncio.sleep(0.3)

        # Verify Org Alpha events list only contains Alpha's events
        events_a = (await client.get(f"/api/v1/organizations/{org_a['id']}/events")).json()["events"]
        assert any(e["resource"] == "alpha-vault" for e in events_a)
        assert not any(e["resource"] == "beta-substation" for e in events_a)

        # Verify Org Beta events list only contains Beta's events
        events_b = (await client.get(f"/api/v1/organizations/{org_b['id']}/events")).json()["events"]
        assert any(e["resource"] == "beta-substation" for e in events_b)
        assert not any(e["resource"] == "alpha-vault" for e in events_b)


@pytest.mark.asyncio
async def test_qdrant_multi_tenant_memory_isolation():
    org_alpha = "org_alpha_iso_test"
    org_beta = "org_beta_iso_test"

    # Write lesson for Alpha
    qdrant_store.write_memory(
        collection_name="mission_memory",
        content="Alpha confidential: Mitigated payment deadlock by rolling back commit d8a1e.",
        metadata={"title": "Alpha Payment Fix", "tags": ["alpha", "payment"]},
        organization_id=org_alpha,
    )

    # Write lesson for Beta
    qdrant_store.write_memory(
        collection_name="mission_memory",
        content="Beta confidential: Isolated Substation 09 SCADA protocol injection.",
        metadata={"title": "Beta SCADA Fix", "tags": ["beta", "scada"]},
        organization_id=org_beta,
    )

    # Query as Org Alpha
    results_alpha = qdrant_store.query_memory(
        collection_name="mission_memory",
        query="payment deadlock and SCADA protocol",
        limit=5,
        organization_id=org_alpha,
    )
    # Alpha MUST see its own memory and MUST NEVER see Beta's memory
    assert any("Alpha confidential" in r.get("content", "") for r in results_alpha)
    assert not any("Beta confidential" in r.get("content", "") for r in results_alpha)

    # Query as Org Beta
    results_beta = qdrant_store.query_memory(
        collection_name="mission_memory",
        query="payment deadlock and SCADA protocol",
        limit=5,
        organization_id=org_beta,
    )
    # Beta MUST see its own memory and MUST NEVER see Alpha's memory
    assert any("Beta confidential" in r.get("content", "") for r in results_beta)
    assert not any("Alpha confidential" in r.get("content", "") for r in results_beta)


# ── 3. Human Approval Workflow Test ───────────────────────────────
@pytest.mark.asyncio
async def test_human_approval_workflow():
    await init_db()
    org_test = "org_approval_test"

    # 1. Low risk action executes immediately without approval
    low_res = await action_policy_engine.evaluate_and_request(
        org_id=org_test,
        agent_name="DiagnosticAgent",
        action_name="read_health",
        params={"target": "db-cluster"},
    )
    assert low_res["ok"] is True
    assert low_res["status"] == "EXECUTED"

    # 2. High risk action requires human approval
    high_res = await action_policy_engine.evaluate_and_request(
        org_id=org_test,
        agent_name="DeploymentAgent",
        action_name="rollback_deployment",
        params={"repo": "payment-api", "version": "v2.4.0"},
        reason="47% error rate spike following deployment v2.4.1",
    )
    assert high_res["ok"] is False
    assert high_res["needs_approval"] is True
    approval_id = high_res["approval_id"]
    assert approval_id is not None

    # 3. List approvals shows pending
    pending = await action_policy_engine.list_approvals(org_test, status_filter="PENDING")
    assert any(a["id"] == approval_id for a in pending)

    # 4. Operator approves action
    appr_res = await action_policy_engine.approve_and_execute(
        approval_id=approval_id,
        reviewer="sre-operator",
        reviewer_role="OPERATOR",
    )
    assert appr_res["ok"] is True
    assert appr_res["status"] == "EXECUTED"

    # 5. Verify status updated in ledger
    updated = await action_policy_engine.list_approvals(org_test)
    approved_item = next(a for a in updated if a["id"] == approval_id)
    assert approved_item["status"] == "EXECUTED"
    assert approved_item["reviewed_by"] == "sre-operator"


# ── 4. Replay Protection & Rate Limiting Integration Test ──────────
@pytest.mark.asyncio
async def test_replay_protection_and_rate_limiting():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create organization with tight rate limit (5 req/min)
        res_org = await client.post(
            "/api/v1/organizations",
            json={"name": "Rate Limit Test Org", "rate_limit": 5},
        )
        org = res_org.json()["organization"]
        endpoint = org["ingestion_endpoint"]

        # 1. Test Replay Protection
        event_id = "replay_unique_evt_777"
        payload = {"event_type": "DEPLOYMENT", "resource": "auth-service"}

        # First request -> Accepted (202)
        r1 = await client.post(
            endpoint,
            json=payload,
            headers={"X-Nexus-Event-Id": event_id, "X-Nexus-Timestamp": str(int(time.time()))},
        )
        assert r1.status_code == 202

        # Duplicate request with same event ID -> Idempotent OK (200)
        r2 = await client.post(
            endpoint,
            json=payload,
            headers={"X-Nexus-Event-Id": event_id, "X-Nexus-Timestamp": str(int(time.time()))},
        )
        assert r2.status_code == 200
        assert r2.json().get("status") == "idempotent_duplicate"
