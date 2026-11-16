import logging
import sys
from datetime import datetime
from pathlib import Path
from backend.config import settings

LOG_FILE = settings.LOGS_DIR / "clipforge.log"

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)

logger = logging.getLogger("clipforge")

class PipelineLogEmitter:
    """Dispatches logs both to standard logger and to the UI via WebSockets."""
    _ws_manager = None

    @classmethod
    def set_ws_manager(cls, manager):
        cls._ws_manager = manager

    @classmethod
    async def emit(cls, stage: str, message: str, level: str = "info", project_id: str = None, clip_id: str = None):
        log_entry = {
            "id": f"log-{int(datetime.now().timestamp() * 1000)}",
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "stage": stage,
            "message": message,
            "project_id": project_id,
        }

        # Log locally
        if level == "error":
            logger.error(f"[{stage.upper()}] {message}")
        elif level == "warn":
            logger.warning(f"[{stage.upper()}] {message}")
        else:
            logger.info(f"[{stage.upper()}] {message}")

        # Broadcast via WebSocket if connected
        if cls._ws_manager:
            await cls._ws_manager.broadcast({
                "type": "log",
                "stage": stage,
                "project_id": project_id,
                "clip_id": clip_id,
                "log": log_entry,
            })
