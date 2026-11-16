import React, { useState } from 'react';
import { 
  Film, 
  Sparkles, 
  Download, 
  Youtube, 
  Play, 
  Trash2, 
  RefreshCw, 
  X, 
  Check, 
  ChevronRight,
  TrendingUp,
  Share2
} from 'lucide-react';
import { GlassCard } from '../components/GlassCard';
import { Clip } from '../types';
import { ScreenId } from '../components/Sidebar';

interface ClipsGalleryProps {
  clips: Clip[];
  onSelectClip: (clip: Clip) => void;
  onDeleteClip: (id: string) => void;
  onNavigate: (screen: ScreenId) => void;
}

export const GeneratedClipsGalleryScreen: React.FC<ClipsGalleryProps> = ({
  clips,
  onSelectClip,
  onDeleteClip,
  onNavigate,
}) => {
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [previewClip, setPreviewClip] = useState<Clip | null>(null);

  const categories = ['all', ...Array.from(new Set(clips.map((c) => c.category)))];

  const filteredClips = clips.filter((c) => {
    if (filterCategory !== 'all' && c.category !== filterCategory) return false;
    return true;
  });

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2.5">
            <Film className="w-6 h-6 text-purple-400" />
            <span>Generated Shorts & Reels</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Browse AI-curated moments, review virality scores, and export finished high-retention vertical videos.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold capitalize transition-all ${
                filterCategory === cat
                  ? 'bg-purple-600/30 text-purple-200 border border-purple-500/40 shadow-[0_0_10px_rgba(139,92,246,0.2)]'
                  : 'bg-white/[0.04] text-slate-400 border border-white/[0.08] hover:text-white'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Grid of Clips */}
      {filteredClips.length === 0 ? (
        <GlassCard className="text-center py-16">
          <Film className="w-12 h-12 text-slate-500 mx-auto mb-3 opacity-40" />
          <h3 className="text-base font-bold text-slate-300">No clips found in gallery</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Run an automation pipeline or upload a video project to generate high-retention vertical shorts.
          </p>
          <button
            onClick={() => onNavigate('new-project')}
            className="mt-4 px-5 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-semibold inline-flex items-center space-x-2 shadow-[0_0_20px_rgba(139,92,246,0.3)]"
          >
            <Sparkles className="w-4 h-4" />
            <span>Process New Video</span>
          </button>
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredClips.map((clip) => {
            const scoreColor =
              clip.viral_score.overall >= 85 ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' :
              clip.viral_score.overall >= 70 ? 'text-amber-400 border-amber-500/30 bg-amber-500/10' :
              'text-sky-400 border-sky-500/30 bg-sky-500/10';

            return (
              <div
                key={clip.id}
                className="glass-card rounded-2xl overflow-hidden border border-white/[0.08] hover:border-purple-500/40 flex flex-col justify-between group transition-all duration-300 shadow-lg"
              >
                <div>
                  {/* Thumbnail / 9:16 Video Container */}
                  <div className="relative aspect-[9/16] bg-slate-950 overflow-hidden flex items-center justify-center">
                    {clip.thumbnail_path ? (
                      <img
                        src={`/storage/${clip.thumbnail_path}`}
                        alt={clip.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-b from-slate-900 to-[#080B14] p-4 text-center">
                        <Film className="w-8 h-8 text-purple-400/50 mb-2" />
                        <span className="text-xs text-slate-500 font-mono">9:16 Vertical</span>
                      </div>
                    )}

                    {/* Viral Score Badge */}
                    <div className="absolute top-3 left-3">
                      <span className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-mono font-bold border backdrop-blur-md ${scoreColor}`}>
                        <Sparkles className="w-3 h-3" />
                        <span>{clip.viral_score.overall}/100</span>
                      </span>
                    </div>

                    {/* Duration Badge */}
                    <div className="absolute top-3 right-3 bg-black/75 backdrop-blur-md px-2 py-0.5 rounded text-[11px] font-mono text-white">
                      {Math.round(clip.duration)}s
                    </div>

                    {/* Play Overlay Button */}
                    <button
                      onClick={() => setPreviewClip(clip)}
                      className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <div className="w-12 h-12 rounded-full bg-purple-600/90 text-white flex items-center justify-center shadow-[0_0_25px_rgba(139,92,246,0.6)] transform scale-90 group-hover:scale-100 transition-transform">
                        <Play className="w-5 h-5 fill-white ml-0.5" />
                      </div>
                    </button>
                  </div>

                  {/* Card Content */}
                  <div className="p-4 space-y-2">
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-purple-400">
                      {clip.category}
                    </span>
                    <h4 className="text-sm font-bold text-white line-clamp-1 group-hover:text-purple-300 transition-colors">
                      {clip.title}
                    </h4>
                    <p className="text-xs text-slate-400 line-clamp-2 italic">
                      "{clip.hook}"
                    </p>

                    <div className="pt-2 flex items-center justify-between text-[11px] text-slate-500 border-t border-white/[0.06]">
                      <span>Style: {clip.caption_preset}</span>
                      <span className="capitalize">{clip.aspect_ratio}</span>
                    </div>
                  </div>
                </div>

                {/* Card Action Footer */}
                <div className="p-3 bg-black/30 border-t border-white/[0.06] flex items-center justify-between gap-1">
                  <button
                    onClick={() => setPreviewClip(clip)}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs font-medium text-slate-300 transition-colors"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Watch Clip</span>
                  </button>

                  <div className="flex items-center space-x-1">
                    {clip.rendered_path && (
                      <a
                        href={`/storage/${clip.rendered_path}`}
                        download={`${clip.title.replace(/[^a-zA-Z0-9]/g, '_')}.mp4`}
                        className="p-2 rounded-xl text-slate-400 hover:text-sky-300 hover:bg-white/[0.06] transition-colors"
                        title="Download MP4"
                      >
                        <Download className="w-4 h-4" />
                      </a>
                    )}

                  <button
                    onClick={() => {
                      onSelectClip(clip);
                      onNavigate('youtube-studio');
                    }}
                    className="p-2 rounded-xl text-slate-400 hover:text-emerald-400 hover:bg-white/[0.06] transition-colors"
                    title="Publish to YouTube Shorts"
                  >
                    <Youtube className="w-4 h-4" />
                  </button>

                  <button
                    onClick={() => onDeleteClip(clip.id)}
                    className="p-2 rounded-xl text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                    title="Delete Clip"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
            );
          })}
        </div>
      )}

      {/* Video Preview Modal */}
      {previewClip && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
          <div className="glass-panel rounded-3xl max-w-2xl w-full p-6 relative border border-white/[0.15] shadow-2xl">
            <button
              onClick={() => setPreviewClip(null)}
              className="absolute top-4 right-4 p-2 rounded-xl bg-white/[0.06] hover:bg-white/[0.1] text-slate-300"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex flex-col md:flex-row gap-6">
              {/* 9:16 Video Player */}
              <div className="w-full md:w-64 aspect-[9/16] bg-black rounded-2xl overflow-hidden shrink-0 border border-white/[0.1] flex items-center justify-center">
                {previewClip.rendered_path ? (
                  <video
                    src={`/storage/${previewClip.rendered_path}`}
                    controls
                    autoPlay
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-center p-4">
                    <Film className="w-8 h-8 text-purple-400 mx-auto mb-2 opacity-60" />
                    <p className="text-xs text-slate-400">Rendering preview clip...</p>
                  </div>
                )}
              </div>

              {/* Clip Details & Scoring Breakdown */}
              <div className="flex-1 space-y-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300">
                      {previewClip.category}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      Duration: {Math.round(previewClip.duration)}s
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white mt-1">{previewClip.title}</h3>
                  <p className="text-xs text-slate-300 italic mt-1">"{previewClip.hook}"</p>
                </div>

                {/* Viral Breakdown Bars */}
                <div className="space-y-2 bg-white/[0.03] p-4 rounded-xl border border-white/[0.06]">
                  <h5 className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                    <span>Viral Score Assessment</span>
                    <span className="text-amber-400 font-mono font-bold">{previewClip.viral_score.overall} / 100</span>
                  </h5>

                  <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 pt-1 font-mono">
                    <div>Hook Impact: <span className="text-white font-bold">{previewClip.viral_score.hook}</span></div>
                    <div>Engagement: <span className="text-white font-bold">{previewClip.viral_score.engagement}</span></div>
                    <div>Story Arc: <span className="text-white font-bold">{previewClip.viral_score.story_completeness}</span></div>
                    <div>Visual Quality: <span className="text-white font-bold">{previewClip.viral_score.visual_quality}</span></div>
                  </div>

                  <p className="text-[11px] text-slate-400 mt-2 italic leading-relaxed">
                    AI Notes: {previewClip.viral_score.explanation}
                  </p>
                </div>

                <div className="flex items-center space-x-3 pt-2">
                  <button
                    onClick={() => setPreviewClip(null)}
                    className="flex-1 py-2.5 rounded-xl bg-white/[0.08] hover:bg-white/[0.15] text-slate-300 text-xs font-semibold text-center transition-all"
                  >
                    Close Preview
                  </button>
                  <button
                    onClick={() => {
                      onSelectClip(previewClip);
                      setPreviewClip(null);
                      onNavigate('youtube-studio');
                    }}
                    className="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold text-center transition-all"
                  >
                    Publish to YouTube
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
