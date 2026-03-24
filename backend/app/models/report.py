import uuid
from sqlalchemy import String, Date, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
import enum


class ReportType(str, enum.Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ReportStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    SUBMITTED = "submitted"


class Report(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "reports"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    report_type: Mapped[ReportType] = mapped_column(
        SAEnum(ReportType, name="report_type"), nullable=False
    )
    period_start: Mapped[str] = mapped_column(Date, nullable=False)
    period_end: Mapped[str] = mapped_column(Date, nullable=False)
    content_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_draft_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReportStatus] = mapped_column(
        SAEnum(ReportStatus, name="report_status"), default=ReportStatus.DRAFT, nullable=False
    )
    pdf_s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # relationships
    project: Mapped["Project"] = relationship("Project", back_populates="reports")
