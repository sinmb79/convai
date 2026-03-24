import uuid
from sqlalchemy import String, Boolean, Date, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
import enum


class InspectionResult(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL_PASS = "conditional_pass"


class InspectionStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    COMPLETED = "completed"


class InspectionRequest(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "inspection_requests"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    wbs_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wbs_items.id"), nullable=True)
    inspection_type: Mapped[str] = mapped_column(String(50), nullable=False)  # rebar, formwork, pipe_burial, etc.
    requested_date: Mapped[str] = mapped_column(Date, nullable=False)
    location_detail: Mapped[str | None] = mapped_column(String(200), nullable=True)
    checklist_items: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[InspectionResult | None] = mapped_column(
        SAEnum(InspectionResult, name="inspection_result"), nullable=True
    )
    inspector_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[InspectionStatus] = mapped_column(
        SAEnum(InspectionStatus, name="inspection_status"), default=InspectionStatus.DRAFT, nullable=False
    )
    pdf_s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # relationships
    project: Mapped["Project"] = relationship("Project", back_populates="inspection_requests")
    wbs_item: Mapped["WBSItem | None"] = relationship("WBSItem")
