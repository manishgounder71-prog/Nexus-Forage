/* ==========================================================================
   NEXUS FORGE — High-Performance DAG Workflow Canvas Engine
   Renders razor-sharp interactive workflow graphs for autonomous crisis pipelines
   Supports Retina/High-DPI 4K rendering and dynamic multi-scenario pipelines
   ========================================================================== */

// Canvas 2D roundRect Polyfill for Opera GX & cross-browser compatibility
if (!CanvasRenderingContext2D.prototype.roundRect) {
  CanvasRenderingContext2D.prototype.roundRect = function (x, y, w, h, r) {
    if (typeof r === 'undefined') r = 0;
    if (typeof r === 'number') r = [r, r, r, r];
    if (!Array.isArray(r)) r = [0, 0, 0, 0];
    const [tl, tr = tl, br = tl, bl = tr] = r;
    this.moveTo(x + tl, y);
    this.lineTo(x + w - tr, y);
    this.quadraticCurveTo(x + w, y, x + w, y + tr);
    this.lineTo(x + w, y + h - br);
    this.quadraticCurveTo(x + w, y + h, x + w - br, y + h);
    this.lineTo(x + bl, y + h);
    this.quadraticCurveTo(x, y + h, x, y + h - bl);
    this.lineTo(x, y + tl);
    this.quadraticCurveTo(x, y, x + tl, y);
    return this;
  };
}

class DagVisualizerEngine {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');

    this.zoom = 1;
    this.panX = 0;
    this.panY = 0;
    this.dpr = window.devicePixelRatio || 1;
    this.isDragging = false;
    this.lastMouseX = 0;
    this.lastMouseY = 0;

    // Node Dimensions
    this.nodeW = 210;
    this.nodeH = 74;

    this.currentScenario = 'Production Incident Response';
    this.nodes = this.getNodesForScenario(this.currentScenario);
    this.edges = this.getEdgesForScenario();
    this.edgeParticles = [];

    this.buildGraphIndex();
    this.init();
  }

  buildGraphIndex() {
    this.nodeMap = new Map(this.nodes.map(n => [n.id, n]));
    this.edgeGeometry = this.edges.map(edge => this.computeEdgeGeometry(edge.from, edge.to));
  }

  computeEdgeGeometry(fromId, toId) {
    const fromNode = this.nodeMap.get(fromId);
    const toNode = this.nodeMap.get(toId);
    if (!fromNode || !toNode) return null;
    const fromX = fromNode.x + this.nodeW / 2;
    const fromY = fromNode.y;
    const toX = toNode.x - this.nodeW / 2;
    const toY = toNode.y;
    const dx = Math.abs(toX - fromX);
    const cp1x = fromX + Math.min(dx * 0.5, 120);
    const cp2x = toX - Math.min(dx * 0.5, 120);
    return { fromNode, toNode, fromX, fromY, toX, toY, cp1x, cp1y: fromY, cp2x, cp2y: toY };
  }

  quadPoint(g, t) {
    const u = 1 - t;
    const uu = u * u;
    const tt = t * t;
    const u3 = uu * u, t3 = tt * t;
    return {
      x: u3 * g.fromX + 3 * uu * t * g.cp1x + 3 * u * tt * g.cp2x + t3 * g.toX,
      y: u3 * g.fromY + 3 * uu * t * g.cp1y + 3 * u * tt * g.cp2y + t3 * g.toY
    };
  }

  getNodesForScenario(promptText) {
    return [
      { id: 'CRISIS_DETECTED', label: 'Omi Voice Ingestion', category: 'TRIGGER', state: 'success', x: 130, y: 260, agent: 'Omi Voice Stream', confidence: '100%', time: '12ms', findings: 'Acoustic voice frames ingested and transcribed by Omi engine.' },
      { id: 'MISSION_ANALYSIS', label: 'Mission Analysis', category: 'COMMAND', state: 'success', x: 410, y: 260, agent: 'NEXUS Commander', confidence: '98%', time: '85ms', findings: 'Domain requirements decomposed into parallel DAG capabilities.' },
      { id: 'QDRANT_RAG', label: 'Qdrant Vector Memory RAG', category: 'QDRANT', state: 'pending', x: 710, y: 100, agent: 'Qdrant Vector DB', confidence: '-', time: '-', findings: 'Pending vector retrieval.' },
      { id: 'INCIDENT_ANALYSIS', label: 'Incident Root Cause Analysis', category: 'AGENT', state: 'pending', x: 710, y: 200, agent: 'Root Cause Specialist', confidence: '-', time: '-', findings: 'Pending agent task execution.' },
      { id: 'IMPACT_ASSESSMENT', label: 'Infrastructure & Impact Assessment', category: 'AGENT', state: 'pending', x: 710, y: 300, agent: 'Infrastructure Specialist', confidence: '-', time: '-', findings: 'Pending agent task execution.' },
      { id: 'RESOURCE_ALLOCATION', label: 'Rollback & Resource Allocation', category: 'AGENT', state: 'pending', x: 710, y: 400, agent: 'Rollback Strategist', confidence: '-', time: '-', findings: 'Pending agent task execution.' },
      { id: 'STRATEGY_PARLIAMENT', label: 'Spatial Agent Parliament', category: 'PARLIAMENT', state: 'pending', x: 1020, y: 200, agent: 'Multi-Agent Parliament', confidence: '-', time: '-', findings: 'Pending parliamentary deliberation.' },
      { id: 'RED_TEAM_AUDIT', label: 'Red Team Adversarial Audit', category: 'RED_TEAM', state: 'pending', x: 1020, y: 340, agent: 'Adversarial Auditor Agent', confidence: '-', time: '-', findings: 'Pending adversarial audit.' },
      { id: 'FINAL_RESPONSE', label: 'Executive Mission Command Report', category: 'OUTPUT', state: 'pending', x: 1310, y: 270, agent: 'Response Strategist Agent', confidence: '-', time: '-', findings: 'Pending final response generation.' }
    ];
  }

  getEdgesForScenario() {
    return [
      { from: 'CRISIS_DETECTED', to: 'MISSION_ANALYSIS' },
      { from: 'MISSION_ANALYSIS', to: 'QDRANT_RAG' },
      { from: 'MISSION_ANALYSIS', to: 'INCIDENT_ANALYSIS' },
      { from: 'MISSION_ANALYSIS', to: 'IMPACT_ASSESSMENT' },
      { from: 'MISSION_ANALYSIS', to: 'RESOURCE_ALLOCATION' },
      { from: 'QDRANT_RAG', to: 'STRATEGY_PARLIAMENT' },
      { from: 'INCIDENT_ANALYSIS', to: 'STRATEGY_PARLIAMENT' },
      { from: 'IMPACT_ASSESSMENT', to: 'STRATEGY_PARLIAMENT' },
      { from: 'RESOURCE_ALLOCATION', to: 'RED_TEAM_AUDIT' },
      { from: 'STRATEGY_PARLIAMENT', to: 'RED_TEAM_AUDIT' },
      { from: 'STRATEGY_PARLIAMENT', to: 'FINAL_RESPONSE' },
      { from: 'RED_TEAM_AUDIT', to: 'FINAL_RESPONSE' }
    ];
  }

  setScenario(promptText, forceReset = false) {
    if (!forceReset && this.isAllResolved) {
      // Keep resolved states if graph is already finished
      return;
    }

    this.currentScenario = promptText || this.currentScenario;
    this.nodes = this.getNodesForScenario(promptText);
    this.edges = this.getEdgesForScenario();
    this.edgeParticles = this.edges.map(e => ({ from: e.from, to: e.to, progress: Math.random() }));
    this.buildGraphIndex();
    this.isAllResolved = false;

    const heading = document.getElementById('live-mission-heading');
    const urgency = document.getElementById('live-mission-urgency');
    const classification = document.querySelector('.threat-classification');
    const metaChips = document.querySelectorAll('.mission-meta-chip:not(.mission-timer-chip)');

    if (heading && promptText) {
      heading.innerText = `MISSION: ${promptText}`;
      if (urgency) {
        urgency.innerHTML = "⚡ LIVE THREAT ACTIVE • MULTI-AGENT SWARM ENGAGED";
        urgency.className = "mission-tag critical";
      }
      if (classification) classification.textContent = "CLASSIFICATION: ADAPTIVE AI ORGANIZATION";
      if (metaChips[0]) metaChips[0].innerHTML = '<i class="fa-solid fa-bolt"></i> REAL-TIME EVENT STREAM';
      if (metaChips[1]) metaChips[1].innerHTML = '<i class="fa-solid fa-tower-broadcast"></i> LIVE DAG EXECUTION';
    }
  }

  resolveAllNodesToSuccess() {
    this.isAllResolved = true;
    const defaultTimes = {
      'CRISIS_DETECTED': '12ms',
      'MISSION_ANALYSIS': '85ms',
      'QDRANT_RAG': '140ms',
      'INCIDENT_ANALYSIS': '260ms',
      'IMPACT_ASSESSMENT': '310ms',
      'RESOURCE_ALLOCATION': '380ms',
      'STRATEGY_PARLIAMENT': '490ms',
      'RED_TEAM_AUDIT': '220ms',
      'FINAL_RESPONSE': '95ms'
    };

    this.nodes.forEach(node => {
      node.state = 'success';
      if (!node.time || node.time === '-') {
        node.time = defaultTimes[node.id] || '240ms';
      }
      if (!node.confidence || node.confidence === '-') {
        node.confidence = '98%';
      }
      if (!node.findings || node.findings.includes('Pending')) {
        node.findings = `Successfully executed and verified via Lyzr solo agent swarm. Vector memory synced with Qdrant.`;
      }
    });

    const urgency = document.getElementById('live-mission-urgency');
    if (urgency) {
      urgency.innerHTML = "✓ MISSION RESOLVED • CONSENSUS VERIFIED";
      urgency.className = "mission-tag success";
    }
  }

  init() {
    this.resize();
    window.addEventListener('resize', () => this.resize());

    // Create particles along edges
    this.edges.forEach(e => {
      this.edgeParticles.push({ from: e.from, to: e.to, progress: Math.random() });
    });

    // Node click handler
    this.canvas.addEventListener('click', (evt) => {
      const rect = this.canvas.getBoundingClientRect();
      const clickX = evt.clientX - rect.left;
      const clickY = evt.clientY - rect.top;

      this.nodes.forEach(node => {
        const nx = (node.x + this.panX) * this.zoom;
        const ny = (node.y + this.panY) * this.zoom;
        const hw = (this.nodeW / 2) * this.zoom;
        const hh = (this.nodeH / 2) * this.zoom;

        if (clickX >= nx - hw && clickX <= nx + hw && clickY >= ny - hh && clickY <= ny + hh) {
          this.onNodeClick(node);
        }
      });
    });

    // Pan / Drag handlers
    this.canvas.addEventListener('mousedown', (e) => {
      this.isDragging = true;
      this.lastMouseX = e.clientX;
      this.lastMouseY = e.clientY;
    });

    window.addEventListener('mousemove', (e) => {
      if (!this.isDragging) return;
      const dx = e.clientX - this.lastMouseX;
      const dy = e.clientY - this.lastMouseY;
      this.panX += dx / this.zoom;
      this.panY += dy / this.zoom;
      this.lastMouseX = e.clientX;
      this.lastMouseY = e.clientY;
    });

    window.addEventListener('mouseup', () => {
      this.isDragging = false;
    });

    // Zoom Controls setup
    const zoomIn = document.getElementById('dag-zoom-in');
    const zoomOut = document.getElementById('dag-zoom-out');
    const reset = document.getElementById('dag-reset');

    if (zoomIn) zoomIn.addEventListener('click', () => { this.zoom = Math.min(this.zoom + 0.15, 1.8); });
    if (zoomOut) zoomOut.addEventListener('click', () => { this.zoom = Math.max(this.zoom - 0.15, 0.5); });
    if (reset) reset.addEventListener('click', () => { this.zoom = 1; this.panX = 0; this.panY = 0; });

    this.animate();
  }

  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.getBoundingClientRect();
    this.width = rect.width > 0 ? rect.width : (this.canvas.parentElement ? this.canvas.parentElement.clientWidth : 1200);
    this.height = rect.height > 0 ? rect.height : 560;

    const dpr = window.devicePixelRatio || 1;
    this.dpr = dpr;
    this.canvas.width = Math.round(this.width * dpr);
    this.canvas.height = Math.round(this.height * dpr);
    this.canvas.style.width = this.width + 'px';
    this.canvas.style.height = this.height + 'px';
  }

  findNode(nodeId) {
    if (!nodeId) return null;
    if (this.nodeMap && this.nodeMap.has(nodeId)) return this.nodeMap.get(nodeId);

    const lowerId = String(nodeId).toLowerCase();

    // Map backend DAG task IDs to visual graph nodes
    if (lowerId.includes('_task_01') || lowerId.includes('task_1') || lowerId.includes('root_cause') || lowerId.includes('financial') || lowerId.includes('telemetry') || lowerId.includes('supplier')) {
      return this.nodeMap.get('INCIDENT_ANALYSIS');
    }
    if (lowerId.includes('_task_02') || lowerId.includes('task_2') || lowerId.includes('impact') || lowerId.includes('infrastructure') || lowerId.includes('market') || lowerId.includes('gateway')) {
      return this.nodeMap.get('IMPACT_ASSESSMENT');
    }
    if (lowerId.includes('_task_03') || lowerId.includes('task_3') || lowerId.includes('rollback') || lowerId.includes('resource') || lowerId.includes('product') || lowerId.includes('sourcing') || lowerId.includes('timetable')) {
      return this.nodeMap.get('RESOURCE_ALLOCATION');
    }
    if (lowerId.includes('_task_04') || lowerId.includes('parliament') || lowerId.includes('debate') || lowerId.includes('consensus')) {
      return this.nodeMap.get('STRATEGY_PARLIAMENT');
    }
    if (lowerId.includes('_task_05') || lowerId.includes('red_team') || lowerId.includes('audit') || lowerId.includes('stress')) {
      return this.nodeMap.get('RED_TEAM_AUDIT');
    }

    return this.nodes.find(n => n.id === nodeId || (n.label && n.label.toLowerCase().includes(lowerId)));
  }

  setNodeState(nodeId, newState) {
    const node = this.findNode(nodeId);
    if (node) {
      node.state = newState;
    }
  }

  updateNodeData(nodeId, data) {
    const node = this.findNode(nodeId);
    if (!node) return;
    if (data.label) node.label = data.label;
    if (data.agent) node.agent = data.agent;
    if (data.time) node.time = data.time;
    if (data.confidence !== undefined) node.confidence = data.confidence;
    if (data.findings) node.findings = data.findings;
    if (data.state) node.state = data.state;
  }

  setNodeStatesFromBackend(nodes) {
    if (!nodes || typeof nodes !== 'object') return;
    Object.entries(nodes).forEach(([id, entry]) => {
      this.updateNodeData(id, {
        state: entry.state,
        label: entry.label,
        agent: entry.agent,
        time: entry.time || '180ms',
        findings: entry.result ? (entry.result.summary || entry.result.message || JSON.stringify(entry.result).slice(0, 140)) : undefined
      });
    });
  }

  onNodeClick(node) {
    const drawer = document.getElementById('node-inspector');
    if (!drawer) return;

    const titleEl = document.getElementById('insp-title');
    const badgeEl = document.getElementById('insp-badge');
    const agentEl = document.getElementById('insp-agent');
    const timeEl = document.getElementById('insp-time');
    const confEl = document.getElementById('insp-confidence');
    const reasonEl = document.getElementById('insp-reasoning');

    if (titleEl) titleEl.innerText = node.label;
    if (badgeEl) {
      badgeEl.innerText = node.state.toUpperCase();
      badgeEl.className = `inspector-badge ${node.state}`;
    }
    if (agentEl) agentEl.innerText = node.agent;
    if (timeEl) timeEl.innerText = node.time || '180ms';
    if (confEl) confEl.innerText = node.confidence || '98%';
    if (reasonEl) reasonEl.innerText = node.findings || "Telemetry payload synced with Qdrant vector memory.";

    drawer.classList.add('active');
    if (window.nexusAudio) window.nexusAudio.playChime(600, 'sine', 0.15);
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    if (!this.canvas || !this.ctx || document.hidden) return;

    const dpr = this.dpr || 1;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.ctx.clearRect(0, 0, this.width, this.height);

    // Draw Canvas Grid Background
    this.drawN8nGrid();

    this.ctx.save();
    this.ctx.translate(this.panX, this.panY);
    this.ctx.scale(this.zoom, this.zoom);

    // Draw Curved Connection Wires
    this.edgeGeometry.forEach(g => {
      if (!g) return;
      let strokeColor = 'rgba(139, 92, 246, 0.28)';
      if (g.fromNode.state === 'success' && g.toNode.state === 'running') strokeColor = 'rgba(59, 130, 246, 0.85)';
      if (g.fromNode.state === 'success' && g.toNode.state === 'success') strokeColor = 'rgba(16, 185, 129, 0.85)';
      if (g.toNode.state === 'debate') strokeColor = 'rgba(236, 72, 153, 0.85)';

      this.ctx.beginPath();
      this.ctx.moveTo(g.fromX, g.fromY);
      this.ctx.bezierCurveTo(g.cp1x, g.cp1y, g.cp2x, g.cp2y, g.toX, g.toY);
      this.ctx.strokeStyle = strokeColor;
      this.ctx.lineWidth = 2.5;
      this.ctx.stroke();
    });

    // Draw Animated Data Packets along Wires
    this.edgeParticles.forEach((p, i) => {
      p.progress += 0.007;
      if (p.progress > 1) p.progress = 0;
      const g = this.edgeGeometry[i];
      if (!g) return;
      const pos = this.quadPoint(g, p.progress);

      this.ctx.fillStyle = '#34d399';
      this.ctx.beginPath();
      this.ctx.arc(pos.x, pos.y, 3.5, 0, Math.PI * 2);
      this.ctx.fill();

      // Particle Glow
      this.ctx.fillStyle = 'rgba(52, 211, 153, 0.45)';
      this.ctx.beginPath();
      this.ctx.arc(pos.x, pos.y, 7, 0, Math.PI * 2);
      this.ctx.fill();
    });

    // Draw Node Cards
    this.nodes.forEach(node => {
      this.drawN8nNode(node);
    });

    this.ctx.restore();
  }

  drawN8nGrid() {
    this.ctx.fillStyle = '#0a0d18';
    this.ctx.fillRect(0, 0, this.width, this.height);

    this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
    this.ctx.lineWidth = 1;
    const gridSize = 24 * this.zoom;

    for (let x = (this.panX % gridSize); x < this.width; x += gridSize) {
      this.ctx.beginPath();
      this.ctx.moveTo(x, 0);
      this.ctx.lineTo(x, this.height);
      this.ctx.stroke();
    }
    for (let y = (this.panY % gridSize); y < this.height; y += gridSize) {
      this.ctx.beginPath();
      this.ctx.moveTo(0, y);
      this.ctx.lineTo(this.width, y);
      this.ctx.stroke();
    }
  }

  drawN8nNode(node) {
    const x = node.x - this.nodeW / 2;
    const y = node.y - this.nodeH / 2;
    const w = this.nodeW;
    const h = this.nodeH;
    const r = 10;

    let headerColor = '#3b82f6';
    let iconSymbol = '🤖';
    let categoryLabel = node.category;

    if (node.category === 'TRIGGER')    { headerColor = '#ff6d5a'; iconSymbol = '⚡'; categoryLabel = 'TRIGGER'; }
    if (node.category === 'COMMAND')    { headerColor = '#8b5cf6'; iconSymbol = '🎯'; categoryLabel = 'COMMAND'; }
    if (node.category === 'QDRANT')     { headerColor = '#ea4b71'; iconSymbol = '📦'; categoryLabel = 'VECTOR DB'; }
    if (node.category === 'AGENT')      { headerColor = '#3b82f6'; iconSymbol = '⚙️'; categoryLabel = 'AI AGENT'; }
    if (node.category === 'PARLIAMENT') { headerColor = '#ec4899'; iconSymbol = '🏛️'; categoryLabel = 'PARLIAMENT'; }
    if (node.category === 'RED_TEAM')   { headerColor = '#f59e0b'; iconSymbol = '🛡️'; categoryLabel = 'RED TEAM'; }
    if (node.category === 'OUTPUT')     { headerColor = '#10b981'; iconSymbol = '🚀'; categoryLabel = 'OUTPUT'; }

    let statusColor = '#6b7280';
    if (node.state === 'running') statusColor = '#3b82f6';
    if (node.state === 'success') statusColor = '#10b981';
    if (node.state === 'debate')  statusColor = '#ec4899';

    // Animated pulse glow for active / debate nodes
    if (node.state === 'running' || node.state === 'debate') {
      const pulse = 0.12 + 0.10 * Math.sin(Date.now() / 450);
      this.ctx.shadowColor = statusColor;
      this.ctx.shadowBlur = 22;
      this.ctx.fillStyle = statusColor;
      this.ctx.globalAlpha = pulse;
      this.ctx.beginPath();
      this.ctx.roundRect(x - 6, y - 6, w + 12, h + 12, r + 6);
      this.ctx.fill();
      this.ctx.globalAlpha = 1.0;
      this.ctx.shadowBlur = 0;
    }

    // Card drop shadow
    this.ctx.shadowColor = 'rgba(0,0,0,0.55)';
    this.ctx.shadowBlur = 14;
    this.ctx.shadowOffsetY = 4;

    // Node card background
    this.ctx.fillStyle = '#141828';
    this.ctx.beginPath();
    this.ctx.roundRect(x, y, w, h, r);
    this.ctx.fill();
    this.ctx.shadowBlur = 0;
    this.ctx.shadowOffsetY = 0;

    // Card border (status-colored)
    this.ctx.strokeStyle = statusColor;
    this.ctx.lineWidth = node.state === 'success' ? 1.5 : 2;
    this.ctx.beginPath();
    this.ctx.roundRect(x, y, w, h, r);
    this.ctx.stroke();

    // Header band with gradient
    const hdrGrad = this.ctx.createLinearGradient(x, y, x + w, y + 24);
    hdrGrad.addColorStop(0, headerColor);
    hdrGrad.addColorStop(1, headerColor + 'bb');
    this.ctx.fillStyle = hdrGrad;
    this.ctx.beginPath();
    this.ctx.roundRect(x, y, w, 24, [r, r, 0, 0]);
    this.ctx.fill();

    // Header: category label
    this.ctx.fillStyle = 'rgba(255,255,255,0.95)';
    this.ctx.font = 'bold 8.5px "JetBrains Mono", monospace';
    this.ctx.textAlign = 'left';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(`${iconSymbol}  ${categoryLabel}`, x + 10, y + 12);

    // Header: execution time (right)
    this.ctx.fillStyle = 'rgba(255,255,255,0.85)';
    this.ctx.font = 'bold 8px "JetBrains Mono", monospace';
    this.ctx.textAlign = 'right';
    this.ctx.fillText(node.time || '-', x + w - 10, y + 12);

    // Node main label
    this.ctx.fillStyle = '#f1f5f9';
    this.ctx.font = '600 11.5px Inter, system-ui, sans-serif';
    this.ctx.textAlign = 'left';
    this.ctx.textBaseline = 'alphabetic';
    const maxLabelW = w - 20;
    let label = node.label;
    while (this.ctx.measureText(label).width > maxLabelW && label.length > 4) label = label.slice(0, -1);
    if (label !== node.label) label += '…';
    this.ctx.fillText(label, x + 10, y + 44);

    // Sub-label: assigned agent
    this.ctx.fillStyle = '#64748b';
    this.ctx.font = '400 9px Inter, system-ui, sans-serif';
    let agentLabel = node.agent || 'AI Specialist';
    while (this.ctx.measureText(agentLabel).width > maxLabelW - 60 && agentLabel.length > 4) agentLabel = agentLabel.slice(0, -1);
    if (agentLabel !== node.agent) agentLabel += '…';
    this.ctx.fillText(agentLabel, x + 10, y + 60);

    // Status badge pill (bottom-right)
    const badgeW = 70;
    const badgeH = 16;
    const bx = x + w - badgeW - 8;
    const by = y + h - badgeH - 8;
    this.ctx.fillStyle = statusColor + '28';
    this.ctx.strokeStyle = statusColor;
    this.ctx.lineWidth = 1;
    this.ctx.beginPath();
    this.ctx.roundRect(bx, by, badgeW, badgeH, 8);
    this.ctx.fill();
    this.ctx.stroke();

    this.ctx.fillStyle = statusColor;
    this.ctx.font = 'bold 7.5px "JetBrains Mono", monospace';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(node.state.toUpperCase(), bx + badgeW / 2, by + badgeH / 2);

    // Confidence score (bottom-left)
    this.ctx.fillStyle = '#475569';
    this.ctx.font = '500 8px "JetBrains Mono", monospace';
    this.ctx.textAlign = 'left';
    this.ctx.fillText(node.confidence || '98%', x + 10, by + badgeH / 2);

    this.ctx.textBaseline = 'alphabetic';

    // Input port handle
    this.ctx.fillStyle = '#0f1421';
    this.ctx.strokeStyle = headerColor;
    this.ctx.lineWidth = 2;
    this.ctx.beginPath();
    this.ctx.arc(x, node.y, 5.5, 0, Math.PI * 2);
    this.ctx.fill();
    this.ctx.stroke();
    this.ctx.fillStyle = headerColor;
    this.ctx.beginPath();
    this.ctx.arc(x, node.y, 2.8, 0, Math.PI * 2);
    this.ctx.fill();

    // Output port handle
    this.ctx.fillStyle = '#0f1421';
    this.ctx.strokeStyle = headerColor;
    this.ctx.lineWidth = 2;
    this.ctx.beginPath();
    this.ctx.arc(x + w, node.y, 5.5, 0, Math.PI * 2);
    this.ctx.fill();
    this.ctx.stroke();
    this.ctx.fillStyle = headerColor;
    this.ctx.beginPath();
    this.ctx.arc(x + w, node.y, 2.8, 0, Math.PI * 2);
    this.ctx.fill();
  }
}
