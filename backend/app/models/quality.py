import uuid
from sqlalchemy import String, Date, Text, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
import enum


class QualityResult(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"


class QualityTest(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "quality_tests"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    wbs_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wbs_items.id"), nullable=True)
    test_type: Mapped[str] = mapped_column(String(50), nullable=False)  # compression_strength, slump, compaction, etc.
    test_date: Mapped[str] = mapped_column(Date, nullable=False)
    location_detail: Mapped[str | None] = mapped_column(String(200), nullable=True)
    design_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    measured_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    result: Mapped[QualityResult] = mapped_column(
        SAEnum(QualityResult, name="quality_result"), nullable=False
    )
    lab_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    report_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    project: Mapped["Project"] = relationship("Project", back_populates="quality_tests")
    wbs_item: Mapped["WBSItem | None"] = relationship("WBSItem")
