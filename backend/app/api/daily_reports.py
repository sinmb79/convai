import uuid
from datetime import date
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from app.deps import CurrentUser, DB
from app.models.daily_report import DailyReport, InputSource
from app.models.project import Project
from app.schemas.daily_report import (
    DailyReportCreate, DailyReportUpdate, DailyReportGenerateRequest, DailyReportResponse
)
from app.services.daily_report_gen import generate_work_content
from app.services.pdf_service import generate_daily_report_pdf

router = APIRouter(prefix="/projects/{project_id}/daily-reports", tags=["작업일보"])


async def _get_project_or_404(project_id: uuid.UUID, db: DB) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return p


@router.get("", response_model=list[DailyReportResponse])
async def list_reports(project_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(
        select(DailyReport)
        .where(DailyReport.project_id == project_id)
        .order_by(DailyReport.report_date.desc())
    )
    return result.scalars().all()


@router.post("", response_model=DailyReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(project_id: uuid.UUID, data: DailyReportCreate, db: DB, current_user: CurrentUser):
    await _get_project_or_404(project_id, db)
    report = DailyReport(**data.model_dump(), project_id=project_id, input_source=InputSource.WEB)
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.post("/generate", response_model=DailyReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(project_id: uuid.UUID, data: DailyReportGenerateRequest, db: DB, current_user: CurrentUser):
    """AI-generate daily report content from structured input."""
    project = await _get_project_or_404(project_id, db)

    work_content = await generate_work_content(
        project_name=project.name,
        report_date=str(data.report_date),
        weather_summary="맑음",  # Will be filled from weather data
        temperature_high=None,
        temperature_low=None,
        workers_count=data.workers_count,
        equipment_list=data.equipment_list or [],
        work_items=data.work_items,
        issues=data.issues,
    )

    report = DailyReport(
        project_id=project_id,
        report_date=data.report_date,
        workers_count=data.workers_count,
        equipment_list=data.equipment_list,
        work_content=work_content,
        issues=data.issues,
        input_source=InputSource.WEB,
        ai_generated=True,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/{report_id}", response_model=DailyReportResponse)
async def get_report(project_id: uuid.UUID, report_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(DailyReport).where(DailyReport.id == report_id, DailyReport.project_id == project_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="일보를 찾을 수 없습니다")
    return report


@router.put("/{report_id}", response_model=DailyReportResponse)
async def update_report(project_id: uuid.UUID, report_id: uuid.UUID, data: DailyReportUpdate, db: DB, current_user: CurrentUser):
    result = await db.execute(select(DailyReport).where(DailyReport.id == report_id, DailyReport.project_id == project_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="일보를 찾을 수 없습니다")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(report, field, value)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/{report_id}/pdf")
async def download_report_pdf(project_id: uuid.UUID, report_id: uuid.UUID, db: DB, current_user: CurrentUser):
    """작업일보 PDF 다운로드"""
    r = await db.execute(select(DailyReport).where(DailyReport.id == report_id, DailyReport.project_id == project_id))
    report = r.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="일보를 찾을 수 없습니다")
    project = await _get_project_or_404(project_id, db)
    pdf_bytes = generate_daily_report_pdf(report, project)
    filename = f"daily_report_{report.report_date}.pdf"
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"})


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(project_id: uuid.UUID, report_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(DailyReport).where(DailyReport.id == report_id, DailyReport.project_id == project_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="일보를 찾을 수 없습니다")
    await db.delete(report)
    await db.commit()
