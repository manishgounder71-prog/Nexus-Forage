const express = require('express');
const router = express.Router();

let connectors = [
  { id: 'conn_github', name: 'GitHub Org Repo Webhook', type: 'github', status: 'ACTIVE', eventsIngested: 240 },
  { id: 'conn_slack', name: 'Slack Crisis Channel Stream', type: 'slack', status: 'ACTIVE', eventsIngested: 615 },
  { id: 'conn_datadog', name: 'Datadog Infrastructure Metrics', type: 'monitoring', status: 'ACTIVE', eventsIngested: 1042 },
  { id: 'conn_pagerduty', name: 'PagerDuty Incident Feed', type: 'support', status: 'ACTIVE', eventsIngested: 78 }
];

// GET /api/connectors
router.get('/', (req, res) => {
  res.status(200).json({ status: 'success', data: { connectors } });
});

// POST /api/connectors/simulate-burst
router.post('/simulate-burst', (req, res) => {
  const { source = 'monitoring', count = 5 } = req.body;
  res.status(200).json({
    status: 'success',
    message: `Injected ${count} synthetic anomaly events across connector: ${source}`,
    correlationDetected: true,
    triggeredMissionId: `msn_burst_${Date.now()}`
  });
});

module.exports = router;
