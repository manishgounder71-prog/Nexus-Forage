"""
demo_seed.py — seeds the ACME DIGITAL demo organization on startup so the
platform is immediately explorable without manual provisioning.
"""
import uuid
from datetime import datetime

from sqlalchemy import select

from app.core.config import settings
from app.db import models as M
from app.db.session import AsyncSessionLocal


async def seed_demo_organization() -> dict:
    org_id = settings.DEMO_ORG_ID
    public_id = "org_acme_digital_pub"
    demo_secret = "whsec_acme_digital_demo_secret_2026"

    async with AsyncSessionLocal() as db:
        async with db.begin():
            org = (await db.execute(select(M.OrganizationModel).where(M.OrganizationModel.id == org_id))).scalar_one_or_none()
            created = False
            if org is None:
                org = M.OrganizationModel(
                    id=org_id,
                    public_id=public_id,
                    name="ACME DIGITAL",
                    slug="acme-digital",
                    org_type="startup",
                    status="ACTIVE",
                    ingestion_secret_hash=demo_secret,
                    settings={"region": "us-west", "tier": "demo", "ingestion_secret": demo_secret},
                )
                db.add(org)
                created = True
            else:
                if not org.public_id:
                    org.public_id = public_id
                if not org.ingestion_secret_hash:
                    org.ingestion_secret_hash = demo_secret

            # Ensure default OrganizationPolicyModel exists
            policy = (await db.execute(select(M.OrganizationPolicyModel).where(M.OrganizationPolicyModel.org_id == org_id))).scalar_one_or_none()
            if policy is None:
                db.add(M.OrganizationPolicyModel(
                    id=f"pol_{org_id[:12]}",
                    org_id=org_id,
                    rate_limit_per_minute=100,
                    timestamp_tolerance_seconds=300,
                    auto_approval_risk_threshold="MEDIUM",
                    crisis_confidence_threshold=0.85,
                ))

            # Demo OWNER user (no API key needed in demo/no-auth mode)
            existing_user = (await db.execute(select(M.OrgUserModel).where(
                M.OrgUserModel.org_id == org_id, M.OrgUserModel.username == "demo.owner"))).scalar_one_or_none()
            if existing_user is None:
                db.add(M.OrgUserModel(org_id=org_id, username="demo.owner",
                                      email="owner@acme.demo", role="OWNER"))

            # Guarantee the demo connectors exist.
            demo_types = {
                "monitoring": "Payment + Infra Monitors",
                "github": "Payment Service Deploys",
                "support": "Support Queue",
                "webhook": "Universal Webhook Ingest"
            }
            from app.core.security import hash_webhook_token
            for ctype, name in demo_types.items():
                row = (await db.execute(select(M.ConnectorModel).where(
                    M.ConnectorModel.org_id == org_id, M.ConnectorModel.connector_type == ctype))).scalar_one_or_none()
                if row is None:
                    cid = f"conn_{org_id[:12]}_{ctype}_{uuid.uuid4().hex[:6]}"
                    tok = f"wh_{org_id}_{uuid.uuid4().hex[:16]}"
                    webhook_url = f"/api/v1/ingest/{public_id}" if ctype == "webhook" else f"/api/v1/platform/orgs/{org_id}/connectors/{cid}/webhook"
                    db.add(M.ConnectorModel(
                        id=cid, org_id=org_id, connector_type=ctype, name=name, status="CONNECTED",
                        enabled=True, webhook_token_hash=hash_webhook_token(tok),
                        webhook_url=webhook_url))

        return {"status": "seeded" if created else "exists", "org_id": org_id, "public_id": public_id}