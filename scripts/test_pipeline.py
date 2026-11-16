import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from datetime import datetime
from backend.config import settings
from backend.core.db import db
from backend.core.logger import logger
from backend.workers.pipeline import pipeline_worker
from backend.video.ffmpeg_engine import ffmpeg_engine
from scripts.generate_test_video import create_sample_video

async def run_end_to_end_pipeline():
    logger.info(">>> STARTING CLIPFORGE AI END-TO-END PIPELINE TEST <<<")
    await db.init_db()

    # 1. Ensure sample test source video exists
    sample_video = settings.UPLOADS_DIR / "sample_test_source.mp4"
    if not sample_video.exists():
        create_sample_video(sample_video, duration_sec=10)

    # 2. Create Project in DB
    project_id = f"test-proj-{int(datetime.now().timestamp())}"
    rel_video_path = str(sample_video.relative_to(settings.ROOT_DIR)).replace("\\", "/")
    
    async with db.get_connection() as conn:
        await conn.execute("""
            INSERT INTO projects (
                id, name, description, source_video_path, duration, width, height,
                fps, status, stage_progress, total_progress, clips_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            "End-To-End Automation Test Project",
            "Autonomous verification run",
            rel_video_path,
            10.0, 1920, 1080, 30.0,
            "idle", 0.0, 0.0, 0,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
        ))
        await conn.commit()

    logger.info(f"Project created with ID: {project_id}")

    # 3. Execute Complete 9-Stage Factory Pipeline
    logger.info("Triggering autonomous factory worker execution...")
    await pipeline_worker._process_project(project_id)

    # 4. Verify Database & File Artifacts
    async with db.get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        proj = await cursor.fetchone()
        assert proj["status"] == "completed", f"Expected completed status, got {proj['status']}"
        assert proj["total_progress"] == 100.0

        c_cursor = await conn.execute("SELECT * FROM clips WHERE project_id = ?", (project_id,))
        clips = await c_cursor.fetchall()
        assert len(clips) > 0, "Pipeline must generate at least 1 clip"
        
        for c in clips:
            rendered = settings.STORAGE_DIR / c["rendered_path"]
            assert rendered.exists(), f"Rendered clip file must exist: {rendered}"
            assert rendered.stat().st_size > 5000, f"Rendered clip must not be empty: {rendered}"
            
            probe = ffmpeg_engine.probe_video(rendered)
            assert probe["width"] == 1080, "Short must have width 1080"
            assert probe["height"] == 1920, "Short must have vertical height 1920"
            logger.info(f"VERIFIED SHORT: {c['title']} | Score: {c['viral_score_json'][:40]}... | Path: {c['rendered_path']} ({probe['width']}x{probe['height']})")

    logger.info("=====================================================================")
    logger.info(">>> END-TO-END AUTOMATION PIPELINE TEST PASSED WITH 100% SUCCESS! <<<")
    logger.info("=====================================================================")

if __name__ == "__main__":
    asyncio.run(run_end_to_end_pipeline())
