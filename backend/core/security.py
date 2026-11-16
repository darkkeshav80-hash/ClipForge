import re
from pathlib import Path
from fastapi import HTTPException
from backend.config import settings

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".flv"}

def sanitize_filename(filename: str) -> str:
    """Removes invalid path and filesystem characters."""
    clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    return clean[:120]

def validate_video_extension(filename: str):
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video extension: '{ext}'. Allowed formats: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )

def safe_storage_path(relative_path: str) -> Path:
    """Ensures that the resolved path stays strictly within the application storage directory."""
    target = (settings.STORAGE_DIR / relative_path).resolve()
    storage_root = settings.STORAGE_DIR.resolve()
    try:
        target.relative_to(storage_root)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied: path traversal detected.")
    return target

def mask_api_key(key: str) -> str:
    if not key or len(key) < 8:
        return "••••••••"
    return f"{key[:4]}••••••••{key[-4:]}"
