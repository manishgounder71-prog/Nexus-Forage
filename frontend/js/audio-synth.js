/* ==========================================================================
   NEXUS FORGE — Web Audio API Synthesizer
   Futuristic UI Sound FX Engine (No external sound files required)
   ========================================================================== */

class NexusAudioSynth {
  constructor() {
    this.ctx = null;
    this.muted = false;
  }

  _initCtx() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  toggleMute() {
    this.muted = !this.muted;
    return this.muted;
  }

  playChime(freq = 523.25, type = 'sine', duration = 0.25) {
    if (this.muted) return;
    this._initCtx();
    if (!this.ctx) return;

    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(freq * 1.5, this.ctx.currentTime + duration);

      gain.gain.setValueAtTime(0.15, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch (e) {
      console.warn("Audio play error:", e);
    }
  }

  playClick() {
    this.playChime(800, 'triangle', 0.04);
  }

  playVoiceActivation() {
    this.playChime(440, 'sine', 0.2);
    setTimeout(() => this.playChime(880, 'sine', 0.3), 100);
  }

  playAgentMessage() {
    this.playChime(659.25, 'triangle', 0.15);
  }

  playAlert() {
    this.playChime(300, 'sawtooth', 0.3);
  }

  playConsensus() {
    this.playChime(523.25, 'sine', 0.2);
    setTimeout(() => this.playChime(659.25, 'sine', 0.2), 150);
    setTimeout(() => this.playChime(783.99, 'sine', 0.3), 300);
  }
}

window.nexusAudio = new NexusAudioSynth();
