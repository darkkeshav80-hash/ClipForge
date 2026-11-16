import React from 'react';
import { 
  Sparkles, 
  Cpu, 
  Play, 
  Pause, 
  RotateCcw, 
  Eye, 
  EyeOff, 
  Activity,
  Layers
} from 'lucide-react';
import { HardwareProfileConfig } from '../types';

interface NavbarProps {
  hardwareProfile: HardwareProfileConfig['profile'];
  isLowPerf: boolean;
  onToggleLowPerf: () => void;
  automationRunning: boolean;
  onStartAutomation: () => void;
  onPauseAutomation: () => void;
  activeScreen: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  hardwareProfile,
  isLowPerf,
  onToggleLowPerf,
  automationRunning,
  onStartAutomation,
  onPauseAutomation,
  activeScreen,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-white/[0.08] px-6 py-3.5 flex items-center justify-between">
      {/* Brand & Active Breadcrumb */}
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-sky-400 p-0.5 shadow-[0_0_20px_rgba(139,92,246,0.35)] flex items-center justify-center">
            <div className="w-full h-full bg-[#080B14] rounded-[10px] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-purple-400 animate-pulse-subtle" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-black tracking-tight bg-gradient-to-r from-white via-slate-100 to-purple-300 bg-clip-text text-transparent">
                CLIPFORGE<span className="text-purple-400 ml-1 font-mono text-sm uppercase tracking-widest">AI</span>
              </span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                v1.0 Local
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">Autonomous Video Clipping Factory</p>
          </div>
        </div>

        <div className="hidden md:flex items-center space-x-2 text-xs text-slate-400 border-l border-white/[0.08] pl-6 font-medium">
          <span className="text-slate-500">View:</span>
          <span className="text-purple-300 font-semibold capitalize bg-purple-500/10 px-2 py-0.5 rounded-md border border-purple-500/20">
            {activeScreen.replace('-', ' ')}
          </span>
        </div>
      </div>

      {/* Right Action Bar */}
      <div className="flex items-center space-x-3">
        {/* Hardware Mode Badge */}
        <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-white/[0.04] border border-white/[0.08] text-xs">
          <Cpu className="w-3.5 h-3.5 text-sky-400" />
          <span className="text-slate-400 text-[11px]">Hardware:</span>
          <span className="font-semibold text-sky-300 font-mono text-xs">{hardwareProfile}</span>
        </div>

        {/* Low Perf Visual Mode Toggle */}
        <button
          onClick={onToggleLowPerf}
          title={isLowPerf ? "Switch to Glassmorphism Mode" : "Switch to Low-Performance Visual Mode (Reduces blur & animations)"}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
            isLowPerf 
              ? 'bg-amber-500/20 border border-amber-500/40 text-amber-300' 
              : 'bg-white/[0.04] border border-white/[0.08] text-slate-300 hover:bg-white/[0.08]'
          }`}
        >
          {isLowPerf ? <EyeOff className="w-3.5 h-3.5 text-amber-400" /> : <Eye className="w-3.5 h-3.5 text-slate-400" />}
          <span className="hidden lg:inline">{isLowPerf ? 'Low Perf Mode (On)' : 'Glass Visuals'}</span>
        </button>

        {/* Start / Pause Automation Button */}
        {automationRunning ? (
          <button
            onClick={onPauseAutomation}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30 transition-all shadow-[0_0_15px_rgba(245,158,11,0.2)]"
          >
            <Pause className="w-4 h-4 fill-amber-300" />
            <span>Pause Factory</span>
          </button>
        ) : (
          <button
            onClick={onStartAutomation}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-500 hover:to-indigo-500 transition-all shadow-[0_0_20px_rgba(139,92,246,0.35)] hover:scale-105 active:scale-95"
          >
            <Play className="w-4 h-4 fill-white" />
            <span>Start Automation</span>
          </button>
        )}
      </div>
    </header>
  );
};
