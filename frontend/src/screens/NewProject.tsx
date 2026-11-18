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
  RefreshCw,
  Scissors,
  RotateCcw,
  Radio
} from 'lucide-react';
import { GlassCard } from '../components/GlassCard';
import { CaptionStyleConfig, Project } from '../types';
import { ScreenId } from '../components/Sidebar';
import { CaptionStylePicker } from '../components/CaptionStylePicker';
import { api } from '../services/api';
import { secondsToHms, hmsToSeconds, clamp } from '../utils/time';

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

export interface VideoDetails {
  video_id: string;
  title: string;
  channel: string;
  thumbnail: string;
  duration: number;
  is_live: boolean;
  was_live: boolean;
  available_heights: number[];
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
  const [urlDetails, setUrlDetails] = useState<VideoDetails | null>(null);
  const [isFetchingDetails, setIsFetchingDetails] = useState(false);
  const [startTime, setStartTime] = useState<number>(0);
  const [endTime, setEndTime] = useState<number>(600);
  const [startText, setStartText] = useState<string>('00:00:00');
  const [endText, setEndText] = useState<string>('00:10:00');
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

  // Step 1: Fetch Video Details Only (NO download)
  const handleFetchDetails = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!urlInput.trim()) return;
    setErrorMsg(null);
    setIsFetchingDetails(true);

    try {
      const details = await api.getVideoInfo(urlInput.trim());
      setUrlDetails(details);

      // Auto-fill project name if not manually edited
      if (!nameUserEdited || !name.trim()) {
        setName(details.title || 'YouTube Clip Project');
      }

      // Configure default range selection
      const maxDur = details.duration > 0 ? details.duration : 1800;
      if (details.is_live) {
        // Live stream default: last 10 minutes
        const s = Math.max(0, maxDur - 600);
        const e = maxDur;
        setStartTime(s);
        setEndTime(e);
        setStartText(secondsToHms(s, true));
        setEndText(secondsToHms(e, true));
      } else {
        // Normal video or replay default: first 10 minutes (or full duration if shorter)
        const s = 0;
        const e = Math.min(maxDur, 600);
        setStartTime(s);
        setEndTime(e);
        setStartText(secondsToHms(s, true));
        setEndText(secondsToHms(e, true));
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch video details';
      setErrorMsg(msg);
      setUrlDetails(null);
    } finally {
      setIsFetchingDetails(false);
    }
  };

  const handleStartBlur = () => {
    const parsed = hmsToSeconds(startText);
    if (!isNaN(parsed) && parsed >= 0 && parsed < endTime) {
      const clamped = clamp(parsed, 0, Math.max(0, endTime - 1));
      setStartTime(clamped);
      setStartText(secondsToHms(clamped, true));
    } else {
      setStartText(secondsToHms(startTime, true));
    }
  };

  const handleEndBlur = () => {
    const parsed = hmsToSeconds(endText);
    const maxDur = urlDetails?.duration && urlDetails.duration > 0 ? urlDetails.duration : 1800;
    if (!isNaN(parsed) && parsed > startTime && parsed <= maxDur) {
      const clamped = clamp(parsed, startTime + 1, maxDur);
      setEndTime(clamped);
      setEndText(secondsToHms(clamped, true));
    } else {
      setEndText(secondsToHms(endTime, true));
    }
  };

  const nudgeStart = (delta: number) => {
    const newStart = clamp(startTime + delta, 0, Math.max(0, endTime - 1));
    setStartTime(newStart);
    setStartText(secondsToHms(newStart, true));
  };

  const nudgeEnd = (delta: number) => {
    const maxDur = urlDetails?.duration && urlDetails.duration > 0 ? urlDetails.duration : 1800;
    const newEnd = clamp(endTime + delta, startTime + 1, maxDur);
    setEndTime(newEnd);
    setEndText(secondsToHms(newEnd, true));
  };

  const handleRemoveVideo = () => {
    setVideoInfo(null);
    setUrlDetails(null);
    setUrlInput('');
    setErrorMsg(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Start Clipping handler (only ONE button at the bottom)
  const handleStartClipping = async () => {
    if (isSubmitting) return;

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      let targetVideoInfo = videoInfo;

      // If URL source with fetched details (range selected):
      if (!targetVideoInfo && urlDetails) {
        setIsProcessingSource(true);
        setSourceStatusText('Downloading selected video range via yt-dlp...');

        const res = await api.importVideoUrl(
          urlInput.trim(),
          liveMinutes,
          liveMode,
          startTime,
          endTime
        );

        targetVideoInfo = {
          video_path: res.video_path || res.filename,
          filename: res.filename || urlDetails.title,
          duration: res.duration || (endTime - startTime),
          width: res.width || 1920,
          height: res.height || 1080,
          fps: res.fps || 30,
          thumbnail_path: res.thumbnail_path || urlDetails.thumbnail,
          is_url: true,
        };
        setVideoInfo(targetVideoInfo);
      }

      if (!targetVideoInfo) {
        setErrorMsg('Please select or upload a video first.');
        setIsSubmitting(false);
        setIsProcessingSource(false);
        return;
      }

      const projectName = name.trim() || targetVideoInfo.filename.replace(/\.[^/.]+$/, '') || 'Untitled Project';
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

      await onLaunchProcessing(targetVideoInfo, config);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to start clipping project.';
      setErrorMsg(msg);
      setIsSubmitting(false);
      setIsProcessingSource(false);
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
              <div className="space-y-4 pt-2">
                {!urlDetails ? (
                  <form onSubmit={handleFetchDetails} className="space-y-4">
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">
                        Paste YouTube Video URL
                      </label>
                      <div className="flex flex-col sm:flex-row gap-3">
                        <input
                          type="url"
                          placeholder="https://www.youtube.com/watch?v=... or https://youtu.be/..."
                          value={urlInput}
                          onChange={(e) => setUrlInput(e.target.value)}
                          required
                          className="flex-1 px-4 py-3 rounded-xl glass-input text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-purple-500 focus:outline-none font-mono"
                        />
                        <button
                          type="submit"
                          disabled={isFetchingDetails || !urlInput.trim()}
                          className="px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 text-white text-xs font-bold transition-all disabled:opacity-50 flex items-center justify-center space-x-2 shrink-0 cursor-pointer shadow-lg shadow-purple-600/20"
                        >
                          {isFetchingDetails ? (
                            <>
                              <Loader2 className="w-4 h-4 animate-spin" />
                              <span>Fetching video details...</span>
                            </>
                          ) : (
                            <>
                              <Sparkles className="w-4 h-4" />
                              <span>Get Video</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>

                    {isFetchingDetails && (
                      <p className="text-xs text-purple-300 flex items-center space-x-2 animate-pulse font-mono">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Fetching video details (no download)...</span>
                      </p>
                    )}

                    <p className="text-[11px] text-slate-500 leading-relaxed">
                      * Enter any YouTube video, Short, or livestream link. Video details will be inspected instantly without downloading files.
                    </p>
                  </form>
                ) : (
                  /* Step 2: Details and Trim Card */
                  <div className="rounded-2xl p-5 border border-purple-500/40 bg-purple-950/20 space-y-5 animate-fade-in">
                    {/* Video Header / Metadata */}
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-white/[0.08] pb-4">
                      <div className="flex items-center space-x-4 min-w-0">
                        <div className="w-28 h-18 rounded-xl bg-black/80 border border-white/[0.1] overflow-hidden shrink-0 relative shadow-inner flex items-center justify-center">
                          {urlDetails.thumbnail ? (
                            <img
                              src={urlDetails.thumbnail}
                              alt={urlDetails.title}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <Film className="w-8 h-8 text-purple-400 opacity-80" />
                          )}
                          <span className="absolute bottom-1 right-1 text-[9px] bg-black/85 px-1.5 py-0.5 rounded text-white font-mono font-bold">
                            {urlDetails.duration > 0 ? secondsToHms(urlDetails.duration) : 'LIVE'}
                          </span>
                        </div>

                        <div className="min-w-0 space-y-1">
                          <div className="flex items-center gap-2">
                            {urlDetails.is_live ? (
                              <span className="px-2.5 py-0.5 rounded-full bg-red-500/20 border border-red-500/30 text-red-400 text-[10px] font-bold animate-pulse flex items-center gap-1.5 shrink-0">
                                <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                                LIVE
                              </span>
                            ) : urlDetails.was_live ? (
                              <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/30 text-amber-300 text-[10px] font-bold shrink-0">
                                Live replay
                              </span>
                            ) : (
                              <span className="px-2.5 py-0.5 rounded-full bg-purple-500/20 border border-purple-500/30 text-purple-300 text-[10px] font-medium shrink-0">
                                Video
                              </span>
                            )}
                            <h3 className="text-sm font-bold text-white truncate max-w-md" title={urlDetails.title}>
                              {urlDetails.title}
                            </h3>
                          </div>

                          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400 font-mono">
                            {urlDetails.channel && (
                              <>
                                <span className="text-slate-300">{urlDetails.channel}</span>
                                <span>•</span>
                              </>
                            )}
                            <span>Total Duration: {urlDetails.duration > 0 ? secondsToHms(urlDetails.duration) : 'Active Stream'}</span>
                          </div>
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={() => { setUrlDetails(null); setErrorMsg(null); }}
                        className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white/[0.06] hover:bg-white/[0.1] text-slate-300 border border-white/[0.1] text-xs font-medium transition-colors shrink-0 cursor-pointer"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        <span>Change Video</span>
                      </button>
                    </div>

                    {/* Which part do you want to clip? */}
                    <div className="space-y-4">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-purple-300 flex items-center gap-1.5">
                          <Scissors className="w-4 h-4 text-purple-400" />
                          Which part do you want to clip?
                        </h4>
                        <div className="text-xs text-slate-300 font-mono bg-purple-950/40 px-3 py-1 rounded-lg border border-purple-500/20">
                          Selected Length:{' '}
                          <span className="text-purple-300 font-bold">
                            {secondsToHms(Math.max(0, endTime - startTime))} ({Math.round(Math.max(0, endTime - startTime))}s)
                          </span>
                        </div>
                      </div>

                      {urlDetails.is_live && (
                        <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-200 text-xs flex items-center gap-2">
                          <Radio className="w-3.5 h-3.5 shrink-0 text-amber-400" />
                          <span>Live stream: you can clip only what has already been streamed.</span>
                        </div>
                      )}

                      {/* Dual Range Slider Controls */}
                      <div className="space-y-4 bg-black/40 p-4 rounded-xl border border-white/[0.06]">
                        {(() => {
                          const maxDuration = urlDetails.duration > 0 ? urlDetails.duration : 1800;
                          return (
                            <div className="space-y-2">
                              <div className="flex justify-between text-xs text-slate-400 font-mono">
                                <span>{secondsToHms(startTime, true)}</span>
                                <span className="text-purple-300 font-semibold">
                                  {secondsToHms(Math.max(0, endTime - startTime))} selected
                                </span>
                                <span>{secondsToHms(maxDuration, true)}</span>
                              </div>

                              <div className="relative h-6 flex items-center">
                                <div className="w-full h-2 rounded-full bg-slate-800" />
                                <div
                                  className="absolute h-2 rounded-full bg-gradient-to-r from-purple-500 to-indigo-500 shadow-[0_0_12px_rgba(168,85,247,0.5)] pointer-events-none"
                                  style={{
                                    left: `${(startTime / maxDuration) * 100}%`,
                                    width: `${Math.max(1, ((endTime - startTime) / maxDuration) * 100)}%`,
                                  }}
                                />
                                <input
                                  type="range"
                                  min={0}
                                  max={maxDuration}
                                  step={1}
                                  value={startTime}
                                  onChange={(e) => {
                                    const val = clamp(parseFloat(e.target.value), 0, Math.max(0, endTime - 1));
                                    setStartTime(val);
                                    setStartText(secondsToHms(val, true));
                                  }}
                                  className="absolute w-full accent-purple-400 cursor-pointer pointer-events-auto opacity-75 hover:opacity-100"
                                />
                                <input
                                  type="range"
                                  min={0}
                                  max={maxDuration}
                                  step={1}
                                  value={endTime}
                                  onChange={(e) => {
                                    const val = clamp(parseFloat(e.target.value), startTime + 1, maxDuration);
                                    setEndTime(val);
                                    setEndText(secondsToHms(val, true));
                                  }}
                                  className="absolute w-full accent-indigo-400 cursor-pointer pointer-events-auto opacity-75 hover:opacity-100"
                                />
                              </div>
                            </div>
                          );
                        })()}

                        {/* Start and End Boxes with Nudge Buttons */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                          {/* Start Time Box */}
                          <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-2">
                            <div className="flex items-center justify-between">
                              <label className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">
                                Start Time (HH:MM:SS)
                              </label>
                              <span className="text-[10px] text-slate-500 font-mono">Sec: {Math.round(startTime)}s</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <input
                                type="text"
                                value={startText}
                                onChange={(e) => setStartText(e.target.value)}
                                onBlur={handleStartBlur}
                                placeholder="00:00:00"
                                className="w-24 px-2.5 py-1.5 bg-black/60 border border-white/[0.12] rounded-lg text-xs font-mono text-center text-white focus:outline-none focus:border-purple-500"
                              />
                              <div className="flex items-center gap-1">
                                <button
                                  type="button"
                                  onClick={() => nudgeStart(-5)}
                                  className="px-2 py-1 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded text-[11px] font-mono transition-all"
                                >
                                  -5s
                                </button>
                                <button
                                  type="button"
                                  onClick={() => nudgeStart(-1)}
                                  className="px-2 py-1 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded text-[11px] font-mono transition-all"
                                >
                                  -1s
                                </button>
                                <button
                                  type="button"
                                  onClick={() => nudgeStart(1)}
                                  className="px-2 py-1 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded text-[11px] font-mono transition-all"
                                >
                                  +1s
                                </button>
                                <button
                                  type="button"
                                  onClick={() => nudgeStart(5)}
                                  className="px-2 py-1 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded text-[11px] font-mono transition-all"
                                >
                                  +5s
                                </button>
                              </div>
                            </div>
                          </div>

                          {/* End Time Box */}
                          <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-2">
                            <div className="flex items-center justify-between">
                              <label className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">
                                End Time (HH:MM:SS)
                              </label>
                              <span className="text-[10px] text-slate-500 font-mono">Sec: {Math.round(endTime)}s</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <input
                                type="text"
                                value={endText}
                                onChange={(e) => setEndText(e.target.value)}
                                onBlur={handleEndBlur}
                                placeholder="00:10:00"
                                className="w-24 px-2.5 py-1.5 bg-black/60 border border-white/[0.12] rounded-lg text-xs font-mono text-center text-white focus:outline-none focus:border-purple-500"
                              />
                              <div className="flex items-center gap-1">
                                <button
                                  type="button"
                                  onClick={() => nudgeEnd(-5)}
                                  className="px-2 py-1 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded text-[11px] font-mono transition-all"
                                >
                                  -5s
                                </button>
                                <button
                                  type="button"
                                  onClick={() => nudgeEnd(-1)}
                                  className="px-2 py-1 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded text-[11px] font-mono transition-all"
                                >
                                  -1s
                                </button>
                                <button
                                  type="button"
                                  onClick={() => nudgeEnd(1)}
                                  className="px-2 py-1 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded text-[11px] font-mono transition-all"
                                >
                                  +1s
                                </button>
                                <button
                                  type="button"
                                  onClick={() => nudgeEnd(5)}
                                  className="px-2 py-1 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded text-[11px] font-mono transition-all"
                                >
                                  +5s
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
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
          disabled={(!videoInfo && !urlDetails) || isSubmitting}
          className={`px-8 py-4 rounded-2xl font-bold text-sm flex items-center space-x-2.5 transition-all shadow-xl ${
            (!videoInfo && !urlDetails) || isSubmitting
              ? 'bg-slate-800/80 text-slate-500 cursor-not-allowed border border-white/[0.05]'
              : 'bg-gradient-to-r from-purple-600 via-indigo-600 to-purple-500 hover:from-purple-500 hover:to-indigo-500 text-white shadow-[0_0_25px_rgba(139,92,246,0.4)] hover:scale-[1.02] active:scale-[0.98]'
          }`}
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>{sourceStatusText || 'Starting Pipeline...'}</span>
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
        {!videoInfo && !urlDetails && (
          <p className="text-xs text-amber-400/90 flex items-center space-x-1.5 font-medium">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            <span>Select or paste a source video above to start clipping</span>
          </p>
        )}
      </div>
    </div>
  );
};
