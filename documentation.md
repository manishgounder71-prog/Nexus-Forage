# NEXUS FORGE — Complete System Documentation
**Autonomous Crisis Command & Adaptive Multi-Agent Swarm Platform**

Version: `3.0.0`  
Target Architecture: Cloud (Vercel + Render) & Local (Docker / Python 3.12 + Node.js)  
Sponsor Ecosystem: **Omi** (Voice Capture & Ambience), **Lyzr** (Agent Framework v3), **Qdrant** (Vector Memory & FastEmbed)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [High-Level Architecture & Data Flow](#2-high-level-architecture--data-flow)
3. [Sponsor Integrations & Technical Deep-Dive](#3-sponsor-integrations--technical-deep-dive)
   - [3.1 Omi: Voice Capture, Wake-Word & Multimodal Parsing](#31-omi-voice-capture-wake-word--multimodal-parsing)
   - [3.2 Lyzr: Agent Framework v3, Manager Hierarchy & Circuit Breakers](#32-lyzr-agent-framework-v3-manager-hierarchy--circuit-breakers)
   - [3.3 Qdrant: 9-Collection Cloud Memory & FastEmbed Semantic Embeddings](#33-qdrant-9-collection-cloud-memory--fastembed-semantic-embeddings)
4. [Organization Connector & Ingestion Platform](#4-organization-connector--ingestion-platform)
   - [4.1 Universal Zero-Code Ingestion Endpoint](#41-universal-zero-code-ingestion-endpoint)
   - [4.2 Security, Cryptography & Rate Limiting](#42-security-cryptography--rate-limiting)
   - [4.3 Dual-Mode Incident Bridge & Correlation Engine](#43-dual-mode-incident-bridge--correlation-engine)
   - [4.4 Concrete Connectors](#44-concrete-connectors)
   - [4.5 Governance, Policy Engine & Human Approval Console](#45-governance-policy-engine--human-approval-console)
5. [Domain Adaptation Engine & Knowledge Packs](#5-domain-adaptation-engine--knowledge-packs)
6. [Autonomous Deliberation Parliament & DAG Execution](#6-autonomous-deliberation-parliament--dag-execution)
7. [Frontend Command Center Architecture](#7-frontend-command-center-architecture)
   - [7.1 Design Philosophy & Aesthetics](#71-design-philosophy--aesthetics)
   - [7.2 Dynamic Endpoint Resolver (`nexus-config.js`)](#72-dynamic-endpoint-resolver-nexus-configjs)
   - [7.3 Interactive Modules & Sound Synthesis](#73-interactive-modules--sound-synthesis)
8. [Comprehensive API & WebSocket Reference](#8-comprehensive-api--websocket-reference)
9. [Deployment & Operations Guide](#9-deployment--operations-guide)
   - [9.1 Deploying Backend to Render](#91-deploying-backend-to-render)
   - [9.2 Deploying Frontend to Vercel](#92-deploying-frontend-to-vercel)
   - [9.3 Zero-Downtime Keep-Alive via Uptime Robot](#93-zero-downtime-keep-alive-via-uptime-robot)
   - [9.4 Local Development & Docker Orchestration](#94-local-development--docker-orchestration)
10. [Testing, Benchmarks & Quality Assurance](#10-testing-benchmarks--quality-assurance)

---

## 1. Executive Summary

**NEXUS FORGE** is an autonomous, mission-driven crisis orchestration platform designed to replace chaotic war rooms with coordinated, multi-agent swarms. During high-stakes incidents—such as critical infrastructure outages, supply chain bottlenecks, security breaches, or sudden financial anomalies—organizations typically suffer from latency, fragmented communication, and analysis paralysis.

NEXUS FORGE solves this by creating a unified command loop:
1. **Listens & Ingests**: Continuous ambient listening via wearable **Omi** hardware or automated webhook telemetry via the **Universal Connector Platform**.
2. **Diagnoses & Triages**: Event normalization, cross-source signal correlation, and automated incident severity classification.
3. **Organizes Swarms**: Dynamic provisioning of specialized agent divisions managed via the **Lyzr Agent Framework v3**.
4. **Deliberates & Resolves**: Multi-agent adversarial debate (dissent, critique, risk voting) to produce battle-tested plans before taking action.
5. **Governs**: Strict policy engine with human-in-the-loop approval workflows for destructive or sensitive operations.
6. **Remembers & Adapts**: Persistent vector memory across 9 collections using **Qdrant** and local **FastEmbed** semantic embeddings, allowing the system to learn from historical incident retrospectives.

---

## 2. High-Level Architecture & Data Flow

```
                      ┌────────────────────────────────────────────────────────┐
                      │                   INGESTION SURFACE                    │
                      │                                                        │
  Audio Stream ──────►│  Omi Voice Service (STT / Webhook / Wake-Word Detection)│
                      │                                                        │
  Webhooks / APIs ───►│  Universal Ingestion Pipeline (HMAC / Rate Limit / Sig)│
                      └──────────────────────────┬─────────────────────────────┘
                                                 │
                                                 ▼
                      ┌────────────────────────────────────────────────────────┐
                      │              CORRELATION & TRIAGE ENGINE               │
                      │  • Sliding-Window Signal Correlator                    │
                      │  • Crisis Severity Classifier (P1/P2/P3)               │
                      │  • Incident Bridge & Mission Trigger                   │
                      └──────────────────────────┬─────────────────────────────┘
                                                 │
                                                 ▼
                      ┌────────────────────────────────────────────────────────┐
                      │            ADAPTIVE ORG & MISSION ENGINE               │
                      │  • Domain Pack Selection (Enterprise, Infra, Supply)   │
                      │  • Supervisor / Specialist Dynamic Provisioning        │
                      │  • Directed Acyclic Graph (DAG) Task Orchestration    │
                      └─────────────┬────────────────────────────┬─────────────┘
                                    │                            │
                                    ▼                            ▼
  ┌──────────────────────────────────────────────┐  ┌──────────────────────────┐
  │         LYZR MULTI-AGENT RUNTIME             │  │   PARLIAMENT OF AGENTS   │
  │ • Lyzr Agent Framework v3 Manager Pipeline   │  │ • Dissent Generation     │
  │ • Studio Agent Execution & Local Fallbacks   │  │ • Strategic Voting       │
  │ • Circuit Breaker Resilience Strategy        │  │ • Consensus Gauge        │
  └──────────────────────┬───────────────────────┘  └────────────┬─────────────┘
                         │                                       │
                         ▼                                       ▼
  ┌────────────────────────────────────────────────────────────────────────────┐
  │                 PERSISTENT MEMORY & GOVERNANCE LAYER                       │
  │ • Qdrant Cloud Vector Store (9 Collections, 384-Dim FastEmbed Cosine)      │
  │ • Connector Action Registry & Human Approval Gate (Fernet Encrypted)       │
  │ • SQLAlchemy Async SQLite / PostgreSQL Transaction Store                   │
  └──────────────────────────────────────┬─────────────────────────────────────┘
                                         │
                                         ▼
  ┌────────────────────────────────────────────────────────────────────────────┐
  │                  REAL-TIME DISPATCH & FRONTEND COCKPIT                     │
  │ • High-Speed WebSockets: `/api/v1/ws/{mission_id}` & `/ws/organizations`   │
  │ • Cyberpunk Glassmorphism UI (Dashboard, Galaxy, DAG Visualizer, Audio)    │
  │ • Dynamic Cloud / Local Endpoint Resolver (`nexus-config.js`)              │
  └────────────────────────────────────────────────────────────────────────────┘
```

### End-to-End Mission Lifecycle

1. **Detection**: An external webhook reaches `/api/v1/ingest/{org_id}` or an ambient transcript chunk hits `/api/v1/missions/omi-webhook`.
2. **Ingestion & Cryptographic Verification**: The ingestion pipeline checks HMAC signatures, verifies the timestamp within $\pm 300\text{s}$ to prevent replay attacks, and enforces token-bucket rate limits.
3. **Correlation**: Events with severity above the threshold or matching patterns within a rolling time window are grouped into an Incident.
4. **Adaptive Assembly**: The `AdaptiveOrgEngine` selects the appropriate domain pack (e.g., `software_incident`, `enterprise_crisis`) and provisions specialists (e.g., SRE Lead, Security Auditor, Communications Director).
5. **Deliberation (Parliament)**: Agents critique the initial proposal. The `DebateEngine` records dissents, tallies votes, calculates a consensus percentage, and outputs an evolved plan (Plan A $\rightarrow$ Plan B).
6. **Execution (Lyzr Runtime)**: The `DAGExecutionEngine` resolves task dependencies. Tasks are dispatched to Lyzr agents via the `LyzrClient`. Non-destructive read tasks execute immediately; destructive write tasks generate an `ActionApproval` record.
7. **Vector Reflection (Qdrant)**: Plan details, execution logs, failure points, and post-mortems are converted to dense 384-dimensional embeddings via FastEmbed and indexed in Qdrant collections.
8. **Live Streaming**: All events, stage changes, DAG node progressions, and consensus metrics are broadcast over WebSockets to the web cockpit.

---

## 3. Sponsor Integrations & Technical Deep-Dive

NEXUS FORGE deeply incorporates the three hackathon sponsor technologies as primary architectural pillars.

### 3.1 Omi: Voice Capture, Wake-Word & Multimodal Parsing

- **Location**: `backend/app/services/omi_service.py`, `backend/app/api/missions.py`
- **Primary Contracts**:
  - `POST /api/v1/missions/voice-ingest`: Accepts raw audio streams (`multipart/form-data`) supporting `.wav`, `.webm`, `.ogg`, `.mp4`, `.mp3`. If configured with an `OMI_API_KEY`, it routes audio to `{OMI_API_URL}/transcribe` or utilizes Gemini Multimodal STT.
  - `POST /api/v1/missions/omi-webhook`: Designed for continuous ingestion from Omi wearable microphones. Receives real-time transcript chunks and passes them through `parse_ambient_stream_chunk()`.
- **Wake-Word & Crisis Intent Parsing**:
  - Scans for trigger patterns: `"nexus"`, `"forge"`, `"crisis"`, `"blackout"`, `"attack"`, `"ransomware"`, `"incident"`, `"scada"`, `"emergency"`.
  - Automatically extracts:
    - **Domain**: Maps to `enterprise_crisis`, `software_incident`, `supply_chain`, or `university_operations`.
    - **Entities**: Extracts server names, locations, and infrastructure components.
    - **Urgency Level**: Maps to `critical`, `high`, or `medium`.
  - Automatically initializes and launches an autonomous mission without requiring manual UI input.
- **Resilience**: Contains an integrated deterministic acoustic pattern parser that allows full offline testing and simulation if internet access is interrupted.

### 3.2 Lyzr: Agent Framework v3, Manager Hierarchy & Circuit Breakers

- **Location**: `backend/app/agents/lyzr_client.py`, `backend/app/agents/runtime.py`, `backend/app/agents/registry.py`
- **Primary Contracts**:
  - Implements the official **Lyzr Agent Framework v3 API**:
    - `POST /v3/agents/`: Provisions specialized division agents with custom system prompts, tools, and temperature.
    - `POST /v3/agents/{id}/execute`: Executes targeted single-agent queries.
    - `POST /v3/agents/manager/execute`: Provisions supervisor agents that orchestrate managed sub-agents.
    - `POST /v3/workflows/dag/execute`: Executes multi-agent dependency graphs.
- **Enterprise Circuit Breaker (`LyzrCircuitBreaker`)**:
  - Tracks live execution health (`CLOSED`, `OPEN`, `HALF_OPEN`).
  - Automatically isolates network timeouts or cloud rate limits without interrupting the mission flow.
  - When the circuit breaker trips, execution seamlessly transitions to the local heuristic reasoning runtime (`LocalAgentRuntime`) to guarantee zero downtime during life-or-death crisis operations.

### 3.3 Qdrant: 9-Collection Cloud Memory & FastEmbed Semantic Embeddings

- **Location**: `backend/app/memory/qdrant_client.py`, `backend/app/memory/writer.py`, `backend/app/memory/retriever.py`
- **Collections Architecture**:
  On startup, `QdrantMemoryStore` connects to the Qdrant Cloud cluster (or local instance) and verifies the existence of **9 dedicated collections**:
  1. `mission_memory`: High-level mission summaries, goals, and results.
  2. `decision_memory`: Specific tactical choices made by agents.
  3. `failure_memory`: Mitigated failure points, bugs, and edge cases.
  4. `workflow_memory`: Successful DAG execution structures.
  5. `agent_memory`: Individual agent performance and critique logs.
  6. `dissent_memory`: Parliament debates and minority dissents.
  7. `reflection_memory`: Post-incident post-mortems and lessons learned.
  8. `domain_memory`: Specialized domain rules and playbooks.
  9. `cross_domain_memory`: General crisis management heuristics across industries.
- **Dense Vector Embedding Pipeline**:
  - Uses Qdrant's official `fastembed` library with `BAAI/bge-small-en-v1.5`.
  - Produces dense **384-dimensional vector embeddings** run locally via optimized ONNX Runtime without sending customer data to external embedding APIs.
  - Features a deterministic cosine vector distance fallback for constrained environments.
- **Vector Search API**:
  - Uses the modern `qdrant-client >= 1.8.0` `query_points()` interface with native Cosine distance metric:
    $$\text{similarity}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$$
  - Enforces tenant isolation by indexing and filtering by `organization_id`.

---

## 4. Organization Connector & Ingestion Platform

The Connector Platform allows NEXUS FORGE to ingest telemetry, logs, and alerts from real-world enterprise infrastructure.

### 4.1 Universal Zero-Code Ingestion Endpoint

- **Endpoint**: `POST /api/v1/ingest/{org_public_id}`
- External applications do not require bespoke SDKs; standard JSON payloads are accepted.
- Custom field mappings translate external schemas (e.g., Datadog, PagerDuty, AWS SNS, GitHub) into the standard `NexusCanonicalEvent` format.

### 4.2 Security, Cryptography & Rate Limiting

- **HMAC Signature Verification**:
  - Header: `X-Nexus-Signature: sha256=<hex_digest>`
  - The hash is computed using the organization's unique secret: $\text{HMAC-SHA256}(K, \text{raw\_body})$.
  - Protected against timing attacks using constant-time comparison `hmac.compare_digest()`.
- **Replay Attack Prevention**:
  - Header: `X-Nexus-Timestamp: <ISO-8601 or UNIX>`
  - Requests older or newer than $\pm 300\text{ seconds}$ are automatically rejected (`400 Bad Request`).
- **Credential Encryption at Rest**:
  - Third-party API tokens, SSH keys, and webhook secrets are encrypted using Fernet (AES-128-CBC + HMAC-SHA256 authenticated encryption) via `CREDENTIAL_ENCRYPTION_KEY`.
- **Token-Bucket Rate Limiter**:
  - In-memory sliding-window token bucket enforces per-organization rate limits (`RATE_LIMIT_PER_MINUTE`, default 60 req/min). Returns `429 Too Many Requests` with retry headers.

### 4.3 Dual-Mode Incident Bridge & Correlation Engine

- **Direct Trigger Mode**:
  - Events with `severity="CRITICAL"` or `event_type="SERVICE_FAILURE"` bypass the buffer and trigger an immediate mission.
- **Sliding-Window Correlator**:
  - Buffers non-critical events in a 10-minute sliding window.
  - When $\ge 3$ related events occur (or distinct services report anomalies), they are correlated into a single unified `Incident` to prevent notification fatigue.

### 4.4 Concrete Connectors

| Connector | Type | Supported Operations |
| :--- | :---: | :--- |
| **GitHub** | Code / CI | Read commits, list PRs, fetch workflow runs, trigger rollback actions. |
| **Slack** | Comms | Post incident updates, notify on-call channels, listen for approval reactions. |
| **Monitoring (Datadog)** | Observability | Ingest CPU/memory metrics, detect error rate spikes, query monitor states. |
| **Custom Webhook** | Ingestion | Ingest custom JSON alerts with user-defined JSONPath field mappings. |
| **Generic REST API** | Integration | Configurable HTTP actions with header authentication and param interpolation. |
| **Customer Support** | Voice / Helpdesk | Ingest ticket spikes, analyze negative sentiment, trigger customer comms. |

### 4.5 Governance, Policy Engine & Human Approval Console

NEXUS FORGE implements strict guardrails against unauthorized agent actions:
1. **Tool Classification**:
   - `READ`: Non-destructive (e.g., fetch logs, query metrics). Executed automatically.
   - `PROPOSE`: Non-destructive plan creation. Executed automatically.
   - `EXECUTE`: Destructive or state-changing (e.g., `restart_service`, `isolate_node`, `deploy_hotfix`).
2. **Approval Workflow**:
   - When an agent attempts an `EXECUTE` tool, the `ActionPolicyEngine` checks the organization's policies.
   - If human confirmation is required, the action is paused in `PENDING` state and logged in the database (`ActionApproval`).
   - The interactive **Connector Center** UI lights up with an approval card showing the risk rating, proposed payload, and requester.
   - A human operator must click **Approve** or **Reject**; only on approval does the connector execute the API call.

---

## 5. Domain Adaptation Engine & Knowledge Packs

NEXUS FORGE adjusts its vocabulary, risk thresholds, and agent specialties based on domain packs located in `backend/app/domain_packs/`:

1. **Enterprise Cyber Crisis (`enterprise_crisis`)**:
   - *Specialists*: Threat Analyst, Network Containment Specialist, Public Relations Officer, Legal Counsel.
   - *Scenarios*: Ransomware, Active Directory compromise, data exfiltration, SCADA manipulation.
2. **Software Incident Management (`software_incident`)**:
   - *Specialists*: Site Reliability Engineer (SRE), Database Administrator (DBA), DevOps Lead, Customer Support Lead.
   - *Scenarios*: Connection pool exhaustion, cascading API failures, DNS outages, memory leaks.
3. **Global Supply Chain Disruptions (`supply_chain`)**:
   - *Specialists*: Logistics Coordinator, Freight Procurement Officer, Warehouse Manager, Vendor Liaison.
   - *Scenarios*: Port labor strikes, canal blockages, fuel supply shortages, customs audits.
4. **University & Campus Operations (`university_operations`)**:
   - *Specialists*: Campus Safety Chief, Facilities Director, Academic Affairs Liaison, Student Welfare Coordinator.
   - *Scenarios*: Severe weather emergencies, dormitory infrastructure failures, cyber attacks on grading portals.
5. **Startup Strategic Pivots (`startup_strategy`)**:
   - *Specialists*: Chief Strategy Officer, Runway & Finance Controller, Product Architect, Growth Marketer.
   - *Scenarios*: Abrupt loss of funding, predatory competitor maneuvers, core API deprecations.

---

## 6. Autonomous Deliberation Parliament & DAG Execution

Rather than trusting a single generative model prompt, NEXUS FORGE uses adversarial agent deliberation.

```
       Plan Proposal (Plan A)
                 │
                 ▼
     ┌───────────────────────┐
     │  PARLIAMENT OF AGENTS │
     │  • SRE Division       │
     │  • Security Lead      │
     │  • Financial Auditor  │
     └───────────┬───────────┘
                 │
     ┌───────────┴───────────┐
     ▼                       ▼
Minority Dissent       Risk Scoring
"Rollback will drop    "Plan A has 82%
active sessions!"       failure risk"
     │                       │
     └───────────┬───────────┘
                 │
                 ▼
      DebateEngine Synthesis
  • Evolve Plan A ──► Plan B
  • Consensus Metric: 94%
  • Residual Risk: 6%
```

### The DAG Execution Engine (`dag_engine.py`)

Tasks are scheduled as a Directed Acyclic Graph:
- **Dependency Resolution**: Nodes declare prerequisites (`depends_on: ["task_1", "task_2"]`).
- **Parallel Dispatch**: Independent tasks run concurrently via `asyncio.gather`.
- **Topological Sorting**: Automatically prevents circular dependencies and provides real-time node coordinates $(x, y)$ to the frontend visualizer.

---

## 7. Frontend Command Center Architecture

- **Path**: `frontend/`
- **Tech Stack**: Vanilla HTML5, CSS3 Glassmorphism, Modern JavaScript (ES6 Modules), Web Audio API, Canvas 2D / 3D.

### 7.1 Design Philosophy & Aesthetics

- **Dark Luxury & Cyberpunk Aesthetic**: High-contrast dark theme (`#080c14`, `#0d1527`), subtle borders (`rgba(0, 240, 255, 0.15)`), dynamic glass backdrop blur (`backdrop-filter: blur(12px)`).
- **Zero Heavy Frameworks**: Ultra-fast initial page load (<150ms), zero bundling step required for frontend hosting.

### 7.2 Dynamic Endpoint Resolver (`nexus-config.js`)

To support running locally and deploying to Vercel/Render simultaneously:
- **Automatic Environment Detection**:
  - Detects `localhost` or `127.0.0.1` $\rightarrow$ routes to `http://localhost:8000` and `ws://localhost:8000`.
  - Detects cloud host (e.g. `*.vercel.app`) $\rightarrow$ falls back to configured Render cloud URL.
- **Interactive Backend Status Modal**:
  - The top navigation bar displays a dynamic indicator: `Backend: Connected` or `Backend: Connecting...`.
  - Clicking this indicator opens a settings modal allowing users to override the API URL at runtime without modifying code.

### 7.3 Interactive Modules & Sound Synthesis

- **Mission Cockpit**: Real-time event log, dynamic progress meters, Plan A vs Plan B risk comparison matrices.
- **Interactive Memory Galaxy (`memory-galaxy.js`)**: Interactive 3D vector canvas rendering memory nodes with real-time Cosine distance calculation.
- **Connector Center (`connector-center.js`)**: Live cards for managing external integrations, testing webhooks, and approving high-risk actions.
- **Web Audio Sound Synthesizer**: Uses native browser `AudioContext` to generate procedural sound effects (warning sirens, confirmation chirps, critical alerts) with no external MP3 dependencies.

---

## 8. Comprehensive API & WebSocket Reference

### 8.1 System & Uptime

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET / HEAD` | `/ping` | Lightweight ping endpoint for UptimeRobot / uptime bots. Returns `200 OK`. |
| `GET` | `/health` | Complete system health check reporting database, memory, and environment state. |

### 8.2 Ingestion & Connectors

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/ingest/{org_public_id}` | Universal ingestion endpoint with HMAC verification and rate limiting. |
| `GET` | `/api/v1/organizations` | Lists registered organizations. |
| `POST` | `/api/v1/organizations` | Onboards a new organization; returns high-entropy ingestion secret. |
| `GET` | `/api/v1/connectors/platform/overview` | Returns active connectors, pending approvals, and event counters. |
| `POST` | `/api/v1/connectors/platform/approvals/{id}/decide`| Approves or rejects an `EXECUTE` tool operation. |

### 8.3 Missions & Deliberation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/missions` | Launches an autonomous crisis mission. |
| `GET` | `/api/v1/missions` | Lists all active and completed missions. |
| `GET` | `/api/v1/missions/{id}` | Fetches full mission details, DAG graph, and resolution summary. |
| `POST` | `/api/v1/missions/voice-ingest` | Accepts audio files for Omi/Gemini transcription and mission dispatch. |
| `POST` | `/api/v1/missions/omi-webhook` | Ingests continuous ambient voice chunks from Omi hardware. |

### 8.4 Vector Memory (Qdrant)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/memory/stats` | Returns total vector points across all 9 collections. |
| `GET` | `/api/v1/memory/collections`| Lists the configuration and vector counts for all collections. |
| `POST` | `/api/v1/memory/query` | Executes semantic vector similarity search via FastEmbed cosine distance. |
| `POST` | `/api/v1/memory/insert` | Programmatically inserts records into a memory collection. |

### 8.5 WebSockets

- `ws://<host>/api/v1/ws/{mission_id}`: Real-time mission event stream (logs, DAG progression, parliament votes).
- `ws://<host>/ws/organizations/{org_id}/events`: Organization-wide stream for live connector telemetry and approvals.

---

## 9. Deployment & Operations Guide

### 9.1 Deploying Backend to Render

1. **Connect Repository**: Link `https://github.com/manishgounder71-prog/Nexus-Forage.git` on [Render](https://render.com).
2. **Blueprint Deployment**: Render will automatically detect `render.yaml` at the root.
3. **Manual Configuration** (if not using blueprint):
   - **Environment**: `Python 3`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables**:
   - Copy values from `backend/.env.example`.
   - Set `DEMO_MODE=true` to enable automatic fallbacks for demo purposes.

### 9.2 Deploying Frontend to Vercel

1. **Import Project**: Import the repository on [Vercel](https://vercel.com).
2. **Project Settings**:
   - **Framework Preset**: `Other`
   - **Root Directory**: `./frontend` (or root using the provided `vercel.json`).
3. **Routing**: `vercel.json` will automatically configure security headers, assets, and clean URL routing.
4. **Connect to Cloud Backend**: Open the deployed frontend, click the **Backend Status** pill in the top header, and enter your Render URL (e.g. `https://nexus-forage.onrender.com`).

### 9.3 Zero-Downtime Keep-Alive via Uptime Robot

Render's free tier spins down web services after 15 minutes of inactivity. Use an uptime bot to keep it awake:
1. Create a free account at [UptimeRobot](https://uptimerobot.com) or [Cron-Job.org](https://cron-job.org).
2. Create a new **HTTP(s) Monitor**:
   - **URL**: `https://<your-render-app>.onrender.com/ping`
   - **Monitoring Interval**: Every 5 or 10 minutes.
   - **HTTP Method**: `GET` or `HEAD`.
3. The `/ping` endpoint returns `200 OK` (`{"pong":true,"status":"UP"}`) with near-zero memory allocation, keeping your backend warm 24/7.

### 9.4 Local Development & Docker Orchestration

#### Local Execution
```bash
# 1. Start Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 2. Start Frontend
cd frontend
npx serve -l 5500 .  # Or python -m http.server 5500
```

#### Docker Compose
```bash
# Run backend, frontend, and local Qdrant cluster in containers
docker compose up --build -d
```

---

## 10. Testing, Benchmarks & Quality Assurance

NEXUS FORGE features a comprehensive test suite covering backend logic, security, memory, and frontend contracts.

### Running Backend Tests (54 Tests)
```bash
cd backend
pytest tests/ -v
```
- **Coverage**:
  - `test_connector_platform.py`: HMAC auth, Fernet encryption, rate limiting, and RBAC.
  - `test_sponsor_stack.py`: Qdrant 9-collection validation, FastEmbed dimensions, Lyzr client execution, and Omi wake-word extraction.
  - `test_mission_flow.py`: Full mission lifecycle from ingestion to resolution.
  - `test_dag_engine.py`: Graph cycle detection, dependency sequencing, and topological sorting.
  - `test_domain_adaptation.py`: Multi-domain knowledge pack switching.
  - `test_dynamic_reasoning.py`: Adversarial deliberation, dissent logging, and consensus synthesis.

### Running Frontend Tests (5 Tests)
```bash
cd frontend
npm test
```
- **Coverage**:
  - HTML document contracts and required element IDs.
  - Web Audio API synthesizer frequency mapping.
  - DAG coordinate calculation algorithm.
  - Vector cosine distance math.
  - Crisis severity threshold classifier.

### Scenario Benchmarks
```bash
python backend/tests/verify_5_novel_scenarios.py
```
Validates the system across 5 real-world crisis situations (SCADA blackout, banking API collapse, supply port strike, campus disaster, SaaS startup runway shock) with automated assertion verification.

---

*Authored for the NEXUS FORGE Project Ecosystem.*
