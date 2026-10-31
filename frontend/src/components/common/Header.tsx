import React from 'react';
import { Camera, User as UserIcon, Monitor, UserCheck, Building2, Video } from 'lucide-react';
import { Badge } from './Badge';

export type PortalView = 'faculty' | 'student' | 'admin' | 'demo';

interface HeaderProps {
  userRole?: string;
  userName?: string;
  isConnected?: boolean;
  currentView?: PortalView;
  onViewChange?: (view: PortalView) => void;
}

export const Header: React.FC<HeaderProps> = ({
  userRole = 'Faculty',
  userName = 'Dr. Sarah Jenkins',
  isConnected = true,
  currentView = 'faculty',
  onViewChange,
}) => {
  return (
    <header className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-xl border-b border-white/10 px-6 py-3 flex items-center justify-between">
      {/* Brand Logo */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Camera className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold tracking-tight font-display text-white">
              Attend<span className="text-gradient">AI</span>
            </h1>
            <Badge variant="purple" size="sm">v1.0</Badge>
          </div>
          <p className="text-xs text-slate-400">Smart Classroom Intelligence Platform</p>
        </div>
      </div>

      {/* Center Portal View Switcher */}
      {onViewChange && (
        <div className="hidden md:flex items-center bg-slate-950/80 border border-white/10 p-1 rounded-xl gap-1">
          <button
            onClick={() => onViewChange('demo')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              currentView === 'demo'
                ? 'bg-cyan-500 text-slate-950 font-bold shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Video className="w-3.5 h-3.5" />
            🎥 Live AI Demo
          </button>
          <button
            onClick={() => onViewChange('faculty')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              currentView === 'faculty'
                ? 'bg-cyan-500 text-slate-950 font-bold shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Monitor className="w-3.5 h-3.5" />
            Faculty Stream
          </button>
          <button
            onClick={() => onViewChange('student')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              currentView === 'student'
                ? 'bg-cyan-500 text-slate-950 font-bold shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <UserCheck className="w-3.5 h-3.5" />
            Student Portal
          </button>
          <button
            onClick={() => onViewChange('admin')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              currentView === 'admin'
                ? 'bg-cyan-500 text-slate-950 font-bold shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            Admin Console
          </button>
        </div>
      )}

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/60 border border-slate-700/50 text-xs text-slate-300">
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-400 shadow-glow-emerald animate-pulse' : 'bg-rose-400'}`} />
          <span>{isConnected ? 'Live Stream Active' : 'Disconnected'}</span>
        </div>

        <div className="flex items-center gap-3 pl-4 border-l border-slate-800">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-sm font-semibold shadow-md">
            <UserIcon className="w-4 h-4" />
          </div>
          <div className="hidden sm:block text-left">
            <p className="text-sm font-semibold text-slate-200">{userName}</p>
            <p className="text-xs text-cyan-400 font-medium capitalize">{userRole}</p>
          </div>
        </div>
      </div>
    </header>
  );
};
