import React from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Film, 
  Sparkles, 
  Youtube, 
  HardDrive, 
  Clock, 
  PieChart, 
  Activity,
  Flame
} from 'lucide-react';
import { GlassCard } from '../components/GlassCard';
import { MetricsWidget } from '../components/MetricsWidget';
import { DashboardMetrics, Clip } from '../types';

interface AnalyticsProps {
  metrics: DashboardMetrics;
  clips: Clip[];
}

export const AnalyticsScreen: React.FC<AnalyticsProps> = ({
  metrics,
  clips,
}) => {
  const categoryCounts: Record<string, number> = {};
  clips.forEach((c) => {
    categoryCounts[c.category] = (categoryCounts[c.category] || 0) + 1;
  });

  return (
    <div className="space-y-8 max-w-6xl mx-auto animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center space-x-2.5">
          <BarChart3 className="w-6 h-6 text-purple-400" />
          <span>Factory Analytics & Performance Telemetry</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Historical clip generation efficiency, viral score averages, category distribution, and storage utilization.
        </p>
      </div>

      {/* Top Counters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricsWidget
          label="Total Source Videos"
          value={metrics.total_videos_processed}
          subValue="processed"
          icon={<Film className="w-5 h-5" />}
          color="purple"
        />
        <MetricsWidget
          label="Clips Produced"
          value={metrics.total_clips_generated}
          subValue="shorts"
          icon={<Sparkles className="w-5 h-5" />}
          color="blue"
        />
        <MetricsWidget
          label="Mean Virality Score"
          value={`${metrics.average_clip_score}/100`}
          subValue="AI rating"
          icon={<TrendingUp className="w-5 h-5" />}
          color="green"
        />
        <MetricsWidget
          label="Shorts Published"
          value={metrics.published_shorts}
          subValue="on YouTube"
          icon={<Youtube className="w-5 h-5" />}
          color="red"
        />
      </div>

      {/* Content Distribution & Performance */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <GlassCard title="Content Category Distribution">
          <div className="space-y-3">
            {Object.keys(categoryCounts).length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">No categorized clips found yet.</p>
            ) : (
              Object.entries(categoryCounts).map(([cat, count]) => {
                const percent = Math.round((count / (clips.length || 1)) * 100);
                return (
                  <div key={cat} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-300 capitalize font-medium">{cat}</span>
                      <span className="text-purple-300 font-mono">{count} clips ({percent}%)</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-purple-500 to-sky-400 rounded-full"
                        style={{ width: `${percent}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </GlassCard>

        <GlassCard title="Disk & Pipeline Storage Footprint">
          <div className="space-y-4">
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-slate-400">Total Factory Storage Used</span>
              <span className="text-emerald-400 font-bold">{(metrics.storage_usage_mb / 1024).toFixed(2)} GB</span>
            </div>

            <div className="w-full h-3 rounded-full bg-slate-800 overflow-hidden flex">
              <div className="bg-purple-500 h-full" style={{ width: '45%' }} title="Rendered Clips"></div>
              <div className="bg-sky-500 h-full" style={{ width: '35%' }} title="Raw Uploads"></div>
              <div className="bg-amber-500 h-full" style={{ width: '20%' }} title="Temp Audio/Frames"></div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-[11px] text-slate-400 font-mono pt-2">
              <div className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span>
                <span>Clips (45%)</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-sky-500"></span>
                <span>Uploads (35%)</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                <span>Temp (20%)</span>
              </div>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};
