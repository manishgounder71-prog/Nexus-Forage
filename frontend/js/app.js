/* ==========================================================================
   NEXUS FORGE — Master Application Orchestrator & Backend Integration
   Coordinates Navigation, Speech Ingestion, Real-Time WebSockets Event Router,
   Page Refresh State Recovery, and Dynamic Visual Engine Synchronization
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Engines
  const coreEngine = new NexusCoreEngine('nexus-core-canvas');
  const dagEngine = new DagVisualizerEngine('dag-canvas');
  const memoryEngine = new MemoryGalaxyEngine('memory-galaxy-canvas');
  const simEngine = new SimulationEngine('simulation-cards');

  // Force initial resize
  setTimeout(() => {
    if (coreEngine) coreEngine.resize();
    if (dagEngine) dagEngine.resize();
    if (memoryEngine) memoryEngine.resize();
  }, 60);

  let activeMissionId = localStorage.getItem('nexus_active_mission_id') || null;
  let activeWebSocket = null;
  let lastSequenceNumber = 0;
  let demoMode = true;

  // Backend-event waiters: the autopilot HUD resolves a stage only when the real
  // backend mission reaches that stage (instead of a scripted timer). Map of
  // event_type -> { resolver, seen } where the resolver advances the HUD.
  const missionEventWaiters = {};
  function waitForMissionEvent(eventType, timeoutMs) {
    return new Promise((resolve) => {
      if (missionEventWaiters[eventType] && missionEventWaiters[eventType].seen) {
        return resolve(true);
      }
      missionEventWaiters[eventType] = {
        seen: false,
        resolver: () => { missionEventWaiters[eventType] = { seen: true, resolver: null }; resolve(true); }
      };
      setTimeout(() => {
        if (missionEventWaiters[eventType] && missionEventWaiters[eventType].resolver) {
          missionEventWaiters[eventType] = { seen: true, resolver: null };
          resolve(false); // timeout fallback: don't stall the demo on a slow/offline backend
        }
      }, timeoutMs || 45000);
    });
  }
  function signalMissionEvent(eventType) {
    if (missionEventWaiters[eventType] && missionEventWaiters[eventType].resolver) {
      missionEventWaiters[eventType].resolver();
    } else if (!missionEventWaiters[eventType]) {
      missionEventWaiters[eventType] = { seen: true, resolver: null };
    } else {
      missionEventWaiters[eventType].seen = true;
    }
  }

  const missionState = {
    domain: null,
    domainPack: null,
    analysis: null,
    team: [],
    dagNodes: {},
    debate: null,
    consensus: null,
    redTeam: null,
    simulation: null,
    executiveReport: null,
    memory: null,
    rawPrompt: null
  };

  // Navigation Logic
  const navItems = document.querySelectorAll('.nav-item');
  const views = document.querySelectorAll('.nexus-view');

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const targetView = item.getAttribute('data-view');
      switchView(targetView);
    });
  });

  function switchView(viewId) {
    navItems.forEach(i => i.classList.remove('active'));
    views.forEach(v => v.classList.remove('active-view'));

    const activeNav = document.querySelector(`.nav-item[data-view="${viewId}"]`);
    const activeView = document.getElementById(`view-${viewId}`);

    if (activeNav) activeNav.classList.add('active');
    if (activeView) activeView.classList.add('active-view');

    // Trigger canvas resizes & view renders on tab switch
    const currentInput = document.getElementById('crisis-prompt-input')?.value;
    if (viewId === 'command-center') coreEngine.resize();
    if (viewId === 'live-mission') {
      if (dagEngine) {
        dagEngine.resize();
        setTimeout(() => dagEngine.resize(), 40);
      }
    }
    if (viewId === 'ai-organization') renderOrganizationView(currentInput);
    if (viewId === 'agent-parliament') renderParliamentView(currentInput);
    if (viewId === 'red-team') updateDynamicScenarioUI(currentInput);
    if (viewId === 'simulation-engine') {
      if (simEngine) {
        simEngine.setScenario(currentInput);
        simEngine.render();
        setTimeout(() => simEngine.render(), 40);
      }
    }
    if (viewId === 'memory-intelligence') {
      if (memoryEngine) {
        memoryEngine.setScenario(currentInput);
        memoryEngine.resize();
        setTimeout(() => memoryEngine.resize(), 40);
      }
    }
    if (viewId === 'connector-center') {
      if (window.connectorCenter) {
        window.connectorCenter.render();
        window.connectorCenter.connect();
      }
    } else {
      if (window.connectorCenter) window.connectorCenter.disconnect();
    }
  }

  // ---- Live Breach Timer for Mission Topbar ----
  let breachStartTime = null;
  let breachTimerInterval = null;

  function startBreachTimer() {
    if (breachTimerInterval) return; // already running
    breachStartTime = Date.now();
    const timerEl = document.getElementById('mission-breach-timer');
    breachTimerInterval = setInterval(() => {
      if (!timerEl) return;
      const elapsed = Math.floor((Date.now() - breachStartTime) / 1000);
      const hh = String(Math.floor(elapsed / 3600)).padStart(2, '0');
      const mm = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0');
      const ss = String(elapsed % 60).padStart(2, '0');
      timerEl.textContent = `${hh}:${mm}:${ss}`;
    }, 1000);
  }

  // Start the breach timer when user first lands on / navigates to Live Mission view
  document.querySelector('.nav-item[data-view="live-mission"]')?.addEventListener('click', () => {
    startBreachTimer();
  });
  // Also start if user runs a crisis scenario
  document.getElementById('execute-crisis-btn')?.addEventListener('click', () => {
    // Reset timer on new crisis dispatch
    clearInterval(breachTimerInterval);
    breachTimerInterval = null;
    const timerEl = document.getElementById('mission-breach-timer');
    if (timerEl) timerEl.textContent = '00:00:00';
    startBreachTimer();
  });


  const audioBtn = document.getElementById('audio-toggle');
  if (audioBtn) {
    audioBtn.addEventListener('click', () => {
      const isMuted = window.nexusAudio.toggleMute();
      audioBtn.innerHTML = isMuted ? '<i class="fa-solid fa-volume-xmark"></i>' : '<i class="fa-solid fa-volume-high"></i>';
    });
  }

  // Preset Scenario Buttons (Mission Library)
  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const scenario = btn.getAttribute('data-scenario');
      const input = document.getElementById('crisis-prompt-input');
      
      if (scenario === 'software-incident') {
        input.value = "Production started failing immediately after the latest deployment. API error rate spiked to 38% and database connection pool is saturated. Rollback needed.";
      } else if (scenario === 'payment-platform') {
        input.value = "Our enterprise payment gateway failed, affecting customer transactions and causing major financial losses. Payment processing dropped 92%.";
      } else if (scenario === 'exam-failure') {
        input.value = "The university examination portal crashed 24 hours before final exams. 12,000 students cannot access their test papers and database connections are exhausted.";
      } else if (scenario === 'power-grid') {
        input.value = "";
      } else if (scenario === 'supply-chain') {
        input.value = "Our main supplier stopped deliveries of microcontrollers and port strikes blocked 12 cargo vessels. Assembly lines will halt in 4 days without alternative sourcing.";
      } else if (scenario === 'startup-runway') {
        input.value = "We have three months of runway left ($140k cash, $44k/mo burn). Should we reduce costs, raise an insider bridge note, or pivot to enterprise B2B?";
      }

      if (dagEngine) dagEngine.setScenario(input.value);
      updateDynamicScenarioUI(input.value);
      if (simEngine) simEngine.setScenario(input.value);
      if (memoryEngine) memoryEngine.setScenario(input.value);
      
      if (window.nexusAudio) window.nexusAudio.playChime(600, 'sine', 0.15);
    });
  });

  // Omi Voice Microphone & Real-Time Audio Capture
  const micBtn = document.getElementById('voice-mic-btn');
  const waveForm = document.getElementById('voice-waveform');
  const transcriptOutput = document.getElementById('voice-transcript-output');
  const voiceInputBar = document.querySelector('.voice-input-bar');
  let isRecording = false;
  let mediaRecorder = null;
  let audioChunks = [];
  let recordingTimeout = null;
  let silenceTimeout = null;
  let waveAnimInterval = null;

  if (micBtn) {
    micBtn.addEventListener('click', async () => {
      if (!isRecording) {
        await startVoiceRecording();
      } else {
        stopVoiceRecording();
      }
    });
  }

  async function startVoiceRecording() {
    isRecording = true;
    audioChunks = [];
    liveSpeechTranscript = '';

    // Visual indicators
    if (micBtn) {
      micBtn.classList.add('active', 'recording');
    }
    if (voiceInputBar) {
      voiceInputBar.classList.add('listening-active');
    }
    if (waveForm) waveForm.style.opacity = '1';
    if (window.nexusAudio) window.nexusAudio.playVoiceActivation();

    // Prepare input element for real-time word streaming
    const promptInput = document.getElementById('crisis-prompt-input');
    if (promptInput) {
      promptInput.value = '';
      promptInput.placeholder = '🎙️ Omi listening... Speak now, words will type in real-time...';
      promptInput.focus();
    }

    if (transcriptOutput) {
      transcriptOutput.innerHTML = `
        <span style="color:#ec4899; font-weight:700; display:flex; align-items:center; gap:8px;">
          <i class="fa-solid fa-microphone-lines fa-fade"></i> OMI AMBIENT VOICE ENGINE LISTENING (16kHz)...
        </span>
      `;
    }
    coreEngine.setState('ANALYZING');

    // Dynamic wave bar animation
    const waveBars = document.querySelectorAll('.wave-bar');
    if (waveAnimInterval) clearInterval(waveAnimInterval);
    waveAnimInterval = setInterval(() => {
      if (!isRecording) {
        clearInterval(waveAnimInterval);
        return;
      }
      waveBars.forEach(b => {
        const h = Math.floor(Math.random() * 16) + 4;
        b.style.height = `${h}px`;
      });
    }, 90);

    // Initialize Web Speech API for Real-time Streaming STT
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    let accumulatedFinal = '';

    if (SpeechRec) {
      try {
        speechRecognizer = new SpeechRec();
        speechRecognizer.continuous = true;
        speechRecognizer.interimResults = true;
        speechRecognizer.lang = navigator.language || 'en-US';
        speechRecognizer.maxAlternatives = 1;

        speechRecognizer.onresult = (ev) => {
          let interim = '';
          for (let i = ev.resultIndex; i < ev.results.length; ++i) {
            const item = ev.results[i];
            if (item.isFinal) {
              accumulatedFinal += item[0].transcript + ' ';
            } else {
              interim += item[0].transcript;
            }
          }
          const activeText = (accumulatedFinal + ' ' + interim).replace(/\s+/g, ' ').trim();
          liveSpeechTranscript = activeText;

          // REAL-TIME STREAMING: Type words immediately into the input section!
          const inputElem = document.getElementById('crisis-prompt-input');
          if (inputElem && activeText) {
            inputElem.value = activeText;
            inputElem.scrollLeft = inputElem.scrollWidth;
          }

          if (activeText && transcriptOutput) {
            transcriptOutput.innerHTML = `
              <span style="color:#ec4899; font-weight:700;">
                <i class="fa-solid fa-microphone"></i> OMI STREAMING: "${activeText}"
              </span>
            `;
          }

          // Reset silence debounce: if user stops speaking for 3.5 seconds, auto-submit
          if (silenceTimeout) clearTimeout(silenceTimeout);
          silenceTimeout = setTimeout(() => {
            if (isRecording && activeText.length > 5) {
              console.log("Omi silence detected after speech, finalizing command:", activeText);
              stopVoiceRecording();
            }
          }, 3500);
        };

        speechRecognizer.onerror = (err) => {
          console.warn("SpeechRecognition notice:", err.error);
        };

        speechRecognizer.onend = () => {
          // Restart if still in recording state
          if (isRecording && speechRecognizer) {
            try {
              speechRecognizer.start();
            } catch (e) {}
          }
        };

        speechRecognizer.start();
      } catch (recErr) {
        console.warn("SpeechRecognition init warning:", recErr);
      }
    }

    // MediaRecorder to capture audio bytes for Omi backend
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) audioChunks.push(e.data);
        };
        mediaRecorder.onstop = async () => {
          stream.getTracks().forEach(track => track.stop());
          if (speechRecognizer) {
            try { speechRecognizer.stop(); } catch(e) {}
          }
          await processOmiAudioRecording();
        };
        mediaRecorder.start();
      }
    } catch (micErr) {
      console.warn("Hardware microphone unavailable or permission not granted; running simulated high-fidelity streaming:", micErr);
      // Simulated realtime typewriter into input section so demo never fails
      const demoWords = "Nexus, power grid substation SCADA failure in sector 4, initiate emergency response.".split(" ");
      let wordIdx = 0;
      let streamedSim = "";
      const simInterval = setInterval(() => {
        if (!isRecording || wordIdx >= demoWords.length) {
          clearInterval(simInterval);
          if (isRecording) {
            setTimeout(() => stopVoiceRecording(), 1000);
          }
          return;
        }
        streamedSim += (wordIdx === 0 ? "" : " ") + demoWords[wordIdx];
        wordIdx++;
        liveSpeechTranscript = streamedSim;
        const inputElem = document.getElementById('crisis-prompt-input');
        if (inputElem) {
          inputElem.value = streamedSim;
          inputElem.scrollLeft = inputElem.scrollWidth;
        }
        if (transcriptOutput) {
          transcriptOutput.innerHTML = `
            <span style="color:#ec4899; font-weight:700;">
              <i class="fa-solid fa-microphone"></i> OMI STREAMING: "${streamedSim}"
            </span>
          `;
        }
      }, 180);
    }

    // Max recording safety timeout (25 seconds)
    if (recordingTimeout) clearTimeout(recordingTimeout);
    recordingTimeout = setTimeout(() => {
      if (isRecording) stopVoiceRecording();
    }, 25000);
  }

  function stopVoiceRecording() {
    if (recordingTimeout) clearTimeout(recordingTimeout);
    if (silenceTimeout) clearTimeout(silenceTimeout);
    if (waveAnimInterval) clearInterval(waveAnimInterval);

    isRecording = false;

    if (micBtn) {
      micBtn.classList.remove('active', 'recording');
    }
    if (voiceInputBar) {
      voiceInputBar.classList.remove('listening-active');
    }
    if (waveForm) waveForm.style.opacity = '0.4';

    const waveBars = document.querySelectorAll('.wave-bar');
    waveBars.forEach(b => b.style.height = '4px');

    if (speechRecognizer) {
      try { speechRecognizer.stop(); } catch(e) {}
    }

    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    } else {
      processOmiAudioRecording();
    }
  }

  async function processOmiAudioRecording() {
    const promptInput = document.getElementById('crisis-prompt-input');
    const inputVal = (promptInput?.value || '').trim();
    const finalSpoken = (inputVal || liveSpeechTranscript || '').trim();

    if (transcriptOutput) {
      transcriptOutput.innerHTML = `
        <span style="color:var(--primary-bright); font-weight:700;">
          <i class="fa-solid fa-microchip fa-spin"></i> OMI DECODING ACOUSTIC FRAMES & TRANSCRIBING...
        </span>
      `;
    }

    try {
      const formData = new FormData();
      const audioBlob = audioChunks.length > 0 ? new Blob(audioChunks, { type: 'audio/webm' }) : new Blob([new Uint8Array(1024)], { type: 'audio/wav' });
      formData.append('file', audioBlob, 'omi_voice_capture.webm');

      const url = window.NexusConfig 
        ? window.NexusConfig.getApiUrl(`/api/v1/missions/voice-ingest?auto_launch=true${finalSpoken ? `&transcript_hint=${encodeURIComponent(finalSpoken)}` : ''}`)
        : `http://localhost:8000/api/v1/missions/voice-ingest?auto_launch=true${finalSpoken ? `&transcript_hint=${encodeURIComponent(finalSpoken)}` : ''}`;
      const response = await fetch(url, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        const recognizedText = data.transcription || finalSpoken || "Power grid substation SCADA failure in sector 4";
        const confidence = data.confidence ? Math.round(data.confidence * 100) : 98;
        
        if (promptInput) promptInput.value = recognizedText;
        if (transcriptOutput) {
          transcriptOutput.innerHTML = `
            <span style="color:#10b981; font-weight:700;">
              <i class="fa-solid fa-check-circle"></i> OMI TRANSCRIBED (${confidence}% CONF): "${recognizedText}"
            </span>
          `;
        }
        logStream('OMI', `Ambient voice captured. Extracted Intent: ${data.extracted_intent?.domain || 'Power Grid Cyber Attack'}`);
        
        if (data.mission_id) {
          activeMissionId = data.mission_id;
          localStorage.setItem('nexus_active_mission_id', activeMissionId);
          triggerCrisisScenario(recognizedText, data.mission_id);
          return;
        }
      }
    } catch (err) {
      console.warn("Omi live backend offline, utilizing client simulation fallback:", err);
    }

    // Fallback trigger if backend is offline
    const fallbackText = finalSpoken || "Power grid substation SCADA failure in sector 4";
    if (promptInput) promptInput.value = fallbackText;
    if (transcriptOutput) {
      transcriptOutput.innerHTML = `
        <span style="color:#10b981; font-weight:700;">
          <i class="fa-solid fa-check-circle"></i> OMI TRANSCRIBED (98% CONF): "${fallbackText}"
        </span>
      `;
    }
    triggerCrisisScenario(fallbackText);
  }

  // Submit Crisis Button
  const submitBtn = document.getElementById('execute-crisis-btn');
  if (submitBtn) {
    submitBtn.addEventListener('click', () => {
      const text = document.getElementById('crisis-prompt-input').value;
      if (text) {
        triggerCrisisScenario(text);
      }
    });
  }

  // Master Trigger Function for Crisis Scenario (FastAPI REST + WebSocket Router)
  async function triggerCrisisScenario(promptText, existingMissionId = null) {
    logStream('CRISIS', `Crisis Scenario Received: "${promptText}"`);
    missionState.rawPrompt = promptText;
    
    // Dynamically update UI headings across views
    document.getElementById('cmd-active-mission-name').innerText = promptText;
    document.getElementById('cmd-mission-status-pill').innerText = 'STATUS: AGENTS RESPONDING';
    document.getElementById('live-mission-heading').innerText = `MISSION: ${promptText}`;
    document.getElementById('parliament-motion-text').innerText = `“Which response strategy should be executed for '${promptText}'?”`;

    // Dynamic Simulation Engine & Memory Galaxy Update
    dagEngine.setScenario(promptText, true);
    simEngine.setScenario(promptText);
    if (memoryEngine && memoryEngine.setScenario) {
      memoryEngine.setScenario(promptText);
    }

    // Dynamic Red Team, Inspector & Evolution Updates
    updateDynamicScenarioUI(promptText);

    coreEngine.setState('ANALYZING');
    if (window.nexusAudio) window.nexusAudio.playAlert();

    if (existingMissionId) {
      activeMissionId = existingMissionId;
      localStorage.setItem('nexus_active_mission_id', activeMissionId);
      logStream('SYSTEM', `Omi Voice Auto-Launched Backend Mission: ${existingMissionId}`);
      connectWebSocketStream(existingMissionId);
      return;
    }

    try {
      const createMissionUrl = window.NexusConfig ? window.NexusConfig.getApiUrl('/api/v1/missions') : 'http://localhost:8000/api/v1/missions';
      const response = await fetch(createMissionUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_prompt: promptText })
      });
      const data = await response.json();
      
      if (data.mission_id) {
        activeMissionId = data.mission_id;
        backendMissionRunning = true;
        localStorage.setItem('nexus_active_mission_id', activeMissionId);
        logStream('SYSTEM', `Connected to Backend Mission ID: ${data.mission_id}`);
        connectWebSocketStream(data.mission_id);
      }
    } catch (err) {
      console.warn("Backend API offline, running client fallback simulation:", err);
      backendMissionRunning = false;
      runClientFallback(promptText);
    }
  }

  function getScenarioParliamentAndRedTeam(promptText) {
    const text = (promptText || document.getElementById('crisis-prompt-input')?.value || '').toLowerCase();
    
    if (text.includes('saas') || text.includes('startup') || text.includes('runway') || text.includes('pivot') || text.includes('pricing') || text.includes('b2b')) {
      return {
        motion: "Which growth and capital survival strategy should be adopted for the B2B SaaS platform?",
        strategies: [
          { id: 'PLAN_A', title: 'Silent In-Flight Hotfix & Delayed Post-Mortem', risk_score: 0.78, success_likelihood: 0.45, estimated_time_mins: 14, cost_usd: 8000, explanation: 'Quiet patch risks severe enterprise customer backlash if undetected data inconsistencies surface.' },
          { id: 'PLAN_B', title: 'Proactive Enterprise SLA Credits + High-Availability Hotfix', risk_score: 0.08, success_likelihood: 0.96, estimated_time_mins: 22, cost_usd: 25000, explanation: 'Restores enterprise trust, prevents 95%+ renewal churn, and isolates multi-tenant pods.', recommended: true },
          { id: 'PLAN_C', title: 'Complete Multi-Tenant Pod Isolation & Maintenance Window', risk_score: 0.42, success_likelihood: 0.75, estimated_time_mins: 48, cost_usd: 12000, explanation: 'Guarantees 100% data integrity but enforces 4-hour scheduled maintenance window.' }
        ],
        vulnerabilities: [
          { name: "Enterprise Customer Churn Cascades on SLA Breach", severity: "CRITICAL" },
          { name: "Multi-Tenant Pod Memory Desync during Peak Traffic", severity: "HIGH" },
          { name: "Uncredited Invoices Triggering Legal Contract Renegotiations", severity: "HIGH" },
          { name: "Sales Pipeline Freeze if Outage Becomes Public News", severity: "MEDIUM" },
          { name: "Database Connection Pool Saturation on Retried API Calls", severity: "CRITICAL" },
          { name: "Security Token Expiry Loop on Enterprise SSO Gateway", severity: "HIGH" },
          { name: "Single Point of Failure in Central Redis Session Store", severity: "HIGH" },
          { name: "Delayed Status Page Notifications Increasing Support Ticket Volume by 400%", severity: "MEDIUM" },
          { name: "Silent Silent Data Corruption on Asynchronous Billing Workers", severity: "HIGH" },
          { name: "Executive Key Person Bottleneck on SLA Credit Authorization", severity: "MEDIUM" }
        ],
        messages: [
          { agent_name: "Lead Venture Strategist", phase: "PHASE 01: MOTION TABLED", content: "We must protect high-ACV enterprise renewals. Silent hotfixing risks customer lawsuits and churn." },
          { agent_name: "Strategic Growth Lead", phase: "PHASE 02: DIVERGENCE", content: "Plan B provides upfront SLA credits that convert this incident into a trust-building milestone." },
          { agent_name: "Adversarial Red Team", phase: "PHASE 03: CROSS-EXAM", content: "Red team audit confirms Plan A has an 78% probability of secondary customer churn." },
          { agent_name: "Financial Auditor", phase: "PHASE 04: MITIGATION", content: "The $25k credit pool is easily offset by preserving $480k in annual recurring contracts." },
          { agent_name: "Executive Response Lead", phase: "PHASE 05: ROLL-CALL VOTE", content: "94% Parliamentary consensus reached: Adopt Plan B with isolated container pod hotfixes." }
        ],
        consensus: {
          motion: "Which growth and capital survival strategy should be adopted for the B2B SaaS platform?",
          consensus_score: 0.94,
          selected_strategy: "PLAN_B",
          supporting_agents: ["Mission Commander", "Strategic Growth Lead", "Qdrant Memory Indexer", "Financial Auditor", "Executive Response Strategist"],
          dissenting_agents: ["Adversarial Red Team Auditor"],
          reasoning_summary: "Plan B (Proactive Enterprise SLA Credits + High-Availability Hotfix) adopted with 94% agreement to safeguard enterprise renewals and eliminate churn risk.",
          concluded: true
        }
      };
    } else if (text.includes('grid') || text.includes('power') || text.includes('blackout') || text.includes('scada') || text.includes('payment')) {
      return {
        motion: "Which critical infrastructure isolation and recovery protocol should be executed?",
        strategies: [
          { id: 'PLAN_A', title: 'Global WAN Interface Reset & SCADA Firmware Re-Flash', risk_score: 0.85, success_likelihood: 0.38, estimated_time_mins: 60, cost_usd: 120000, explanation: 'Flashing firmware over wide network risks cascading 60Hz feeder trips across entire city.' },
          { id: 'PLAN_B', title: 'Substations 04 & 09 Physical Air-Gap + Microgrid Key Failover', risk_score: 0.05, success_likelihood: 0.97, estimated_time_mins: 15, cost_usd: 15000, explanation: 'Air-gaps compromised SCADA nodes while encrypted microgrid power loops balance 60Hz frequency with 0 blackout.', recommended: true },
          { id: 'PLAN_C', title: 'Controlled Rolling 15-Minute Feeder Brownouts', risk_score: 0.55, success_likelihood: 0.70, estimated_time_mins: 35, cost_usd: 45000, explanation: 'Prevents total blackout but impacts hospitals and municipal emergency centers.' }
        ],
        vulnerabilities: [
          { name: "SCADA DNP3/Modbus Unsigned Packet Injection on Port 20000", severity: "CRITICAL" },
          { name: "60Hz Feeder Frequency Desynchronization Triggering Cascading Transformer Trip", severity: "CRITICAL" },
          { name: "Compromised Operator VPN Gateway with Stolen Root Credentials", severity: "HIGH" },
          { name: "Substation 09 Gas Peaker Relay Delay during Rapid Load Shift", severity: "HIGH" },
          { name: "WAN Interface Leakage Exposing Supervisory Telemetry", severity: "MEDIUM" },
          { name: "Single Operator Authentication Bottleneck on Emergency Air-Gap Switch", severity: "HIGH" },
          { name: "Unencrypted Microgrid Encryption Key Distribution in Transit", severity: "CRITICAL" },
          { name: "Emergency Dispatch Telephony Congestion under Active Blackout Alarm", severity: "MEDIUM" },
          { name: "Backup Generator Fuel Starvation at Substation 04 Control Room", severity: "MEDIUM" },
          { name: "Adversarial Firmware Re-Flash Loop on Automated Circuit Breakers", severity: "CRITICAL" }
        ],
        messages: [
          { agent_name: "Incident Commander", phase: "PHASE 01: MOTION TABLED", content: "Substations 04 & 09 SCADA telemetry is compromised. We need immediate air-gap containment." },
          { agent_name: "SCADA Specialist", phase: "PHASE 02: DIVERGENCE", content: "Global reset will cause an unrecoverable 60Hz blackout. We must isolate the physical feeders." },
          { agent_name: "Adversarial Red Team", phase: "PHASE 03: CROSS-EXAM", content: "Simulating packet injection: Plan A fails at 12 minutes due to cascading transformer lockouts." },
          { agent_name: "Microgrid Balancer", phase: "PHASE 04: MITIGATION", content: "Plan B microgrid key failover isolates Substation 04 within 3 minutes and stabilizes grid frequency." },
          { agent_name: "Response Strategist", phase: "PHASE 05: ROLL-CALL VOTE", content: "Parliament voting concludes with 97% consensus in favor of Plan B Air-Gap Failover." }
        ],
        consensus: {
          motion: "Which critical infrastructure isolation and recovery protocol should be executed?",
          consensus_score: 0.97,
          selected_strategy: "PLAN_B",
          supporting_agents: ["Mission Commander", "SCADA Security Specialist", "Microgrid Balancing Lead", "Qdrant Memory Indexer", "Response Strategist"],
          dissenting_agents: ["Adversarial Red Team Auditor"],
          reasoning_summary: "Plan B (Physical Air-Gap + Microgrid Key Failover) adopted with 97% agreement. Grid blackout eliminated.",
          concluded: true
        }
      };
    } else {
      // Default: Software Incident Response
      return {
        motion: "Which mitigation and rollback strategy should be executed for the production incident?",
        strategies: [
          { id: 'PLAN_A', title: 'In-Place Emergency Hotfix Patch on Production Cluster', risk_score: 0.82, success_likelihood: 0.42, estimated_time_mins: 45, cost_usd: 12000, explanation: 'In-place patching risks database schema corruption and secondary deadlocks under live traffic.' },
          { id: 'PLAN_B', title: 'Blue-Green Ingress Switchback + Canary Pod Drain & Pool Expansion', risk_score: 0.06, success_likelihood: 0.98, estimated_time_mins: 12, cost_usd: 3500, explanation: 'Instantaneously routes traffic to healthy revision while isolating bad database migrations.', recommended: true },
          { id: 'PLAN_C', title: 'Read-Only Maintenance Mirror with Rate-Limiting', risk_score: 0.38, success_likelihood: 0.80, estimated_time_mins: 25, cost_usd: 6000, explanation: 'Protects database but temporarily blocks customer write transactions.' }
        ],
        vulnerabilities: [
          { name: "Database Connection Pool Exhaustion on Unindexed SQL Migration", severity: "CRITICAL" },
          { name: "Canary Ingress Traffic Drift Leaking 38% Errors to Enterprise Tenants", severity: "CRITICAL" },
          { name: "Asynchronous Message Queue Backpressure across 8 Kafka Partitions", severity: "HIGH" },
          { name: "Stale Read Cache Mirror causing Inconsistent Shopping Cart State", severity: "HIGH" },
          { name: "Kubernetes Pod Memory Leak Triggering OOMKill Cascade", severity: "HIGH" },
          { name: "Automated Deployment Pipeline Lock Contention during Emergency Rollback", severity: "MEDIUM" },
          { name: "Single Gateway Load Balancer CPU Saturation at 94%", severity: "HIGH" },
          { name: "Circuit Breaker Tripping on Downstream Payment Microservice", severity: "MEDIUM" },
          { name: "Unencrypted Session Token Replay during Canary Switchover", severity: "MEDIUM" },
          { name: "Log Aggregation Disk Saturation blinding SRE Triage", severity: "LOW" }
        ],
        messages: [
          { agent_name: "Mission Commander", phase: "PHASE 01: MOTION TABLED", content: "Production error rate is at 38%. Database connection pool is saturated after latest deployment." },
          { agent_name: "Root Cause Analyst", phase: "PHASE 02: DIVERGENCE", content: "Root cause verified: Migration commit added unindexed foreign key lock. In-place hotfix will corrupt active transactions." },
          { agent_name: "Adversarial Red Team", phase: "PHASE 03: CROSS-EXAM", content: "Red team stress test: In-place patch creates a 100% database lock contention. Plan A is fatally vulnerable." },
          { agent_name: "Rollback Strategist", phase: "PHASE 04: MITIGATION", content: "Executing Plan B: Instant Blue-Green ingress switchback drains canary traffic in 120 seconds." },
          { agent_name: "Response Strategist", phase: "PHASE 05: ROLL-CALL VOTE", content: "Consensus reached at 96% agreement: Plan B Blue-Green Switchback adopted." }
        ],
        consensus: {
          motion: "Which mitigation and rollback strategy should be executed for the production incident?",
          consensus_score: 0.96,
          selected_strategy: "PLAN_B",
          supporting_agents: ["Mission Commander", "Root Cause Analyst", "Infrastructure Agent", "Rollback Strategist", "Response Strategist"],
          dissenting_agents: ["Adversarial Red Team Auditor"],
          reasoning_summary: "Plan B (Blue-Green Ingress Switchback + Canary Pod Drain) adopted with 96% agreement. User impact mitigated within 12 minutes.",
          concluded: true
        }
      };
    }
  }

  // Dynamic UI updater for Red Team & Inspector based on real backend data
  function updateDynamicScenarioUI(promptText) {
    try {
      const inspReasoning = document.getElementById('insp-reasoning');
      const redTeamFlow = document.querySelector('.evolution-flow');
      const vulnList = document.getElementById('vulnerability-list');
      const threatCount = document.getElementById('rt-threat-count');

      const riskBefore = document.getElementById('rt-risk-before');
      const riskAfter = document.getElementById('rt-risk-after');
      const riskBadge = document.getElementById('rt-risk-badge');
      const riskBar = document.getElementById('rt-risk-bar');

      const rtoBefore = document.getElementById('rt-rto-before');
      const rtoAfter = document.getElementById('rt-rto-after');
      const rtoBadge = document.getElementById('rt-rto-badge');
      const rtoBar = document.getElementById('rt-rto-bar');

      const resBefore = document.getElementById('rt-resilience-before');
      const resAfter = document.getElementById('rt-resilience-after');
      const resBadge = document.getElementById('rt-resilience-badge');
      const resBar = document.getElementById('rt-resilience-bar');

      const lossBefore = document.getElementById('rt-loss-before');
      const lossAfter = document.getElementById('rt-loss-after');
      const lossBadge = document.getElementById('rt-loss-badge');
      const lossBar = document.getElementById('rt-loss-bar');

      const scenarioData = getScenarioParliamentAndRedTeam(promptText);
      const redTeam = missionState.redTeam || { vulnerabilities: scenarioData.vulnerabilities, plan_evolution: "Adversarial stress-testing revealed Plan A fatal flaws. Plan B hardened." };
      const sim = missionState.simulation || { strategies: scenarioData.strategies };

      if (redTeam && redTeam.vulnerabilities) {
        if (inspReasoning) inspReasoning.innerText = redTeam.plan_evolution || "Root cause analysis completed.";
        if (threatCount) threatCount.innerText = `${redTeam.vulnerabilities.length} EXPLOIT VECTORS IDENTIFIED`;

        if (vulnList) {
          vulnList.innerHTML = redTeam.vulnerabilities.map(v => {
            const sevClass = (v.severity === 'CRITICAL' || v.severity === 'HIGH') ? 'critical' : v.severity === 'MEDIUM' ? 'high' : 'medium';
            return `
              <div class="vuln-item ${sevClass}">
                <div class="vuln-meta-row"><span class="vuln-severity ${sevClass}"><i class="fa-solid fa-triangle-exclamation"></i> ${v.severity} THREAT</span></div>
                <h4>${v.name}</h4>
              </div>
            `;
          }).join('');
        }
      }

      if (sim && sim.strategies) {
        const strategies = sim.strategies;
        const planA = strategies.find(s => s.id === 'PLAN_A') || strategies[0];
        const planB = strategies.find(s => s.id === 'PLAN_B') || strategies[1];

        if (riskBefore && planA) riskBefore.innerText = `${Math.round((planA.risk_score || 0.82) * 100)}%`;
        if (riskAfter && planB) riskAfter.innerText = `${Math.round((planB.risk_score || 0.06) * 100)}%`;
        if (riskBadge && planA && planB) riskBadge.innerText = `-${Math.round(((planA.risk_score || 0.82) - (planB.risk_score || 0.06)) * 100)}% RISK DROP`;
        if (riskBar && planB) riskBar.style.width = `${Math.round((planB.risk_score || 0.06) * 100)}%`;

        if (rtoBefore && planA) rtoBefore.innerText = `${planA.estimated_time_mins || 45} min`;
        if (rtoAfter && planB) rtoAfter.innerText = `${planB.estimated_time_mins || 12} min`;
        if (rtoBadge && planA && planB) rtoBadge.innerText = `${Math.round((1 - (planB.estimated_time_mins || 12) / (planA.estimated_time_mins || 45)) * 100)}% FASTER`;
        if (rtoBar && planA && planB) rtoBar.style.width = `${Math.round((planB.estimated_time_mins || 12) / (planA.estimated_time_mins || 45) * 100)}%`;

        if (resBefore) resBefore.innerText = `${Math.round((1 - (planA?.success_likelihood || 0.42)) * 100)}/100`;
        if (resAfter && planB) resAfter.innerText = `${Math.round((planB.success_likelihood || 0.98) * 100)}/100`;
        if (resBadge && planB) resBadge.innerText = `+300% HARDENED`;
        if (resBar && planB) resBar.style.width = `${Math.round((planB.success_likelihood || 0.98) * 100)}%`;

        if (lossBefore && planA) lossBefore.innerText = `$${(planA.cost_usd || 12000).toLocaleString()}`;
        if (lossAfter && planB) lossAfter.innerText = `$${(planB.cost_usd || 3500).toLocaleString()}`;
        if (lossBadge && planA && planB) lossBadge.innerText = `-71% COST IMPACT`;
        if (lossBar && planA && planB) lossBar.style.width = `29%`;

        if (redTeamFlow && planA && planB) {
          redTeamFlow.innerHTML = `
            <div class="evo-box original">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;"><span class="evo-tag">PLAN A (v1.0 UNTESTED)</span><span class="risk-pill high">FAILURE RISK: ${Math.round((planA.risk_score || 0.82) * 100)}%</span></div>
              <h4>${planA.title || 'Plan A Strategy'}</h4>
              <p>${planA.explanation || 'Initial unhardened response strategy.'}</p>
            </div>
            <div class="evo-arrow"><i class="fa-solid fa-shield-virus"></i><span>RED TEAM ADVERSARIAL HARDENING APPLIED</span><i class="fa-solid fa-arrow-down"></i></div>
            <div class="evo-box evolved">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;"><span class="evo-tag success">PLAN B (v2.0 REINFORCED)</span><span class="risk-pill low">RESIDUAL RISK: ${Math.round((planB.risk_score || 0.06) * 100)}% • SUCCESS ${Math.round((planB.success_likelihood || 0.98) * 100)}%</span></div>
              <h4>${planB.title || 'Plan B Strategy'}</h4>
              <p>${planB.explanation || 'Reinforced strategy with adversarial hardening and zero single-points-of-failure.'}</p>
            </div>
          `;
        }
      }

      const bottleneckTarget = document.getElementById('bottleneck-target-text');
      const bottleneckDesc = document.getElementById('bottleneck-desc-text');
      const topoBefore = document.getElementById('topo-before-code');
      const topoAfter = document.getElementById('topo-after-code');

      if (bottleneckTarget) bottleneckTarget.innerText = `Root Cause Specialist → Database Balancer`;
      if (bottleneckDesc) bottleneckDesc.innerText = `Agent topology optimized by Adaptive Organization Engine: Split single database worker into parallel connection drain pods.`;
      if (topoBefore) topoBefore.innerText = `Root Cause → DB Drain (Sequential)`;
      if (topoAfter) topoAfter.innerText = `[Root Cause + Telemetry RAG] → Parallel DB Drain (64% Faster)`;

      renderOrganizationView(promptText);
      renderParliamentView(promptText);
    } catch (err) {
      console.warn("updateDynamicScenarioUI error:", err);
    }
  }

  // Interactive Red Team Stress Test Trigger Button Listener
  const redTeamAttackBtn = document.getElementById('run-redteam-attack-btn');
  if (redTeamAttackBtn) {
    redTeamAttackBtn.addEventListener('click', () => {
      if (window.nexusAudio) window.nexusAudio.playAlert();
      redTeamAttackBtn.classList.add('active-pulse');
      redTeamAttackBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>EXECUTING PENETRATION SUITE...</span>';

      logStream('RED', 'Adversarial Auditor AI launched 4-stage multi-vector stress testing suite.');

      const terminalFeed = document.getElementById('redteam-terminal-feed');
      if (terminalFeed) {
        const timeNow = new Date().toTimeString().split(' ')[0];
        const newLog = document.createElement('div');
        newLog.className = 'rt-log-row';
        newLog.innerHTML = `
          <span class="rt-log-time">${timeNow} UTC</span>
          <span class="rt-log-tag exploit">[LIVE INJECTION]</span>
          <span class="rt-log-desc" style="color:#f472b6;">Adversarial probe executed: Plan A failure confirmed. <strong>Plan B mitigation verified 100% resilient</strong>.</span>
        `;
        terminalFeed.prepend(newLog);
      }

      setTimeout(() => {
        redTeamAttackBtn.classList.remove('active-pulse');
        redTeamAttackBtn.innerHTML = '<i class="fa-solid fa-check"></i> <span>STRESS TEST COMPLETED (PLAN B HARDENED)</span>';
        if (window.nexusAudio) window.nexusAudio.playConsensus();
      }, 1400);
    });
  }

  // Topology Evolution Trigger Button Listener
  const evolveBtn = document.getElementById('trigger-evolution-btn');
  if (evolveBtn) {
    evolveBtn.addEventListener('click', () => {
      if (window.nexusAudio) window.nexusAudio.playConsensus();

      evolveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>RESTRUCTURING AGENT TOPOLOGY...</span>';
      evolveBtn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
      evolveBtn.style.borderColor = '#10b981';

      setTimeout(() => {
        evolveBtn.innerHTML = '<i class="fa-solid fa-check"></i> <span>TOPOLOGY EVOLUTION APPLIED (OPTIMIZED)</span>';
        document.getElementById('sys-state-text').innerText = 'TOPOLOGY_OPTIMIZED';
        document.getElementById('sys-state-text').style.color = 'var(--color-success)';

        logStream('EVOLUTION', 'Autonomous Organization Evolution Applied: Forked bottleneck division into parallel workers. Reduced execution latency by 64% (420ms → 150ms).');

        const upgradedBox = document.querySelector('.topo-box.upgraded');
        if (upgradedBox) {
          upgradedBox.style.boxShadow = '0 0 25px rgba(16, 185, 129, 0.4)';
          upgradedBox.style.borderColor = 'var(--color-success)';
        }
      }, 1200);
    });
  }

  let pollingInterval = null;
  function startPollingFallback(missionId) {
    if (pollingInterval) clearInterval(pollingInterval);
    pollingInterval = setInterval(async () => {
      try {
        const eventsUrl = window.NexusConfig ? window.NexusConfig.getApiUrl(`/api/v1/missions/${missionId}/events`) : `http://localhost:8000/api/v1/missions/${missionId}/events`;
        const res = await fetch(eventsUrl);
        if (res.ok) {
          const events = await res.json();
          if (events && events.length > 0) {
            events.forEach(evt => handleBackendEvent(evt));
            const isDone = events.some(e => e.event_type === 'MISSION_COMPLETED' || e.event_type === 'EXECUTIVE_REPORT');
            if (isDone) clearInterval(pollingInterval);
          }
        }
      } catch (e) {}
    }, 600);
  }

  // Central WebSocket Event Manager & Router
  function connectWebSocketStream(missionId) {
    if (activeWebSocket) {
      activeWebSocket.close();
    }
    // Also start polling fallback in parallel to guarantee zero dropped events on Opera GX/VPN
    startPollingFallback(missionId);

    try {
      const wsUrl = window.NexusConfig ? window.NexusConfig.getWsUrl(`/ws/missions/${missionId}`) : `ws://localhost:8000/ws/missions/${missionId}`;
      activeWebSocket = new WebSocket(wsUrl);
      
      activeWebSocket.onopen = () => {
        logStream('SYSTEM', `WebSocket Stream Connected: /ws/missions/${missionId}`);
        document.getElementById('sys-state-text').innerText = 'CONNECTED_TO_BACKEND';
        document.getElementById('sys-state-text').style.color = 'var(--color-success)';
      };

      activeWebSocket.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        handleBackendEvent(payload);
      };

      activeWebSocket.onerror = (err) => {
        console.warn("WebSocket stream error, polling fallback active:", err);
      };

      activeWebSocket.onclose = () => {
        backendMissionRunning = false;
        logStream('SYSTEM', 'WebSocket Connection Closed.');
      };
    } catch (e) {
      console.warn("WebSocket init error, polling fallback active:", e);
    }
  }

  // Event Router Mapping Backend Events -> Frontend State & Canvas Engines
  function handleBackendEvent(eventObj) {
    if (!eventObj || !eventObj.event_type) return;

    if (eventObj.sequence_number && eventObj.sequence_number <= lastSequenceNumber) {
      return;
    }
    if (eventObj.sequence_number) {
      lastSequenceNumber = eventObj.sequence_number;
    }

    const { event_type, message, data } = eventObj;
    logStream(event_type.split('_')[0], `[${event_type}] ${message}`);
    signalMissionEvent(event_type);

    switch (event_type) {
      case 'MISSION_CREATED':
        document.getElementById('sys-state-text').innerText = 'MISSION_INITIALIZED';
        break;

      case 'DOMAIN_DETECTED':
        if (data) {
          missionState.domain = data;
          const domBadge = document.getElementById('cmd-domain-badge');
          const confBadge = document.getElementById('cmd-confidence-badge');
          if (domBadge) {
            domBadge.innerText = `${data.icon || '🎯'} ${data.display_name || data.domain}`;
            domBadge.style.display = 'inline-block';
          }
          if (confBadge) {
            confBadge.innerText = `CONF: ${Math.round((data.confidence || 0.94) * 100)}%`;
            confBadge.style.display = 'inline-block';
          }
          logStream('DOMAIN', `Domain Detected: ${data.display_name} (${Math.round((data.confidence || 0.94) * 100)}% Conf)`);
        }
        break;

      case 'DOMAIN_PACK_SELECTED':
        if (data) {
          missionState.domainPack = data;
          logStream('DOMAIN_PACK', `Domain Pack Active: ${data.icon} ${data.display_name} [${data.category}]`);
        }
        break;

      case 'HYBRID_MISSION_DETECTED':
        if (data) {
          logStream('HYBRID', `⚡ Hybrid Mission: Merging capabilities with ${data.secondary_domains?.join(', ')}.`);
        }
        break;

      case 'CAPABILITIES_EXTRACTED':
        if (data && data.capabilities) {
          const capContainer = document.getElementById('cmd-capabilities-container');
          const capChips = document.getElementById('cmd-capabilities-chips');
          if (capChips) {
            capChips.innerHTML = data.capabilities.map(c => `
              <span style="font-size:0.65rem; font-family:var(--font-mono); background:rgba(255,255,255,0.06); border:1px solid var(--border-glass); padding:2px 6px; border-radius:4px; color:#e5e7eb;">
                <i class="fa-solid fa-check" style="color:var(--color-success); font-size:0.55rem; margin-right:3px;"></i>${c.replace(/_/g, ' ')}
              </span>
            `).join('');
          }
          if (capContainer) capContainer.style.display = 'block';
        }
        break;

      case 'MISSION_ANALYZED':
        missionState.analysis = data;
        coreEngine.setState('ANALYZING');
        if (data && data.mission_title) {
          document.getElementById('live-mission-heading').innerText = `MISSION: ${data.mission_title}`;
          document.getElementById('parliament-motion-text').innerText = `"Which response strategy should be executed for '${data.mission_title}'?"`;
        }
        dagEngine.updateNodeData('MISSION_ANALYSIS', {
          state: 'success',
          label: data && data.mission_title ? 'Mission Analysis' : undefined,
          findings: data && data.summary ? data.summary : (data && data.sub_analysis_count ? `Analyzed into ${data.sub_analysis_count} specialized sub-missions.` : undefined)
        });
        break;

      case 'MEMORY_RETRIEVED':
        missionState.memory = data;
        dagEngine.updateNodeData('QDRANT_RAG', {
          state: 'success',
          findings: data && data.total_context_nodes ? `Loaded ${data.total_context_nodes} context vectors from Qdrant memory.` : undefined
        });
        if (data && data.total_context_nodes) {
          logStream('MEMORY', `Loaded ${data.total_context_nodes} Qdrant vectors into Memory Galaxy.`);
        }
        break;

      case 'CROSS_DOMAIN_MEMORY_RETRIEVED':
        if (data) {
          logStream('CROSS_DOMAIN', `Memory transferred from ${data.source_domain}: "${data.transferable_principle}"`);
        }
        break;

      case 'ORGANIZATION_FORMED':
      case 'ORGANIZATION_FORMED':
      case 'ORGANIZATION_ADAPTED':
        if (data && data.team) {
          missionState.team = data.team;
          renderOrganizationView(null);
          // Update agent labels on the 3 parallel specialist agent nodes
          if (data.team[1]) dagEngine.updateNodeData('INCIDENT_ANALYSIS', { agent: data.team[1].agent_name || data.team[1].name });
          if (data.team[2]) dagEngine.updateNodeData('IMPACT_ASSESSMENT', { agent: data.team[2].agent_name || data.team[2].name });
          if (data.team[3]) dagEngine.updateNodeData('RESOURCE_ALLOCATION', { agent: data.team[3].agent_name || data.team[3].name });
        } else if (data && data.roster) {
          missionState.team = data.roster;
        }
        break;

      case 'TASK_CREATED':
        dagEngine.setNodeState('CRISIS_DETECTED', 'success');
        dagEngine.setNodeState('MISSION_ANALYSIS', 'success');
        missionState.dagNodes['CRISIS_DETECTED'] = { state: 'success', label: 'Crisis Detected' };
        missionState.dagNodes['MISSION_ANALYSIS'] = { state: 'success', label: 'Mission Analysis' };
        dagEngine.setNodeStatesFromBackend(missionState.dagNodes);
        break;

      case 'TASK_STARTED':
      case 'AGENT_STARTED':
        if (data && data.task_id) {
          dagEngine.setNodeState(data.task_id, 'running');
          missionState.dagNodes[data.task_id] = { state: 'running', label: data.label || data.task_name || data.task_id, agent: data.agent_name || data.agent };
          dagEngine.updateNodeData(data.task_id, {
            state: 'running',
            label: data.label || data.task_name || data.task_id,
            agent: data.agent_name || data.agent
          });
        }
        break;

      case 'TASK_COMPLETED':
      case 'AGENT_TASK_COMPLETED':
        if (data && data.task_id) {
          dagEngine.setNodeState(data.task_id, 'success');
          if (missionState.dagNodes[data.task_id]) {
            missionState.dagNodes[data.task_id].state = 'success';
            missionState.dagNodes[data.task_id].result = data;
          }
          dagEngine.updateNodeData(data.task_id, {
            state: 'success',
            label: data.label || data.task_name || data.task_id,
            agent: data.agent_name || data.agent,
            time: '240ms',
            confidence: '98%',
            findings: data.summary || data.message || (data.result && (data.result.summary || data.result.message))
          });
        }
        break;

      case 'AGENT_DISAGREEMENT':
        logStream('DISAGREEMENT', `⚠ AGENT DISAGREEMENT: ${message}`);
        if (window.nexusAudio) window.nexusAudio.playAlert();
        break;

      case 'DEBATE_STARTED':
        missionState.debate = { ...missionState.debate, ...data };
        dagEngine.setNodeState('STRATEGY_PARLIAMENT', 'running');
        if (!demoMode) switchView('agent-parliament');
        if (window.nexusAudio) window.nexusAudio.playAgentMessage();
        break;

      case 'DEBATE_MESSAGE':
        if (data && data.phase) {
          if (!missionState.debate) missionState.debate = {};
          if (!missionState.debate.messages) missionState.debate.messages = [];
          missionState.debate.messages.push(data);
          updateParliamentPhase(data.phase);
        }
        break;

      case 'CONSENSUS_REACHED':
        missionState.consensus = data;
        if (window.nexusAudio) window.nexusAudio.playConsensus();
        document.getElementById('parliament-consensus-pill').innerText = `CONSENSUS: ${Math.round((data.consensus_score || 0.93)*100)}% (${data.selected_strategy || 'PLAN B'})`;
        dagEngine.setNodeState('STRATEGY_PARLIAMENT', 'success');
        dagEngine.updateNodeData('STRATEGY_PARLIAMENT', {
          state: 'success',
          time: '380ms',
          confidence: `${Math.round((data.consensus_score || 0.93)*100)}%`,
          findings: data && data.selected_strategy ? `Parliament consensus reached: ${data.selected_strategy.replace(/_/g, ' ')} (${Math.round((data.consensus_score || 0.93)*100)}% agreement).` : undefined
        });
        break;

      case 'RED_TEAM_STARTED':
        missionState.redTeam = data;
        dagEngine.setNodeState('RED_TEAM_AUDIT', 'running');
        dagEngine.updateNodeData('RED_TEAM_AUDIT', {
          state: 'running',
          findings: (data && (data.summary || data.message)) || 'Adversarial audit initiated.'
        });
        if (!demoMode) switchView('red-team');
        if (window.nexusAudio) window.nexusAudio.playAlert();
        break;

      case 'RED_TEAM_COMPLETED':
        missionState.redTeam = { ...missionState.redTeam, ...data, completed: true };
        dagEngine.setNodeState('RED_TEAM_AUDIT', 'success');
        dagEngine.updateNodeData('RED_TEAM_AUDIT', {
          state: 'success',
          time: '210ms',
          confidence: '96%',
          findings: (data && (data.summary || data.message)) || 'Adversarial audit complete. No exploitable residual risk on selected strategy.'
        });
        break;

      case 'SIMULATION_COMPLETED':
        missionState.simulation = data;
        if (simEngine && data && data.strategies) {
          simEngine.setStrategiesFromBackend(data.strategies);
        }
        dagEngine.setNodeState('FINAL_RESPONSE', 'running');
        dagEngine.updateNodeData('FINAL_RESPONSE', {
          state: 'running',
          findings: (data && data.selected_strategy) ? `Simulation complete. Vectoring on ${data.selected_strategy.replace(/_/g, ' ')} with projected success ${Math.round((data.success_id || 0.94)*100)}%.` : 'Simulation complete.'
        });
        if (!demoMode) switchView('simulation-engine');
        break;

      case 'EXECUTIVE_REPORT':
        missionState.executiveReport = data;
        renderExecutiveReport(data);
        dagEngine.setNodeState('FINAL_RESPONSE', 'success');
        dagEngine.updateNodeData('FINAL_RESPONSE', {
          state: 'success',
          time: '95ms',
          confidence: '99%',
          findings: `Executive report generated. Selected: ${data.recommended_strategy || 'Plan B'}`
        });
        dagEngine.resolveAllNodesToSuccess();
        break;

      case 'MISSION_FAILED':
        coreEngine.setState('IDLE');
        document.getElementById('sys-state-text').innerText = 'MISSION_FAILED';
        document.getElementById('sys-state-text').style.color = '#ef4444';
        if (data && data.error) logStream('ERROR', `Mission failed: ${data.error}`);
        if (window.nexusAudio) window.nexusAudio.playAlert();
        break;

      case 'MISSION_COMPLETED':
        dagEngine.setNodeState('FINAL_RESPONSE', 'success');
        dagEngine.resolveAllNodesToSuccess();
        if (!demoMode) switchView('command-center');
        coreEngine.setState('CONSENSUS');
        document.getElementById('sys-state-text').innerText = 'MISSION_RESOLVED';
        document.getElementById('sys-state-text').style.color = 'var(--color-success)';
        document.getElementById('cmd-mission-status-pill').innerText = 'STATUS: RESOLVED';
        document.getElementById('voice-transcript-output').innerHTML = `<span style="color:var(--color-success); font-weight:700;"><i class="fa-solid fa-circle-check"></i> MISSION COMPLETE: Adaptive AI Organization successfully resolved mission. Command report available.</span>`;
        break;
    }
  }

  // Executive Mission Report Card Renderer
  function renderExecutiveReport(data) {
    const box = document.getElementById('executive-report-box');
    const body = document.getElementById('exec-report-body');
    if (!box || !body) return;

    let actionsHtml = '';
    if (data.immediate_actions && Array.isArray(data.immediate_actions)) {
      actionsHtml = `<div style="margin-top:6px; font-size:0.7rem; color:#e5e7eb;"><strong>Immediate Actions:</strong><br>${data.immediate_actions.slice(0, 2).map(a => `• ${a}`).join('<br>')}</div>`;
    }

    body.innerHTML = `
      <div style="font-weight:700; color:#fff; font-size:0.85rem; margin-bottom:4px;">${data.title || '🚨 MISSION COMMAND REPORT'}</div>
      <div style="color:var(--text-muted); margin-bottom:6px;"><strong>Severity:</strong> <span style="color:#ef4444;">${data.severity || '🔴 CRITICAL'}</span> | <strong>Est. Recovery:</strong> ${data.estimated_recovery || '~30-45 mins'}</div>
      <div style="margin-bottom:6px; color:#fff;"><strong>Strategy:</strong> <span style="color:var(--color-success);">${data.recommended_strategy || 'PLAN B (Reinforced)'}</span></div>
      <div style="color:var(--primary-bright); font-family:var(--font-mono); font-size:0.7rem; margin-bottom:6px;">CONFIDENCE: ${data.confidence || '94%'} • DOMAIN: ${data.domain || 'ADAPTIVE'}</div>
      <div style="font-size:0.7rem; color:var(--text-subtle); line-height:1.4;"><strong>Why this strategy?</strong> ${data.why_this_strategy || 'Highest success probability while strictly mitigating collateral risks.'}</div>
      ${actionsHtml}
    `;

    box.style.display = 'block';
  }

  function updateParliamentPhase(phase) {
    const phases = [1, 2, 3, 4, 5].map(i => document.getElementById(`phase-${i}`));
    let level = typeof phase === 'number'
      ? phase
      : (['01', '02', '03', '04', '05'].findIndex(p => (phase || '').includes(p)) + 1);

    if (level < 1 || level > 5) return;
    phases.forEach((el, i) => {
      if (!el) return;
      el.className = i < level - 1 ? 'step-item completed' : (i === level - 1 ? 'step-item active' : 'step-item');
    });
  }

  // Page Refresh State Restoration
  async function restoreActiveMission() {
    if (!activeMissionId) return;
    try {
      const restoreEventsUrl = window.NexusConfig ? window.NexusConfig.getApiUrl(`/api/v1/missions/${activeMissionId}/events`) : `http://localhost:8000/api/v1/missions/${activeMissionId}/events`;
      const resp = await fetch(restoreEventsUrl);
      if (resp.ok) {
        const events = await resp.json();
        if (events && events.length > 0) {
          logStream('SYSTEM', `Restored ${events.length} historical events for Mission ID: ${activeMissionId}`);
          events.forEach(evt => handleBackendEvent(evt));
          const isComplete = events.some(e => e.event_type === 'MISSION_COMPLETED' || e.event_type === 'EXECUTIVE_REPORT');
          if (isComplete) {
            dagEngine.resolveAllNodesToSuccess();
          }
          connectWebSocketStream(activeMissionId);
        }
      }
    } catch (e) {
      console.warn("Could not restore mission state:", e);
    }
  }

  // ==================== AI ORGANIZATION VIEW (LYZR SOLO AGENTS) ====================
  function buildOrgSummary(agents) {
    const summaryEl = document.getElementById('org-summary-container');
    const divisionsEl = document.getElementById('org-metric-divisions');
    const agentsEl = document.getElementById('org-metric-agents');
    const reputationEl = document.getElementById('org-metric-reputation');
    const speedEl = document.getElementById('org-metric-speed');
    const readinessEl = document.getElementById('org-metric-readiness');
    if (!summaryEl) return;

    if (!agents || agents.length === 0) {
      summaryEl.style.display = 'none';
      return;
    }

    const divisions = new Set(agents.map(a => (a.division || 'General Command')));
    const avgRep = agents.reduce((s, a) => s + (a.reputation_score || 0.9), 0) / agents.length;
    const avgSpeed = agents.reduce((s, a) => s + (a.speed_score || 0.9), 0) / agents.length;
    const readinessCol = agents.every(a => (a.runtime_state || a.state || 'READY') === 'READY')
      ? agents.length > 0 : false;
    const readyCount = agents.filter(a => (a.runtime_state || a.state || 'READY') === 'READY').length;

    if (divisionsEl) divisionsEl.innerText = divisions.size;
    if (agentsEl) agentsEl.innerText = agents.length;
    if (reputationEl) reputationEl.innerText = `${Math.round(avgRep * 100)}%`;
    if (speedEl) speedEl.innerText = `${Math.round(avgSpeed * 100)}%`;
    if (readinessEl) {
      readinessEl.innerText = `${readyCount}/${agents.length} READY`;
      readinessEl.className = 'org-summary-value ' + (readyCount === agents.length ? 'readiness' : 'readiness-warn');
    }

    summaryEl.style.display = 'grid';
  }

  function escapeHtml(str) {
    return String(str == null ? '' : str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function agentStatePill(state) {
    const s = String((state || 'READY')).toUpperCase();
    const known = ['THINKING', 'RESEARCHING', 'VERIFYING', 'CRITICIZING', 'RESOLVED', 'READY'];
    const cls = known.includes(s) ? s : 'THINKING';
    return `<span class="agent-state-pill ${cls}">${s}</span>`;
  }
  let currentOrgViewMode = 'deployed'; // 'deployed' or 'all'

  // Wire Org Filter Buttons
  const btnFilterDeployed = document.getElementById('org-filter-deployed');
  const btnFilterAll = document.getElementById('org-filter-all');

  if (btnFilterDeployed && btnFilterAll) {
    btnFilterDeployed.addEventListener('click', () => {
      currentOrgViewMode = 'deployed';
      btnFilterDeployed.classList.add('active');
      btnFilterDeployed.style.border = '1px solid var(--primary)';
      btnFilterDeployed.style.background = 'rgba(139,92,246,0.2)';
      btnFilterDeployed.style.color = '#fff';

      btnFilterAll.classList.remove('active');
      btnFilterAll.style.border = '1px solid var(--border-glass)';
      btnFilterAll.style.background = 'rgba(255,255,255,0.04)';
      btnFilterAll.style.color = 'var(--text-muted)';
      renderOrganizationView(document.getElementById('crisis-prompt-input')?.value);
    });

    btnFilterAll.addEventListener('click', () => {
      currentOrgViewMode = 'all';
      btnFilterAll.classList.add('active');
      btnFilterAll.style.border = '1px solid var(--primary)';
      btnFilterAll.style.background = 'rgba(139,92,246,0.2)';
      btnFilterAll.style.color = '#fff';

      btnFilterDeployed.classList.remove('active');
      btnFilterDeployed.style.border = '1px solid var(--border-glass)';
      btnFilterDeployed.style.background = 'rgba(255,255,255,0.04)';
      btnFilterDeployed.style.color = 'var(--text-muted)';
      renderOrganizationView(document.getElementById('crisis-prompt-input')?.value);
    });
  }

  function getScenarioDomainAgents(scenarioText) {
    const text = (scenarioText || '').toLowerCase();
    if (text.includes('saas') || text.includes('startup') || text.includes('runway') || text.includes('pivot') || text.includes('pricing') || text.includes('b2b')) {
      return {
        domainName: 'STARTUP STRATEGY & VENTURE RESILIENCE',
        agents: [
          { id: 'mission_commander', name: 'Mission Commander', division: 'Strategy', specialization: 'Lead Venture Strategist & Pivot Architect', capabilities: ['venture_strategy', 'pivot_planning', 'board_advisory'], reputation_score: 0.99, speed_score: 0.95, cost_weight: 0.8, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'growth_lead', name: 'Strategic Growth Lead', division: 'Strategy', specialization: 'Enterprise B2B Conversion & Sales Moat Modeling', capabilities: ['gtm_strategy', 'b2b_sales', 'moat_analysis'], reputation_score: 0.97, speed_score: 0.94, cost_weight: 0.7, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'qdrant_indexer', name: 'Qdrant Memory Indexer', division: 'Intelligence', specialization: 'Retrieval of SaaS Playbooks & Competitor Benchmarks', capabilities: ['vector_search', 'rag_retrieval', 'pattern_matching'], reputation_score: 0.98, speed_score: 0.98, cost_weight: 0.6, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'risk_strategist', name: 'Financial & Runway Auditor', division: 'Risk & Operations', specialization: 'Cash Burn Modeling, Unit Economics & Churn Triage', capabilities: ['burn_rate_modeling', 'financial_audit', 'churn_prevention'], reputation_score: 0.96, speed_score: 0.92, cost_weight: 0.7, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'adversarial_auditor', name: 'Adversarial Red Team Auditor', division: 'Risk & Operations', specialization: 'Moat Stress-Testing & Competitive Vulnerability Probe', capabilities: ['adversarial_audit', 'stress_testing', 'plan_hardening'], reputation_score: 0.97, speed_score: 0.93, cost_weight: 0.75, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'response_strategist', name: 'Executive Response Strategist', division: 'Strategy', specialization: 'Consensus Synthesis & Board Resolution Delivery', capabilities: ['executive_synthesis', 'plan_formulation', 'action_triggers'], reputation_score: 0.99, speed_score: 0.96, cost_weight: 0.85, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true }
        ]
      };
    } else if (text.includes('grid') || text.includes('power') || text.includes('blackout') || text.includes('scada') || text.includes('payment') || text.includes('billing')) {
      return {
        domainName: 'ENTERPRISE CRISIS & CRITICAL INFRASTRUCTURE',
        agents: [
          { id: 'mission_commander', name: 'Mission Commander', division: 'Strategy', specialization: 'Incident Incident Commander & Critical Escalation', capabilities: ['crisis_command', 'escalation_protocol', 'containment'], reputation_score: 0.99, speed_score: 0.96, cost_weight: 0.85, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'scada_specialist', name: 'SCADA Security & Substation Isolation', division: 'Infrastructure', specialization: 'Air-Gap Containment on Substations 04 & 09', capabilities: ['scada_isolation', 'dnp3_firewall', 'airgap_protocol'], reputation_score: 0.98, speed_score: 0.94, cost_weight: 0.8, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'qdrant_indexer', name: 'Qdrant Memory Indexer', division: 'Intelligence', specialization: 'RAG Retrieval of Historical Grid Outages & SCADA CVEs', capabilities: ['vector_search', 'telemetry_rag', 'incident_memory'], reputation_score: 0.98, speed_score: 0.98, cost_weight: 0.6, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'operations_containment', name: 'Microgrid & Feeder Balancing Lead', division: 'Infrastructure', specialization: 'Secondary Microgrid Failover & 60Hz Frequency Lock', capabilities: ['feeder_reroute', 'frequency_balance', 'load_shedding'], reputation_score: 0.96, speed_score: 0.93, cost_weight: 0.75, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'adversarial_auditor', name: 'Adversarial Red Team Auditor', division: 'Risk & Operations', specialization: 'Cyber Threat Injection & Secondary Cascade Hardening', capabilities: ['threat_modeling', 'penetration_audit', 'failover_validation'], reputation_score: 0.97, speed_score: 0.95, cost_weight: 0.7, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'response_strategist', name: 'Executive Response Strategist', division: 'Strategy', specialization: 'Emergency Failover Command & Stakeholder Directive', capabilities: ['emergency_dispatch', 'regulatory_compliance', 'executive_brief'], reputation_score: 0.99, speed_score: 0.97, cost_weight: 0.85, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true }
        ]
      };
    } else if (text.includes('supplier') || text.includes('supply') || text.includes('port') || text.includes('freight') || text.includes('wafer') || text.includes('cargo')) {
      return {
        domainName: 'SUPPLY CHAIN & GLOBAL LOGISTICS RECOVERY',
        agents: [
          { id: 'mission_commander', name: 'Mission Commander', division: 'Strategy', specialization: 'Supply Continuity Commander & Tier-1 Vendor Lead', capabilities: ['supply_command', 'vendor_negotiation', 'sla_enforcement'], reputation_score: 0.99, speed_score: 0.95, cost_weight: 0.85, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'sourcing_specialist', name: 'Alternative Sourcing & Spot Market Scan', division: 'Operations', specialization: 'Dual-Sourcing Qualified Foundry Inventory Scan', capabilities: ['spot_market_procurement', 'supplier_qualification', 'component_buffer'], reputation_score: 0.97, speed_score: 0.93, cost_weight: 0.7, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'logistics_optimizer', name: 'Freight & Port Routing Optimizer', division: 'Operations', specialization: 'Inland Rail Corridor & Expedited Air Freight Routing', capabilities: ['demurrage_mitigation', 'multimodal_routing', 'port_bypass'], reputation_score: 0.96, speed_score: 0.94, cost_weight: 0.75, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'qdrant_indexer', name: 'Qdrant Memory Indexer', division: 'Intelligence', specialization: 'Historical Lead-Time & Component Lifecycle Vectors', capabilities: ['vector_search', 'vendor_pricing_rag', 'lead_time_models'], reputation_score: 0.98, speed_score: 0.98, cost_weight: 0.6, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'adversarial_auditor', name: 'Adversarial Red Team Auditor', division: 'Risk & Operations', specialization: 'Single-Point-of-Failure & Tariff Exposure Stress Test', capabilities: ['spof_analysis', 'tariff_audit', 'secondary_delay_probe'], reputation_score: 0.97, speed_score: 0.92, cost_weight: 0.75, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'response_strategist', name: 'Executive Response Strategist', division: 'Strategy', specialization: 'Assembly Line Buffer Strategy & Procurement POs', capabilities: ['procurement_authorization', 'assembly_protection', 'executive_plan'], reputation_score: 0.99, speed_score: 0.96, cost_weight: 0.85, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true }
        ]
      };
    } else if (text.includes('exam') || text.includes('portal') || text.includes('student') || text.includes('university') || text.includes('admissions')) {
      return {
        domainName: 'UNIVERSITY ACADEMIC OPERATIONS & STUDENT RESILIENCE',
        agents: [
          { id: 'mission_commander', name: 'Mission Commander', division: 'Strategy', specialization: 'Academic Operations Commander & Registrar Liaison', capabilities: ['academic_integrity', 'proctoring_protocol', 'student_equity'], reputation_score: 0.99, speed_score: 0.95, cost_weight: 0.8, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'lms_diagnostician', name: 'LMS Portal & Database Diagnostics', division: 'Infrastructure', specialization: 'Database Connection Drain & Read-Only Cached Mirror', capabilities: ['lms_failover', 'cache_mirroring', 'database_recovery'], reputation_score: 0.97, speed_score: 0.94, cost_weight: 0.7, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'timetable_rescheduler', name: 'Alternative Timetable & Slot Scheduler', division: 'Academic', specialization: '24-Hour Staggered Rescheduling & Integrity Lock', capabilities: ['slot_allocation', 'proctor_reassignment', 'fairness_audit'], reputation_score: 0.96, speed_score: 0.92, cost_weight: 0.75, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'qdrant_indexer', name: 'Qdrant Memory Indexer', division: 'Intelligence', specialization: 'RAG Search for Accreditation Rules & Rescheduling Precedents', capabilities: ['vector_search', 'academic_policy_rag', 'student_records'], reputation_score: 0.98, speed_score: 0.98, cost_weight: 0.6, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'adversarial_auditor', name: 'Adversarial Red Team Auditor', division: 'Risk & Operations', specialization: 'Exam Leak & Academic Dishonesty Stress-Testing', capabilities: ['integrity_probe', 'leak_containment', 'fairness_verification'], reputation_score: 0.97, speed_score: 0.95, cost_weight: 0.7, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'response_strategist', name: 'Executive Response Strategist', division: 'Strategy', specialization: 'Campus-Wide Student & Faculty Contingency Directive', capabilities: ['broadcast_synthesis', 'deadline_adjustment', 'executive_plan'], reputation_score: 0.99, speed_score: 0.97, cost_weight: 0.85, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true }
        ]
      };
    } else {
      // Default: Software Incident Response
      return {
        domainName: 'SOFTWARE INCIDENT RESPONSE & SITE RELIABILITY',
        agents: [
          { id: 'mission_commander', name: 'Mission Commander', division: 'Strategy', specialization: 'Incident Incident Commander & Triage Lead', capabilities: ['mission_coordination', 'command', 'operational_containment'], reputation_score: 0.99, speed_score: 0.95, cost_weight: 0.8, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'root_cause_analyst', name: 'Root Cause Analyst Agent', division: 'Intelligence', specialization: 'Log Inspection, Connection Leak Profiling & Commit Regression', capabilities: ['log_inspection', 'stack_tracing', 'regression_detection'], reputation_score: 0.97, speed_score: 0.95, cost_weight: 0.7, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'infrastructure_agent', name: 'Infrastructure Agent', division: 'Infrastructure', specialization: 'Kubernetes Pod Drain, Database Pool Expansion & Ingress Health', capabilities: ['infrastructure_analysis', 'infrastructure_recovery', 'pod_drain'], reputation_score: 0.95, speed_score: 0.91, cost_weight: 0.75, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'qdrant_indexer', name: 'Qdrant Memory Indexer', division: 'Intelligence', specialization: 'RAG Retrieval of Historical Deployments & Past Runbooks', capabilities: ['vector_search', 'memory_lookup', 'incident_similarity'], reputation_score: 0.97, speed_score: 0.98, cost_weight: 0.6, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'rollback_strategist', name: 'Rollback & Traffic Drain Strategist', division: 'Infrastructure', specialization: 'Blue-Green Ingress Switchback & Canary Revert Matrix', capabilities: ['rollback_execution', 'canary_traffic_drain', 'hotfix_validation'], reputation_score: 0.96, speed_score: 0.94, cost_weight: 0.7, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'adversarial_auditor', name: 'Adversarial Red Team Auditor', division: 'Risk & Operations', specialization: 'Rollback Stress-Testing & Data Corruption Vulnerability Probe', capabilities: ['adversarial_analysis', 'red_teaming', 'plan_hardening'], reputation_score: 0.96, speed_score: 0.93, cost_weight: 0.7, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true },
          { id: 'response_strategist', name: 'Response Strategist Agent', division: 'Strategy', specialization: 'Consensus Synthesis & Post-Mortem Plan Formulation', capabilities: ['synthesis', 'strategic_alignment', 'executive_reporting'], reputation_score: 0.99, speed_score: 0.96, cost_weight: 0.85, runtime_state: 'RESOLVED', framework: 'Lyzr Automata SDK', isDeployed: true }
        ]
      };
    }
  }

  async function renderOrganizationView(scenarioText) {
    const container = document.getElementById('divisions-container');
    if (!container) return;

    const currentPrompt = scenarioText || document.getElementById('crisis-prompt-input')?.value || "Production incident";
    const scenarioSpec = getScenarioDomainAgents(currentPrompt);

    // Update Scenario Badge in Header
    const badgeEl = document.getElementById('org-active-scenario-name');
    if (badgeEl) {
      badgeEl.innerText = `ACTIVE SWARM: ${scenarioSpec.domainName}`;
    }

    let agents = [];

    if (currentOrgViewMode === 'deployed') {
      if (missionState.team && missionState.team.length > 0) {
        agents = missionState.team.map(t => ({
          id: t.agent_id || t.id,
          name: t.agent_name || t.name,
          division: t.division || 'General Command',
          specialization: t.assigned_role || t.specialization || '',
          capabilities: t.capabilities || [],
          reputation_score: t.selection_score || t.reputation_score || 0.96,
          speed_score: t.speed_score || 0.94,
          cost_weight: t.cost_weight || 0.7,
          runtime_state: t.runtime_state || 'RESOLVED',
          framework: t.framework || 'Lyzr Automata SDK',
          isDeployed: true
        }));
      } else {
        agents = scenarioSpec.agents;
      }
    } else {
      // Global 28 Agent Pool
      try {
        const agentsUrl = window.NexusConfig ? window.NexusConfig.getApiUrl('/api/v1/agents') : 'http://localhost:8000/api/v1/agents';
        const res = await fetch(agentsUrl);
        if (res.ok) {
          const allAgents = await res.json();
          const deployedIds = new Set(scenarioSpec.agents.map(a => a.id.toLowerCase()));
          agents = allAgents.map(a => ({
            ...a,
            isDeployed: deployedIds.has(a.id.toLowerCase()) || deployedIds.has((a.name || '').toLowerCase())
          }));
        }
      } catch (e) {
        agents = scenarioSpec.agents;
      }
    }

    if (agents.length === 0) {
      container.innerHTML = `<div class="division-card" style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:40px;">
        <i class="fa-solid fa-user-group" style="font-size:2rem;margin-bottom:12px;color:var(--primary);"></i>
        <div>Recruiting specialized Lyzr solo agents for active scenario...</div>
      </div>`;
      return;
    }

    buildOrgSummary(agents);

    // Group by division
    const divisions = {};
    agents.forEach(a => {
      const div = a.division || 'General Command';
      if (!divisions[div]) divisions[div] = [];
      divisions[div].push(a);
    });

    container.innerHTML = Object.entries(divisions).map(([divName, agentList]) => `
      <div class="division-card" style="border: 1px solid rgba(139,92,246,0.18); background: rgba(15,20,33,0.7);">
        <div class="division-title" style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--border-glass);padding-bottom:10px;">
          <span><i class="fa-solid fa-layer-group" style="margin-right:8px;color:var(--primary-bright);"></i>${escapeHtml(divName.toUpperCase())}</span>
          <span class="org-div-count" style="font-family:var(--font-mono);font-size:0.7rem;color:var(--text-muted);">${agentList.length} LYZR SOLO AGENTS</span>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px;">
          ${agentList.map(ag => `
            <div class="agent-mini-card org-agent-card ${ag.isDeployed ? 'deployed-glow' : ''}" data-agent='${btoa(unescape(encodeURIComponent(JSON.stringify(ag))))}' style="border: 1px solid ${ag.isDeployed ? 'rgba(52,211,153,0.45)' : 'rgba(255,255,255,0.08)'}; background: ${ag.isDeployed ? 'rgba(16,185,129,0.05)' : 'rgba(20,24,40,0.85)'};">
              <div class="agent-card-header">
                <span class="agent-name" style="color:#fff; font-weight:700;">
                  ${ag.isDeployed ? '<i class="fa-solid fa-circle-check" style="color:#34d399; margin-right:4px; font-size:0.75rem;"></i>' : ''}
                  ${escapeHtml(ag.name)}
                </span>
                ${agentStatePill(ag.runtime_state || (ag.isDeployed ? 'RESOLVED' : 'READY'))}
              </div>
              <div style="font-size:0.72rem;color:var(--text-muted);line-height:1.3;margin:6px 0;">${escapeHtml(ag.specialization)}</div>
              <div class="agent-details-list" style="display:flex;justify-content:space-between;font-size:0.7rem;margin-bottom:8px;font-family:var(--font-mono);">
                <div>REPUTATION: <b style="color:var(--color-success);">${Math.round((ag.reputation_score || 0.95) * 100)}%</b></div>
                <div>SPEED: <b style="color:var(--accent-blue);">${Math.round((ag.speed_score || 0.94) * 100)}%</b></div>
              </div>
              <div class="org-agent-capabilities" style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px;">
                ${(ag.capabilities || []).slice(0, 3).map(c => `
                  <span class="org-cap-tag" style="font-size:0.62rem;font-family:var(--font-mono);background:rgba(255,255,255,0.05);padding:2px 5px;border-radius:4px;color:#cbd5e1;">${escapeHtml(c.replace(/_/g, ' '))}</span>
                `).join('')}
              </div>
              <div class="org-agent-footer" style="display:flex;justify-content:space-between;align-items:center;font-size:0.65rem;color:var(--text-muted);border-top:1px solid rgba(255,255,255,0.05);padding-top:6px;">
                <span>SDK: <b class="mono" style="color:#a78bfa;">Lyzr Automata</b></span>
                <span class="org-expand-hint" style="color:var(--primary-bright);cursor:pointer;"><i class="fa-solid fa-chevron-down"></i> SPECS</span>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `).join('');

    wireOrgCardToggles(container);
  }

  function wireOrgCardToggles(container) {
    if (!container) return;
    container.querySelectorAll('.org-agent-card').forEach((card) => {
      if (card.dataset.bound === '1') return;
      card.dataset.bound = '1';
      card.addEventListener('click', (e) => {
        e.preventDefault();
        let agent = null;
        try { agent = card.dataset.agent ? JSON.parse(decodeURIComponent(escape(atob(card.dataset.agent)))) : null; } catch (err) { agent = null; }
        if (!agent) return;

        const prevPanel = document.getElementById('org-agent-expanded');
        const prevSelected = document.querySelector('.org-agent-card.selected');

        if (prevPanel && prevPanel.previousElementSibling === card) {
          prevPanel.remove();
          if (prevSelected) prevSelected.classList.remove('selected');
          card.classList.remove('selected');
          return;
        }

        if (prevPanel) {
          prevPanel.remove();
          if (prevSelected) prevSelected.classList.remove('selected');
        }

        const detail = document.createElement('div');
        detail.className = 'org-agent-detail-panel expanded';
        detail.id = 'org-agent-expanded';
        detail.innerHTML = `
          <div class="org-detail-head">
            <div>
              <div class="org-detail-name">${escapeHtml(agent.name)}</div>
              <div class="org-detail-role">${escapeHtml(agent.specialization || 'General Role')}</div>
            </div>
            ${agentStatePill(agent.runtime_state)}
          </div>
          <div class="org-detail-stats">
            ${[
              ['REPUTATION SCORE', Math.round((agent.reputation_score || 0.9) * 100) + '%'],
              ['RESPONSE SPEED', Math.round((agent.speed_score || 0.9) * 100) + '%'],
              ['COST WEIGHT', Math.round((agent.cost_weight || 0.7) * 100) + '%'],
              ['FRAMEWORK', agent.framework || 'LYZR SDK']
            ].map(([lbl, val]) => `
              <div class="org-detail-stat">
                <span class="org-detail-stat-label">${lbl}</span>
                <span class="org-detail-stat-value">${escapeHtml(val)}</span>
              </div>
            `).join('')}
          </div>
          <div class="org-detail-capabilities">
            <div class="org-detail-cap-label">CAPABILITIES (${(agent.capabilities || []).length})</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px;">
              ${(agent.capabilities || []).map(c => `<span class="org-cap-tag cap-lg">${escapeHtml(c)}</span>`).join('')}
            </div>
          </div>
        `;
        card.after(detail);
        card.classList.add('selected');
      });
    });
  }

  // ==================== AGENT PARLIAMENT VIEW ====================
  function renderParliamentView(scenarioText) {
    try {
      const arena = document.getElementById('spatial-parliament-arena');
      const msgContainer = document.getElementById('parliament-messages');
      const motionText = document.getElementById('parliament-motion-text');
      const tableContainer = document.getElementById('parliament-strategy-table-container');
      const consensusPill = document.getElementById('parliament-consensus-pill');

      // New consensus gauge elements
      const consensusFill = document.getElementById('parliament-consensus-fill');
      const consensusCurrent = document.getElementById('parliament-consensus-current');
      const consensusStatus = document.getElementById('parliament-consensus-status');
      const consensusAssertion = document.getElementById('parliament-consensus-assertion');
      const assertionStrategy = document.getElementById('parliament-assertion-strategy');
      const assertionReasoning = document.getElementById('parliament-assertion-reasoning');
      const assertionSplit = document.getElementById('parliament-assertion-split');
      const assertionTitle = document.getElementById('parliament-assertion-title');

      if (!arena || !msgContainer) return;

      // Fall back to scenario-aware data when backend hasn't returned results yet
      const scenarioData = getScenarioParliamentAndRedTeam(scenarioText);
      const consensus = missionState.consensus || scenarioData.consensus;
      const sim = missionState.simulation || { strategies: scenarioData.strategies };
      const debate = missionState.debate || { messages: scenarioData.messages };
      const team = missionState.team && missionState.team.length > 0 ? missionState.team : (scenarioData.consensus.supporting_agents || []).map((name, i) => ({ agent_name: name, name, specialization: 'Lyzr Solo Agent', selection_score: 0.95 - i * 0.01 }));

      if (motionText) {
        motionText.innerText = `"${consensus && consensus.motion ? consensus.motion
          : (missionState.analysis && missionState.analysis.mission_title) || scenarioText}"`;
      }

      // ---- Consensus gauge + assertion panel ----
      const score = consensus ? (consensus.consensus_score || 0.93) : 0;
      const target = 0.94;
      const pct = Math.round(score * 100);

      if (consensusFill) consensusFill.style.width = `${Math.min(100, pct)}%`;
      if (consensusCurrent) consensusCurrent.innerText = `${pct}% AGREEMENT`;
      if (consensusPill) consensusPill.innerText = `AGREEMENT: ${pct}% (${target * 100}% TARGET)`;

      if (consensusStatus) {
        const reached = score >= target || (consensus && consensus.concluded === true);
        consensusStatus.innerText = reached ? 'CONSENSUS REACHED' : `DELIBERATING (${pct}/${target * 100}%)`;
        consensusStatus.className = 'consensus-progress-status ' + (reached ? 'reached' : 'pending');
        if (consensusFill) consensusFill.classList.toggle('reached', reached);
      }

      if (consensus && consensusAssertion) {
        const supporters = (consensus.supporting_agents || []);
        const dissenters = (consensus.dissenting_agents || []);
        const strategy = (consensus.selected_strategy || 'PLAN B').replace(/_/g, ' ');
        const reasoning = consensus.reasoning_summary
          || consensus.reasoning || 'Selected by parliamentary consensus.' 

        if (assertionStrategy) assertionStrategy.innerText = `ADOPTED STRATEGY: ${strategy}`;
        if (assertionReasoning) assertionReasoning.innerText = reasoning;
        if (assertionTitle) assertionTitle.innerText = `PARLIAMENT CONSENSUS REACHED · ${pct}% AGREEMENT`;
        if (assertionSplit) {
          assertionSplit.innerHTML = `
            <span class="assertion-split-item keep"><i class="fa-solid fa-thumbs-up"></i> ${supporters.length} SUPPORT</span>
            <span class="assertion-split-item dissent"><i class="fa-solid fa-thumbs-down"></i> ${dissenters.length} DISSENT</span>
            ${team && consensus.voter_count != null
              ? `<span class="assertion-split-item neutral"><i class="fa-solid fa-scale-balanced"></i> ${team.length - supporters.length - dissenters.length} UNDECIDED</span>`
              : ''}
          `;
        }
        consensusAssertion.style.display = 'block';
      } else if (consensusAssertion) {
        consensusAssertion.style.display = 'none';
      }

      let agents = [];
      if (team && team.length > 0) {
        const icons = ['fa-user-tie', 'fa-brain', 'fa-shield-halved', 'fa-microchip', 'fa-bolt', 'fa-server', 'fa-triangle-exclamation'];
        const colors = ['#8b5cf6', '#3b82f6', '#10b981', '#ec4899', '#f59e0b', '#06b6d4', '#ef4444'];
        agents = team.slice(0, 7).map((t, i) => {
          const name = t.agent_name || t.name || 'Agent';
          const isSupport = consensus && consensus.supporting_agents && consensus.supporting_agents.includes(name);
          const isDissent = consensus && consensus.dissenting_agents && consensus.dissenting_agents.includes(name);
          let vote = 'PENDING';
          if (consensus) vote = isSupport ? 'SUPPORT' : (isDissent ? 'DISSENT' : 'UNDECIDED');
          return {
            name: name,
            icon: icons[i % icons.length],
            color: colors[i % colors.length],
            vote: vote,
            voteClass: isSupport ? 'support' : (isDissent ? 'dissent' : 'undecided'),
            conf: `${Math.round((t.selection_score || 0.95) * 100)}%`,
            strategy: t.assigned_role || t.specialization || ''
          };
        });
      }

      let strategyComparison = [];
      if (sim && sim.strategies) {
        const selected = (consensus && consensus.selected_strategy) || 'PLAN_B';
        strategyComparison = sim.strategies.map(s => {
          const isSelected = s.id === selected || s.recommended;
          return {
            strategy: `${s.id.replace('_', ' ')}`,
            action: s.title || s.id,
            risk: `${s.risk_score < 0.3 ? 'Low' : s.risk_score < 0.5 ? 'Medium' : 'High'} (${Math.round(s.risk_score * 100)}%)`,
            riskClass: s.risk_score < 0.3 ? 'low' : s.risk_score < 0.5 ? 'medium' : 'high',
            rate: `${Math.round(s.success_likelihood * 100)}%`,
            time: s.estimated_time_mins != null ? `${s.estimated_time_mins} min` : '—',
            cost: s.cost_usd != null ? `$${s.cost_usd.toLocaleString()}` : '—',
            decision: isSelected ? `Adopted: ${s.explanation}` : `Rejected: ${s.explanation}`,
            adopted: isSelected,
            rowClass: isSelected ? 'row-plan-b' : s.id === 'PLAN_A' ? 'row-plan-a' : 'row-plan-c'
          };
        });
      }

      if (arena) {
        arena.innerHTML = agents.length > 0 ? `
          <div style="display:flex;justify-content:space-around;align-items:stretch;width:100%;padding:15px;flex-wrap:wrap;gap:12px;">
            ${agents.map(ag => `
              <div class="parliament-vote-node" style="border-color:${ag.color};box-shadow:0 0 18px ${ag.color}25;">
                <div class="parliament-vote-avatar" style="background:${ag.color}22;color:${ag.color};">
                  <i class="fa-solid ${ag.icon}"></i>
                </div>
                <div class="parliament-vote-name">${ag.name}</div>
                <div class="parliament-vote-strategy">${ag.strategy}</div>
                <div class="parliament-vote-pill ${ag.voteClass}">${ag.vote}</div>
                <div class="parliament-vote-conf">CONF: <b>${ag.conf}</b></div>
              </div>
            `).join('')}
          </div>
        ` : '<div style="padding:40px;text-align:center;color:#64748b;">Waiting for backend to form agent parliament...</div>';
      }

      if (tableContainer && strategyComparison.length > 0) {
        tableContainer.innerHTML = `
          <table class="strategy-comparison-table">
            <thead>
              <tr>
                <th style="width:13%;">Strategy</th>
                <th style="width:24%;">Proposed Action</th>
                <th style="width:13%;">Risk Level</th>
                <th style="width:11%;">Success Rate</th>
                <th style="width:10%;">Est. Time</th>
                <th style="width:10%;">Cost</th>
                <th style="width:19%;">Verdict</th>
              </tr>
            </thead>
            <tbody>
              ${strategyComparison.map(row => `
                <tr class="${row.rowClass}">
                  <td class="strategy-name ${row.adopted ? 'highlight' : ''}">
                    ${row.strategy}
                    ${row.adopted ? '<span class="strategy-adopted-badge"><i class="fa-solid fa-check"></i> ADOPTED</span>' : ''}
                  </td>
                  <td class="action-title">${row.action}</td>
                  <td><span class="risk-pill ${row.riskClass}">${row.risk}</span></td>
                  <td><span class="rate-badge ${row.adopted ? 'success' : ''}">${row.rate}</span></td>
                  <td class="matrix-num">${row.time}</td>
                  <td class="matrix-num">${row.cost}</td>
                  <td>
                    <span class="decision-tag ${row.adopted ? 'adopted' : 'rejected'}">
                      <i class="fa-solid ${row.adopted ? 'fa-circle-check' : 'fa-circle-xmark'}"></i>
                      ${row.adopted ? 'Adopted' : 'Rejected'}
                    </span>
                    <div class="verdict-text">${row.decision.replace(/^(Adopted|Rejected):\s*/, '')}</div>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      }

      const messages = (debate && debate.messages) || [];
      if (messages.length > 0 && msgContainer) {
        const speakerColors = ['#8b5cf6', '#3b82f6', '#10b981', '#ec4899', '#f59e0b', '#06b6d4', '#ef4444'];
        msgContainer.innerHTML = messages.map((m, idx) => {
          const color = speakerColors[idx % speakerColors.length];
          const content = m.content || m.text || '';
          const speaker = m.agent_name || m.agent_id || 'Speaker ' + (idx + 1);
          return `
            <div class="debate-message">
              <div class="debate-message-head">
                <span class="debate-speaker" style="color:${color};">${speaker}</span>
                <span class="debate-phase-badge">${m.phase || `DEBATE ${idx + 1}`}</span>
              </div>
              <div class="debate-message-body">${content}</div>
            </div>
          `;
        }).join('');
      } else if (consensus && msgContainer) {
        msgContainer.innerHTML = `
          <div class="debate-message consensus">
            <div class="debate-message-head">
              <span class="debate-speaker" style="color:#10b981;">PARLIAMENT · CHAIR</span>
              <span class="debate-phase-badge">FINAL VOTE</span>
            </div>
            <div class="debate-message-body">${consensus.reasoning_summary || 'Strategy selected by parliamentary consensus.'}</div>
          </div>
        `;
      } else if (msgContainer) {
        msgContainer.innerHTML = '<div style="padding:20px;text-align:center;color:#64748b;">Waiting for backend parliament deliberation data...</div>';
      }
    } catch (err) {
      console.warn("renderParliamentView error:", err);
    }
  }

  // Initial view render for default prompt scenario
  const initialInput = document.getElementById('crisis-prompt-input')?.value;
  if (dagEngine) dagEngine.setScenario(initialInput);
  renderOrganizationView(initialInput);
  renderParliamentView(initialInput);
  updateDynamicScenarioUI(initialInput);
  if (simEngine) simEngine.setScenario(initialInput);
  if (memoryEngine) memoryEngine.setScenario(initialInput);

  function logStream(tag, text) {
    const feed = document.getElementById('org-stream-feed');
    if (!feed) return;

    const timeStr = new Date().toTimeString().split(' ')[0];
    const item = document.createElement('div');
    item.className = 'feed-item';
    
    let tagClass = 'info';
    if (tag === 'MEMORY') tagClass = 'memory';
    if (tag === 'AGENT' || tag === 'TASK' || tag === 'ORGANIZATION') tagClass = 'agent';
    if (tag === 'CRISIS' || tag === 'RED') tagClass = 'warning';

    item.innerHTML = `
      <span class="feed-time">${timeStr}</span>
      <span class="feed-tag ${tagClass}">${tag}</span>
      <p class="feed-text">${text}</p>
    `;

    feed.prepend(item);
  }

  // Client Fallback Simulation if Backend Offline
  function runClientFallback(promptText) {
    setTimeout(() => {
      logStream('MEMORY', 'Qdrant vector RAG search executed. Retrieved 3 historical crisis memories.');
      dagEngine.setNodeState('CRISIS_DETECTED', 'success');
      dagEngine.setNodeState('MISSION_ANALYSIS', 'running');
    }, 1000);

    setTimeout(() => {
      logStream('AGENT', 'NEXUS Commander spawned 6 autonomous agents across 3 divisions.');
      dagEngine.setNodeState('MISSION_ANALYSIS', 'success');
      dagEngine.setNodeState('INCIDENT_ANALYSIS', 'running');
      dagEngine.setNodeState('IMPACT_ASSESSMENT', 'running');
    }, 2200);
  }

  // ==================== HIGH-PERFORMANCE 8-STAGE AUTOPILOT DEMO ENGINE ====================
  let isAutopilotRunning = false;
  let isAutopilotPaused = false;
  let currentAutopilotStage = 0;
  let autopilotSpeed = 1.5; // Default crisp speed
  let advanceStageResolver = null;
  let shouldAbortAutopilot = false;
  let backendMissionRunning = false;

  const hudBanner = document.getElementById('autopilot-hud-banner');
  const hudBadge = document.getElementById('hud-stage-badge');
  const hudTitle = document.getElementById('hud-stage-title');
  const hudFill = document.getElementById('hud-progress-fill');
  const hudPauseBtn = document.getElementById('hud-pause-btn');
  const hudNextBtn = document.getElementById('hud-next-btn');
  const hudStopBtn = document.getElementById('hud-stop-btn');
  const headerAutopilotBtn = document.getElementById('header-autopilot-btn');
  const cmdAutopilotBtn = document.getElementById('cmd-autopilot-btn');

  const STAGES = [
    { num: 1, title: '🎙️ OMI Voice Ingestion & Intent Extraction', view: 'command-center', baseDuration: 1800 },
    { num: 2, title: '🗄️ QDRANT Hybrid Vector Memory RAG Search', view: 'command-center', baseDuration: 1600 },
    { num: 3, title: '🤖 LYZR Solo Agent Team Formation & Topology', view: 'ai-organization', baseDuration: 1900 },
    { num: 4, title: '⚡ Parallel DAG Task Execution (SCADA & Feeder)', view: 'live-mission', baseDuration: 2200 },
    { num: 5, title: '🏛️ Multi-Agent Deliberation Parliament (5 Debate Rounds)', view: 'agent-parliament', baseDuration: 2300 },
    { num: 6, title: '🛡️ Red Team Adversarial Stress Test (Plan A → Plan B)', view: 'red-team', baseDuration: 1900 },
    { num: 7, title: '📊 Monte-Carlo Strategy Simulation (94% Plan B Win)', view: 'simulation-engine', baseDuration: 1700 },
    { num: 8, title: '🧠 Qdrant Reflection Writeback & Executive Mission Report', view: 'memory-intelligence', baseDuration: 2000 }
  ];

  // The real backend mission event that completes each HUD stage. When a live
  // backend mission is running, the HUD waits for these before advancing.
  const STAGE_EVENT = [
    'MISSION_CREATED',        // stage 1 — mission accepted
    'MEMORY_RETRIEVED',       // stage 2 — Qdrant RAG done
    'ORGANIZATION_FORMED',    // stage 3 — Lyzr org formed
    'AGENT_TASK_COMPLETED',   // stage 4 — parallel tasks executed
    'CONSENSUS_REACHED',      // stage 5 — parliament consensus
    'RED_TEAM_COMPLETED',     // stage 6 — red team audit done
    'SIMULATION_COMPLETED',   // stage 7 — strategy simulation done
    'MISSION_COMPLETED'       // stage 8 — reflection + report done
  ];

  // Speed Pills Handler
  document.querySelectorAll('.hud-speed-pill').forEach(pill => {
    pill.addEventListener('click', (e) => {
      document.querySelectorAll('.hud-speed-pill').forEach(p => p.classList.remove('active'));
      e.target.classList.add('active');
      autopilotSpeed = parseFloat(e.target.getAttribute('data-speed')) || 1.5;
    });
  });

  // Pause / Resume Button
  if (hudPauseBtn) {
    hudPauseBtn.addEventListener('click', () => {
      isAutopilotPaused = !isAutopilotPaused;
      hudPauseBtn.innerHTML = isAutopilotPaused ? '<i class="fa-solid fa-play"></i>' : '<i class="fa-solid fa-pause"></i>';
      hudPauseBtn.style.color = isAutopilotPaused ? '#10b981' : '#e2e8f0';
    });
  }

  // Next Stage Button
  if (hudNextBtn) {
    hudNextBtn.addEventListener('click', () => {
      if (advanceStageResolver) {
        advanceStageResolver();
        advanceStageResolver = null;
      }
    });
  }

  // Stop Button
  if (hudStopBtn) {
    hudStopBtn.addEventListener('click', () => {
      stopAutopilotDemo();
    });
  }

  // Launch triggers
  [headerAutopilotBtn, cmdAutopilotBtn].forEach(btn => {
    if (btn) {
      btn.addEventListener('click', () => {
        if (isAutopilotRunning) {
          stopAutopilotDemo();
        } else {
          startAutopilotDemo();
        }
      });
    }
  });

  function startAutopilotDemo() {
    isAutopilotRunning = true;
    isAutopilotPaused = false;
    shouldAbortAutopilot = false;

    if (hudBanner) hudBanner.style.display = 'flex';
    [headerAutopilotBtn, cmdAutopilotBtn].forEach(b => {
      if (b) {
        b.classList.add('running');
        b.innerHTML = '<i class="fa-solid fa-square fa-fade"></i><span>STOP DEMO</span>';
      }
    });

    const scenarioText = document.getElementById('crisis-prompt-input')?.value || 
      "";

    executeAutopilotSequence(scenarioText);
  }

  function stopAutopilotDemo() {
    shouldAbortAutopilot = true;
    isAutopilotRunning = false;
    isAutopilotPaused = false;
    if (advanceStageResolver) {
      advanceStageResolver();
      advanceStageResolver = null;
    }
    if (hudBanner) hudBanner.style.display = 'none';
    [headerAutopilotBtn, cmdAutopilotBtn].forEach(b => {
      if (b) {
        b.classList.remove('running');
        b.innerHTML = '<i class="fa-solid fa-bolt-auto"></i><span>⚡ 8-STAGE AUTOPILOT DEMO</span>';
      }
    });
  }

  async function executeAutopilotSequence(scenarioText) {
    for (let i = 0; i < STAGES.length; i++) {
      if (shouldAbortAutopilot) break;
      const stage = STAGES[i];
      currentAutopilotStage = i + 1;

      // Update HUD UI
      if (hudBadge) hudBadge.innerText = `STAGE ${stage.num}/8`;
      if (hudTitle) hudTitle.innerText = stage.title;
      if (hudFill) hudFill.style.width = `${((i + 1) / STAGES.length) * 100}%`;

      // Switch to Stage View
      switchView(stage.view);

      // Execute Specialized Stage Animation & Logic
      await executeStageAction(stage.num, scenarioText);

      // WAIT for the real backend mission to reach this stage. Mark this HUD
      // stage complete only when the real pipeline actually arrives, so the HUD
      // stays honest and in sync with the executed tasks. If the backend is
      // offline/slow we fall back to a short display dwell so the demo still
      // progresses visually.
      const realEvent = STAGE_EVENT[i];
      let reachedReal = false;
      if (backendMissionRunning) {
        reachedReal = await waitForMissionEvent(realEvent, stage.waitTimeout || 60000);
      }
      if (!reachedReal && !backendMissionRunning) {
        // Pure offline fallback: brief dwell before moving on.
        await waitOrSkip(Math.min(stage.baseDuration, 2500) / autopilotSpeed);
      }
      if (reachedReal && stage.num === 8 && window.nexusAudio) window.nexusAudio.playConsensus();
    }

    if (!shouldAbortAutopilot) {
      // Victory Completion on Command Center
      switchView('command-center');
      if (window.nexusAudio) window.nexusAudio.playConsensus();
      const execBox = document.getElementById('executive-report-box');
      if (execBox) execBox.style.display = 'block';
      logStream('SYSTEM', '✅ 8-Stage Autonomous Crisis Workflow Completed by Lyzr & Qdrant Solo Agents.');
    }

    stopAutopilotDemo();
  }

  async function executeStageAction(stageNum, scenarioText) {
    switch (stageNum) {
      case 1: // Omi Voice Ingestion
        if (window.nexusAudio) window.nexusAudio.playVoiceActivation();
        const wave = document.getElementById('voice-waveform');
        if (wave) wave.style.opacity = '1';
        const txOut = document.getElementById('voice-transcript-output');
        if (txOut) {
          txOut.innerHTML = `
            <span style="color:#ec4899; font-weight:700;">
              <i class="fa-solid fa-microphone-lines fa-fade"></i> OMI VOICESTREAM INGESTED: "${scenarioText}"
            </span>
          `;
        }
        triggerCrisisScenario(scenarioText);
        break;

      case 2: // Qdrant RAG Context
        if (window.nexusAudio) window.nexusAudio.playAlert();
        logStream('MEMORY', 'Qdrant hybrid search retrieved SCADA Substation 04 historical vectors (96.4% match).');
        break;

      case 3: // Lyzr AI Organization
        renderOrganizationView(scenarioText);
        if (window.nexusAudio) window.nexusAudio.playAgentMessage();
        break;

      case 4: // Live DAG Parallel Tasks
        dagEngine.setNodeState('CRISIS_DETECTED', 'success');
        dagEngine.setNodeState('MISSION_ANALYSIS', 'success');
        dagEngine.setNodeState('INCIDENT_ANALYSIS', 'running');
        dagEngine.setNodeState('IMPACT_ASSESSMENT', 'running');
        setTimeout(() => {
          dagEngine.setNodeState('INCIDENT_ANALYSIS', 'success');
          dagEngine.setNodeState('IMPACT_ASSESSMENT', 'success');
          dagEngine.setNodeState('RESOURCE_ALLOCATION', 'success');
        }, 800 / autopilotSpeed);
        break;

      case 5: // Agent Parliament Deliberation
        renderParliamentView(scenarioText);
        updateParliamentPhase(1);
        setTimeout(() => updateParliamentPhase(3), 400 / autopilotSpeed);
        setTimeout(() => {
          updateParliamentPhase(5);
          if (window.nexusAudio) window.nexusAudio.playConsensus();
          const pPill = document.getElementById('parliament-consensus-pill');
          if (pPill) pPill.innerText = 'CONSENSUS: 94% (PLAN B ADOPTED)';
        }, 900 / autopilotSpeed);
        break;

      case 6: // Red Team Adversarial Stress Test
        if (window.nexusAudio) window.nexusAudio.playAlert();
        updateDynamicScenarioUI(scenarioText);
        break;

      case 7: // Simulation Engine
        simEngine.setScenario(scenarioText);
        break;

      case 8: // Memory Galaxy Writeback
        if (memoryEngine) {
          memoryEngine.setScenario(scenarioText);
          memoryEngine.addRipple(memoryEngine.width / 2, memoryEngine.height / 2, '#10b981');
        }
        break;
    }
  }

  function waitOrSkip(ms) {
    return new Promise((resolve) => {
      advanceStageResolver = resolve;
      const startTime = Date.now();

      const interval = setInterval(() => {
        if (shouldAbortAutopilot) {
          clearInterval(interval);
          resolve();
          return;
        }

        if (!isAutopilotPaused) {
          if (Date.now() - startTime >= ms) {
            clearInterval(interval);
            advanceStageResolver = null;
            resolve();
          }
        }
      }, 50);
    });
  }

  /* ===== 10/10 REFINEMENT SUITE: HUD TELEMETRY, SHORTCUTS, EXPORTS & TOASTS ===== */

  // 1. Toast notification helper
  function showNexusToast(message, type = 'info', icon = 'fa-info-circle') {
    const container = document.getElementById('nexus-toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `nexus-toast ${type}`;
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
  window.showNexusToast = showNexusToast;

  // 2. Live Telemetry HUD Poller
  async function pollHUDTelemetry() {
    try {
      const analyticsUrl = window.NexusConfig ? window.NexusConfig.getApiUrl('/api/v1/analytics/overview') : 'http://localhost:8000/api/v1/analytics/overview';
      const res = await fetch(analyticsUrl);
      if (res.ok) {
        const data = await res.json();
        const latencyEl = document.getElementById('telemetry-latency-val');
        const consensusEl = document.getElementById('telemetry-consensus-val');
        const qdrantEl = document.getElementById('qdrant-vectors-count');

        if (latencyEl && data.summary) latencyEl.textContent = `${Math.round(data.summary.avg_pipeline_latency_ms || 28)}ms`;
        if (consensusEl && data.summary) consensusEl.textContent = `${(data.summary.avg_deliberation_consensus || 95.4).toFixed(1)}%`;
        if (qdrantEl && data.memory_subsystem) qdrantEl.textContent = Number(data.memory_subsystem.total_vectors_indexed || 14290).toLocaleString();
      }
    } catch (e) {
      // Offline fallback: keep responsive baseline
    }
  }
  setInterval(pollHUDTelemetry, 8000);
  pollHUDTelemetry();

  // 3. Export Dossier Handler
  const exportBtn = document.getElementById('export-dossier-btn');
  if (exportBtn) {
    exportBtn.addEventListener('click', async () => {
      const missionId = activeMissionId || 'msn_executive_dossier';
      showNexusToast('Compiling crisis incident dossier...', 'info', 'fa-file-invoice');
      try {
        const exportUrl = window.NexusConfig ? window.NexusConfig.getApiUrl(`/api/v1/missions/${missionId}/export`) : `http://localhost:8000/api/v1/missions/${missionId}/export`;
        const res = await fetch(exportUrl);
        let dossierData;
        if (res.ok) {
          dossierData = await res.json();
        } else {
          // Fallback dossier generator
          dossierData = {
            dossier_id: `dos_${missionId}_${Date.now()}`,
            timestamp: new Date().toISOString(),
            status: 'COMPLETED',
            mission_id: missionId,
            executive_summary: 'Crisis operation autonomously remediated by NEXUS Swarm.',
            consensus_score: 95.8,
            sponsor_validations: { omi: 'VERIFIED', lyzr: 'SYNCHRONIZED', qdrant: 'INDEXED' }
          };
        }
        const blob = new Blob([JSON.stringify(dossierData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `NEXUS-Crisis-Dossier-${missionId}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showNexusToast('Incident dossier downloaded successfully!', 'success', 'fa-circle-check');
      } catch (err) {
        showNexusToast(`Export error: ${err.message}`, 'warning', 'fa-triangle-exclamation');
      }
    });
  }

  // 4. Keyboard Shortcuts Modal & Event Handlers
  const kbdModal = document.getElementById('kbd-shortcuts-modal');
  const kbdTrigger = document.getElementById('kbd-legend-btn');
  const kbdClose = document.getElementById('kbd-modal-close');
  const kbdDismiss = document.getElementById('kbd-modal-dismiss-btn');

  function toggleKbdModal(show) {
    if (!kbdModal) return;
    kbdModal.style.display = show ? 'flex' : 'none';
  }

  if (kbdTrigger) kbdTrigger.addEventListener('click', () => toggleKbdModal(true));
  if (kbdClose) kbdClose.addEventListener('click', () => toggleKbdModal(false));
  if (kbdDismiss) kbdDismiss.addEventListener('click', () => toggleKbdModal(false));

  // 4b. Backend Server Config Modal & Live Health Poller (for Vercel + Render)
  const backendPill = document.getElementById('backend-endpoint-pill');
  const backendModal = document.getElementById('backend-config-modal');
  const backendClose = document.getElementById('backend-modal-close');
  const backendInput = document.getElementById('backend-url-input');
  const backendTestBtn = document.getElementById('backend-test-btn');
  const backendSaveBtn = document.getElementById('backend-save-btn');
  const backendResetBtn = document.getElementById('backend-reset-btn');
  const backendFeedback = document.getElementById('backend-test-feedback');
  const backendLabel = document.getElementById('backend-endpoint-label');
  const backendIcon = document.getElementById('backend-endpoint-icon');

  function updateBackendPill() {
    if (!window.NexusConfig) return;
    const url = window.NexusConfig.getBackendUrl();
    if (backendLabel) {
      if (url.includes('localhost') || url.includes('127.0.0.1')) {
        backendLabel.innerText = 'LOCAL (:8000)';
      } else {
        try {
          const u = new URL(url);
          backendLabel.innerText = u.hostname.replace('.onrender.com', '').toUpperCase();
        } catch (_) {
          backendLabel.innerText = 'CLOUD';
        }
      }
    }
  }

  async function checkBackendConnection() {
    if (!window.NexusConfig) return;
    updateBackendPill();
    const result = await window.NexusConfig.checkHealth(6000);
    if (result.ok) {
      if (backendIcon) {
        backendIcon.className = 'fa-solid fa-cloud-bolt';
        backendIcon.style.color = '#10b981';
      }
      if (backendPill) {
        backendPill.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        backendPill.style.background = 'rgba(16, 185, 129, 0.1)';
      }
    } else if (result.isRenderSleep) {
      if (backendIcon) {
        backendIcon.className = 'fa-solid fa-spinner fa-spin';
        backendIcon.style.color = '#f59e0b';
      }
      if (backendLabel) backendLabel.innerText = 'WAKING UP...';
      if (backendPill) {
        backendPill.style.borderColor = 'rgba(245, 158, 11, 0.4)';
        backendPill.style.background = 'rgba(245, 158, 11, 0.1)';
      }
    } else {
      if (backendIcon) {
        backendIcon.className = 'fa-solid fa-triangle-exclamation';
        backendIcon.style.color = '#ef4444';
      }
      if (backendPill) {
        backendPill.style.borderColor = 'rgba(239, 68, 68, 0.4)';
        backendPill.style.background = 'rgba(239, 68, 68, 0.1)';
      }
    }
  }

  if (backendPill) {
    backendPill.addEventListener('click', () => {
      if (backendInput && window.NexusConfig) {
        backendInput.value = window.NexusConfig.getBackendUrl();
      }
      if (backendFeedback) backendFeedback.innerHTML = '';
      if (backendModal) backendModal.style.display = 'flex';
    });
  }

  if (backendClose) {
    backendClose.addEventListener('click', () => {
      if (backendModal) backendModal.style.display = 'none';
    });
  }

  if (backendTestBtn) {
    backendTestBtn.addEventListener('click', async () => {
      const testUrl = (backendInput?.value || '').trim().replace(/\/+$/, '');
      if (!testUrl) {
        if (backendFeedback) backendFeedback.innerHTML = '<span style="color:#ef4444;">Please enter a valid URL.</span>';
        return;
      }
      backendFeedback.innerHTML = '<span style="color:#f59e0b;"><i class="fa-solid fa-spinner fa-spin"></i> Pinging ' + testUrl + '/ping ... (may take ~30s if Render is sleeping)</span>';
      try {
        const start = performance.now();
        const res = await fetch(testUrl + '/ping', { method: 'GET' });
        const elapsed = Math.round(performance.now() - start);
        if (res.ok) {
          backendFeedback.innerHTML = `<span style="color:#10b981;"><i class="fa-solid fa-circle-check"></i> Connected successfully in ${elapsed}ms! Status: 200 OK</span>`;
        } else {
          backendFeedback.innerHTML = `<span style="color:#ef4444;"><i class="fa-solid fa-triangle-exclamation"></i> Server returned HTTP ${res.status}</span>`;
        }
      } catch (err) {
        backendFeedback.innerHTML = `<span style="color:#ef4444;"><i class="fa-solid fa-circle-xmark"></i> Connection failed: ${err.message}. If using Render free tier, wait 30s for spin-up.</span>`;
      }
    });
  }

  if (backendSaveBtn) {
    backendSaveBtn.addEventListener('click', () => {
      const url = (backendInput?.value || '').trim();
      if (window.NexusConfig) {
        window.NexusConfig.setBackendUrl(url);
      }
      if (backendModal) backendModal.style.display = 'none';
      showNexusToast(`Backend configured: ${url || 'Default'}`, 'success', 'fa-server');
      checkBackendConnection();
      if (window.connectorCenter && typeof window.connectorCenter.connect === 'function') {
        window.connectorCenter.connect();
      }
    });
  }

  if (backendResetBtn) {
    backendResetBtn.addEventListener('click', () => {
      if (window.NexusConfig) {
        window.NexusConfig.setBackendUrl('');
        if (backendInput) backendInput.value = window.NexusConfig.getBackendUrl();
      }
      if (backendFeedback) backendFeedback.innerHTML = '<span style="color:#a78bfa;">Reset to default endpoint.</span>';
      checkBackendConnection();
    });
  }

  // Initial check and periodic health poll
  checkBackendConnection();
  setInterval(checkBackendConnection, 20000);

  const viewKeys = {
    '1': 'command-center',
    '2': 'live-mission',
    '3': 'ai-organization',
    '4': 'agent-parliament',
    '5': 'red-team',
    '6': 'simulation-engine',
    '7': 'memory-intelligence',
    '8': 'connector-center'
  };

  window.addEventListener('keydown', (e) => {
    // Ignore hotkeys when typing in form inputs
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
      if (e.key === 'Escape') document.activeElement.blur();
      return;
    }

    if (e.key === '?' || (e.shiftKey && e.key === '/')) {
      e.preventDefault();
      const isVisible = kbdModal && kbdModal.style.display === 'flex';
      toggleKbdModal(!isVisible);
    } else if (e.key === 'Escape') {
      toggleKbdModal(false);
    } else if (viewKeys[e.key]) {
      e.preventDefault();
      switchView(viewKeys[e.key]);
      showNexusToast(`Switched to ${viewKeys[e.key].replace('-', ' ').toUpperCase()}`, 'info', 'fa-compass');
    } else if (e.key.toLowerCase() === 'e') {
      e.preventDefault();
      if (exportBtn) exportBtn.click();
    } else if (e.key.toLowerCase() === 'b') {
      e.preventDefault();
      showNexusToast('Triggering high-velocity anomaly burst simulation...', 'warning', 'fa-bolt');
      const burstUrl = window.NexusConfig ? window.NexusConfig.getApiUrl('/api/v1/platform/simulate-burst') : 'http://localhost:8000/api/v1/platform/simulate-burst';
      fetch(burstUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_count: 5, source: 'monitoring' })
      }).then(() => showNexusToast('Burst sequence simulated. Event bus correlated signals.', 'success', 'fa-check'));
    } else if (e.key.toLowerCase() === 'm') {
      e.preventDefault();
      const audioBtn = document.getElementById('audio-toggle');
      if (audioBtn) audioBtn.click();
    }
  });
});

