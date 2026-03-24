"""AI-powered inspection request generation."""
import json
from app.services.ai_engine import complete_json
from app.services.prompts.inspection import SYSTEM_PROMPT, build_prompt


async def generate_checklist(
    project_name: str,
    inspection_type: str,
    location_detail: str | None,
    requested_date: str,
    wbs_name: str | None,
) -> list[dict]:
    """Generate inspection checklist items using Claude."""
    prompt = build_prompt(
        project_name=project_name,
        inspection_type=inspection_type,
        location_detail=location_detail,
        requested_date=requested_date,
        wbs_name=wbs_name,
    )

    raw = await complete_json(
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_PROMPT,
        temperature=0.2,
    )

    try:
        data = json.loads(raw)
        return data.get("checklist_items", [])
    except (json.JSONDecodeError, KeyError):
        # Fallback: return empty checklist
        return []
