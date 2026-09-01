"use client";

import { useEffect, useRef } from "react";

interface VoiceVisualizerProps {
  isListening: boolean;
  audioLevel?: number;
}

export default function VoiceVisualizer({ isListening, audioLevel = 0.5 }: VoiceVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!isListening || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const width = canvas.width;
      const height = canvas.height;
      const centerY = height / 2;

      // Draw multi-layered glow wave
      const bars = 24;
      const barWidth = 3;
      const gap = (width - bars * barWidth) / (bars - 1);

      for (let i = 0; i < bars; i++) {
        const x = i * (barWidth + gap);
        const distFromCenter = Math.abs(i - bars / 2) / (bars / 2);
        const dynamicAmp = (1 - distFromCenter * 0.5) * (0.3 + Math.sin(phase + i * 0.4) * 0.2 + audioLevel * 0.5);
        const barHeight = Math.max(4, height * dynamicAmp);

        const gradient = ctx.createLinearGradient(0, centerY - barHeight / 2, 0, centerY + barHeight / 2);
        gradient.addColorStop(0, "#3b82f6"); // blue-500
        gradient.addColorStop(0.5, "#06b6d4"); // cyan-500
        gradient.addColorStop(1, "#10b981"); // emerald-500

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, centerY - barHeight / 2, barWidth, barHeight, 2);
        ctx.fill();
      }

      phase += 0.12;
      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [isListening, audioLevel]);

  if (!isListening) return null;

  return (
    <div className="flex items-center justify-center h-7 px-2">
      <canvas ref={canvasRef} width={140} height={24} className="w-[140px] h-[24px]" />
    </div>
  );
}
