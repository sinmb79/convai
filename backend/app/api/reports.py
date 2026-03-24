import uuid
from datetime import date
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func
from app.deps import CurrentUser, DB
from app.models.report import Report, ReportType
from app.models.daily_report import DailyReport
from app.models.weather import WeatherAlert
from app.models.project import Project
from app.schemas.report import ReportGenerateRequest, ReportResponse
from app.services.report_gen import generate_weekly_report, generate_monthly_report

router = APIRouter(prefix="/projects/{project_id}/reports", tags=["공정보고서"])


# Report schemas (inline for simplicity)
from pydantic import BaseModel
from app.models.report import ReportType, ReportStatus


class ReportGenerateRequest(BaseModel):
    report_type: ReportType
    period_start: date
    period_end: date


class ReportResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    report_type: ReportType
    period_start: date
    period_end: date
    ai_draft_text: str | None
    status: ReportStatus
    pdf_s3_key: str | None

    model_config = {"from_attributes": True}


async def _get_project_or_404(project_id: uuid.UUID, db: DB) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return p


def _compute_overall_progress(tasks) -> float:
    if not tasks:
        return 0.0
    total = sum(t.progress_pct for t in tasks)
    return total / len(tasks)


@router.get("", response_model=list[ReportResponse])
async def list_reports(project_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(
        select(Report)
        .where(Report.project_id == project_id)
        .order_by(Report.period_start.desc())
    )
    return result.scalars().all()


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(project_id: uuid.UUID, data: ReportGenerateRequest, db: DB, current_user: CurrentUser):
    """AI-generate weekly or monthly report draft."""
    project = await _get_project_or_404(project_id, db)

    # Get daily reports in period
    daily_result = await db.execute(
        select(DailyReport).where(
            DailyReport.project_id == project_id,
            DailyReport.report_date >= data.period_start,
            DailyReport.report_date <= data.period_end,
        ).order_by(DailyReport.report_date)
    )
    daily_reports = daily_result.scalars().all()

    # Get tasks for progress
    from app.models.task import Task
    tasks_result = await db.execute(select(Task).where(Task.project_id == project_id))
    tasks = tasks_result.scalars().all()
    overall_progress = _compute_overall_progress(tasks)

    if data.report_type == ReportType.WEEKLY:
        # Get weather alerts in period
        alerts_result = await db.execute(
            select(WeatherAlert).where(
                WeatherAlert.project_id == project_id,
                WeatherAlert.alert_date >= data.period_start,
                WeatherAlert.alert_date <= data.period_end,
            )
        )
        weather_alerts = alerts_result.scalars().all()

        ai_text, content_json = await generate_weekly_report(
            project_name=project.name,
            period_start=str(data.period_start),
            period_end=str(data.period_end),
            daily_reports=daily_reports,
            overall_progress_pct=overall_progress,
            weather_alerts=weather_alerts,
        )
    else:
        ai_text, content_json = await generate_monthly_report(
            project_name=project.name,
            period_start=str(data.period_start),
            period_end=str(data.period_end),
            daily_reports=daily_reports,
            overall_progress_pct=overall_progress,
        )

    report = Report(
        project_id=project_id,
        report_type=data.report_type,
        period_start=data.period_start,
        period_end=data.period_end,
        content_json=content_json,
        ai_draft_text=ai_text,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(project_id: uuid.UUID, report_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Report).where(Report.id == report_id, Report.project_id == project_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다")
    return report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(project_id: uuid.UUID, report_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Report).where(Report.id == report_id, Report.project_id == project_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다")
    await db.delete(report)
    await db.commit()
