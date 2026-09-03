# Architecture — NEXUS FORGE Autonomous Crisis Command

This document maps the autonomous mission pipeline to the three mandatory hackathon
technologies — **Omi** (voice capture), **Qdrant** (persistent vector memory), and
**Lyzr** (multi-agent orchestration) — and shows how every data flow in the system
passes through at least one of them.

```
  Voice /\ Ambience            Mission Request / Orchestration               Persistent Memory
  +-------------------------------------+        +------------------------------------------+
  |  Omi                                |        |  Lyzr Agent Framework                    |
  |  voice-ingest  /  omi-webhook       |        |  +------------+   manager_agent()   +--+ |
  |  transcribe + wake-word parse       |->planner| manager      |--------------------->|  | |
  |  crisis trigger                     |        |  +------------+        invoke     +--+ |
  +-------------------------------------+        |       | <-- delegates subtasks --> |..| |
                                                 |  supervisors (Grid / Supply / Edu) |  | |
                                                 |  LyzrAgentRuntimeAdapter           +--+ |
                                                 +------------------------------------------+
                                                          ^  | reasoning/answers
                                                          |  v
                                        +------------------------------------------+
                                        |  Qdrant vector memory (cosine, 384-dim)  |
                                        |  mission | decision | failure | agent |  |
                                        |  dissent | reflection | domain | cross   |
                                        +------------------------------------------+
```

---

## 1. Omi — voice capture & autonomous launch

**Files:** `app/services/omi_service.py`, `app/api/missions.py`

Omi is the primary input gateway. Spoken or hardware-streamed audio is turned into a
structured, actionable mission trigger.

- `POST /api/v1/missions/voice-ingest` — accepts raw audio bytes (wav/webm/ogg/mp4/mpeg),
  calls `OmiVoiceIngestionService.transcribe_audio_bytes()`.
  - **Live path:** with a real `OMI_API_KEY` (not `omi_dev_...`), it POSTs the audio to
    `{OMI_API_URL}/transcribe` and reads the returned transcription/text.
  - **Fallback:** without a real key it uses a deterministic acoustic decoder so the
    demo never depends on live network access.
- `POST /api/v1/missions/omi-webhook` — receives ambient transcript chunks from Omi
  wearable streams; `parse_ambient_stream_chunk()` detects wake words / crisis keywords
  (`nexus`, `crisis`, `attack`, `blackout`, `scada`, `strike`, …), extracts intent
  (domain, entities, urgency), and auto-launches a mission via the mission engine.
- Wake-word activation and automatic crisis-command parsing are part of the same
  ingestion contract, so the system starts *before* a human needs to type anything.

## 2. Lyzr — multi-agent orchestration, reasoning & task execution

**Files:** `app/agents/lyzr_client.py`, `app/agents/runtime.py`, `app/agents/registry.py`,
`app/agents/selector.py`, `app/orchestration/adaptive_org_engine.py`

Lyzr is the reasoning brain that turns a mission trigger into delegated, observable work.

- `LyzrClient` (`lyzr_client.py`) implements the **Lyzr Agent Framework v3 HTTP API**:
  - `create_agent(...)` → `POST /v3/agents/` provisions a standalone Lyzr agent.
  - `invoke_agent(agent_id, query)` → `POST /v3/agents/{id}/execute` runs it.
  - `manager_agent(manager_id, query, managed_agents)` → orchestrates a supervisor that
    routes subtasks across specialist sub-agents.
  - `run_dag_workflow(...)` → multi-agent DAG orchestration.
  - Auth via the `x-api-key` header; base URL configurable through `LYZR_BASE_URL`
    (default `https://agent-prod.studio.lyzr.ai`).
- `LyzrAgentRuntimeAdapter.execute_task()` (runtime) is the single execution contract for
  every division agent. When a valid Lyzr key is configured it **delegates the task to
  Lyzr for real**; otherwise it executes a deterministic reasoning loop (offline/demo).
- `adaptive_org_engine.py` selects and scales the agent org per mission; `debate_engine.py`
  runs argumentation/consensus; `dag_engine.py` resolves the execution graph —
  all consuming the Lyzr runtime adapter as the task-execution sink.

## 3. Qdrant — persistent vector memory

**Files:** `app/memory/qdrant_client.py`, `app/memory/retriever.py`, `app/memory/writer.py`

Qdrant stores every meaningful artifact so the platform gets smarter across missions.

- `QdrantMemoryStore` connects to the cloud endpoint from `QDRANT_URL`/`QDRANT_API_KEY`,
  or falls back to an in-memory Qdrant instance — both through the real `qdrant-client`.
- On boot it **creates/ensures** nine cosine 384-dim collections:
  `mission_memory`, `decision_memory`, `failure_memory`, `workflow_memory`,
  `agent_memory`, `dissent_memory`, `reflection_memory`, `domain_memory`,
  `cross_domain_memory`.
- Embeddings are computed by a deterministic, content-aware hashing embedder
  (`embed_text`, 384-dim, L2-normalized) — offline and reproducible, no external API.
- `write_memory()` upserts records; `query_memory()` uses `query_points(...)`
  (the `qdrant-client ≥1.x` API; `.search` was removed/renamed and is not used).
- `GET /api/v1/memory/stats` and `/api/v1/memory/collections` expose store health;
  `/api/v1/memory/query` and `/api/v1/memory/insert` expose programmatic access.

---

## 4. Organization Connector Platform (event pipeline → incident → mission)

**Files:** `app/connectors/`, `app/connectors/agent_tools.py`, `app/pipeline/`,
`app/api/connectors.py`, `app/api/demo_seed.py`, `app/api/websocket.py`

Beyond voice, the platform ingests **real operational signals** from an organization's
systems and turns them into autonomous missions — closing the loop between infrastructure
and the AI command capability above.

### Connector SDK (`app/connectors/`)
- A `Connector` ABC + base modules (`base/schemas.py`, `authentication.py`, `events.py`,
  `permissions.py`) every source implements. All connectors normalize raw payloads into a
  `NexusCanonicalEvent` carrying severity, `event_type`, `resource`, `related_services`,
  `deployment_recent`, `error_rate`, `avg_latency_ms`, and a deterministic
  `dedupe_hash`.
- Concrete connectors: **GitHub** (deploys/pushes/alerts), **Slack**, **Monitoring & Alerts**,
  **Universal Webhook**, **Custom API**, **Support & Ticketing**.
- `registry/connector_registry.py` maps connector type → class, validates config, and
  stores type-specific keys in `ConnectorConfig.custom` with a `.get()` accessor.

### Event pipeline (`app/pipeline/`)
- `event_bus.py` — async pub/sub with wildcard subscribers and a non-blocking dispatch
  loop (slow handlers run as `asyncio.create_task`).
- `normalizer.py` — idempotent: `compute_dedupe_hash(connector_id, event_type, resource,
  source_event_id)` so duplicate webhooks are dropped.
- `correlator.py` — **rolling per-org resource clusters** merge events by `resource` OR
  `related_services` overlap within a 10-minute window, with a 1 s debounce so burst
  signals coalesce. Confidence is **max-based + corroboration bonus**, and a cluster only
  becomes a crisis if it clears the threshold (`> 0.7`).
- `crisis_detector.py` — upgrades a correlated cluster to a **crisis** (`CRITICAL`,
  `P1`) when severity, deployment coincidence, or multi-signal corroboration warrant it.
- `incident_bridge.py` — builds a mission prompt from the incident, auto-launches a
  **NEXUS mission** (`run_mission_safely(…, organization_id=…)`) so the org's live
  connector tools reach the agents, and labels the incident `INVESTIGATING` with a
  `mission_id`.

### Agent tools (`app/connectors/agent_tools.py`)
- `ConnectorToolRegistry` exposes READ / PROPOSE / EXECUTE tools per org+connector:
  `connector_read_health`, `connector_read_events`, `connector_propose_change`,
  `connector_execute_change`. EXECUTE is approval-gated and RBAC-protected; risk classes
  map (PROPOSAL→MEDIUM, CHANGE→HIGH, ROTATION→HIGH). Tools are injected into the agent
  task payload by `mission_engine._get_connector_tools(org_id)`.

### REST + demo
- `GET /api/v1/platform/catalog`, `GET /api/v1/platform/orgs`,
  `GET/POST /api/v1/platform/orgs/{org}/connectors`, `GET …/events`, `GET …/incidents`,
  `POST …/incidents/{id}/command` (resolve / escalate / dismiss / run_mission), and
  `POST /api/v1/platform/demo/crisis`.
- `demo_seed.seed_demo_organization()` provisions `org_acme_digital`, OWNER RBAC role, and
  three live connectors (monitoring / github / support).
- `ws://…/ws/organizations/{org}/events` streams normalized events, incidents, and crisis
  escalations to the frontend **Connectors** tab.

### Data flow
```
GitHub/Slack/monitoring/webhook/custom_API/support
        │ (raw payload, HMAC/Bearer auth, rate-limited)
        ▼
  Connector.normalize() → NexusCanonicalEvent (dedupe_hash)
        ▼
  event_bus ──► normalizer (dedupe) ──► correlator (rolling clusters, 1s debounce)
        ▼                                   │ confidence > 0.7 ?
      store                                ▼
        │                              crisis_detector (CRITICAL / P1)
        ▼                                   ▼
  incident created ────────────────► incident_bridge._launch(org_id=…)
                                          ▼
                               run_mission_safely → NEXUS mission
                              agents get connector read/propose/execute tools
                                          ▼
                              incident → INVESTIGATING + mission_id
                                          ▼
                        streamed to /ws/organizations/{org}/events
```

---

## Mission lifecycle (end-to-end)

1. **Capture (Omi):** audio/ambient chunk → transcription → wake-word + intent.
2. **Trigger:** mission auto-launched from spoken command or manual UI.
3. **Plan (Lyzr):** mission engine builds tasks; adaptive org provisions manager +
   division supervisors; DAG engine orders dependencies.
4. **Execute (Lyzr runtime):** each agent runs `execute_task()` — live Lyzr agents when
   keyed; local reasoning loop otherwise. Parallel missions supported.
5. **Deliberate (debate engine):** dissent, voting, consensus gauge, enriched strategy.
6. **Remember (Qdrant):** outcomes written to mission/decision/failure/reflection memory;
   future runs query memory for similar incidents and adapt.
7. **Stream:** `/api/v1/ws/{mission_id}` pushes live events to the frontend.

## Security & secrets

- All credentials (`OMI_API_KEY`, `LYZR_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`,
  `GEMINI_API_KEY`) are read from **environment/.env only** (`app/core/config.py`).
  No secret values are hardcoded in source; `.env` is git-ignored and `.env.example`
  holds empty placeholders.
- API keys sent to Lyzr/Omi as `x-api-key` / `Bearer` headers; never logged.
- **Connector platform:** connectors authenticate via HMAC signature or Bearer token
  (`app/core/security.py`); webhook payloads are HMAC-verified; secrets are encrypted at
  rest (Fernet) by the connector config layer; every request is rate-limited
  (`rate_limiter.py`) and RBAC-gated (`permissions.py`, roles like OWNER/VIEWER) using the
  `X-Org-API-Key` service key. Agent EXECUTE tools require explicit approval.

## Deployment

- `Dockerfile` + `docker-compose.yml` in `backend/` for containerized backend.
- Frontend is static (served by any static server or by the same image).
- Verified runtime: standard **CPython 3.12** virtualenv (binary wheel installs for
  numpy/grpcio/qdrant-client). MSYS2/UCRT Python is unsupported.