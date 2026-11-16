import React, { useRef, useEffect } from 'react';
import { Terminal, CheckCircle2, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { ProcessingLog } from '../types';

interface LiveLogViewerProps {
  logs: ProcessingLog[];
  height?: string;
  onClear?: () => void;
}

export const LiveLogViewer: React.FC<LiveLogViewerProps> = ({
  logs,
  height = 'h-64',
  onClear,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="glass-panel rounded-2xl overflow-hidden border border-white/[0.1]">
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#0A0E1A]/80 border-b border-white/[0.08]">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-300">
          <Terminal className="w-3.5 h-3.5 text-purple-400" />
          <span>LIVE PIPELINE LOGS</span>
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
            {logs.length} events
          </span>
        </div>
        {onClear && (
          <button
            onClick={onClear}
            className="text-xs text-slate-400 hover:text-white transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      <div
        ref={containerRef}
        className={`${height} overflow-y-auto p-4 space-y-2 font-mono text-xs bg-[#060913]/90 select-text`}
      >
        {logs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 text-center">
            <Terminal className="w-6 h-6 mb-2 opacity-40 text-purple-400" />
            <p>Awaiting pipeline execution events...</p>
          </div>
        ) : (
          logs.map((log) => {
            const time = new Date(log.timestamp).toLocaleTimeString();
            const levelIcon =
              log.level === 'success' ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" /> :
              log.level === 'warn' ? <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" /> :
              log.level === 'error' ? <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" /> :
              <Info className="w-3.5 h-3.5 text-sky-400 shrink-0 mt-0.5" />;

            const levelColor =
              log.level === 'success' ? 'text-emerald-300' :
              log.level === 'warn' ? 'text-amber-300' :
              log.level === 'error' ? 'text-rose-300' : 'text-slate-300';

            return (
              <div key={log.id} className="flex items-start space-x-2.5 leading-relaxed group hover:bg-white/[0.02] p-1 rounded">
                <span className="text-slate-500 text-[10px] select-none font-mono shrink-0">[{time}]</span>
                {levelIcon}
                <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wider bg-white/[0.06] text-slate-400 shrink-0">
                  {log.stage}
                </span>
                <span className={`${levelColor} break-all font-sans text-xs`}>{log.message}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
