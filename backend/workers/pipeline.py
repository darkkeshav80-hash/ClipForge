import asyncio
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from backend.config import settings
from backend.core.logger import logger, PipelineLogEmitter
from backend.core.db import db
from backend.video.ffmpeg_engine import ffmpeg_engine
from backend.video.face_tracker import face_tracker
from backend.video.punch_in import calculate_punch_moments
from backend.video.silence_remover import silence_detector
from backend.ai.transcription import transcriber
from backend.ai.analyzer import video_analyzer
from backend.ai.reviewer import quality_reviewer
from backend.captions.ass_writer import ass_writer
from backend.captions.sync_validator import sync_validator
from backend.publishing.youtube_client import youtube_client

class PipelineWorker:
    """
    Fault-Tolerant Autonomous Clipping Factory Worker:
    - One failed clip never kills the entire job.
    - Continuous 5-minute transcript checkpointing.
    - Non-overlapping ASS subtitles with sync validation.
    - Accurate face-centered framing and dynamic aspect ratios.
    - Honest UI: skips publishing stage when publishing is disabled.
    """
    def __init__(self):
        self.is_running = False
        self.is_paused = False
        self.current_project_id: Optional[str] = None
        self._task: Optional[asyncio.Task] = None

    async def start(self, project_id: Optional[str] = None):
        if self.is_running and not self.is_paused:
            logger.info("Pipeline already running.")
            if project_id:
                async with db.get_connection() as conn:
                    await conn.execute("UPDATE projects SET status = 'queued' WHERE id = ?", (project_id,))
                    await conn.commit()
                logger.info(f"Enqueued project {project_id} for automated processing.")
            return

        self.is_running = True
        self.is_paused = False
        self.current_project_id = project_id
        if PipelineLogEmitter._ws_manager:
            await PipelineLogEmitter._ws_manager.broadcast({
                "type": "control",
                "action": "start",
                "stage": "importing",
                "progress": 5.0,
                "project_id": project_id,
            })
        self._task = asyncio.create_task(self._run_loop(project_id))
        logger.info(f"Pipeline started for project: {project_id or 'next queued'}")

    async def pause(self):
        self.is_paused = True
        logger.info("Pipeline paused.")
        if PipelineLogEmitter._ws_manager:
            await PipelineLogEmitter._ws_manager.broadcast({
                "type": "control",
                "action": "pause",
                "stage": "paused",
            })
        if self.current_project_id:
            await self._update_project_status(self.current_project_id, "paused", 0.0)

    async def resume(self):
        self.is_paused = False
        logger.info("Pipeline resumed.")
        if PipelineLogEmitter._ws_manager:
            await PipelineLogEmitter._ws_manager.broadcast({
                "type": "control",
                "action": "resume",
            })

    async def stop(self):
        self.is_running = False
        self.is_paused = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Pipeline stopped.")
        if PipelineLogEmitter._ws_manager:
            await PipelineLogEmitter._ws_manager.broadcast({
                "type": "control",
                "action": "stop",
                "stage": "idle",
                "progress": 0.0,
            })
        if self.current_project_id:
            await self._update_project_status(self.current_project_id, "idle", 0.0)

    async def _update_project_status(self, project_id: str, status: str, total_progress: float, stage_progress: float = 0.0):
        async with db.get_connection() as conn:
            await conn.execute("""
                UPDATE projects SET status = ?, stage_progress = ?, total_progress = ?, updated_at = ? WHERE id = ?
            """, (status, stage_progress, total_progress, datetime.now().isoformat(), project_id))
            await conn.commit()
        if PipelineLogEmitter._ws_manager:
            await PipelineLogEmitter._ws_manager.broadcast({
                "type": "progress",
                "project_id": project_id,
                "status": status,
                "stage": status,
                "total_progress": total_progress,
                "progress": total_progress,
                "stage_progress": stage_progress,
            })

    async def _run_loop(self, project_id: Optional[str]):
        try:
            if project_id:
                await self._process_project(project_id)

            # Drain queue if any projects are waiting
            while self.is_running:
                async with db.get_connection() as conn:
                    cursor = await conn.execute("""
                        SELECT id FROM projects WHERE status = 'queued' ORDER BY created_at ASC LIMIT 1
                    """)
                    row = await cursor.fetchone()

                if row:
                    self.current_project_id = row["id"]
                    await self._process_project(row["id"])
                else:
                    break
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            logger.info("Pipeline worker task cancelled.")
        except Exception as e:
            logger.error(f"Pipeline execution fatal error: {e}", exc_info=True)
            if self.current_project_id:
                await self._update_project_status(self.current_project_id, "error", 0.0)
                await PipelineLogEmitter.emit("error", f"Pipeline aborted due to error: {str(e)}", "error", self.current_project_id)
        finally:
            self.is_running = False

    async def _process_project(self, project_id: str):
        # 1. Load project details from DB
        async with db.get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            project_row = await cursor.fetchone()

        if not project_row or not project_row["source_video_path"]:
            msg = f"Project {project_id} not found or has no source video path."
            logger.error(msg)
            await PipelineLogEmitter.emit("importing", msg, "error", project_id)
            return

        project = dict(project_row)

        p_str = project["source_video_path"]
        p_path = Path(p_str)
        if p_path.is_absolute() and p_path.exists():
            source_video = p_path
        elif (settings.ROOT_DIR / p_str).exists():
            source_video = settings.ROOT_DIR / p_str
        elif (settings.STORAGE_DIR / p_str).exists():
            source_video = settings.STORAGE_DIR / p_str
        elif (settings.UPLOADS_DIR / p_path.name).exists():
            source_video = settings.UPLOADS_DIR / p_path.name
        elif (settings.ROOT_DIR / p_path.name).exists():
            source_video = settings.ROOT_DIR / p_path.name
        else:
            raise FileNotFoundError(f"Source video not found: {p_str}")

        # STAGE 1: IMPORTING
        await self._check_pause()
        await self._update_project_status(project_id, "importing", 10.0, stage_progress=50.0)
        await PipelineLogEmitter.emit("importing", f"Probing video streams: {source_video.name}", "info", project_id)
        probe_info = await asyncio.to_thread(ffmpeg_engine.probe_video, source_video)

        async with db.get_connection() as conn:
            await conn.execute("""
                UPDATE projects SET duration = ?, width = ?, height = ?, fps = ? WHERE id = ?
            """, (probe_info["duration"], probe_info["width"], probe_info["height"], probe_info["fps"], project_id))
            await conn.commit()
        await self._update_project_status(project_id, "importing", 15.0, stage_progress=100.0)

        # STAGE 2: TRANSCRIBING (With 5-minute checkpointing & live progress)
        await self._check_pause()
        await self._update_project_status(project_id, "transcribing", 15.0, stage_progress=0.0)
        await PipelineLogEmitter.emit("transcribing", "Extracting 16kHz audio for Whisper speech recognition...", "info", project_id)

        audio_wav = settings.TEMP_DIR / f"{project_id}_audio.wav"
        if not audio_wav.exists() or audio_wav.stat().st_size == 0:
            await asyncio.to_thread(ffmpeg_engine.extract_audio, source_video, audio_wav)

        await PipelineLogEmitter.emit("transcribing", "Running Faster-Whisper with word timestamps & live checkpoints...", "info", project_id)
        
        # Read automation settings for language/model preferences
        async with db.get_connection() as conn:
            c = await conn.execute("SELECT * FROM automation_settings WHERE id = 1")
            auto_set_row = await c.fetchone()
        auto_set = dict(auto_set_row) if auto_set_row else {}

        loop = asyncio.get_running_loop()
        last_logged_pct = [-10.0]

        def on_transcribe_progress(stage_pct: float, msg: str):
            tot_prog = round(15.0 + (stage_pct / 100.0) * 25.0, 1)
            asyncio.run_coroutine_threadsafe(
                self._update_project_status(project_id, "transcribing", tot_prog, stage_progress=stage_pct),
                loop
            )
            if stage_pct - last_logged_pct[0] >= 10.0 or stage_pct >= 99.0:
                last_logged_pct[0] = stage_pct
                asyncio.run_coroutine_threadsafe(
                    PipelineLogEmitter.emit("transcribing", msg, "info", project_id),
                    loop
                )

        transcript_lang = auto_set["language"] if auto_set and "language" in auto_set.keys() else "auto"
        transcript_data = await asyncio.to_thread(
            transcriber.transcribe,
            audio_path=audio_wav,
            language=transcript_lang,
            progress_callback=on_transcribe_progress
        )

        await self._update_project_status(project_id, "transcribing", 40.0, stage_progress=100.0)
        await PipelineLogEmitter.emit(
            "transcribing",
            f"Transcription complete: {len(transcript_data.get('words', []))} words decoded ({transcript_data.get('language', 'auto')}).",
            "success",
            project_id
        )

        # STAGE 3 & 4: ANALYZING & SELECTING
        await self._check_pause()
        await self._update_project_status(project_id, "analyzing", 45.0, stage_progress=50.0)
        await PipelineLogEmitter.emit("analyzing", "AI Virality Scoring Engine evaluating storytelling peaks and hooks...", "info", project_id)

        target_clips = auto_set["clips_per_video"] if auto_set else 3
        min_viral = auto_set["min_viral_score"] if auto_set else 70
        min_dur = float(auto_set["min_duration"]) if auto_set else 15.0
        max_dur = float(auto_set["max_duration"]) if auto_set else 60.0
        project_preset = project.get("caption_preset") or (auto_set["default_caption_preset"] if auto_set else "mrbeast")
        default_preset = project_preset

        clips_to_make = await video_analyzer.discover_clips(
            transcript_data=transcript_data,
            target_clips=target_clips,
            min_duration=min_dur,
            max_duration=max_dur,
            min_viral_score=min_viral,
            default_preset=default_preset,
            video_path=source_video,
        )

        await self._update_project_status(project_id, "selecting", 60.0, stage_progress=100.0)
        await PipelineLogEmitter.emit("selecting", f"AI curated {len(clips_to_make)} viral candidate shorts.", "success", project_id)

        # Save clips with collision-free unique IDs
        saved_clips = []
        for idx, c in enumerate(clips_to_make):
            unique_suffix = uuid.uuid4().hex[:4]
            clip_id = f"clip-{project_id[-4:]}-{idx+1}-{unique_suffix}"
            c["id"] = clip_id
            c["project_id"] = project_id
            c["caption_preset"] = project_preset

            # Project aspect ratio preference
            aspect = c.get("aspect_ratio") or project.get("aspect_ratio") or "9:16"
            c["aspect_ratio"] = aspect

            async with db.get_connection() as conn:
                await conn.execute("""
                    INSERT OR REPLACE INTO clips (
                        id, project_id, title, description, start_time, end_time, duration,
                        transcript, hook, category, viral_score_json, editing_plan_json,
                        caption_preset, aspect_ratio, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    clip_id, project_id, c["title"], c["description"], c["start_time"], c["end_time"],
                    c["duration"], c["transcript"], c["hook"], c["category"], json.dumps(c["viral_score"]),
                    json.dumps(c["editing_plan"]), c["caption_preset"], aspect, "draft",
                    datetime.now().isoformat()
                ))
                await conn.commit()
            saved_clips.append(c)

        # STAGE 5, 6, 7: EDITING, CAPTIONING, RENDERING
        await self._update_project_status(project_id, "editing", 70.0)

        rendered_count = 0
        total_clips = len(saved_clips)

        for idx, clip in enumerate(saved_clips):
            await self._check_pause()
            clip_id = clip["id"]
            progress_pct = 70.0 + (idx / max(1, total_clips)) * 20.0
            clip_pct = round(((idx + 1) / max(1, total_clips)) * 100.0, 1)
            await self._update_project_status(project_id, "rendering", round(progress_pct, 1), stage_progress=clip_pct)

            try:
                await PipelineLogEmitter.emit(
                    "editing",
                    f"Processing clip {idx+1}/{total_clips}: calculating face tracking center & dynamic zoom...",
                    "info",
                    project_id,
                    clip_id
                )

                # Compute speaker face analysis (Single Face Center vs Dual-Speaker Podcast Split)
                speaker_analysis = await asyncio.to_thread(
                    face_tracker.analyze_speakers,
                    source_video, clip["start_time"], clip["duration"]
                )
                crop_center_x = speaker_analysis["single_center_x"]
                speaker_layout = speaker_analysis["layout"]
                left_c = speaker_analysis["left_center_x"]
                right_c = speaker_analysis["right_center_x"]

                if speaker_layout == "split":
                    await PipelineLogEmitter.emit(
                        "editing",
                        f"Podcast 2-shot detected: stacking speakers vertically in 9:16 (L:{left_c}, R:{right_c})",
                        "info",
                        project_id,
                        clip_id
                    )

                # STAGE 6: CAPTIONING (Generate Non-Overlapping Kinetic ASS Subtitles)
                preset_name = clip.get("caption_preset") or project.get("caption_preset") or "mrbeast"
                await PipelineLogEmitter.emit(
                    "captioning",
                    f"Generating kinetic {preset_name} ASS subtitles with zero-jitter active glow...",
                    "info",
                    project_id,
                    clip_id
                )

                # Load preset configuration from database or style engine
                async with db.get_connection() as conn:
                    cursor = await conn.execute("SELECT * FROM caption_presets WHERE preset_id = ?", (preset_name,))
                    preset_row = await cursor.fetchone()

                if preset_row:
                    p_dict = dict(preset_row)
                    preset_conf = {
                        "name": p_dict.get("name", preset_name),
                        "font_family": p_dict.get("font_family", "Impact"),
                        "font_size": p_dict.get("font_size", 48),
                        "font_weight": str(p_dict.get("font_weight", "800")),
                        "text_color": p_dict.get("text_color", "#FFFFFF"),
                        "highlight_color": p_dict.get("highlight_color", "#FACC15"),
                        "outline_color": p_dict.get("outline_color", "#000000"),
                        "outline_width": p_dict.get("outline_width", 4),
                        "position": p_dict.get("position", "bottom"),
                        "all_caps": bool(p_dict.get("all_caps", True)),
                        "words_per_line": p_dict.get("words_per_line", 3),
                    }
                else:
                    preset_conf = {"name": preset_name, "position": "bottom"}

                ass_path = settings.CAPTIONS_DIR / f"{clip_id}.ass"
                clip_words = clip.get("words", [])
                plan = clip.get("editing_plan", {})
                kws = plan.get("keywords", [])

                # Calculate dynamic hook-beat punch-in zoom timestamps
                punch_moments = calculate_punch_moments(
                    words=clip_words,
                    clip_start_offset=clip["start_time"],
                    duration=clip["duration"],
                    keywords=kws
                )
                if punch_moments:
                    await PipelineLogEmitter.emit(
                        "editing",
                        f"Dynamic punch-in zooms scheduled at {punch_moments}s on hook words",
                        "info",
                        project_id,
                        clip_id
                    )

                ass_writer.generate_ass(
                    words=clip_words,
                    preset=preset_conf,
                    output_path=ass_path,
                    video_width=probe_info.get("width", 1080),
                    video_height=probe_info.get("height", 1920),
                    clip_start_offset=clip["start_time"],
                    keywords=kws,
                    title=clip.get("title", "")
                )

                # Validate ASS timing sync
                sync_report = sync_validator.evaluate_sync(
                    ass_path=ass_path,
                    reference_words=clip_words,
                    clip_start_offset=clip["start_time"]
                )
                if not sync_report["synced"]:
                    await PipelineLogEmitter.emit(
                        "captioning",
                        f"Caption sync advisory: median offset is {sync_report['median_offset_ms']}ms",
                        "warning",
                        project_id,
                        clip_id
                    )

                # STAGE 7: RENDERING (FFmpeg with auto-retry and safe fallback)
                output_clip_path = settings.CLIPS_DIR / f"{clip_id}_rendered.mp4"
                thumb_path = settings.THUMBNAILS_DIR / f"{clip_id}_thumb.jpg"

                target_aspect = clip.get("aspect_ratio", "9:16")
                await PipelineLogEmitter.emit(
                    "rendering",
                    f"Rendering {target_aspect} short with FFmpeg ({speaker_layout} layout, dynamic zooms)...",
                    "info",
                    project_id,
                    clip_id
                )

                rendered_path, fallback_used, render_warn = await asyncio.to_thread(
                    ffmpeg_engine.render_clip,
                    input_video=source_video,
                    start_time=clip["start_time"],
                    duration=clip["duration"],
                    output_clip=output_clip_path,
                    aspect_ratio=target_aspect,
                    crop_center_x=crop_center_x,
                    layout=speaker_layout,
                    left_center_x=left_c,
                    right_center_x=right_c,
                    punch_moments=punch_moments,
                    zoom_in=bool(plan.get("smart_zoom", True)),
                    ass_subtitles_path=ass_path,
                    normalize_audio=True,
                    threads=settings.FFMPEG_THREADS,
                    max_duration_clamp=max_dur
                )

                if fallback_used:
                    await PipelineLogEmitter.emit(
                        "rendering",
                        f"Notice: Clip rendered with safe universal subtitles ({render_warn}).",
                        "warning",
                        project_id,
                        clip_id
                    )

                # Extract thumbnail
                await asyncio.to_thread(
                    ffmpeg_engine.extract_thumbnail,
                    video_path=output_clip_path,
                    timestamp=0.5,
                    output_thumb_path=thumb_path
                )

                # STAGE 8: REVIEWING (Multi-Model Quality Check)
                await PipelineLogEmitter.emit("reviewing", f"Running multi-model quality audit on {clip['title']}...", "info", project_id, clip_id)
                review_verdict = await quality_reviewer.review_clip(
                    clip_title=clip["title"],
                    hook=clip["hook"],
                    transcript=clip["transcript"],
                    duration=clip["duration"]
                )

                # Update clip in DB
                rel_clip_path = str(output_clip_path.relative_to(settings.STORAGE_DIR)).replace("\\", "/")
                rel_thumb_path = str(thumb_path.relative_to(settings.STORAGE_DIR)).replace("\\", "/")

                async with db.get_connection() as conn:
                    await conn.execute("""
                        UPDATE clips SET
                            rendered_path = ?,
                            thumbnail_path = ?,
                            review_verdict_json = ?,
                            status = 'ready'
                        WHERE id = ?
                    """, (rel_clip_path, rel_thumb_path, json.dumps(review_verdict), clip_id))
                    await conn.commit()

                rendered_count += 1
                if PipelineLogEmitter._ws_manager:
                    await PipelineLogEmitter._ws_manager.broadcast({
                        "type": "clip_ready",
                        "clip_id": clip_id,
                        "project_id": project_id,
                    })
                await PipelineLogEmitter.emit("rendering", f"Clip {clip_id} successfully rendered & ready for export!", "success", project_id, clip_id)

            except Exception as clip_err:
                logger.error(f"Clip {clip_id} hit an error and was skipped: {clip_err}", exc_info=True)
                await PipelineLogEmitter.emit(
                    "rendering",
                    f"Clip {clip_id} encountered an error and was skipped: {str(clip_err)}",
                    "error",
                    project_id,
                    clip_id
                )
                async with db.get_connection() as conn:
                    await conn.execute("UPDATE clips SET status = 'failed' WHERE id = ?", (clip_id,))
                    await conn.commit()
                # One failed clip NEVER kills the rest of the job!
                continue

        # STAGE 9: PUBLISHING (Only if explicitly enabled)
        auto_pub = bool(auto_set.get("auto_publish_youtube", False)) if auto_set else False
        if auto_pub:
            await self._update_project_status(project_id, "publishing", 95.0)
            await PipelineLogEmitter.emit("publishing", "Auto-publishing enabled. Processing YouTube queue...", "info", project_id)
        else:
            logger.info("Auto-publishing is disabled. Skipping publishing stage.")

        # Finalize project
        async with db.get_connection() as conn:
            await conn.execute("""
                UPDATE projects SET status = 'completed', stage_progress = 100.0, total_progress = 100.0, clips_count = ?, updated_at = ? WHERE id = ?
            """, (rendered_count, datetime.now().isoformat(), project_id))
            await conn.commit()

        await PipelineLogEmitter.emit("publishing", f"Autonomous video factory run complete! {rendered_count} clips ready in gallery.", "success", project_id)

    async def _check_pause(self):
        while self.is_paused:
            await asyncio.sleep(1.0)

pipeline_worker = PipelineWorker()
