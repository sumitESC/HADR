import React, { useState } from 'react';
import { MapPin, ChevronDown, ChevronUp } from 'lucide-react';

interface RightNodesPanelProps {
  currentTimestep?: number;
}

interface DownstreamNode {
  name: string;
  type: string;
  pop: number;
  elev: number;
  arrivalMin: number;
  arrivalStr: string;
  risk: 'critical' | 'high' | 'moderate';
}

export const RightNodesPanel: React.FC<RightNodesPanelProps> = ({ currentTimestep = 120 }) => {
  const [collapsed, setCollapsed] = useState<boolean>(false);

  const nodes: DownstreamNode[] = [
    { name: 'New Tehri Town', type: 'Urban', pop: 25400, elev: 780, arrivalMin: 15, arrivalStr: 'T + 15m', risk: 'critical' },
    { name: 'Koteshwar Dam & Village', type: 'Hydro Dam', pop: 4200, elev: 540, arrivalMin: 30, arrivalStr: 'T + 30m', risk: 'critical' },
    { name: 'Bhagirathipuram', type: 'Settlement', pop: 8100, elev: 610, arrivalMin: 60, arrivalStr: 'T + 60m', risk: 'high' },
    { name: 'Dobra Chanti Bridge', type: 'Bridge', pop: 0, elev: 650, arrivalMin: 90, arrivalStr: 'T + 90m', risk: 'high' },
    { name: 'Devprayag Confluence', type: 'Confluence', pop: 12500, elev: 460, arrivalMin: 120, arrivalStr: 'T + 120m', risk: 'moderate' },
  ];

  return (
    <div className="w-[230px] z-40 control-sidebar p-3.5 my-auto mr-4 flex flex-col space-y-2 shrink-0 border border-slate-800/90 shadow-2xl pointer-events-auto">
      <div 
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-between cursor-pointer border-b border-slate-800 pb-1.5"
      >
        <h3 className="text-[11px] font-extrabold text-white uppercase tracking-wider flex items-center gap-1.5 font-heading">
          <MapPin className="w-3.5 h-3.5 text-cyan-400" /> Downstream Nodes
        </h3>
        {collapsed ? <ChevronDown className="w-3.5 h-3.5 text-slate-400" /> : <ChevronUp className="w-3.5 h-3.5 text-slate-400" />}
      </div>

      {!collapsed && (
        <div className="space-y-1.5 max-h-[300px] overflow-y-auto pt-1">
          {nodes.map((node, idx) => {
            const isArrived = currentTimestep >= node.arrivalMin;
            return (
              <div
                key={idx}
                className={`p-2 rounded-lg border transition-all space-y-1 ${
                  isArrived
                    ? 'bg-red-950/40 border-red-800/80 shadow-md shadow-red-900/30'
                    : 'control-card border-slate-800/80'
                }`}
              >
                <div className="flex items-center justify-between">
                  <h4 className="text-[11px] font-bold text-white truncate max-w-[130px] flex items-center gap-1">
                    {isArrived && <span className="w-2 h-2 rounded-full bg-red-500 animate-ping shrink-0" />}
                    {node.name}
                  </h4>
                  <span className={`px-1.5 py-0.5 rounded text-[8px] font-mono font-bold uppercase ${
                    isArrived
                      ? 'bg-red-600 text-white border border-red-500 font-extrabold'
                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}>
                    {isArrived ? 'FLOOD ARRIVED' : node.arrivalStr}
                  </span>
                </div>
                <div className="flex justify-between items-center text-[9px] text-slate-400">
                  <span>{node.type}</span>
                  <span className={`font-mono ${isArrived ? 'text-red-400 font-bold' : 'text-cyan-400'}`}>{node.elev}m</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
