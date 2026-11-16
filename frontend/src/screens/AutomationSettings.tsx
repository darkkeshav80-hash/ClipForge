import React, { useState } from 'react';
import { 
  Flame, 
  Play, 
  Pause, 
  Square, 
  Save, 
  Check, 
  Sparkles, 
  Sliders, 
  RotateCcw,
  ShieldAlert,
  Youtube
} from 'lucide-react';
import { GlassCard } from '../components/GlassCard';
import { AutomationSettings, CaptionStyleConfig } from '../types';
import { api } from '../services/api';

interface AutomationSettingsProps {
  settings: AutomationSettings;
  presets: CaptionStyleConfig[];
  isRunning: boolean;
  onUpdateSettings: (settings: AutomationSettings) => void;
  onControlAction: (action: 'start' | 'pause' | 'resume' | 'stop') => void;
}

export const AutomationSettingsScreen: React.FC<AutomationSettingsProps> = ({
  settings,
  presets,
  isRunning,
  onUpdateSettings,
  onControlAction,
}) => {
  const [formData, setFormData] = useState<AutomationSettings>({ ...settings });
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const updated = await api.saveAutomationSettings(formData);
      onUpdateSettings(updated);
      setSaveStatus('Automation parameters updated successfully!');
      setTimeout(() => setSaveStatus(null), 3000);
    } catch (err: any) {
      setSaveStatus(`Error saving settings: ${err.message}`);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2.5">
            <Flame className="w-6 h-6 text-amber-500" />
            <span>Autonomous Factory Orchestration</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure hands-free background workers to ingest videos, detect viral moments, render vertical Shorts, and push to YouTube.
          </p>
        </div>

        {/* Global Factory Master Controls */}
        <div className="flex items-center space-x-2">
          {isRunning ? (
            <>
              <button
                onClick={() => onControlAction('pause')}
                className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-semibold hover:bg-amber-500/30 transition-all"
              >
                <Pause className="w-4 h-4" />
                <span>Pause Factory</span>
              </button>
              <button
                onClick={() => onControlAction('stop')}
                className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-semibold hover:bg-rose-500/30 transition-all"
              >
                <Square className="w-4 h-4" />
                <span>Stop</span>
              </button>
            </>
          ) : (
            <button
              onClick={() => onControlAction('start')}
              className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-xs font-semibold shadow-[0_0_20px_rgba(139,92,246,0.4)] hover:from-purple-500 transition-all"
            >
              <Play className="w-4 h-4 fill-white" />
              <span>START AUTONOMOUS FACTORY</span>
            </button>
          )}
        </div>
      </div>

      {saveStatus && (
        <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-200 text-xs font-mono">
          {saveStatus}
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Factory Thresholds */}
        <GlassCard title="Autonomous Filtering & Extraction Limits">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-semibold text-slate-300">
                  Clips Per Video: <span className="font-mono text-purple-300 font-bold">{formData.clips_per_video}</span>
                </label>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={formData.clips_per_video}
                onChange={(e) => setFormData({ ...formData, clips_per_video: Number(e.target.value) })}
                className="w-full accent-purple-500"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-semibold text-slate-300">
                  Minimum Viral Threshold: <span className="font-mono text-amber-300 font-bold">{formData.min_viral_score}/100</span>
                </label>
              </div>
              <input
                type="range"
                min="50"
                max="90"
                value={formData.min_viral_score}
                onChange={(e) => setFormData({ ...formData, min_viral_score: Number(e.target.value) })}
                className="w-full accent-amber-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Default Caption Preset
              </label>
              <select
                value={formData.default_caption_preset}
                onChange={(e) => setFormData({ ...formData, default_caption_preset: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl glass-input text-xs"
              >
                {presets.map((p) => (
                  <option key={p.preset_id} value={p.preset_id}>
                    {p.name} ({p.category})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Export Resolution
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(['1080p', '720p', '480p'] as const).map((res) => (
                  <button
                    key={res}
                    type="button"
                    onClick={() => setFormData({ ...formData, output_resolution: res })}
                    className={`py-2 rounded-xl text-xs font-mono font-bold transition-all ${
                      formData.output_resolution === res
                        ? 'bg-purple-600/30 text-purple-200 border border-purple-500/50'
                        : 'bg-white/[0.04] text-slate-400'
                    }`}
                  >
                    {res}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </GlassCard>

        {/* Autonomous Distribution */}
        <GlassCard title="Automated Quality & Publishing Pipeline" icon={<Youtube className="w-4 h-4 text-red-500" />}>
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <label className="flex items-center space-x-3 cursor-pointer p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                <input
                  type="checkbox"
                  checked={formData.auto_quality_review}
                  onChange={(e) => setFormData({ ...formData, auto_quality_review: e.target.checked })}
                  className="rounded bg-slate-800 border-white/20 text-purple-600"
                />
                <div>
                  <span className="text-xs font-semibold text-white block">Auto Multi-Model Quality Review</span>
                  <span className="text-[10px] text-slate-400">Re-renders clip if start/end bounds are unnatural</span>
                </div>
              </label>

              <label className="flex items-center space-x-3 cursor-pointer p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                <input
                  type="checkbox"
                  checked={formData.auto_publish_youtube}
                  onChange={(e) => setFormData({ ...formData, auto_publish_youtube: e.target.checked })}
                  className="rounded bg-slate-800 border-white/20 text-purple-600"
                />
                <div>
                  <span className="text-xs font-semibold text-white block">Autonomous YouTube Shorts Upload</span>
                  <span className="text-[10px] text-slate-400">Pushes verified clips directly to connected channel</span>
                </div>
              </label>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Daily YouTube Upload Cap
                </label>
                <input
                  type="number"
                  min="1"
                  max="15"
                  value={formData.daily_upload_limit}
                  onChange={(e) => setFormData({ ...formData, daily_upload_limit: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-xl glass-input text-xs font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Drip Schedule
                </label>
                <select
                  value={formData.publishing_schedule}
                  onChange={(e) => setFormData({ ...formData, publishing_schedule: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl glass-input text-xs"
                >
                  <option value="immediate">Immediate (As soon as rendered)</option>
                  <option value="daily_12pm">Daily at 12:00 PM</option>
                  <option value="daily_6pm">Daily at 6:00 PM (Peak)</option>
                  <option value="spaced_3h">Spaced Every 3 Hours</option>
                </select>
              </div>
            </div>
          </div>
        </GlassCard>

        {/* Save */}
        <div className="flex justify-end">
          <button
            type="submit"
            className="flex items-center space-x-2 px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs shadow-[0_0_20px_rgba(139,92,246,0.3)] transition-all"
          >
            <Save className="w-4 h-4" />
            <span>Save Automation Configuration</span>
          </button>
        </div>
      </form>
    </div>
  );
};
