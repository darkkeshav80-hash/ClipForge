import ipaddress
import re
import socket
import uuid
from pathlib import Path
from urllib.parse import urlparse
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

def unique_filename(filename: str) -> str:
    """Sanitizes a filename and appends a short random suffix so uploads never overwrite each other."""
    clean = sanitize_filename(filename)
    p = Path(clean)
    stem = p.stem[:100] or "video"
    return f"{stem}_{uuid.uuid4().hex[:8]}{p.suffix.lower()}"

def validate_public_url(url: str) -> str:
    """SSRF guard: only http(s) URLs whose host resolves exclusively to public IP addresses."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=400, detail="Invalid URL. Must be a full http:// or https:// address.")
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror:
        raise HTTPException(status_code=400, detail="Could not resolve the URL's host.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                or ip.is_multicast or ip.is_unspecified):
            raise HTTPException(status_code=400, detail="URLs pointing to local or private network addresses are not allowed.")
    return url

def is_masked_key(key: str) -> bool:
    return bool(key) and "•" in key

def mask_api_key(key: str) -> str:
    if not key or len(key) < 8:
        return "••••••••"
    return f"{key[:4]}••••••••{key[-4:]}"
