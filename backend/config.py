import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "CLIPFORGE AI"
    VERSION: str = "1.0.0"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    FRONTEND_PORT: int = 3000
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Base Paths
    ROOT_DIR: Path = BASE_DIR
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOADS_DIR: Path = BASE_DIR / "storage" / "uploads"
    CLIPS_DIR: Path = BASE_DIR / "storage" / "clips"
    THUMBNAILS_DIR: Path = BASE_DIR / "storage" / "thumbnails"
    CAPTIONS_DIR: Path = BASE_DIR / "storage" / "captions"
    TEMP_DIR: Path = BASE_DIR / "storage" / "temp"
    MODELS_DIR: Path = BASE_DIR / "models"
    LOGS_DIR: Path = BASE_DIR / "logs"
    CONFIG_DIR: Path = BASE_DIR / "config"
    DATABASE_PATH: Path = BASE_DIR / "storage" / "clipforge.db"

    # Hardware Tuning
    HARDWARE_PROFILE: str = "BALANCED" # ECO | BALANCED | QUALITY
    FFMPEG_THREADS: int = 4
    MAX_CONCURRENT_JOBS: int = 1
    ENABLE_GPU_ACCELERATION: bool = False

    # AI Provider Keys
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    TOGETHER_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    DEFAULT_WHISPER_MODEL: str = "base"

    # YouTube API
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""
    YOUTUBE_REDIRECT_URI: str = "http://localhost:8000/api/youtube/callback"

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
for d in [
    settings.STORAGE_DIR,
    settings.UPLOADS_DIR,
    settings.CLIPS_DIR,
    settings.THUMBNAILS_DIR,
    settings.CAPTIONS_DIR,
    settings.TEMP_DIR,
    settings.MODELS_DIR,
    settings.LOGS_DIR,
    settings.CONFIG_DIR,
]:
    d.mkdir(parents=True, exist_ok=True)
