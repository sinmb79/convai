"""AI-powered daily report generation."""
from app.services.ai_engine import complete
from app.services.prompts.daily_report import SYSTEM_PROMPT, build_prompt


async def generate_work_content(
    project_name: str,
    report_date: str,
    weather_summary: str,
    temperature_high: float | None,
    temperature_low: float | None,
    workers_count: dict,
    equipment_list: list,
    work_items: list[str],
    issues: str | None,
) -> str:
    """Generate the work content text for a daily report."""
    temp_str = ""
    if temperature_high is not None and temperature_low is not None:
        temp_str = f"최고 {temperature_high}°C / 최저 {temperature_low}°C"
    elif temperature_high is not None:
        temp_str = f"최고 {temperature_high}°C"
    else:
        temp_str = "기온 정보 없음"

    prompt = build_prompt(
        project_name=project_name,
        report_date=report_date,
        weather_summary=weather_summary or "맑음",
        temperature=temp_str,
        workers=workers_count or {},
        equipment=equipment_list or [],
        work_items=work_items,
        issues=issues,
    )

    return await complete(
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_PROMPT,
        temperature=0.3,
    )
