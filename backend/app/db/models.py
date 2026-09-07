import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════
# ORGANIZATION & CONNECTOR MODELS (Multi-Tenant Platform)
# ═══════════════════════════════════════════════════════════════

class OrganizationModel(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=generate_uuid)
    public_id = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    org_type = Column(String, default="other")  # startup, enterprise, university, tech_team, other
    settings = Column(JSON, default=dict)
    status = Column(String, default="ACTIVE")  # ACTIVE, ONBOARDING, SUSPENDED
    ingestion_secret_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    users = relationship("OrgUserModel", back_populates="organization", cascade="all, delete-orphan")
    connectors = relationship("ConnectorModel", back_populates="organization", cascade="all, delete-orphan")
    events = relationship("NexusEventModel", back_populates="organization", cascade="all, delete-orphan")
    incidents = relationship("IncidentModel", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLogModel", back_populates="organization", cascade="all, delete-orphan")
    org_memories = relationship("OrgMemoryModel", back_populates="organization", cascade="all, delete-orphan")
    approvals = relationship("ActionApprovalModel", back_populates="organization", cascade="all, delete-orphan")
    policies = relationship("OrganizationPolicyModel", back_populates="organization", cascade="all, delete-orphan")
    missions = relationship("MissionModel", back_populates="organization", cascade="all, delete-orphan")


class OrgUserModel(Base):
    __tablename__ = "org_users"

    id = Column(String, primary_key=True, default=generate_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    username = Column(String, nullable=False)
    email = Column(String, nullable=True)
    role = Column(String, default="VIEWER")  # OWNER, ADMIN, OPERATOR, ANALYST, VIEWER
    permissions = Column(JSON, default=list)
    api_key_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("OrganizationModel", back_populates="users")


class ConnectorModel(Base):
    __tablename__ = "connectors"

    id = Column(String, primary_key=True, default=generate_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    connector_type = Column(String, nullable=False)  # github, slack, webhook, monitoring, custom_api, etc.
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    config = Column(JSON, default=dict)  # encrypted credentials stored here
    status = Column(String, default="DISCONNECTED")  # CONNECTED, DEGRADED, AUTHENTICATION_ERROR, RATE_LIMITED, DISCONNECTED, UNKNOWN
    enabled = Column(Boolean, default=True)
    permissions = Column(JSON, default=lambda: {"read": True, "propose": True, "execute": False})
    allowed_agents = Column(JSON, default=list)
    allowed_event_types = Column(JSON, default=list)
    rate_limit = Column(Integer, default=60)  # requests per minute
    health_check_interval = Column(Integer, default=300)  # seconds
    events_count = Column(Integer, default=0)
    failed_events = Column(Integer, default=0)
    last_event_at = Column(DateTime, nullable=True)
    last_health_check = Column(DateTime, nullable=True)
    webhook_token_hash = Column(String, nullable=True)
    webhook_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    organization = relationship("OrganizationModel", back_populates="connectors")
    nexus_events = relationship("NexusEventModel", back_populates="connector", cascade="all, delete-orphan")


class NexusEventModel(Base):
    __tablename__ = "nexus_events"
    __table_args__ = (
        Index("ix_nexus_events_org_received", "org_id", "received_at"),
        Index("ix_nexus_events_dedupe", "org_id", "dedupe_hash"),
    )

    id = Column(String, primary_key=True, default=generate_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    connector_id = Column(String, ForeignKey("connectors.id"), nullable=True)
    source_event_id = Column(String, nullable=True)
    event_type = Column(String, nullable=False)
    severity = Column(String, default="info")  # info, low, medium, high, critical
    resource = Column(String, nullable=True)
    summary = Column(Text, default="")
    metadata_json = Column(JSON, default=dict)
    raw_payload = Column(JSON, default=dict)
    received_at = Column(DateTime, default=utc_now)
    processed = Column(Boolean, default=False)
    dedupe_hash = Column(String, nullable=True, index=True)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=True)

    organization = relationship("OrganizationModel", back_populates="events")
    connector = relationship("ConnectorModel", back_populates="nexus_events")
    incident = relationship("IncidentModel", back_populates="related_events")


class IncidentModel(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=generate_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    severity = Column(String, default="medium")
    confidence = Column(Float, default=0.0)
    status = Column(String, default="DETECTED")  # DETECTED, INVESTIGATING, MITIGATING, RESOLVED, DISMISSED
    affected_resources = Column(JSON, default=list)
    signals = Column(JSON, default=list)  # explainable detection signals
    event_count = Column(Integer, default=0)
    first_seen = Column(DateTime, default=utc_now)
    last_seen = Column(DateTime, default=utc_now)
    mission_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("OrganizationModel", back_populates="incidents")
    related_events = relationship("NexusEventModel", back_populates="incident")


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    actor = Column(String, nullable=False)  # user_id or "SYSTEM" or "NEXUS"
    action = Column(String, nullable=False)  # connector_connected, event_received, incident_created, etc.
    resource_type = Column(String, nullable=True)  # connector, event, incident, mission, etc.
    resource_id = Column(String, nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("OrganizationModel", back_populates="audit_logs")


class OrgMemoryModel(Base):
    __tablename__ = "org_memories"

    id = Column(String, primary_key=True, default=generate_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    domain = Column(String, default="GENERAL")
    incident_type = Column(String, nullable=True)
    capabilities = Column(JSON, default=list)
    outcome = Column(String, nullable=True)
    lesson = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    source = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("OrganizationModel", back_populates="org_memories")


class ActionApprovalModel(Base):
    __tablename__ = "action_approvals"

    id = Column(String, primary_key=True, default=generate_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    incident_id = Column(String, nullable=True, index=True)
    mission_id = Column(String, nullable=True, index=True)
    agent_name = Column(String, nullable=False)
    action_name = Column(String, nullable=False)  # e.g. rollback_deployment, restart_service
    target_connector_id = Column(String, nullable=True)
    risk_level = Column(String, default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    params = Column(JSON, default=dict)
    reason = Column(Text, default="")
    status = Column(String, default="PENDING")  # PENDING, APPROVED, REJECTED, EXECUTED, FAILED
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    execution_result = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("OrganizationModel", back_populates="approvals")


class OrganizationPolicyModel(Base):
    __tablename__ = "organization_policies"

    id = Column(String, primary_key=True, default=generate_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    rate_limit_per_minute = Column(Integer, default=100)
    timestamp_tolerance_seconds = Column(Integer, default=300)
    auto_approval_risk_threshold = Column(String, default="MEDIUM")  # LOW, MEDIUM (HIGH/CRITICAL always require human)
    crisis_confidence_threshold = Column(Float, default=0.85)
    max_payload_bytes = Column(Integer, default=1048576)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    organization = relationship("OrganizationModel", back_populates="policies")


class MissionModel(Base):
    __tablename__ = "missions"

    id = Column(String, primary_key=True, default=generate_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    title = Column(String, nullable=False)
    raw_prompt = Column(Text, nullable=False)
    mission_type = Column(String, default="critical_system_failure")
    severity = Column(String, default="critical")
    urgency = Column(Float, default=0.95)
    deadline_hours = Column(Integer, default=24)
    status = Column(String, default="CREATED")  # CREATED, ANALYZED, EXECUTING, DEBATING, RED_TEAM, COMPLETED, FAILED
    constraints = Column(JSON, default=list)
    required_capabilities = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    organization = relationship("OrganizationModel", back_populates="missions")
    tasks = relationship("TaskModel", back_populates="mission", cascade="all, delete-orphan")
    events = relationship("MissionEventModel", back_populates="mission", cascade="all, delete-orphan")

class MissionEventModel(Base):
    __tablename__ = "mission_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    mission_id = Column(String, ForeignKey("missions.id"), nullable=False)
    event_type = Column(String, nullable=False)
    stage = Column(String, default="EXECUTION")
    message = Column(Text, nullable=False)
    payload = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)

    mission = relationship("MissionModel", back_populates="events")

class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)
    division = Column(String, nullable=False)  # Intelligence, Strategy, Risk & Operations
    specialization = Column(String, nullable=False)
    capabilities = Column(JSON, default=list)
    cost_weight = Column(Float, default=0.7)
    speed_score = Column(Float, default=0.9)
    reputation_score = Column(Float, default=0.92)
    total_missions = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    mission_id = Column(String, ForeignKey("missions.id"), nullable=False)
    title = Column(String, nullable=False)
    assigned_agent_id = Column(String, nullable=True)
    assigned_agent_name = Column(String, nullable=True)
    state = Column(String, default="PENDING")  # PENDING, READY, RUNNING, BLOCKED, COMPLETED, FAILED
    confidence = Column(Float, default=0.0)
    reasoning_trace = Column(Text, default="")
    output_deliverable = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    mission = relationship("MissionModel", back_populates="tasks")

class DebateModel(Base):
    __tablename__ = "debates"

    id = Column(String, primary_key=True, default=generate_uuid)
    mission_id = Column(String, nullable=False)
    motion_text = Column(Text, nullable=False)
    current_phase = Column(String, default="01_EVIDENCE")
    consensus_score = Column(Float, default=0.0)
    selected_strategy = Column(String, default="")
    reasoning_summary = Column(Text, default="")
    supporting_agents = Column(JSON, default=list)
    dissenting_agents = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)
