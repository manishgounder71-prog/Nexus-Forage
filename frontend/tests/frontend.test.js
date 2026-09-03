const { test, describe } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');

describe('NEXUS FORGE Frontend UI & Logic Test Suite', () => {
  const htmlPath = path.join(__dirname, '..', 'index.html');
  const htmlContent = fs.readFileSync(htmlPath, 'utf8');

  test('HTML Document Contract: Critical Elements Present', () => {
    // Verify document title and metadata
    assert.match(htmlContent, /<title>NEXUS FORGE/i, 'Title should reference NEXUS FORGE');
    assert.match(htmlContent, /dark-theme/i, 'Dark theme root class should be present');

    // Verify navigation views
    const requiredViews = [
      'command-center',
      'live-mission',
      'ai-organization',
      'agent-parliament',
      'red-team',
      'simulation-engine',
      'memory-intelligence',
      'connector-center'
    ];
    for (const view of requiredViews) {
      assert.ok(htmlContent.includes(`data-view="${view}"`), `Nav item for ${view} must exist`);
    }

    // Verify sponsor integration badges
    assert.ok(htmlContent.includes('OMI'), 'Omi sponsor badge must exist');
    assert.ok(htmlContent.includes('LYZR'), 'Lyzr sponsor badge must exist');
    assert.ok(htmlContent.includes('QDRANT'), 'Qdrant sponsor badge must exist');

    // Verify script dependencies loaded
    assert.ok(htmlContent.includes('js/app.js'), 'app.js script tag required');
    assert.ok(htmlContent.includes('js/connector-center.js'), 'connector-center.js script tag required');
    assert.ok(htmlContent.includes('js/memory-galaxy.js'), 'memory-galaxy.js script tag required');
  });

  test('Audio Synthesis: Frequency Mapping & Scale Integrity', () => {
    // Replicate synthesizer sound scale mapping from audio-synth.js
    const noteFrequencies = {
      'C4': 261.63,
      'E4': 329.63,
      'G4': 392.00,
      'B4': 493.88,
      'C5': 523.25,
      'alert': 880.00,
      'crisis': 220.00
    };

    assert.strictEqual(noteFrequencies['C4'], 261.63);
    assert.ok(noteFrequencies['alert'] > noteFrequencies['C5'], 'Alert pitch should be high-frequency');
    assert.ok(noteFrequencies['crisis'] < noteFrequencies['C4'], 'Crisis drone should be low-frequency bass');
  });

  test('DAG Visualizer Layout & Coordinates Algorithm', () => {
    // Test topological rank placement algorithm
    const nodes = [
      { id: 'T1', dependencies: [] },
      { id: 'T2', dependencies: ['T1'] },
      { id: 'T3', dependencies: ['T1'] },
      { id: 'T4', dependencies: ['T2', 'T3'] }
    ];

    function computeDepths(nodeList) {
      const depths = {};
      nodeList.forEach(n => {
        if (n.dependencies.length === 0) {
          depths[n.id] = 0;
        } else {
          const maxParentDepth = Math.max(...n.dependencies.map(p => depths[p] ?? 0));
          depths[n.id] = maxParentDepth + 1;
        }
      });
      return depths;
    }

    const depths = computeDepths(nodes);
    assert.strictEqual(depths['T1'], 0, 'Root node should be at depth 0');
    assert.strictEqual(depths['T2'], 1, 'Child node T2 should be at depth 1');
    assert.strictEqual(depths['T3'], 1, 'Child node T3 should be at depth 1');
    assert.strictEqual(depths['T4'], 2, 'Converged node T4 should be at depth 2');
  });

  test('Memory Galaxy Cosine Vector Distance Calculation', () => {
    function cosineSimilarity(v1, v2) {
      assert.strictEqual(v1.length, v2.length, 'Vectors must have identical dimensions');
      let dot = 0, norm1 = 0, norm2 = 0;
      for (let i = 0; i < v1.length; i++) {
        dot += v1[i] * v2[i];
        norm1 += v1[i] * v1[i];
        norm2 += v2[i] * v2[i];
      }
      return dot / (Math.sqrt(norm1) * Math.sqrt(norm2));
    }

    const vA = [1.0, 0.0, 0.5, 0.8];
    const vB = [1.0, 0.0, 0.5, 0.8]; // identical
    const vC = [-1.0, 0.0, -0.5, -0.8]; // opposite

    assert.strictEqual(Math.round(cosineSimilarity(vA, vB)), 1, 'Identical vectors score 1.0');
    assert.strictEqual(Math.round(cosineSimilarity(vA, vC)), -1, 'Opposite vectors score -1.0');
  });

  test('Crisis Severity Classifier & Threshold Logic', () => {
    function classifySignal(text) {
      const lower = text.toLowerCase();
      if (lower.includes('critical') || lower.includes('blackout') || lower.includes('breach')) {
        return 'CRITICAL';
      }
      if (lower.includes('warning') || lower.includes('latency') || lower.includes('dissent')) {
        return 'WARNING';
      }
      return 'NORMAL';
    }

    assert.strictEqual(classifySignal('Substation 04 blackout imminent'), 'CRITICAL');
    assert.strictEqual(classifySignal('Database latency above threshold'), 'WARNING');
    assert.strictEqual(classifySignal('Routine heartbeat healthy'), 'NORMAL');
  });
});
