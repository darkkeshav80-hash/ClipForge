import React from 'react';
import { 
  LayoutDashboard, 
  PlusCircle, 
  Layers, 
  Film, 
  Bot, 
  KeyRound, 
  Youtube, 
  BarChart3, 
  Cpu, 
  Settings,
  Flame,
  CheckCircle2
} from 'lucide-react';

export type ScreenId = 
  | 'dashboard'
  | 'new-project'
  | 'processing'
  | 'clips-gallery'
  | 'ai-models'
  | 'api-providers'
  | 'youtube-studio'
  | 'analytics'
  | 'automation'
  | 'system-settings';

interface SidebarProps {
  currentScreen: ScreenId;
  onNavigate: (screen: ScreenId) => void;
  clipsCount?: number;
  queueCount?: number;
}

interface NavItem {
  id: ScreenId;
  label: string;
  icon: any;
  badge?: string;
  count?: number;
  highlight?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentScreen,
  onNavigate,
  clipsCount = 0,
  queueCount = 0,
}) => {
  const navSections: NavSection[] = [
    {
      title: 'FACTORY WORKFLOW',
      items: [
        { id: 'dashboard' as ScreenId, label: 'Overview', icon: LayoutDashboard },
        { id: 'new-project' as ScreenId, label: 'New Project', icon: PlusCircle, badge: 'New' },
        { id: 'processing' as ScreenId, label: 'Processing Queue', icon: Layers, count: queueCount },
        { id: 'clips-gallery' as ScreenId, label: 'Generated Clips', icon: Film, count: clipsCount },
      ],
    },
    {
      title: 'AI BRAIN & PROVIDERS',
      items: [
        { id: 'ai-models' as ScreenId, label: 'AI Model Manager', icon: Bot },
        { id: 'api-providers' as ScreenId, label: 'API Providers', icon: KeyRound },
      ],
    },
    {
      title: 'DISTRIBUTION & CONTROL',
      items: [
        { id: 'youtube-studio' as ScreenId, label: 'YouTube Studio', icon: Youtube },
        { id: 'analytics' as ScreenId, label: 'Analytics', icon: BarChart3 },
        { id: 'automation' as ScreenId, label: 'Automation Factory', icon: Flame },
        { id: 'system-settings' as ScreenId, label: 'System & Hardware', icon: Settings },
      ],
    },
  ];

  return (
    <aside className="w-64 shrink-0 glass-panel border-r border-white/[0.08] min-h-[calc(100vh-65px)] flex flex-col justify-between py-5 px-3">
      <div className="space-y-6">
        {navSections.map((sec, idx) => (
          <div key={idx} className="space-y-1">
            <h4 className="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest font-mono">
              {sec.title}
            </h4>
            <div className="mt-2 space-y-0.5">
              {sec.items.map((item) => {
                const Icon = item.icon;
                const isActive = currentScreen === item.id;

                return (
                  <button
                    key={item.id}
                    onClick={() => onNavigate(item.id)}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all group ${
                      isActive
                        ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30 shadow-[0_0_15px_rgba(139,92,246,0.15)] font-semibold'
                        : 'text-slate-400 hover:text-slate-100 hover:bg-white/[0.04]'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <Icon className={`w-4 h-4 transition-colors ${
                        isActive ? 'text-purple-400' : 'text-slate-400 group-hover:text-slate-200'
                      }`} />
                      <span>{item.label}</span>
                    </div>

                    <div className="flex items-center space-x-1.5">
                      {item.badge && (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                          {item.badge}
                        </span>
                      )}
                      {typeof item.count === 'number' && item.count > 0 && (
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                          isActive ? 'bg-purple-500/30 text-purple-200' : 'bg-white/[0.08] text-slate-300'
                        }`}>
                          {item.count}
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* System Status footer */}
      <div className="p-3 rounded-xl bg-surface-card border border-white/[0.06] mt-4">
        <div className="flex items-center space-x-2 text-[11px] font-medium text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Engine: Ready (127.0.0.1:8000)</span>
        </div>
        <p className="text-[10px] text-slate-500 mt-1">FFmpeg 7.x + Whisper Core Online</p>
      </div>
    </aside>
  );
};
