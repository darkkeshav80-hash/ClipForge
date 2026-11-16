import React, { useState } from 'react';
import { 
  KeyRound, 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  ExternalLink, 
  Eye, 
  EyeOff, 
  RefreshCw, 
  Plus, 
  ShieldCheck, 
  Server,
  Zap
} from 'lucide-react';
import { GlassCard } from '../components/GlassCard';
import { AIProvider } from '../types';
import { api } from '../services/api';

interface APIProviderSettingsProps {
  providers: AIProvider[];
  onUpdateProvider: (provider: AIProvider) => void;
}

export const APIProviderSettingsScreen: React.FC<APIProviderSettingsProps> = ({
  providers,
  onUpdateProvider,
}) => {
  const [testingId, setTestingId] = useState<string | null>(null);
  const [showKeyMap, setShowKeyMap] = useState<Record<string, boolean>>({});
  const [testResult, setTestResult] = useState<Record<string, { success: boolean; msg: string }>>({});

  const toggleShowKey = (id: string) => {
    setShowKeyMap((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleTest = async (provider: AIProvider) => {
    setTestingId(provider.id);
    setTestResult((prev) => ({ ...prev, [provider.id]: { success: false, msg: 'Testing connectivity...' } }));

    try {
      const res = await api.testProvider(provider.id);
      setTestResult((prev) => ({
        ...prev,
        [provider.id]: { success: res.success, msg: res.message || 'Connected successfully!' }
      }));
      if (res.models && res.models.length > 0) {
        onUpdateProvider({
          ...provider,
          status: 'connected',
          models: res.models,
        });
      }
    } catch (err: any) {
      setTestResult((prev) => ({
        ...prev,
        [provider.id]: { success: false, msg: err.message || 'Connection failed' }
      }));
    } finally {
      setTestingId(null);
    }
  };

  const handleToggleEnable = async (provider: AIProvider) => {
    const updated = { ...provider, enabled: !provider.enabled };
    await api.updateProvider(updated);
    onUpdateProvider(updated);
  };

  const handleKeyChange = async (provider: AIProvider, newKey: string) => {
    const updated = { ...provider, api_key: newKey };
    await api.updateProvider(updated);
    onUpdateProvider(updated);
  };

  const handleBaseUrlChange = async (provider: AIProvider, newUrl: string) => {
    const updated = { ...provider, base_url: newUrl };
    await api.updateProvider(updated);
    onUpdateProvider(updated);
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2.5">
            <KeyRound className="w-6 h-6 text-purple-400" />
            <span>AI Provider & API Integrations</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure private API keys for frontier LLMs, Groq LPUs, and local Ollama servers. Keys are stored safely in your local Windows vault.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono px-3 py-1.5 rounded-xl bg-purple-500/10 text-purple-300 border border-purple-500/20">
          <ShieldCheck className="w-4 h-4 text-purple-400" />
          <span>Local Vault Encryption: Active</span>
        </div>
      </div>

      {/* Provider Cards */}
      <div className="space-y-4">
        {providers.map((p) => {
          const isTesting = testingId === p.id;
          const showKey = showKeyMap[p.id];
          const result = testResult[p.id];

          return (
            <div
              key={p.id}
              className={`glass-panel rounded-2xl p-6 border transition-all ${
                p.enabled ? 'border-white/[0.12]' : 'border-white/[0.04] opacity-75'
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
                <div className="flex items-center space-x-3">
                  <div className={`p-2.5 rounded-xl border ${
                    p.id === 'ollama' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                    p.id === 'groq' ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' :
                    'bg-purple-500/10 border-purple-500/20 text-purple-400'
                  }`}>
                    {p.id === 'ollama' ? <Server className="w-5 h-5" /> : <Zap className="w-5 h-5" />}
                  </div>

                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="text-sm font-bold text-white">{p.name}</h3>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                        p.status === 'connected' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                        'bg-white/[0.06] text-slate-400'
                      }`}>
                        {p.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5 font-mono">Type: {p.type}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  {/* Test Connection Button */}
                  <button
                    onClick={() => handleTest(p)}
                    disabled={isTesting || (!p.api_key && p.id !== 'ollama')}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] text-xs font-semibold text-slate-200 border border-white/[0.1] transition-all disabled:opacity-40"
                  >
                    {isTesting ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />
                    ) : (
                      <RefreshCw className="w-3.5 h-3.5 text-purple-400" />
                    )}
                    <span>{isTesting ? 'Testing...' : 'Test Connection'}</span>
                  </button>

                  {/* Enable/Disable Toggle */}
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={p.enabled}
                      onChange={() => handleToggleEnable(p)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                  </label>
                </div>
              </div>

              {/* Provider Inputs */}
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                {p.id !== 'ollama' && (
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wide mb-1">
                      API Key
                    </label>
                    <div className="relative">
                      <input
                        type={showKey ? 'text' : 'password'}
                        value={p.api_key || ''}
                        onChange={(e) => handleKeyChange(p, e.target.value)}
                        placeholder={`Enter your ${p.name} API Key...`}
                        className="w-full px-3 py-2 pr-10 rounded-xl glass-input text-xs font-mono"
                      />
                      <button
                        type="button"
                        onClick={() => toggleShowKey(p.id)}
                        className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-200"
                      >
                        {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wide mb-1">
                    API Base URL {p.id === 'ollama' && '(Default localhost:11434)'}
                  </label>
                  <input
                    type="text"
                    value={p.base_url || ''}
                    onChange={(e) => handleBaseUrlChange(p, e.target.value)}
                    placeholder="https://api.provider.com/v1"
                    className="w-full px-3 py-2 rounded-xl glass-input text-xs font-mono"
                  />
                </div>
              </div>

              {/* Models List Badge */}
              <div className="mt-3 flex flex-wrap items-center gap-1.5">
                <span className="text-[10px] text-slate-500 font-mono">Models:</span>
                {p.models.map((m) => (
                  <span key={m} className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/[0.04] text-slate-300 border border-white/[0.06]">
                    {m}
                  </span>
                ))}
              </div>

              {/* Test Result Message */}
              {result && (
                <div className={`mt-3 p-2.5 rounded-xl text-xs font-mono flex items-center space-x-2 ${
                  result.success ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                }`}>
                  {result.success ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <XCircle className="w-4 h-4 shrink-0" />}
                  <span>{result.msg}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
