import uuid
from datetime import date, datetime
from pydantic import BaseModel
from app.models.daily_report import ReportStatus, InputSource


class DailyReportCreate(BaseModel):
    report_date: date
    weather_summary: str | None = None
    temperature_high: float | None = None
    temperature_low: float | None = None
    workers_count: dict | None = None
    equipment_list: list | None = None
    work_content: str | None = None
    issues: str | None = None


class DailyReportGenerateRequest(BaseModel):
    """Request to AI-generate a daily report"""
    report_date: date
    workers_count: dict  # {"직종명": 인원수}
    equipment_list: list  # [{"type": "장비명", "count": 1, "hours": 8}]
    work_items: list[str]  # List of work done
    issues: str | None = None
    photos_count: int = 0


class DailyReportUpdate(BaseModel):
    weather_summary: str | None = None
    temperature_high: float | None = None
    temperature_low: float | None = None
    workers_count: dict | None = None
    equipment_list: list | None = None
    work_content: str | None = None
    issues: str | None = None
    status: ReportStatus | None = None


class DailyReportPhotoResponse(BaseModel):
    id: uuid.UUID
    s3_key: str
    caption: str | None
    sort_order: int

    model_config = {"from_attributes": True}


class DailyReportResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    report_date: date
    weather_summary: str | None
    temperature_high: float | None
    temperature_low: float | None
    workers_count: dict | None
    equipment_list: list | None
    work_content: str | None
    issues: str | None
    input_source: InputSource
    ai_generated: bool
    status: ReportStatus
    confirmed_by: uuid.UUID | None
    confirmed_at: datetime | None
    pdf_s3_key: str | None
    photos: list[DailyReportPhotoResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}
