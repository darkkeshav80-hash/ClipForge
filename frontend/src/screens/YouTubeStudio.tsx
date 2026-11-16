import React, { useState } from 'react';
import { 
  Youtube, 
  Sparkles, 
  UploadCloud, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  ExternalLink, 
  ShieldCheck, 
  Sliders, 
  Calendar,
  Lock,
  Globe,
  Eye
} from 'lucide-react';
import { GlassCard } from '../components/GlassCard';
import { Clip, YouTubeStudioStatus } from '../types';
import { api } from '../services/api';

interface YouTubeStudioProps {
  status: YouTubeStudioStatus;
  clips: Clip[];
  onRefreshStatus?: () => void;
}

export const YouTubeStudioScreen: React.FC<YouTubeStudioProps> = ({
  status,
  clips,
  onRefreshStatus,
}) => {
  const [publishingMode, setPublishingMode] = useState<'review' | 'full_auto' | 'scheduled'>('review');
  const [selectedClipId, setSelectedClipId] = useState<string>(clips[0]?.id || '');
  const [title, setTitle] = useState<string>(clips[0]?.title || 'Viral AI Insight that Changes Everything #shorts');
  const [description, setDescription] = useState<string>(
    "Generated automatically with ClipForge AI. Discover more insights! \n\n#shorts #podcast #viral #clipforge"
  );
  const [tags, setTags] = useState<string>('shorts, podcast, insights, motivation, clips');
  const [privacy, setPrivacy] = useState<'public' | 'unlisted' | 'private'>('public');
  const [scheduleTime, setScheduleTime] = useState<string>('');
  const [isPublishing, setIsPublishing] = useState<boolean>(false);
  const [publishResult, setPublishResult] = useState<{ success: boolean; msg: string; url?: string } | null>(null);

  const handlePublish = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClipId) return;

    setIsPublishing(true);
    setPublishResult(null);

    try {
      const tagList = tags.split(',').map((t) => t.trim()).filter(Boolean);
      const res = await api.publishToYouTube(selectedClipId, {
        title,
        description,
        tags: tagList,
        privacy,
        schedule_time: scheduleTime || undefined,
      });

      setPublishResult({
        success: res.success,
        msg: res.message || 'Short successfully uploaded to your YouTube channel!',
        url: res.url,
      });
      if (onRefreshStatus) onRefreshStatus();
    } catch (err: any) {
      setPublishResult({
        success: false,
        msg: err.message || 'Failed to upload video to YouTube.',
      });
    } finally {
      setIsPublishing(false);
    }
  };

  const handleSelectClip = (clipId: string) => {
    setSelectedClipId(clipId);
    const found = clips.find((c) => c.id === clipId);
    if (found) {
      setTitle(`${found.title} #shorts`);
      setDescription(`${found.hook}\n\nGenerated with ClipForge AI.\n\n#shorts #${found.category.replace(/\s+/g, '')}`);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2.5">
            <Youtube className="w-6 h-6 text-red-500" />
            <span>YouTube Shorts Studio</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Direct YouTube Data API v3 publishing. Schedule, title, and push high-retention Shorts to your verified channel.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <span className={`text-xs font-mono px-3 py-1.5 rounded-xl border flex items-center space-x-2 ${
            status.connected
              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
              : 'bg-amber-500/10 text-amber-300 border-amber-500/20'
          }`}>
            <span className={`w-2 h-2 rounded-full ${status.connected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`}></span>
            <span>{status.connected ? `Connected: ${status.channel_title || 'Channel'}` : 'OAuth Not Linked'}</span>
          </span>
        </div>
      </div>

      {/* Quota & Channel Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <GlassCard title="Connected Channel" icon={<Youtube className="w-4 h-4 text-red-500" />}>
          <div className="space-y-2">
            <h4 className="text-sm font-bold text-white">{status.channel_title || 'Demo Channel (Ready)'}</h4>
            <div className="flex items-center space-x-4 text-xs text-slate-400 font-mono">
              <span>{status.subscriber_count || 1240} Subs</span>
              <span>•</span>
              <span>{status.video_count || 48} Shorts</span>
            </div>
            <p className="text-[10px] text-slate-500 mt-2 font-mono">
              API Mode: {status.auth_mode || 'OAuth 2.0 Client'}
            </p>
          </div>
        </GlassCard>

        <GlassCard title="Daily API Quota Tracker" icon={<Clock className="w-4 h-4 text-sky-400" />}>
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-400">Used Today</span>
              <span className="text-sky-300 font-bold">{status.quota_used || 1600} / {status.quota_limit || 10000}</span>
            </div>
            <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full bg-sky-400 rounded-full"
                style={{ width: `${((status.quota_used || 1600) / (status.quota_limit || 10000)) * 100}%` }}
              ></div>
            </div>
            <p className="text-[10px] text-slate-500">Each video upload consumes ~1,600 YouTube API units.</p>
          </div>
        </GlassCard>

        <GlassCard title="Automation Dispatch Mode" icon={<Sliders className="w-4 h-4 text-purple-400" />}>
          <div className="space-y-2">
            <div className="grid grid-cols-3 gap-1">
              {(['review', 'full_auto', 'scheduled'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setPublishingMode(mode)}
                  className={`py-1 px-1.5 rounded-lg text-[10px] font-bold uppercase transition-all ${
                    publishingMode === mode
                      ? 'bg-purple-600/30 text-purple-200 border border-purple-500/50'
                      : 'bg-white/[0.04] text-slate-400'
                  }`}
                >
                  {mode.replace('_', ' ')}
                </button>
              ))}
            </div>
            <p className="text-[10px] text-slate-400">
              {publishingMode === 'review' ? 'Manual review & 1-click confirmation before uploading.' :
               publishingMode === 'full_auto' ? 'Immediately publish any clip scoring >= viral threshold.' :
               'Queue and drip feed clips at optimal audience peak times.'}
            </p>
          </div>
        </GlassCard>
      </div>

      {/* Manual Upload Form */}
      <GlassCard title="Publish Short with AI Metadata Generator">
        <form onSubmit={handlePublish} className="space-y-5">
          {/* Clip Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">
              Select Rendered Clip
            </label>
            <select
              value={selectedClipId}
              onChange={(e) => handleSelectClip(e.target.value)}
              className="w-full px-4 py-3 rounded-xl glass-input text-xs font-medium"
            >
              {clips.length === 0 ? (
                <option value="">No clips available - render a clip first</option>
              ) : (
                clips.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title} (Score: {c.viral_score.overall} | {Math.round(c.duration)}s)
                  </option>
                ))
              )}
            </select>
          </div>

          {/* Title */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">
              YouTube Short Title (Max 100 chars, includes #shorts)
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={100}
              required
              className="w-full px-4 py-3 rounded-xl glass-input text-xs font-medium"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">
              Description & Pinned Comments
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full p-3 rounded-xl glass-input text-xs font-medium"
            />
          </div>

          {/* Tags & Privacy */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">
                Tags (Comma separated)
              </label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="w-full px-4 py-3 rounded-xl glass-input text-xs font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">
                Visibility Status
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'public', label: 'Public', icon: Globe },
                  { id: 'unlisted', label: 'Unlisted', icon: Eye },
                  { id: 'private', label: 'Private', icon: Lock },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setPrivacy(item.id as any)}
                    className={`py-2.5 px-3 rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all ${
                      privacy === item.id
                        ? 'bg-purple-600/30 text-purple-200 border border-purple-500/50'
                        : 'bg-white/[0.04] text-slate-400'
                    }`}
                  >
                    <item.icon className="w-3.5 h-3.5" />
                    <span>{item.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Submit */}
          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={isPublishing || clips.length === 0}
              className="flex items-center space-x-2 px-6 py-3 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 text-white font-semibold text-xs shadow-[0_0_20px_rgba(239,68,68,0.4)] hover:from-red-500 transition-all disabled:opacity-50"
            >
              <UploadCloud className="w-4 h-4" />
              <span>{isPublishing ? 'Uploading to YouTube...' : 'Authorize & Upload Short'}</span>
            </button>
          </div>

          {publishResult && (
            <div className={`p-4 rounded-xl text-xs font-mono flex items-center justify-between ${
              publishResult.success ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30' : 'bg-rose-500/10 text-rose-300 border border-rose-500/30'
            }`}>
              <div className="flex items-center space-x-2">
                {publishResult.success ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
                <span>{publishResult.msg}</span>
              </div>
              {publishResult.url && (
                <a
                  href={publishResult.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center space-x-1 underline text-sky-400 hover:text-sky-300 font-semibold"
                >
                  <span>View on YouTube</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </div>
          )}
        </form>
      </GlassCard>
    </div>
  );
};
