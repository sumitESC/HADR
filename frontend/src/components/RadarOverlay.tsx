import React, { useRef, useEffect, useCallback } from 'react';

interface RadarOverlayProps {
  damLat: number;
  damLon: number;
  progress: number; // 0-1, how far the flood has propagated
  isPlaying: boolean;
  mapBounds?: { north: number; south: number; east: number; west: number };
  opacity?: number;
  currentTimestep: number;
}

/**
 * Doppler-style radar animation overlay using HTML5 Canvas.
 * Creates a pulsing, radial gradient flood spread from the dam breach point
 * with concentric ring animations and a rotating sweep line.
 */
export const RadarOverlay: React.FC<RadarOverlayProps> = ({
  damLat: _damLat,
  damLon: _damLon,
  progress,
  isPlaying,
  opacity = 0.55,
  currentTimestep
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrameRef = useRef<number>(0);
  const sweepAngleRef = useRef<number>(0);
  const pulsePhaseRef = useRef<number>(0);
  const timeRef = useRef<number>(0);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;
    const cx = W * 0.42; // Dam position offset to upper-left area
    const cy = H * 0.35;

    timeRef.current += 0.016; // ~60fps
    sweepAngleRef.current += 0.018;
    pulsePhaseRef.current += 0.035;

    ctx.clearRect(0, 0, W, H);
    ctx.globalAlpha = opacity;

    const maxRadius = Math.max(W, H) * 0.7 * Math.max(0.15, progress);
    const pulse = Math.sin(pulsePhaseRef.current) * 0.08 + 1.0;

    // 1. Radial gradient flood spread (core heatmap)
    const depthColors = [
      { stop: 0.0,  color: 'rgba(220, 38, 38, 0.9)' },   // Red (deepest)
      { stop: 0.15, color: 'rgba(245, 158, 11, 0.8)' },   // Orange
      { stop: 0.30, color: 'rgba(234, 179, 8, 0.7)' },    // Yellow
      { stop: 0.50, color: 'rgba(34, 197, 94, 0.6)' },    // Green
      { stop: 0.70, color: 'rgba(6, 182, 212, 0.5)' },    // Cyan
      { stop: 0.88, color: 'rgba(59, 130, 246, 0.3)' },   // Blue
      { stop: 1.0,  color: 'rgba(59, 130, 246, 0.0)' },   // Transparent
    ];

    const floodGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, maxRadius * pulse);
    depthColors.forEach(({ stop, color }) => {
      floodGrad.addColorStop(stop, color);
    });

    // Elliptical shape (wider downstream)
    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(1.0, 0.65); // Wider than tall (valley shape)
    ctx.rotate(0.4); // Tilt downstream
    ctx.beginPath();
    ctx.arc(0, 0, maxRadius * pulse, 0, Math.PI * 2);
    ctx.fillStyle = floodGrad;
    ctx.fill();
    ctx.restore();

    // 2. Concentric ripple rings (radar pulse)
    const numRings = 6;
    for (let i = 0; i < numRings; i++) {
      const ringPhase = (pulsePhaseRef.current * 0.8 + i * 1.0) % (Math.PI * 2);
      const ringRadius = maxRadius * (0.15 + (i / numRings) * 0.85);
      const ringAlpha = Math.max(0, 0.25 * Math.sin(ringPhase) * (1.0 - i / numRings));

      if (ringAlpha > 0.02) {
        ctx.save();
        ctx.translate(cx, cy);
        ctx.scale(1.0, 0.65);
        ctx.rotate(0.4);
        ctx.beginPath();
        ctx.arc(0, 0, ringRadius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(56, 189, 248, ${ringAlpha})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.restore();
      }
    }

    // 3. Radar sweep line (rotating beam)
    if (isPlaying) {
      const sweepLen = maxRadius * 1.1;
      const sweepAngle = sweepAngleRef.current;

      ctx.save();
      ctx.translate(cx, cy);

      // Sweep cone gradient (fading trail)
      for (let a = 0; a < 12; a++) {
        const trailAngle = sweepAngle - a * 0.03;
        const trailAlpha = Math.max(0, 0.35 - a * 0.03);
        const trailGrad = ctx.createLinearGradient(0, 0, 
          Math.cos(trailAngle) * sweepLen, 
          Math.sin(trailAngle) * sweepLen
        );
        trailGrad.addColorStop(0, `rgba(56, 189, 248, ${trailAlpha})`);
        trailGrad.addColorStop(1, `rgba(56, 189, 248, 0)`);

        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(
          Math.cos(trailAngle) * sweepLen,
          Math.sin(trailAngle) * sweepLen
        );
        ctx.strokeStyle = trailGrad;
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Main sweep line
      const mainGrad = ctx.createLinearGradient(0, 0, 
        Math.cos(sweepAngle) * sweepLen, 
        Math.sin(sweepAngle) * sweepLen
      );
      mainGrad.addColorStop(0, 'rgba(96, 215, 255, 0.8)');
      mainGrad.addColorStop(0.5, 'rgba(56, 189, 248, 0.5)');
      mainGrad.addColorStop(1, 'rgba(56, 189, 248, 0)');

      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(
        Math.cos(sweepAngle) * sweepLen,
        Math.sin(sweepAngle) * sweepLen
      );
      ctx.strokeStyle = mainGrad;
      ctx.lineWidth = 2.5;
      ctx.stroke();

      ctx.restore();
    }

    // 4. Dam epicenter marker (pulsing dot)
    const epicPulse = 6 + Math.sin(timeRef.current * 3) * 3;
    ctx.save();
    ctx.globalAlpha = 0.9;
    
    // Outer glow
    const glowGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, epicPulse * 3);
    glowGrad.addColorStop(0, 'rgba(239, 68, 68, 0.6)');
    glowGrad.addColorStop(1, 'rgba(239, 68, 68, 0)');
    ctx.beginPath();
    ctx.arc(cx, cy, epicPulse * 3, 0, Math.PI * 2);
    ctx.fillStyle = glowGrad;
    ctx.fill();

    // Core dot
    ctx.beginPath();
    ctx.arc(cx, cy, epicPulse, 0, Math.PI * 2);
    ctx.fillStyle = '#ef4444';
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.restore();

    // 5. Depth scale indicator text
    ctx.save();
    ctx.globalAlpha = 0.7;
    ctx.font = '10px "JetBrains Mono", monospace';
    
    const scaleLabels = [
      { r: 0.15, label: '>4.0m', color: '#ef4444' },
      { r: 0.35, label: '2-3m', color: '#eab308' },
      { r: 0.55, label: '1-2m', color: '#22c55e' },
      { r: 0.75, label: '0.5-1m', color: '#06b6d4' },
    ];

    scaleLabels.forEach(({ r, label, color }) => {
      const labelR = maxRadius * r;
      const labelX = cx + Math.cos(-0.5) * labelR;
      const labelY = cy + Math.sin(-0.5) * labelR * 0.65;
      
      if (labelR > 20) {
        ctx.fillStyle = color;
        ctx.fillText(label, labelX, labelY);
      }
    });

    ctx.restore();

    animFrameRef.current = requestAnimationFrame(draw);
  }, [progress, isPlaying, opacity, currentTimestep]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const resize = () => {
      const parent = canvas.parentElement;
      if (parent) {
        canvas.width = parent.clientWidth;
        canvas.height = parent.clientHeight;
      }
    };

    resize();
    window.addEventListener('resize', resize);
    
    animFrameRef.current = requestAnimationFrame(draw);

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animFrameRef.current);
    };
  }, [draw]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 z-[399] pointer-events-none"
      style={{ mixBlendMode: 'screen' }}
    />
  );
};

export default RadarOverlay;
