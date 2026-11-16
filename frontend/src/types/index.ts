export type PipelineStage = 
  | 'idle'
  | 'importing'
  | 'transcribing'
  | 'analyzing'
  | 'selecting'
  | 'editing'
  | 'captioning'
  | 'rendering'
  | 'reviewing'
  | 'publishing'
  | 'completed'
  | 'error'
  | 'paused';

export interface Project {
  id: string;
  name: string;
  description?: string;
  source_video_path?: string;
  source_url?: string;
  thumbnail_path?: string;
  duration: number;
  width: number;
  height: number;
  fps: number;
  caption_preset?: string;
  aspect_ratio?: '9:16' | '16:9' | '1:1';
  status: PipelineStage;
  stage_progress: number;
  total_progress: number;
  clips_count: number;
  created_at: string;
  updated_at: string;
}

export interface ViralScoreBreakdown {
  overall: number; // 0-100
  hook: number;
  engagement: number;
  emotional_impact: number;
  story_completeness: number;
  information_value: number;
  audio_clarity: number;
  visual_quality: number;
  ending_quality: number;
  explanation: string;
}

export interface EditingDecisionPlan {
  clip_id: string;
  start_time: number;
  end_time: number;
  duration: number;
  hook_text: string;
  important_sentences: string[];
  unnecessary_pauses: [number, number][];
  silence_removal: boolean;
  zooms: { timestamp: number; type: 'zoom_in' | 'zoom_out'; scale: number }[];
  caption_preset: string;
  caption_placement: 'bottom' | 'top';
  target_aspect_ratio: '9:16' | '16:9' | '1:1';
  face_tracking: boolean;
  speaker_tracking: boolean;
  crop_center_x?: number; // 0.0 - 1.0
  audio_enhanced: boolean;
  recommended_resolution: '1080p' | '720p' | '480p';
}

export interface Clip {
  id: string;
  project_id: string;
  title: string;
  description: string;
  start_time: number;
  end_time: number;
  duration: number;
  transcript: string;
  hook: string;
  category: string;
  viral_score: ViralScoreBreakdown;
  editing_plan: EditingDecisionPlan;
  rendered_path?: string;
  thumbnail_path?: string;
  caption_preset: string;
  aspect_ratio: '9:16' | '16:9' | '1:1';
  status: 'draft' | 'rendering' | 'ready' | 'reviewed' | 'published' | 'failed';
  review_verdict?: {
    approved: boolean;
    issues: string[];
    feedback: string;
  };
  youtube_published?: boolean;
  youtube_video_id?: string;
  youtube_url?: string;
  created_at: string;
}

export interface CaptionStyleConfig {
  preset_id: string;
  name: string;
  description: string;
  category: 'social' | 'podcast' | 'gaming' | 'cinematic' | 'animated' | 'minimal';
  font_family: string;
  font_size: number;
  font_weight: string;
  text_color: string;
  highlight_color: string;
  outline_color: string;
  outline_width: number;
  shadow_color: string;
  shadow_blur: number;
  background_color: string;
  border_radius: number;
  position: 'bottom' | 'top';
  words_per_line: number;
  animation_style: 
    | 'none'
    | 'word_bounce'
    | 'karaoke_glow'
    | 'typewriter'
    | 'pop_up'
    | 'gradient_sweep'
    | 'rgb_pulse'
    | 'shake';
  animation_speed: number;
  all_caps: boolean;
  emoji_enabled: boolean;
  line_spacing: number;
  is_recommended?: boolean;
}

export interface AIProvider {
  id: string;
  name: string;
  type: 'openai' | 'gemini' | 'anthropic' | 'deepseek' | 'groq' | 'together' | 'ollama' | 'openrouter' | 'custom';
  enabled: boolean;
  api_key?: string;
  base_url?: string;
  models: string[];
  selected_model: string;
  status: 'connected' | 'disconnected' | 'testing' | 'error';
  last_tested?: string;
  error_message?: string;
}

export type AITaskType = 
  | 'video_understanding'
  | 'clip_discovery'
  | 'viral_scoring'
  | 'editing_decisions'
  | 'caption_correction'
  | 'hook_generation'
  | 'title_generation'
  | 'description_generation'
  | 'thumbnail_analysis'
  | 'final_quality_review';

export interface TaskModelAssignment {
  task: AITaskType;
  provider_id: string;
  model: string;
}

export interface HardwareProfileConfig {
  profile: 'ECO' | 'BALANCED' | 'QUALITY';
  max_ram_usage_gb: number;
  ffmpeg_threads: number;
  analysis_resolution: '360p' | '480p' | '720p';
  whisper_model: 'tiny' | 'base' | 'small' | 'medium';
  enable_gpu: boolean;
  max_concurrent_jobs: number;
}

export interface AutomationSettings {
  auto_start: boolean;
  clips_per_video: number;
  min_viral_score: number;
  min_duration: number;
  max_duration: number;
  target_aspect_ratio: '9:16' | '16:9' | '1:1';
  default_caption_preset: string;
  output_resolution: '1080p' | '720p' | '480p';
  language: string;
  auto_generate_metadata: boolean;
  auto_quality_review: boolean;
  auto_publish_youtube: boolean;
  daily_upload_limit: number;
  publishing_schedule: string; // 'immediate' | 'daily_at_time'
}

export interface YouTubeStudioStatus {
  connected: boolean;
  channel_id?: string;
  channel_title?: string;
  channel_thumbnail?: string;
  subscriber_count?: number;
  video_count?: number;
  quota_used: number;
  quota_limit: number;
  auth_mode: 'oauth' | 'api_key';
}

export interface ProcessingLog {
  id: string;
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'success';
  stage: PipelineStage;
  message: string;
  project_id?: string;
}

export interface DashboardMetrics {
  total_videos_processed: number;
  total_clips_generated: number;
  published_shorts: number;
  failed_jobs: number;
  average_clip_score: number;
  storage_usage_mb: number;
  storage_total_gb: number;
  queue_length: number;
  ai_status: 'online' | 'degraded' | 'offline';
  hardware_profile: 'ECO' | 'BALANCED' | 'QUALITY';
}
