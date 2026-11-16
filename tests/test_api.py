import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.db import db

client = TestClient(app)

def test_api_health():
    res = client.get("/api/analytics/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "total_videos_processed" in data
    assert "average_clip_score" in data

def test_caption_presets():
    res = client.get("/api/captions/presets")
    assert res.status_code == 200
    presets = res.json()
    assert len(presets) >= 22
    preset_ids = [p["preset_id"] for p in presets]
    assert "mrbeast-bold" in preset_ids
    assert "hormozi-emphasis" in preset_ids
    assert "clean-white" in preset_ids

def test_providers_list():
    res = client.get("/api/providers")
    assert res.status_code == 200
    providers = res.json()
    assert len(providers) >= 8
    types = [p["type"] for p in providers]
    assert "ollama" in types
    assert "openai" in types
    assert "gemini" in types

def test_project_crud():
    # Create project
    create_payload = {
        "name": "Automated Test Project",
        "duration": 120.0,
        "width": 1920,
        "height": 1080,
    }
    res = client.post("/api/projects", json=create_payload)
    assert res.status_code == 200
    proj = res.json()
    assert proj["name"] == "Automated Test Project"
    proj_id = proj["id"]

    # Get project
    res_get = client.get(f"/api/projects/{proj_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == proj_id

    # Delete project
    res_del = client.delete(f"/api/projects/{proj_id}")
    assert res_del.status_code == 200

def test_automation_settings():
    res = client.get("/api/automation/settings")
    assert res.status_code == 200
    data = res.json()
    assert "min_viral_score" in data
    assert "clips_per_video" in data

if __name__ == "__main__":
    asyncio.run(db.init_db())
    test_api_health()
    test_caption_presets()
    test_providers_list()
    test_project_crud()
    test_automation_settings()
    print("ALL API TESTS PASSED SUCCESSFULLY!")
