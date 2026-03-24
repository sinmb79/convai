import uuid
from sqlalchemy import String, Boolean, Date, Text, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
import enum


class PermitStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class PermitItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "permit_items"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    permit_type: Mapped[str] = mapped_column(String(100), nullable=False)  # 도로점용허가, 하천점용허가, etc.
    authority: Mapped[str | None] = mapped_column(String(100), nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deadline: Mapped[str | None] = mapped_column(Date, nullable=True)
    status: Mapped[PermitStatus] = mapped_column(
        SAEnum(PermitStatus, name="permit_status"), default=PermitStatus.NOT_STARTED, nullable=False
    )
    submitted_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    approved_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    document_s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # relationships
    project: Mapped["Project"] = relationship("Project", back_populates="permit_items")
