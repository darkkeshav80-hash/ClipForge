import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from backend.core.db import db
from backend.providers.adapter_registry import provider_registry
from backend.core.logger import logger
from backend.core.security import mask_api_key, is_masked_key

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
            d["api_key"] = mask_api_key(d["api_key"]) if d.get("api_key") else ""
            result.append(d)
        return result

@router.put("/{provider_id}", response_model=Dict[str, Any])
async def update_provider(provider_id: str, data: Dict[str, Any]):
    base_url = (data.get("base_url") or "").strip()
    if base_url and not base_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="base_url must start with http:// or https://")

    async with db.get_connection() as conn:
        cursor = await conn.execute("SELECT api_key FROM ai_providers WHERE id = ?", (provider_id,))
        existing = await cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Provider not found")

        # The API never returns real keys, so a missing or masked key means "unchanged".
        incoming_key = data.get("api_key")
        api_key = (existing["api_key"] or "") if (incoming_key is None or is_masked_key(incoming_key)) else incoming_key

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
            api_key,
            base_url,
            json.dumps(data.get("models", [])),
            data.get("selected_model", ""),
            data.get("status", "disconnected"),
            provider_id
        ))
        await conn.commit()
    return {**data, "api_key": mask_api_key(api_key) if api_key else ""}

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
