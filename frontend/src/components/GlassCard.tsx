import React from 'react';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  icon?: React.ReactNode;
  headerAction?: React.ReactNode;
  glow?: 'purple' | 'blue' | 'none';
  onClick?: () => void;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className = '',
  title,
  subtitle,
  icon,
  headerAction,
  glow = 'none',
  onClick,
}) => {
  const glowClass = 
    glow === 'purple' ? 'hover:border-purple-500/40 hover:shadow-[0_0_25px_rgba(139,92,246,0.2)]' :
    glow === 'blue' ? 'hover:border-sky-500/40 hover:shadow-[0_0_25px_rgba(56,189,248,0.2)]' : '';

  return (
    <div
      onClick={onClick}
      className={`glass-panel rounded-2xl p-6 transition-all duration-300 relative overflow-hidden ${glowClass} ${className} ${onClick ? 'cursor-pointer' : ''}`}
    >
      {(title || headerAction || icon) && (
        <div className="flex items-center justify-between mb-4 border-b border-white/[0.06] pb-3">
          <div className="flex items-center space-x-3">
            {icon && (
              <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
                {icon}
              </div>
            )}
            <div>
              {title && <h3 className="text-base font-semibold text-slate-100">{title}</h3>}
              {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
            </div>
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
