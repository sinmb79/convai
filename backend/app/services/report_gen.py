"""Weekly and monthly report generation."""
from app.services.ai_engine import complete
from app.services.prompts.report import (
    WEEKLY_SYSTEM_PROMPT, MONTHLY_SYSTEM_PROMPT,
    build_weekly_prompt, build_monthly_prompt,
)


async def generate_weekly_report(
    project_name: str,
    period_start: str,
    period_end: str,
    daily_reports: list,
    overall_progress_pct: float,
    weather_alerts: list,
) -> tuple[str, dict]:
    """
    Generate weekly report text and structured data.
    Returns (ai_text, content_json).
    """
    daily_summaries = [
        {
            "date": str(r.report_date),
            "work_content": r.work_content or "",
        }
        for r in daily_reports
    ]

    weather_issues = [f"{a.alert_date}: {a.message}" for a in weather_alerts]

    # Calculate stats
    total_workers = sum(
        sum(r.workers_count.values()) if r.workers_count else 0
        for r in daily_reports
    )

    prompt = build_weekly_prompt(
        project_name=project_name,
        period_start=period_start,
        period_end=period_end,
        daily_summaries=daily_summaries,
        overall_progress_pct=overall_progress_pct,
        weather_issues=weather_issues,
    )

    ai_text = await complete(
        messages=[{"role": "user", "content": prompt}],
        system=WEEKLY_SYSTEM_PROMPT,
        temperature=0.3,
    )

    content_json = {
        "period_start": period_start,
        "period_end": period_end,
        "overall_progress_pct": overall_progress_pct,
        "daily_count": len(daily_reports),
        "total_workers": total_workers,
        "weather_alert_count": len(weather_alerts),
    }

    return ai_text, content_json


async def generate_monthly_report(
    project_name: str,
    period_start: str,
    period_end: str,
    daily_reports: list,
    overall_progress_pct: float,
) -> tuple[str, dict]:
    """Generate monthly report text and structured data."""
    # Group dailies by week for summary
    weekly_summaries = []
    for r in daily_reports[::7]:  # Sample weekly
        if r.work_content:
            weekly_summaries.append(f"- {r.report_date}: {r.work_content[:80]}...")

    prompt = build_monthly_prompt(
        project_name=project_name,
        period_start=period_start,
        period_end=period_end,
        weekly_summaries=weekly_summaries,
        overall_progress_pct=overall_progress_pct,
    )

    ai_text = await complete(
        messages=[{"role": "user", "content": prompt}],
        system=MONTHLY_SYSTEM_PROMPT,
        temperature=0.3,
    )

    content_json = {
        "period_start": period_start,
        "period_end": period_end,
        "overall_progress_pct": overall_progress_pct,
        "daily_count": len(daily_reports),
    }

    return ai_text, content_json
