/**
 * connector-center.js — Organization Connector Platform & NEXUS CONNECT frontend.
 *
 * Supports:
 *  - Dynamic multi-tenant organization switching
 *  - Organization onboarding wizard (zero-code webhook generation)
 *  - Live Ingestion Endpoint & HMAC credential inspector
 *  - Connected systems & catalog
 *  - Real-time Incident Command Center & Live WebSocket event stream
 *  - Server-side Human Approval gate (Approve / Reject actions)
 */
(function () {
  'use strict';

  function getApiBase() {
    return window.NexusConfig ? window.NexusConfig.getApiUrl('/api/v1') : 'http://localhost:8000/api/v1';
  }
  let currentOrgId = 'org_acme_digital';
  let currentPublicId = 'org_acme_digital_pub';
  let currentOrgName = 'ACME DIGITAL';

  let ws = null;
  let reconnectTimer = null;

  // ── Public hooks called from app.js ───────────────────────────
  window.connectorCenter = {
    render: render,
    connect: connect,
    disconnect: disconnect,
    setOrg: setOrganization,
  };

  // ── View render hook (called on nav switch) ───────────────────
  async function render() {
    await loadOrganizations();
    await loadConnectors();
    await loadCatalog();
    await loadIncidents();
    await loadApprovals();
    await refreshKpis();
  }

  // ── API helpers ───────────────────────────────────────────────
  async function api(path, options) {
    const res = await fetch(getApiBase() + path, options);
    if (!res.ok) {
      let errText = `HTTP ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson.detail) errText = errJson.detail;
      } catch (_) {}
      throw new Error(errText);
    }
    return res.json();
  }

  // ── Organization Switcher ─────────────────────────────────────
  async function loadOrganizations() {
    const select = document.getElementById('cc-org-select');
    if (!select) return;
    try {
      const { organizations } = await api('/organizations');
      if (organizations && organizations.length) {
        select.innerHTML = organizations.map(o => `
          <option value="${esc(o.id)}" data-public="${esc(o.public_id || o.id)}" ${o.id === currentOrgId ? 'selected' : ''}>
            ${esc(o.name)} (${esc(o.slug)})
          </option>
        `).join('');

        const active = organizations.find(o => o.id === currentOrgId) || organizations[0];
        if (active) {
          currentOrgId = active.id;
          currentPublicId = active.public_id || active.id;
          currentOrgName = active.name;
          const badgeName = document.getElementById('cc-org-name');
          if (badgeName) badgeName.innerText = currentOrgName;
        }
      }
    } catch (_) {}
  }

  function setOrganization(orgId) {
    currentOrgId = orgId;
    disconnect();
    connect();
    render();
  }

  // ── KPI strip ─────────────────────────────────────────────────
  async function refreshKpis() {
    const ids = ['cc-kpi-connectors', 'cc-kpi-events', 'cc-kpi-incidents', 'cc-kpi-crises', 'cc-kpi-missions'];
    ids.forEach(id => { const el = document.getElementById(id); if (el) el.textContent = '–'; });
    try {
      const conn = await api(`/organizations/${currentOrgId}/connectors`);
      setText('cc-kpi-connectors', conn.count || 0);
    } catch (_) {}
    try {
      const ev = await api(`/organizations/${currentOrgId}/events?limit=1`);
      setText('cc-kpi-events', ev.count || 0);
    } catch (_) { setText('cc-kpi-events', '0'); }
    try {
      const inc = await api(`/organizations/${currentOrgId}/incidents`);
      setText('cc-kpi-incidents', inc.count || 0);
      setText('cc-kpi-crises', (inc.incidents || []).filter(i => i.crisis && i.crisis.is_crisis).length);
    } catch (_) {}
    try {
      const mis = await api(`/organizations/${currentOrgId}/missions`);
      setText('cc-kpi-missions', mis.count || 0);
    } catch (_) {}
  }

  // ── Connectors ────────────────────────────────────────────────
  async function loadConnectors() {
    const box = document.getElementById('cc-connector-list');
    if (!box) return;
    try {
      const { connectors } = await api(`/organizations/${currentOrgId}/connectors`);
      if (!connectors.length) {
        box.innerHTML = `<div class="cc-empty">No connectors registered yet. Use "New Workspace" or connect systems.</div>`;
        return;
      }
      box.innerHTML = connectors.map(c => `
        <div class="cc-connector-row">
          <div class="cc-conn-icon"><i class="fa-solid ${iconFor(c.connector_type)}"></i></div>
          <div class="cc-conn-body">
            <div class="cc-conn-name">${esc(c.name)} <span class="cc-type-chip">${esc(c.connector_type)}</span></div>
            <div class="cc-conn-meta">${c.events_count || 0} events · last ${c.last_event_at ? fmtAgo(c.last_event_at) : 'never'}</div>
          </div>
          <div class="cc-conn-status-pill ${c.status === 'CONNECTED' ? 'ok' : ''}">${esc(c.status)}</div>
        </div>`).join('');
    } catch (e) {
      box.innerHTML = `<div class="cc-empty">Backend unreachable: ${esc(e.message)}. Ensure backend is running or configured in Settings.</div>`;
    }
  }

  function iconFor(type) {
    return { github: 'fa-brands fa-github', slack: 'fa-brands fa-slack', monitoring: 'fa-chart-line',
             webhook: 'fa-magnet', custom_api: 'fa-code', support: 'fa-headset' }[type] || 'fa-plug';
  }

  // ── Catalog ───────────────────────────────────────────────────
  async function loadCatalog() {
    const box = document.getElementById('cc-catalog-list');
    if (!box) return;
    try {
      const { catalog } = await api('/platform/catalog');
      box.innerHTML = catalog.map(c => `
        <div class="cc-catalog-item" title="${esc(c.description || '')}">
          <i class="fa-solid ${iconFor(c.type)}"></i>
          <span>${esc(c.display_name)}</span>
          <code>${esc(c.auth_type.replace('_', ' '))}</code>
        </div>`).join('');
    } catch (_) {
      box.innerHTML = `<div class="cc-empty">Catalog unavailable.</div>`;
    }
  }

  // ── Incidents ─────────────────────────────────────────────────
  async function loadIncidents() {
    const box = document.getElementById('cc-incident-list');
    if (!box) return;
    try {
      const { incidents } = await api(`/organizations/${currentOrgId}/incidents`);
      if (!incidents || !incidents.length) {
        box.innerHTML = `<div class="cc-empty">No active incidents. Launch demo crisis or send an ingestion event.</div>`;
        return;
      }
      box.innerHTML = incidents.map(i => `
        <div class="cc-incident-card ${i.crisis && i.crisis.is_crisis ? 'crisis' : ''}">
          <div class="cc-inc-head">
            <span class="cc-sev sev-${esc(i.severity)}">${esc((i.severity || 'info').toUpperCase())}</span>
            <span class="cc-conf">${Math.round((i.confidence || 0) * 100)}% CONFIDENCE</span>
            ${i.mission_id ? `<span class="cc-mission-chip"><i class="fa-solid fa-robot"></i> ${esc(i.mission_id.slice(0, 14))}</span>` : ''}
          </div>
          <div class="cc-inc-title">${esc(i.title || i.summary || 'Operational Disruption')}</div>
          <div class="cc-inc-events">${(i.event_types || []).map(t => `<code>${esc(t)}</code>`).join(' ')}</div>
          <div class="cc-inc-action">
            <button class="cc-act" data-inc="${esc(i.id)}" data-act="${i.status === 'RESOLVED' ? 'escalate' : 'resolve'}">
              ${i.status === 'RESOLVED' ? 'Re-open' : 'Resolve'}
            </button>
            ${i.mission_id ? '' : `<button class="cc-act gold" data-inc="${esc(i.id)}" data-act="run_mission"><i class="fa-solid fa-robot"></i> Launch Mission</button>`}
            <span class="cc-inc-status">${esc(i.status)}</span>
          </div>
        </div>`).join('');

      box.querySelectorAll('.cc-act').forEach(btn => {
        btn.addEventListener('click', () => commandAction(btn.dataset.inc, btn.dataset.act));
      });
    } catch (e) {
      box.innerHTML = `<div class="cc-empty">Failed to load incidents: ${esc(e.message)}</div>`;
    }
  }

  async function commandAction(incidentId, action) {
    try {
      await api(`/platform/orgs/${currentOrgId}/incidents/${incidentId}/command`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      });
      await loadIncidents();
      await refreshKpis();
    } catch (e) {
      alert('Command failed: ' + e.message);
    }
  }

  // ── Human Approvals ───────────────────────────────────────────
  async function loadApprovals() {
    const box = document.getElementById('cc-approvals-list');
    if (!box) return;
    try {
      const { approvals } = await api(`/organizations/${currentOrgId}/approvals?status=PENDING`);
      if (!approvals || !approvals.length) {
        box.innerHTML = `<div class="cc-empty">No pending high-risk approvals. Automated policy active.</div>`;
        return;
      }
      box.innerHTML = approvals.map(a => `
        <div class="cc-approval-card risk-${esc((a.risk_level || 'high').toLowerCase())}">
          <div class="cc-appr-head">
            <span class="cc-appr-risk risk-${esc((a.risk_level || 'high').toLowerCase())}">${esc(a.risk_level)} RISK</span>
            <span class="cc-appr-agent"><i class="fa-solid fa-robot"></i> ${esc(a.agent_name)}</span>
          </div>
          <div class="cc-appr-action">${esc(a.action_name.replace(/_/g, ' ').toUpperCase())}</div>
          <div class="cc-appr-reason">${esc(a.reason || 'High-risk operational mitigation proposed.')}</div>
          <div class="cc-appr-btns">
            <button class="cc-btn-approve" data-id="${esc(a.id)}"><i class="fa-solid fa-check"></i> APPROVE & EXECUTE</button>
            <button class="cc-btn-reject" data-id="${esc(a.id)}"><i class="fa-solid fa-xmark"></i> REJECT</button>
          </div>
        </div>
      `).join('');

      box.querySelectorAll('.cc-btn-approve').forEach(btn => {
        btn.addEventListener('click', () => approveAction(btn.dataset.id));
      });
      box.querySelectorAll('.cc-btn-reject').forEach(btn => {
        btn.addEventListener('click', () => rejectAction(btn.dataset.id));
      });
    } catch (_) {
      box.innerHTML = `<div class="cc-empty">No approvals pending.</div>`;
    }
  }

  async function approveAction(approvalId) {
    try {
      const res = await api(`/organizations/${currentOrgId}/approvals/${approvalId}/approve`, { method: 'POST' });
      pushEvent('info', 'APPROVAL', `Action ${approvalId} approved and executed successfully`);
      await loadApprovals();
      await refreshKpis();
    } catch (e) {
      alert('Approval failed: ' + e.message);
    }
  }

  async function rejectAction(approvalId) {
    try {
      await api(`/organizations/${currentOrgId}/approvals/${approvalId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'Operator rejected action.' })
      });
      pushEvent('warning', 'REJECTION', `Action ${approvalId} was rejected by operator`);
      await loadApprovals();
    } catch (e) {
      alert('Rejection failed: ' + e.message);
    }
  }

  // ── Live event stream ─────────────────────────────────────────
  function connect() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;
    setWsStatus('CONNECTING');
    const wsUrl = window.NexusConfig 
      ? window.NexusConfig.getWsUrl(`/ws/organizations/${currentOrgId}/events`)
      : `ws://localhost:8000/ws/organizations/${currentOrgId}/events`;
    ws = new WebSocket(wsUrl);
    ws.onopen = () => { setWsStatus('LIVE'); pushEvent('info', 'SYSTEM', `Connected to organization stream (${currentOrgId})`); };
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.topic && msg.topic.endsWith('.events')) {
          const m = msg.message;
          pushEvent(m.severity, m.event_type, `[${m.resource || 'sys'}] ${m.summary || ''}`);
        } else if (msg.topic && msg.topic.endsWith('.incidents')) {
          pushEvent('high', 'INCIDENT', (msg.text || msg.title || 'Incident') + ' — ' + (msg.message?.title || ''));
          loadIncidents();
          refreshKpis();
        } else if (msg.topic && msg.topic.endsWith('.crises')) {
          pushEvent('critical', 'CRISIS', 'CRISIS ESCALATED → Autonomous NEXUS mission initiated');
          loadIncidents();
          refreshKpis();
        } else if (msg.topic && msg.topic.endsWith('.approvals')) {
          pushEvent('warning', 'APPROVAL', `High-risk action proposed: ${msg.message?.action_name}`);
          loadApprovals();
        }
      } catch (_) {}
    };
    ws.onerror = () => { setWsStatus('ERROR'); };
    ws.onclose = () => { setWsStatus('OFFLINE'); scheduleReconnect(); };
  }

  function disconnect() {
    if (ws) { ws.onclose = null; ws.close(); ws = null; }
    setWsStatus('OFFLINE');
  }

  function scheduleReconnect() {
    if (reconnectTimer) return;
    reconnectTimer = setTimeout(() => { reconnectTimer = null; connect(); }, 3000);
  }

  function pushEvent(sev, tag, text) {
    const feed = document.getElementById('cc-event-stream');
    if (!feed) return;
    const now = new Date().toLocaleTimeString([], { hour12: false });
    const div = document.createElement('div');
    div.className = 'cc-event sev-' + (sev || 'info');
    div.innerHTML = `<span class="cc-etime">${now}</span><span class="cc-etag">${esc(tag)}</span><span class="cc-etext">${esc(text)}</span>`;
    feed.prepend(div);
    while (feed.children.length > 60) feed.removeChild(feed.lastChild);
  }

  function setWsStatus(label) {
    const el = document.getElementById('cc-ws-status');
    if (!el) return;
    el.innerHTML = `<i class="fa-solid fa-circle"></i> ${label}`;
    el.className = 'cc-conn-status ' + (label === 'LIVE' ? 'live' : '');
  }

  // ── Demo crisis ───────────────────────────────────────────────
  async function launchDemo() {
    const btn = document.getElementById('cc-launch-demo');
    if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> FIRING…'; }
    try {
      const res = await api('/platform/demo/crisis', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ org_id: currentOrgId }),
      });
      pushEvent('critical', 'DEMO', `Demo crisis fired — ${res.count} signals ingested for ${currentOrgId}`);
      setTimeout(() => { loadIncidents(); loadApprovals(); refreshKpis(); }, 2500);
    } catch (e) {
      pushEvent('error', 'DEMO', 'Failed to fire: ' + e.message);
    } finally {
      if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> LAUNCH DEMO CRISIS'; }
    }
  }

  // ── Onboarding Modal ──────────────────────────────────────────
  function openOnboardModal() {
    const container = document.getElementById('cc-modal-container');
    if (!container) return;
    container.innerHTML = `
      <div class="cc-modal-backdrop" id="cc-modal-backdrop">
        <div class="cc-modal">
          <div class="cc-modal-title"><i class="fa-solid fa-rocket"></i> Connect Your Organization</div>
          <div class="cc-modal-desc">Create a workspace and generate a zero-code NEXUS Ingestion Endpoint for your infrastructure.</div>
          
          <div class="cc-form-group">
            <label class="cc-form-label">Organization Name</label>
            <input type="text" id="ob-org-name" class="cc-form-input" placeholder="e.g. Stripe, Uber, Tesla Energy" value="" autofocus />
          </div>
          <div class="cc-form-group">
            <label class="cc-form-label">Industry / Domain</label>
            <select id="ob-org-industry" class="cc-form-input">
              <option value="software">Software & SaaS</option>
              <option value="fintech">Financial Services & Payments</option>
              <option value="energy">Energy & Infrastructure</option>
              <option value="supply_chain">Logistics & Supply Chain</option>
              <option value="higher_ed">Higher Education</option>
            </select>
          </div>

          <div id="ob-result" style="display:none; margin-top:14px;">
            <div class="cc-form-label" style="color:var(--color-success);"><i class="fa-solid fa-circle-check"></i> Workspace Created & Endpoint Ready</div>
            <div style="font-size:0.68rem; color:var(--text-subtle); margin-bottom:4px;">NEXUS Ingestion Endpoint:</div>
            <div class="cc-code-box" id="ob-endpoint-box"></div>
            <div style="font-size:0.68rem; color:var(--text-subtle); margin:8px 0 4px;">HMAC-SHA256 Secret (Saved Securely):</div>
            <div class="cc-code-box" id="ob-secret-box"></div>
            
            <button class="cc-btn cc-btn-primary" id="ob-test-event-btn" style="margin-top:12px; width:100%;">
              <i class="fa-solid fa-paper-plane"></i> SEND TEST EVENT & ACTIVATE
            </button>
          </div>

          <div class="cc-modal-actions">
            <button class="cc-btn" id="ob-cancel-btn">CANCEL</button>
            <button class="cc-btn cc-btn-primary" id="ob-submit-btn"><i class="fa-solid fa-arrow-right"></i> GENERATE ENDPOINT</button>
          </div>
        </div>
      </div>
    `;

    document.getElementById('ob-cancel-btn')?.addEventListener('click', closeModal);
    document.getElementById('cc-modal-backdrop')?.addEventListener('click', (e) => {
      if (e.target.id === 'cc-modal-backdrop') closeModal();
    });

    document.getElementById('ob-submit-btn')?.addEventListener('click', async () => {
      const name = document.getElementById('ob-org-name')?.value?.trim();
      const industry = document.getElementById('ob-org-industry')?.value;
      if (!name) { alert('Please enter an organization name.'); return; }

      const submitBtn = document.getElementById('ob-submit-btn');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> CREATING…';

      try {
        const res = await api('/organizations', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: name, industry: industry, rate_limit: 100 })
        });

        const org = res.organization;
        currentOrgId = org.id;
        currentPublicId = org.public_id;
        currentOrgName = org.name;

        const baseHttp = window.NexusConfig ? window.NexusConfig.getHttpBase() : 'http://localhost:8000';
        document.getElementById('ob-endpoint-box').innerText = `POST ${baseHttp}${org.ingestion_endpoint}`;
        document.getElementById('ob-secret-box').innerText = org.ingestion_secret;
        document.getElementById('ob-result').style.display = 'block';
        submitBtn.style.display = 'none';

        document.getElementById('ob-test-event-btn')?.addEventListener('click', async () => {
          const testBtn = document.getElementById('ob-test-event-btn');
          testBtn.disabled = true;
          testBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> DELIVERING TEST WEBHOOK…';

          try {
            await fetch(`${baseHttp}${org.ingestion_endpoint}`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-Nexus-Event-Id': `test_evt_${Date.now()}`,
                'X-Nexus-Timestamp': new Date().toISOString(),
              },
              body: JSON.stringify({
                event_type: 'SERVICE_FAILURE',
                severity: 'critical',
                resource: 'api-gateway',
                summary: 'Synthetic test webhook verification from onboarding wizard.',
                error_rate: '45%'
              })
            });

            closeModal();
            setOrganization(org.id);
            pushEvent('info', 'ONBOARDING', `Workspace "${org.name}" activated! Test event ingested.`);
          } catch (err) {
            alert('Failed to send test event: ' + err.message);
            testBtn.disabled = false;
            testBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> RETRY TEST';
          }
        });

      } catch (err) {
        alert('Failed to create organization: ' + err.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-arrow-right"></i> GENERATE ENDPOINT';
      }
    });
  }

  // ── Endpoint Details Modal ────────────────────────────────────
  async function openEndpointModal() {
    const container = document.getElementById('cc-modal-container');
    if (!container) return;

    const endpointUrl = window.NexusConfig
      ? window.NexusConfig.getApiUrl(`/api/v1/ingest/${currentPublicId}`)
      : `http://localhost:8000/api/v1/ingest/${currentPublicId}`;

    container.innerHTML = `
      <div class="cc-modal-backdrop" id="cc-modal-backdrop">
        <div class="cc-modal">
          <div class="cc-modal-title"><i class="fa-solid fa-plug-circle-bolt"></i> Ingestion Endpoint: ${esc(currentOrgName)}</div>
          <div class="cc-modal-desc">Configure your external tools (GitHub, Datadog, Prometheus, Slack, or microservices) to send events here.</div>

          <div class="cc-form-group">
            <label class="cc-form-label">HTTP Webhook Target (POST)</label>
            <div class="cc-code-box">${esc(endpointUrl)}</div>
          </div>

          <div class="cc-form-group">
            <label class="cc-form-label">HMAC-SHA256 Required Headers</label>
            <div class="cc-code-box">X-Nexus-Timestamp: &lt;ISO8601 or Unix timestamp&gt;<br>X-Nexus-Signature: sha256=&lt;hmac_hex&gt;<br>X-Nexus-Event-Id: &lt;unique_id_for_replay_protection&gt;</div>
          </div>

          <div class="cc-form-group">
            <label class="cc-form-label">cURL Integration Example</label>
            <div class="cc-code-box" style="font-size:0.64rem;">curl -X POST "${esc(endpointUrl)}" \\<br>&nbsp;&nbsp;-H "Content-Type: application/json" \\<br>&nbsp;&nbsp;-d '{"resource": "payment-api", "severity": "critical", "error_rate": "42%", "summary": "Outage detected"}'</div>
          </div>

          <div class="cc-modal-actions">
            <button class="cc-btn cc-btn-primary" id="ep-close-btn">CLOSE</button>
          </div>
        </div>
      </div>
    `;

    document.getElementById('ep-close-btn')?.addEventListener('click', closeModal);
    document.getElementById('cc-modal-backdrop')?.addEventListener('click', (e) => {
      if (e.target.id === 'cc-modal-backdrop') closeModal();
    });
  }

  function closeModal() {
    const container = document.getElementById('cc-modal-container');
    if (container) container.innerHTML = '';
  }

  // ── Utilities ─────────────────────────────────────────────────
  function esc(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
  }
  function setText(id, v) { const el = document.getElementById(id); if (el) el.textContent = v; }
  function fmtAgo(iso) {
    const sec = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
    if (sec < 60) return sec + 's ago';
    if (sec < 3600) return Math.floor(sec / 60) + 'm ago';
    return Math.floor(sec / 3600) + 'h ago';
  }

  // ── Bind DOM once document is ready ───────────────────────────
  function bind() {
    document.getElementById('cc-launch-demo')?.addEventListener('click', launchDemo);
    document.getElementById('cc-refresh')?.addEventListener('click', render);
    document.getElementById('cc-btn-onboard')?.addEventListener('click', openOnboardModal);
    document.getElementById('cc-btn-endpoint')?.addEventListener('click', openEndpointModal);

    const orgSelect = document.getElementById('cc-org-select');
    if (orgSelect) {
      orgSelect.addEventListener('change', (e) => {
        const selected = e.target.value;
        const selectedOpt = e.target.selectedOptions[0];
        currentPublicId = selectedOpt?.dataset.public || selected;
        setOrganization(selected);
      });
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bind);
  else bind();
})();