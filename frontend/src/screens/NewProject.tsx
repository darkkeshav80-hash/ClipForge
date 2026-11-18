import React, { useState, useRef, useEffect } from 'react';
import { 
  PlusCircle, 
  Sparkles, 
  Layers, 
  Check, 
  ArrowRight, 
  UploadCloud, 
  FileVideo, 
  Link as LinkIcon, 
  AlertCircle, 
  CheckCircle2, 
  Film, 
  Loader2, 
  Smartphone, 
  Clock, 
  Trash2,
  RefreshCw
} from 'lucide-react';
import { GlassCard } from '../components/GlassCard';
import { CaptionStyleConfig, Project } from '../types';
import { ScreenId } from '../components/Sidebar';
import { CaptionStylePicker } from '../components/CaptionStylePicker';
import { api } from '../services/api';

export interface PreProcessingConfig {
  name: string;
  aspectRatio: '9:16' | '16:9' | '1:1';
  clipsCount: number;
  captionPreset: string;
  minDuration: number;
  maxDuration: number;
  minViralScore: number;
  silenceRemoval: boolean;
  faceTracking: boolean;
  smartZoom: boolean;
}

export interface VideoInfo {
  video_path: string;
  filename: string;
  duration: number;
  width: number;
  height: number;
  fps: number;
  size?: number;
  thumbnail_path?: string;
  is_url?: boolean;
}

interface NewProjectProps {
  presets: CaptionStyleConfig[];
  onLaunchProcessing: (videoData: any, config: PreProcessingConfig) => Promise<void> | void;
  onNavigate: (screen: ScreenId) => void;
  initialVideoInfo?: VideoInfo | null;
}

function formatFileSize(bytes?: number): string {
  if (!bytes || bytes <= 0) return '';
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export const NewProjectScreen: React.FC<NewProjectProps> = ({
  presets,
  onLaunchProcessing,
  onNavigate,
  initialVideoInfo,
}) => {
  // Source Video States
  const [tab, setTab] = useState<'upload' | 'url'>('upload');
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isProcessingSource, setIsProcessingSource] = useState(false);
  const [sourceStatusText, setSourceStatusText] = useState('Analyzing media...');
  const [urlInput, setUrlInput] = useState('');
  const [liveMinutes, setLiveMinutes] = useState<number>(10);
  const [liveMode, setLiveMode] = useState<'last' | 'next'>('last');
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(initialVideoInfo || null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sync initialVideoInfo if passed externally (e.g. from Clip Cutter)
  useEffect(() => {
    if (initialVideoInfo) {
      setVideoInfo(initialVideoInfo);
      if (!nameUserEdited || !name.trim()) {
        const cleanName = initialVideoInfo.filename.replace(/\.[^/.]+$/, '').trim();
        setName(cleanName || 'Untitled Project');
      }
    }
  }, [initialVideoInfo]);

  // Pipeline Settings States
  const [name, setName] = useState('');
  const [nameUserEdited, setNameUserEdited] = useState(false);
  const [aspectRatio, setAspectRatio] = useState<'9:16' | '16:9' | '1:1'>('9:16');
  const [minViralScore, setMinViralScore] = useState<number>(70);
  const [clipsCount, setClipsCount] = useState<number>(5);
  const [minDuration, setMinDuration] = useState<number>(15);
  const [maxDuration, setMaxDuration] = useState<number>(60);
  const [selectedPreset, setSelectedPreset] = useState<string>(() => {
    return localStorage.getItem('clipforge_selected_caption_style') || 'mrbeast';
  });
  const [silenceRemoval, setSilenceRemoval] = useState<boolean>(true);
  const [faceTracking, setFaceTracking] = useState<boolean>(true);
  const [smartZoom, setSmartZoom] = useState<boolean>(true);

  // Submission / Double-click prevention state
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Handle local file selection
  const handleFile = async (file: File) => {
    setErrorMsg(null);
    const validExtensions = ['.mp4', '.mov', '.mkv', '.webm'];
    const hasValidExt = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    if (!hasValidExt) {
      setErrorMsg(`Unsupported file type: ${file.name}. Please upload an MP4, MOV, MKV, or WEBM video.`);
      return;
    }

    try {
      setIsProcessingSource(true);
      setSourceStatusText(`Uploading ${file.name}...`);
      setUploadProgress(0);

      const res = await api.uploadVideo(file, (percent) => {
        setUploadProgress(percent);
      });

      const readyData: VideoInfo = {
        video_path: res.path,
        filename: res.filename || file.name,
        duration: res.duration || 0,
        width: res.width || 1920,
        height: res.height || 1080,
        fps: res.fps || 30,
        size: file.size,
        thumbnail_path: res.thumbnail_path,
        is_url: false,
      };

      setVideoInfo(readyData);

      // Auto-fill project name from video filename if not manually edited
      if (!nameUserEdited || !name.trim()) {
        const cleanName = readyData.filename.replace(/\.[^/.]+$/, '').trim();
        setName(cleanName || 'Untitled Project');
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Video upload failed. Please try another file.');
    } finally {
      setIsProcessingSource(false);
      setUploadProgress(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  // Handle URL import via yt-dlp
  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;
    setErrorMsg(null);
    setIsProcessingSource(true);
    setSourceStatusText('Downloading video & analyzing streams via yt-dlp...');

    try {
      const res = await api.importVideoUrl(urlInput.trim(), liveMinutes, liveMode) as any;
      const readyData: VideoInfo = {
        video_path: res.video_path || res.path,
        filename: res.filename || res.title || 'Imported Video',
        duration: res.duration || 120,
        width: res.width || 1920,
        height: res.height || 1080,
        fps: res.fps || 30,
        thumbnail_path: res.thumbnail_path || res.thumbnail_url,
        is_url: true,
      };

      setVideoInfo(readyData);

      // Auto-fill project name from URL video title
      if (!nameUserEdited || !name.trim()) {
        setName(readyData.filename);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to download video from URL. Make sure the link is public and accessible.');
    } finally {
      setIsProcessingSource(false);
    }
  };

  const handleRemoveVideo = () => {
    setVideoInfo(null);
    setUrlInput('');
    setErrorMsg(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Start Clipping handler (only ONE button at the bottom)
  const handleStartClipping = async () => {
    if (!videoInfo || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const projectName = name.trim() || videoInfo.filename.replace(/\.[^/.]+$/, '') || 'Untitled Project';
      const config: PreProcessingConfig = {
        name: projectName,
        aspectRatio,
        clipsCount,
        captionPreset: selectedPreset,
        minDuration,
        maxDuration,
        minViralScore,
        silenceRemoval,
        faceTracking,
        smartZoom,
      };

      await onLaunchProcessing(videoInfo, config);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to start clipping project.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in pb-16">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center space-x-2.5">
          <PlusCircle className="w-6 h-6 text-purple-400" />
          <span>New Clipping Project</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Import a source video, configure AI virality thresholds and caption aesthetics, then launch clipping in one step.
        </p>
      </div>

      {/* Global Error Banner */}
      {errorMsg && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center space-x-3 text-rose-300 text-xs animate-shake">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span className="flex-1">{errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="text-rose-400 hover:text-white text-xs underline">
            Dismiss
          </button>
        </div>
      )}

      {/* 1. SOURCE VIDEO SECTION (AT THE TOP) */}
      <GlassCard title="1. Select Source Video (PC Upload or Online URL)">
        {!videoInfo ? (
          <div className="space-y-4">
            {/* Tabs */}
            <div className="flex space-x-3 border-b border-white/[0.08] pb-3">
              <button
                type="button"
                onClick={() => setTab('upload')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  tab === 'upload'
                    ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30 shadow-[0_0_12px_rgba(168,85,247,0.2)]'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <FileVideo className="w-4 h-4" />
                <span>Upload From PC</span>
              </button>
              <button
                type="button"
                onClick={() => setTab('url')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  tab === 'url'
                    ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30 shadow-[0_0_12px_rgba(168,85,247,0.2)]'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <LinkIcon className="w-4 h-4" />
                <span>Import via URL (YouTube / Web)</span>
              </button>
            </div>

            {/* Tab: Upload From PC */}
            {tab === 'upload' && (
              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-3xl p-10 text-center cursor-pointer transition-all duration-300 ${
                  isDragging
                    ? 'border-purple-500 bg-purple-500/10 scale-[1.01]'
                    : 'border-white/[0.12] hover:border-purple-500/50 hover:bg-white/[0.02]'
                }`}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={(e) => e.target.files && handleFile(e.target.files[0])}
                  accept=".mp4,.mov,.mkv,.webm"
                  className="hidden"
                />

                <div className="max-w-md mx-auto space-y-4">
                  <div className="w-16 h-16 rounded-3xl bg-purple-600/20 text-purple-400 flex items-center justify-center mx-auto border border-purple-500/30">
                    <UploadCloud className="w-8 h-8" />
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-white">Drag & drop source video here</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Supports MP4, MOV, MKV, or WEBM up to 4K resolution.
                    </p>
                  </div>

                  <button
                    type="button"
                    className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-lg shadow-purple-600/30 transition-all"
                  >
                    Browse Files on Computer
                  </button>
                </div>

                {uploadProgress !== null && (
                  <div className="mt-6 max-w-sm mx-auto space-y-2">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Uploading video...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="bg-purple-500 h-full rounded-full transition-all duration-200"
                        style={{ width: `${uploadProgress}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Tab: Import via URL */}
            {tab === 'url' && (
              <form onSubmit={handleUrlSubmit} className="space-y-4 pt-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">
                    Paste Online Video URL
                  </label>
                  <div className="flex flex-col sm:flex-row gap-3">
                    <input
                      type="url"
                      placeholder="https://www.youtube.com/watch?v=..."
                      value={urlInput}
                      onChange={(e) => setUrlInput(e.target.value)}
                      required
                      className="flex-1 px-4 py-3 rounded-xl glass-input text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                    <button
                      type="submit"
                      disabled={isProcessingSource}
                      className="px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 text-white text-xs font-bold transition-all disabled:opacity-50 flex items-center justify-center space-x-2 shrink-0"
                    >
                      {isProcessingSource ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Downloading Video...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4" />
                          <span>Download & Import</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Livestream DVR Capture Window Options */}
                <div className="p-3.5 rounded-2xl bg-purple-950/20 border border-purple-500/20 text-xs text-slate-300 space-y-2.5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="flex items-center space-x-2 font-medium text-purple-200">
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
                      </span>
                      <span>Livestream DVR Capture:</span>
                    </span>
                    <div className="flex items-center space-x-1.5">
                      <span className="text-[11px] text-slate-400 mr-1">Duration:</span>
                      {[5, 10, 15, 20].map((mins) => (
                        <button
                          key={mins}
                          type="button"
                          onClick={() => setLiveMinutes(mins)}
                          className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                            liveMinutes === mins
                              ? 'bg-purple-600 text-white shadow-[0_0_10px_rgba(168,85,247,0.3)]'
                              : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'
                          }`}
                        >
                          {mins}m
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-400 border-t border-white/[0.06] pt-2 gap-2">
                    <span>If the link is an active livestream, capture instantly from DVR:</span>
                    <div className="flex items-center space-x-1.5">
                      <button
                        type="button"
                        onClick={() => setLiveMode('last')}
                        className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition-all ${
                          liveMode === 'last'
                            ? 'bg-purple-500/30 text-purple-200 border border-purple-500/40'
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        Past {liveMinutes}m (DVR)
                      </button>
                      <button
                        type="button"
                        onClick={() => setLiveMode('next')}
                        className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition-all ${
                          liveMode === 'next'
                            ? 'bg-purple-500/30 text-purple-200 border border-purple-500/40'
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        Next {liveMinutes}m
                      </button>
                    </div>
                  </div>
                </div>

                {isProcessingSource && (
                  <p className="text-xs text-purple-300 flex items-center space-x-2 animate-pulse font-mono">
                    <span>⏳</span>
                    <span>{sourceStatusText}</span>
                  </p>
                )}

                <p className="text-[11px] text-slate-500 leading-relaxed">
                  * Supports YouTube, Twitter/X, Twitch, and web MP4 streams. Video is downloaded locally into your storage folder for offline AI slicing.
                </p>
              </form>
            )}
          </div>
        ) : (
          /* CHOSEN VIDEO CARD: Shows filename, duration, resolution, size/FPS, thumbnail, and Change/Remove button */
          <div className="rounded-2xl p-5 border border-purple-500/40 bg-purple-950/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-fade-in">
            <div className="flex items-center space-x-4 min-w-0">
              <div className="w-24 h-16 rounded-xl bg-black/70 border border-white/[0.1] overflow-hidden shrink-0 flex items-center justify-center relative">
                {videoInfo.thumbnail_path ? (
                  <img
                    src={videoInfo.thumbnail_path.startsWith('http') ? videoInfo.thumbnail_path : `/storage/${videoInfo.thumbnail_path}`}
                    alt="Source thumbnail"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <Film className="w-8 h-8 text-purple-400 opacity-80" />
                )}
                <span className="absolute bottom-1 right-1 text-[9px] bg-black/80 px-1.5 py-0.5 rounded text-white font-mono font-bold">
                  {formatDuration(videoInfo.duration)}
                </span>
              </div>

              <div className="min-w-0 space-y-1">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <h3 className="text-sm font-bold text-white truncate max-w-md" title={videoInfo.filename}>
                    {videoInfo.filename}
                  </h3>
                </div>

                <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400 font-mono">
                  <span className="bg-white/[0.06] px-2 py-0.5 rounded text-slate-300">
                    {videoInfo.width}x{videoInfo.height}
                  </span>
                  <span>•</span>
                  <span className="bg-white/[0.06] px-2 py-0.5 rounded text-slate-300">
                    {formatDuration(videoInfo.duration)}
                  </span>
                  {videoInfo.size ? (
                    <>
                      <span>•</span>
                      <span className="bg-white/[0.06] px-2 py-0.5 rounded text-slate-300">
                        {formatFileSize(videoInfo.size)}
                      </span>
                    </>
                  ) : null}
                  <span>•</span>
                  <span className="bg-white/[0.06] px-2 py-0.5 rounded text-slate-300">
                    {Math.round(videoInfo.fps || 30)} FPS
                  </span>
                  <span>•</span>
                  <span className="text-emerald-400 font-semibold">Video Ready</span>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={handleRemoveVideo}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white/[0.06] hover:bg-rose-500/20 text-slate-300 hover:text-rose-300 border border-white/[0.1] text-xs font-medium transition-colors shrink-0"
              title="Change or remove selected video"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Change Video</span>
            </button>
          </div>
        )}
      </GlassCard>

      {/* 2. PROJECT IDENTITY (Auto-filled from video, editable) */}
      <GlassCard title="2. Project Identity">
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">
            Project Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              setNameUserEdited(true);
            }}
            placeholder={videoInfo ? videoInfo.filename : "e.g. Podcast Highlights Ep 42"}
            className="w-full px-4 py-3 rounded-xl glass-input text-sm text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
          />
          <p className="text-[11px] text-slate-500 mt-1">
            Auto-populated from the video filename or URL title. You can customize this anytime.
          </p>
        </div>
      </GlassCard>

      {/* 3. ASPECT RATIO & FRAMING TARGET */}
      <GlassCard title="3. Aspect Ratio & Framing Target">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { id: '9:16' as const, title: '9:16 Vertical (Shorts/Reels)', desc: 'Optimized for TikTok, YouTube Shorts & IG Reels with intelligent face centering' },
            { id: '16:9' as const, title: '16:9 Landscape', desc: 'Standard widescreen format with auto-zooms for longform highlights' },
            { id: '1:1' as const, title: '1:1 Square', desc: 'Square feed layout with centered video and large top/bottom captions' },
          ].map((ratio) => (
            <div
              key={ratio.id}
              onClick={() => setAspectRatio(ratio.id)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                aspectRatio === ratio.id
                  ? 'bg-purple-600/20 border-purple-500/50 shadow-[0_0_15px_rgba(139,92,246,0.2)]'
                  : 'bg-white/[0.03] border-white/[0.08] hover:bg-white/[0.06]'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm font-bold text-white">{ratio.id}</span>
                {aspectRatio === ratio.id && <Check className="w-4 h-4 text-purple-400" />}
              </div>
              <h4 className="text-xs font-semibold text-slate-200 mt-2">{ratio.title}</h4>
              <p className="text-[11px] text-slate-400 mt-1">{ratio.desc}</p>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* 4. AI DISCOVERY & VIRALITY THRESHOLDS */}
      <GlassCard title="4. AI Discovery & Virality Thresholds">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
                Minimum Viral Score Threshold
              </label>
              <span className="font-mono text-xs font-bold text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                {minViralScore} / 100
              </span>
            </div>
            <input
              type="range"
              min="50"
              max="95"
              value={minViralScore}
              onChange={(e) => setMinViralScore(Number(e.target.value))}
              className="w-full accent-purple-500"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Only segments scoring above this virality threshold will be rendered.
            </p>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
                Target Clips to Extract
              </label>
              <span className="font-mono text-xs font-bold text-purple-300 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
                {clipsCount} clips
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              value={clipsCount}
              onChange={(e) => setClipsCount(Number(e.target.value))}
              className="w-full accent-purple-500"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Maximum number of viral candidate shorts to generate from this video.
            </p>
          </div>
        </div>
      </GlassCard>

      {/* 5. DURATION CONSTRAINTS & PROCESSING OPTIONS */}
      <GlassCard title="5. Duration Limits & Autonomous Editing">
        <div className="space-y-6">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2 flex items-center space-x-1.5">
              <Clock className="w-3.5 h-3.5 text-purple-400" />
              <span>Clip Duration Constraints (Seconds)</span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <span className="text-[10px] text-slate-400">Min Duration (s)</span>
                <input
                  type="number"
                  value={minDuration}
                  onChange={(e) => setMinDuration(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg glass-input text-xs font-mono"
                  min="10"
                  max="60"
                />
              </div>
              <div>
                <span className="text-[10px] text-slate-400">Max Duration (s)</span>
                <input
                  type="number"
                  value={maxDuration}
                  onChange={(e) => setMaxDuration(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg glass-input text-xs font-mono"
                  min="20"
                  max="180"
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-white/[0.06]">
            <label className="flex items-center space-x-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] cursor-pointer hover:bg-white/[0.04]">
              <input
                type="checkbox"
                checked={silenceRemoval}
                onChange={(e) => setSilenceRemoval(e.target.checked)}
                className="rounded bg-slate-800 border-white/20 text-purple-600 focus:ring-purple-500"
              />
              <span className="text-xs text-slate-300 font-medium">Silence Removal</span>
            </label>

            <label className="flex items-center space-x-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] cursor-pointer hover:bg-white/[0.04]">
              <input
                type="checkbox"
                checked={faceTracking}
                onChange={(e) => setFaceTracking(e.target.checked)}
                className="rounded bg-slate-800 border-white/20 text-purple-600 focus:ring-purple-500"
              />
              <span className="text-xs text-slate-300 font-medium">Face Centering</span>
            </label>

            <label className="flex items-center space-x-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] cursor-pointer hover:bg-white/[0.04]">
              <input
                type="checkbox"
                checked={smartZoom}
                onChange={(e) => setSmartZoom(e.target.checked)}
                className="rounded bg-slate-800 border-white/20 text-purple-600 focus:ring-purple-500"
              />
              <span className="text-xs text-slate-300 font-medium">Dynamic Zooms</span>
            </label>
          </div>
        </div>
      </GlassCard>

      {/* 6. CAPTION STYLE PICKER BEFORE RENDERING */}
      <GlassCard title="6. Autonomous Caption Styling (CapCut Presets)">
        <CaptionStylePicker
          presets={presets}
          selectedPresetId={selectedPreset}
          onSelectPreset={(id) => setSelectedPreset(id)}
        />
      </GlassCard>

      {/* 7. ONLY ONE BUTTON TO START PROCESSING AT THE BOTTOM */}
      <div className="pt-4 flex flex-col items-end space-y-2">
        <button
          type="button"
          onClick={handleStartClipping}
          disabled={!videoInfo || isSubmitting}
          className={`px-8 py-4 rounded-2xl font-bold text-sm flex items-center space-x-2.5 transition-all shadow-xl ${
            !videoInfo || isSubmitting
              ? 'bg-slate-800/80 text-slate-500 cursor-not-allowed border border-white/[0.05]'
              : 'bg-gradient-to-r from-purple-600 via-indigo-600 to-purple-500 hover:from-purple-500 hover:to-indigo-500 text-white shadow-[0_0_25px_rgba(139,92,246,0.4)] hover:scale-[1.02] active:scale-[0.98]'
          }`}
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Starting Pipeline...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              <span>Start Clipping</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>

        {/* Disabled Reason / Explanation */}
        {!videoInfo && (
          <p className="text-xs text-amber-400/90 flex items-center space-x-1.5 font-medium">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            <span>Select or upload a source video above to start clipping</span>
          </p>
        )}
      </div>
    </div>
  );
};
