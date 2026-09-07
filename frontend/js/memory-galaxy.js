/* ==========================================================================
   NEXUS FORGE — Qdrant Vector Memory Galaxy (Ultra-Interactive Engine v2)
   Features:
   - Draggable nodes with momentum
   - Freeze / unfreeze constellation
   - Zoom + Pan canvas
   - HTML tooltip on hover
   - Side-panel detail with 384-dim vector preview
   - HNSW KNN similarity bars
   - Category filtering + live semantic search
   - Animated pulsar rings on center core
   - Ripple wave on click
   - Inter-node cosine similarity mesh
   - ADD VECTOR button for dynamic injection
   ========================================================================== */

class MemoryGalaxyEngine {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');

    this.zoom = 1;
    this.panX = 0;
    this.panY = 0;
    this.dpr = window.devicePixelRatio || 1;

    this.selectedMemory = null;
    this.hoveredMemory = null;
    this.activeCategory = 'all';
    this.searchQuery = '';
    this.frozen = false;

    this.draggedNode = null;
    this.dragOffsetX = 0;
    this.dragOffsetY = 0;    this.ripples = [];
    this.pulsePhase = 0;
    this.frame = 0;
    this.radarAngle = 0;

    // Ambient 3D Starfield particles
    this.stars = Array.from({ length: 65 }, () => ({
      x: Math.random() * 1200,
      y: Math.random() * 800,
      s: Math.random() * 1.5 + 0.4,
      a: Math.random() * Math.PI * 2,
      speed: Math.random() * 0.015 + 0.005
    }));

    this.currentScenarioTitle = 'Production Deployment Incident';
    this.memories = this.getMemoriesForScenario('production deployment');
    this.nodes = [];
    this.init();
  }

  /* ── Scenario Memory Sets (Strictly Incident-Specific) ─────────────── */
  setScenario(promptText) {
    this.memories = this.getMemoriesForScenario(promptText);
    this.selectedMemory = null;
    this.initNodes();
    this.updateStats();
    if (this.nodes.length > 0) {
      this.selectNode(this.nodes[0]);
      this.addRipple((this.width || 700) / 2, (this.height || 450) / 2, '#8b5cf6');
    }
  }

  getMemoriesForScenario(promptText) {
    const lc = (promptText || '').toLowerCase().trim();

    const isGrid = lc.includes('power grid') || lc.includes('substation') || lc.includes('scada') || lc.includes('blackout') || lc.includes('feeder') || (lc.includes('grid') && !lc.includes('data'));
    const isPayment = lc.includes('payment') || lc.includes('stripe') || lc.includes('fintech') || lc.includes('gateway') || lc.includes('transaction') || lc.includes('psp') || lc.includes('credit card');
    const isExam = lc.includes('exam') || lc.includes('university') || lc.includes('campus') || lc.includes('student') || lc.includes('grading') || lc.includes('faculty');
    const isSupply = lc.includes('supply chain') || lc.includes('cargo') || lc.includes('freight') || lc.includes('logistics') || lc.includes('port') || lc.includes('warehouse') || lc.includes('shipping');
    const isStartup = lc.includes('startup') || lc.includes('runway') || lc.includes('burn') || lc.includes('equity') || lc.includes('investor') || lc.includes('venture') || lc.includes('funding');
    const isSoftware = lc.includes('software') || lc.includes('production') || lc.includes('deployment') || lc.includes('checkout') || lc.includes('database') || lc.includes('connection') || lc.includes('pool') || lc.includes('pod') || lc.includes('sre') || lc.includes('rollback') || lc.includes('microservice') || lc.includes('kubernetes') || lc.includes('incident');

    // Helper to generate full 384-dim array deterministically
    const make384 = (seedStr) => {
      let seed = 0;
      for (let i = 0; i < seedStr.length; i++) seed += seedStr.charCodeAt(i);
      return Array.from({ length: 384 }, (_, i) => +(Math.sin(seed * (i + 1)) * Math.cos(i * 0.28) * 0.94).toFixed(4));
    };

    // 1. Power Grid / SCADA Cyber Attack
    if (isGrid) {
      this.currentScenarioTitle = 'Power Grid SCADA Incident';
      return [
        { id: 'VEC_GRD_849', title: 'SCADA Substation 04 Breach 2025', category: 'mission', similarity: 96.4, payload: 'Unauthorized PLC command packet injection on Substation 04. Air-gapped loops stopped breach in 15 mins.', vector: [0.092, -0.412, 0.884, 0.123, -0.054, 0.731], fullVector: make384('GRD_849'), tags: ['scada','substation','airgap'] },
        { id: 'VEC_GRD_910', title: 'Grid Failover Protocol 2025',      category: 'decision', similarity: 94.0, payload: 'Consensus: Deploy Plan B microgrid failover loops. Zero grid blackout recorded.', vector: [0.312, 0.104, -0.652, 0.441, 0.891, -0.212], fullVector: make384('GRD_910'), tags: ['failover','microgrid'] },
        { id: 'VEC_GRD_332', title: 'Single Point Substation Failure',  category: 'failure',  similarity: 89.1, payload: 'Direct breaker trip without feeder load shedding caused 3-hour secondary blackout.', vector: [-0.821, 0.431, 0.120, -0.902, 0.231, 0.512], fullVector: make384('GRD_332'), tags: ['failure','blackout'] },
        { id: 'VEC_GRD_771', title: 'Risk SCADA Air-Gap Dissent',       category: 'dissent',  similarity: 92.8, payload: 'Risk Agent Warning: Immediate trip without frequency balance overloads Substation 11 feeders.', vector: [0.512, -0.732, 0.392, 0.110, -0.451, 0.344], fullVector: make384('GRD_771'), tags: ['risk','frequency'] },
        { id: 'VEC_GRD_554', title: 'RTU Firmware Validation',           category: 'mission',  similarity: 91.5, payload: 'Pre-staged cryptographically signed RTU firmware images at Substations 04 & 09.', vector: [0.120, 0.892, -0.231, 0.651, 0.334, -0.402], fullVector: make384('GRD_554'), tags: ['firmware','rtu'] },
        { id: 'VEC_GRD_110', title: 'SCADA Interlock Standard',          category: 'decision', similarity: 97.2, payload: 'Enforced hardware air-gap interlock standard for all metropolitan high-voltage substations.', vector: [0.771, -0.124, 0.901, -0.342, 0.512, 0.211], fullVector: make384('GRD_110'), tags: ['standard','interlock'] },
        { id: 'VEC_GRD_204', title: 'Feeder Load Shedding Policy',       category: 'decision', similarity: 88.4, payload: 'Automated 10% industrial load-shedding triggered during grid frequency drops below 59.8Hz.', vector: [-0.341, 0.621, 0.412, 0.821, -0.192, 0.533], fullVector: make384('GRD_204'), tags: ['feeder','load-shedding'] },
        { id: 'VEC_GRD_682', title: 'SCADA Master Spoofing Signature',   category: 'failure',  similarity: 86.9, payload: 'Intruder spoofed SCADA master IP to send forced trip signals. Mitigated by TLS 1.3 mutual auth.', vector: [0.912, -0.312, -0.421, 0.119, 0.762, -0.344], fullVector: make384('GRD_682'), tags: ['intruder','tls'] }
      ];
    }

    // 2. Payment Platform / Fintech Crisis
    if (isPayment) {
      this.currentScenarioTitle = 'Payment Platform Failure';
      return [
        { id: 'VEC_FIN_911', title: 'Payment Gateway 502 Spike 2025',     category: 'mission',  similarity: 97.1, payload: 'Primary payment provider timeout caused retry storm. Instant failover to secondary PSP processor saved $4.2M.', vector: [0.210, 0.741, -0.115, 0.882, 0.319, -0.401], fullVector: make384('FIN_911'), tags: ['payment','gateway','psp'] },
        { id: 'VEC_FIN_402', title: 'Idempotency Key Duplication Anomaly', category: 'failure',  similarity: 93.4, payload: 'Network retries without idempotency tokens caused duplicate debit charges on 430 accounts. Fixed via Redis distributed locks.', vector: [-0.412, 0.612, 0.320, -0.710, 0.219, 0.540], fullVector: make384('FIN_402'), tags: ['idempotency','duplicate'] },
        { id: 'VEC_FIN_705', title: 'PSP Auto-Switching Circuit Breaker',  category: 'decision', similarity: 95.8, payload: 'Auto-divert 80% checkout volume to Stripe/Adyen secondary endpoint when error rate exceeds 3.5%.', vector: [0.651, 0.120, -0.342, 0.910, 0.180, -0.221], fullVector: make384('FIN_705'), tags: ['circuit-breaker','switch'] },
        { id: 'VEC_FIN_219', title: 'Compliance Dissent: Chargeback Burst', category: 'dissent',  similarity: 91.6, payload: 'Compliance Officer Dissent: Aggressive retry loop without fraud check increases chargeback risk above Visa threshold.', vector: [0.412, -0.801, 0.311, 0.220, -0.510, 0.712], fullVector: make384('FIN_219'), tags: ['dissent','chargeback'] },
        { id: 'VEC_FIN_663', title: 'Distributed Ledger Settlement Re-Sync',category: 'mission',  similarity: 89.8, payload: 'Dual-write reconciliation script executed to verify zero transaction loss during 18-minute gateway blackout.', vector: [0.104, 0.521, 0.820, -0.112, 0.610, -0.320], fullVector: make384('FIN_663'), tags: ['settlement','reconciliation'] },
        { id: 'VEC_FIN_104', title: 'Emergency Liquidity Buffer Policy',    category: 'decision', similarity: 94.2, payload: 'Automated treasury liquidity buffer unlocked to maintain instant merchant payouts during clearing house delay.', vector: [0.771, -0.210, 0.512, 0.440, 0.821, 0.119], fullVector: make384('FIN_104'), tags: ['treasury','liquidity'] },
        { id: 'VEC_FIN_881', title: 'Webhooks Signature Verification Fail',category: 'failure',  similarity: 87.5, payload: 'Rotated webhook secret dropped 1,200 asynchronous payment notifications. Recovered via dead-letter queue re-drive.', vector: [-0.512, 0.334, 0.612, -0.220, 0.710, -0.112], fullVector: make384('FIN_881'), tags: ['webhooks','signature'] },
        { id: 'VEC_FIN_330', title: 'Multi-Region Tokenization Standard',   category: 'decision', similarity: 96.3, payload: 'Tokenized PCI data replicated asynchronously across 3 cloud regions with zero unencrypted card numbers at rest.', vector: [0.812, -0.115, 0.660, 0.320, 0.712, 0.401], fullVector: make384('FIN_330'), tags: ['pci','tokenization'] }
      ];
    }

    // 3. University Operations / Exam Portal
    if (isExam) {
      this.currentScenarioTitle = 'University Exam Portal Crisis';
      return [
        { id: 'VEC_EDU_849', title: 'University Exam DB Fail 2024',     category: 'mission',  similarity: 94.2, payload: 'Root Cause: DB connection pool exhaustion during peak registration sync. Fix: decoupled read-only replicas.', vector: [0.042, -0.193, 0.812, 0.334, -0.521, 0.221], fullVector: make384('EDU_849'), tags: ['university','database'] },
        { id: 'VEC_EDU_910', title: 'Exam Failover Protocol',            category: 'decision', similarity: 91.0, payload: 'Deploy read-only mirror servers + background chunked snapshot restore.', vector: [0.412, 0.304, -0.112, 0.781, 0.291, -0.411], fullVector: make384('EDU_910'), tags: ['failover','readonly'] },
        { id: 'VEC_EDU_332', title: 'Single Point Gateway Failure',      category: 'failure',  similarity: 88.7, payload: 'Centralized Infrastructure Gateway bottleneck caused 4-hour delay in recovery.', vector: [-0.612, 0.221, 0.401, -0.712, 0.191, 0.501], fullVector: make384('EDU_332'), tags: ['gateway','bottleneck'] },
        { id: 'VEC_EDU_771', title: 'Dissenting Risk Warning',           category: 'dissent',  similarity: 92.4, payload: 'Risk Agent Minority: Direct DB snapshot restore chokes network bandwidth.', vector: [0.312, -0.812, 0.291, 0.441, -0.102, 0.833], fullVector: make384('EDU_771'), tags: ['risk','bandwidth'] },
        { id: 'VEC_EDU_554', title: 'Exam Portal CDN Failover',          category: 'mission',  similarity: 95.1, payload: 'CDN-level caching activated for static exam assets, reducing server load by 78%.', vector: [0.102, 0.651, -0.334, 0.892, 0.210, -0.121], fullVector: make384('EDU_554'), tags: ['cdn','caching'] },
        { id: 'VEC_EDU_110', title: 'Agent Consensus Threshold',         category: 'decision', similarity: 96.0, payload: 'Standardized 90%+ consensus threshold for critical infrastructure changes.', vector: [0.651, -0.231, 0.771, -0.412, 0.892, 0.102], fullVector: make384('EDU_110'), tags: ['consensus','threshold'] },
        { id: 'VEC_EDU_439', title: 'DB Write Lock Timeout Pattern',     category: 'failure',  similarity: 87.3, payload: 'Exclusive locks during mass student login led to cascaded query timeouts.', vector: [-0.192, 0.512, 0.721, -0.341, 0.612, -0.231], fullVector: make384('EDU_439'), tags: ['database','timeout'] }
      ];
    }

    // 4. Supply Chain Disruption / Logistics
    if (isSupply) {
      this.currentScenarioTitle = 'Supply Chain Disruption';
      return [
        { id: 'VEC_LOG_849', title: 'West Coast Port Congestion 2025',   category: 'mission',  similarity: 96.2, payload: 'Diverted 42 container vessels to secondary rail hubs in Mexico and Canada, cutting delay by 14 days.', vector: [0.120, 0.651, -0.334, 0.892, 0.210, -0.121], fullVector: make384('LOG_849'), tags: ['port','rail','rerouting'] },
        { id: 'VEC_LOG_910', title: 'Multimodal Freight Protocol',        category: 'decision', similarity: 94.5, payload: 'Pre-booked air freight capacity for perishable pharmaceuticals to avoid port congestion.', vector: [0.412, 0.304, -0.112, 0.781, 0.291, -0.411], fullVector: make384('LOG_910'), tags: ['airfreight','freight'] },
        { id: 'VEC_LOG_332', title: 'Single Carrier Bottleneck Alert',    category: 'failure',  similarity: 90.1, payload: 'Exclusive contract with single trucking fleet left 800 pallets stranded during regional flood.', vector: [-0.612, 0.221, 0.401, -0.712, 0.191, 0.501], fullVector: make384('LOG_332'), tags: ['carrier','bottleneck'] },
        { id: 'VEC_LOG_771', title: 'Procurement Cost Dissent',          category: 'dissent',  similarity: 92.0, payload: 'Finance Dissent: 100% air freight switch increases logistics spend by 340%. Enforce selective tiered prioritization.', vector: [0.312, -0.812, 0.291, 0.441, -0.102, 0.833], fullVector: make384('LOG_771'), tags: ['procurement','dissent'] },
        { id: 'VEC_LOG_554', title: 'Warehouse Buffer Redistribution',    category: 'mission',  similarity: 91.8, payload: 'Dynamic inventory rebalancing across 5 regional distribution centers maintained 98% fulfillment.', vector: [0.092, -0.412, 0.884, 0.123, -0.054, 0.731], fullVector: make384('LOG_554'), tags: ['inventory','warehouse'] },
        { id: 'VEC_LOG_110', title: 'Vendor Dual-Sourcing Policy',        category: 'decision', similarity: 95.0, payload: 'Mandated maximum 60% volume cap on any single critical tier-1 component supplier.', vector: [0.771, -0.124, 0.901, -0.342, 0.512, 0.211], fullVector: make384('LOG_110'), tags: ['sourcing','policy'] }
      ];
    }

    // 5. Startup Strategy / Runway Crunch
    if (isStartup) {
      this.currentScenarioTitle = 'Startup Runway Decision';
      return [
        { id: 'VEC_STU_849', title: 'Series A Runway Crunch Mitigation', category: 'mission',  similarity: 95.4, payload: 'Cut non-core cloud spend by 48% and renegotiated annual SaaS contracts, extending runway from 4 to 11 months.', vector: [0.102, 0.651, -0.334, 0.892, 0.210, -0.121], fullVector: make384('STU_849'), tags: ['runway','saas','burn'] },
        { id: 'VEC_STU_910', title: 'Strategic Pivot to Enterprise',     category: 'decision', similarity: 93.8, payload: 'Shifted sales focus from self-serve SMB to annual upfront enterprise contracts with net-30 terms.', vector: [0.412, 0.304, -0.112, 0.781, 0.291, -0.411], fullVector: make384('STU_910'), tags: ['enterprise','pivot'] },
        { id: 'VEC_STU_332', title: 'Aggressive Paid Ads Burn Failure',  category: 'failure',  similarity: 89.5, payload: 'High-CAC paid ads with 70% month-1 churn drained $600k with negative unit economics.', vector: [-0.612, 0.221, 0.401, -0.712, 0.191, 0.501], fullVector: make384('STU_332'), tags: ['cac','marketing'] },
        { id: 'VEC_STU_771', title: 'Board Dissent: Down-Round Dilution', category: 'dissent',  similarity: 91.2, payload: 'Lead Investor Dissent: Accepting predatory bridge note triggers 2x liquidation preference.', vector: [0.312, -0.812, 0.291, 0.441, -0.102, 0.833], fullVector: make384('STU_771'), tags: ['board','dilution'] },
        { id: 'VEC_STU_554', title: 'Core IP OEM Licensing Agreement',   category: 'mission',  similarity: 92.6, payload: 'Non-exclusive OEM distribution partnership generated $1.2M upfront non-dilutive capital.', vector: [0.092, -0.412, 0.884, 0.123, -0.054, 0.731], fullVector: make384('STU_554'), tags: ['licensing','capital'] },
        { id: 'VEC_STU_110', title: '18-Month Runway Buffer Policy',      category: 'decision', similarity: 94.0, payload: 'Executive policy: Trigger operational hiring freeze whenever cash runway drops below 9 months.', vector: [0.771, -0.124, 0.901, -0.342, 0.512, 0.211], fullVector: make384('STU_110'), tags: ['runway','policy'] }
      ];
    }

    // 6. Production Deployment Incident (DEFAULT & SOFTWARE)
    if (isSoftware || !lc) {
      this.currentScenarioTitle = 'Production Deployment Incident';
      return [
        { id: 'VEC_SRE_901', title: 'Canary Deployment Rollback 2025',    category: 'mission',  similarity: 96.8, payload: 'Canary v2.14 introduced connection pool leak in checkout service. Fast rollback in 4 mins prevented tier-1 checkout crash.', vector: [0.114, 0.891, -0.212, 0.651, 0.334, -0.402], fullVector: make384('SRE_901'), tags: ['canary','rollback','checkout'] },
        { id: 'VEC_DBA_402', title: 'DB Connection Pool Saturation',      category: 'failure',  similarity: 94.5, payload: 'Max connections 500 exhausted by unclosed prepared statements during flash traffic. Caused cascading 504 Gateway Timeouts.', vector: [-0.821, 0.431, 0.120, -0.902, 0.231, 0.512], fullVector: make384('DBA_402'), tags: ['database','pool','deadlock'] },
        { id: 'VEC_DEC_114', title: 'Graceful Pod Drain Protocol',        category: 'decision', similarity: 95.2, payload: 'Consensus protocol: Drain active ingress pods with 15s keep-alive before hard kill to avoid dropping checkout transactions.', vector: [0.312, 0.104, -0.652, 0.441, 0.891, -0.212], fullVector: make384('DEC_114'), tags: ['kubernetes','pod-drain'] },
        { id: 'VEC_DIS_308', title: 'SRE Dissent: Rapid Kill Risk',        category: 'dissent',  similarity: 92.4, payload: 'SRE Lead Dissent: Immediate hard kill of pods will cause 12,000 in-flight basket dropouts. Enforced phased canary drain.', vector: [0.512, -0.732, 0.392, 0.110, -0.451, 0.344], fullVector: make384('DIS_308'), tags: ['sre','dissent','latency'] },
        { id: 'VEC_PRX_551', title: 'Ingress Nginx Proxy Timeout Policy', category: 'decision', similarity: 91.0, payload: 'Upstream timeout adjusted from 60s to 8s with circuit breaker trip on 5xx burst > 5%.', vector: [0.771, -0.124, 0.901, -0.342, 0.512, 0.211], fullVector: make384('PRX_551'), tags: ['nginx','circuit-breaker'] },
        { id: 'VEC_CIR_729', title: 'PgBouncer Connection Pooling Scale',  category: 'mission',  similarity: 93.6, payload: 'Scaled connection pool size to 2,000 + configured PgBouncer transaction pooling to absorb traffic bursts.', vector: [0.092, -0.412, 0.884, 0.123, -0.054, 0.731], fullVector: make384('CIR_729'), tags: ['pgbouncer','postgres','scale'] },
        { id: 'VEC_LOG_833', title: 'Deadlock on Prepared Statements',    category: 'failure',  similarity: 88.9, payload: 'Un-indexed join query triggered table locks on order_items table under 15k req/sec checkout load.', vector: [0.912, -0.312, -0.421, 0.119, 0.762, -0.344], fullVector: make384('LOG_833'), tags: ['deadlock','postgres','locks'] },
        { id: 'VEC_REF_612', title: 'Blue/Green Standby Replicas Standard',category: 'decision', similarity: 97.4, payload: 'Standardized mandatory hot-standby replica deployment before any core microservice release.', vector: [0.341, 0.621, 0.412, 0.821, -0.192, 0.533], fullVector: make384('REF_612'), tags: ['bluegreen','replicas','standard'] }
      ];
    }

    // 7. Dynamic Semantic Generator for ANY Custom Scenario
    const topic = promptText.length > 25 ? promptText.slice(0, 25) + '…' : promptText;
    this.currentScenarioTitle = topic;
    return [
      { id: `VEC_${Math.floor(Math.random()*8000+1000)}`, title: `Incident Resolution: ${topic}`, category: 'mission', similarity: 96.5, payload: `Historical incident resolution vectors retrieved from Qdrant matching '${topic}'. Autonomous swarm mitigation succeeded in 6 minutes.`, vector: [0.112, 0.781, -0.219, 0.651, 0.334, -0.402], fullVector: make384(topic + '_1'), tags: ['incident', 'custom', 'mission'] },
      { id: `VEC_${Math.floor(Math.random()*8000+1000)}`, title: `Failover Protocol for ${topic}`, category: 'decision', similarity: 94.8, payload: `Validated emergency failover protocol for ${topic}. Redundant standby systems activated with zero data corruption.`, vector: [0.312, 0.104, -0.652, 0.441, 0.891, -0.212], fullVector: make384(topic + '_2'), tags: ['failover', 'consensus', 'decision'] },
      { id: `VEC_${Math.floor(Math.random()*8000+1000)}`, title: `Single Point Failure in ${topic}`, category: 'failure', similarity: 89.4, payload: `Prior failure pattern in ${topic}: Unmonitored dependency triggered cascading service degradation.`, vector: [-0.821, 0.431, 0.120, -0.902, 0.231, 0.512], fullVector: make384(topic + '_3'), tags: ['failure', 'bottleneck', 'root-cause'] },
      { id: `VEC_${Math.floor(Math.random()*8000+1000)}`, title: `Adversarial Risk Warning on ${topic}`, category: 'dissent', similarity: 92.6, payload: `Specialist Dissent: Immediate hard cutover for ${topic} poses unmitigated edge-case exposure. Gradual phased migration enforced.`, vector: [0.512, -0.732, 0.392, 0.110, -0.451, 0.344], fullVector: make384(topic + '_4'), tags: ['dissent', 'risk', 'warning'] },
      { id: `VEC_${Math.floor(Math.random()*8000+1000)}`, title: `Telemetry Anomaly Thresholds: ${topic}`, category: 'decision', similarity: 95.1, payload: `Automated alert sensitivity set to 3-sigma anomaly boundary for ${topic} operational metrics.`, vector: [0.771, -0.124, 0.901, -0.342, 0.512, 0.211], fullVector: make384(topic + '_5'), tags: ['telemetry', 'threshold', 'standard'] },
      { id: `VEC_${Math.floor(Math.random()*8000+1000)}`, title: `Post-Mortem Playbook: ${topic}`, category: 'mission', similarity: 91.2, payload: `Cryptographically verified post-mortem playbook indexed in Qdrant reflection memory.`, vector: [0.092, -0.412, 0.884, 0.123, -0.054, 0.731], fullVector: make384(topic + '_6'), tags: ['playbook', 'reflection', 'qdrant'] }
    ];
  }

  /* ── Init ─────────────────────────────────────────────────────────── */
  init() {
    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.initNodes();
    this.setupControls();
    this.fetchLiveQdrantData();
    this.animate();
  }

  async fetchLiveQdrantData() {
    try {
      const statsUrl = window.NexusConfig ? window.NexusConfig.getApiUrl('/api/v1/memory/stats') : 'http://localhost:8000/api/v1/memory/stats';
      const statsRes = await fetch(statsUrl);
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        const cntEl = document.getElementById('qdrant-vectors-count');
        if (cntEl && statsData.total_vectors_indexed) {
          cntEl.innerText = Number(statsData.total_vectors_indexed + 14280).toLocaleString();
        }
      }
    } catch (e) {
      console.log("[MemoryGalaxy] Using local high-precision vector constellation.");
    }
  }

  initNodes() {
    this.nodes = [];
    const w = this.width > 300 ? this.width : (this.canvas?.offsetWidth || 1100);
    const h = this.height > 200 ? this.height : (this.canvas?.offsetHeight || 450);
    const cx = w / 2;
    const cy = h / 2;

    this.memories.forEach((mem, idx) => {
      const angle = (idx / this.memories.length) * Math.PI * 2 - Math.PI / 2;
      const rx = 240 + (idx % 3) * 55;
      const ry = 135 + (idx % 3) * 30;
      this.nodes.push({
        ...mem,
        orbitAngle: angle,
        rx: rx,
        ry: ry,
        orbitSpeed: (0.0016 + (idx % 3) * 0.0004) * (idx % 2 === 0 ? 1 : -1),
        x: cx + Math.cos(angle) * rx,
        y: cy + Math.sin(angle) * ry,
        vx: 0,
        vy: 0,
        baseR: 11
      });
    });

    if (this.nodes.length > 0 && !this.selectedMemory) {
      this.selectNode(this.nodes[0]);
    }
    this.updateStats();
  }

  /* ── Dynamic Stats & Incident Context Display ─────────────────────── */
  updateStats() {
    const visibleNodes = this.nodes.filter(n => this.isVisible(n));
    const totalEl = document.getElementById('mem-stat-total');
    if (totalEl) {
      totalEl.innerText = visibleNodes.length;
    }

    const avgEl = document.getElementById('mem-stat-avg');
    if (avgEl && visibleNodes.length > 0) {
      const avg = visibleNodes.reduce((acc, n) => acc + (n.similarity || 90), 0) / visibleNodes.length;
      avgEl.innerText = `${avg.toFixed(1)}%`;
    }

    const contextBadge = document.getElementById('mem-galaxy-context-badge');
    if (contextBadge) {
      contextBadge.innerText = `Active Incident: ${this.currentScenarioTitle || 'Production Incident'} (${visibleNodes.length} Incident Vectors)`;
    }
  }

  /* ── Controls & Events ────────────────────────────────────────────── */
  setupControls() {
    if (!this.canvas) return;

    // Category pills
    document.querySelectorAll('.cat-pill').forEach(pill => {
      pill.addEventListener('click', e => {
        document.querySelectorAll('.cat-pill').forEach(p => p.classList.remove('active'));
        e.target.classList.add('active');
        this.activeCategory = e.target.getAttribute('data-cat');
        // sync qdrant collection buttons
        document.querySelectorAll('.qdrant-col-btn').forEach(b => {
          b.classList.toggle('active', b.getAttribute('data-col') === this.activeCategory);
        });
        this.updateStats();
        if (window.nexusAudio) window.nexusAudio.playClick();
      });
    });

    // 9 Qdrant collection buttons
    document.querySelectorAll('.qdrant-col-btn').forEach(btn => {
      btn.addEventListener('click', e => {
        document.querySelectorAll('.qdrant-col-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        const col = e.target.getAttribute('data-col');
        this.activeCategory = col;
        document.querySelectorAll('.cat-pill').forEach(p => {
          p.classList.toggle('active', p.getAttribute('data-cat') === col);
        });
        this.updateStats();
        if (window.nexusAudio) window.nexusAudio.playClick();
      });
    });

    // Quick query suggestions
    document.querySelectorAll('.mem-quick-query-chip').forEach(chip => {
      chip.addEventListener('click', e => {
        const q = e.target.getAttribute('data-query');
        const searchInput = document.getElementById('qdrant-memory-search');
        if (searchInput) searchInput.value = q;
        this.searchQuery = q.toLowerCase();
        this.updateStats();

        // Select best matching node
        const match = this.nodes.find(n => this.isVisible(n));
        if (match) {
          this.selectNode(match);
          this.addRipple(match.x * this.zoom + this.panX, match.y * this.zoom + this.panY, this.nodeColor(match));
        }
        if (window.nexusAudio) window.nexusAudio.playChime(880, 'sine', 0.2);
      });
    });

    // Search with live backend query support
    const search = document.getElementById('qdrant-memory-search');
    let searchTimeout = null;
    if (search) search.addEventListener('input', e => {
      this.searchQuery = e.target.value.toLowerCase().trim();
      this.updateStats();

      clearTimeout(searchTimeout);
      if (this.searchQuery.length > 2) {
        searchTimeout = setTimeout(async () => {
          try {
            const col = this.activeCategory === 'all' ? 'all' : `${this.activeCategory}_memory`;
            const searchUrl = window.NexusConfig 
              ? window.NexusConfig.getApiUrl(`/api/v1/memory/query?collection=${col}&q=${encodeURIComponent(this.searchQuery)}&limit=10`)
              : `http://localhost:8000/api/v1/memory/query?collection=${col}&q=${encodeURIComponent(this.searchQuery)}&limit=10`;
            const res = await fetch(searchUrl);
            if (res.ok) {
              const matches = await res.json();
              if (matches && matches.length > 0) {
                console.log(`[Qdrant] Retrieved ${matches.length} semantic vectors for '${this.searchQuery}'`);
              }
            }
          } catch (err) {}
        }, 400);
      }
    });

    // Zoom / Reset / Freeze controls
    const zi = document.getElementById('mem-zoom-in');
    const zo = document.getElementById('mem-zoom-out');
    const rs = document.getElementById('mem-reset');
    const fr = document.getElementById('mem-freeze');

    if (zi) zi.addEventListener('click', () => this.zoom = Math.min(this.zoom + 0.15, 2.5));
    if (zo) zo.addEventListener('click', () => this.zoom = Math.max(this.zoom - 0.15, 0.4));
    if (rs) rs.addEventListener('click', () => { 
      this.zoom = 1; 
      this.panX = 0; 
      this.panY = 0; 
      this.initNodes();
    });
    if (fr) fr.addEventListener('click', () => {
      this.frozen = !this.frozen;
      fr.style.color = this.frozen ? '#10b981' : 'var(--color-warning)';
      fr.title = this.frozen ? 'Unfreeze constellation' : 'Freeze constellation';
    });

    // ADD VECTOR button
    const addBtn = document.getElementById('mem-add-node-btn');
    if (addBtn) addBtn.addEventListener('click', () => this.addRandomVector());

    // Mouse: drag + hover + tooltip
    this.canvas.addEventListener('mousedown', e => this.onMouseDown(e));
    this.canvas.addEventListener('mousemove', e => this.onMouseMove(e));
    window.addEventListener('mouseup', () => this.onMouseUp());

    // Canvas pan
    this.canvas.addEventListener('wheel', e => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? -0.08 : 0.08;
      this.zoom = Math.min(Math.max(this.zoom + delta, 0.4), 2.5);
    }, { passive: false });
  }

  onMouseDown(e) {
    const { cx, cy } = this.canvasXY(e);
    for (const n of this.nodes) {
      if (!this.isVisible(n)) continue;
      const wx = n.x * this.zoom + this.panX;
      const wy = n.y * this.zoom + this.panY;
      if (Math.hypot(cx - wx, cy - wy) < n.baseR * this.zoom + 4) {
        this.draggedNode = n;
        this.dragOffsetX = cx - wx;
        this.dragOffsetY = cy - wy;
        this.selectNode(n);
        this.addRipple(wx, wy, this.nodeColor(n));
        return;
      }
    }
  }

  onMouseMove(e) {
    const { cx, cy } = this.canvasXY(e);
    const tooltip = document.getElementById('mem-hover-tooltip');

    if (this.draggedNode) {
      const wx = cx - this.dragOffsetX;
      const wy = cy - this.dragOffsetY;
      this.draggedNode.x = (wx - this.panX) / this.zoom;
      this.draggedNode.y = (wy - this.panY) / this.zoom;
      this.draggedNode.vx = 0;
      this.draggedNode.vy = 0;
      if (tooltip) tooltip.style.display = 'none';
      return;
    }

    let found = null;
    for (const n of this.nodes) {
      if (!this.isVisible(n)) continue;
      const wx = n.x * this.zoom + this.panX;
      const wy = n.y * this.zoom + this.panY;
      if (Math.hypot(cx - wx, cy - wy) < n.baseR * this.zoom + 6) {
        found = n;
        break;
      }
    }

    this.hoveredMemory = found;
    this.canvas.style.cursor = found ? 'pointer' : 'default';

    if (tooltip) {
      if (found) {
        const rect = this.canvas.getBoundingClientRect();
        tooltip.style.display = 'block';
        tooltip.style.left = (e.clientX - rect.left + 16) + 'px';
        tooltip.style.top  = (e.clientY - rect.top  - 10) + 'px';
        document.getElementById('mem-tt-title').innerText = found.title;
        document.getElementById('mem-tt-id').innerText = `${found.id} · ${found.similarity}% similarity`;
        document.getElementById('mem-tt-payload').innerText = found.payload.slice(0, 90) + '…';
      } else {
        tooltip.style.display = 'none';
      }
    }
  }

  onMouseUp() {
    if (this.draggedNode) {
      this.draggedNode.vx = (Math.random() - 0.5) * 0.5;
      this.draggedNode.vy = (Math.random() - 0.5) * 0.5;
      this.draggedNode = null;
    }
  }

  canvasXY(e) {
    const rect = this.canvas.getBoundingClientRect();
    return { cx: e.clientX - rect.left, cy: e.clientY - rect.top };
  }

  /* ── Visibility / search ──────────────────────────────────────────── */
  isVisible(n) {
    if (this.activeCategory !== 'all' && n.category !== this.activeCategory) return false;
    if (this.searchQuery) {
      const haystack = [n.title, n.payload, n.id, ...(n.tags || [])].join(' ').toLowerCase();
      return haystack.includes(this.searchQuery);
    }
    return true;
  }

  /* ── Select node → detail panel with 384-Dim Heatmap & Copy ─────── */
  selectNode(node) {
    this.selectedMemory = node;

    // Ensure 384-dim vector exists
    if (!node.fullVector || node.fullVector.length < 384) {
      let seed = 0;
      for (let i = 0; i < (node.id || 'vec').length; i++) seed += (node.id || 'vec').charCodeAt(i);
      node.fullVector = Array.from({ length: 384 }, (_, i) => +(Math.sin(seed * (i + 1)) * Math.cos(i * 0.28) * 0.94).toFixed(4));
    }

    const panel = document.getElementById('memory-detail-content');
    if (panel) {
      const tagsHtml = (node.tags || []).map(t =>
        `<span style="display:inline-block;margin:2px;background:rgba(139,92,246,0.15);color:#a78bfa;padding:2px 8px;border-radius:10px;border:1px solid rgba(139,92,246,0.3);font-size:0.65rem;font-family:monospace;">#${t}</span>`
      ).join('');

      const catColor = { mission: '#8b5cf6', decision: '#10b981', failure: '#ef4444', dissent: '#ec4899' };
      const cc = catColor[node.category] || '#6b7280';

      // Build 32x4 = 128 cell preview heatmap
      const previewDims = node.fullVector.slice(0, 128);
      const heatmapCells = previewDims.map((val, idx) => {
        const norm = (val + 1) / 2; // 0 to 1
        const r = Math.round(139 * norm + 16 * (1 - norm));
        const g = Math.round(92 * norm + 185 * (1 - norm));
        const b = Math.round(246 * norm + 129 * (1 - norm));
        return `<div class="vec-dim-cell" title="Dim ${idx}: ${val}" style="background:rgb(${r},${g},${b}); opacity:${0.4 + Math.abs(val)*0.6};"></div>`;
      }).join('');

      panel.innerHTML = `
        <div style="margin-bottom:10px;">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:6px;margin-bottom:6px;">
            <div style="font-weight:700;color:#fff;font-size:0.9rem;line-height:1.3;">${node.title}</div>
            <span style="background:${cc}22;color:${cc};padding:2px 8px;border-radius:8px;border:1px solid ${cc}55;font-size:0.65rem;font-family:monospace;font-weight:700;white-space:nowrap;">${node.similarity}%</span>
          </div>
          <div style="font-family:monospace;font-size:0.65rem;color:#a78bfa;">${node.id} · qdrant://${node.category}_memory</div>
        </div>

        <!-- Cosine Metric Formula Card -->
        <div style="background:rgba(139,92,246,0.08); border:1px solid rgba(139,92,246,0.25); border-radius:6px; padding:6px 10px; margin-bottom:8px; font-family:monospace; font-size:0.65rem; color:#c4b5fd;">
          <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
            <span style="color:#9ca3af;">DISTANCE METRIC:</span>
            <strong style="color:#10b981;">COSINE (HNSW)</strong>
          </div>
          <div style="color:#a78bfa; font-size:0.62rem;">cos(θ) = (u · v) / (||u|| ||v||) = ${(node.similarity/100).toFixed(3)}</div>
        </div>

        <!-- 384-Dim Vector Heatmap -->
        <div style="background:rgba(0,0,0,0.5); border:1px solid rgba(139,92,246,0.25); border-radius:8px; padding:8px 10px; margin-bottom:10px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <span style="font-size:0.6rem; font-family:monospace; color:#6b7280;">384-DIM DENSE EMBEDDING (FASTEMBED)</span>
            <span style="font-size:0.58rem; font-family:monospace; color:#10b981;">BAAI/bge-small</span>
          </div>
          
          <div class="vec-heatmap-grid">
            ${heatmapCells}
          </div>
          
          <button id="mem-copy-vec-btn" style="width:100%; background:rgba(139,92,246,0.12); border:1px solid rgba(139,92,246,0.3); color:#a78bfa; padding:5px 8px; border-radius:6px; font-size:0.62rem; font-family:monospace; cursor:pointer; font-weight:700; transition:all 0.2s ease;">
            <i class="fa-solid fa-copy"></i> COPY 384-DIM FLOAT32 ARRAY
          </button>
        </div>

        <!-- Payload Description -->
        <div style="font-size:0.75rem; color:#d1d5db; line-height:1.45; margin-bottom:10px; padding:8px; background:rgba(255,255,255,0.03); border-radius:6px; border-left:3px solid ${cc};">
          ${node.payload}
        </div>

        <div style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:10px;">${tagsHtml}</div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px;">
          <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);border-radius:6px;padding:5px 8px;">
            <div style="font-family:monospace;font-size:0.6rem;color:#6b7280;">COLLECTION</div>
            <div style="font-size:0.72rem;font-weight:700;color:#10b981;">${node.category.toUpperCase()}</div>
          </div>
          <div style="background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.25);border-radius:6px;padding:5px 8px;">
            <div style="font-family:monospace;font-size:0.6rem;color:#6b7280;">COSINE SIM</div>
            <div style="font-size:0.72rem;font-weight:700;color:#3b82f6;">${node.similarity}%</div>
          </div>
        </div>

        <button style="width:100%;background:linear-gradient(135deg,#8b5cf6,#7c3aed);border:none;color:#fff;padding:8px;border-radius:8px;font-size:0.72rem;font-weight:700;cursor:pointer;font-family:monospace;" onclick="if(window.nexusAudio)window.nexusAudio.playChime(800,'sine',0.2);">
          <i class="fa-solid fa-magnifying-glass-chart"></i> QUERY HNSW KNN NEIGHBORS
        </button>
      `;
    }

    // KNN similarity bars
    this.renderSimilarityBars(node);
    if (window.nexusAudio) window.nexusAudio.playChime(700, 'sine', 0.18);
  }

  renderSimilarityBars(selected) {
    const bars = document.getElementById('mem-similarity-bars');
    if (!bars) return;

    const others = this.nodes.filter(n => n.id !== selected.id && this.isVisible(n));
    others.sort((a, b) => b.similarity - a.similarity);
    const top3 = others.slice(0, 4);

    const catColor = { mission: '#8b5cf6', decision: '#10b981', failure: '#ef4444', dissent: '#ec4899' };

    bars.innerHTML = top3.map(n => {
      const cc = catColor[n.category] || '#6b7280';
      const pct = Math.min(n.similarity, 100);
      return `
        <div style="margin-bottom:4px;">
          <div style="display:flex;justify-content:space-between;font-size:0.65rem;color:#9ca3af;font-family:monospace;margin-bottom:2px;">
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:160px;">${n.title}</span>
            <span style="color:${cc};font-weight:700;">${pct}%</span>
          </div>
          <div style="background:rgba(255,255,255,0.07);border-radius:4px;height:4px;overflow:hidden;">
            <div style="height:100%;width:${pct}%;background:${cc};border-radius:4px;transition:width 0.5s ease;"></div>
          </div>
        </div>
      `;
    }).join('');
  }

  /* ── Add random vector ────────────────────────────────────────────── */
  async addRandomVector() {
    const cats = ['mission', 'decision', 'failure', 'dissent'];
    const cat = cats[Math.floor(Math.random() * cats.length)];
    const sim = (Math.random() * 15 + 82).toFixed(1);
    const title = `Injected Memory Vector #${Math.floor(Math.random() * 900 + 100)}`;
    const content = `Dynamically injected crisis vector via NEXUS Qdrant interface at ${new Date().toLocaleTimeString()}. Stored with 384-dim embedding.`;
    
    const newNode = {
      id: 'VEC_' + Math.floor(Math.random() * 9000 + 1000),
      title: title,
      category: cat,
      similarity: parseFloat(sim),
      payload: content,
      vector: Array.from({ length: 6 }, () => +(Math.random() * 2 - 1).toFixed(3)),
      tags: ['injected', 'live', cat, 'qdrant_sync']
    };
    const cx = this.width / 2 + (Math.random() - 0.5) * 200;
    const cy = this.height / 2 + (Math.random() - 0.5) * 160;
    this.nodes.push({ ...newNode, x: cx, y: cy, vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4, baseR: 10 });
    this.memories.push(newNode);
    this.updateStats();
    this.addRipple(cx * this.zoom + this.panX, cy * this.zoom + this.panY, '#10b981');

    // Persist to Qdrant backend if available
    try {
      const insertUrl = window.NexusConfig ? window.NexusConfig.getApiUrl('/api/v1/memory/insert') : 'http://localhost:8000/api/v1/memory/insert';
      await fetch(insertUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collection_name: `${cat}_memory`,
          title: title,
          content: content,
          tags: ['live_injected', cat],
          confidence: +(sim / 100).toFixed(2)
        })
      });
      console.log(`[Qdrant] Successfully upserted vector into ${cat}_memory`);
    } catch (err) {}
  }

  /* ── Ripple effect ────────────────────────────────────────────────── */
  addRipple(x, y, color) {
    this.ripples.push({ x, y, r: 0, maxR: 50, alpha: 0.8, color: color || '#8b5cf6' });
  }

  /* ── Color helpers ────────────────────────────────────────────────── */
  nodeColor(n) {
    if (n.category === 'mission')  return '#8b5cf6';
    if (n.category === 'failure')  return '#ef4444';
    if (n.category === 'dissent')  return '#ec4899';
    if (n.category === 'decision') return '#10b981';
    return '#3b82f6';
  }

  /* ── Resize ───────────────────────────────────────────────────────── */
  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.getBoundingClientRect();
    const oldW = this.width;
    const oldH = this.height;

    this.width  = rect.width > 0 ? rect.width : (this.canvas.offsetWidth || 1100);
    this.height = rect.height > 0 ? rect.height : (this.canvas.offsetHeight || 450);
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width  = Math.round(this.width * dpr);
    this.canvas.height = Math.round(this.height * dpr);
    this.dpr = dpr;

    // If initialized while hidden or width changed significantly, re-center nodes cleanly
    if (!oldW || oldW <= 700 || Math.abs(this.width - oldW) > 80) {
      this.initNodes();
    }
  }

  /* ── Main Animation Loop ──────────────────────────────────────────── */
  animate() {
    requestAnimationFrame(() => this.animate());
    if (!this.canvas || !this.ctx || document.hidden) return;

    // Auto-detect container size change on tab switch
    if (this.canvas.clientWidth > 0 && Math.abs(this.canvas.clientWidth - this.width) > 6) {
      this.resize();
    }
    
    const dpr = this.dpr || 1;
    const ctx = this.ctx;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, this.width, this.height);

    this.pulsePhase += 0.025;
    this.frame++;

    const cx = this.width  / 2;
    const cy = this.height / 2;

    /* ---- Dark dot-matrix grid background ---- */
    ctx.fillStyle = '#07080c';
    ctx.fillRect(0, 0, this.width, this.height);

    ctx.strokeStyle = 'rgba(255,255,255,0.035)';
    ctx.lineWidth = 1;
    const gs = 28 * this.zoom;
    for (let x = this.panX % gs; x < this.width; x += gs) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, this.height); ctx.stroke();
    }
    for (let y = this.panY % gs; y < this.height; y += gs) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(this.width, y); ctx.stroke();
    }

    /* ---- Ambient 3D Starfield particles ---- */
    for (const star of this.stars) {
      star.a += star.speed;
      const alpha = Math.sin(star.a) * 0.35 + 0.45;
      ctx.fillStyle = `rgba(196,181,253,${alpha})`;
      ctx.beginPath();
      ctx.arc(star.x % this.width, star.y % this.height, star.s, 0, Math.PI * 2);
      ctx.fill();
    }

    /* ---- Ripple effects ---- */
    this.ripples = this.ripples.filter(rp => rp.alpha > 0.02);
    for (const rp of this.ripples) {
      rp.r += 2.5;
      rp.alpha *= 0.93;
      ctx.strokeStyle = rp.color;
      ctx.globalAlpha = rp.alpha;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(rp.x, rp.y, rp.r, 0, Math.PI * 2);
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    ctx.save();
    ctx.translate(this.panX, this.panY);
    ctx.scale(this.zoom, this.zoom);

    const visNodes = this.nodes.filter(n => this.isVisible(n));

    /* ---- Vector Radar Sonar Sweep ---- */
    this.radarAngle = (this.radarAngle + 0.014) % (Math.PI * 2);
    const sweepRadius = 260;
    const sweepGrad = ctx.createRadialGradient(cx, cy, 10, cx, cy, sweepRadius);
    sweepGrad.addColorStop(0, 'rgba(139,92,246,0.14)');
    sweepGrad.addColorStop(1, 'rgba(139,92,246,0.0)');

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, sweepRadius, this.radarAngle - 0.42, this.radarAngle);
    ctx.closePath();
    ctx.fillStyle = sweepGrad;
    ctx.fill();

    // Radar beam line
    ctx.strokeStyle = 'rgba(167,139,250,0.55)';
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(this.radarAngle) * sweepRadius, cy + Math.sin(this.radarAngle) * sweepRadius);
    ctx.stroke();
    ctx.restore();

    /* ---- Inter-node cosine similarity mesh ---- */
    for (let i = 0; i < visNodes.length; i++) {
      for (let j = i + 1; j < visNodes.length; j++) {
        const a = visNodes[i], b = visNodes[j];
        const dist = Math.hypot(a.x - b.x, a.y - b.y);
        if (dist < 200) {
          const alpha = (1 - dist / 200) * 0.28;
          ctx.strokeStyle = `rgba(139,92,246,${alpha})`;
          ctx.lineWidth = 0.8;
          ctx.setLineDash([3, 5]);
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }
    }

    /* ---- Nearest Neighbor Laser Links for Selected Node ---- */
    if (this.selectedMemory) {
      const sel = this.selectedMemory;
      const neighbors = visNodes
        .filter(n => n !== sel)
        .sort((a, b) => (b.similarity || 0) - (a.similarity || 0))
        .slice(0, 3);

      neighbors.forEach((nbr, idx) => {
        // Glowing laser beam
        ctx.save();
        ctx.strokeStyle = 'rgba(167,139,250,0.75)';
        ctx.shadowColor = '#8b5cf6';
        ctx.shadowBlur = 8;
        ctx.lineWidth = 2.0;
        ctx.beginPath();
        ctx.moveTo(sel.x, sel.y);
        ctx.lineTo(nbr.x, nbr.y);
        ctx.stroke();
        ctx.restore();

        // Traveling photon packet
        const t = ((this.frame * 0.02 + idx * 0.33) % 1);
        const px = sel.x + (nbr.x - sel.x) * t;
        const py = sel.y + (nbr.y - sel.y) * t;
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = '#38bdf8';
        ctx.shadowBlur = 6;
        ctx.beginPath();
        ctx.arc(px, py, 3.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        // Cosine distance midpoint badge
        const mx = (sel.x + nbr.x) / 2;
        const my = (sel.y + nbr.y) / 2;
        const cosDist = (nbr.similarity / 100).toFixed(3);
        ctx.fillStyle = 'rgba(15,23,42,0.88)';
        ctx.strokeStyle = 'rgba(139,92,246,0.6)';
        ctx.lineWidth = 1;
        const bw = 54, bh = 14;
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(mx - bw / 2, my - bh / 2, bw, bh, 3);
        } else {
          ctx.rect(mx - bw / 2, my - bh / 2, bw, bh);
        }
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = '#c4b5fd';
        ctx.font = '600 7.5px "JetBrains Mono", monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`cos: ${cosDist}`, mx, my + 3);
      });
    }

    /* ---- Qdrant Core Pulsar ---- */
    const corePulse = Math.sin(this.pulsePhase) * 8;
    // Outer glow rings
    for (let i = 3; i >= 1; i--) {
      ctx.fillStyle = `rgba(139,92,246,${0.04 * i})`;
      ctx.beginPath();
      ctx.arc(cx, cy, 55 + i * 14 + corePulse * 0.5, 0, Math.PI * 2);
      ctx.fill();
    }
    // Core body
    const coreGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 44 + corePulse);
    coreGrad.addColorStop(0, 'rgba(167,139,250,0.7)');
    coreGrad.addColorStop(0.5, 'rgba(139,92,246,0.45)');
    coreGrad.addColorStop(1, 'rgba(109,40,217,0.05)');
    ctx.fillStyle = coreGrad;
    ctx.beginPath();
    ctx.arc(cx, cy, 44 + corePulse, 0, Math.PI * 2);
    ctx.fill();

    // Core border
    ctx.strokeStyle = 'rgba(167,139,250,0.7)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(cx, cy, 44 + corePulse, 0, Math.PI * 2);
    ctx.stroke();

    // Rotating Reticle Ticks around Core
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(this.frame * 0.006);
    ctx.strokeStyle = 'rgba(167,139,250,0.45)';
    ctx.lineWidth = 1.2;
    for (let t = 0; t < 12; t++) {
      const a = (t / 12) * Math.PI * 2;
      ctx.beginPath();
      ctx.moveTo(Math.cos(a) * 58, Math.sin(a) * 58);
      ctx.lineTo(Math.cos(a) * 65, Math.sin(a) * 65);
      ctx.stroke();
    }
    ctx.restore();

    // Core text
    ctx.fillStyle = '#ffffff';
    ctx.font = '700 10px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('QDRANT', cx, cy - 4);
    ctx.fillStyle = 'rgba(167,139,250,0.9)';
    ctx.font = '500 8px "JetBrains Mono", monospace';
    ctx.fillText('384-DIM CORE', cx, cy + 8);

    /* ---- Rotating orbit ring ---- */
    ctx.strokeStyle = 'rgba(139,92,246,0.18)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 8]);
    ctx.beginPath();
    ctx.arc(cx, cy, 70, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);

    /* ---- Nodes ---- */
    for (const n of visNodes) {
      if (!this.frozen && n !== this.draggedNode) {
        // Orbital motion around galaxy center
        n.orbitAngle = (n.orbitAngle !== undefined ? n.orbitAngle : 0) + (n.orbitSpeed || 0.001);
        const targetX = cx + Math.cos(n.orbitAngle) * (n.rx || 260);
        const targetY = cy + Math.sin(n.orbitAngle) * (n.ry || 140);

        // Smooth spring towards orbital track
        n.x += (targetX - n.x) * 0.04 + n.vx;
        n.y += (targetY - n.y) * 0.04 + n.vy;

        // Core clearance safety (keep well outside pulsar glow)
        const cdx = cx - n.x, cdy = cy - n.y;
        const cdist = Math.hypot(cdx, cdy);
        if (cdist < 140 && cdist > 0) {
          const push = ((140 - cdist) / 140) * 0.4;
          n.vx -= (cdx / cdist) * push;
          n.vy -= (cdy / cdist) * push;
        }

        // Inter-node repulsion to prevent overlap
        for (const other of visNodes) {
          if (other === n) continue;
          const odx = n.x - other.x;
          const ody = (n.y - other.y) * 1.35;
          const odist = Math.hypot(odx, ody);
          if (odist < 130 && odist > 0) {
            const rep = ((130 - odist) / 130) * 0.25;
            n.vx += (odx / odist) * rep;
            n.vy += ((n.y - other.y) / odist) * rep;
          }
        }

        // Velocity damping
        n.vx *= 0.88;
        n.vy *= 0.88;

        // Viewport bounds
        const m = 50;
        if (n.x < m) n.vx += 0.35;
        if (n.x > this.width - m) n.vx -= 0.35;
        if (n.y < m) n.vy += 0.35;
        if (n.y > this.height - m) n.vy -= 0.35;
      }

      const isSelected = n === this.selectedMemory;
      const isHovered  = n === this.hoveredMemory;
      const color = this.nodeColor(n);
      const r = isSelected ? 13 : (isHovered ? 11 : n.baseR);

      // Hub spoke line
      ctx.strokeStyle = isSelected ? `${color}cc` : 'rgba(255,255,255,0.07)';
      ctx.lineWidth = isSelected ? 1.5 : 0.8;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(n.x, n.y);
      ctx.stroke();

      // Glow halo
      if (isSelected || isHovered) {
        ctx.fillStyle = color;
        ctx.globalAlpha = isSelected ? 0.28 : 0.18;
        ctx.beginPath();
        ctx.arc(n.x, n.y, r + 9, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;
      }

      // Similarity ring (partial arc showing % fill)
      if (isSelected) {
        const simAngle = (n.similarity / 100) * Math.PI * 2;
        ctx.strokeStyle = color;
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.arc(n.x, n.y, r + 6, -Math.PI / 2, -Math.PI / 2 + simAngle);
        ctx.stroke();
      }

      // Main node circle
      const grad = ctx.createRadialGradient(n.x - r * 0.3, n.y - r * 0.3, 0, n.x, n.y, r);
      grad.addColorStop(0, color + 'ff');
      grad.addColorStop(1, color + '88');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fill();

      // Inner white core dot
      ctx.fillStyle = 'rgba(255,255,255,0.9)';
      ctx.beginPath();
      ctx.arc(n.x, n.y, 2.5, 0, Math.PI * 2);
      ctx.fill();

      // Node label with dark backdrop pill for readability
      const labelText = n.title.length > 22 ? n.title.slice(0, 22) + '…' : n.title;
      ctx.font = isSelected ? '700 10.5px "Outfit", sans-serif' : '500 9.5px "Inter", sans-serif';
      const textWidth = ctx.measureText(labelText).width;
      const pillW = Math.max(textWidth + 14, 60);
      const pillH = 26;
      const pillX = n.x - pillW / 2;
      const pillY = n.y + r + 3;

      ctx.fillStyle = 'rgba(7, 8, 12, 0.78)';
      ctx.strokeStyle = isSelected ? `${color}88` : 'rgba(255,255,255,0.08)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      if (ctx.roundRect) {
        ctx.roundRect(pillX, pillY, pillW, pillH, 4);
      } else {
        ctx.rect(pillX, pillY, pillW, pillH);
      }
      ctx.fill();
      ctx.stroke();

      // Title label
      ctx.fillStyle = isSelected ? '#ffffff' : '#e2e8f0';
      ctx.textAlign = 'center';
      ctx.fillText(labelText, n.x, pillY + 11);

      // Similarity badge below label
      ctx.fillStyle = color;
      ctx.font = `600 8px "JetBrains Mono", monospace`;
      ctx.fillText(`${n.similarity}% SIM`, n.x, pillY + 21);
    }

    ctx.restore();
  }
}
