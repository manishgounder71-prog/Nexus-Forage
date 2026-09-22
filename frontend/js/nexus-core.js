/* ==========================================================================
   NEXUS FORGE — NEXUS CORE 3D Holographic AI Living Canvas Engine
   Renders organic neural particle constellation, state-reactive hologram orb,
   and rotating cyber-rings with glowing energy field
   ========================================================================== */

class NexusCoreEngine {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');

    this.width = 400;
    this.height = 280;
    this.dpr = window.devicePixelRatio || 1;
    this.state = 'IDLE'; // IDLE, ANALYZING, ACTIVE, CONSENSUS
    
    this.particles = [];
    this.numParticles = 90;
    this.rotationAngle = 0;
    this.pulsePhase = 0;

    this.init();
  }

  init() {
    this.resize();
    window.addEventListener('resize', () => this.resize());
    
    // Create neural particles
    this.particles = [];
    for (let i = 0; i < this.numParticles; i++) {
      this.particles.push({
        angle: Math.random() * Math.PI * 2,
        radius: 35 + Math.random() * 125,
        size: 1.5 + Math.random() * 3.0,
        speed: (0.003 + Math.random() * 0.008) * (Math.random() > 0.5 ? 1 : -1),
        pulse: Math.random() * Math.PI,
        color: Math.random() > 0.4 ? '#a78bfa' : (Math.random() > 0.5 ? '#38bdf8' : '#ec4899')
      });
    }

    this.animate();
  }

  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.getBoundingClientRect();
    const parent = this.canvas.parentElement;
    
    this.width = rect.width > 50 ? rect.width : (parent ? parent.clientWidth : 420);
    this.height = rect.height > 50 ? rect.height : (parent ? parent.clientHeight : 280);
    if (this.width < 100) this.width = 420;
    if (this.height < 100) this.height = 280;
    
    const dpr = window.devicePixelRatio || 1;
    this.dpr = dpr;
    this.canvas.width = Math.round(this.width * dpr);
    this.canvas.height = Math.round(this.height * dpr);
    this.canvas.style.width = this.width + 'px';
    this.canvas.style.height = this.height + 'px';
  }

  setState(newState) {
    this.state = newState;
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    if (!this.canvas || !this.ctx || document.hidden) return;

    if (this.width < 50 || this.height < 50) {
      this.resize();
    }

    const dpr = this.dpr || 1;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.ctx.clearRect(0, 0, this.width, this.height);

    const centerX = this.width / 2;
    const centerY = this.height / 2 - 10;

    this.rotationAngle += this.state === 'ANALYZING' ? 0.02 : 0.008;
    this.pulsePhase += 0.045;

    // Draw central glowing intelligence orb
    const isAnalyzing = this.state === 'ANALYZING';
    const isConsensus = this.state === 'CONSENSUS';
    const orbRadius = 40 + Math.sin(this.pulsePhase) * (isAnalyzing ? 10 : 5);
    
    // Outer atmospheric halo
    const haloGrad = this.ctx.createRadialGradient(
      centerX, centerY, 10,
      centerX, centerY, orbRadius * 3.2
    );

    if (isAnalyzing) {
      haloGrad.addColorStop(0, 'rgba(244, 63, 94, 0.85)');
      haloGrad.addColorStop(0.4, 'rgba(168, 85, 247, 0.45)');
      haloGrad.addColorStop(0.8, 'rgba(59, 130, 246, 0.15)');
      haloGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    } else if (isConsensus) {
      haloGrad.addColorStop(0, 'rgba(16, 185, 129, 0.9)');
      haloGrad.addColorStop(0.4, 'rgba(59, 130, 246, 0.45)');
      haloGrad.addColorStop(0.8, 'rgba(139, 92, 246, 0.15)');
      haloGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    } else {
      haloGrad.addColorStop(0, 'rgba(139, 92, 246, 0.85)');
      haloGrad.addColorStop(0.4, 'rgba(56, 189, 248, 0.35)');
      haloGrad.addColorStop(0.8, 'rgba(236, 72, 153, 0.12)');
      haloGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    }

    this.ctx.fillStyle = haloGrad;
    this.ctx.beginPath();
    this.ctx.arc(centerX, centerY, orbRadius * 3.2, 0, Math.PI * 2);
    this.ctx.fill();

    // Secondary energy pulse shockwave
    const shockwaveRadius = (orbRadius * 1.6 + (Math.sin(this.pulsePhase * 1.5) * 15));
    this.ctx.strokeStyle = isAnalyzing ? 'rgba(244, 63, 94, 0.4)' : (isConsensus ? 'rgba(52, 211, 153, 0.45)' : 'rgba(167, 139, 250, 0.35)');
    this.ctx.lineWidth = 1.5;
    this.ctx.beginPath();
    this.ctx.arc(centerX, centerY, shockwaveRadius, 0, Math.PI * 2);
    this.ctx.stroke();

    // 3D Orbiting Cyber Rings (Tilted Gyroscope Effect)
    this.drawRing(centerX, centerY, 75, this.rotationAngle, 'rgba(167, 139, 250, 0.55)', [6, 8], 0.45);
    this.drawRing(centerX, centerY, 110, -this.rotationAngle * 1.25, 'rgba(56, 189, 248, 0.45)', [10, 14], -0.55);
    this.drawRing(centerX, centerY, 140, this.rotationAngle * 0.75, 'rgba(244, 114, 182, 0.35)', [4, 12], 0.25);

    // Inner Solid Core
    const innerGrad = this.ctx.createRadialGradient(
      centerX - 5, centerY - 5, 2,
      centerX, centerY, orbRadius * 0.55
    );
    innerGrad.addColorStop(0, '#ffffff');
    innerGrad.addColorStop(0.5, isAnalyzing ? '#f43f5e' : (isConsensus ? '#34d399' : '#a855f7'));
    innerGrad.addColorStop(1, 'rgba(0,0,0,0.8)');

    this.ctx.fillStyle = innerGrad;
    this.ctx.beginPath();
    this.ctx.arc(centerX, centerY, orbRadius * 0.55, 0, Math.PI * 2);
    this.ctx.fill();

    // Draw Particles & Force Connections
    const positions = new Float64Array(this.particles.length * 2);
    for (let i = 0; i < this.particles.length; i++) {
      const p = this.particles[i];
      p.angle += p.speed;
      positions[i * 2] = centerX + Math.cos(p.angle) * p.radius;
      positions[i * 2 + 1] = centerY + Math.sin(p.angle) * (p.radius * 0.62);
    }

    for (let i = 0; i < this.particles.length; i++) {
      const p = this.particles[i];
      const px = positions[i * 2];
      const py = positions[i * 2 + 1];

      // Draw connections to nearby particles
      for (let j = i + 1; j < this.particles.length; j++) {
        const p2x = positions[j * 2];
        const p2y = positions[j * 2 + 1];
        const ddx = px - p2x;
        const ddy = py - p2y;
        const dist2 = ddx * ddx + ddy * ddy;
        const threshold = 48 * 48;

        if (dist2 < threshold) {
          const dist = Math.sqrt(dist2);
          const alpha = (1 - dist / 48) * (isAnalyzing ? 0.65 : 0.4);
          this.ctx.strokeStyle = isAnalyzing ? `rgba(244, 63, 94, ${alpha})` : `rgba(167, 139, 250, ${alpha})`;
          this.ctx.lineWidth = 0.8;
          this.ctx.beginPath();
          this.ctx.moveTo(px, py);
          this.ctx.lineTo(p2x, p2y);
          this.ctx.stroke();
        }
      }

      // Draw particle dot with glow
      this.ctx.fillStyle = p.color;
      this.ctx.beginPath();
      this.ctx.arc(px, py, p.size, 0, Math.PI * 2);
      this.ctx.fill();
    }
  }

  drawRing(cx, cy, r, angle, color, dash = [8, 12], tilt = 0.45) {
    this.ctx.save();
    this.ctx.translate(cx, cy);
    this.ctx.rotate(angle);
    this.ctx.scale(1, Math.abs(tilt) + 0.25);
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = 1.6;
    this.ctx.setLineDash(dash);
    this.ctx.beginPath();
    this.ctx.arc(0, 0, r, 0, Math.PI * 2);
    this.ctx.stroke();
    this.ctx.restore();
  }
}
