import React from 'react';
import { Play, Pause, RotateCcw, Clock } from 'lucide-react';

interface BottomTimelineBarProps {
  timesteps: number[];
  currentStepIdx: number;
  setCurrentStepIdx: (idx: number) => void;
  isPlaying: boolean;
  setIsPlaying: (playing: boolean) => void;
  currentTimestep: number;
}

export const BottomTimelineBar: React.FC<BottomTimelineBarProps> = ({
  timesteps,
  currentStepIdx,
  setCurrentStepIdx,
  isPlaying,
  setIsPlaying,
  currentTimestep
}) => {
  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-40 w-7/12 max-w-2xl control-sidebar p-3.5 rounded-2xl border border-slate-800 shadow-2xl flex items-center gap-4 pointer-events-auto">
      {/* Play/Pause */}
      <button
        onClick={() => setIsPlaying(!isPlaying)}
        className="w-10 h-10 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white flex items-center justify-center shadow-lg shadow-cyan-500/30 transition-all shrink-0"
      >
        {isPlaying ? <Pause className="w-5 h-5 fill-white" /> : <Play className="w-5 h-5 fill-white" />}
      </button>

      <button
        onClick={() => setCurrentStepIdx(0)}
        className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white shrink-0"
      >
        <RotateCcw className="w-4 h-4" />
      </button>

      {/* Slider & Timestep Markers */}
      <div className="flex-1 space-y-1">
        <div className="flex justify-between items-center text-[11px] font-bold">
          <span className="text-slate-400 font-mono">T+0m (Surge)</span>
          <span className="text-cyan-400 font-mono text-xs flex items-center gap-1">
            <Clock className="w-3 h-3 text-cyan-400" /> T + {currentTimestep} Minutes
          </span>
          <span className="text-slate-400 font-mono">T+360m (Peak)</span>
        </div>
        <input
          type="range"
          min={0}
          max={timesteps.length - 1}
          step={1}
          value={currentStepIdx}
          onChange={(e) => setCurrentStepIdx(Number(e.target.value))}
          className="w-full h-2 bg-slate-900 rounded-lg appearance-none cursor-pointer"
        />
      </div>
    </div>
  );
};
