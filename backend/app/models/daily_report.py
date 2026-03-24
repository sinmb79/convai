import uuid
from sqlalchemy import String, Integer, Boolean, Date, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from datetime import datetime
import enum


class ReportStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    SUBMITTED = "submitted"


class InputSource(str, enum.Enum):
    KAKAO = "kakao"
    WEB = "web"
    API = "api"


class DailyReport(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "daily_reports"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    report_date: Mapped[str] = mapped_column(Date, nullable=False, index=True)
    weather_summary: Mapped[str | None] = mapped_column(String(100), nullable=True)
    temperature_high: Mapped[float | None] = mapped_column(nullable=True)
    temperature_low: Mapped[float | None] = mapped_column(nullable=True)
    workers_count: Mapped[dict | None] = mapped_column(JSONB, nullable=True)   # {"concrete": 5, ...}
    equipment_list: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{"type": "backhoe", ...}]
    work_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    issues: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_source: Mapped[InputSource] = mapped_column(
        SAEnum(InputSource, name="input_source"), default=InputSource.WEB, nullable=False
    )
    raw_kakao_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        SAEnum(ReportStatus, name="daily_report_status"), default=ReportStatus.DRAFT, nullable=False
    )
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    pdf_s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # relationships
    project: Mapped["Project"] = relationship("Project", back_populates="daily_reports")
    photos: Mapped[list["DailyReportPhoto"]] = relationship(
        "DailyReportPhoto", back_populates="daily_report", cascade="all, delete-orphan"
    )
    confirmed_user: Mapped["User | None"] = relationship("User", foreign_keys=[confirmed_by])


class DailyReportPhoto(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "daily_report_photos"

    daily_report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("daily_reports.id"), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    caption: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # relationships
    daily_report: Mapped["DailyReport"] = relationship("DailyReport", back_populates="photos")
