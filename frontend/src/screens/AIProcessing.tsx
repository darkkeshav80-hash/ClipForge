import React from 'react';
import { 
  Layers, 
  Sparkles, 
  Pause, 
  Play, 
  Square, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Film,
  ArrowRight,
  Loader2
} from 'lucide-react';
import { GlassCard } from '../components/GlassCard';
import { LiveLogViewer } from '../components/LiveLogViewer';
import { PipelineStage, ProcessingLog, Project } from '../types';
import { ScreenId } from '../components/Sidebar';

interface AIProcessingProps {
  currentProject: Project | null;
  currentStage: PipelineStage;
  stageProgress: number;
  totalProgress: number;
  logs: ProcessingLog[];
  onControlAction: (action: 'start' | 'pause' | 'resume' | 'stop') => void;
  onNavigate: (screen: ScreenId) => void;
  onClearLogs?: () => void;
}

const STAGES: { id: PipelineStage; label: string; desc: string }[] = [
  { id: 'importing', label: '1. Importing', desc: 'Validating format & probing video streams' },
  { id: 'transcribing', label: '2. Transcribing', desc: 'Faster-Whisper audio extraction & word timestamps' },
  { id: 'analyzing', label: '3. Analyzing', desc: 'Audio energy, visual frames & scene boundary detection' },
  { id: 'selecting', label: '4. Selecting', desc: 'AI virality scoring & hook moment extraction' },
  { id: 'editing', label: '5. Editing', desc: '9:16 vertical crop, smart zoom & silence jump cuts' },
  { id: 'captioning', label: '6. Captioning', desc: 'Burn-in kinetic typography with active word glow' },
  { id: 'rendering', label: '7. Rendering', desc: 'FFmpeg multi-threaded GPU/CPU export' },
  { id: 'reviewing', label: '8. Reviewing', desc: 'AI multi-model quality validation & checks' },
  { id: 'publishing', label: '9. Publishing', desc: 'Auto-publish to YouTube Shorts (if enabled)' },
];

export const AIProcessingScreen: React.FC<AIProcessingProps> = ({
  currentProject,
  currentStage,
  stageProgress,
  totalProgress,
  logs,
  onControlAction,
  onNavigate,
  onClearLogs,
}) => {
  const currentStageIndex = STAGES.findIndex((s) => s.id === currentStage);

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-400 animate-ping"></span>
            <h1 className="text-2xl font-bold text-white flex items-center space-x-2.5">
              <span>Autonomous Factory Pipeline</span>
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Current Target: <span className="text-purple-300 font-semibold">{currentProject?.name || 'No video loaded'}</span>
          </p>
        </div>

        {/* Pipeline Control Buttons */}
        <div className="flex items-center space-x-2">
          {currentStage === 'paused' ? (
            <button
              onClick={() => onControlAction('resume')}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold transition-all shadow-[0_0_15px_rgba(139,92,246,0.3)]"
            >
              <Play className="w-4 h-4 fill-white" />
              <span>Resume</span>
            </button>
          ) : (
            <button
              onClick={() => onControlAction('pause')}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-white/[0.08] hover:bg-white/[0.15] text-amber-300 border border-amber-500/30 text-xs font-semibold transition-all"
            >
              <Pause className="w-4 h-4" />
              <span>Pause</span>
            </button>
          )}

          <button
            onClick={() => onControlAction('stop')}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 text-xs font-semibold transition-all"
          >
            <Square className="w-3.5 h-3.5 fill-rose-300" />
            <span>Abort</span>
          </button>

          <button
            onClick={() => onNavigate('clips-gallery')}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-purple-600/30 hover:bg-purple-600/50 text-purple-200 border border-purple-500/40 text-xs font-semibold transition-all"
          >
            <span>Clips Gallery</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Primary Progress Display */}
      <GlassCard>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs uppercase font-mono font-bold tracking-wider text-purple-400">
                Overall Pipeline Progress
              </span>
              <h3 className="text-xl font-extrabold text-white mt-1 capitalize">
                Stage: {currentStage.replace('_', ' ')}
              </h3>
            </div>
            <div className="text-right">
              <span className="text-3xl font-black font-mono text-purple-300 tracking-tight">
                {totalProgress}%
              </span>
              <p className="text-[11px] text-slate-400">Stage: {stageProgress}%</p>
            </div>
          </div>

          {/* Master Progress Bar */}
          <div className="w-full h-3 rounded-full bg-slate-900/80 border border-white/[0.08] overflow-hidden p-0.5">
            <div
              className="h-full bg-gradient-to-r from-purple-600 via-indigo-500 to-sky-400 rounded-full transition-all duration-300 shadow-[0_0_15px_rgba(139,92,246,0.5)]"
              style={{ width: `${totalProgress}%` }}
            ></div>
          </div>
        </div>
      </GlassCard>

      {/* Stages Horizontal/Vertical Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {STAGES.map((s, idx) => {
          const isDone = currentStage !== 'idle' && (currentStageIndex > idx || currentStage === 'completed');
          const isCurrent = s.id === currentStage && currentStage !== 'idle' && currentStage !== 'paused' && currentStage !== 'completed';
          const isPending = !isDone && !isCurrent;

          return (
            <div
              key={s.id}
              className={`p-4 rounded-2xl border transition-all relative overflow-hidden ${
                isCurrent
                  ? 'bg-purple-600/20 border-purple-500 shadow-[0_0_20px_rgba(139,92,246,0.25)]'
                  : isDone
                  ? 'bg-emerald-950/20 border-emerald-500/40 text-slate-300'
                  : 'bg-white/[0.02] border-white/[0.06] text-slate-500'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className={`text-xs font-bold font-mono ${
                  isCurrent ? 'text-purple-300' : isDone ? 'text-emerald-400' : 'text-slate-500'
                }`}>
                  {s.label}
                </span>

                {isDone && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
                {isCurrent && <Loader2 className="w-4 h-4 text-purple-400 animate-spin shrink-0" />}
                {isPending && <Clock className="w-4 h-4 text-slate-600 shrink-0" />}
              </div>

              <p className="text-[11px] text-slate-400 mt-2 line-clamp-2">
                {s.desc}
              </p>

              {isCurrent && (
                <div className="mt-3 w-full bg-black/40 h-1 rounded-full overflow-hidden">
                  <div
                    className="bg-purple-400 h-full rounded-full transition-all duration-200"
                    style={{ width: `${stageProgress}%` }}
                  ></div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Live Log Streamer */}
      <div>
        <h3 className="text-sm font-bold text-white mb-3 flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-sky-400" />
          <span>Real-Time Engine Telemetry</span>
        </h3>
        <LiveLogViewer logs={logs} height="h-72" onClear={onClearLogs} />
      </div>
    </div>
  );
};
