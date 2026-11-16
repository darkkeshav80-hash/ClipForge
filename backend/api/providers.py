import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from backend.core.db import db
from backend.providers.adapter_registry import provider_registry
from backend.core.logger import logger

router = APIRouter(prefix="/api/providers", tags=["providers"])

@router.get("", response_model=List[Dict[str, Any]])
async def list_providers():
    async with db.get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM ai_providers ORDER BY name ASC")
        rows = await cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["enabled"] = bool(d["enabled"])
            d["models"] = json.loads(d.get("models_json") or "[]")
            result.append(d)
        return result

@router.put("/{provider_id}", response_model=Dict[str, Any])
async def update_provider(provider_id: str, data: Dict[str, Any]):
    async with db.get_connection() as conn:
        await conn.execute("""
            UPDATE ai_providers SET
                enabled = ?,
                api_key = ?,
                base_url = ?,
                models_json = ?,
                selected_model = ?,
                status = ?
            WHERE id = ?
        """, (
            1 if data.get("enabled") else 0,
            data.get("api_key", ""),
            data.get("base_url", ""),
            json.dumps(data.get("models", [])),
            data.get("selected_model", ""),
            data.get("status", "disconnected"),
            provider_id
        ))
        await conn.commit()
    return data

@router.post("/{provider_id}/test")
async def test_provider_endpoint(provider_id: str):
    logger.info(f"Testing provider connection: {provider_id}")
    provider = await provider_registry.get_provider(provider_id)
    result = await provider.test_connection()
    
    status_str = "connected" if result.get("success") else "error"
    models = result.get("models", [])
    
    async with db.get_connection() as conn:
        if models:
            await conn.execute("""
                UPDATE ai_providers SET status = ?, models_json = ? WHERE id = ?
            """, (status_str, json.dumps(models), provider_id))
        else:
            await conn.execute("UPDATE ai_providers SET status = ? WHERE id = ?", (status_str, provider_id))
        await conn.commit()

    return result
