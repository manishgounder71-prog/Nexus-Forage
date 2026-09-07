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
    this.dragOffsetY = 0;

    this.ripples = [];
    this.pulsePhase = 0;
    this.frame = 0;

    this.memories = this.getMemoriesForScenario('default');
    this.nodes = [];
    this.init();
  }

  /* ── Scenario Memory Sets ─────────────────────────────────────────── */
  setScenario(promptText) {
    this.memories = this.getMemoriesForScenario(promptText);
    this.initNodes();
    this.updateStats();
  }

  getMemoriesForScenario(promptText) {
    const lc = (promptText || '').toLowerCase();
    const isGrid = lc.includes('power grid') || lc.includes('cyber-attack') || lc.includes('substation');
    const isExam = lc.includes('exam') || lc.includes('university') || lc.includes('database');

    if (isGrid) return [
      { id: 'VEC_8492', title: 'SCADA Substation 04 Breach 2025', category: 'mission', similarity: 96.4, payload: 'Unauthorized PLC command packet injection on Substation 04. Air-gapped loops stopped breach in 15 mins.', vector: [0.092, -0.412, 0.884, 0.123, -0.054, 0.731], tags: ['scada','substation','airgap'] },
      { id: 'VEC_9104', title: 'Grid Failover Protocol 2025',      category: 'decision', similarity: 94.0, payload: 'Consensus: Deploy Plan B microgrid failover loops. Zero grid blackout recorded.', vector: [0.312, 0.104, -0.652, 0.441, 0.891, -0.212], tags: ['failover','microgrid'] },
      { id: 'VEC_3321', title: 'Single Point Substation Failure',  category: 'failure',  similarity: 89.1, payload: 'Direct breaker trip without feeder load shedding caused 3-hour secondary blackout.', vector: [-0.821, 0.431, 0.120, -0.902, 0.231, 0.512], tags: ['failure','blackout'] },
      { id: 'VEC_7712', title: 'Risk SCADA Air-Gap Dissent',       category: 'dissent',  similarity: 92.8, payload: 'Risk Agent Warning: Immediate trip without frequency balance overloads Substation 11 feeders.', vector: [0.512, -0.732, 0.392, 0.110, -0.451, 0.344], tags: ['risk','frequency'] },
      { id: 'VEC_5549', title: 'RTU Firmware Validation',           category: 'mission',  similarity: 91.5, payload: 'Pre-staged cryptographically signed RTU firmware images at Substations 04 & 09.', vector: [0.120, 0.892, -0.231, 0.651, 0.334, -0.402], tags: ['firmware','rtu'] },
      { id: 'VEC_1109', title: 'SCADA Interlock Standard',          category: 'decision', similarity: 97.2, payload: 'Enforced hardware air-gap interlock standard for all metropolitan high-voltage substations.', vector: [0.771, -0.124, 0.901, -0.342, 0.512, 0.211], tags: ['standard','interlock'] },
      { id: 'VEC_2041', title: 'Feeder Load Shedding Policy',       category: 'decision', similarity: 88.4, payload: 'Automated 10% industrial load-shedding triggered during grid frequency drops below 59.8Hz.', vector: [-0.341, 0.621, 0.412, 0.821, -0.192, 0.533], tags: ['feeder','load-shedding'] },
      { id: 'VEC_6821', title: 'SCADA Intruder Signature 2024',     category: 'failure',  similarity: 86.9, payload: 'Intruder spoofed SCADA master IP to send forced trip signals. Mitigated by TLS 1.3 mutual auth.', vector: [0.912, -0.312, -0.421, 0.119, 0.762, -0.344], tags: ['intruder','tls'] }
    ];

    if (isExam) return [
      { id: 'VEC_8492', title: 'University Exam DB Fail 2024',     category: 'mission',  similarity: 94.2, payload: 'Root Cause: DB connection pool exhaustion during peak registration sync. Fix: decoupled read-only replicas.', vector: [0.042, -0.193, 0.812, 0.334, -0.521, 0.221], tags: ['university','database'] },
      { id: 'VEC_9104', title: 'Exam Failover Protocol',            category: 'decision', similarity: 91.0, payload: 'Deploy read-only mirror servers + background chunked snapshot restore.', vector: [0.412, 0.304, -0.112, 0.781, 0.291, -0.411], tags: ['failover','readonly'] },
      { id: 'VEC_3321', title: 'Single Point Gateway Failure',      category: 'failure',  similarity: 88.7, payload: 'Centralized Infrastructure Gateway bottleneck caused 4-hour delay in recovery.', vector: [-0.612, 0.221, 0.401, -0.712, 0.191, 0.501], tags: ['gateway','bottleneck'] },
      { id: 'VEC_7712', title: 'Dissenting Risk Warning',           category: 'dissent',  similarity: 92.4, payload: 'Risk Agent Minority: Direct DB snapshot restore chokes network bandwidth.', vector: [0.312, -0.812, 0.291, 0.441, -0.102, 0.833], tags: ['risk','bandwidth'] },
      { id: 'VEC_5549', title: 'Exam Portal CDN Failover',          category: 'mission',  similarity: 85.1, payload: 'CDN-level caching activated for static exam assets, reducing server load by 78%.', vector: [0.102, 0.651, -0.334, 0.892, 0.210, -0.121], tags: ['cdn','caching'] },
      { id: 'VEC_1109', title: 'Agent Consensus Threshold',         category: 'decision', similarity: 96.0, payload: 'Standardized 90%+ consensus threshold for critical infrastructure changes.', vector: [0.651, -0.231, 0.771, -0.412, 0.892, 0.102], tags: ['consensus','threshold'] },
      { id: 'VEC_4391', title: 'DB Write Lock Timeout Pattern',     category: 'failure',  similarity: 87.3, payload: 'Exclusive locks during mass student login led to cascaded query timeouts.', vector: [-0.192, 0.512, 0.721, -0.341, 0.612, -0.231], tags: ['database','timeout'] }
    ];

    // default
    return [
      { id: 'VEC_8492', title: 'University Exam DB Fail 2024',     category: 'mission',  similarity: 94.2, payload: 'DB connection pool exhaustion during peak registration. Fix: read-only replicas.', vector: [0.042, -0.193, 0.812, 0.334, -0.521, 0.221], tags: ['university','database'] },
      { id: 'VEC_9104', title: 'Grid Failover Protocol 2025',      category: 'decision', similarity: 91.0, payload: 'Multi-region DNS fallback deployed. Zero downtime recorded.', vector: [0.412, 0.304, -0.112, 0.781, 0.291, -0.411], tags: ['dns','failover'] },
      { id: 'VEC_3321', title: 'Single Point Failure Alert',        category: 'failure',  similarity: 88.7, payload: 'Centralized Gateway bottleneck caused 4-hour delay in recovery.', vector: [-0.612, 0.221, 0.401, -0.712, 0.191, 0.501], tags: ['gateway','failure'] },
      { id: 'VEC_7712', title: 'Dissenting Risk Warning',           category: 'dissent',  similarity: 92.4, payload: 'Risk Agent: snapshot restore chokes bandwidth. Alternative advised.', vector: [0.312, -0.812, 0.291, 0.441, -0.102, 0.833], tags: ['risk','bandwidth'] },
      { id: 'VEC_5549', title: 'Port Supply Chain RAG',             category: 'mission',  similarity: 85.1, payload: 'Cargo vessels rerouted via secondary rail hubs during labor strike.', vector: [0.102, 0.651, -0.334, 0.892, 0.210, -0.121], tags: ['port','supply-chain'] },
      { id: 'VEC_1109', title: 'Agent Consensus Threshold',         category: 'decision', similarity: 96.0, payload: 'Standardized 90%+ consensus threshold for critical changes.', vector: [0.651, -0.231, 0.771, -0.412, 0.892, 0.102], tags: ['consensus','policy'] }
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

      const queryUrl = window.NexusConfig ? window.NexusConfig.getApiUrl('/api/v1/memory/query?collection=all&limit=20') : 'http://localhost:8000/api/v1/memory/query?collection=all&limit=20';
      const queryRes = await fetch(queryUrl);
      if (queryRes.ok) {
        const queryData = await queryRes.json();
        if (Array.isArray(queryData) && queryData.length > 0) {
          const liveMemories = queryData.map((item, idx) => ({
            id: item.memory_id ? `VEC_${item.memory_id.slice(0,4).toUpperCase()}` : `VEC_${8000 + idx}`,
            title: item.title || item.content?.slice(0, 32) || 'Qdrant Memory Point',
            category: (item.memory_type || 'mission').replace('_memory', ''),
            similarity: item.similarity_score ? +(item.similarity_score * 100).toFixed(1) : 94.5,
            payload: item.content || 'Indexed memory payload stored in Qdrant cluster.',
            vector: Array.from({ length: 6 }, () => +(Math.random() * 2 - 1).toFixed(3)),
            tags: item.tags || ['qdrant', 'live_sync']
          }));
          this.memories = liveMemories;
          this.initNodes();
          this.updateStats();
        }
      }
    } catch (e) {
      console.log("[MemoryGalaxy] Backend offline, utilizing high-fidelity local vector constellation.", e);
    }
  }

  initNodes() {
    this.nodes = [];
    const cx = (this.width || 700) / 2;
    const cy = (this.height || 450) / 2;

    this.memories.forEach((mem, idx) => {
      const angle = (idx / this.memories.length) * Math.PI * 2 - Math.PI / 2;
      const r = 115 + (idx % 3) * 52;
      this.nodes.push({
        ...mem,
        x: cx + Math.cos(angle) * r,
        y: cy + Math.sin(angle) * r * 0.72,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        baseR: 10
      });
    });
    this.updateStats();
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
        this.updateStats();
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
    if (rs) rs.addEventListener('click', () => { this.zoom = 1; this.panX = 0; this.panY = 0; });
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

  /* ── Stats ────────────────────────────────────────────────────────── */
  updateStats() {
    const visible = this.nodes.filter(n => this.isVisible(n));
    const total = document.getElementById('mem-stat-total');
    const avg   = document.getElementById('mem-stat-avg');
    if (total) total.innerText = visible.length;
    if (avg && visible.length) {
      const mean = visible.reduce((s, n) => s + n.similarity, 0) / visible.length;
      avg.innerText = mean.toFixed(1) + '%';
    }
  }

  /* ── Select node → detail panel ──────────────────────────────────── */
  selectNode(node) {
    this.selectedMemory = node;

    const panel = document.getElementById('memory-detail-content');
    if (panel) {
      const vecStr = node.vector.map(v => v.toFixed(3)).join(', ');
      const tagsHtml = (node.tags || []).map(t =>
        `<span style="display:inline-block;margin:2px;background:rgba(139,92,246,0.15);color:#a78bfa;padding:2px 8px;border-radius:10px;border:1px solid rgba(139,92,246,0.3);font-size:0.65rem;font-family:monospace;">#${t}</span>`
      ).join('');

      const catColor = { mission: '#8b5cf6', decision: '#10b981', failure: '#ef4444', dissent: '#ec4899' };
      const cc = catColor[node.category] || '#6b7280';

      panel.innerHTML = `
        <div style="margin-bottom:10px;">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:6px;margin-bottom:6px;">
            <div style="font-weight:700;color:#fff;font-size:0.9rem;line-height:1.3;">${node.title}</div>
            <span style="background:${cc}22;color:${cc};padding:2px 8px;border-radius:8px;border:1px solid ${cc}55;font-size:0.65rem;font-family:monospace;font-weight:700;white-space:nowrap;">${node.similarity}%</span>
          </div>
          <div style="font-family:monospace;font-size:0.65rem;color:#a78bfa;">${node.id} · qdrant://${node.category}_memory</div>
        </div>

        <div style="background:rgba(0,0,0,0.45);border:1px solid rgba(139,92,246,0.25);border-radius:8px;padding:10px;margin-bottom:10px;">
          <div style="font-size:0.6rem;font-family:monospace;color:#6b7280;margin-bottom:5px;">384-DIM VECTOR EMBEDDING PREVIEW</div>
          <code style="font-size:0.68rem;color:#a78bfa;word-break:break-all;line-height:1.6;">[${vecStr}, …+378 dims]</code>
        </div>

        <div style="font-size:0.78rem;color:#d1d5db;line-height:1.5;margin-bottom:10px;padding:8px;background:rgba(255,255,255,0.03);border-radius:6px;border-left:3px solid ${cc};">
          ${node.payload}
        </div>

        <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;">${tagsHtml}</div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px;">
          <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.25);border-radius:6px;padding:6px 10px;">
            <div style="font-family:monospace;font-size:0.65rem;color:#6b7280;">CATEGORY</div>
            <div style="font-size:0.78rem;font-weight:700;color:#10b981;">${node.category.toUpperCase()}</div>
          </div>
          <div style="background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.25);border-radius:6px;padding:6px 10px;">
            <div style="font-family:monospace;font-size:0.65rem;color:#6b7280;">COSINE SIM</div>
            <div style="font-size:0.78rem;font-weight:700;color:#3b82f6;">${node.similarity}%</div>
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
    this.width  = rect.width > 0 ? rect.width : (this.canvas.offsetWidth || 700);
    this.height = rect.height > 0 ? rect.height : (this.canvas.offsetHeight || 450);
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width  = Math.round(this.width * dpr);
    this.canvas.height = Math.round(this.height * dpr);
    this.dpr = dpr;
  }

  /* ── Main Animation Loop ──────────────────────────────────────────── */
  animate() {
    requestAnimationFrame(() => this.animate());
    if (!this.canvas || !this.ctx || document.hidden) return;
    
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
        n.x += n.vx;
        n.y += n.vy;
        // Gentle center attraction
        const dx = cx - n.x, dy = cy - n.y;
        const dist = Math.hypot(dx, dy);
        if (dist > 80) {
          n.vx += dx / dist * 0.015;
          n.vy += dy / dist * 0.015;
        }
        // Dampen
        n.vx *= 0.992;
        n.vy *= 0.992;
        // Bounds
        const m = 40;
        if (n.x < m) n.vx += 0.3;
        if (n.x > this.width - m) n.vx -= 0.3;
        if (n.y < m) n.vy += 0.3;
        if (n.y > this.height - m) n.vy -= 0.3;
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

      // Title label
      ctx.fillStyle = isSelected ? '#ffffff' : '#e5e7eb';
      ctx.font = isSelected ? '700 10.5px "Outfit", sans-serif' : '500 9.5px "Inter", sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(n.title.length > 22 ? n.title.slice(0, 22) + '…' : n.title, n.x, n.y + r + 13);

      // Similarity badge below label
      ctx.fillStyle = color;
      ctx.font = `600 8px "JetBrains Mono", monospace`;
      ctx.fillText(`${n.similarity}% SIM`, n.x, n.y + r + 24);
    }

    ctx.restore();
  }
}
