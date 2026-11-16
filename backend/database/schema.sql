-- CLIPFORGE AI SQLite Database Schema

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    source_video_path TEXT,
    source_url TEXT,
    thumbnail_path TEXT,
    duration REAL DEFAULT 0.0,
    width INTEGER DEFAULT 1920,
    height INTEGER DEFAULT 1080,
    fps REAL DEFAULT 30.0,
    status TEXT DEFAULT 'idle',
    stage_progress REAL DEFAULT 0.0,
    total_progress REAL DEFAULT 0.0,
    clips_count INTEGER DEFAULT 0,
    caption_preset TEXT DEFAULT 'mrbeast',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clips (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    duration REAL NOT NULL,
    transcript TEXT,
    hook TEXT,
    category TEXT DEFAULT 'podcast',
    viral_score_json TEXT NOT NULL,
    editing_plan_json TEXT NOT NULL,
    rendered_path TEXT,
    thumbnail_path TEXT,
    caption_preset TEXT DEFAULT 'mrbeast-bold',
    aspect_ratio TEXT DEFAULT '9:16',
    status TEXT DEFAULT 'draft',
    review_verdict_json TEXT,
    youtube_published INTEGER DEFAULT 0,
    youtube_video_id TEXT,
    youtube_url TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS caption_presets (
    preset_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    font_family TEXT,
    font_size INTEGER,
    font_weight TEXT,
    text_color TEXT,
    highlight_color TEXT,
    outline_color TEXT,
    outline_width INTEGER,
    shadow_color TEXT,
    shadow_blur INTEGER,
    background_color TEXT,
    border_radius INTEGER,
    position TEXT,
    words_per_line INTEGER,
    animation_style TEXT,
    animation_speed REAL,
    all_caps INTEGER DEFAULT 0,
    emoji_enabled INTEGER DEFAULT 0,
    line_spacing REAL DEFAULT 1.2
);

CREATE TABLE IF NOT EXISTS ai_providers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    enabled INTEGER DEFAULT 0,
    api_key TEXT,
    base_url TEXT,
    models_json TEXT,
    selected_model TEXT,
    status TEXT DEFAULT 'disconnected',
    last_tested TEXT,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS task_assignments (
    task TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    model TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS automation_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    auto_start INTEGER DEFAULT 0,
    clips_per_video INTEGER DEFAULT 5,
    min_viral_score INTEGER DEFAULT 70,
    min_duration INTEGER DEFAULT 15,
    max_duration INTEGER DEFAULT 60,
    target_aspect_ratio TEXT DEFAULT '9:16',
    default_caption_preset TEXT DEFAULT 'mrbeast-bold',
    output_resolution TEXT DEFAULT '1080p',
    language TEXT DEFAULT 'en',
    auto_generate_metadata INTEGER DEFAULT 1,
    auto_quality_review INTEGER DEFAULT 1,
    auto_publish_youtube INTEGER DEFAULT 0,
    daily_upload_limit INTEGER DEFAULT 5,
    publishing_schedule TEXT DEFAULT 'immediate'
);

CREATE TABLE IF NOT EXISTS youtube_uploads (
    id TEXT PRIMARY KEY,
    clip_id TEXT NOT NULL,
    video_id TEXT,
    title TEXT,
    privacy TEXT DEFAULT 'public',
    status TEXT DEFAULT 'pending',
    youtube_url TEXT,
    published_at TEXT,
    FOREIGN KEY (clip_id) REFERENCES clips(id)
);

CREATE INDEX IF NOT EXISTS idx_clips_project_id ON clips(project_id);
CREATE INDEX IF NOT EXISTS idx_clips_status ON clips(status);
