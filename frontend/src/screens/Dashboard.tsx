import React from 'react';
import { 
  Film, 
  Sparkles, 
  Youtube, 
  AlertTriangle, 
  HardDrive, 
  Layers, 
  TrendingUp, 
  Play, 
  Upload, 
  ArrowRight,
  Clock,
  CheckCircle2,
  Sliders,
  ChevronRight
} from 'lucide-react';
import { MetricsWidget } from '../components/MetricsWidget';
import { GlassCard } from '../components/GlassCard';
import { DashboardMetrics, Project, Clip } from '../types';
import { ScreenId } from '../components/Sidebar';

interface DashboardProps {
  metrics: DashboardMetrics;
  projects: Project[];
  clips: Clip[];
  onNavigate: (screen: ScreenId) => void;
  onSelectProject?: (project: Project) => void;
  onSelectClip?: (clip: Clip) => void;
}

export const DashboardScreen: React.FC<DashboardProps> = ({
  metrics,
  projects,
  clips,
  onNavigate,
  onSelectProject,
  onSelectClip,
}) => {
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero Welcome Banner */}
      <div className="relative rounded-3xl p-8 overflow-hidden border border-white/[0.12] bg-gradient-to-r from-purple-900/30 via-slate-900/60 to-sky-950/30 shadow-[0_10px_40px_rgba(0,0,0,0.5)]">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20"></div>
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 text-xs font-semibold mb-4 border border-purple-500/30">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Autonomous Local Clipping Factory</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight leading-tight">
            Turn long videos into <span className="bg-gradient-to-r from-purple-400 to-sky-400 bg-clip-text text-transparent">viral 9:16 Shorts</span> in minutes.
          </h1>
          <p className="mt-3 text-slate-300 text-sm md:text-base leading-relaxed">
            Opus Clip & Klap intelligence running completely offline on your Windows PC. Multi-speaker face tracking, dynamic 22+ animated caption presets, AI virality scoring, and automated YouTube publishing.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              onClick={() => onNavigate('new-project')}
              className="flex items-center space-x-2 px-5 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs md:text-sm font-semibold transition-all shadow-[0_0_25px_rgba(139,92,246,0.4)] hover:scale-105 active:scale-95"
            >
              <Upload className="w-4 h-4" />
              <span>Upload Video / Paste URL</span>
            </button>
            
            <button
              onClick={() => onNavigate('automation')}
              className="flex items-center space-x-2 px-5 py-3 rounded-xl bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/30 text-xs md:text-sm font-semibold transition-all"
            >
              <Play className="w-4 h-4 fill-sky-300" />
              <span>Automation Engine</span>
            </button>
          </div>
        </div>
      </div>

      {/* Primary KPI Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricsWidget
          label="Videos Processed"
          value={metrics.total_videos_processed}
          subValue="videos"
          icon={<Film className="w-5 h-5" />}
          trend="+12%"
          color="purple"
        />
        <MetricsWidget
          label="Clips Generated"
          value={metrics.total_clips_generated}
          subValue="shorts"
          icon={<Sparkles className="w-5 h-5" />}
          trend="+28%"
          color="blue"
        />
        <MetricsWidget
          label="YouTube Shorts"
          value={metrics.published_shorts}
          subValue="published"
          icon={<Youtube className="w-5 h-5" />}
          trend="+4"
          color="green"
        />
        <MetricsWidget
          label="Avg Viral Score"
          value={`${metrics.average_clip_score}/100`}
          subValue="high engagement"
          icon={<TrendingUp className="w-5 h-5" />}
          color="amber"
        />
        <MetricsWidget
          label="Queue Jobs"
          value={metrics.queue_length}
          subValue="active"
          icon={<Layers className="w-5 h-5" />}
          color="purple"
        />
        <MetricsWidget
          label="Local Storage"
          value={`${(metrics.storage_usage_mb / 1024).toFixed(1)} GB`}
          subValue={`of ${metrics.storage_total_gb} GB`}
          icon={<HardDrive className="w-5 h-5" />}
          color="blue"
        />
      </div>

      {/* Content Split: Projects & High-Score Clips */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Projects */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Film className="w-5 h-5 text-purple-400" />
              <span>Recent Video Projects</span>
            </h2>
            <button
              onClick={() => onNavigate('new-project')}
              className="text-xs text-purple-400 hover:text-purple-300 font-semibold flex items-center space-x-1"
            >
              <span>Create New</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {projects.length === 0 ? (
              <GlassCard className="text-center py-12">
                <Film className="w-10 h-10 text-slate-500 mx-auto mb-3 opacity-60" />
                <h4 className="text-sm font-semibold text-slate-300">No projects yet</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                  Upload your first video or paste a supported video URL to automatically create high-retention clips.
                </p>
                <button
                  onClick={() => onNavigate('new-project')}
                  className="mt-4 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-semibold inline-flex items-center space-x-2"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>Upload Video Now</span>
                </button>
              </GlassCard>
            ) : (
              projects.slice(0, 4).map((proj) => (
                <div
                  key={proj.id}
                  onClick={() => {
                    if (onSelectProject) onSelectProject(proj);
                    onNavigate('processing');
                  }}
                  className="glass-card rounded-2xl p-4 flex items-center justify-between cursor-pointer group"
                >
                  <div className="flex items-center space-x-4">
                    <div className="w-16 h-12 rounded-xl bg-slate-800/80 border border-white/[0.08] overflow-hidden flex items-center justify-center shrink-0 relative">
                      {proj.thumbnail_path ? (
                        <img src={`/storage/${proj.thumbnail_path}`} alt={proj.name} className="w-full h-full object-cover" />
                      ) : (
                        <Film className="w-6 h-6 text-purple-400/60" />
                      )}
                      <span className="absolute bottom-1 right-1 text-[9px] bg-black/80 px-1 rounded text-white font-mono">
                        {Math.floor(proj.duration / 60)}:{(Math.floor(proj.duration) % 60).toString().padStart(2, '0')}
                      </span>
                    </div>

                    <div>
                      <h4 className="text-sm font-semibold text-white group-hover:text-purple-300 transition-colors">
                        {proj.name}
                      </h4>
                      <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1">
                        <span className="capitalize text-slate-300 font-mono text-[11px] bg-white/[0.06] px-1.5 py-0.5 rounded">
                          {proj.status}
                        </span>
                        <span>•</span>
                        <span>{proj.clips_count} clips detected</span>
                        <span>•</span>
                        <span>{new Date(proj.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <div className="text-right hidden sm:block">
                      <span className="text-xs font-mono font-semibold text-purple-300">
                        {proj.total_progress}%
                      </span>
                      <div className="w-24 bg-slate-800 h-1.5 rounded-full overflow-hidden mt-1">
                        <div
                          className="bg-gradient-to-r from-purple-500 to-sky-400 h-full rounded-full transition-all duration-300"
                          style={{ width: `${proj.total_progress}%` }}
                        ></div>
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-purple-400 transition-transform group-hover:translate-x-1" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Top Clips Spotlight */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-amber-400" />
              <span>Viral Clips Ready</span>
            </h2>
            <button
              onClick={() => onNavigate('clips-gallery')}
              className="text-xs text-sky-400 hover:text-sky-300 font-semibold flex items-center space-x-1"
            >
              <span>View All ({clips.length})</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {clips.length === 0 ? (
              <GlassCard className="text-center py-10">
                <Sparkles className="w-8 h-8 text-slate-500 mx-auto mb-2 opacity-50" />
                <p className="text-xs text-slate-400">No clips ready yet</p>
                <p className="text-[11px] text-slate-500 mt-1">Clips will appear here as soon as AI finishes rendering</p>
              </GlassCard>
            ) : (
              clips.slice(0, 3).map((clip) => (
                <div
                  key={clip.id}
                  onClick={() => {
                    if (onSelectClip) onSelectClip(clip);
                    onNavigate('clips-gallery');
                  }}
                  className="glass-card rounded-2xl p-3 flex items-center space-x-3 cursor-pointer group"
                >
                  <div className="w-14 h-20 bg-slate-900 rounded-xl overflow-hidden shrink-0 border border-white/[0.08] relative">
                    {clip.thumbnail_path ? (
                      <img src={`/storage/${clip.thumbnail_path}`} alt={clip.title} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-xs text-slate-600 font-mono">9:16</div>
                    )}
                    <span className="absolute top-1 left-1 px-1 rounded bg-black/80 text-[9px] font-mono font-bold text-amber-300">
                      ★ {clip.viral_score.overall}
                    </span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <h5 className="text-xs font-semibold text-white truncate group-hover:text-purple-300">
                      {clip.title}
                    </h5>
                    <p className="text-[11px] text-slate-400 truncate mt-0.5 italic">
                      "{clip.hook}"
                    </p>
                    <div className="flex items-center space-x-2 mt-2">
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
                        {Math.round(clip.duration)}s
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.05] text-slate-400">
                        {clip.caption_preset}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
