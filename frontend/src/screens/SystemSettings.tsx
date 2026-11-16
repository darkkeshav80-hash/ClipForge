import React, { useState } from 'react';
import { 
  Settings, 
  Cpu, 
  HardDrive, 
  Trash2, 
  Check, 
  ShieldCheck, 
  AlertTriangle, 
  Save, 
  Zap, 
  Eye, 
  EyeOff,
  Activity
} from 'lucide-react';
import { GlassCard } from '../components/GlassCard';
import { HardwareProfileConfig } from '../types';
import { api } from '../services/api';

interface SystemSettingsProps {
  hardware: HardwareProfileConfig;
  isLowPerf: boolean;
  onToggleLowPerf: () => void;
  onUpdateHardware: (config: HardwareProfileConfig) => void;
}

export const SystemSettingsScreen: React.FC<SystemSettingsProps> = ({
  hardware,
  isLowPerf,
  onToggleLowPerf,
  onUpdateHardware,
}) => {
  const [profile, setProfile] = useState<HardwareProfileConfig['profile']>(hardware.profile);
  const [ffmpegThreads, setFfmpegThreads] = useState<number>(hardware.ffmpeg_threads);
  const [whisperModel, setWhisperModel] = useState<HardwareProfileConfig['whisper_model']>(hardware.whisper_model);
  const [enableGpu, setEnableGpu] = useState<boolean>(hardware.enable_gpu);
  const [cleanupDays, setCleanupDays] = useState<number>(7);
  const [cleanupStatus, setCleanupStatus] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const handleProfileSelect = (p: HardwareProfileConfig['profile']) => {
    setProfile(p);
    if (p === 'ECO') {
      setFfmpegThreads(2);
      setWhisperModel('tiny');
      setEnableGpu(false);
    } else if (p === 'BALANCED') {
      setFfmpegThreads(4);
      setWhisperModel('base');
      setEnableGpu(false);
    } else {
      setFfmpegThreads(8);
      setWhisperModel('small');
      setEnableGpu(true);
    }
  };

  const handleSave = async () => {
    const newConfig: HardwareProfileConfig = {
      profile,
      max_ram_usage_gb: profile === 'ECO' ? 6 : profile === 'BALANCED' ? 12 : 16,
      ffmpeg_threads: ffmpegThreads,
      analysis_resolution: profile === 'ECO' ? '360p' : profile === 'BALANCED' ? '480p' : '720p',
      whisper_model: whisperModel,
      enable_gpu: enableGpu,
      max_concurrent_jobs: profile === 'ECO' ? 1 : 2,
    };

    try {
      await api.updateSystemSettings({ hardware: newConfig, low_performance_mode: isLowPerf });
      onUpdateHardware(newConfig);
      setSaveStatus('Hardware settings applied successfully!');
      setTimeout(() => setSaveStatus(null), 3000);
    } catch (err: any) {
      setSaveStatus(`Failed to update settings: ${err.message}`);
    }
  };

  const handleCleanup = async () => {
    try {
      const res = await api.triggerStorageCleanup(cleanupDays);
      setCleanupStatus(`Cleaned up temp storage! Freed ${res.freed_mb} MB.`);
      setTimeout(() => setCleanupStatus(null), 4000);
    } catch (err: any) {
      setCleanupStatus(`Cleanup error: ${err.message}`);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2.5">
            <Settings className="w-6 h-6 text-purple-400" />
            <span>Hardware & System Configuration</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Tune FFmpeg threads, Faster-Whisper memory models, and disk cleanup routines for optimal Windows performance.
          </p>
        </div>

        <button
          onClick={handleSave}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs shadow-[0_0_20px_rgba(139,92,246,0.3)] transition-all"
        >
          <Save className="w-4 h-4" />
          <span>Save System Settings</span>
        </button>
      </div>

      {saveStatus && (
        <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-200 text-xs font-mono">
          {saveStatus}
        </div>
      )}

      {/* Hardware Profile Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          {
            id: 'ECO' as const,
            title: 'ECO PROFILE',
            desc: 'Minimal RAM footprint (<6GB). 2 CPU threads, Tiny Whisper model, 360p analysis frames.',
            badge: 'Laptop Friendly',
          },
          {
            id: 'BALANCED' as const,
            title: 'BALANCED (Recommended)',
            desc: 'Moderate footprint (<12GB). 4 CPU threads, Base Whisper model, 480p frames with fast rendering.',
            badge: 'Standard PC',
          },
          {
            id: 'QUALITY' as const,
            title: 'QUALITY STUDIO',
            desc: 'Maximum precision. Small/Medium Whisper, 8 threads, GPU acceleration enabled if available.',
            badge: 'Max Precision',
          },
        ].map((item) => (
          <div
            key={item.id}
            onClick={() => handleProfileSelect(item.id)}
            className={`p-5 rounded-2xl border cursor-pointer transition-all ${
              profile === item.id
                ? 'bg-purple-600/20 border-purple-500 shadow-[0_0_20px_rgba(139,92,246,0.25)]'
                : 'bg-white/[0.03] border-white/[0.08] hover:bg-white/[0.06]'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono font-bold uppercase text-purple-300 bg-purple-500/20 px-2 py-0.5 rounded border border-purple-500/30">
                {item.badge}
              </span>
              {profile === item.id && <Check className="w-4 h-4 text-purple-400" />}
            </div>
            <h4 className="text-sm font-bold text-white mt-2">{item.title}</h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </div>

      {/* Visual & Execution Engine Tweaks */}
      <GlassCard title="Execution & Video Engine Tuning" icon={<Cpu className="w-4 h-4 text-sky-400" />}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              FFmpeg Encoding Threads: <span className="font-mono text-purple-300 font-bold">{ffmpegThreads}</span>
            </label>
            <input
              type="range"
              min="1"
              max="16"
              value={ffmpegThreads}
              onChange={(e) => setFfmpegThreads(Number(e.target.value))}
              className="w-full accent-purple-500"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Controls CPU thread count utilized by FFmpeg during vertical cropping and subtitle burn-in.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Whisper Transcription Model
            </label>
            <select
              value={whisperModel}
              onChange={(e) => setWhisperModel(e.target.value as any)}
              className="w-full px-3 py-2 rounded-xl glass-input text-xs font-mono"
            >
              <option value="tiny">Tiny (39M params - Fast, lowest RAM ~1GB)</option>
              <option value="base">Base (74M params - Balanced accuracy ~1.5GB)</option>
              <option value="small">Small (244M params - High accuracy ~2.5GB)</option>
              <option value="medium">Medium (769M params - Studio precision ~5GB)</option>
            </select>
          </div>

          <div className="sm:col-span-2 pt-2 border-t border-white/[0.06] flex flex-wrap gap-6 items-center">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={enableGpu}
                onChange={(e) => setEnableGpu(e.target.checked)}
                className="rounded bg-slate-800 border-white/20 text-purple-600"
              />
              <div>
                <span className="text-xs font-semibold text-white block">Enable GPU Acceleration (NVENC / AMF)</span>
                <span className="text-[10px] text-slate-400">Uses hardware acceleration if supported on Windows</span>
              </div>
            </label>

            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={isLowPerf}
                onChange={onToggleLowPerf}
                className="rounded bg-slate-800 border-white/20 text-purple-600"
              />
              <div>
                <span className="text-xs font-semibold text-white block">Low-Performance Visual Mode</span>
                <span className="text-[10px] text-slate-400">Disables heavy blur & animations for ultra-smooth rendering</span>
              </div>
            </label>
          </div>
        </div>
      </GlassCard>

      {/* Storage Hygiene */}
      <GlassCard title="Storage Hygiene & Auto-Cleanup" icon={<HardDrive className="w-4 h-4 text-emerald-400" />}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h4 className="text-xs font-bold text-white">Purge Temporary Files & Intermediate Frames</h4>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Safely removes extracted audio chunks and scene frames older than specified days while keeping your original videos and finished clips untouched.
            </p>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <select
              value={cleanupDays}
              onChange={(e) => setCleanupDays(Number(e.target.value))}
              className="px-3 py-2 rounded-xl glass-input text-xs font-mono"
            >
              <option value={3}>Older than 3 days</option>
              <option value={7}>Older than 7 days</option>
              <option value={14}>Older than 14 days</option>
              <option value={30}>Older than 30 days</option>
            </select>

            <button
              onClick={handleCleanup}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] text-xs font-semibold text-slate-200 border border-white/[0.1] transition-all"
            >
              <Trash2 className="w-3.5 h-3.5 text-rose-400" />
              <span>Clean Storage</span>
            </button>
          </div>
        </div>

        {cleanupStatus && (
          <div className="mt-3 p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-mono">
            {cleanupStatus}
          </div>
        )}
      </GlassCard>
    </div>
  );
};
