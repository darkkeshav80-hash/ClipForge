from fastapi import APIRouter
from typing import List, Dict, Any
from backend.core.db import db

router = APIRouter(prefix="/api/models", tags=["models"])

@router.get("/assignments", response_model=List[Dict[str, Any]])
async def get_assignments():
    async with db.get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM task_assignments")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

@router.post("/assignments")
async def save_assignments(assignments: List[Dict[str, Any]]):
    async with db.get_connection() as conn:
        for a in assignments:
            await conn.execute("""
                INSERT OR REPLACE INTO task_assignments (task, provider_id, model)
                VALUES (?, ?, ?)
            """, (a["task"], a["provider_id"], a["model"]))
        await conn.commit()
    return {"success": True, "count": len(assignments)}
