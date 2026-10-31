import React from 'react';
import { TrackData } from '../../hooks/useWebSocketFeed';
import { Badge } from '../common/Badge';

interface LiveVideoCanvasProps {
  tracks: TrackData[];
  isLive: boolean;
}

export const LiveVideoCanvas: React.FC<LiveVideoCanvasProps> = ({ tracks, isLive }) => {
  return (
    <div className="relative w-full h-[450px] bg-slate-950 rounded-2xl overflow-hidden border border-white/10 shadow-2xl flex items-center justify-center">
      {/* Background Simulated Classroom Feed */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-[#0f172a] to-slate-950 flex items-center justify-center opacity-80">
        <div className="text-center space-y-2">
          <div className="w-16 h-16 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mx-auto text-cyan-400">
            <span className="text-2xl font-bold font-display">AI</span>
          </div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Primary Camera Stream — Hall A-102 (1280 × 720 @ 10 FPS)
          </p>
        </div>
      </div>

      {/* Live Badge Overlay */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-2">
        <div className="px-3 py-1 rounded-full bg-slate-900/90 border border-white/10 backdrop-blur-md flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${isLive ? 'bg-rose-500 shadow-glow-rose animate-pulse' : 'bg-slate-500'}`} />
          <span className="text-xs font-bold uppercase tracking-wider text-white">
            {isLive ? 'LIVE STREAM' : 'STREAM PAUSED'}
          </span>
        </div>
        <Badge variant="purple">{tracks.length} Faces Tracked</Badge>
      </div>

      {/* Simulated Student Bounding Box Overlays */}
      <div className="absolute inset-0 pointer-events-none p-6">
        {/* Track 1 Overlay */}
        <div
          className="absolute border-2 border-cyan-400 bg-cyan-500/10 rounded-lg p-1 transition-all duration-300 pointer-events-auto"
          style={{ top: '25%', left: '20%', width: '140px', height: '160px' }}
        >
          <div className="bg-slate-900/90 backdrop-blur-md px-2 py-1 rounded border border-cyan-400/30 text-[10px] text-white flex flex-col gap-0.5 shadow-lg">
            <div className="flex items-center justify-between font-bold">
              <span>track_1</span>
              <span className="text-cyan-300">94%</span>
            </div>
            <p className="text-slate-300 truncate">Alex Rivera</p>
            <div className="flex items-center gap-1 mt-0.5">
              <span className="px-1 py-0.2 rounded bg-emerald-500/20 text-emerald-400 font-semibold">Attentive</span>
              <span className="px-1 py-0.2 rounded bg-indigo-500/20 text-indigo-300">Eng: 88%</span>
            </div>
          </div>
        </div>

        {/* Track 2 Overlay (Drowsiness Alert Simulation) */}
        <div
          className="absolute border-2 border-amber-400 bg-amber-500/10 rounded-lg p-1 transition-all duration-300 pointer-events-auto"
          style={{ top: '25%', left: '65%', width: '140px', height: '160px' }}
        >
          <div className="bg-slate-900/90 backdrop-blur-md px-2 py-1 rounded border border-amber-400/30 text-[10px] text-white flex flex-col gap-0.5 shadow-lg">
            <div className="flex items-center justify-between font-bold">
              <span>track_2</span>
              <span className="text-amber-300">89%</span>
            </div>
            <p className="text-slate-300 truncate">Jordan Lee</p>
            <div className="flex items-center gap-1 mt-0.5">
              <span className="px-1 py-0.2 rounded bg-amber-500/20 text-amber-400 font-semibold">EAR: 0.18</span>
              <span className="px-1 py-0.2 rounded bg-amber-500/20 text-amber-400">Drowsy</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
