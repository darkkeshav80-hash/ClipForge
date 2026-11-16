import React, { useState } from 'react';
import { 
  Bot, 
  Sparkles, 
  Cpu, 
  Layers, 
  Check, 
  Save, 
  DollarSign, 
  ShieldCheck, 
  Sliders,
  AlertCircle
} from 'lucide-react';
import { GlassCard } from '../components/GlassCard';
import { AIProvider, AITaskType, TaskModelAssignment } from '../types';
import { api } from '../services/api';

interface AIModelManagerProps {
  providers: AIProvider[];
  assignments: TaskModelAssignment[];
  onUpdateAssignments: (assignments: TaskModelAssignment[]) => void;
}

const TASK_DEFS: { id: AITaskType; title: string; desc: string; defaultModel: string }[] = [
  { id: 'video_understanding', title: 'Video Understanding & Vision Frames', desc: 'Analyzes visual scene dynamics, objects, and speaker faces', defaultModel: 'gemini-2.5-flash' },
  { id: 'clip_discovery', title: 'Viral Moment Discovery', desc: 'Scans full audio transcripts for emotional peaks and hooks', defaultModel: 'gpt-4o-mini' },
  { id: 'viral_scoring', title: 'Virality Scoring Engine (0-100)', desc: 'Computes multi-factor retention potential and hook scores', defaultModel: 'gpt-4o-mini' },
  { id: 'editing_decisions', title: 'AI Editing Brain & Decision Plan', desc: 'Generates structured JSON cuts, zooms, silence trimmings', defaultModel: 'gpt-4o' },
  { id: 'caption_correction', title: 'Caption & Subtitle Alignment', desc: 'Punctuation, casing, emoji insertion, and Hinglish fixes', defaultModel: 'llama-3.3-70b-versatile' },
  { id: 'hook_generation', title: 'Punchy Hook Rewriter', desc: 'Optimizes first 3 seconds to maximize scroll-stop rate', defaultModel: 'gpt-4o-mini' },
  { id: 'title_generation', title: 'SEO YouTube Shorts Title', desc: 'Generates algorithm-optimized, high CTR video titles', defaultModel: 'gpt-4o-mini' },
  { id: 'description_generation', title: 'Description & Viral Hashtags', desc: 'Drafts relevant description, timestamps, and metadata tags', defaultModel: 'gpt-4o-mini' },
  { id: 'thumbnail_analysis', title: 'Thumbnail Frame Ranking', desc: 'Selects the most visually expressive frame for the cover', defaultModel: 'gemini-2.5-flash' },
  { id: 'final_quality_review', title: 'Multi-Model Post-Render Quality Review', desc: 'Validates independent storytelling and checks crop accuracy', defaultModel: 'claude-3-5-haiku' },
];

export const AIModelManagerScreen: React.FC<AIModelManagerProps> = ({
  providers,
  assignments,
  onUpdateAssignments,
}) => {
  const [modelMode, setModelMode] = useState<'free' | 'mixed' | 'quality'>('mixed');
  const [currentAssignments, setCurrentAssignments] = useState<TaskModelAssignment[]>(
    assignments.length > 0 ? assignments : TASK_DEFS.map((t) => ({
      task: t.id,
      provider_id: 'ollama',
      model: t.defaultModel,
    }))
  );
  const [monthlyBudgetLimit, setMonthlyBudgetLimit] = useState<number>(20);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const handleModelChange = (task: AITaskType, providerId: string, model: string) => {
    setCurrentAssignments((prev) => {
      const idx = prev.findIndex((a) => a.task === task);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = { task, provider_id: providerId, model };
        return next;
      }
      return [...prev, { task, provider_id: providerId, model }];
    });
  };

  const handleSave = async () => {
    try {
      await api.saveTaskAssignments(currentAssignments);
      onUpdateAssignments(currentAssignments);
      setSaveStatus('Model assignments saved successfully!');
      setTimeout(() => setSaveStatus(null), 3000);
    } catch (err: any) {
      setSaveStatus(`Failed to save: ${err.message}`);
    }
  };

  // Helper to get available models across all enabled providers
  const allAvailableModels: { providerId: string; providerName: string; model: string }[] = [];
  providers.forEach((p) => {
    p.models.forEach((m) => {
      allAvailableModels.push({ providerId: p.id, providerName: p.name, model: m });
    });
  });

  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2.5">
            <Bot className="w-6 h-6 text-purple-400" />
            <span>Advanced AI Model Manager</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Assign specialized AI models per task. Route heavy reasoning to powerful models while keeping transcript processing fast & local.
          </p>
        </div>

        <button
          onClick={handleSave}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold text-xs shadow-[0_0_20px_rgba(139,92,246,0.4)] hover:from-purple-500 transition-all"
        >
          <Save className="w-4 h-4" />
          <span>Save Model Routing</span>
        </button>
      </div>

      {saveStatus && (
        <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-200 text-xs font-mono">
          {saveStatus}
        </div>
      )}

      {/* Model Modes (Free / Mixed / Quality) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { id: 'free', title: 'FREE LOCAL MODE', desc: '100% offline via Ollama & local heuristics. Zero API costs, runs on CPU/RAM.', badge: 'No Cloud' },
          { id: 'mixed', title: 'MIXED MODE (Recommended)', desc: 'Local whisper transcription + fast cloud LLM for viral selection & editing JSON.', badge: 'Optimal' },
          { id: 'quality', title: 'MAX QUALITY MODE', desc: 'Uses frontier reasoning models (GPT-4o, Claude 3.7, Gemini 2.5 Pro) for high retention.', badge: 'Studio' },
        ].map((mode) => (
          <div
            key={mode.id}
            onClick={() => setModelMode(mode.id as any)}
            className={`p-5 rounded-2xl border cursor-pointer transition-all ${
              modelMode === mode.id
                ? 'bg-purple-600/20 border-purple-500 shadow-[0_0_20px_rgba(139,92,246,0.25)]'
                : 'bg-white/[0.03] border-white/[0.08] hover:bg-white/[0.06]'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase font-bold text-purple-300 bg-purple-500/20 px-2 py-0.5 rounded border border-purple-500/30">
                {mode.badge}
              </span>
              {modelMode === mode.id && <Check className="w-4 h-4 text-purple-400" />}
            </div>
            <h4 className="text-sm font-bold text-white mt-2">{mode.title}</h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">{mode.desc}</p>
          </div>
        ))}
      </div>

      {/* Spending & Cost Controls */}
      <GlassCard title="API Spending Guard & Limits" icon={<DollarSign className="w-4 h-4 text-emerald-400" />}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 items-center">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Monthly API Spending Cap: <span className="font-mono text-emerald-400">${monthlyBudgetLimit} USD</span>
            </label>
            <input
              type="range"
              min="5"
              max="100"
              value={monthlyBudgetLimit}
              onChange={(e) => setMonthlyBudgetLimit(Number(e.target.value))}
              className="w-full accent-emerald-500"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Automatically falls back to local Ollama if monthly spending reaches this threshold.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] text-xs space-y-1 font-mono">
            <div className="text-slate-400">Estimated Cost per 10-Min Video: <span className="text-white font-bold">$0.02 - $0.05</span></div>
            <div className="text-slate-400">Active Fallback Provider: <span className="text-purple-300 font-bold">Ollama (Local)</span></div>
          </div>
        </div>
      </GlassCard>

      {/* Task-Based Routing Table */}
      <GlassCard title="Task-Based Model Routing (10 Specialized Sub-Tasks)">
        <div className="divide-y divide-white/[0.06]">
          {TASK_DEFS.map((task) => {
            const current = currentAssignments.find((a) => a.task === task.id);
            const selectedVal = current ? `${current.provider_id}:${current.model}` : '';

            return (
              <div key={task.id} className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="max-w-md">
                  <h4 className="text-xs font-bold text-white flex items-center space-x-2">
                    <span>{task.title}</span>
                  </h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">{task.desc}</p>
                </div>

                <div className="flex items-center space-x-3 shrink-0">
                  <select
                    value={selectedVal}
                    onChange={(e) => {
                      const [pId, mId] = e.target.value.split(':');
                      handleModelChange(task.id, pId, mId);
                    }}
                    className="px-3 py-2 rounded-xl glass-input text-xs font-mono min-w-[220px]"
                  >
                    {allAvailableModels.length === 0 ? (
                      <option value="ollama:llama3.2">Ollama - llama3.2 (Local)</option>
                    ) : (
                      allAvailableModels.map((item, idx) => (
                        <option key={idx} value={`${item.providerId}:${item.model}`}>
                          {item.providerName} — {item.model}
                        </option>
                      ))
                    )}
                  </select>
                </div>
              </div>
            );
          })}
        </div>
      </GlassCard>
    </div>
  );
};
