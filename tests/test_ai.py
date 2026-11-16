import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from backend.core.db import db
from backend.ai.scorer import viral_scorer
from backend.ai.editing_brain import editing_brain
from backend.ai.reviewer import quality_reviewer

async def run_ai_tests():
    await db.init_db()

    transcript = (
        "Most people don't realize that in the next 24 months, "
        "autonomous AI agents will replace almost all middle management. "
        "The reason is simple: coordinating information between two software tools "
        "can now be done instantly and without error."
    )

    # 1. Test Viral Scorer
    score_breakdown = await viral_scorer.evaluate_moment(transcript, duration=22.0, category="podcast")
    assert "overall" in score_breakdown
    assert 0 <= score_breakdown["overall"] <= 100
    assert "hook" in score_breakdown
    assert "explanation" in score_breakdown
    print(f"Viral score computed: {score_breakdown['overall']}/100 (Hook: {score_breakdown['hook']})")

    # 2. Test Editing Decision Brain
    plan = await editing_brain.generate_editing_plan(
        clip_id="test-clip-01",
        start_time=10.0,
        end_time=32.0,
        transcript=transcript,
        category="podcast",
        default_preset="mrbeast-bold"
    )
    assert plan["clip_id"] == "test-clip-01"
    assert "hook_text" in plan
    assert "target_aspect_ratio" in plan
    assert plan["target_aspect_ratio"] == "9:16"
    assert plan["face_tracking"] is True
    print(f"Editing decision plan generated: Hook='{plan['hook_text']}', Aspect='{plan['target_aspect_ratio']}'")

    # 3. Test Multi-Model Reviewer
    verdict = await quality_reviewer.review_clip(
        clip_title="Why Agents Replace Management",
        hook=plan["hook_text"],
        transcript=transcript,
        duration=22.0
    )
    assert "approved" in verdict
    assert "score" in verdict
    print(f"Quality reviewer verdict: Approved={verdict['approved']}, Quality Score={verdict['score']}")

if __name__ == "__main__":
    asyncio.run(run_ai_tests())
    print("ALL AI ENGINE TESTS PASSED SUCCESSFULLY!")
