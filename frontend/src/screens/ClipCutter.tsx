import React, { useState, useEffect, useRef } from 'react';
import { 
  Scissors, 
  Youtube, 
  Search, 
  Play, 
  Pause, 
  Download, 
  Sparkles, 
  Clock, 
  AlertCircle, 
  CheckCircle2, 
  Radio, 
  FileAudio, 
  Film, 
  Loader2, 
  ChevronRight, 
  RotateCcw,
  Volume2,
  Sliders,
  ExternalLink
} from 'lucide-react';
import { GlassCard } from '../components/GlassCard';
import { ClipInfo, ClipCutQuality, ClipCutResult } from '../types';
import { api } from '../services/api';
import { secondsToHms, hmsToSeconds, clamp } from '../utils/time';

interface YTPlayer {
  playVideo: () => void;
  pauseVideo: () => void;
  seekTo: (seconds: number, allowSeekAhead?: boolean) => void;
  getCurrentTime: () => number;
  getPlayerState: () => number;
  destroy: () => void;
}

interface YTPlayerOptions {
  videoId: string;
  playerVars?: {
    autoplay?: 0 | 1;
    controls?: 0 | 1;
    modestbranding?: 0 | 1;
    rel?: 0 | 1;
    origin?: string;
  };
  events?: {
    onReady?: (event: { target: YTPlayer }) => void;
    onStateChange?: (event: { data: number; target: YTPlayer }) => void;
  };
}

interface YTNamespace {
  Player: new (elementId: string | HTMLElement, options: YTPlayerOptions) => YTPlayer;
  PlayerState: {
    ENDED: number;
    PLAYING: number;
    PAUSED: number;
    BUFFERING: number;
    CUED: number;
  };
}

declare global {
  interface Window {
    onYouTubeIframeAPIReady?: () => void;
    YT?: YTNamespace;
  }
}

interface ClipCutterProps {
  onUseInProject: (clipResult: ClipCutResult) => void;
}

export const ClipCutterScreen: React.FC<ClipCutterProps> = ({ onUseInProject }) => {
  const [urlInput, setUrlInput] = useState('');
  const [isLoadingInfo, setIsLoadingInfo] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Video Info State
  const [clipInfo, setClipInfo] = useState<ClipInfo | null>(null);

  // Range and Player State
  const [startTime, setStartTime] = useState<number>(0);
  const [endTime, setEndTime] = useState<number>(60);
  const [startInputText, setStartInputText] = useState('00:00');
  const [endInputText, setEndInputText] = useState('01:00');
  const [selectedQuality, setSelectedQuality] = useState<ClipCutQuality>('1080');

  // Player controls
  const playerRef = useRef<YTPlayer | null>(null);
  const [isPlayerReady, setIsPlayerReady] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentPlaybackTime, setCurrentPlaybackTime] = useState<number>(0);
  const [isPreviewingCut, setIsPreviewingCut] = useState(false);

  // Cutting Action State
  const [isCutting, setIsCutting] = useState(false);
  const [cutResult, setCutResult] = useState<ClipCutResult | null>(null);

  // Load YouTube IFrame API script on mount if not loaded
  useEffect(() => {
    if (!window.YT) {
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      const firstScriptTag = document.getElementsByTagName('script')[0];
      firstScriptTag?.parentNode?.insertBefore(tag, firstScriptTag);
    }
  }, []);

  // Initialize YT Player when video info is available
  useEffect(() => {
    if (!clipInfo?.video_id) return;

    let isSubscribed = true;

    const createPlayer = () => {
      if (!isSubscribed) return;
      if (playerRef.current) {
        try {
          playerRef.current.destroy();
        } catch (e) {
          // ignore cleanup error
        }
      }

      try {
        const player = new window.YT!.Player('yt-player-container', {
          videoId: clipInfo.video_id,
          playerVars: {
            autoplay: 0,
            controls: 1,
            modestbranding: 1,
            rel: 0,
          },
          events: {
            onReady: (event) => {
              if (isSubscribed) {
                playerRef.current = event.target;
                setIsPlayerReady(true);
              }
            },
            onStateChange: (event) => {
              if (isSubscribed && window.YT) {
                setIsPlaying(event.data === window.YT.PlayerState.PLAYING);
              }
            },
          },
        });
      } catch (err) {
        console.error('Failed to create YouTube Player', err);
      }
    };

    if (window.YT && window.YT.Player) {
      createPlayer();
    } else {
      window.onYouTubeIframeAPIReady = () => {
        createPlayer();
      };
    }

    return () => {
      isSubscribed = false;
      if (playerRef.current) {
        try {
          playerRef.current.destroy();
        } catch (e) {
          // ignore
        }
        playerRef.current = null;
      }
      setIsPlayerReady(false);
      setIsPlaying(false);
    };
  }, [clipInfo?.video_id]);

  // Monitor playback during cut preview
  useEffect(() => {
    let timer: number | null = null;
    if (isPlaying) {
      timer = window.setInterval(() => {
        if (playerRef.current) {
          try {
            const curr = playerRef.current.getCurrentTime();
            setCurrentPlaybackTime(curr);
            if (isPreviewingCut && curr >= endTime) {
              playerRef.current.pauseVideo();
              setIsPreviewingCut(false);
              setIsPlaying(false);
            }
          } catch (e) {
            // ignore
          }
        }
      }, 250);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isPlaying, isPreviewingCut, endTime]);

  // Effective duration bounds
  const maxVideoDuration = clipInfo?.duration && clipInfo.duration > 0 ? clipInfo.duration : 1800;
  const clipDuration = Math.max(0, endTime - startTime);
  const isOverDurationLimit = clipDuration > 600;

  // Handle URL Inspection
  const handleInspectUrl = async () => {
    if (!urlInput.trim()) return;
    setErrorMsg(null);
    setCutResult(null);
    setIsLoadingInfo(true);

    try {
      const data = await api.getClipInfo(urlInput.trim());
      setClipInfo(data);

      const maxDur = data.duration > 0 ? data.duration : 1800;
      const initialEnd = Math.min(maxDur, 60);
      setStartTime(0);
      setEndTime(initialEnd);
      setStartInputText(secondsToHms(0));
      setEndInputText(secondsToHms(initialEnd));

      // Choose best initial quality
      if (data.available_heights.includes(1080)) {
        setSelectedQuality('1080');
      } else if (data.available_heights.includes(720)) {
        setSelectedQuality('720');
      } else if (data.available_heights.length > 0) {
        const highest = Math.max(...data.available_heights);
        setSelectedQuality(String(highest) as ClipCutQuality);
      } else {
        setSelectedQuality('720');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to inspect YouTube URL';
      setErrorMsg(msg);
      setClipInfo(null);
    } finally {
      setIsLoadingInfo(false);
    }
  };

  // Sync range helpers
  const updateStart = (val: number) => {
    const clamped = clamp(val, 0, Math.max(0, endTime - 0.5));
    setStartTime(clamped);
    setStartInputText(secondsToHms(clamped));
  };

  const updateEnd = (val: number) => {
    const clamped = clamp(val, startTime + 0.5, maxVideoDuration);
    setEndTime(clamped);
    setEndInputText(secondsToHms(clamped));
  };

  const handleStartInputChange = (text: string) => {
    setStartInputText(text);
    const secs = hmsToSeconds(text);
    if (!isNaN(secs)) {
      setStartTime(clamp(secs, 0, Math.max(0, endTime - 0.5)));
    }
  };

  const handleEndInputChange = (text: string) => {
    setEndInputText(text);
    const secs = hmsToSeconds(text);
    if (!isNaN(secs)) {
      setEndTime(clamp(secs, startTime + 0.5, maxVideoDuration));
    }
  };

  const nudgeStart = (delta: number) => {
    updateStart(startTime + delta);
  };

  const nudgeEnd = (delta: number) => {
    updateEnd(endTime + delta);
  };

  const setStartFromPlayer = () => {
    if (playerRef.current) {
      try {
        const curr = playerRef.current.getCurrentTime();
        updateStart(curr);
      } catch (e) {
        // ignore
      }
    }
  };

  const setEndFromPlayer = () => {
    if (playerRef.current) {
      try {
        const curr = playerRef.current.getCurrentTime();
        updateEnd(curr);
      } catch (e) {
        // ignore
      }
    }
  };

  const applyQuickDuration = (seconds: number) => {
    updateEnd(startTime + seconds);
  };

  const previewCutRange = () => {
    if (playerRef.current) {
      try {
        playerRef.current.seekTo(startTime, true);
        playerRef.current.playVideo();
        setIsPreviewingCut(true);
        setIsPlaying(true);
      } catch (e) {
        // ignore
      }
    }
  };

  // Execute Cutting
  const handleExecuteCut = async () => {
    if (!clipInfo) return;
    if (endTime <= startTime) {
      setErrorMsg('End time must be after start time.');
      return;
    }
    if (isOverDurationLimit) {
      setErrorMsg('Clip cannot exceed 10 minutes (600 seconds).');
      return;
    }

    setErrorMsg(null);
    setIsCutting(true);

    try {
      const res = await api.createClip({
        url: urlInput.trim(),
        start: startTime,
        end: endTime,
        quality: selectedQuality,
      });
      setCutResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Clip cutting failed';
      setErrorMsg(msg);
    } finally {
      setIsCutting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Top Banner / Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/[0.08] pb-6">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-purple-500/20 border border-purple-500/30 text-purple-400">
              <Scissors className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
                Clip Cutter
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-medium">
                  100% Free • No API Keys
                </span>
              </h1>
              <p className="text-sm text-slate-400 mt-1">
                Precision frame-accurate YouTube video and livestream segment trimmer powered by yt-dlp & FFmpeg.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* URL Input Bar */}
      <GlassCard className="p-6">
        <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
          Paste YouTube URL (Video, Short, or Livestream)
        </label>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Youtube className="w-5 h-5 text-red-400" />
            </div>
            <input
              type="text"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleInspectUrl()}
              placeholder="https://www.youtube.com/watch?v=... or https://youtu.be/... or livestream link"
              className="w-full pl-11 pr-4 py-3 bg-black/40 border border-white/[0.1] rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 transition-all font-mono"
            />
          </div>
          <button
            onClick={handleInspectUrl}
            disabled={isLoadingInfo || !urlInput.trim()}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-500 disabled:bg-purple-900/40 disabled:text-slate-500 text-white font-medium text-sm rounded-xl transition-all shadow-lg shadow-purple-600/20 flex items-center justify-center space-x-2 shrink-0 cursor-pointer"
          >
            {isLoadingInfo ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Inspecting Video...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Load Video</span>
              </>
            )}
          </button>
        </div>

        {errorMsg && (
          <div className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-sm flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 shrink-0 text-red-400" />
            <span>{errorMsg}</span>
          </div>
        )}
      </GlassCard>

      {/* Main Studio Area */}
      {clipInfo && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Player & Video Info (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <GlassCard className="p-4 overflow-hidden">
              {/* YouTube Player Container */}
              <div className="relative w-full aspect-video rounded-xl overflow-hidden bg-black/80 border border-white/[0.08] shadow-inner">
                <div id="yt-player-container" className="w-full h-full" />
              </div>

              {/* Video Title and Metadata Badges */}
              <div className="mt-4 space-y-2">
                <div className="flex items-start justify-between gap-3">
                  <h2 className="text-base font-semibold text-slate-100 line-clamp-2">
                    {clipInfo.title}
                  </h2>
                  {clipInfo.is_live ? (
                    <span className="shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/20 border border-red-500/30 text-red-400 text-xs font-semibold animate-pulse">
                      <span className="w-2 h-2 rounded-full bg-red-500" />
                      LIVE STREAM
                    </span>
                  ) : clipInfo.was_live ? (
                    <span className="shrink-0 px-2.5 py-1 rounded-full bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-semibold">
                      Live Replay
                    </span>
                  ) : (
                    <span className="shrink-0 px-2.5 py-1 rounded-full bg-purple-500/20 border border-purple-500/30 text-purple-300 text-xs font-medium">
                      Standard Video
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                  {clipInfo.channel && (
                    <span className="font-medium text-slate-300">{clipInfo.channel}</span>
                  )}
                  {clipInfo.duration > 0 && (
                    <span className="flex items-center gap-1 font-mono">
                      <Clock className="w-3.5 h-3.5" />
                      Full Length: {secondsToHms(clipInfo.duration)}
                    </span>
                  )}
                  {currentPlaybackTime > 0 && (
                    <span className="text-purple-400 font-mono">
                      Player: {secondsToHms(currentPlaybackTime)}
                    </span>
                  )}
                </div>

                {clipInfo.note && (
                  <div className="mt-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-200 text-xs flex items-center gap-2">
                    <Radio className="w-4 h-4 shrink-0 text-amber-400" />
                    <span>{clipInfo.note}</span>
                  </div>
                )}
              </div>
            </GlassCard>

            {/* Range Preview Player Controls */}
            <GlassCard className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={previewCutRange}
                    className="px-4 py-2 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 text-purple-300 rounded-xl text-xs font-medium flex items-center space-x-2 transition-all cursor-pointer"
                  >
                    <Play className="w-3.5 h-3.5 fill-purple-400" />
                    <span>Preview Cut Selection ({secondsToHms(startTime)} → {secondsToHms(endTime)})</span>
                  </button>
                </div>
                <div className="text-xs text-slate-400 font-mono">
                  Length: <span className={isOverDurationLimit ? 'text-red-400 font-bold' : 'text-purple-300 font-bold'}>{secondsToHms(clipDuration)}</span>
                  <span className="text-slate-500"> / max 10:00</span>
                </div>
              </div>
            </GlassCard>
          </div>

          {/* Right Column: Trimmer Controls, Quality & Actions (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <GlassCard className="p-6 space-y-6">
              <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
                <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-purple-400" />
                  Cut Configuration
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  {secondsToHms(clipDuration)} selected
                </span>
              </div>

              {/* Start Timestamp Control */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-300 uppercase tracking-wider">Start Time</span>
                  <button
                    onClick={setStartFromPlayer}
                    className="text-purple-400 hover:text-purple-300 text-[11px] flex items-center gap-1 cursor-pointer"
                    title="Set start to current YouTube player time"
                  >
                    <Clock className="w-3 h-3" />
                    <span>Set to Current Player Time</span>
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={startInputText}
                    onChange={(e) => handleStartInputChange(e.target.value)}
                    placeholder="00:00:00"
                    className="w-28 px-3 py-2 bg-black/40 border border-white/[0.1] rounded-xl text-sm font-mono text-center text-white focus:outline-none focus:border-purple-500"
                  />
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => nudgeStart(-5)}
                      className="px-2 py-1.5 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded-lg text-xs font-mono transition-all"
                    >
                      -5s
                    </button>
                    <button
                      onClick={() => nudgeStart(-1)}
                      className="px-2 py-1.5 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded-lg text-xs font-mono transition-all"
                    >
                      -1s
                    </button>
                    <button
                      onClick={() => nudgeStart(1)}
                      className="px-2 py-1.5 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded-lg text-xs font-mono transition-all"
                    >
                      +1s
                    </button>
                    <button
                      onClick={() => nudgeStart(5)}
                      className="px-2 py-1.5 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded-lg text-xs font-mono transition-all"
                    >
                      +5s
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={0}
                  max={maxVideoDuration}
                  step={0.5}
                  value={startTime}
                  onChange={(e) => updateStart(parseFloat(e.target.value))}
                  className="w-full accent-purple-500 cursor-pointer"
                />
              </div>

              {/* End Timestamp Control */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-300 uppercase tracking-wider">End Time</span>
                  <button
                    onClick={setEndFromPlayer}
                    className="text-purple-400 hover:text-purple-300 text-[11px] flex items-center gap-1 cursor-pointer"
                    title="Set end to current YouTube player time"
                  >
                    <Clock className="w-3 h-3" />
                    <span>Set to Current Player Time</span>
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={endInputText}
                    onChange={(e) => handleEndInputChange(e.target.value)}
                    placeholder="00:00:00"
                    className="w-28 px-3 py-2 bg-black/40 border border-white/[0.1] rounded-xl text-sm font-mono text-center text-white focus:outline-none focus:border-purple-500"
                  />
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => nudgeEnd(-5)}
                      className="px-2 py-1.5 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded-lg text-xs font-mono transition-all"
                    >
                      -5s
                    </button>
                    <button
                      onClick={() => nudgeEnd(-1)}
                      className="px-2 py-1.5 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded-lg text-xs font-mono transition-all"
                    >
                      -1s
                    </button>
                    <button
                      onClick={() => nudgeEnd(1)}
                      className="px-2 py-1.5 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded-lg text-xs font-mono transition-all"
                    >
                      +1s
                    </button>
                    <button
                      onClick={() => nudgeEnd(5)}
                      className="px-2 py-1.5 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 rounded-lg text-xs font-mono transition-all"
                    >
                      +5s
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={0}
                  max={maxVideoDuration}
                  step={0.5}
                  value={endTime}
                  onChange={(e) => updateEnd(parseFloat(e.target.value))}
                  className="w-full accent-purple-500 cursor-pointer"
                />
              </div>

              {/* Quick Length Presets */}
              <div className="space-y-1.5">
                <span className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Quick Duration from Start:</span>
                <div className="flex flex-wrap gap-1.5">
                  {[15, 30, 60, 90, 180, 300].map((dur) => (
                    <button
                      key={dur}
                      onClick={() => applyQuickDuration(dur)}
                      className="px-2.5 py-1 bg-white/[0.04] hover:bg-purple-600/20 hover:border-purple-500/30 border border-white/[0.08] text-slate-300 rounded-lg text-xs font-mono transition-all cursor-pointer"
                    >
                      +{dur >= 60 ? `${dur / 60}m` : `${dur}s`}
                    </button>
                  ))}
                </div>
              </div>

              {/* Quality Selector */}
              <div className="space-y-2 border-t border-white/[0.08] pt-4">
                <span className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Target Resolution & Format
                </span>
                <div className="grid grid-cols-3 gap-2">
                  {(['1080', '720', '480', '360', '240', '144'] as ClipCutQuality[]).map((q) => {
                    const isAvailable = clipInfo.available_heights.includes(parseInt(q, 10));
                    const isSelected = selectedQuality === q;
                    return (
                      <button
                        key={q}
                        onClick={() => setSelectedQuality(q)}
                        className={`py-2 px-3 rounded-xl text-xs font-mono font-medium border transition-all cursor-pointer flex items-center justify-center gap-1 ${
                          isSelected
                            ? 'bg-purple-600 border-purple-500 text-white shadow-md shadow-purple-600/30'
                            : isAvailable
                            ? 'bg-white/[0.03] border-white/[0.08] text-slate-300 hover:bg-white/[0.08]'
                            : 'bg-white/[0.01] border-white/[0.04] text-slate-500'
                        }`}
                      >
                        <Film className="w-3.5 h-3.5" />
                        <span>{q}p</span>
                      </button>
                    );
                  })}
                  <button
                    onClick={() => setSelectedQuality('audio')}
                    className={`col-span-3 py-2 px-3 rounded-xl text-xs font-mono font-medium border transition-all cursor-pointer flex items-center justify-center gap-2 ${
                      selectedQuality === 'audio'
                        ? 'bg-purple-600 border-purple-500 text-white shadow-md shadow-purple-600/30'
                        : 'bg-white/[0.03] border-white/[0.08] text-slate-300 hover:bg-white/[0.08]'
                    }`}
                  >
                    <FileAudio className="w-3.5 h-3.5" />
                    <span>Extract Audio Only (M4A)</span>
                  </button>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-2">
                <button
                  onClick={handleExecuteCut}
                  disabled={isCutting || isOverDurationLimit || endTime <= startTime}
                  className="w-full py-3.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:from-purple-950 disabled:to-indigo-950 disabled:text-slate-500 text-white font-semibold text-sm rounded-xl transition-all shadow-xl shadow-purple-600/25 flex items-center justify-center space-x-2 cursor-pointer"
                >
                  {isCutting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Cutting Segment via yt-dlp & FFmpeg...</span>
                    </>
                  ) : (
                    <>
                      <Scissors className="w-4 h-4" />
                      <span>Cut & Extract ({secondsToHms(clipDuration)})</span>
                    </>
                  )}
                </button>
                {isOverDurationLimit && (
                  <p className="text-red-400 text-xs text-center mt-2">
                    Clip exceeds 10 minutes (600s). Please shorten selection.
                  </p>
                )}
              </div>
            </GlassCard>

            {/* Cut Result Card */}
            {cutResult && (
              <GlassCard className="p-6 border-emerald-500/30 bg-emerald-950/10 space-y-4">
                <div className="flex items-center space-x-2 text-emerald-400">
                  <CheckCircle2 className="w-5 h-5 shrink-0" />
                  <h4 className="font-semibold text-sm">Clip Successfully Extracted!</h4>
                </div>

                <div className="bg-black/40 rounded-xl p-3 border border-white/[0.08] space-y-1.5 text-xs">
                  <div className="flex justify-between text-slate-400">
                    <span>Filename:</span>
                    <span className="font-mono text-slate-200 truncate max-w-[200px]" title={cutResult.filename}>
                      {cutResult.filename}
                    </span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Duration:</span>
                    <span className="font-mono text-slate-200">{cutResult.duration.toFixed(1)}s</span>
                  </div>
                  {cutResult.width > 0 && (
                    <div className="flex justify-between text-slate-400">
                      <span>Dimensions:</span>
                      <span className="font-mono text-slate-200">{cutResult.width} × {cutResult.height}</span>
                    </div>
                  )}
                </div>

                <div className="flex flex-col sm:flex-row gap-2 pt-1">
                  <a
                    href={cutResult.download_url}
                    download={cutResult.filename}
                    className="flex-1 py-2.5 px-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all shadow-md shadow-emerald-600/20"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download File</span>
                  </a>
                  <button
                    onClick={() => onUseInProject(cutResult)}
                    className="flex-1 py-2.5 px-3 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all shadow-md shadow-purple-600/20 cursor-pointer"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Use in New Project</span>
                  </button>
                </div>
              </GlassCard>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
