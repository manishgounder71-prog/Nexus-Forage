const express = require('express');
const router = express.Router();

// In-memory or persistence store for missions
let missions = [
  {
    id: 'msn_grid_sec_01',
    title: 'Regional Power Grid Anomaly Response',
    status: 'COMPLETED',
    priority: 'high',
    domain: 'Critical Infrastructure',
    agentsEngaged: 6,
    consensusScore: 97.2,
    createdAt: new Date(Date.now() - 3600000).toISOString()
  },
  {
    id: 'msn_sc_pharm_02',
    title: 'Cold-Chain Disruption Mitigation',
    status: 'EXECUTING',
    priority: 'critical',
    domain: 'Supply Chain',
    agentsEngaged: 5,
    consensusScore: 94.5,
    createdAt: new Date(Date.now() - 1200000).toISOString()
  },
  {
    id: 'msn_acad_net_03',
    title: 'Distributed DDoS & Credential Defense',
    status: 'CREATED',
    priority: 'medium',
    domain: 'Cybersecurity',
    agentsEngaged: 4,
    consensusScore: 91.8,
    createdAt: new Date(Date.now() - 300000).toISOString()
  }
];

// GET /api/missions - List all missions
router.get('/', (req, res) => {
  const { status, domain } = req.query;
  let filtered = [...missions];
  if (status) filtered = filtered.filter(m => m.status.toLowerCase() === status.toLowerCase());
  if (domain) filtered = filtered.filter(m => m.domain.toLowerCase() === domain.toLowerCase());

  res.status(200).json({
    status: 'success',
    total: filtered.length,
    data: { missions: filtered }
  });
});

// POST /api/missions - Create new crisis mission
router.post('/', (req, res) => {
  const { title, raw_prompt, domain, priority } = req.body;
  if (!raw_prompt && !title) {
    return res.status(400).json({ status: 'error', message: 'raw_prompt or title is required' });
  }

  const newMission = {
    id: `msn_${Math.random().toString(36).substring(2, 9)}`,
    title: title || (raw_prompt ? raw_prompt.substring(0, 50) : 'Autonomous Mission'),
    raw_prompt: raw_prompt || title,
    status: 'EXECUTING',
    priority: priority || 'high',
    domain: domain || 'Critical Infrastructure',
    agentsEngaged: 5,
    consensusScore: 95.0,
    createdAt: new Date().toISOString()
  };

  missions.unshift(newMission);
  res.status(201).json({
    status: 'success',
    message: 'Crisis mission dispatched to autonomous swarm',
    data: { mission: newMission }
  });
});

// GET /api/missions/:id - Get mission details
router.get('/:id', (req, res) => {
  const mission = missions.find(m => m.id === req.params.id);
  if (!mission) {
    return res.status(404).json({ status: 'error', message: 'Mission not found' });
  }
  res.status(200).json({ status: 'success', data: { mission } });
});

// GET /api/missions/:id/export - Export incident dossier
router.get('/:id/export', (req, res) => {
  const mission = missions.find(m => m.id === req.params.id) || {
    id: req.params.id,
    title: 'Autonomous Crisis Operation',
    domain: 'Critical Infrastructure',
    status: 'COMPLETED',
    consensusScore: 96.5
  };

  res.status(200).json({
    status: 'success',
    dossier: {
      dossierId: `dos_${mission.id}_${Date.now()}`,
      exportedAt: new Date().toISOString(),
      mission,
      summary: 'Executive crisis response post-mortem generated automatically by NEXUS Swarm.',
      consensusLevel: `${mission.consensusScore}%`,
      complianceHash: `0x${Buffer.from(mission.id).toString('hex')}`
    }
  });
});

module.exports = router;
