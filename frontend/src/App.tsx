import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, ScreenId } from './components/Sidebar';
import { DashboardScreen } from './screens/Dashboard';
import { NewProjectScreen, VideoInfo } from './screens/NewProject';
import { ClipCutterScreen } from './screens/ClipCutter';
import { AIProcessingScreen } from './screens/AIProcessing';
import { GeneratedClipsGalleryScreen } from './screens/GeneratedClipsGallery';
import { AIModelManagerScreen } from './screens/AIModelManager';
import { APIProviderSettingsScreen } from './screens/APIProviderSettings';
import { YouTubeStudioScreen } from './screens/YouTubeStudio';
import { AnalyticsScreen } from './screens/Analytics';
import { AutomationSettingsScreen } from './screens/AutomationSettings';
import { SystemSettingsScreen } from './screens/SystemSettings';

import { 
  Project, 
  Clip, 
  CaptionStyleConfig, 
  AIProvider, 
  TaskModelAssignment, 
  HardwareProfileConfig, 
  AutomationSettings, 
  YouTubeStudioStatus, 
  DashboardMetrics, 
  ProcessingLog, 
  PipelineStage,
  ClipCutResult 
} from './types';
import { api } from './services/api';
import { wsClient } from './services/websocket';

import { INITIAL_PRESETS } from './types/presets';

export const App: React.FC = () => {
  const [activeScreen, setActiveScreen] = useState<ScreenId>('dashboard');
  const [isLowPerf, setIsLowPerf] = useState<boolean>(false);
  const [automationRunning, setAutomationRunning] = useState<boolean>(false);

  // Core Data States
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    total_videos_processed: 8,
    total_clips_generated: 24,
    published_shorts: 12,
    failed_jobs: 0,
    average_clip_score: 87,
    storage_usage_mb: 4200,
    storage_total_gb: 512,
    queue_length: 0,
    ai_status: 'online',
    hardware_profile: 'BALANCED',
  });

  const [projects, setProjects] = useState<Project[]>([]);
  const [clips, setClips] = useState<Clip[]>([]);
  const [prefilledVideoInfo, setPrefilledVideoInfo] = useState<VideoInfo | null>(null);

  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [currentClip, setCurrentClip] = useState<Clip | null>(null);
  const [presets, setPresets] = useState<CaptionStyleConfig[]>(INITIAL_PRESETS);
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [assignments, setAssignments] = useState<TaskModelAssignment[]>([]);

  const [hardware, setHardware] = useState<HardwareProfileConfig>({
    profile: 'BALANCED',
    max_ram_usage_gb: 12,
    ffmpeg_threads: 4,
    analysis_resolution: '480p',
    whisper_model: 'base',
    enable_gpu: false,
    max_concurrent_jobs: 1,
  });

  const [automationSettings, setAutomationSettings] = useState<AutomationSettings>({
    auto_start: false,
    clips_per_video: 5,
    min_viral_score: 70,
    min_duration: 15,
    max_duration: 60,
    target_aspect_ratio: '9:16',
    default_caption_preset: 'mrbeast-bold',
    output_resolution: '1080p',
    language: 'en',
    auto_generate_metadata: true,
    auto_quality_review: true,
    auto_publish_youtube: false,
    daily_upload_limit: 3,
    publishing_schedule: 'immediate',
  });

  const [youtubeStatus, setYouTubeStatus] = useState<YouTubeStudioStatus>({
    connected: false,
    channel_id: '',
    channel_title: '',
    subscriber_count: 0,
    video_count: 0,
    quota_used: 0,
    quota_limit: 10000,
    auth_mode: 'oauth',
  });

  // Telemetry & Logs (Live clean state)
  const [currentStage, setCurrentStage] = useState<PipelineStage>('idle');
  const [stageProgress, setStageProgress] = useState<number>(0);
  const [totalProgress, setTotalProgress] = useState<number>(0);
  const [logs, setLogs] = useState<ProcessingLog[]>([]);

  // Load from API on mount
  useEffect(() => {
    async function loadInitial() {
      try {
        const [dashMetrics, projList, clipList, presetList, provList, taskList, autoSet, ytStat] = await Promise.all([
          api.getDashboardMetrics().catch(() => null),
          api.getProjects().catch(() => null),
          api.getClips().catch(() => null),
          api.getCaptionPresets().catch(() => null),
          api.getProviders().catch(() => null),
          api.getTaskAssignments().catch(() => null),
          api.getAutomationSettings().catch(() => null),
          api.getYouTubeStatus().catch(() => null),
        ]);

        if (dashMetrics) setMetrics(dashMetrics);
        if (projList && projList.length > 0) setProjects(projList);
        if (clipList && clipList.length > 0) {
          setClips(clipList);
          setCurrentClip(clipList[0]);
        }
        if (presetList && presetList.length > 0) setPresets(presetList);
        if (provList && provList.length > 0) setProviders(provList);
        if (taskList && taskList.length > 0) setAssignments(taskList);
        if (autoSet) setAutomationSettings(autoSet);
        if (ytStat) setYouTubeStatus(ytStat);
      } catch (e) {
        console.warn('Backend loading: using initial state', e);
      }
    }
    loadInitial();

    // Subscribe to live WebSocket pipeline events
    const unsubscribe = wsClient.subscribe((event: any) => {
      if (event.log) {
        setLogs((prev) => [...prev, event.log!]);
      }
      if (event.type === 'control') {
        if (event.action === 'stop') {
          setAutomationRunning(false);
          setCurrentStage('idle');
          setTotalProgress(0);
          setStageProgress(0);
        } else if (event.action === 'pause') {
          setAutomationRunning(false);
          setCurrentStage('paused');
        } else if (event.action === 'resume' || event.action === 'start') {
          setAutomationRunning(true);
        }
      }
      const stg = event.stage || event.status;
      if (stg) {
        setCurrentStage(stg as PipelineStage);
        if (stg === 'completed') {
          setAutomationRunning(false);
          setTotalProgress(100);
          setStageProgress(100);
          api.getProjects().then((p) => p && setProjects(p)).catch(() => {});
          api.getClips().then((c) => c && setClips(c)).catch(() => {});
        } else if (stg === 'error') {
          setAutomationRunning(false);
        } else if (stg !== 'idle' && stg !== 'paused') {
          setAutomationRunning(true);
        }
      }
      const rawProg = typeof event.progress === 'number' ? event.progress : event.total_progress;
      if (typeof rawProg === 'number') {
        setTotalProgress(Math.round(rawProg));
      }
      if (typeof event.stage_progress === 'number') {
        setStageProgress(Math.round(event.stage_progress));
      } else if (typeof rawProg === 'number') {
        setStageProgress(Math.min(100, Math.round((rawProg % 12) * 8 + 10)));
      }
      if (event.type === 'clip_ready') {
        api.getClips().then((cl) => {
          if (cl) setClips(cl);
        }).catch(() => {});
      }
    });

    // Fallback polling interval every 2.5s to keep UI perfectly synchronized with DB
    const pollInterval = setInterval(async () => {
      try {
        const projs = await api.getProjects();
        if (projs && projs.length > 0) {
          setProjects(projs);
          const activeProj = projs.find((p) => p.status && !['completed', 'error', 'idle'].includes(p.status));
          if (activeProj) {
            setCurrentStage(activeProj.status as PipelineStage);
            setTotalProgress(Math.round(activeProj.total_progress || 0));
            setStageProgress(Math.round(activeProj.stage_progress || 0));
            setAutomationRunning(true);
            setCurrentProject((prev) => prev ? { ...prev, ...activeProj } : activeProj);
          }
        }
      } catch (err) {
        // silent polling failure
      }
    }, 2500);

    return () => {
      unsubscribe();
      clearInterval(pollInterval);
    };
  }, []);

  const handleStartAutomation = async () => {
    setAutomationRunning(true);
    try {
      await api.controlAutomation('start', currentProject?.id);
    } catch (e) {
      console.error(e);
    }
  };

  const handlePauseAutomation = async () => {
    setAutomationRunning(false);
    try {
      await api.controlAutomation('pause', currentProject?.id);
    } catch (e) {
      console.error(e);
    }
  };

  const handleControlAction = async (action: 'start' | 'pause' | 'resume' | 'stop') => {
    if (action === 'start' || action === 'resume') {
      setAutomationRunning(true);
      if (action === 'start') {
        setCurrentStage('importing');
        setTotalProgress(5);
        setStageProgress(10);
      }
    } else if (action === 'pause') {
      setAutomationRunning(false);
      setCurrentStage('paused');
    } else if (action === 'stop') {
      setAutomationRunning(false);
      setCurrentStage('idle');
      setTotalProgress(0);
      setStageProgress(0);
      setLogs((prev) => [
        ...prev,
        {
          id: `stop-${Date.now()}`,
          timestamp: new Date().toISOString(),
          level: 'warn',
          stage: 'idle',
          message: 'Pipeline execution stopped by user.',
        }
      ]);
    }

    try {
      await api.controlAutomation(action, currentProject?.id);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteClip = async (id: string) => {
    try {
      await api.deleteClip(id);
      setClips((prev) => prev.filter((c) => c.id !== id));
      if (currentClip?.id === id) {
        setCurrentClip(null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleLaunchProcessing = async (videoData: any, config?: any) => {
    try {
      const projId = currentProject?.id || `proj-${Date.now()}`;
      let minD = config?.minDuration ?? 15;
      let maxD = config?.maxDuration ?? 60;

      // Update backend automation parameters if user customized them
      if (config) {
        if (config.durationRange === '15-30') {
          minD = 15; maxD = 30;
        } else if (config.durationRange === '30-60') {
          minD = 30; maxD = 60;
        }

        try {
          await api.saveAutomationSettings({
            ...automationSettings,
            clips_per_video: Number(config.clipsCount) || 3,
            target_aspect_ratio: config.aspectRatio || '9:16',
            default_caption_preset: config.captionPreset || 'mrbeast',
            min_viral_score: Number(config.minViralScore) || 70,
            min_duration: minD,
            max_duration: maxD,
          });
        } catch (e) {
          console.warn('Failed to save pre-processing parameters:', e);
        }
      }

      const projectPayload = {
        id: projId,
        name: config?.name || videoData.filename || currentProject?.name || 'Uploaded Video',
        source_video_path: videoData.video_path || videoData.path || currentProject?.source_video_path || '',
        thumbnail_path: videoData.thumbnail_path || currentProject?.thumbnail_path || '',
        duration: videoData.duration || currentProject?.duration || 0,
        width: videoData.width || currentProject?.width || 1920,
        height: videoData.height || currentProject?.height || 1080,
        fps: videoData.fps || currentProject?.fps || 30,
        caption_preset: config?.captionPreset || currentProject?.caption_preset || localStorage.getItem('clipforge_selected_caption_style') || 'mrbeast',
        aspect_ratio: config?.aspectRatio || currentProject?.aspect_ratio || '9:16',
        target_clips: config?.clipsCount || 3,
        min_viral_score: config?.minViralScore || 70,
        min_duration: minD,
        max_duration: maxD,
        status: 'importing' as PipelineStage,
      };

      const savedProj = await api.createProject(projectPayload);
      setCurrentProject(savedProj);
      setProjects((prev) => [savedProj, ...prev.filter((p) => p.id !== savedProj.id)]);
      setAutomationRunning(true);
      setCurrentStage('importing');
      setTotalProgress(5);
      setStageProgress(10);
      setLogs([
        {
          id: `start-${Date.now()}`,
          timestamp: new Date().toISOString(),
          level: 'info',
          stage: 'importing',
          message: `Starting ClipForge automated clipping factory for ${savedProj.name} (${config?.clipsCount || 3} clips, ${config?.aspectRatio || '9:16'}, ${config?.captionPreset || 'mrbeast-bold'})...`,
        }
      ]);

      // 2. Switch to processing view
      setActiveScreen('processing');

      // 3. Trigger backend automation worker
      await api.controlAutomation('start', savedProj.id);
    } catch (err: any) {
      console.error('Failed to launch processing:', err);
    }
  };

  const handleUseClipInProject = (clipResult: ClipCutResult) => {
    setPrefilledVideoInfo({
      video_path: clipResult.path,
      filename: clipResult.filename,
      duration: clipResult.duration,
      width: clipResult.width,
      height: clipResult.height,
      fps: clipResult.fps,
      thumbnail_path: clipResult.thumbnail_path,
      is_url: false,
    });
    setActiveScreen('new-project');
  };

  return (
    <div className={`min-h-screen bg-[#080B14] text-slate-100 flex flex-col ${isLowPerf ? 'low-perf' : ''}`}>
      {/* Top Glass Navbar */}
      <Navbar
        hardwareProfile={hardware.profile}
        isLowPerf={isLowPerf}
        onToggleLowPerf={() => setIsLowPerf(!isLowPerf)}
        automationRunning={automationRunning}
        onStartAutomation={handleStartAutomation}
        onPauseAutomation={handlePauseAutomation}
        activeScreen={activeScreen}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Navigation */}
        <Sidebar
          currentScreen={activeScreen}
          onNavigate={(screen) => setActiveScreen(screen)}
          clipsCount={clips.length}
          queueCount={projects.filter((p) => p.status !== 'completed' && p.status !== 'error').length}
        />

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          {activeScreen === 'dashboard' && (
            <DashboardScreen
              metrics={metrics}
              projects={projects}
              clips={clips}
              onNavigate={(s) => setActiveScreen(s)}
              onSelectProject={(p) => setCurrentProject(p)}
              onSelectClip={(c) => setCurrentClip(c)}
            />
          )}

          {activeScreen === 'clip-cutter' && (
            <ClipCutterScreen
              onUseInProject={handleUseClipInProject}
            />
          )}

          {activeScreen === 'new-project' && (
            <NewProjectScreen
              presets={presets}
              onLaunchProcessing={handleLaunchProcessing}
              onNavigate={(s) => setActiveScreen(s)}
              initialVideoInfo={prefilledVideoInfo}
            />
          )}

          {activeScreen === 'processing' && (
            <AIProcessingScreen
              currentProject={currentProject}
              currentStage={currentStage}
              stageProgress={stageProgress}
              totalProgress={totalProgress}
              logs={logs}
              onControlAction={handleControlAction}
              onNavigate={(s) => setActiveScreen(s)}
              onClearLogs={() => setLogs([])}
            />
          )}

          {activeScreen === 'clips-gallery' && (
            <GeneratedClipsGalleryScreen
              clips={clips}
              onSelectClip={(c) => setCurrentClip(c)}
              onDeleteClip={handleDeleteClip}
              onNavigate={(s) => setActiveScreen(s)}
            />
          )}

          {activeScreen === 'ai-models' && (
            <AIModelManagerScreen
              providers={providers}
              assignments={assignments}
              onUpdateAssignments={(a) => setAssignments(a)}
            />
          )}

          {activeScreen === 'api-providers' && (
            <APIProviderSettingsScreen
              providers={providers}
              onUpdateProvider={(p) => {
                setProviders((prev) => prev.map((pr) => pr.id === p.id ? p : pr));
              }}
            />
          )}

          {activeScreen === 'youtube-studio' && (
            <YouTubeStudioScreen
              status={youtubeStatus}
              clips={clips}
              onRefreshStatus={() => api.getYouTubeStatus().then(setYouTubeStatus)}
            />
          )}

          {activeScreen === 'analytics' && (
            <AnalyticsScreen
              metrics={metrics}
              clips={clips}
            />
          )}

          {activeScreen === 'automation' && (
            <AutomationSettingsScreen
              settings={automationSettings}
              presets={presets}
              isRunning={automationRunning}
              onUpdateSettings={(s) => setAutomationSettings(s)}
              onControlAction={handleControlAction}
            />
          )}

          {activeScreen === 'system-settings' && (
            <SystemSettingsScreen
              hardware={hardware}
              isLowPerf={isLowPerf}
              onToggleLowPerf={() => setIsLowPerf(!isLowPerf)}
              onUpdateHardware={(h) => setHardware(h)}
            />
          )}
        </main>
      </div>
    </div>
  );
};
