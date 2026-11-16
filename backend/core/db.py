import aiosqlite
import json
from contextlib import asynccontextmanager
from pathlib import Path
from backend.config import settings
from backend.core.logger import logger

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "database" / "schema.sql"

class Database:
    def __init__(self, db_path: Path = settings.DATABASE_PATH):
        self.db_path = db_path

    @asynccontextmanager
    async def get_connection(self):
        """Yields an active SQLite connection with row_factory set to Row."""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA foreign_keys = ON;")
            yield conn

    async def init_db(self):
        """Initializes tables and seeds default presets/providers."""
        async with self.get_connection() as conn:
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            await conn.executescript(schema_sql)
            await conn.commit()

        # Seed Caption Presets if table is empty
        await self.seed_caption_presets()
        # Seed AI Providers if table is empty
        await self.seed_ai_providers()
        # Seed Default Automation Settings
        await self.seed_automation_settings()
        logger.info(f"Database initialized at {self.db_path}")

    async def seed_caption_presets(self):
        presets_file = settings.CONFIG_DIR / "caption_presets.json"
        if not presets_file.exists():
            return
        async with self.get_connection() as conn:
            cursor = await conn.execute("SELECT COUNT(*) as count FROM caption_presets")
            row = await cursor.fetchone()
            if row and row["count"] > 0:
                return

            with open(presets_file, "r", encoding="utf-8") as f:
                presets = json.load(f)

            for p in presets:
                await conn.execute("""
                    INSERT OR REPLACE INTO caption_presets (
                        preset_id, name, description, category, font_family, font_size,
                        font_weight, text_color, highlight_color, outline_color, outline_width,
                        shadow_color, shadow_blur, background_color, border_radius, position,
                        words_per_line, animation_style, animation_speed, all_caps, emoji_enabled, line_spacing
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p["preset_id"], p["name"], p["description"], p["category"], p["font_family"],
                    p["font_size"], p["font_weight"], p["text_color"], p["highlight_color"],
                    p["outline_color"], p["outline_width"], p["shadow_color"], p["shadow_blur"],
                    p["background_color"], p["border_radius"], p["position"], p["words_per_line"],
                    p["animation_style"], p["animation_speed"], 1 if p.get("all_caps") else 0,
                    1 if p.get("emoji_enabled") else 0, p.get("line_spacing", 1.2)
                ))
            await conn.commit()
            logger.info(f"Seeded {len(presets)} caption presets into database")

    async def seed_ai_providers(self):
        providers_file = settings.CONFIG_DIR / "api_providers.json"
        if not providers_file.exists():
            return
        async with self.get_connection() as conn:
            cursor = await conn.execute("SELECT COUNT(*) as count FROM ai_providers")
            row = await cursor.fetchone()
            if row and row["count"] > 0:
                return

            with open(providers_file, "r", encoding="utf-8") as f:
                providers = json.load(f)

            for p in providers:
                await conn.execute("""
                    INSERT OR REPLACE INTO ai_providers (
                        id, name, type, enabled, api_key, base_url, models_json, selected_model, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p["id"], p["name"], p["type"], 1 if p.get("enabled") else 0,
                    p.get("api_key", ""), p.get("base_url", ""), json.dumps(p.get("models", [])),
                    p.get("selected_model", ""), p.get("status", "disconnected")
                ))
            await conn.commit()
            logger.info(f"Seeded {len(providers)} AI provider configurations into database")

    async def seed_automation_settings(self):
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT OR IGNORE INTO automation_settings (
                    id, auto_start, clips_per_video, min_viral_score, min_duration,
                    max_duration, target_aspect_ratio, default_caption_preset,
                    output_resolution, language, auto_generate_metadata, auto_quality_review,
                    auto_publish_youtube, daily_upload_limit, publishing_schedule
                ) VALUES (1, 0, 5, 70, 15, 60, '9:16', 'mrbeast-bold', '1080p', 'en', 1, 1, 0, 5, 'immediate')
            """)
            await conn.commit()

db = Database()
