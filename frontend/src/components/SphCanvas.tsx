import React, { useEffect, useRef } from 'react';
import type { SphData } from '../types';

interface SphCanvasProps {
  sphData: SphData | null;
  currentTimestep: number;
}

export const SphCanvas: React.FC<SphCanvasProps> = ({ sphData, currentTimestep }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !sphData) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw downhill fluid particles
      sphData.particles.forEach((p) => {
        // Find particle position for currentTimestep
        const traj = p.trajectories.find(t => t.timestep_min === currentTimestep) || p.trajectories[0];
        if (!traj) return;

        // Map lat/lon to canvas coordinates (Tehri region bounds: Lon 78.40-78.60, Lat 30.25-30.45)
        const x = ((traj.lon - 78.40) / 0.20) * canvas.width;
        const y = ((30.45 - traj.lat) / 0.20) * canvas.height;

        // Velocity color gradient (cyan to orange/red)
        const speed = traj.velocity_ms;
        const hue = Math.max(0, 200 - speed * 15);
        ctx.fillStyle = `hsl(${hue}, 90%, 55%)`;

        ctx.beginPath();
        ctx.arc(x, y, Math.max(2, traj.depth_m * 0.4), 0, Math.PI * 2);
        ctx.fill();

        // Velocity particle trail
        ctx.strokeStyle = `hsla(${hue}, 90%, 55%, 0.4)`;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + Math.sin(p.particle_id) * 6, y + 8 + speed * 1.2);
        ctx.stroke();
      });

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [sphData, currentTimestep]);

  return (
    <canvas
      ref={canvasRef}
      width={600}
      height={400}
      className="w-full h-full absolute inset-0 pointer-events-none z-20"
    />
  );
};
