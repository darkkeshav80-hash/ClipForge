import React from 'react';

interface MetricsWidgetProps {
  label: string;
  value: string | number;
  subValue?: string;
  icon: React.ReactNode;
  trend?: string;
  trendType?: 'positive' | 'negative' | 'neutral';
  color?: 'purple' | 'blue' | 'green' | 'amber' | 'red';
}

export const MetricsWidget: React.FC<MetricsWidgetProps> = ({
  label,
  value,
  subValue,
  icon,
  trend,
  trendType = 'positive',
  color = 'purple',
}) => {
  const colorMap = {
    purple: {
      bg: 'bg-purple-500/10',
      border: 'border-purple-500/20',
      text: 'text-purple-400',
      glow: 'shadow-[0_0_20px_rgba(139,92,246,0.15)]',
    },
    blue: {
      bg: 'bg-sky-500/10',
      border: 'border-sky-500/20',
      text: 'text-sky-400',
      glow: 'shadow-[0_0_20px_rgba(56,189,248,0.15)]',
    },
    green: {
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20',
      text: 'text-emerald-400',
      glow: 'shadow-[0_0_20px_rgba(34,197,94,0.15)]',
    },
    amber: {
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20',
      text: 'text-amber-400',
      glow: 'shadow-[0_0_20px_rgba(245,158,11,0.15)]',
    },
    red: {
      bg: 'bg-rose-500/10',
      border: 'border-rose-500/20',
      text: 'text-rose-400',
      glow: 'shadow-[0_0_20px_rgba(239,68,68,0.15)]',
    },
  }[color];

  return (
    <div className={`glass-panel rounded-2xl p-5 border border-white/[0.08] hover:border-white/[0.18] transition-all duration-300 relative group overflow-hidden ${colorMap.glow}`}>
      <div className="flex items-start justify-between">
        <div>
          <span className="text-xs font-medium text-slate-400 tracking-wide uppercase">{label}</span>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-white tracking-tight">{value}</span>
            {subValue && <span className="text-xs text-slate-400 font-medium">{subValue}</span>}
          </div>
          {trend && (
            <div className="mt-2 flex items-center space-x-1.5 text-xs">
              <span className={
                trendType === 'positive' ? 'text-emerald-400 font-medium' :
                trendType === 'negative' ? 'text-rose-400 font-medium' : 'text-slate-400'
              }>
                {trend}
              </span>
              <span className="text-slate-500 text-[10px]">vs last week</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-xl ${colorMap.bg} ${colorMap.border} border ${colorMap.text} transition-transform group-hover:scale-110 duration-300`}>
          {icon}
        </div>
      </div>
    </div>
  );
};
