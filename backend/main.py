import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.core.logger import logger
from backend.core.db import db

# Import API Routers
from backend.api.projects import router as projects_router
from backend.api.videos import router as videos_router
from backend.api.clips import router as clips_router
from backend.api.captions import router as captions_router
from backend.api.models import router as models_router
from backend.api.providers import router as providers_router
from backend.api.automation import router as automation_router
from backend.api.youtube import router as youtube_router
from backend.api.analytics import router as analytics_router
from backend.api.system import router as system_router
from backend.api.websocket import router as websocket_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    logger.info("=======================================================")
    logger.info(f" Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f" Host: {settings.HOST}:{settings.PORT}")
    logger.info(f" Storage Directory: {settings.STORAGE_DIR}")
    logger.info("=======================================================")
    
    # Initialize SQLite schema & seed catalogs
    await db.init_db()

    # Recovery: check for interrupted jobs from previous session
    async with db.get_connection() as conn:
        cursor = await conn.execute("SELECT id, name, source_video_path FROM projects WHERE status IN ('importing', 'transcribing', 'analyzing', 'editing', 'rendering', 'queued')")
        interrupted = await cursor.fetchall()
        if interrupted:
            logger.info(f"Marking {len(interrupted)} interrupted job(s) from previous session as resumable...")
            await conn.execute("UPDATE projects SET status = 'interrupted' WHERE status IN ('importing', 'transcribing', 'analyzing', 'editing', 'rendering', 'queued')")
            await conn.commit()
        
        # Clean up duplicate empty/stuck projects
        await conn.execute("""
            DELETE FROM projects WHERE status = 'interrupted' AND (duration IS NULL OR duration = 0)
            AND id NOT IN (SELECT MIN(id) FROM projects GROUP BY source_video_path)
        """)
        await conn.commit()

    yield

    # Shutdown sequence
    logger.info(f"Shutting down {settings.APP_NAME}...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Autonomous Local AI Video Clipping Factory",
    lifespan=lifespan,
)

# CORS Middleware (Local-first browser access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def block_cross_site_writes(request: Request, call_next):
    """CSRF guard: CORS does not stop a foreign web page from *sending* simple requests
    (e.g. multipart uploads), so reject state-changing requests from unknown browser origins."""
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin and origin not in settings.ALLOWED_ORIGINS:
            return JSONResponse(status_code=403, content={"detail": "Cross-origin request blocked."})
    return await call_next(request)

# Added last so it runs first: rejects unexpected Host headers (DNS-rebinding protection)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# Register REST Routers
app.include_router(projects_router)
app.include_router(videos_router)
app.include_router(clips_router)
app.include_router(captions_router)
app.include_router(models_router)
app.include_router(providers_router)
app.include_router(automation_router)
app.include_router(youtube_router)
app.include_router(analytics_router)
app.include_router(system_router)
app.include_router(websocket_router)

# Serve ONLY the public media folders. The storage root also holds the SQLite database
# (which contains API keys), uploads and temp files, and must never be exposed.
for _sub, _dir in (("clips", settings.CLIPS_DIR), ("thumbnails", settings.THUMBNAILS_DIR), ("previews", settings.PREVIEWS_DIR)):
    app.mount(f"/storage/{_sub}", StaticFiles(directory=str(_dir)), name=f"storage-{_sub}")

# Mount Built Frontend if available
frontend_dist = settings.ROOT_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    async def index():
        return {
            "app": settings.APP_NAME,
            "version": settings.VERSION,
            "status": "running",
            "frontend_dev_url": f"http://localhost:{settings.FRONTEND_PORT}",
            "docs": f"http://localhost:{settings.PORT}/docs",
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.ENVIRONMENT == "development")
